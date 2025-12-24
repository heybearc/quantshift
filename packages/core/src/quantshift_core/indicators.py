"""Technical indicators and multi-timeframe analysis."""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import structlog

logger = structlog.get_logger()


class TechnicalIndicators:
    """Calculate technical indicators for trading strategies."""

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(
        data: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD indicator."""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands."""
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average Directional Index (trend strength)."""
        # Calculate +DM and -DM
        high_diff = high.diff()
        low_diff = -low.diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        # Calculate ATR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator."""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=3).mean()
        
        return k, d


class MultiTimeframeAnalyzer:
    """Analyze multiple timeframes for better trade decisions."""

    def __init__(self):
        """Initialize multi-timeframe analyzer."""
        self.indicators = TechnicalIndicators()

    def get_trend(
        self,
        data: pd.DataFrame,
        fast_period: int = 50,
        slow_period: int = 200
    ) -> str:
        """
        Determine trend direction.
        
        Args:
            data: DataFrame with OHLCV data
            fast_period: Fast MA period
            slow_period: Slow MA period
            
        Returns:
            'up', 'down', or 'neutral'
        """
        if len(data) < slow_period:
            return 'neutral'
        
        fast_ma = self.indicators.sma(data['close'], fast_period).iloc[-1]
        slow_ma = self.indicators.sma(data['close'], slow_period).iloc[-1]
        
        if fast_ma > slow_ma * 1.01:  # 1% buffer
            return 'up'
        elif fast_ma < slow_ma * 0.99:
            return 'down'
        else:
            return 'neutral'

    def check_trend_alignment(
        self,
        daily_data: pd.DataFrame,
        hourly_data: pd.DataFrame,
        current_data: pd.DataFrame
    ) -> Dict:
        """
        Check if trends align across multiple timeframes.
        
        Args:
            daily_data: Daily timeframe data
            hourly_data: Hourly timeframe data
            current_data: Current timeframe data (e.g., 15min)
            
        Returns:
            Dictionary with trend analysis
        """
        daily_trend = self.get_trend(daily_data)
        hourly_trend = self.get_trend(hourly_data, fast_period=20, slow_period=50)
        current_trend = self.get_trend(current_data, fast_period=10, slow_period=20)
        
        # Check alignment
        all_up = daily_trend == 'up' and hourly_trend == 'up' and current_trend == 'up'
        all_down = daily_trend == 'down' and hourly_trend == 'down' and current_trend == 'down'
        
        result = {
            'daily_trend': daily_trend,
            'hourly_trend': hourly_trend,
            'current_trend': current_trend,
            'aligned': all_up or all_down,
            'direction': 'up' if all_up else ('down' if all_down else 'mixed'),
            'strength': self._calculate_trend_strength(daily_data)
        }
        
        logger.debug("trend_alignment_checked", **result)
        
        return result

    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength using ADX."""
        if len(data) < 14:
            return 0.0
        
        adx = self.indicators.adx(
            data['high'],
            data['low'],
            data['close']
        ).iloc[-1]
        
        return adx if not np.isnan(adx) else 0.0

    def get_support_resistance(
        self,
        data: pd.DataFrame,
        lookback: int = 50
    ) -> Dict[str, List[float]]:
        """
        Identify support and resistance levels.
        
        Args:
            data: DataFrame with OHLCV data
            lookback: Number of periods to look back
            
        Returns:
            Dictionary with support and resistance levels
        """
        if len(data) < lookback:
            return {'support': [], 'resistance': []}
        
        recent_data = data.tail(lookback)
        
        # Find local maxima (resistance)
        resistance_levels = []
        for i in range(1, len(recent_data) - 1):
            if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1]):
                resistance_levels.append(recent_data['high'].iloc[i])
        
        # Find local minima (support)
        support_levels = []
        for i in range(1, len(recent_data) - 1):
            if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1]):
                support_levels.append(recent_data['low'].iloc[i])
        
        return {
            'support': sorted(support_levels)[-3:],  # Top 3 support levels
            'resistance': sorted(resistance_levels, reverse=True)[:3]  # Top 3 resistance
        }

    def should_trade(
        self,
        symbol: str,
        daily_data: pd.DataFrame,
        hourly_data: pd.DataFrame,
        current_data: pd.DataFrame,
        direction: str
    ) -> Tuple[bool, str]:
        """
        Determine if trade should be taken based on multi-timeframe analysis.
        
        Args:
            symbol: Trading symbol
            daily_data: Daily timeframe data
            hourly_data: Hourly timeframe data
            current_data: Current timeframe data
            direction: Intended trade direction ('long' or 'short')
            
        Returns:
            Tuple of (should_trade, reason)
        """
        # Check trend alignment
        alignment = self.check_trend_alignment(daily_data, hourly_data, current_data)
        
        # For long trades
        if direction == 'long':
            if not alignment['aligned'] or alignment['direction'] != 'up':
                return False, "Trends not aligned for long"
            
            if alignment['strength'] < 20:
                return False, "Trend too weak (ADX < 20)"
            
            # Check if price is above key moving averages
            if len(daily_data) >= 50:
                sma_50 = self.indicators.sma(daily_data['close'], 50).iloc[-1]
                current_price = current_data['close'].iloc[-1]
                
                if current_price < sma_50:
                    return False, "Price below 50 SMA on daily"
            
            logger.info("long_trade_approved", symbol=symbol, strength=alignment['strength'])
            return True, "All timeframes aligned for long"
        
        # For short trades
        elif direction == 'short':
            if not alignment['aligned'] or alignment['direction'] != 'down':
                return False, "Trends not aligned for short"
            
            if alignment['strength'] < 20:
                return False, "Trend too weak (ADX < 20)"
            
            # Check if price is below key moving averages
            if len(daily_data) >= 50:
                sma_50 = self.indicators.sma(daily_data['close'], 50).iloc[-1]
                current_price = current_data['close'].iloc[-1]
                
                if current_price > sma_50:
                    return False, "Price above 50 SMA on daily"
            
            logger.info("short_trade_approved", symbol=symbol, strength=alignment['strength'])
            return True, "All timeframes aligned for short"
        
        return False, "Invalid direction"

    def get_entry_timing(
        self,
        data: pd.DataFrame,
        direction: str
    ) -> Dict:
        """
        Get optimal entry timing based on indicators.
        
        Args:
            data: Current timeframe data
            direction: Trade direction ('long' or 'short')
            
        Returns:
            Dictionary with entry timing analysis
        """
        if len(data) < 50:
            return {'ready': False, 'reason': 'Insufficient data'}
        
        # Calculate indicators
        rsi = self.indicators.rsi(data['close']).iloc[-1]
        macd_line, signal_line, _ = self.indicators.macd(data['close'])
        macd_current = macd_line.iloc[-1]
        signal_current = signal_line.iloc[-1]
        
        if direction == 'long':
            # Look for pullback in uptrend
            if rsi > 70:
                return {'ready': False, 'reason': 'RSI overbought'}
            
            if rsi < 30:
                return {'ready': True, 'reason': 'RSI oversold - good entry'}
            
            if macd_current > signal_current:
                return {'ready': True, 'reason': 'MACD bullish'}
            
            return {'ready': False, 'reason': 'Wait for better entry'}
        
        elif direction == 'short':
            # Look for bounce in downtrend
            if rsi < 30:
                return {'ready': False, 'reason': 'RSI oversold'}
            
            if rsi > 70:
                return {'ready': True, 'reason': 'RSI overbought - good entry'}
            
            if macd_current < signal_current:
                return {'ready': True, 'reason': 'MACD bearish'}
            
            return {'ready': False, 'reason': 'Wait for better entry'}
        
        return {'ready': False, 'reason': 'Invalid direction'}
