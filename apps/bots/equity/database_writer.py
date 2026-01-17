#!/usr/bin/env python3
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg2
import logging

logger = logging.getLogger(__name__)

class DatabaseWriter:
    def __init__(self, bot_name: str = 'equity-bot', db_url: str = None):
        self.bot_name = bot_name
        self.db_url = db_url or os.getenv('DATABASE_URL', "postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift")
        self.conn = None
        
    def connect(self):
        try:
            self.conn = psycopg2.connect(self.db_url)
            logger.info(f"Connected to database for {self.bot_name}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
            
    def update_status(self, account_info: Dict[str, Any], positions: List[Dict], trades_count: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
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
                str(uuid.uuid4()), self.bot_name, 'RUNNING', datetime.now(),
                float(account_info.get('equity', 0)), float(account_info.get('balance', 0)),
                float(account_info.get('buying_power', 0)), float(account_info.get('portfolio_value', 0)),
                float(sum(p.get('unrealized_pl', 0) for p in positions)), 0.0,
                len(positions), trades_count, datetime.now(), datetime.now()
            ))
            self.conn.commit()
            logger.info(f"✅ Updated status - Equity: ${account_info.get('equity', 0):,.2f}, Positions: {len(positions)}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            self.conn.rollback()
            
    def update_positions(self, positions: List[Dict]):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM positions WHERE bot_name = %s", (self.bot_name,))
            
            for pos in positions:
                quantity = float(pos.get('quantity', 0))
                entry_price = float(pos.get('entry_price', 0))
                current_price = float(pos.get('current_price', 0))
                unrealized_pl = float(pos.get('unrealized_pl', 0))
                market_value = quantity * current_price
                unrealized_pl_pct = (unrealized_pl / (entry_price * quantity)) * 100 if entry_price > 0 and quantity > 0 else 0
                
                cursor.execute("""
                    INSERT INTO positions (
                        id, bot_name, symbol, quantity, entry_price, current_price,
                        cost_basis, market_value, unrealized_pl, unrealized_pl_pct, strategy, entered_at, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()), self.bot_name, pos['symbol'],
                    quantity, entry_price, current_price, (quantity * entry_price), market_value,
                    unrealized_pl, unrealized_pl_pct, 'MA_CROSSOVER', datetime.now(), datetime.now(), datetime.now()
                ))
            self.conn.commit()
            logger.info(f"✅ Updated {len(positions)} positions")
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            self.conn.rollback()
