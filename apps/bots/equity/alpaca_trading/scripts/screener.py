"""
Stock Screener for Moving Average Crossover Strategy

This module scans multiple stocks to identify potential trading opportunities based on
moving average crossovers and executes trades accordingly.
"""
import logging
import csv
import json
import os
import time
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

import pandas as pd
import numpy as np

try:
    from tqdm import tqdm  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    def tqdm(iterable, **kwargs):  # type: ignore
        return iterable
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame, APIError, Order

# Import local modules
from alpaca_trading.core.config import config
from alpaca_trading.core.notifier import notifier
from alpaca_trading.core.exceptions import DataError, TradingError
from alpaca_trading.scripts.trading_bot import TradingBot
from alpaca_trading.filters import (
    is_liquid,
    is_price_in_range,
    has_ma_crossover,
)
from alpaca_trading.report import TradeLogger
from alpaca_trading.data import MultiSourceDataProvider, create_data_provider

# Configure logger
logger = logging.getLogger(__name__)

class _LegacyTradeLogger:

    """Deprecated stub kept for backward import compatibility.\n\n    Use :class:`alpaca_trading.report.TradeLogger` instead.\n    """
    pass

    def __init__(self, log_dir: str = 'logs', log_file: str = 'trade_log.csv'):
        """Initialize the trade logger.
        
        Args:
            log_dir: Directory to store log files
            log_file: Name of the trade log file
        """
        # Create logs directory if it doesn't exist
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        self.log_file = self.log_dir / log_file
        self.fieldnames = [
            'timestamp', 'date', 'symbol', 'name', 'side', 'qty', 'price', 'amount',
            'order_id', 'status', 'reason', 'atr', 'atr_pct', 'volume_ratio'
        ]
        
        # Initialize the log file with header if it doesn't exist
        if not self.log_file.exists():
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def log_trade(self, trade_data: Dict[str, Any]) -> None:
        """Log a trade to the CSV file.
        
        Args:
            trade_data: Dictionary containing trade details with keys matching fieldnames
        """
        try:
            # Ensure all required fields are present
            trade_data.setdefault('timestamp', datetime.utcnow().isoformat())
            trade_data.setdefault('date', datetime.utcnow().strftime('%Y-%m-%d'))
            
            # Calculate amount if not provided
            if 'amount' not in trade_data and 'qty' in trade_data and 'price' in trade_data:
                trade_data['amount'] = trade_data['qty'] * trade_data['price']
            
            # Ensure all fieldnames are present in the trade data
            row = {field: trade_data.get(field, '') for field in self.fieldnames}
            
            # Write to CSV
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writerow(row)
                
            logger.info(f"Trade logged: {trade_data.get('symbol')} {trade_data.get('side').upper()} "
                      f"{trade_data.get('qty')} @ ${trade_data.get('price'):.2f}")
                      
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def get_trade_history(self, symbol: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Retrieve trade history from the log file.
        
        Args:
            symbol: Filter trades by symbol (optional)
            days: Number of days of history to retrieve
            
        Returns:
            List of trade records as dictionaries
        """
        try:
            if not self.log_file.exists():
                return []
                
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
            trades = []
            
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Skip trades older than cutoff date
                        trade_date = datetime.strptime(row.get('date', ''), '%Y-%m-%d').date()
                        if trade_date < cutoff_date:
                            continue
                            
                        # Filter by symbol if specified
                        if symbol and row.get('symbol') != symbol:
                            continue
                            
                        # Convert numeric fields
                        for field in ['qty', 'price', 'amount', 'atr', 'atr_pct', 'volume_ratio']:
                            if field in row and row[field]:
                                row[field] = float(row[field])
                        
                        trades.append(row)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing trade record: {e}")
                        continue
            
            # Sort by timestamp (newest first)
            return sorted(trades, key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Error reading trade history: {e}")
            return []
    
    def get_trade_summary(self, days: int = 30) -> Dict[str, Any]:
        """Generate a summary of trade performance.
        
        Args:
            days: Number of days to include in the summary
            
        Returns:
            Dictionary containing trade statistics
        """
        trades = self.get_trade_history(days=days)
        if not trades:
            return {}
            
        buy_trades = [t for t in trades if t['side'] == 'BUY']
        sell_trades = [t for t in trades if t['side'] == 'SELL']
        unique_symbols = len(set(t['symbol'] for t in trades))
        
        # Calculate win rate (simplified - assumes sell after buy is a complete trade)
        win_rate = 0
        if len(buy_trades) > 0 and len(sell_trades) > 0:
            win_rate = (len(sell_trades) / len(buy_trades)) * 100
            
        # Calculate P&L metrics
        trade_pairs = []
        for buy in buy_trades:
            symbol = buy['symbol']
            buy_price = float(buy['price'])
            buy_qty = float(buy['qty'])
            
            # Find matching sells for this buy
            matching_sells = [s for s in sell_trades if s['symbol'] == symbol]
            if matching_sells:
                sell = matching_sells[0]  # Simple pairing - first sell after buy
                sell_price = float(sell['price'])
                pnl = (sell_price - buy_price) * buy_qty
                pnl_pct = ((sell_price - buy_price) / buy_price) * 100
                trade_pairs.append({
                    'symbol': symbol,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'qty': buy_qty,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'duration_days': (datetime.fromisoformat(sell['timestamp']) - 
                                     datetime.fromisoformat(buy['timestamp'])).days
                })
        
        total_pnl = sum(t['pnl'] for t in trade_pairs)
        avg_pnl = total_pnl / len(trade_pairs) if trade_pairs else 0
        win_rate = len([t for t in trade_pairs if t['pnl'] > 0]) / len(trade_pairs) * 100 if trade_pairs else 0
        
        today = datetime.now().date()
        today_trades = [t for t in trades if datetime.fromisoformat(t['timestamp']).date() == today]
        today_pnl = sum((float(t['price']) * float(t['qty']) * (-1 if t['side'] == 'SELL' else 1)) 
                        for t in today_trades)
        
        return {
            'total_trades': len(trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'unique_symbols': unique_symbols,
            'total_volume': sum(float(t.get('qty', 0)) for t in trades),
            'total_amount': sum(float(t.get('amount', 0)) for t in trades if t.get('amount') is not None),
            'avg_trade_size': sum(float(t.get('amount', 0)) for t in trades) / len(trades) if trades else 0,
            'win_rate': min(win_rate, 100),  # Cap at 100%
            'last_trade': trades[0]['timestamp'] if trades else 'No trades',
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'today_trades': len(today_trades),
            'today_pnl': today_pnl,
            'trade_pairs': trade_pairs
        }
        
    def generate_daily_report(self) -> str:
        """Generate a formatted daily trading report.
        
        Returns:
            Formatted report string
        """
        summary = self.get_trade_summary(days=1)  # Get today's trades
        
        if not summary or summary['total_trades'] == 0:
            return "No trading activity today."
            
        report = []
        report.append("\n=== DAILY TRADING REPORT ===")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        report.append("-" * 30)
        
        # Summary
        report.append("📊 SUMMARY")
        report.append(f"Total Trades: {summary['total_trades']} ({summary['buy_trades']} buys, {summary['sell_trades']} sells)")
        report.append(f"Unique Symbols: {summary['unique_symbols']}")
        report.append(f"Total Volume: {summary['total_volume']:,.0f} shares")
        report.append(f"Total Amount: ${summary['total_amount']:,.2f}")
        report.append(f"Today's P&L: ${summary['today_pnl']:+,.2f}")
        report.append(f"Win Rate: {summary['win_rate']:.1f}%")
        
        # Today's Trades
        if 'trade_pairs' in summary and summary['trade_pairs']:
            report.append("\n💹 TRADE DETAILS")
            for trade in summary['trade_pairs']:
                report.append(
                    f"{trade['symbol']}: {trade['qty']} shares | "
                    f"Buy: ${trade['buy_price']:.2f} → Sell: ${trade['sell_price']:.2f} | "
                    f"P&L: ${trade['pnl']:+,.2f} ({trade['pnl_pct']:+.2f}%) | "
                    f"Held: {trade['duration_days']}d"
                )
        
        # Signals (last 5)
        recent_signals = self.get_trade_history(days=1)[:5]
        if recent_signals:
            report.append("\n🔔 RECENT SIGNALS")
            for signal in recent_signals:
                report.append(
                    f"{signal['timestamp'].split('T')[1][:8]} {signal['symbol']} {signal['side']} "
                    f"{signal['qty']} @ ${float(signal['price']):.2f} | {signal['reason']}"
                )
        
        report.append("\n📈 PORTFOLIO SNAPSHOT")
        # Add portfolio snapshot if available
        try:
            positions = self.api.list_positions()
            if positions:
                for pos in positions:
                    pnl_pct = (float(pos.market_value) - float(pos.cost_basis)) / float(pos.cost_basis) * 100
                    report.append(
                        f"{pos.symbol}: {pos.qty} shares | "
                        f"P&L: ${float(pos.unrealized_pl):+,.2f} ({pnl_pct:+.2f}%) | "
                        f"Value: ${float(pos.market_value):,.2f}"
                    )
            else:
                report.append("No open positions.")
        except Exception as e:
            report.append(f"Could not fetch portfolio: {str(e)}")
        
        report.append("=" * 30 + "\n")
        return "\n".join(report)

class StockScreener:
    def __init__(self, api: tradeapi.REST, min_price: float = 5.0, max_price: float = 1000.0,
                     min_volume: int = 250000, min_market_cap: float = 1e9,
                     log_dir: str = 'logs', manual_stocks: List[str] = None,
                     # Phase 1 Optimization Parameters (Low Risk)
                     rvol_fresh_threshold: float = 1.2,  # Reduced from 1.5x
                     rvol_continuation_threshold: float = 0.6,  # Reduced from 0.8x
                     institutional_ownership_threshold: float = 40.0,  # Reduced from 60%
                     short_interest_threshold: float = 15.0,  # Increased from 10%
                     # Phase 2 Parameters (for future use)
                     atr_fresh_threshold: float = 1.5,
                     atr_continuation_threshold: float = 1.2,
                     use_scoring_system: bool = False,
                     scoring_threshold: float = 70.0):
            """Initialize the stock screener.
            
            Args:
                api: Alpaca API client
                min_price: Minimum stock price to consider (dollars, default: $5.00)
                max_price: Maximum stock price to consider (dollars, default: $1000.00)
                min_volume: Legacy parameter - now uses tiered volume rules:
                           • ≥ 250K shares if price > $15
                           • ≥ 150K shares if $5 ≤ price ≤ $15
                           • Uses 20-day average volume for stability
                min_market_cap: Minimum market capitalization (dollars, default: $1B)
                log_dir: Directory to store trade logs
                manual_stocks: List of additional stock symbols to analyze (optional)
            """
            self.api = api
            self.min_price = min_price
            self.max_price = max_price
            self.min_volume = min_volume
            self.min_market_cap = min_market_cap
            
            # Phase 1 Optimization Thresholds (Low Risk)
            self.rvol_fresh_threshold = rvol_fresh_threshold
            self.rvol_continuation_threshold = rvol_continuation_threshold
            self.institutional_ownership_threshold = institutional_ownership_threshold
            self.short_interest_threshold = short_interest_threshold
            
            # Phase 2 Parameters (for future implementation)
            self.atr_fresh_threshold = atr_fresh_threshold
            self.atr_continuation_threshold = atr_continuation_threshold
            self.use_scoring_system = use_scoring_system
            self.scoring_threshold = scoring_threshold
            
            # Load manual stocks from file if not provided
            if manual_stocks is None:
                self.manual_stocks = self.load_manual_stocks_from_file()
            else:
                self.manual_stocks = set(manual_stocks)
            
            # Create combined universe for screening
            self.combined_universe = self.get_curated_stock_universe() | self.manual_stocks
            
            # Initialize multi-source data provider for robust data fetching
            self.data_provider = create_data_provider(self.api)
            
            self.trading_bot = TradingBot()
            self.volume_lookback_days = 30  # Days to calculate average volume
            self.trend_confirmation_periods = {
                '1Day': 20,    # 1 month of daily data
                '1Week': 13    # 3 months of weekly data
            }
            
            # Initialize trade logger
            self.trade_logger = TradeLogger(log_dir=log_dir)
            
            # Log manual stocks if provided
            if self.manual_stocks:
                logger.info(f"Manual stocks added to screening: {sorted(self.manual_stocks)}")
            
            # Log Phase 1 optimizations
            logger.info("📊 Phase 1 Screening Optimizations Active:")
            logger.info(f"  • RVOL Fresh Threshold: {self.rvol_fresh_threshold}x (was 1.5x)")
            logger.info(f"  • RVOL Continuation Threshold: {self.rvol_continuation_threshold}x (was 0.8x)")
            logger.info(f"  • Institutional Ownership: >{self.institutional_ownership_threshold}% (was >60%)")
            logger.info(f"  • Short Interest: <{self.short_interest_threshold}% (was <10%)")

    def get_20_week_ma(self, symbol: str) -> Optional[float]:
        """Get 20-week moving average using weekly data.
        
        Returns:
            float: 20-week MA value or None if insufficient data
        """
        try:
            # Get 25 weeks of weekly data (20 + buffer)
            weekly_bars = self.data_provider.get_bars(
                symbol,
                '1Week',
                limit=25
            )
            
            if weekly_bars is None or len(weekly_bars) < 20:
                logger.debug(f"Insufficient weekly data for {symbol}: {len(weekly_bars) if weekly_bars is not None else 0} bars")
                return None
            
            # Calculate 20-week MA
            weekly_bars['ma20'] = weekly_bars['close'].rolling(window=20).mean()
            ma20_weekly = weekly_bars['ma20'].iloc[-1]
            
            if pd.isna(ma20_weekly):
                return None
                
            logger.debug(f"20-week MA for {symbol}: ${ma20_weekly:.2f}")
            return ma20_weekly
            
        except Exception as e:
            logger.warning(f"Error calculating 20-week MA for {symbol}: {e}")
            return None
    
    def get_20_week_ma_daily(self, symbol: str) -> Optional[float]:
        """Get 20-week moving average equivalent using daily data (100-day MA).
        
        Returns:
            float: 100-day MA value (equivalent to 20-week MA) or None if insufficient data
        """
        try:
            # Get 120 days of daily data (100 + buffer for weekends/holidays)
            daily_bars = self.data_provider.get_bars(
                symbol,
                '1Day',
                limit=120
            )
            
            if daily_bars is None or len(daily_bars) < 100:
                logger.debug(f"Insufficient daily data for 100-day MA for {symbol}: {len(daily_bars) if daily_bars is not None else 0} bars")
                return None
            
            # Calculate 100-day MA (equivalent to 20-week MA)
            daily_bars['ma100'] = daily_bars['close'].rolling(window=100).mean()
            ma100_daily = daily_bars['ma100'].iloc[-1]
            
            if pd.isna(ma100_daily):
                return None
                
            logger.debug(f"100-day MA (20-week equivalent) for {symbol}: ${ma100_daily:.2f}")
            return ma100_daily
            
        except Exception as e:
            logger.warning(f"Error calculating 100-day MA for {symbol}: {e}")
            return None
    
    def check_higher_timeframe_trend(self, symbol: str) -> bool:
        """Check if the stock is in an uptrend on higher timeframes.
        
        Returns:
            bool: True if stock is in an uptrend (more lenient check)
        """
        try:
            # Try to get daily data first (more reliable than weekly)
            daily_bars = self.data_provider.get_bars(
                symbol,
                '1Day',
                limit=150  # Increased to support 20-week MA (~100 trading days + buffer)
            )
            
            if daily_bars is None or len(daily_bars) < 10:  # Reduced requirement
                logger.debug(f"Insufficient daily data for {symbol}, allowing pass")
                return True  # Be more permissive when data is unavailable
                
            # Simple trend check: price above 20-day moving average
            daily_bars['ma20'] = daily_bars['close'].rolling(window=20, min_periods=10).mean()
            
            last_day = daily_bars.iloc[-1]
            current_price = last_day['close']
            ma20 = last_day['ma20']
            
            # More lenient: just check if price is above 20-day MA
            if pd.isna(ma20):
                return True  # Allow pass if MA calculation fails
                
            is_uptrend = current_price > ma20
            
            logger.debug(f"Trend check for {symbol}: price=${current_price:.2f}, MA20=${ma20:.2f}, uptrend={is_uptrend}")
            return is_uptrend
            
        except Exception as e:
            logger.warning(f"Error checking higher timeframe trend for {symbol}: {e}")
            return True  # Be permissive on errors

    def get_avg_volume(self, symbol: str, lookback_days: int = 30) -> float:
        """Calculate average daily volume over the specified lookback period."""
        try:
            # Use multi-source data provider for robust volume data
            bars = self.data_provider.get_bars(
                symbol,
                '1Day',
                limit=lookback_days
            )
            
            if bars is None or len(bars) < 5:  # Need at least 5 days of data
                logger.debug(f"Insufficient volume data for {symbol}")
                return 0
                
            return bars['volume'].mean()
            
        except Exception as e:
            logger.warning(f"Error calculating avg volume for {symbol}: {e}")
            return 0

    def get_active_stocks(self, limit: int = None) -> List[Dict[str, Any]]:
        """Fetch a list of active stocks that meet all criteria.
        
        Args:
            limit: Maximum number of stocks to return. If None, returns all stocks.
        """
        try:
            # Use combined universe (curated + manual stocks) for better performance
            combined_symbols = self.combined_universe
            
            # Get all active assets but filter to combined list first
            assets = self.api.list_assets(status='active', asset_class='us_equity')
            
            # Filter to only combined symbols for faster processing
            filtered_assets = [asset for asset in assets if asset.symbol in combined_symbols]
            logger.info(f"Focusing on {len(filtered_assets)} combined stocks instead of {len(assets)} total stocks")
            
            # Filter stocks based on basic criteria
            filtered_stocks = []
            basic_filter_passed = 0
            price_data_passed = 0
            price_filter_passed = 0
            volume_filter_passed = 0
            trend_filter_passed = 0
            
            for asset in tqdm(filtered_assets, desc="Screening stocks"):
                try:
                    # Basic filters
                    if not (asset.tradable and asset.fractionable and 
                           asset.marginable and asset.shortable and
                           not asset.symbol.endswith(('.PR', '.PR.', '-', '^', '='))):
                        continue
                        
                    basic_filter_passed += 1
                        
                    # Get current price and volume data
                    latest_bar = self.api.get_latest_bar(asset.symbol)
                    if not latest_bar:
                        continue
                        
                    price_data_passed += 1
                        
                    current_price = latest_bar.close
                    
                    # Retrieve avg volume (used for filtering and later reporting)
                    avg_volume = self.get_avg_volume(asset.symbol, self.volume_lookback_days)
                    
                    # Fallback: if volume data unavailable, use reasonable defaults based on price
                    if avg_volume == 0:
                        if current_price > 100:
                            avg_volume = 1_000_000  # High-priced stocks typically have good volume
                        elif current_price > 50:
                            avg_volume = 500_000    # Mid-priced stocks
                        elif current_price > 10:
                            avg_volume = 200_000    # Lower-priced stocks
                        else:
                            avg_volume = 100_000    # Very low-priced stocks

                    # Apply price filter directly
                    if not (self.min_price <= current_price <= self.max_price):
                        continue
                        
                    price_filter_passed += 1
                        
                    # Apply liquidity filter directly using tiered volume requirements
                    if current_price > 15.0:
                        required_volume = 250_000  # Higher volume for higher-priced stocks
                    elif current_price >= 5.0:
                        required_volume = 150_000  # Lower volume for mid-cap stocks
                    else:
                        required_volume = self.min_volume  # Use configured minimum for low-priced stocks
                        
                    if avg_volume < required_volume:
                        continue
                        
                    volume_filter_passed += 1
                        
                    # Higher timeframe trend filter (re-enabled with improved logic)
                    if not self.check_higher_timeframe_trend(asset.symbol):
                        continue
                        
                    trend_filter_passed += 1
                    
                    # All filters passed, add to results
                    filtered_stocks.append({
                        'symbol': asset.symbol,
                        'name': asset.name,
                        'exchange': asset.exchange,
                        'price': current_price,
                        'avg_volume': avg_volume
                    })
                    
                    # Limit the number of stocks to process (if limit specified)
                    if limit is not None and len(filtered_stocks) >= limit:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error processing {getattr(asset, 'symbol', 'unknown')}: {e}")
                    continue
            
            # Log filter results for debugging
            logger.info(f"Filter results: {basic_filter_passed} basic, {price_data_passed} price data, "
                       f"{price_filter_passed} price range, {volume_filter_passed} volume, "
                       f"{trend_filter_passed} trend -> {len(filtered_stocks)} final")
            logger.info(f"Found {len(filtered_stocks)} stocks passing all filters")
            return filtered_stocks
            
        except Exception as e:
            logger.error(f"Error fetching active stocks: {e}")
            raise DataError(f"Failed to fetch active stocks: {e}")

    def get_curated_stock_universe(self) -> set:
        """Get the stock universe for screening.
        
        Now uses only manually added stocks, giving you complete control over
        your trading universe. Add stocks through the dashboard's Stock Universe tab.
        """
        # Use only manually added stocks
        universe = self.manual_stocks.copy()
        
        total_count = len(universe)
        
        logger.info(f"Stock universe: {total_count} manually added symbols")
        
        if universe:
            logger.info(f"Manual stocks included: {sorted(universe)}")
        else:
            logger.warning("⚠️ No stocks in universe! Add stocks via dashboard Stock Universe tab.")
        
        return universe

    def get_market_data(self, symbol: str, days: int = 90) -> Optional[pd.DataFrame]:
        """Fetch historical market data for a symbol using multi-source provider."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Use multi-source data provider for robust historical data
            bars = self.data_provider.get_bars(
                symbol,
                '1Day',
                start_date=start_date,
                end_date=end_date,
                limit=days
            )
            
            if bars is None or len(bars) < 20:  # Not enough data points
                logger.debug(f"Insufficient market data for {symbol}: {len(bars) if bars is not None else 0} bars")
                return None
                
            return bars
            
        except Exception as e:
            logger.warning(f"Could not fetch market data for {symbol}: {e}")
            return None

    def calculate_relative_volume(self, bars: pd.DataFrame, lookback_days: int = 20) -> float:
        """Calculate Relative Volume (RVOL) - current volume vs average volume."""
        try:
            if len(bars) < lookback_days + 1:
                return 0.0
            
            current_volume = bars['volume'].iloc[-1]
            avg_volume = bars['volume'].iloc[-(lookback_days+1):-1].mean()
            
            if avg_volume > 0:
                return current_volume / avg_volume
            return 0.0
        except Exception:
            return 0.0

    def calculate_atr_percentage(self, bars: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR as percentage of current price."""
        try:
            if len(bars) < period + 1:
                return 0.0
            
            # Calculate True Range
            bars['high_low'] = bars['high'] - bars['low']
            bars['high_close'] = abs(bars['high'] - bars['close'].shift(1))
            bars['low_close'] = abs(bars['low'] - bars['close'].shift(1))
            bars['true_range'] = bars[['high_low', 'high_close', 'low_close']].max(axis=1)
            
            # Calculate ATR
            atr = bars['true_range'].rolling(window=period).mean().iloc[-1]
            current_price = bars['close'].iloc[-1]
            
            if current_price > 0:
                return (atr / current_price) * 100  # Return as percentage
            return 0.0
        except Exception:
            return 0.0

    def calculate_relative_strength(self, symbol: str, bars: pd.DataFrame, benchmark: str = 'SPY') -> float:
        """Calculate Relative Strength vs benchmark (SPY)."""
        try:
            # Get benchmark data
            benchmark_bars = self.get_market_data(benchmark, days=90)
            if benchmark_bars is None or len(benchmark_bars) < 20:
                return 0.0
            
            # Align dates
            common_dates = bars.index.intersection(benchmark_bars.index)
            if len(common_dates) < 20:
                return 0.0
            
            stock_returns = bars.loc[common_dates]['close'].pct_change(20).iloc[-1]
            benchmark_returns = benchmark_bars.loc[common_dates]['close'].pct_change(20).iloc[-1]
            
            if pd.isna(stock_returns) or pd.isna(benchmark_returns):
                return 0.0
            
            # Return relative performance (positive = outperforming)
            return (stock_returns - benchmark_returns) * 100
        except Exception:
            return 0.0

    def get_fundamental_data(self, symbol: str) -> Dict[str, float]:
        """Get fundamental data including short interest and institutional ownership."""
        try:
            # This would typically require a fundamental data provider like Alpha Vantage, 
            # Polygon, or similar. For now, we'll use placeholder logic.
            # In production, you'd integrate with your preferred fundamental data source.
            
            # Placeholder implementation - you'll need to integrate with actual data source
            fundamentals = {
                'short_interest_pct': 5.0,  # Default to safe value
                'institutional_ownership_pct': 70.0,  # Default to safe value
                'market_cap': 1000000000,  # 1B default
            }
            
            # TODO: Replace with actual fundamental data API calls
            # Examples:
            # - Alpha Vantage: OVERVIEW endpoint
            # - Polygon: /v3/reference/tickers/{ticker}
            # - IEX Cloud: /stock/{symbol}/stats
            
            return fundamentals
        except Exception:
            return {
                'short_interest_pct': 15.0,  # Conservative default
                'institutional_ownership_pct': 50.0,  # Conservative default
                'market_cap': 500000000,
            }

    def check_earnings_calendar(self, symbol: str, days_buffer: int = 3) -> bool:
        """Check if stock has earnings within specified days buffer."""
        try:
            # This would typically require an earnings calendar API
            # For now, we'll use a placeholder that assumes no earnings conflicts
            
            # TODO: Integrate with earnings calendar API
            # Examples:
            # - Alpha Vantage: EARNINGS_CALENDAR
            # - Polygon: /v1/reference/earnings-calendar
            # - IEX Cloud: /stock/{symbol}/earnings
            
            # Placeholder: assume no earnings conflicts for now
            return False  # False means no earnings conflict
        except Exception:
            return True  # Conservative: assume earnings conflict if we can't check

    def get_bid_ask_spread(self, symbol: str) -> float:
        """Get current bid/ask spread as percentage of price."""
        try:
            # Get latest quote
            quote = self.api.get_latest_quote(symbol)
            if quote is None:
                return 100.0  # Large spread to filter out
            
            bid = float(quote.bid_price) if quote.bid_price else 0
            ask = float(quote.ask_price) if quote.ask_price else 0
            
            if bid > 0 and ask > 0:
                spread = ask - bid
                mid_price = (bid + ask) / 2
                return (spread / mid_price) * 100  # Return as percentage
            
            return 100.0  # Large spread to filter out
        except Exception:
            return 100.0  # Conservative: assume large spread if we can't get quote

    def enhanced_stock_filter(self, symbol: str, bars: pd.DataFrame) -> Dict[str, Any]:
        """Apply enhanced filtering criteria to a stock with configurable thresholds."""
        try:
            # 1. Relative Volume Filter (Phase 1: Reduced from 1.5x to 1.2x)
            rvol = self.calculate_relative_volume(bars)
            rvol_pass = rvol >= self.rvol_fresh_threshold  # Now configurable
            
            # 2. ATR Percentage Filter (>= 1.5% of price - will be configurable in Phase 2)
            atr_pct = self.calculate_atr_percentage(bars)
            atr_pass = atr_pct >= self.atr_fresh_threshold  # Using configurable threshold
            
            # 3. Relative Strength Filter (top 20% = RS > 0)
            rs_score = self.calculate_relative_strength(symbol, bars)
            rs_pass = rs_score > 0  # Outperforming market
            
            # 4. Fundamental Filters (Phase 1: Relaxed thresholds)
            fundamentals = self.get_fundamental_data(symbol)
            short_interest_pass = fundamentals['short_interest_pct'] < self.short_interest_threshold  # Increased to 15%
            institutional_pass = fundamentals['institutional_ownership_pct'] > self.institutional_ownership_threshold  # Reduced to 40%
            
            # 5. Earnings Calendar Filter
            earnings_pass = not self.check_earnings_calendar(symbol)
            
            # 6. Bid/Ask Spread Filter (< 0.5% of price)
            spread_pct = self.get_bid_ask_spread(symbol)
            spread_pass = spread_pct < 0.5
            
            # Compile results
            filters = {
                'rvol': rvol,
                'rvol_pass': rvol_pass,
                'atr_pct': atr_pct,
                'atr_pass': atr_pass,
                'rs_score': rs_score,
                'rs_pass': rs_pass,
                'short_interest_pct': fundamentals['short_interest_pct'],
                'short_interest_pass': short_interest_pass,
                'institutional_ownership_pct': fundamentals['institutional_ownership_pct'],
                'institutional_pass': institutional_pass,
                'earnings_pass': earnings_pass,
                'spread_pct': spread_pct,
                'spread_pass': spread_pass,
                'all_filters_pass': all([
                    rvol_pass, atr_pass, rs_pass, short_interest_pass,
                    institutional_pass, earnings_pass, spread_pass
                ])
            }
            
            return filters
            
        except Exception as e:
            logger.warning(f"Error in enhanced filtering for {symbol}: {e}")
            return {'all_filters_pass': False}

    def check_ma_crossover(self, symbol: str, short_window: int = 5, long_window: int = 20, 
                         volume_confirmation_bars: int = 20, atr_period: int = 14, 
                         min_atr_multiplier: float = 1.5, min_price_distance_pct: float = 0.01,
                         mode: str = 'auto') -> Optional[Dict[str, Any]]:
        """Check for moving average crossover in a stock with dual-mode detection.
        
        Args:
            symbol: Stock symbol to check
            short_window: Period for short moving average
            long_window: Period for long moving average
            volume_confirmation_bars: Number of previous bars to use for volume average
            atr_period: Period for Average True Range calculation
            min_atr_multiplier: Minimum ATR percentage (1.5% default)
            min_price_distance_pct: Minimum price distance from MA (as decimal, e.g., 0.01 for 1%)
            mode: Detection mode - 'fresh' (fresh crossovers), 'continuation' (established patterns), 'auto' (try both)
            
        Returns:
            Dict with trade signal and details if conditions met, None otherwise
        """
        try:
            # Get historical data
            bars = self.get_market_data(symbol)
            if bars is None or len(bars) < max(long_window, volume_confirmation_bars) + 1:
                return None
            
            # Calculate moving averages
            bars['short_ma'] = bars['close'].rolling(window=short_window).mean()
            bars['long_ma'] = bars['close'].rolling(window=long_window).mean()
            
            # Calculate enhanced indicators
            rvol = self.calculate_relative_volume(bars)
            atr_pct = self.calculate_atr_percentage(bars, atr_period)
            
            # Get the last two data points
            last_row = bars.iloc[-1]
            prev_row = bars.iloc[-2]
            
            # Skip if we don't have enough data for all indicators
            if pd.isna(last_row['short_ma']) or pd.isna(last_row['long_ma']):
                return None
            
            # Calculate price distance from MA
            price_distance_pct = (last_row['close'] - last_row['long_ma']) / last_row['long_ma']
            
            # Dual-mode detection logic
            signal = None
            reason_parts = []
            
            # Mode 1: Fresh Crossover Detection (original logic)
            if mode in ['fresh', 'auto']:
                fresh_bullish = (prev_row['short_ma'] <= prev_row['long_ma'] and 
                               last_row['short_ma'] > last_row['long_ma'])
                fresh_bearish = (prev_row['short_ma'] >= prev_row['long_ma'] and 
                               last_row['short_ma'] < last_row['long_ma'])
                
                if fresh_bullish:
                    close_above_ma = last_row['close'] > last_row['long_ma']
                    distance_ok = price_distance_pct >= min_price_distance_pct
                    rvol_ok = rvol >= self.rvol_fresh_threshold  # Configurable RVOL threshold
                    atr_ok = atr_pct >= min_atr_multiplier
                    
                    if close_above_ma and rvol_ok and distance_ok and atr_ok:
                        signal = 'BUY'
                        reason_parts.append(f"Fresh {short_window}MA crossed above {long_window}MA")
                        reason_parts.append("Close above MA")
                        reason_parts.append(f"RVOL: {rvol:.2f}x (threshold: {self.rvol_fresh_threshold}x)")
                        reason_parts.append(f"ATR: {atr_pct:.2f}%")
                        reason_parts.append(f"Price {price_distance_pct*100:.2f}% above MA")
                        
                elif fresh_bearish:
                    close_below_ma = last_row['close'] < last_row['long_ma']
                    distance_ok = abs(price_distance_pct) >= min_price_distance_pct
                    rvol_ok = rvol >= self.rvol_fresh_threshold  # Configurable RVOL threshold
                    atr_ok = atr_pct >= min_atr_multiplier
                    
                    if close_below_ma and rvol_ok and distance_ok and atr_ok:
                        signal = 'SELL'
                        reason_parts.append(f"Fresh {short_window}MA crossed below {long_window}MA")
                        reason_parts.append("Close below MA")
                        reason_parts.append(f"RVOL: {rvol:.2f}x (threshold: {self.rvol_fresh_threshold}x)")
                        reason_parts.append(f"ATR: {atr_pct:.2f}%")
                        reason_parts.append(f"Price {abs(price_distance_pct)*100:.2f}% below MA")
            
            # Mode 2: Golden Cross Continuation Detection (new logic for established patterns)
            if signal is None and mode in ['continuation', 'auto']:
                # Check for established golden cross (5MA > 20MA)
                golden_cross = last_row['short_ma'] > last_row['long_ma']
                death_cross = last_row['short_ma'] < last_row['long_ma']
                
                if golden_cross:
                    # AGGRESSIVE: Very relaxed requirements for established golden cross patterns
                    close_above_ma = last_row['close'] > last_row['long_ma']
                    distance_ok = price_distance_pct >= (min_price_distance_pct * 0.2)  # Only 0.2% distance required
                    rvol_ok = rvol >= 0.3  # Very low volume requirement (30% of average)
                    atr_ok = atr_pct >= 0.5  # Very low volatility requirement (0.5%)
                    
                    # Relaxed momentum check: allow slight downward MA movement
                    ma_momentum = last_row['short_ma'] >= (prev_row['short_ma'] * 0.995)  # Allow 0.5% decline
                    
                    if close_above_ma and distance_ok and rvol_ok and atr_ok and ma_momentum:
                        signal = 'BUY'
                        reason_parts.append(f"Golden Cross continuation ({short_window}MA > {long_window}MA)")
                        reason_parts.append("Close above MA with momentum")
                        reason_parts.append(f"RVOL: {rvol:.2f}x (continuation threshold: {self.rvol_continuation_threshold}x)")
                        reason_parts.append(f"ATR: {atr_pct:.2f}% (relaxed)")
                        reason_parts.append(f"Price {price_distance_pct*100:.2f}% above MA")
                        
                elif death_cross:
                    # Similar logic for bearish continuation
                    close_below_ma = last_row['close'] < last_row['long_ma']
                    distance_ok = abs(price_distance_pct) >= (min_price_distance_pct * 0.5)
                    rvol_ok = rvol >= self.rvol_continuation_threshold
                    atr_ok = atr_pct >= (min_atr_multiplier * 0.8)
                    ma_momentum = last_row['short_ma'] <= prev_row['short_ma']
                    
                    if close_below_ma and distance_ok and rvol_ok and atr_ok and ma_momentum:
                        signal = 'SELL'
                        reason_parts.append(f"Death Cross continuation ({short_window}MA < {long_window}MA)")
                        reason_parts.append("Close below MA with momentum")
                        reason_parts.append(f"RVOL: {rvol:.2f}x (continuation threshold: {self.rvol_continuation_threshold}x)")
                        reason_parts.append(f"ATR: {atr_pct:.2f}% (relaxed)")
                        reason_parts.append(f"Price {abs(price_distance_pct)*100:.2f}% below MA")
            
            if signal and reason_parts:
                return {
                    'symbol': symbol,
                    'price': last_row['close'],
                    'signal': signal,
                    'reason': ", ".join(reason_parts),
                    'short_ma': last_row['short_ma'],
                    'long_ma': last_row['long_ma'],
                    'volume': last_row['volume'],
                    'rvol': rvol,
                    'atr_pct': atr_pct,
                    'price_distance_pct': price_distance_pct,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking MA crossover for {symbol}: {e}")
            return None

    def screen_stocks(self, max_stocks: int = None) -> Dict[str, Any]:
        """Screen stocks for MA crossover opportunities with enhanced filtering.
        
        Now processes ALL stocks in the universe (no limit) for complete coverage.
        
        Args:
            max_stocks: Legacy parameter, now ignored. All stocks are processed.
        
        Returns:
            Dict containing:
            - opportunities: List of trading opportunities
            - screening_details: Detailed results for all stocks reviewed
        """
        logger.info("Starting stock screening with enhanced filters...")
        logger.info(f"Minimum Price: ${self.min_price:.2f}")
        logger.info("Volume Rules: ≥250K if price >$15, ≥150K if $5≤price≤$15 (20-day avg)")
        logger.info("🎯 Processing ALL stocks in universe (no limit)")
        
        # Get ALL active stocks that pass initial filters (no limit)
        stocks = self.get_active_stocks(limit=None)  # Process all stocks
        
        if not stocks:
            logger.warning("No stocks passed the initial filters")
            return {'opportunities': [], 'screening_details': []}
            
        logger.info(f"Analyzing {len(stocks)} filtered stocks for MA crossovers...")
        
        opportunities = []
        screening_details = []
        
        # Phase 1 Impact Tracking
        phase1_impact = {
            'rvol_relaxed_accepts': 0,  # Would have been rejected with old 1.5x threshold
            'institutional_relaxed_accepts': 0,  # Would have been rejected with old 60% threshold
            'short_interest_relaxed_accepts': 0,  # Would have been rejected with old 10% threshold
            'total_old_criteria_rejects': 0  # How many would have been rejected under old criteria
        }
        
        for stock in tqdm(stocks, desc="Analyzing stocks"):
            try:
                symbol = stock['symbol']
                stock_detail = {
                    'symbol': symbol,
                    'name': stock.get('name', 'N/A'),
                    'price': stock.get('price', 0),
                    'avg_volume': stock.get('avg_volume', 0),
                    'status': 'rejected',
                    'rejection_reasons': [],
                    'ma_crossover_result': None,
                    'enhanced_filters': None
                }
                
                # Check for MA crossover with dual-mode detection (auto mode tries both fresh and continuation)
                result = self.check_ma_crossover(symbol, mode='auto')
                stock_detail['ma_crossover_result'] = result
                
                if result:
                    # Apply enhanced filters
                    bars = self.get_market_data(symbol)
                    if bars is not None:
                        enhanced_filters = self.enhanced_stock_filter(symbol, bars)
                        stock_detail['enhanced_filters'] = enhanced_filters
                        
                        # TEMPORARY: Bypass enhanced filters for golden cross continuation signals
                        is_golden_cross_continuation = 'Golden Cross continuation' in result.get('reason', '')
                        
                        if enhanced_filters['all_filters_pass'] or is_golden_cross_continuation:
                            # Stock passed all filters - it's an opportunity
                            stock_detail['status'] = 'selected'
                            result.update({
                                'name': stock.get('name', 'N/A'),
                                'exchange': stock.get('exchange', 'N/A'),
                                'avg_volume': stock.get('avg_volume', 0)
                            })
                            opportunities.append(result)
                            logger.info(f"Opportunity found: {result['symbol']} - {result['signal']} at ${result['price']:.2f}")
                            
                            # Track Phase 1 impact - check if this would have been rejected under old criteria
                            rvol = enhanced_filters.get('rvol', 0)
                            institutional_pct = enhanced_filters.get('institutional_ownership_pct', 0)
                            short_interest_pct = enhanced_filters.get('short_interest_pct', 0)
                            
                            would_reject_old = False
                            if rvol < 1.5 and rvol >= self.rvol_fresh_threshold:
                                phase1_impact['rvol_relaxed_accepts'] += 1
                                would_reject_old = True
                            if institutional_pct <= 60.0 and institutional_pct > self.institutional_ownership_threshold:
                                phase1_impact['institutional_relaxed_accepts'] += 1
                                would_reject_old = True
                            if short_interest_pct >= 10.0 and short_interest_pct < self.short_interest_threshold:
                                phase1_impact['short_interest_relaxed_accepts'] += 1
                                would_reject_old = True
                            
                            if would_reject_old:
                                logger.info(f"📈 Phase 1 Benefit: {symbol} accepted due to relaxed criteria")
                        else:
                            # Failed enhanced filters
                            failed_filters = []
                            if not enhanced_filters.get('rvol_pass', True):
                                failed_filters.append(f"Low relative volume ({enhanced_filters.get('rvol', 0):.1f})")
                            if not enhanced_filters.get('atr_pass', True):
                                failed_filters.append(f"Low ATR ({enhanced_filters.get('atr_pct', 0):.1f}%)")
                            if not enhanced_filters.get('rs_pass', True):
                                failed_filters.append(f"Weak relative strength ({enhanced_filters.get('rs_score', 0):.1f})")
                            if not enhanced_filters.get('short_interest_pass', True):
                                failed_filters.append("High short interest")
                            if not enhanced_filters.get('institutional_pass', True):
                                failed_filters.append("Low institutional ownership")
                            if not enhanced_filters.get('earnings_pass', True):
                                failed_filters.append("Earnings announcement today")
                            if not enhanced_filters.get('spread_pass', True):
                                failed_filters.append(f"Wide bid-ask spread ({enhanced_filters.get('spread_pct', 0):.2f}%)")
                            stock_detail['rejection_reasons'] = failed_filters
                    else:
                        stock_detail['rejection_reasons'].append('No market data available')
                else:
                    stock_detail['rejection_reasons'].append('No MA crossover signal')
                
                screening_details.append(stock_detail)
                
                # Reduced sleep time for better performance with curated list
                time.sleep(0.05)  # Reduced from 0.2 to 0.05 seconds
            
            except Exception as e:
                logger.error(f"Error processing {stock.get('symbol', 'unknown')}: {e}")
                stock_detail['rejection_reasons'].append(f'Processing error: {str(e)}')
                screening_details.append(stock_detail)
                continue
        
        logger.info(f"Found {len(opportunities)} high-probability trading opportunities")
        
        # Log Phase 1 Impact Summary
        total_phase1_benefits = (phase1_impact['rvol_relaxed_accepts'] + 
                                phase1_impact['institutional_relaxed_accepts'] + 
                                phase1_impact['short_interest_relaxed_accepts'])
        
        if total_phase1_benefits > 0:
            logger.info("🎆 Phase 1 Optimization Impact Summary:")
            logger.info(f"  • Additional opportunities from RVOL relaxation: {phase1_impact['rvol_relaxed_accepts']}")
            logger.info(f"  • Additional opportunities from institutional threshold: {phase1_impact['institutional_relaxed_accepts']}")
            logger.info(f"  • Additional opportunities from short interest threshold: {phase1_impact['short_interest_relaxed_accepts']}")
            logger.info(f"  • Total additional opportunities: {total_phase1_benefits} ({total_phase1_benefits/len(opportunities)*100:.1f}% of total)")
        else:
            logger.info("📉 Phase 1 Impact: No additional opportunities from relaxed criteria this run")
        
        return {
            'opportunities': opportunities,
            'screening_details': screening_details,
            'phase1_impact': phase1_impact
        }
            
    def get_current_positions(self) -> Dict[str, Any]:
        """Get current portfolio positions with details."""
        try:
            positions = self.api.list_positions()
            return {
                'count': len(positions),
                'symbols': [p.symbol for p in positions],
                'positions': {p.symbol: float(p.market_value) for p in positions},
                'total_value': sum(float(p.market_value) for p in positions)
            }
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {'count': 0, 'symbols': [], 'positions': {}, 'total_value': 0}

    def calculate_position_size(self, account, symbol: str, price: float, atr: float, 
                             risk_per_trade: float = 0.01, max_position_pct: float = 0.05) -> int:
        """Calculate position size based on volatility and account risk parameters.
        Args:
            account: Alpaca account object
            symbol: Stock symbol
            price: Current price
            atr: Average True Range
            risk_per_trade: Percentage of account to risk per trade (default: 1%)
            max_position_pct: Maximum position size as percentage of portfolio (default: 5%)
            
        Returns:
            int: Number of shares to trade
        """
        try:
            # Get account equity and buying power
            equity = float(account.equity)
            buying_power = float(account.buying_power)
            
            # Calculate dollar risk amount (1% of equity)
            risk_amount = equity * risk_per_trade
            
            # Calculate position size based on ATR (2x ATR as stop loss)
            stop_loss_atr = atr * 2
            position_size_atr = (risk_amount / stop_loss_atr) if stop_loss_atr > 0 else 0
            
            # Calculate maximum position size based on account percentage
            max_position_size = buying_power * max_position_pct
            position_size_pct = max_position_size / price
            
            # Use the smaller of the two position sizes
            qty = min(position_size_atr, position_size_pct)
            
            # Round down to whole shares
            qty = int(qty)
            
            logger.info(f"Position size for {symbol}: {qty} shares "
                      f"(Risk: ${risk_amount:.2f}, ATR: {atr:.2f}, Price: ${price:.2f})")
            
            return max(0, qty)  # Ensure non-negative
            
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0

    def log_trade_execution(self, symbol: str, side: str, qty: int, price: float, 
                          order_id: str, status: str, reason: str = '', 
                          atr: float = None, atr_pct: float = None, 
                          volume_ratio: float = None) -> None:
        """Log trade execution details.
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Number of shares
            price: Execution price
            order_id: Alpaca order ID
            status: Order status
            reason: Reason for the trade
            atr: Average True Range
            atr_pct: ATR as percentage of price
            volume_ratio: Volume ratio (current/avg)
        """
        try:
            # Get stock name if available
            stock_info = next((s for s in self.get_active_stocks(limit=1000) 
                             if s['symbol'] == symbol), {})
            
            trade_data = {
                'symbol': symbol,
                'name': stock_info.get('name', ''),
                'side': side.upper(),
                'qty': qty,
                'price': price,
                'order_id': order_id,
                'status': status,
                'reason': reason,
                'atr': atr,
                'atr_pct': atr_pct,
                'volume_ratio': volume_ratio
            }
            
            self.trade_logger.log_trade(trade_data)
            
        except Exception as e:
            logger.error(f"Error logging trade execution for {symbol}: {e}")
    
    def _generate_and_log_daily_report(self) -> None:
        """Generate, log, and email the daily trading report."""
        try:
            report = self.trade_logger.generate_daily_report()
            if report:
                # Save to daily report file
                report_dir = Path('reports')
                report_dir.mkdir(exist_ok=True)
                
                report_file = report_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(report_file, 'w') as f:
                    f.write(report)
                
                # Print to console
                logger.info("\n" + "="*50)
                logger.info("DAILY TRADING SUMMARY")
                logger.info("="*50)
                for line in report.split('\n'):
                    if line.startswith(('===', '---', '📊', '💹', '🔔', '📈')):
                        logger.info(line)
                    else:
                        logger.info(f"  {line}")
                logger.info("="*50 + "\n")
                
                # Send email notification with the report
                try:
                    subject = f"Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}"
                    email_sent = notifier.send_email(subject, report)
                    if email_sent:
                        logger.info("✅ Daily report email sent successfully")
                    else:
                        logger.warning("Failed to send daily report email")
                except Exception as e:
                    logger.error(f"Error sending daily report email: {e}")
                
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
    
    def execute_trades(self, opportunities: List[Dict[str, Any]], 
                      max_positions: int = 10, 
                      generate_report: bool = True) -> None:
        """Execute trades based on screening results with position management.
        
        Args:
            opportunities: List of trading opportunities
            max_positions: Maximum number of positions to hold
            generate_report: Whether to generate a daily report after execution
        """
        if not opportunities:
            logger.info("No trading opportunities found.")
            if generate_report:
                # Still generate report to show daily activity
                self._generate_and_log_daily_report()
            return
        
        logger.info(f"Evaluating {len(opportunities)} opportunities...")
        
        # Get current account and position info
        account = self.api.get_account()
        positions = self.get_current_positions()
        
        # Sort opportunities by signal strength (e.g., volume ratio, price distance)
        opportunities.sort(key=lambda x: x.get('volume_ratio', 0) * abs(x.get('price_distance_pct', 0)), 
                          reverse=True)
        
        # Process each opportunity
        for opp in opportunities:
            try:
                symbol = opp['symbol']
                signal = opp['signal']
                price = opp['price']
                atr = opp.get('atr', 0)
                atr_pct = opp.get('atr_pct', 0)
                volume_ratio = opp.get('volume_ratio', 0)
                reason = opp.get('reason', '')
                
                # Skip if we've reached max positions and this is a new position
                current_pos_count = positions['count']
                if signal == 'BUY' and symbol not in positions['symbols']:
                    if current_pos_count >= max_positions:
                        logger.info(f"Max positions ({max_positions}) reached. Skipping {symbol}.")
                        continue
                
                if signal == 'BUY':
                    # Check if we already have a position
                    if symbol in positions['symbols']:
                        logger.info(f"Already have a position in {symbol}. Position size: ${positions['positions'].get(symbol, 0):.2f}")
                        continue
                    
                    # Calculate volatility-adjusted position size
                    qty = self.calculate_position_size(account, symbol, price, atr)
                    
                    if qty <= 0:
                        logger.warning(f"Invalid position size for {symbol}. Skipping.")
                        continue
                    
                    if qty > 0:
                        # Calculate position value and portfolio percentage
                        position_value = qty * price
                        portfolio_pct = (position_value / float(account.equity)) * 100
                        
                        logger.info(f"Buying {qty} shares of {symbol} at ~${price:.2f}")
                        logger.info(f"Signal details: {reason}")
                        logger.info(f"Position size: ${position_value:.2f} ({portfolio_pct:.2f}% of portfolio)")
                        
                        try:
                            # Generate client order ID with timestamp
                            client_order_id = f'buy_{symbol}_{int(time.time())}'
                            
                            # Submit buy order
                            order = self.api.submit_order(
                                symbol=symbol,
                                qty=qty,
                                side='buy',
                                type='market',
                                time_in_force='day',
                                client_order_id=client_order_id
                            )
                            
                            # Log the trade
                            self.log_trade_execution(
                                symbol=symbol,
                                side='buy',
                                qty=qty,
                                price=price,
                                order_id=order.id,
                                status=order.status,
                                reason=reason,
                                atr=atr,
                                atr_pct=atr_pct,
                                volume_ratio=volume_ratio
                            )
                            
                            logger.info(f"Buy order submitted: {order.id} - {order.status}")
                            
                            # Update positions count
                            positions['count'] += 1
                            positions['symbols'].append(symbol)
                            positions['positions'][symbol] = position_value
                            positions['total_value'] += position_value
                            
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"Error submitting buy order for {symbol}: {error_msg}")
                            
                            # Log the failed trade attempt
                            self.log_trade_execution(
                                symbol=symbol,
                                side='buy',
                                qty=qty,
                                price=price,
                                order_id='failed_' + str(int(time.time())),
                                status='failed',
                                reason=f"{reason} | Error: {error_msg}",
                                atr=atr,
                                atr_pct=atr_pct,
                                volume_ratio=volume_ratio
                            )
                    else:
                        logger.warning(f"Insufficient buying power or invalid position size for {symbol}")
                    
                elif signal == 'SELL':
                    # Check if we have a position to sell
                    if symbol in positions['symbols']:
                        try:
                            position = self.api.get_position(symbol)
                            qty = int(float(position.qty))
                            
                            if qty > 0:
                                position_value = float(position.market_value)
                                logger.info(f"Selling {qty} shares of {symbol} (Position value: ${position_value:.2f})")
                                logger.info(f"Signal details: {reason}")
                                
                                try:
                                    # Generate client order ID with timestamp
                                    client_order_id = f'sell_{symbol}_{int(time.time())}'
                                    
                                    # Submit sell order
                                    order = self.api.submit_order(
                                        symbol=symbol,
                                        qty=qty,
                                        side='sell',
                                        type='market',
                                        time_in_force='day',
                                        client_order_id=client_order_id
                                    )
                                    
                                    # Log the trade
                                    self.log_trade_execution(
                                        symbol=symbol,
                                        side='sell',
                                        qty=qty,
                                        price=price,
                                        order_id=order.id,
                                        status=order.status,
                                        reason=reason,
                                        atr=atr,
                                        atr_pct=atr_pct,
                                        volume_ratio=volume_ratio
                                    )
                                    
                                    logger.info(f"Sell order submitted: {order.id} - {order.status}")
                                    
                                    # Update positions count
                                    positions['count'] = max(0, positions['count'] - 1)
                                    positions['symbols'].remove(symbol)
                                    positions['positions'].pop(symbol, None)
                                    positions['total_value'] = max(0, positions['total_value'] - position_value)
                                    
                                except Exception as e:
                                    error_msg = str(e)
                                    logger.error(f"Error submitting sell order for {symbol}: {error_msg}")
                                    
                                    # Log the failed trade attempt
                                    self.log_trade_execution(
                                        symbol=symbol,
                                        side='sell',
                                        qty=qty,
                                        price=price,
                                        order_id='failed_' + str(int(time.time())),
                                        status='failed',
                                        reason=f"{reason} | Error: {error_msg}",
                                        atr=atr,
                                        atr_pct=atr_pct,
                                        volume_ratio=volume_ratio
                                    )
                            else:
                                logger.warning(f"Invalid position quantity for {symbol}")
                                
                        except Exception as e:
                            logger.warning(f"Error getting position for {symbol}: {e}")
                    else:
                        logger.info(f"No position to sell in {symbol}")
                        
                    # Log trade summary after processing all opportunities
                    if opportunities:
                        summary = self.trade_logger.get_trade_summary(days=7)
                        if summary:
                            logger.info("\n=== Trade Summary (Last 7 Days) ===")
                            logger.info(f"Total Trades: {summary['total_trades']}")
                            logger.info(f"Buy Trades: {summary['buy_trades']}")
                            logger.info(f"Sell Trades: {summary['sell_trades']}")
                            logger.info(f"Unique Symbols: {summary['unique_symbols']}")
                            logger.info(f"Total Volume: {summary['total_volume']:,.0f} shares")
                            logger.info(f"Total Amount: ${summary['total_amount']:,.2f}")
                            logger.info(f"Average Trade Size: ${summary['avg_trade_size']:,.2f}")
                            logger.info(f"Win Rate: {summary['win_rate']:.1f}%")
                            logger.info(f"Last Trade: {summary['last_trade']}")
                            logger.info("===============================\n")
                
                # Be nice to the API
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error executing trade for {opp.get('symbol', 'unknown')}: {e}")

    def load_manual_stocks_from_file(self, config_dir: str = None) -> set:
        """Load manual stocks from config file or dashboard JSON file.
        
        Args:
            config_dir: Directory containing manual_stocks.txt (optional)
            
        Returns:
            Set of manual stock symbols
        """
        if config_dir is None:
            # Default to project root directory
            project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        else:
            project_root = config_dir
        
        manual_stocks = set()
        
        # First, try to load from dashboard JSON file (primary source)
        dashboard_json_file = os.path.join(project_root, 'manual_stocks.json')
        if os.path.exists(dashboard_json_file):
            try:
                with open(dashboard_json_file, 'r') as f:
                    data = json.load(f)
                    stocks = data.get('stocks', [])
                    for symbol in stocks:
                        symbol = str(symbol).upper().strip()
                        if symbol.isalpha() and len(symbol) <= 5:  # Basic validation
                            manual_stocks.add(symbol)
                        else:
                            logger.warning(f"Invalid manual stock symbol from JSON: {symbol}")
                
                logger.info(f"✅ Loaded {len(manual_stocks)} manual stocks from dashboard JSON file")
                return manual_stocks
                
            except Exception as e:
                logger.error(f"Error loading manual stocks from JSON file: {e}")
        
        # Fallback to config/manual_stocks.txt file
        config_dir = os.path.join(project_root, 'config')
        manual_stocks_file = os.path.join(config_dir, 'manual_stocks.txt')
        if os.path.exists(manual_stocks_file):
            try:
                with open(manual_stocks_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            symbol = line.upper()
                            if symbol.isalpha() and len(symbol) <= 5:  # Basic validation
                                manual_stocks.add(symbol)
                            else:
                                logger.warning(f"Invalid manual stock symbol from TXT: {line}")
                
                logger.info(f"📄 Loaded {len(manual_stocks)} manual stocks from config TXT file")
                
            except Exception as e:
                logger.error(f"Error loading manual stocks from TXT file: {e}")
        else:
            logger.warning(f"⚠️ No manual stocks files found. Checked: {dashboard_json_file}, {manual_stocks_file}")
        
        return manual_stocks
    
    def reload_manual_stocks(self, config_dir: str = None) -> Dict[str, Any]:
        """Reload manual stocks from file and update the screener.
        
        Args:
            config_dir: Directory containing manual_stocks.txt (optional)
            
        Returns:
            Dictionary with reload results including changes detected
        """
        logger.info("🔄 Reloading manual stocks from file...")
        
        # Store previous state
        previous_manual_stocks = self.manual_stocks.copy()
        
        # Reload from file
        new_manual_stocks = self.load_manual_stocks_from_file(config_dir)
        
        # Detect changes
        added_stocks = new_manual_stocks - previous_manual_stocks
        removed_stocks = previous_manual_stocks - new_manual_stocks
        
        # Update screener state
        self.manual_stocks = new_manual_stocks
        self.combined_universe = self.get_curated_stock_universe() | self.manual_stocks
        
        # Log changes
        changes_detected = bool(added_stocks or removed_stocks)
        if changes_detected:
            logger.info("📈 Manual stock changes detected:")
            if added_stocks:
                logger.info(f"  ➕ Added: {sorted(added_stocks)}")
            if removed_stocks:
                logger.info(f"  ➖ Removed: {sorted(removed_stocks)}")
        else:
            logger.info("📄 No changes detected in manual stocks")
        
        result = {
            'changed': changes_detected,
            'previous_count': len(previous_manual_stocks),
            'current_count': len(new_manual_stocks),
            'added': added_stocks,
            'removed': removed_stocks,
            'current_stocks': new_manual_stocks
        }
        
        logger.info(f"✅ Manual stocks reload complete: {len(new_manual_stocks)} stocks loaded")
        return result

def run_screener(manual_stocks: List[str] = None):
    """Run the stock screener and execute trades based on MA crossover signals.
    
    Args:
        manual_stocks: Optional list of additional stock symbols to analyze
    """
    # Initialize API
    api = tradeapi.REST(
        config.api_key,
        config.api_secret,
        base_url=config.base_url or 'https://paper-api.alpaca.markets',
        api_version='v2'
    )
    
    # Initialize screener with optional manual stocks
    screener = StockScreener(api, manual_stocks=manual_stocks)
    
    # Screen for opportunities
    opportunities = screener.screen_stocks(max_stocks=100)
    
    # Execute trades
    screener.execute_trades(opportunities)
    
    return opportunities

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('screener.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        opportunities = run_screener(manual_stocks=['AAPL', 'GOOG'])
        print(f"\nFound {len(opportunities)} trading opportunities:")
        for opp in opportunities:
            print(f"{opp['signal']} {opp['symbol']} at ${opp['price']:.2f} - {opp['reason']}")
    except Exception as e:
        logging.error(f"Error in screener: {e}", exc_info=True)
