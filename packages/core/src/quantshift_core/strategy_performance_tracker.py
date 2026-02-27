"""
Strategy Performance Tracker

Updates strategy_performance table with metrics after each trade.
Calculates win rate, P&L, Sharpe ratio, profit factor, and drawdown per strategy.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import psycopg2
import structlog

logger = structlog.get_logger()


class StrategyPerformanceTracker:
    """Tracks and updates per-strategy performance metrics."""
    
    def __init__(self, db_conn):
        """
        Initialize the tracker.
        
        Args:
            db_conn: PostgreSQL database connection
        """
        self.db_conn = db_conn
    
    def update_strategy_performance(
        self,
        bot_name: str,
        strategy_name: str,
        trade_pnl: float,
        trade_pnl_pct: float,
        is_win: bool
    ) -> None:
        """
        Update strategy performance metrics after a trade closes.
        
        Args:
            bot_name: Name of the bot
            strategy_name: Name of the strategy that generated the trade
            trade_pnl: Trade P&L in dollars
            trade_pnl_pct: Trade P&L as percentage
            is_win: Whether the trade was profitable
        """
        try:
            cursor = self.db_conn.cursor()
            
            # Get current strategy performance or create new record
            cursor.execute("""
                SELECT 
                    total_trades, winning_trades, losing_trades,
                    total_pnl, total_pnl_pct, peak_equity,
                    avg_win, avg_loss, largest_win, largest_loss
                FROM strategy_performance
                WHERE bot_name = %s AND strategy_name = %s
            """, (bot_name, strategy_name))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                (total_trades, winning_trades, losing_trades,
                 total_pnl, total_pnl_pct, peak_equity,
                 avg_win, avg_loss, largest_win, largest_loss) = result
                
                total_trades += 1
                total_pnl += trade_pnl
                total_pnl_pct += trade_pnl_pct
                
                if is_win:
                    winning_trades += 1
                    # Update avg_win
                    if avg_win is None:
                        avg_win = trade_pnl
                    else:
                        avg_win = ((avg_win * (winning_trades - 1)) + trade_pnl) / winning_trades
                    # Update largest_win
                    if largest_win is None or trade_pnl > largest_win:
                        largest_win = trade_pnl
                else:
                    losing_trades += 1
                    # Update avg_loss
                    if avg_loss is None:
                        avg_loss = abs(trade_pnl)
                    else:
                        avg_loss = ((avg_loss * (losing_trades - 1)) + abs(trade_pnl)) / losing_trades
                    # Update largest_loss
                    if largest_loss is None or abs(trade_pnl) > largest_loss:
                        largest_loss = abs(trade_pnl)
                
                # Calculate win rate
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Calculate profit factor
                total_wins = avg_win * winning_trades if avg_win and winning_trades > 0 else 0
                total_losses = avg_loss * losing_trades if avg_loss and losing_trades > 0 else 0
                profit_factor = (total_wins / total_losses) if total_losses > 0 else None
                
                # Update peak equity and calculate drawdown
                if total_pnl > peak_equity:
                    peak_equity = total_pnl
                    current_drawdown = 0
                else:
                    current_drawdown = ((peak_equity - total_pnl) / peak_equity * 100) if peak_equity > 0 else 0
                
                # Get max drawdown
                cursor.execute("""
                    SELECT max_drawdown FROM strategy_performance
                    WHERE bot_name = %s AND strategy_name = %s
                """, (bot_name, strategy_name))
                max_dd_result = cursor.fetchone()
                max_drawdown = max_dd_result[0] if max_dd_result else 0
                
                if current_drawdown > (max_drawdown or 0):
                    max_drawdown = current_drawdown
                
                # Update the record
                cursor.execute("""
                    UPDATE strategy_performance SET
                        total_trades = %s,
                        winning_trades = %s,
                        losing_trades = %s,
                        win_rate = %s,
                        total_pnl = %s,
                        total_pnl_pct = %s,
                        avg_win = %s,
                        avg_loss = %s,
                        largest_win = %s,
                        largest_loss = %s,
                        profit_factor = %s,
                        max_drawdown = %s,
                        current_drawdown = %s,
                        peak_equity = %s,
                        last_trade_at = NOW(),
                        updated_at = NOW()
                    WHERE bot_name = %s AND strategy_name = %s
                """, (
                    total_trades, winning_trades, losing_trades, win_rate,
                    total_pnl, total_pnl_pct,
                    avg_win, avg_loss, largest_win, largest_loss,
                    profit_factor, max_drawdown, current_drawdown, peak_equity,
                    bot_name, strategy_name
                ))
            else:
                # Create new record
                win_rate = 100.0 if is_win else 0.0
                winning_trades = 1 if is_win else 0
                losing_trades = 0 if is_win else 1
                avg_win = trade_pnl if is_win else None
                avg_loss = abs(trade_pnl) if not is_win else None
                largest_win = trade_pnl if is_win else None
                largest_loss = abs(trade_pnl) if not is_win else None
                profit_factor = None
                peak_equity = trade_pnl if trade_pnl > 0 else 0
                current_drawdown = 0 if trade_pnl >= 0 else abs(trade_pnl / peak_equity * 100) if peak_equity > 0 else 0
                max_drawdown = current_drawdown
                
                cursor.execute("""
                    INSERT INTO strategy_performance (
                        id, bot_name, strategy_name,
                        total_trades, winning_trades, losing_trades, win_rate,
                        total_pnl, total_pnl_pct,
                        avg_win, avg_loss, largest_win, largest_loss,
                        profit_factor, max_drawdown, current_drawdown, peak_equity,
                        last_trade_at, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        NOW(), NOW(), NOW()
                    )
                """, (
                    bot_name, strategy_name,
                    1, winning_trades, losing_trades, win_rate,
                    trade_pnl, trade_pnl_pct,
                    avg_win, avg_loss, largest_win, largest_loss,
                    profit_factor, max_drawdown, current_drawdown, peak_equity
                ))
            
            self.db_conn.commit()
            
            logger.info(
                "strategy_performance_updated",
                bot_name=bot_name,
                strategy=strategy_name,
                trade_pnl=trade_pnl,
                is_win=is_win,
                total_trades=total_trades if result else 1,
                win_rate=win_rate
            )
            
        except Exception as e:
            logger.error("strategy_performance_update_failed", error=str(e), exc_info=True)
            if self.db_conn:
                try:
                    self.db_conn.rollback()
                except:
                    pass
