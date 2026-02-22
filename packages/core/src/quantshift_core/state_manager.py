"""State management with Redis and PostgreSQL for hot-standby failover."""

import json
import signal
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import redis
import structlog
from sqlalchemy.orm import Session

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
        key = f"bot:{self.bot_name}:heartbeat"
        self.redis_client.setex(key, 60, datetime.utcnow().isoformat())

    def is_primary(self) -> bool:
        """Check if this bot instance should be primary."""
        try:
            # Check if another instance has recent heartbeat
            key = f"bot:{self.bot_name}:primary_lock"
            lock = self.redis_client.set(key, "locked", nx=True, ex=30)
            return lock is not None
        except Exception as e:
            logger.error("primary_check_failed", error=str(e))
            return True  # Default to primary if Redis fails
