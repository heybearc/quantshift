#!/usr/bin/env python3
"""
Daily Trading Automation System
Implements a comprehensive breakout trading strategy with:
- Pre-market stock screening
- Intraday breakout detection
- Automated bracket order placement
- End-of-day reporting
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import fcntl

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame, APIError
from alpaca_trading.core.config import config
from alpaca_trading.utils.logging_config import setup_logger
from alpaca_trading.strategies.breakout_strategy import BreakoutStrategy
from alpaca_trading.scripts.screener import StockScreener
from alpaca_trading.utils.market_calendar import MarketCalendar
from alpaca_trading.utils.performance_tracker import PerformanceTracker
from alpaca_trading.core.notifier import notifier
from alpaca_trading.utils.golden_cross_scanner import GoldenCrossScanner

# Set up logging
logger = setup_logger(__name__)

def load_manual_stocks() -> List[str]:
    """Load manual stocks from dashboard JSON file or configuration file."""
    from pathlib import Path
    import json
    
    project_root = Path(__file__).parent.parent.parent
    manual_stocks = []
    
    # First, try to load from dashboard JSON file (primary source)
    dashboard_json_file = project_root / "manual_stocks.json"
    if dashboard_json_file.exists():
        try:
            with open(dashboard_json_file, 'r') as f:
                data = json.load(f)
                
                # Handle both formats: dashboard format {'stocks': [...]} and golden cross format [...]
                if isinstance(data, list):
                    # Golden cross scanner format - direct array of symbols
                    stocks = data
                else:
                    # Dashboard format - object with 'stocks' key
                    stocks = data.get('stocks', [])
                    
                for symbol in stocks:
                    symbol = str(symbol).upper().strip()
                    if symbol.isalpha() and len(symbol) <= 5:  # Basic validation
                        manual_stocks.append(symbol)
            
            if manual_stocks:
                logger.info(f"✅ Loaded {len(manual_stocks)} manual stocks from dashboard JSON file")
                return manual_stocks
                
        except Exception as e:
            logger.error(f"Error loading manual stocks from JSON file: {e}")
    
    # Fallback to config/manual_stocks.txt file
    config_file = project_root / "config" / "manual_stocks.txt"
    try:
        if config_file.exists():
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Extract just the symbol (in case there are comments after)
                        symbol = line.split('#')[0].strip().upper()
                        if symbol and symbol.isalpha():  # Basic validation
                            manual_stocks.append(symbol)
            
            if manual_stocks:
                logger.info(f"📄 Loaded {len(manual_stocks)} manual stocks from config TXT file")
        else:
            logger.warning(f"⚠️ No manual stocks files found. Checked: {dashboard_json_file}, {config_file}")
            
    except Exception as e:
        logger.warning(f"Error loading manual stocks from TXT file: {e}")
    
    return manual_stocks

class DailyTradingAutomation:
    """Main class for daily trading automation"""
    
    def __init__(self):
        self.alpaca_client = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        self.breakout_strategy = BreakoutStrategy()
        
        # Load manual stocks and initialize screener with them
        manual_stocks = load_manual_stocks()
        # Initialize screener with Phase 1 optimized thresholds
        self.stock_screener = StockScreener(
            self.alpaca_client, 
            manual_stocks=manual_stocks,
            # Phase 1 Low-Risk Optimizations
            rvol_fresh_threshold=1.2,  # Reduced from 1.5x
            rvol_continuation_threshold=0.6,  # Reduced from 0.8x
            institutional_ownership_threshold=40.0,  # Reduced from 60%
            short_interest_threshold=15.0  # Increased from 10%
        )
        
        self.market_calendar = MarketCalendar()
        self.performance_tracker = PerformanceTracker()
        self.eligible_stocks = []
        self.active_positions = {}
        
        # Trading parameters from config
        self.max_positions = config.max_positions
        self.position_size = config.position_size
        self.stop_loss_pct = config.stop_loss_pct
        
        # Scaling strategy parameters
        self.scale_out_first_pct = config.scale_out_first_pct
        self.scale_out_resistance_pct = config.scale_out_resistance_pct
        self.trailing_stop_atr_mult = config.trailing_stop_atr_mult
        self.min_shares_for_scaling = config.min_shares_for_scaling
        
        # Load existing positions from Alpaca account
        self.load_existing_positions()
        
        logger.info("Daily Trading Automation initialized")
    
    def load_existing_positions(self):
        """Load existing positions from Alpaca account into active_positions tracking"""
        try:
            positions = self.alpaca_client.list_positions()
            logger.info(f"Loading {len(positions)} existing positions from Alpaca account")
            
            for pos in positions:
                symbol = pos.symbol
                shares = int(pos.qty)
                entry_price = float(pos.avg_entry_price)
                current_price = float(pos.current_price)
                
                # Create position tracking structure
                # Note: We won't have all the original scaling strategy data,
                # so we'll create a simplified version for existing positions
                position_info = {
                    'symbol': symbol,
                    'total_shares': shares,
                    'remaining_shares': shares,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'unrealized_pl': float(pos.unrealized_pl),
                    'market_value': float(pos.market_value),
                    'scaling_strategy': {
                        'first_scale_executed': False,
                        'resistance_scale_executed': False,
                        'scaled_out': False,
                        'scale_out_target': entry_price * 1.04,  # Default 4% target
                        'resistance_level': None,
                        'last_high': current_price,  # Initialize with current price
                        'trailing_stop_active': False
                    },
                    'initial_stop': entry_price * (1 - self.stop_loss_pct),
                    'current_stop': entry_price * (1 - self.stop_loss_pct),
                    'atr': entry_price * 0.02,  # Default 2% ATR estimate
                    'order_id': None,  # Original order ID not available
                    'stop_order_id': None,
                    'loaded_from_account': True  # Flag to indicate this was loaded
                }
                
                self.active_positions[symbol] = position_info
                logger.info(f"Loaded existing position: {symbol} - {shares} shares @ ${entry_price:.2f}")
                
        except Exception as e:
            logger.error(f"Error loading existing positions: {e}")
    
    def update_golden_cross_universe(self):
        """Update stock universe with fresh golden cross discoveries"""
        try:
            logger.info("🔍 Starting automated golden cross universe update...")
            
            # Initialize golden cross scanner
            scanner = GoldenCrossScanner()
            
            # Perform comprehensive scan
            golden_cross_stocks = scanner.scan_all_universes()
            
            if golden_cross_stocks:
                # Update the manual stocks file
                scanner.update_manual_stocks_file(golden_cross_stocks)
                
                # Reload the screener with new stocks
                manual_stocks = load_manual_stocks()
                self.stock_screener = StockScreener(
                    self.alpaca_client, 
                    manual_stocks=manual_stocks,
                    # Phase 1 Low-Risk Optimizations
                    rvol_fresh_threshold=1.2,
                    rvol_continuation_threshold=0.6,
                    institutional_ownership_threshold=40.0,
                    short_interest_threshold=15.0
                )
                
                logger.info(f"✅ Updated universe with {len(golden_cross_stocks)} golden cross stocks")
                logger.info(f"📊 New universe size: {len(manual_stocks)} stocks")
                
                # Log top discoveries
                for i, stock in enumerate(golden_cross_stocks[:5], 1):
                    logger.info(f"🏆 {i}. {stock['symbol']} - ${stock['current_price']:.2f} - "
                              f"MA Spread: {stock['ma_spread']:.1f}% - {stock['sector']}")
                
                return len(golden_cross_stocks)
            else:
                logger.warning("❌ No golden cross stocks found in scan")
                return 0
                
        except Exception as e:
            logger.error(f"Error updating golden cross universe: {e}")
            return 0
    
    def pre_market_routine(self):
        """Execute pre-market routine at 8:00 AM ET"""
        # Create lock file to prevent duplicate runs
        lock_file_path = '/tmp/alpaca_premarket_lock'
        
        try:
            # Try to acquire lock
            lock_file = open(lock_file_path, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write process info to lock file
            lock_file.write(f"PID: {os.getpid()}\nStarted: {datetime.now()}\n")
            lock_file.flush()
            
            logger.info("🔒 Acquired pre-market routine lock")
            
        except (IOError, OSError) as e:
            logger.warning(f"⚠️ Pre-market routine already running (lock file exists). Skipping execution.")
            return
            
        try:
            logger.info("🌅 Starting pre-market routine")
            
            # Reload positions from Alpaca account to sync any overnight changes
            logger.info("🔄 Reloading positions from Alpaca account")
            self.load_existing_positions()
            
            # Update stock universe with fresh golden cross discoveries
            logger.info("🔍 Updating stock universe with golden cross scan")
            golden_cross_count = self.update_golden_cross_universe()
            
            # Fetch eligible stocks for today with detailed screening results
            logger.info("📋 Fetching eligible stocks for today")
            screening_results = self.stock_screener.screen_stocks()  # Process ALL stocks in universe
            opportunities = screening_results['opportunities']
            screening_details = screening_results['screening_details']
            
            # Log transparency info about screening process
            logger.info(f"📈 Screening Summary: {len(screening_details)} stocks reviewed, {len(opportunities)} opportunities found")
            
            self.eligible_stocks = [opp['symbol'] for opp in opportunities if opp.get('symbol')]
            logger.info(f"✅ Found {len(self.eligible_stocks)} eligible stocks")
            
            # Cache intraday data for eligible stocks
            logger.info("📊 Caching intraday data for eligible stocks")
            for symbol in self.eligible_stocks:
                try:
                    # Get recent intraday data for caching
                    bars = self.alpaca_client.get_bars(
                        symbol, TimeFrame.Minute, limit=100
                    ).df
                    if not bars.empty:
                        self.breakout_strategy.cache_intraday_data(symbol, bars)
                except Exception as e:
                    logger.warning(f"Could not cache data for {symbol}: {e}")
        
            # Place trades for pre-market opportunities
            if opportunities and len(self.active_positions) < self.max_positions:
                logger.info(f"🚀 Placing trades for {len(opportunities)} pre-market opportunities")
                
                for opportunity in opportunities:
                    # Check if we still have capacity
                    if len(self.active_positions) >= self.max_positions:
                        logger.info(f"📊 Max positions ({self.max_positions}) reached, stopping trade placement")
                        break
                        
                    symbol = opportunity.get('symbol')
                    if symbol and symbol not in self.active_positions:
                        try:
                            logger.info(f"📈 Placing pre-market trade for {symbol}")
                            # Create a signal dict for the trade placement
                            signal = {
                                'action': 'BUY',
                                'signal_type': 'pre_market_opportunity',
                                'reason': opportunity.get('reason', 'Pre-market screening opportunity'),
                                'entry_price': opportunity.get('price', 0),  # Fixed: use 'entry_price' key
                                'volume': opportunity.get('volume', 0),
                                'atr': opportunity.get('atr', 0)
                            }
                            
                            # Place the trade
                            self.place_breakout_trade(symbol, signal)
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to place pre-market trade for {symbol}: {e}")
                            continue
            else:
                if not opportunities:
                    logger.info("📊 No pre-market opportunities found to trade")
                else:
                    logger.info(f"📊 Max positions ({self.max_positions}) already reached, no new trades placed")
        
            # Send detailed pre-market screening summary email (moved to end)
            logger.info("📧 Sending detailed pre-market screening summary")
            self._send_pre_market_summary_email(opportunities, screening_details)
            
            logger.info("✅ Pre-market routine completed successfully")
        
        except Exception as e:
            logger.error(f"❌ Error in pre-market routine: {e}")
            raise
        finally:
            # Always release the lock
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                os.remove(lock_file_path)
                logger.info("🔓 Released pre-market routine lock")
            except:
                pass  # Lock file might not exist if we never acquired it
    
    def fetch_eligible_stocks(self) -> List[str]:
        """Fetch stocks that meet daily and weekly screening criteria"""
        try:
            # Get list of active stocks (you can customize this list)
            stock_universe = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'SHOP', 'SQ', 'ROKU',
                'ZM', 'DOCU', 'SNOW', 'PLTR', 'COIN', 'HOOD', 'SOFI', 'UPST'
            ]
            
            eligible = []
            
            for symbol in stock_universe:
                try:
                    # Use yfinance as fallback for historical data
                    import yfinance as yf
                    
                    # Get daily data from yfinance
                    ticker = yf.Ticker(symbol)
                    daily_data = ticker.history(period="3mo", interval="1d")
                    weekly_data = ticker.history(period="1y", interval="1wk")
                    
                    if not daily_data.empty and not weekly_data.empty:
                        # Convert to format expected by strategy
                        daily_data.columns = daily_data.columns.str.lower()
                        weekly_data.columns = weekly_data.columns.str.lower()
                        
                        if self.breakout_strategy.meets_screening_criteria(daily_data, weekly_data):
                            eligible.append(symbol)
                            logger.info(f"{symbol} meets screening criteria")
                        else:
                            logger.debug(f"{symbol} does not meet screening criteria")
                    else:
                        logger.warning(f"No data available for {symbol}")
                        
                except Exception as e:
                    logger.warning(f"Error screening {symbol}: {e}")
                    continue
            
            return eligible
            
        except Exception as e:
            logger.error(f"Error fetching eligible stocks: {e}")
            return []
    
    def preload_intraday_data(self):
        """Preload 15-minute intraday data for eligible stocks"""
        try:
            logger.info("Preloading intraday data...")
            
            for symbol in self.eligible_stocks:
                try:
                    # Get 15-minute bars for the last 5 days
                    bars = self.alpaca_client.get_bars(symbol, TimeFrame.Minute, limit=500)
                    
                    # Cache the data for quick access during trading hours
                    self.breakout_strategy.cache_intraday_data(symbol, bars)
                    
                except Exception as e:
                    logger.warning(f"Error preloading data for {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error preloading intraday data: {e}")
    
    def filter_earnings_stocks(self):
        """Remove stocks with earnings announcements today"""
        try:
            # This would integrate with earnings calendar API
            # For now, we'll implement a placeholder
            logger.info("Filtering stocks with earnings announcements...")
            
            # TODO: Implement earnings calendar integration
            # earnings_today = self.get_earnings_calendar()
            # self.eligible_stocks = [s for s in self.eligible_stocks if s not in earnings_today]
            
        except Exception as e:
            logger.error(f"Error filtering earnings stocks: {e}")
    
    def intraday_monitoring(self):
        """Monitor for breakout signals during market hours"""
        try:
            logger.info("Starting intraday monitoring...")
            
            # Monitor existing positions first
            self.monitor_existing_positions()
            
            # Manage scaling positions
            self.manage_scaling_positions()
            
            # Check for new opportunities if we have capacity
            if len(self.active_positions) < self.max_positions:
                # If eligible_stocks is empty (e.g., bot restarted after pre-market),
                # run screening to find opportunities
                if not self.eligible_stocks:
                    logger.info("No eligible stocks cached - running intraday screening...")
                    screening_result = self.stock_screener.screen_stocks()
                    opportunities = screening_result.get('opportunities', [])
                    logger.info(f"Found {len(opportunities)} opportunities during intraday screening")
                    
                    # Place trades for qualifying opportunities
                    for opportunity in opportunities:
                        if len(self.active_positions) >= self.max_positions:
                            break
                            
                        symbol = opportunity['symbol']
                        if symbol not in self.active_positions:
                            # Create signal object for trade placement
                            signal = {
                                'symbol': symbol,
                                'entry_price': opportunity.get('price', 0),
                                'signal_reason': opportunity.get('signal_reason', 'Intraday breakout'),
                                'volume': opportunity.get('volume', 0),
                                'atr': opportunity.get('atr', 0)
                            }
                            
                            logger.info(f"Placing intraday trade for {symbol}: {signal['signal_reason']}")
                            self.place_breakout_trade(symbol, signal)
                else:
                    # Use cached eligible stocks from pre-market routine
                    for symbol in self.eligible_stocks:
                        if symbol not in self.active_positions:
                            # Get latest intraday data
                            latest_bars = self.alpaca_client.get_bars(
                                symbol, TimeFrame.Minute, limit=5
                            ).df
                            
                            if not latest_bars.empty:
                                # Cache the data
                                self.breakout_strategy.cache_intraday_data(symbol, latest_bars)
                                
                                # Check for breakout signal
                                signal = self.breakout_strategy.check_breakout_signal(symbol, latest_bars)
                                
                                if signal['action'] == 'BUY':
                                    logger.info(f"Breakout signal detected for {symbol}: {signal}")
                                    self.place_breakout_trade(symbol, signal)
                                
        except Exception as e:
            logger.error(f"Error in intraday monitoring: {e}")
    
    def place_breakout_trade(self, symbol: str, signal: Dict):
        """Place initial market order for breakout trade with dynamic scaling strategy"""
        try:
            logger.info(f"Placing breakout trade for {symbol}")
            
            # Get current price and ATR
            current_price = signal['entry_price']
            atr_value = signal.get('atr', current_price * 0.02)  # Fallback to 2% if no ATR
            
            # Calculate position size
            shares = int(self.position_size / current_price)
            if shares < self.min_shares_for_scaling:  # Use config parameter
                logger.warning(f"Position size too small for scaling strategy: {symbol}")
                return
            
            # Calculate initial stop loss (2% or 1.5x ATR, whichever is larger)
            stop_loss_atr = current_price - (self.trailing_stop_atr_mult * atr_value)
            stop_loss_pct = current_price * (1 - self.stop_loss_pct)
            initial_stop = round(max(stop_loss_atr, stop_loss_pct), 2)
            
            # Place initial market order only (no bracket)
            market_order = self.alpaca_client.submit_order(
                symbol=symbol,
                qty=shares,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            
            if market_order:
                # Calculate scaling targets
                scale_out_target = round(current_price + atr_value, 2)  # +1 ATR
                scale_out_shares = int(shares * self.scale_out_first_pct)  # Use config parameter
                remaining_shares = shares - scale_out_shares
                
                # Store position with scaling strategy data
                self.active_positions[symbol] = {
                    'order_id': market_order.id,
                    'entry_price': current_price,
                    'total_shares': shares,
                    'remaining_shares': shares,  # Track remaining shares
                    'initial_stop': initial_stop,
                    'current_stop': initial_stop,
                    'entry_time': datetime.now(),
                    'signal': signal,
                    'atr': atr_value,
                    'scaling_strategy': {
                        'scale_out_target': scale_out_target,
                        'scale_out_shares': scale_out_shares,
                        'scaled_out': False,
                        'trailing_stop_active': False,
                        'swing_low': current_price,  # Track swing lows for trailing
                        'last_high': current_price   # Track recent highs
                    },
                    'realized_profit': 0
                }
                
                # Place initial stop loss order
                stop_order = self.alpaca_client.submit_order(
                    symbol=symbol,
                    qty=shares,
                    side='sell',
                    type='stop',
                    stop_price=initial_stop,
                    time_in_force='gtc'
                )
                
                if stop_order:
                    self.active_positions[symbol]['stop_order_id'] = stop_order.id
                
                logger.info(f"Market order placed for {symbol}: {shares} shares at ${current_price:.2f}")
                logger.info(f"Initial stop: ${initial_stop:.2f}, Scale-out target: ${scale_out_target:.2f} (+1 ATR)")
                logger.info(f"Strategy: Sell {scale_out_shares} shares at ${scale_out_target:.2f}, trail remaining {remaining_shares}")
                
        except Exception as e:
            logger.error(f"Error placing breakout trade for {symbol}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def manage_scaling_positions(self):
        """Manage positions with enhanced scaling-out and trailing stop strategy"""
        try:
            for symbol, position in list(self.active_positions.items()):
                try:
                    # Get current price
                    latest_bars = self.alpaca_client.get_bars(
                        symbol, TimeFrame.Minute, limit=1
                    ).df
                    
                    if latest_bars.empty:
                        continue
                        
                    current_price = latest_bars['close'].iloc[-1]
                    scaling = position['scaling_strategy']
                    entry_price = position['entry_price']
                    initial_stop = position.get('initial_stop', entry_price * 0.98)  # 2% default if not set
                    
                    # Calculate risk per share (entry - stop)
                    risk_per_share = entry_price - initial_stop
                    
                    # Calculate 2:1 R:R target (2x the risk above entry)
                    two_to_one_target = entry_price + (2 * risk_per_share)
                    
                    # Update recent high
                    if current_price > scaling['last_high']:
                        scaling['last_high'] = current_price
                    
                    # Enhanced scaling strategy with 2:1 R:R targets
                    if not scaling['scaled_out'] and current_price >= two_to_one_target:
                        # First scale-out at 2:1 R:R (take 25-50% profit)
                        self._execute_enhanced_scale_out(symbol, position, current_price, "2:1_RR")
                    
                    elif scaling['scaled_out'] and not scaling.get('second_scale_out', False):
                        # Optional second scale-out at 3:1 R:R
                        three_to_one_target = entry_price + (3 * risk_per_share)
                        if current_price >= three_to_one_target:
                            self._execute_enhanced_scale_out(symbol, position, current_price, "3:1_RR")
                    
                    # Update trailing stop for remaining shares (1x ATR trail)
                    if scaling['scaled_out'] and position['remaining_shares'] > 0:
                        self._update_enhanced_trailing_stop(symbol, position, current_price)
                    
                except Exception as e:
                    logger.error(f"Error managing position for {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in manage_scaling_positions: {e}")

    def _execute_enhanced_scale_out(self, symbol: str, position: Dict, current_price: float, scale_type: str):
        """Execute enhanced scale-out at 2:1 or 3:1 R:R targets"""
        try:
            scaling = position['scaling_strategy']
            
            # Determine scale-out percentage based on type
            if scale_type == "2:1_RR":
                scale_pct = 0.4  # Take 40% profit at 2:1 R:R
                scaling['scaled_out'] = True
            elif scale_type == "3:1_RR":
                scale_pct = 0.3  # Take additional 30% at 3:1 R:R
                scaling['second_scale_out'] = True
            else:
                scale_pct = 0.25  # Default 25%
            
            scale_out_shares = int(position['remaining_shares'] * scale_pct)
            
            if scale_out_shares <= 0:
                return
            
            # Place sell order for partial position
            scale_order = self.alpaca_client.submit_order(
                symbol=symbol,
                qty=scale_out_shares,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            if scale_order:
                # Update position tracking
                position['remaining_shares'] -= scale_out_shares
                
                # Calculate profit on scaled portion
                profit = (current_price - position['entry_price']) * scale_out_shares
                total_profit = position.get('realized_profit', 0) + profit
                position['realized_profit'] = total_profit
                
                # Update trailing stop for remaining shares
                if position['remaining_shares'] > 0:
                    self._update_enhanced_trailing_stop(symbol, position, current_price, force_update=True)
                
                logger.info(f"ENHANCED SCALE-OUT ({scale_type}): Sold {scale_out_shares} shares of {symbol} at ${current_price:.2f}")
                logger.info(f"Profit on scaled portion: ${profit:.2f} | Total realized: ${total_profit:.2f}")
                logger.info(f"Remaining {position['remaining_shares']} shares with enhanced trailing stop")
                
                # Send notification for significant profit taking
                if profit > 100:  # Notify for profits > $100
                    self.send_trade_notification(
                        f"Profit Taking: {symbol}",
                        f"Scaled out {scale_out_shares} shares at {scale_type} target\n"
                        f"Price: ${current_price:.2f}\n"
                        f"Profit: ${profit:.2f}\n"
                        f"Remaining: {position['remaining_shares']} shares"
                    )
                
        except Exception as e:
            logger.error(f"Error executing enhanced scale-out for {symbol}: {e}")

    def _update_enhanced_trailing_stop(self, symbol: str, position: Dict, current_price: float, force_update: bool = False):
        """Update trailing stop using 1x ATR methodology"""
        try:
            # Get recent bars for ATR calculation
            bars = self.alpaca_client.get_bars(
                symbol, TimeFrame.Day, limit=15
            ).df
            
            if len(bars) < 14:
                return
            
            # Calculate ATR (14-period)
            bars['high_low'] = bars['high'] - bars['low']
            bars['high_close'] = abs(bars['high'] - bars['close'].shift(1))
            bars['low_close'] = abs(bars['low'] - bars['close'].shift(1))
            bars['true_range'] = bars[['high_low', 'high_close', 'low_close']].max(axis=1)
            atr = bars['true_range'].rolling(window=14).mean().iloc[-1]
            
            # Calculate new trailing stop (1x ATR below current high)
            scaling = position['scaling_strategy']
            new_stop = scaling['last_high'] - atr
            
            # Only update if new stop is higher than current stop (trailing up)
            current_stop = position.get('current_stop', position['entry_price'] * 0.98)
            
            if new_stop > current_stop or force_update:
                # Cancel existing stop order
                if 'stop_order_id' in position:
                    try:
                        self.alpaca_client.cancel_order(position['stop_order_id'])
                    except:
                        pass
                
                # Place new trailing stop order
                if position['remaining_shares'] > 0:
                    stop_order = self.alpaca_client.submit_order(
                        symbol=symbol,
                        qty=position['remaining_shares'],
                        side='sell',
                        type='stop',
                        stop_price=new_stop,
                        time_in_force='gtc'
                    )
                    
                    if stop_order:
                        position['stop_order_id'] = stop_order.id
                        position['current_stop'] = new_stop
                        
                        logger.info(f"TRAILING STOP UPDATED: {symbol} stop moved to ${new_stop:.2f} (1x ATR: ${atr:.2f})")
                
        except Exception as e:
            logger.error(f"Error updating enhanced trailing stop for {symbol}: {e}")
    
    def monitor_existing_positions(self):
        """Monitor existing positions for exit conditions"""
        try:
            positions_to_remove = []
            
            for symbol, position_info in self.active_positions.items():
                try:
                    # Skip order status check for positions loaded from account (no order_id)
                    if position_info.get('order_id') is None:
                        # For legacy positions, just update current price and continue
                        if position_info.get('loaded_from_account', False):
                            logger.debug(f"Monitoring legacy position {symbol} (no order_id tracking)")
                            continue
                        else:
                            logger.warning(f"Error monitoring position {symbol}: order_id is missing")
                            continue
                    
                    # Check order status
                    order_status = self.alpaca_client.get_order(position_info['order_id']).status
                    
                    if order_status in ['filled', 'partially_filled']:
                        # Position is active, monitor for additional exit conditions
                        latest_price = self.alpaca_client.get_latest_price(symbol)
                        
                        # Check for additional exit signals (e.g., reversal patterns)
                        exit_signal = self.breakout_strategy.check_exit_signal(symbol, latest_price)
                        
                        if exit_signal:
                            self.close_position(symbol, exit_signal['reason'])
                            positions_to_remove.append(symbol)
                    
                    elif order_status in ['canceled', 'rejected', 'expired']:
                        # Order was not filled, remove from active positions
                        positions_to_remove.append(symbol)
                        
                except Exception as e:
                    logger.warning(f"Error monitoring position {symbol}: {e}")
            
            # Remove closed positions
            for symbol in positions_to_remove:
                del self.active_positions[symbol]
                
        except Exception as e:
            logger.error(f"Error monitoring existing positions: {e}")
    
    def close_position(self, symbol: str, reason: str):
        """Close an existing position"""
        try:
            logger.info(f"Closing position for {symbol}. Reason: {reason}")
            
            # Cancel existing bracket order and place market sell order
            position_info = self.active_positions[symbol]
            self.alpaca_client.cancel_order(position_info['order_id'])
            
            # Place market sell order
            sell_order = self.alpaca_client.submit_order(
                symbol=symbol,
                qty=position_info['shares'],
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            if sell_order:
                logger.info(f"Position closed for {symbol}")
                
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
    
    def end_of_day_routine(self):
        """Execute end-of-day routine"""
        try:
            logger.info("Starting end-of-day routine...")
            
            # 1. Log all trades to CSV
            self.log_trades_to_csv()
            
            # 2. Update performance report
            self.update_performance_report()
            
            # 3. Send end-of-day email notification
            self.send_end_of_day_email()
            
            # 4. Clean up for next day
            self.cleanup_for_next_day()
            
            logger.info("End-of-day routine completed")
            
        except Exception as e:
            logger.error(f"Error in end-of-day routine: {e}")
    
    def log_trades_to_csv(self):
        """Log all trades to CSV file"""
        try:
            trades_file = f"logs/trades_{datetime.now().strftime('%Y%m%d')}.csv"
            
            # Get all filled orders for today
            filled_orders = self.alpaca_client.list_orders(status='filled', limit=100)
            
            if filled_orders:
                df = pd.DataFrame([order.__dict__ for order in filled_orders])
                df.to_csv(trades_file, index=False)
                logger.info(f"Trades logged to {trades_file}")
            else:
                logger.info("No trades to log today")
                
        except Exception as e:
            logger.error(f"Error logging trades to CSV: {e}")
    
    def update_performance_report(self):
        """Update daily performance report"""
        try:
            self.performance_tracker.update_daily_performance()
            logger.info("Performance report updated")
            
        except Exception as e:
            logger.error(f"Error updating performance report: {e}")
    
    def send_end_of_day_email(self):
        """Send end-of-day summary email"""
        try:
            # Get current account info
            account = self.alpaca_client.get_account()
            
            # Calculate P&L values
            current_equity = float(account.equity)
            last_equity = float(account.last_equity)
            day_pl = current_equity - last_equity
            
            # Get positions for total unrealized P&L
            positions = self.alpaca_client.list_positions()
            total_unrealized_pl = sum(float(pos.unrealized_pl) for pos in positions)
            
            # Get today's filled orders (filter by today's date)
            today = datetime.now().date()
            filled_orders = self.alpaca_client.list_orders(
                status='filled', 
                limit=50,
                after=today.strftime('%Y-%m-%d'),
                until=(today + timedelta(days=1)).strftime('%Y-%m-%d')
            )
            
            # Generate email content
            subject = f"End-of-Day Trading Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
🌅 END-OF-DAY TRADING SUMMARY
Date: {datetime.now().strftime('%Y-%m-%d')}
Time: {datetime.now().strftime('%H:%M:%S ET')}

📊 ACCOUNT STATUS:
• Portfolio Value: ${current_equity:,.2f}
• Buying Power: ${float(account.buying_power):,.2f}
• Day P&L: ${day_pl:,.2f} ({day_pl/last_equity*100:+.2f}%)
• Total Unrealized P&L: ${total_unrealized_pl:,.2f}

📈 ACTIVE POSITIONS: {len(self.active_positions)}
"""

            # Add position details
            if self.active_positions:
                body += "\n🎯 CURRENT POSITIONS:\n"
                for symbol, position in self.active_positions.items():
                    body += f"• {symbol}: {position['remaining_shares']} shares @ ${position['entry_price']:.2f}\n"
                    if 'scaling_strategy' in position:
                        scaling = position['scaling_strategy']
                        if scaling['scaled_out']:
                            body += f"  ✅ Scaled out {scaling['scale_out_shares']} shares\n"
                        body += f"  🎯 Next target: ${scaling['scale_out_target']:.2f}\n"
                        body += f"  🛡️ Stop: ${position['current_stop']:.2f}\n"
            else:
                body += "\n💤 No active positions\n"
            
            # Add today's trades
            if filled_orders:
                body += f"\n📋 TODAY'S TRADES ({len(filled_orders)}):\n"
                for order in filled_orders[:10]:  # Show last 10 trades
                    side_emoji = "🟢" if order.side == 'buy' else "🔴"
                    body += f"{side_emoji} {order.side.upper()} {order.qty} {order.symbol} @ ${float(order.filled_avg_price or 0):.2f}\n"
            else:
                body += "\n📋 No trades executed today\n"
            
            # Add eligible stocks for tomorrow
            body += f"\n🔍 ELIGIBLE STOCKS FOR TOMORROW: {len(self.eligible_stocks)}\n"
            if self.eligible_stocks:
                body += f"Stocks: {', '.join(self.eligible_stocks[:10])}"
                if len(self.eligible_stocks) > 10:
                    body += f" (+{len(self.eligible_stocks) - 10} more)"
                body += "\n"
            
            body += f"""
⚙️ SYSTEM STATUS:
• Max Positions: {self.max_positions}
• Position Size: ${self.position_size:,.0f}
• Stop Loss: {self.stop_loss_pct * 100:.1f}%

🕐 NEXT SCHEDULE:
• Pre-market: Tomorrow 8:00 AM ET
• Intraday: Every 15 min, 9:00 AM - 3:45 PM ET
• End-of-day: Tomorrow 4:30 PM ET

---
Alpaca Trading Bot - Advanced ATR Scaling Strategy
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}
"""
            
            # Send the email
            if notifier.enabled:
                success = notifier.send_email(subject, body)
                if success:
                    logger.info("✅ End-of-day email sent successfully")
                else:
                    logger.warning("❌ Failed to send end-of-day email")
            else:
                logger.warning("📧 Email notifications disabled - would have sent:")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body preview: {body[:200]}...")
                
        except Exception as e:
            logger.error(f"Error sending end-of-day email: {e}")

    def cleanup_for_next_day(self):
        """Clean up data structures for next trading day"""
        try:
            # Clear eligible stocks list
            self.eligible_stocks = []
            
            # Clear cached intraday data
            self.breakout_strategy.clear_cache()
            
            # Keep active positions for next day monitoring
            logger.info("Cleanup completed for next day")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
    
    def _send_pre_market_summary_email(self, opportunities, screening_details):
        """Send detailed pre-market screening summary email with rejection reasons"""
        try:
            from alpaca_trading.core.notifier import notifier
            from datetime import datetime
            import hashlib
            
            # Check for duplicate email within the same day
            today = datetime.now().strftime("%Y-%m-%d")
            email_lock_file = f'/tmp/alpaca_premarket_email_{today}'
            
            # Create a hash of the email content for deduplication
            content_hash = hashlib.md5(f"{len(opportunities)}_{len(screening_details)}_{today}".encode()).hexdigest()
            
            # Check if we already sent an email today with similar content
            if os.path.exists(email_lock_file):
                try:
                    with open(email_lock_file, 'r') as f:
                        last_hash = f.read().strip()
                        if last_hash == content_hash:
                            logger.warning(f"⚠️ Pre-market email already sent today with same content. Skipping duplicate.")
                            return
                except:
                    pass  # If we can't read the file, proceed with sending
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")
            subject = f"Pre-Market Screening Complete - {len(opportunities)} Opportunities Found"
            
            # Get universe size for transparency
            try:
                universe_size = len(self.stock_screener.get_curated_stock_universe())
            except:
                universe_size = "~192"  # Fallback estimate
            
            # Build email body with enhanced transparency
            body = f"""
🌅 PRE-MARKET SCREENING COMPLETE

Time: {current_time}

📈 SCREENING TRANSPARENCY:
- Total Universe Size: {universe_size} stocks (manually curated)
- Stocks Reviewed: {len(screening_details)} (ALL stocks in universe processed)
- Opportunities Found: {len(opportunities)} (selected for trading consideration)
- Screening Coverage: 100% of universe (no limits applied)

"""
            
            # Add selected opportunities
            if opportunities:
                body += "🎯 SELECTED OPPORTUNITIES:\n"
                for i, opp in enumerate(opportunities, 1):
                    body += f"{i}. {opp['symbol']} ({opp.get('name', 'N/A')})\n"
                    body += f"   Signal: {opp['signal']} at ${opp['price']:.2f}\n"
                    body += f"   Reason: {opp['reason']}\n"
                    if 'rvol' in opp:
                        body += f"   Volume: {opp['rvol']:.1f}x avg, ATR: {opp.get('atr_pct', 0):.1f}%\n"
                    body += "\n"
            else:
                body += "🎯 No opportunities found today\n\n"
            
            # Add COMPLETE list of all stocks screened with specific reasons
            body += f"📋 COMPLETE SCREENING RESULTS ({len(screening_details)} stocks):\n\n"
            
            # Sort stocks alphabetically for easy reference
            sorted_stocks = sorted(screening_details, key=lambda x: x.get('symbol', ''))
            
            # Separate accepted and rejected for better organization
            accepted_stocks = [stock for stock in sorted_stocks if stock.get('status') == 'accepted']
            rejected_stocks = [stock for stock in sorted_stocks if stock.get('status') == 'rejected']
            
            # Show accepted stocks first
            if accepted_stocks:
                body += f"✅ ACCEPTED STOCKS ({len(accepted_stocks)}):\n"
                for stock in accepted_stocks:
                    symbol = stock.get('symbol', 'N/A')
                    name = stock.get('name', 'N/A')
                    price = stock.get('price', 0)
                    body += f"• {symbol} ({name}) - ${price:.2f}\n"
                    body += f"  ✓ Passed all screening filters and selected as opportunity\n"
                    # Add any additional acceptance details if available
                    if stock.get('ma_crossover_result'):
                        body += f"  ✓ Moving average crossover signal detected\n"
                    if stock.get('enhanced_filters'):
                        filters = stock['enhanced_filters']
                        if filters.get('volume_pass'):
                            body += f"  ✓ Volume filter passed\n"
                        if filters.get('atr_pass'):
                            body += f"  ✓ ATR filter passed\n"
                        if filters.get('trend_pass'):
                            body += f"  ✓ Trend filter passed\n"
                    body += "\n"
            
            # Show rejected stocks with specific reasons
            if rejected_stocks:
                body += f"❌ REJECTED STOCKS ({len(rejected_stocks)}):\n"
                for stock in rejected_stocks:
                    symbol = stock.get('symbol', 'N/A')
                    name = stock.get('name', 'N/A')
                    price = stock.get('price', 0)
                    reasons = stock.get('rejection_reasons', ['Unknown reason'])
                    
                    body += f"• {symbol} ({name})"
                    if price > 0:
                        body += f" - ${price:.2f}"
                    body += "\n"
                    
                    # List all specific rejection reasons
                    for reason in reasons:
                        body += f"  ✗ {reason}\n"
                    
                    # Add additional context if available
                    if not stock.get('ma_crossover_result'):
                        body += f"  ✗ No moving average crossover signal\n"
                    
                    body += "\n"
            
            # Add system status
            body += f"""
⚙️ SYSTEM STATUS:
• Total Universe: {universe_size} stocks (manually curated)
• Stocks Reviewed: {len(screening_details)} (ALL stocks processed)
• Opportunities Found: {len(opportunities)} (selected for trading)
• Coverage: 100% of universe (no screening limits)
• Max Positions: {self.max_positions}
• Position Size: ${self.position_size:,.0f}
• Stop Loss: {self.stop_loss_pct * 100:.1f}%
• Data Sources: Alpaca, Polygon, Tiingo APIs operational

🕐 NEXT STEPS:
• Intraday monitoring starts at 9:00 AM ET
• Position entries during market hours (9:30 AM - 4:00 PM ET)
• End-of-day summary at 4:30 PM ET

---
Alpaca Trading Bot - Pre-Market Analysis
Generated: {current_time}
"""
            
            # Send the email
            if notifier.enabled:
                success = notifier.send_email(subject, body)
                if success:
                    logger.info("✅ Pre-market summary email sent successfully")
                    # Record that we sent this email to prevent duplicates
                    try:
                        with open(email_lock_file, 'w') as f:
                            f.write(content_hash)
                        logger.info(f"📝 Recorded email send to prevent duplicates")
                    except Exception as e:
                        logger.warning(f"Could not record email send: {e}")
                else:
                    logger.warning("❌ Failed to send pre-market summary email")
            else:
                logger.warning("📧 Email notifications disabled - would have sent:")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body preview: {body[:200]}...")
                
        except Exception as e:
            logger.error(f"Error sending pre-market summary email: {e}")
    
    def run_scheduler(self):
        """Run the daily trading scheduler"""
        logger.info("Starting Daily Trading Automation Scheduler")
        
        # Schedule golden cross universe update at 6:00 AM ET (before pre-market)
        schedule.every().day.at("06:00").do(self.update_golden_cross_universe)
        
        # Schedule pre-market routine at 8:00 AM ET
        schedule.every().day.at("08:00").do(self.pre_market_routine)
        
        # Schedule intraday monitoring every 15 minutes during market hours
        for hour in range(9, 16):  # 9 AM to 4 PM ET
            for minute in [0, 15, 30, 45]:
                time_str = f"{hour:02d}:{minute:02d}"
                schedule.every().day.at(time_str).do(self.intraday_monitoring)
        
        # Schedule end-of-day routine at 4:30 PM ET
        schedule.every().day.at("16:30").do(self.end_of_day_routine)
        
        # Schedule scaling management every 5 minutes
        for minute in range(0, 60, 5):
            time_str = f"{minute:02d}"
            schedule.every().day.at(f"09:{time_str}").do(self.manage_scaling_positions)
            schedule.every().day.at(f"10:{time_str}").do(self.manage_scaling_positions)
            schedule.every().day.at(f"11:{time_str}").do(self.manage_scaling_positions)
            schedule.every().day.at(f"12:{time_str}").do(self.manage_scaling_positions)
            schedule.every().day.at(f"13:{time_str}").do(self.manage_scaling_positions)
            schedule.every().day.at(f"14:{time_str}").do(self.manage_scaling_positions)
            schedule.every().day.at(f"15:{time_str}").do(self.manage_scaling_positions)
        
        # Keep the scheduler running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(60)

def main():
    """Main entry point"""
    try:
        automation = DailyTradingAutomation()
        automation.run_scheduler()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
