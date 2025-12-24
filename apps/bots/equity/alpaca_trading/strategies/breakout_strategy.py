"""
Breakout Trading Strategy
Implements breakout detection with volume surge confirmation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

# Technical analysis library
try:
    import ta
except ImportError:
    # Fallback to manual calculations if ta library not available
    ta = None

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
from alpaca_trading.core.config import config

from alpaca_trading.utils.logging_config import setup_logger

logger = setup_logger(__name__)

class BreakoutStrategy:
    """Breakout trading strategy with volume confirmation"""
    
    def __init__(self):
        self.intraday_cache = {}  # Cache for intraday data
        
        # Strategy parameters - RELAXED FOR TESTING
        self.ema_short_period = 20
        self.ema_long_period = 50
        self.volume_surge_multiplier = 1.5  # Reduced from 2.0 to 1.5
        self.breakout_threshold = 0.01  # Reduced from 0.02 to 0.01 (1% instead of 2%)
        self.atr_period = 14
        self.min_volume = 50000  # Reduced from 100000
        self.min_price = 5.0  # Minimum stock price
        self.max_price = 500.0  # Maximum stock price
        
    def _convert_bars_to_dataframe(self, bars) -> pd.DataFrame:
        """Convert Alpaca bars to pandas DataFrame"""
        try:
            if isinstance(bars, pd.DataFrame):
                # Already a DataFrame (from yfinance or other sources)
                # Ensure column names are lowercase
                df = bars.copy()
                df.columns = df.columns.str.lower()
                return df
            
            # Handle BarsV2 object from Alpaca API
            if hasattr(bars, 'df'):
                return bars.df
            
            # Handle list of Bar objects
            if hasattr(bars, '__iter__') and not isinstance(bars, (str, bytes)):
                data = []
                for bar in bars:
                    if hasattr(bar, 'timestamp'):
                        data.append({
                            'timestamp': bar.timestamp,
                            'open': bar.open,
                            'high': bar.high,
                            'low': bar.low,
                            'close': bar.close,
                            'volume': bar.volume
                        })
                
                if data:
                    df = pd.DataFrame(data)
                    df.set_index('timestamp', inplace=True)
                    return df
            
            # If all else fails, try to convert directly
            return pd.DataFrame(bars)
            
        except Exception as e:
            logger.error(f"Error converting bars to DataFrame: {e}")
            return pd.DataFrame()

    def meets_screening_criteria(self, daily_data, weekly_data) -> bool:
        """Check if stock meets daily and weekly screening criteria"""
        try:
            # Convert to DataFrames
            daily_df = self._convert_bars_to_dataframe(daily_data)
            weekly_df = self._convert_bars_to_dataframe(weekly_data)
            
            if daily_df.empty or weekly_df.empty:
                return False
        
            # Basic filters
            latest_price = daily_df['close'].iloc[-1]
            avg_volume = daily_df['volume'].tail(20).mean()
            
            if latest_price < self.min_price or latest_price > self.max_price:
                return False
            
            if avg_volume < self.min_volume:
                return False
            
            # Technical criteria
            daily_ema_20 = self.calculate_ema(daily_df['close'], 20)
            daily_ema_50 = self.calculate_ema(daily_df['close'], 50)
            
            # Daily trend: Price above EMA20, EMA20 above EMA50
            if latest_price < daily_ema_20.iloc[-1]:
                return False
            
            if daily_ema_20.iloc[-1] < daily_ema_50.iloc[-1]:
                return False
            
            # Weekly trend filter
            weekly_ema_10 = self.calculate_ema(weekly_df['close'], 10)
            weekly_latest = weekly_df['close'].iloc[-1]
            
            if weekly_latest < weekly_ema_10.iloc[-1]:
                return False
            
            # Volume trend (increasing volume over last 5 days)
            recent_volume = daily_df['volume'].tail(5).mean()
            older_volume = daily_df['volume'].tail(20).head(15).mean()
            
            if recent_volume < older_volume * 1.2:  # 20% increase in volume
                return False
            
            # ATR filter (sufficient volatility)
            atr = self.calculate_atr(daily_df)
            if atr.iloc[-1] < latest_price * 0.015:  # Minimum 1.5% ATR
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in screening criteria: {e}")
            return False
    
    def cache_intraday_data(self, symbol: str, bars):
        """Cache intraday data for quick access"""
        try:
            # Convert to DataFrame
            bars_df = self._convert_bars_to_dataframe(bars)
            
            self.intraday_cache[symbol] = {
                'data': bars_df,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error caching intraday data for {symbol}: {e}")
    
    def check_breakout_signal(self, symbol: str, latest_bars) -> Dict[str, Any]:
        """Check for breakout signal with volume confirmation"""
        try:
            # Convert to DataFrame
            latest_df = self._convert_bars_to_dataframe(latest_bars)
            
            if latest_df.empty:
                return {'action': 'HOLD', 'reason': 'No data'}
            
            # Get cached data for context
            cached_data = self.intraday_cache.get(symbol, {}).get('data', pd.DataFrame())
            
            # Combine cached and latest data
            if not cached_data.empty:
                combined_data = pd.concat([cached_data, latest_df]).drop_duplicates()
            else:
                combined_data = latest_df
            
            # Need at least 50 bars for reliable signals
            if len(combined_data) < 50:
                return {'action': 'HOLD', 'reason': 'Insufficient data'}
            
            # Calculate indicators
            current_price = combined_data['close'].iloc[-1]
            current_volume = combined_data['volume'].iloc[-1]
            
            # Volume surge check
            avg_volume = combined_data['volume'].tail(20).mean()
            volume_surge = current_volume > (avg_volume * self.volume_surge_multiplier)
            
            # Resistance level (recent high)
            resistance_period = 20
            resistance_level = combined_data['high'].tail(resistance_period).max()
            
            # Price breakout check
            price_breakout = current_price > resistance_level * (1 + self.breakout_threshold)
            
            # Trend confirmation
            ema_20 = self.calculate_ema(combined_data['close'], 20)
            ema_50 = self.calculate_ema(combined_data['close'], 50)
            trend_bullish = ema_20.iloc[-1] > ema_50.iloc[-1]
            
            # RSI filter (not overbought)
            rsi = self.calculate_rsi(combined_data['close'])
            rsi_ok = rsi.iloc[-1] < 70
            
            # Price range tightening (lower volatility before breakout)
            recent_range = combined_data['high'].tail(5) - combined_data['low'].tail(5)
            older_range = combined_data['high'].tail(20).head(15) - combined_data['low'].tail(20).head(15)
            price_range_tight = recent_range.mean() < older_range.mean()
            
            # All conditions must be met for BUY signal
            if (volume_surge and price_breakout and trend_bullish and 
                rsi_ok and price_range_tight):
                
                # Calculate ATR for position sizing and stops
                atr = self.calculate_atr(combined_data)
                current_atr = atr.iloc[-1] if not atr.empty else current_price * 0.02
                
                return {
                    'action': 'BUY',
                    'entry_price': current_price,
                    'atr': current_atr,  # Include ATR for scaling strategy
                    'volume_ratio': current_volume / avg_volume,
                    'rsi': rsi.iloc[-1],
                    'confidence': self.calculate_signal_confidence(
                        volume_surge, price_breakout, trend_bullish, rsi_ok, price_range_tight
                    ),
                    'reason': 'Breakout with volume surge'
                }
            
            return {'action': 'HOLD', 'reason': 'Conditions not met'}
            
        except Exception as e:
            logger.error(f"Error checking breakout signal for {symbol}: {e}")
            return {'action': 'HOLD', 'reason': f'Error: {e}'}

    def check_exit_signal(self, symbol: str, current_price: float) -> Optional[Dict[str, Any]]:
        """Check for exit signal on existing position"""
        try:
            cached_data = self.intraday_cache.get(symbol, {}).get('data', pd.DataFrame())
            
            if cached_data.empty:
                return None
            
            # Check for reversal patterns
            recent_data = cached_data.tail(10)
            
            # Volume declining
            recent_volume = recent_data['volume'].tail(3).mean()
            older_volume = recent_data['volume'].head(7).mean()
            volume_declining = recent_volume < older_volume * 0.7
            
            # Price below EMA20
            ema_20 = self.calculate_ema(cached_data['close'], 20)
            below_ema = current_price < ema_20.iloc[-1]
            
            # RSI overbought
            rsi = self.calculate_rsi(cached_data['close'])
            rsi_overbought = rsi.iloc[-1] > 75
            
            if volume_declining and (below_ema or rsi_overbought):
                return {
                    'exit': True,
                    'reason': 'Reversal signal detected',
                    'rsi': rsi.iloc[-1],
                    'volume_declining': volume_declining
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking exit signal for {symbol}: {e}")
            return None
    
    def calculate_signal_confidence(self, volume_surge: bool, price_breakout: bool, 
                                  trend_bullish: bool, rsi_ok: bool, 
                                  price_range_tight: bool) -> float:
        """Calculate confidence score for the signal"""
        conditions = [volume_surge, price_breakout, trend_bullish, rsi_ok, price_range_tight]
        return sum(conditions) / len(conditions)
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        if ta:
            return ta.trend.EMAIndicator(prices, window=period).ema_indicator()
        else:
            # Manual EMA calculation
            return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        if ta:
            return ta.momentum.RSIIndicator(prices, window=period).rsi()
        else:
            # Manual RSI calculation
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        if ta:
            return ta.volatility.AverageTrueRange(
                high=data['high'], 
                low=data['low'], 
                close=data['close'], 
                window=period
            ).average_true_range()
        else:
            # Manual ATR calculation
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return true_range.rolling(window=period).mean()
    
    def clear_cache(self):
        """Clear the intraday data cache"""
        self.intraday_cache = {}
        logger.info("Intraday data cache cleared")
