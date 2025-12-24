"""
Performance Tracker
Tracks and reports trading performance metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Optional, Any
import logging

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
from alpaca_trading.core.config import config

from alpaca_trading.utils.logging_config import setup_logger

logger = setup_logger(__name__)

class PerformanceTracker:
    """Track and analyze trading performance"""
    
    def __init__(self):
        self.alpaca_client = tradeapi.REST(config.api_key, config.api_secret, config.base_url)
        self.performance_file = "logs/performance_history.json"
        self.trades_directory = "logs/"
        
        # Ensure logs directory exists
        os.makedirs(self.trades_directory, exist_ok=True)
        
        # Load existing performance data
        self.performance_history = self.load_performance_history()
    
    def load_performance_history(self) -> Dict:
        """Load existing performance history from file"""
        try:
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'daily_performance': {},
                    'monthly_summary': {},
                    'overall_stats': {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'total_pnl': 0.0,
                        'max_drawdown': 0.0,
                        'sharpe_ratio': 0.0,
                        'start_date': datetime.now().isoformat()
                    }
                }
        except Exception as e:
            logger.error(f"Error loading performance history: {e}")
            return {'daily_performance': {}, 'monthly_summary': {}, 'overall_stats': {}}
    
    def save_performance_history(self):
        """Save performance history to file"""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving performance history: {e}")
    
    def update_daily_performance(self):
        """Update daily performance metrics"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get today's trades
            trades_today = self.get_trades_for_date(today)
            
            if not trades_today:
                logger.info("No trades found for today")
                return
            
            # Calculate daily metrics
            daily_metrics = self.calculate_daily_metrics(trades_today)
            
            # Update performance history
            self.performance_history['daily_performance'][today] = daily_metrics
            
            # Update overall statistics
            self.update_overall_stats(daily_metrics)
            
            # Save to file
            self.save_performance_history()
            
            # Generate daily report
            self.generate_daily_report(today, daily_metrics)
            
            logger.info(f"Daily performance updated for {today}")
            
        except Exception as e:
            logger.error(f"Error updating daily performance: {e}")
    
    def get_trades_for_date(self, date_str: str) -> List[Dict]:
        """Get all trades for a specific date"""
        try:
            trades_file = f"{self.trades_directory}trades_{date_str.replace('-', '')}.csv"
            
            if os.path.exists(trades_file):
                df = pd.read_csv(trades_file)
                return df.to_dict('records')
            else:
                # Fallback to API call
                return [order.__dict__ for order in self.alpaca_client.list_orders(status='filled', limit=100)]
                
        except Exception as e:
            logger.error(f"Error getting trades for {date_str}: {e}")
            return []
    
    def calculate_daily_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate daily performance metrics from trades"""
        try:
            if not trades:
                return {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'gross_pnl': 0.0,
                    'net_pnl': 0.0,
                    'win_rate': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'largest_win': 0.0,
                    'largest_loss': 0.0,
                    'total_volume': 0,
                    'total_fees': 0.0
                }
            
            df = pd.DataFrame(trades)
            
            # Calculate P&L for each trade
            buy_trades = df[df['side'] == 'buy'].copy()
            sell_trades = df[df['side'] == 'sell'].copy()
            
            # Match buy and sell orders to calculate P&L
            pnl_list = []
            fees_total = 0.0
            volume_total = 0
            
            for _, sell_trade in sell_trades.iterrows():
                symbol = sell_trade['symbol']
                sell_qty = float(sell_trade['qty'])
                sell_price = float(sell_trade['filled_avg_price'])
                
                # Find corresponding buy trade
                matching_buys = buy_trades[buy_trades['symbol'] == symbol]
                
                if not matching_buys.empty:
                    buy_trade = matching_buys.iloc[0]  # Take first matching buy
                    buy_price = float(buy_trade['filled_avg_price'])
                    buy_qty = float(buy_trade['qty'])
                    
                    # Calculate P&L
                    qty = min(sell_qty, buy_qty)
                    pnl = (sell_price - buy_price) * qty
                    pnl_list.append(pnl)
                    
                    # Add fees if available
                    if 'fees' in sell_trade:
                        fees_total += float(sell_trade.get('fees', 0))
                    if 'fees' in buy_trade:
                        fees_total += float(buy_trade.get('fees', 0))
                    
                    volume_total += qty
            
            # Calculate metrics
            total_trades = len(pnl_list)
            winning_trades = len([p for p in pnl_list if p > 0])
            losing_trades = len([p for p in pnl_list if p < 0])
            
            gross_pnl = sum(pnl_list)
            net_pnl = gross_pnl - fees_total
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            wins = [p for p in pnl_list if p > 0]
            losses = [p for p in pnl_list if p < 0]
            
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            largest_win = max(wins) if wins else 0
            largest_loss = min(losses) if losses else 0
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'gross_pnl': round(gross_pnl, 2),
                'net_pnl': round(net_pnl, 2),
                'win_rate': round(win_rate, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'largest_win': round(largest_win, 2),
                'largest_loss': round(largest_loss, 2),
                'total_volume': int(volume_total),
                'total_fees': round(fees_total, 2),
                'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating daily metrics: {e}")
            return {}
    
    def update_overall_stats(self, daily_metrics: Dict[str, Any]):
        """Update overall performance statistics"""
        try:
            overall = self.performance_history['overall_stats']
            
            # Update cumulative stats
            overall['total_trades'] += daily_metrics.get('total_trades', 0)
            overall['winning_trades'] += daily_metrics.get('winning_trades', 0)
            overall['losing_trades'] += daily_metrics.get('losing_trades', 0)
            overall['total_pnl'] += daily_metrics.get('net_pnl', 0)
            
            # Calculate win rate
            total_trades = overall['total_trades']
            if total_trades > 0:
                overall['win_rate'] = round((overall['winning_trades'] / total_trades) * 100, 2)
            
            # Update drawdown (simplified calculation)
            daily_pnl = daily_metrics.get('net_pnl', 0)
            if daily_pnl < 0:
                overall['max_drawdown'] = min(overall.get('max_drawdown', 0), daily_pnl)
            
        except Exception as e:
            logger.error(f"Error updating overall stats: {e}")
    
    def generate_daily_report(self, date: str, metrics: Dict[str, Any]):
        """Generate daily performance report"""
        try:
            report_file = f"{self.trades_directory}daily_report_{date.replace('-', '')}.txt"
            
            report_content = f"""
DAILY TRADING REPORT - {date}
{'=' * 50}

TRADE SUMMARY:
- Total Trades: {metrics.get('total_trades', 0)}
- Winning Trades: {metrics.get('winning_trades', 0)}
- Losing Trades: {metrics.get('losing_trades', 0)}
- Win Rate: {metrics.get('win_rate', 0):.2f}%

PROFIT & LOSS:
- Gross P&L: ${metrics.get('gross_pnl', 0):.2f}
- Net P&L: ${metrics.get('net_pnl', 0):.2f}
- Total Fees: ${metrics.get('total_fees', 0):.2f}

TRADE ANALYSIS:
- Average Win: ${metrics.get('avg_win', 0):.2f}
- Average Loss: ${metrics.get('avg_loss', 0):.2f}
- Largest Win: ${metrics.get('largest_win', 0):.2f}
- Largest Loss: ${metrics.get('largest_loss', 0):.2f}
- Profit Factor: {metrics.get('profit_factor', 0):.2f}

VOLUME:
- Total Volume: {metrics.get('total_volume', 0):,} shares

OVERALL PERFORMANCE:
- Total P&L (All Time): ${self.performance_history['overall_stats'].get('total_pnl', 0):.2f}
- Total Trades (All Time): {self.performance_history['overall_stats'].get('total_trades', 0)}
- Overall Win Rate: {self.performance_history['overall_stats'].get('win_rate', 0):.2f}%
- Max Drawdown: ${self.performance_history['overall_stats'].get('max_drawdown', 0):.2f}

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with open(report_file, 'w') as f:
                f.write(report_content)
            
            logger.info(f"Daily report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """Get monthly performance summary"""
        try:
            month_key = f"{year}-{month:02d}"
            daily_data = self.performance_history.get('daily_performance', {})
            
            # Filter daily data for the month
            month_data = {k: v for k, v in daily_data.items() if k.startswith(month_key)}
            
            if not month_data:
                return {}
            
            # Aggregate monthly metrics
            total_trades = sum(day.get('total_trades', 0) for day in month_data.values())
            total_pnl = sum(day.get('net_pnl', 0) for day in month_data.values())
            winning_days = len([day for day in month_data.values() if day.get('net_pnl', 0) > 0])
            trading_days = len(month_data)
            
            return {
                'month': month_key,
                'trading_days': trading_days,
                'total_trades': total_trades,
                'total_pnl': round(total_pnl, 2),
                'winning_days': winning_days,
                'win_rate_days': round((winning_days / trading_days) * 100, 2) if trading_days > 0 else 0,
                'avg_daily_pnl': round(total_pnl / trading_days, 2) if trading_days > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly summary: {e}")
            return {}
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for last N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            daily_data = self.performance_history.get('daily_performance', {})
            
            # Filter data for the period
            period_data = {}
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                if date_str in daily_data:
                    period_data[date_str] = daily_data[date_str]
                current_date += timedelta(days=1)
            
            if not period_data:
                return {}
            
            # Calculate summary metrics
            total_pnl = sum(day.get('net_pnl', 0) for day in period_data.values())
            total_trades = sum(day.get('total_trades', 0) for day in period_data.values())
            winning_days = len([day for day in period_data.values() if day.get('net_pnl', 0) > 0])
            trading_days = len(period_data)
            
            daily_pnls = [day.get('net_pnl', 0) for day in period_data.values()]
            
            return {
                'period_days': days,
                'trading_days': trading_days,
                'total_trades': total_trades,
                'total_pnl': round(total_pnl, 2),
                'avg_daily_pnl': round(total_pnl / trading_days, 2) if trading_days > 0 else 0,
                'winning_days': winning_days,
                'win_rate_days': round((winning_days / trading_days) * 100, 2) if trading_days > 0 else 0,
                'best_day': round(max(daily_pnls), 2) if daily_pnls else 0,
                'worst_day': round(min(daily_pnls), 2) if daily_pnls else 0,
                'volatility': round(np.std(daily_pnls), 2) if daily_pnls else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
