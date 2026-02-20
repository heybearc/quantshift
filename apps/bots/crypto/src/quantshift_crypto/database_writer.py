#!/usr/bin/env python3
"""
Database Writer for QuantShift Crypto Bot - Admin Platform Integration
Writes crypto bot data to PostgreSQL for the Next.js admin dashboard
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class CryptoDatabaseWriter:
    """Writes crypto trading bot data to PostgreSQL for admin platform"""

    def __init__(self, bot_name: str = 'crypto-bot', db_url: str = None):
        self.bot_name = bot_name
        self.db_url = db_url or os.getenv(
            'DATABASE_URL',
            'postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift'
        )
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        self.conn.autocommit = False
        logger.info(f"Connected to database for {self.bot_name}")

    def disconnect(self):
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")

    def is_connected(self) -> bool:
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT 1')
            cur.fetchone()
            return True
        except Exception:
            return False

    def ensure_connected(self) -> bool:
        if self.conn and self.is_connected():
            return True
        try:
            self.connect()
            return True
        except Exception as e:
            logger.warning(f"Could not reconnect: {e}")
            return False

    def update_status(self, account_info: Dict[str, Any], positions: List[Dict], trades_count: int):
        """Upsert bot status row — called every heartbeat."""
        if not self.ensure_connected():
            return
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO bot_status (
                    id, bot_name, status, last_heartbeat, account_equity,
                    account_cash, buying_power, portfolio_value,
                    unrealized_pl, realized_pl, positions_count, trades_count,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bot_name)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    last_heartbeat = EXCLUDED.last_heartbeat,
                    account_equity = EXCLUDED.account_equity,
                    account_cash = EXCLUDED.account_cash,
                    buying_power = EXCLUDED.buying_power,
                    portfolio_value = EXCLUDED.portfolio_value,
                    unrealized_pl = EXCLUDED.unrealized_pl,
                    realized_pl = EXCLUDED.realized_pl,
                    positions_count = EXCLUDED.positions_count,
                    trades_count = EXCLUDED.trades_count,
                    updated_at = EXCLUDED.updated_at
            """, (
                str(uuid.uuid4()),
                self.bot_name,
                'RUNNING',
                datetime.now(),
                float(account_info.get('equity', 0)),
                float(account_info.get('cash', 0)),
                float(account_info.get('buying_power', 0)),
                float(account_info.get('portfolio_value', 0)),
                float(sum(p.get('unrealized_pl', 0) for p in positions)),
                0.0,
                len(positions),
                trades_count,
                datetime.now(),
                datetime.now(),
            ))
            self.conn.commit()
            logger.debug(f"Bot status updated: {len(positions)} positions, {trades_count} trades")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass

    def seed_bot_config(self, strategy_name: str, symbols: List[str]):
        """Ensure bot_config has an entry for this bot."""
        if not self.ensure_connected():
            return
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO bot_config (
                    id, name, strategy, symbols, enabled, paper_trading,
                    risk_per_trade, max_position_size, max_portfolio_heat,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (name) DO UPDATE SET
                    strategy = EXCLUDED.strategy,
                    updated_at = NOW()
            """, (
                str(uuid.uuid4()),
                self.bot_name,
                strategy_name,
                symbols,
                True,
                True,   # sandbox = paper trading
                0.02,
                0.10,
                0.20,
            ))
            self.conn.commit()
            logger.info(f"Bot config seeded: strategy={strategy_name}")
        except Exception as e:
            logger.warning(f"Could not seed bot_config: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass

    def update_positions(self, positions: List[Dict[str, Any]]):
        """Replace all positions for this bot."""
        if not self.ensure_connected():
            return
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM positions WHERE bot_name = %s", (self.bot_name,))
            for pos in positions:
                cur.execute("""
                    INSERT INTO positions (
                        id, bot_name, symbol, quantity, entry_price,
                        current_price, market_value, cost_basis,
                        unrealized_pl, unrealized_pl_pct, stop_loss,
                        take_profit, strategy, entered_at,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    str(uuid.uuid4()),
                    self.bot_name,
                    pos.get('symbol', ''),
                    float(pos.get('quantity', 0)),
                    float(pos.get('entry_price', 0)),
                    float(pos.get('current_price', 0)),
                    float(pos.get('market_value', 0)),
                    float(pos.get('cost_basis', 0)),
                    float(pos.get('unrealized_pl', 0)),
                    float(pos.get('unrealized_plpc', 0)) * 100,
                    pos.get('stop_loss'),
                    pos.get('take_profit'),
                    pos.get('strategy', 'MA_CROSSOVER'),
                    datetime.now(),
                ))
            self.conn.commit()
            logger.debug(f"Updated {len(positions)} positions")
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass

    def record_trade(self, symbol: str, side: str, quantity: float,
                     entry_price: float, strategy: str, order_id: str = None):
        """Record a new open trade."""
        if not self.ensure_connected():
            return None
        try:
            trade_id = str(uuid.uuid4())
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO trades (
                    id, bot_name, symbol, side, quantity, entry_price,
                    status, strategy, entered_at, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
                RETURNING id
            """, (
                trade_id, self.bot_name, symbol, side.upper(),
                float(quantity), float(entry_price), 'OPEN', strategy,
            ))
            self.conn.commit()
            logger.info(f"Recorded trade: {side} {quantity} {symbol} @ ${entry_price:.4f}")
            return trade_id
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return None

    def close_trade(self, trade_id: str, exit_price: float, exit_reason: str = ''):
        """Mark a trade as closed and calculate P&L."""
        if not self.ensure_connected():
            return
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM trades WHERE id = %s", (trade_id,))
            trade = cur.fetchone()
            if not trade:
                return
            entry_price = float(trade['entry_price'])
            quantity = float(trade['quantity'])
            if trade['side'] == 'BUY':
                pnl = (float(exit_price) - entry_price) * quantity
            else:
                pnl = (entry_price - float(exit_price)) * quantity
            pnl_pct = (pnl / (entry_price * quantity)) * 100 if entry_price * quantity else 0
            cur.execute("""
                UPDATE trades SET
                    exit_price = %s, status = 'CLOSED', exit_reason = %s,
                    exited_at = NOW(), pnl = %s, pnl_percent = %s, updated_at = NOW()
                WHERE id = %s
            """, (float(exit_price), exit_reason, pnl, pnl_pct, trade_id))
            self.conn.commit()
            logger.info(f"Closed trade {trade_id}: P&L ${pnl:.4f} ({pnl_pct:.2f}%)")
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
