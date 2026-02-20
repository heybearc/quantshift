#!/usr/bin/env python3
"""
Database Writer for QuantShift Admin Platform Integration
Writes bot data to PostgreSQL for the Next.js admin dashboard
"""
import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

class DatabaseWriter:
    """Writes trading bot data to PostgreSQL for admin platform"""
    
    def __init__(self, bot_name: str = 'equity-bot', db_url: str = None):
        self.bot_name = bot_name
        # Use localhost for local testing, production will use LXC 131
        self.db_url = db_url or os.getenv('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/quantshift")
        self.conn = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            logger.info(f"Connected to database for {self.bot_name}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
            
    def update_status(self, account_info: Dict[str, Any], positions: List[Dict], trades_count: int):
        """
        Update bot status - call every minute
        
        Args:
            account_info: Dict with equity, cash, buying_power, portfolio_value, etc.
            positions: List of current positions
            trades_count: Total number of trades
        """
        try:
            cursor = self.conn.cursor()
            
            # Upsert bot status
            cursor.execute("""
                INSERT INTO bot_status (
                    bot_name, status, last_heartbeat, account_equity,
                    account_cash, buying_power, portfolio_value,
                    unrealized_pl, realized_pl, positions_count, trades_count,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                self.bot_name,
                'RUNNING',
                datetime.now(),
                float(account_info.get('equity', 0)),
                float(account_info.get('balance', 0)),
                float(account_info.get('buying_power', 0)),
                float(account_info.get('portfolio_value', 0)),
                float(sum(p.get('unrealized_pl', 0) for p in positions)),
                0.0,  # realized_pl - calculate from closed trades
                len(positions),
                trades_count,
                datetime.now(),
                datetime.now()
            ))
            
            self.conn.commit()
            logger.debug(f"Updated status for {self.bot_name}")
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            self.conn.rollback()
            
    def record_trade_entry(self, symbol: str, side: str, quantity: float, 
                          entry_price: float, stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None, 
                          strategy: str = 'MA_CROSSOVER',
                          signal_type: Optional[str] = None,
                          entry_reason: Optional[str] = None) -> Optional[str]:
        """
        Record trade entry
        
        Returns:
            trade_id: UUID of created trade
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO trades (
                    bot_name, symbol, side, quantity, entry_price,
                    stop_loss, take_profit, status, strategy,
                    signal_type, entry_reason, entered_at,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                self.bot_name,
                symbol,
                side.upper(),
                float(quantity),
                float(entry_price),
                float(stop_loss) if stop_loss else None,
                float(take_profit) if take_profit else None,
                'OPEN',
                strategy,
                signal_type,
                entry_reason,
                datetime.now(),
                datetime.now(),
                datetime.now()
            ))
            
            trade_id = cursor.fetchone()[0]
            self.conn.commit()
            
            logger.info(f"Recorded trade entry: {side} {quantity} {symbol} @ ${entry_price:.2f}")
            return trade_id
            
        except Exception as e:
            logger.error(f"Error recording trade entry: {e}")
            self.conn.rollback()
            return None
            
    def record_trade_exit(self, trade_id: str, exit_price: float, 
                         exit_reason: Optional[str] = None):
        """
        Record trade exit and calculate P&L
        
        Args:
            trade_id: UUID of the trade
            exit_price: Exit price
            exit_reason: Reason for exit
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Get trade details
            cursor.execute("""
                SELECT * FROM trades WHERE id = %s
            """, (trade_id,))
            
            trade = cursor.fetchone()
            if not trade:
                logger.error(f"Trade {trade_id} not found")
                return
                
            # Calculate P&L
            entry_price = float(trade['entryPrice'])
            quantity = float(trade['quantity'])
            
            if trade['side'] == 'BUY':
                pnl = (float(exit_price) - entry_price) * quantity
            else:  # SELL/SHORT
                pnl = (entry_price - float(exit_price)) * quantity

            pnl_percent = (pnl / (entry_price * quantity)) * 100
            
            # Update trade
            cursor.execute("""
                UPDATE trades
                SET exit_price = %s,
                    status = %s,
                    exit_reason = %s,
                    exited_at = %s,
                    pnl = %s,
                    pnl_percent = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                float(exit_price),
                'CLOSED',
                exit_reason,
                datetime.now(),
                pnl,
                pnl_percent,
                datetime.now(),
                trade_id
            ))
            
            self.conn.commit()
            logger.info(f"Recorded trade exit: {trade['symbol']} @ ${exit_price:.2f}, P&L: ${pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error recording trade exit: {e}")
            self.conn.rollback()
            
    def update_positions(self, positions: List[Dict[str, Any]]):
        """
        Update all current positions
        
        Args:
            positions: List of position dicts with symbol, quantity, prices, etc.
        """
        try:
            cursor = self.conn.cursor()
            
            # Delete existing positions for this bot
            cursor.execute("""
                DELETE FROM positions WHERE bot_name = %s
            """, (self.bot_name,))

            # Insert current positions
            for pos in positions:
                cursor.execute("""
                    INSERT INTO positions (
                        bot_name, symbol, quantity, entry_price,
                        current_price, market_value, cost_basis,
                        unrealized_pl, unrealized_pl_pct, stop_loss,
                        take_profit, strategy, entered_at,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.bot_name,
                    pos['symbol'],
                    float(pos['quantity']),
                    float(pos['entry_price']),
                    float(pos['current_price']),
                    float(pos['market_value']),
                    float(pos['cost_basis']),
                    float(pos['unrealized_pl']),
                    float(pos['unrealized_plpc']) * 100,  # Convert to percentage
                    None,  # stop_loss - add if available
                    None,  # take_profit - add if available
                    'MA_CROSSOVER',
                    datetime.now(),
                    datetime.now(),
                    datetime.now()
                ))
            
            self.conn.commit()
            logger.debug(f"Updated {len(positions)} positions for {self.bot_name}")
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            self.conn.rollback()
            
    def record_daily_performance(self, daily_trades: List[Dict[str, Any]], 
                                account_equity: float):
        """
        Record daily performance metrics
        
        Args:
            daily_trades: List of trades from today
            account_equity: Current account equity
        """
        try:
            if not daily_trades:
                logger.debug("No trades today, skipping performance record")
                return
                
            cursor = self.conn.cursor()
            
            # Calculate metrics
            winning_trades = [t for t in daily_trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in daily_trades if t.get('pnl', 0) < 0]
            
            total_wins = sum(t.get('pnl', 0) for t in winning_trades)
            total_losses = abs(sum(t.get('pnl', 0) for t in losing_trades))
            total_pnl = sum(t.get('pnl', 0) for t in daily_trades)
            
            win_rate = (len(winning_trades) / len(daily_trades)) * 100 if daily_trades else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            # Insert or update daily metrics
            cursor.execute("""
                INSERT INTO performance_metrics (
                    bot_name, date, total_trades, winning_trades,
                    losing_trades, win_rate, profit_factor,
                    sharpe_ratio, max_drawdown, total_pnl,
                    total_pnl_pct, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bot_name, date)
                DO UPDATE SET
                    total_trades = EXCLUDED.total_trades,
                    winning_trades = EXCLUDED.winning_trades,
                    losing_trades = EXCLUDED.losing_trades,
                    win_rate = EXCLUDED.win_rate,
                    profit_factor = EXCLUDED.profit_factor,
                    total_pnl = EXCLUDED.total_pnl,
                    total_pnl_pct = EXCLUDED.total_pnl_pct,
                    updated_at = EXCLUDED.updated_at
            """, (
                self.bot_name,
                datetime.now().date(),
                len(daily_trades),
                len(winning_trades),
                len(losing_trades),
                win_rate,
                profit_factor,
                0.0,  # sharpe_ratio - calculate if needed
                0.0,  # max_drawdown - calculate if needed
                total_pnl,
                (total_pnl / account_equity) * 100 if account_equity > 0 else 0,
                datetime.now(),
                datetime.now()
            ))
            
            self.conn.commit()
            logger.info(f"Recorded daily performance: {len(daily_trades)} trades, P&L: ${total_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error recording daily performance: {e}")
            self.conn.rollback()
