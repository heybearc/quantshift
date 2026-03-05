"""State management with Redis and PostgreSQL for hot-standby failover."""

import json
import os
import signal
import sys
from datetime import datetime
from typing import Any, Dict, Optional, List
from contextlib import contextmanager

import redis
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text

from quantshift_core.config import get_settings
from quantshift_core.database import get_db

logger = structlog.get_logger()


class StateManager:
    """Manage bot state across Redis and PostgreSQL for failover."""

    def __init__(self, bot_name: str) -> None:
        """Initialize state manager."""
        self.bot_name = bot_name
        settings = get_settings()
        
        # Redis connection - use URL from settings (password included if needed)
        redis_url = str(settings.redis_url)
        
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self.db = get_db()
        self._shutdown_handlers: list = []
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        logger.info("signal_handlers_registered", bot_name=self.bot_name)

    def _handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle graceful shutdown."""
        logger.info(
            "shutdown_initiated",
            bot_name=self.bot_name,
            signal=signal.Signals(signum).name,
        )
        
        # Run registered shutdown handlers
        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error("shutdown_handler_failed", error=str(e))
        
        # Save final state
        try:
            self.save_state({"shutdown_time": datetime.utcnow().isoformat()})
            logger.info("final_state_saved", bot_name=self.bot_name)
        except Exception as e:
            logger.error("final_state_save_failed", error=str(e))
        
        sys.exit(0)

    def register_shutdown_handler(self, handler: callable) -> None:
        """Register a function to run on shutdown."""
        self._shutdown_handlers.append(handler)

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save bot state to Redis."""
        try:
            key = f"bot:{self.bot_name}:state"
            state["last_update"] = datetime.utcnow().isoformat()
            self.redis_client.setex(
                key,
                3600,  # 1 hour TTL
                json.dumps(state),
            )
            logger.debug("state_saved", bot_name=self.bot_name, key=key)
        except Exception as e:
            logger.error("state_save_failed", error=str(e))
    
    def update_state(self, state: Dict[str, Any]) -> None:
        """Alias for save_state for backward compatibility."""
        self.save_state(state)

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load bot state from Redis."""
        try:
            key = f"bot:{self.bot_name}:state"
            data = self.redis_client.get(key)
            if data:
                state = json.loads(data)
                logger.info("state_loaded", bot_name=self.bot_name)
                return state
            return None
        except Exception as e:
            logger.error("state_load_failed", error=str(e))
            return None

    def save_position(self, symbol: str, position_data: Dict[str, Any]) -> None:
        """Save position to Redis for quick recovery."""
        try:
            key = f"bot:{self.bot_name}:position:{symbol}"
            position_data["last_update"] = datetime.utcnow().isoformat()
            self.redis_client.setex(
                key,
                86400,  # 24 hour TTL
                json.dumps(position_data),
            )
            logger.debug("position_saved", symbol=symbol)
        except Exception as e:
            # Silently fail if Redis is read-only (standby server)
            if "read only replica" not in str(e).lower():
                logger.error("position_save_failed", symbol=symbol, error=str(e))

    def load_positions(self) -> Dict[str, Dict[str, Any]]:
        """Load all positions from Redis."""
        try:
            pattern = f"bot:{self.bot_name}:position:*"
            positions = {}
            for key in self.redis_client.scan_iter(match=pattern):
                symbol = key.split(":")[-1]
                data = self.redis_client.get(key)
                if data:
                    positions[symbol] = json.loads(data)
            logger.info("positions_loaded", count=len(positions))
            return positions
        except Exception as e:
            logger.error("positions_load_failed", error=str(e))
            return {}

    def clear_position(self, symbol: str) -> None:
        """Clear position from Redis."""
        try:
            key = f"bot:{self.bot_name}:position:{symbol}"
            self.redis_client.delete(key)
            logger.debug("position_cleared", symbol=symbol)
        except Exception as e:
            logger.error("position_clear_failed", symbol=symbol, error=str(e))

    def heartbeat(self) -> None:
        """Send heartbeat to indicate bot is alive."""
        try:
            key = f"bot:{self.bot_name}:heartbeat"
            self.redis_client.setex(key, 60, datetime.utcnow().isoformat())
        except Exception as e:
            # Silently fail if Redis is read-only (standby server)
            if "read only replica" not in str(e).lower():
                logger.error("redis_heartbeat_failed", error=str(e))

    def is_primary(self) -> bool:
        """Check if this bot instance should be primary.
        
        Uses Redis lock with instance ID to prevent split-brain.
        Primary refreshes lock every cycle. Standby waits for lock to expire.
        """
        try:
            import socket
            instance_id = f"{socket.gethostname()}:{os.getpid()}"
            key = f"bot:{self.bot_name}:primary_lock"
            
            # Try to acquire lock with our instance ID
            acquired = self.redis_client.set(key, instance_id, nx=True, ex=30)
            
            if acquired:
                # We acquired the lock - we are primary
                return True
            
            # Lock exists - check if it's ours
            current_holder = self.redis_client.get(key)
            if current_holder == instance_id:
                # We already hold the lock - refresh it
                self.redis_client.expire(key, 30)
                return True
            
            # Another instance holds the lock - we are standby
            return False
            
        except Exception as e:
            error_msg = str(e)
            # If Redis is read-only replica, we are standby
            if "read only replica" in error_msg.lower() or "readonly" in error_msg.lower():
                logger.debug("redis_readonly_standby", bot_name=self.bot_name)
                return False
            
            logger.error("primary_check_failed", error=error_msg)
            return True  # Default to primary if Redis fails for other reasons
    
    @contextmanager
    def atomic_transaction(self):
        """
        Context manager for atomic database transactions.
        
        Usage:
            with state_manager.atomic_transaction() as session:
                # Perform database operations
                # Automatically commits on success, rolls back on error
        """
        with self.db.session() as session:
            try:
                yield session
                # Commit happens automatically in db.session() context manager
                logger.debug("transaction_committed", bot_name=self.bot_name)
            except Exception as e:
                # Rollback happens automatically in db.session() context manager
                logger.error("transaction_rolled_back", bot_name=self.bot_name, error=str(e))
                raise
    
    def update_position_atomic(
        self,
        bot_name: str,
        symbol: str,
        quantity: float,
        entry_price: float,
        current_price: float,
        unrealized_pl: float,
        strategy_name: str
    ) -> None:
        """
        Update position in database with atomic transaction and row locking.
        
        Uses FOR UPDATE to lock the row and prevent race conditions.
        If bot crashes mid-update, transaction is rolled back automatically.
        
        Args:
            bot_name: Name of the bot
            symbol: Trading symbol
            quantity: Position quantity
            entry_price: Entry price
            current_price: Current market price
            unrealized_pl: Unrealized profit/loss
            strategy_name: Strategy that created this position
        """
        with self.atomic_transaction() as session:
            # Lock the row for update to prevent concurrent modifications
            result = session.execute(
                text("""
                    SELECT id FROM positions 
                    WHERE bot_name = :bot_name AND symbol = :symbol
                    FOR UPDATE
                """),
                {"bot_name": bot_name, "symbol": symbol}
            ).fetchone()
            
            # Calculate unrealized P&L percentage
            unrealized_pl_pct = 0.0
            if entry_price and entry_price > 0:
                unrealized_pl_pct = ((current_price - entry_price) / entry_price) * 100
            
            if result:
                # Update existing position
                session.execute(
                    text("""
                        UPDATE positions
                        SET quantity = :quantity,
                            entry_price = :entry_price,
                            current_price = :current_price,
                            unrealized_pl = :unrealized_pl,
                            unrealized_pl_pct = :unrealized_pl_pct,
                            strategy = :strategy_name,
                            updated_at = NOW()
                        WHERE bot_name = :bot_name AND symbol = :symbol
                    """),
                    {
                        "bot_name": bot_name,
                        "symbol": symbol,
                        "quantity": quantity,
                        "entry_price": entry_price,
                        "current_price": current_price,
                        "unrealized_pl": unrealized_pl,
                        "unrealized_pl_pct": unrealized_pl_pct,
                        "strategy_name": strategy_name
                    }
                )
                logger.debug("position_updated_atomic", symbol=symbol)
            else:
                # Insert new position
                session.execute(
                    text("""
                        INSERT INTO positions 
                        (bot_name, symbol, quantity, entry_price, current_price, 
                         unrealized_pl, unrealized_pl_pct, strategy, created_at, updated_at)
                        VALUES 
                        (:bot_name, :symbol, :quantity, :entry_price, :current_price,
                         :unrealized_pl, :unrealized_pl_pct, :strategy_name, NOW(), NOW())
                    """),
                    {
                        "bot_name": bot_name,
                        "symbol": symbol,
                        "quantity": quantity,
                        "entry_price": entry_price,
                        "current_price": current_price,
                        "unrealized_pl": unrealized_pl,
                        "unrealized_pl_pct": unrealized_pl_pct,
                        "strategy_name": strategy_name
                    }
                )
                logger.debug("position_inserted_atomic", symbol=symbol)
    
    def delete_position_atomic(self, bot_name: str, symbol: str) -> None:
        """
        Delete position from database with atomic transaction.
        
        Args:
            bot_name: Name of the bot
            symbol: Trading symbol to delete
        """
        with self.atomic_transaction() as session:
            session.execute(
                text("""
                    DELETE FROM positions
                    WHERE bot_name = :bot_name AND symbol = :symbol
                """),
                {"bot_name": bot_name, "symbol": symbol}
            )
            logger.debug("position_deleted_atomic", symbol=symbol)
    
    def get_positions_atomic(self, bot_name: str) -> List[Dict[str, Any]]:
        """
        Get all positions for a bot with atomic read.
        
        Args:
            bot_name: Name of the bot
            
        Returns:
            List of position dictionaries
        """
        with self.atomic_transaction() as session:
            result = session.execute(
                text("""
                    SELECT symbol, quantity, entry_price, current_price, 
                           unrealized_pl, strategy_name, created_at, updated_at
                    FROM positions
                    WHERE bot_name = :bot_name
                """),
                {"bot_name": bot_name}
            )
            
            positions = []
            for row in result:
                positions.append({
                    "symbol": row.symbol,
                    "quantity": float(row.quantity),
                    "entry_price": float(row.entry_price),
                    "current_price": float(row.current_price),
                    "unrealized_pl": float(row.unrealized_pl),
                    "strategy_name": row.strategy_name,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })
            
            logger.debug("positions_fetched_atomic", count=len(positions))
            return positions
    
    def sync_positions_atomic(
        self,
        bot_name: str,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Sync multiple positions atomically in a single transaction.
        
        All positions are updated/inserted in one transaction.
        If any operation fails, all changes are rolled back.
        
        Args:
            bot_name: Name of the bot
            positions: List of position dictionaries
            
        Returns:
            Dict with counts of inserted, updated, deleted positions
        """
        stats = {"inserted": 0, "updated": 0, "deleted": 0}
        
        with self.atomic_transaction() as session:
            # Get existing positions
            existing = session.execute(
                text("SELECT symbol FROM positions WHERE bot_name = :bot_name FOR UPDATE"),
                {"bot_name": bot_name}
            ).fetchall()
            existing_symbols = {row.symbol for row in existing}
            
            # Update/insert new positions
            new_symbols = set()
            for pos in positions:
                symbol = pos["symbol"]
                new_symbols.add(symbol)
                
                # Calculate unrealized P&L percentage
                unrealized_pl_pct = 0.0
                if pos["entry_price"] and pos["entry_price"] > 0:
                    unrealized_pl_pct = ((pos["current_price"] - pos["entry_price"]) / pos["entry_price"]) * 100
                
                if symbol in existing_symbols:
                    # Update
                    session.execute(
                        text("""
                            UPDATE positions
                            SET quantity = :quantity,
                                entry_price = :entry_price,
                                current_price = :current_price,
                                unrealized_pl = :unrealized_pl,
                                unrealized_pl_pct = :unrealized_pl_pct,
                                strategy = :strategy_name,
                                updated_at = NOW()
                            WHERE bot_name = :bot_name AND symbol = :symbol
                        """),
                        {
                            "bot_name": bot_name,
                            "symbol": symbol,
                            "quantity": pos["quantity"],
                            "entry_price": pos["entry_price"],
                            "current_price": pos["current_price"],
                            "unrealized_pl": pos["unrealized_pl"],
                            "unrealized_pl_pct": unrealized_pl_pct,
                            "strategy_name": pos.get("strategy_name", "UNKNOWN")
                        }
                    )
                    stats["updated"] += 1
                else:
                    # Insert
                    session.execute(
                        text("""
                            INSERT INTO positions 
                            (bot_name, symbol, quantity, entry_price, current_price, 
                             unrealized_pl, unrealized_pl_pct, strategy, created_at, updated_at)
                            VALUES 
                            (:bot_name, :symbol, :quantity, :entry_price, :current_price,
                             :unrealized_pl, :unrealized_pl_pct, :strategy_name, NOW(), NOW())
                        """),
                        {
                            "bot_name": bot_name,
                            "symbol": symbol,
                            "quantity": pos["quantity"],
                            "entry_price": pos["entry_price"],
                            "current_price": pos["current_price"],
                            "unrealized_pl": pos["unrealized_pl"],
                            "unrealized_pl_pct": unrealized_pl_pct,
                            "strategy_name": pos.get("strategy_name", "UNKNOWN")
                        }
                    )
                    stats["inserted"] += 1
            
            # Delete positions that no longer exist
            deleted_symbols = existing_symbols - new_symbols
            for symbol in deleted_symbols:
                session.execute(
                    text("DELETE FROM positions WHERE bot_name = :bot_name AND symbol = :symbol"),
                    {"bot_name": bot_name, "symbol": symbol}
                )
                stats["deleted"] += 1
            
            logger.info(
                "positions_synced_atomic",
                bot_name=bot_name,
                inserted=stats["inserted"],
                updated=stats["updated"],
                deleted=stats["deleted"]
            )
            
        return stats
