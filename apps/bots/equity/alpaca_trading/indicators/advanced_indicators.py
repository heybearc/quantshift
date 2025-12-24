"""Advanced Trading Indicators - Converted from TradingView PineScript.

These indicators are professional-grade tools converted from TradingView
to Python for use with the Alpaca trading bot.

Sources:
- TC Top & Bottom Finder
- TC Breakout Detector  
- TC Market Reversals
- TC Trend Dashboard
- TC Whale Money Flow
- TC Support/Resistance Levels
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal from an indicator."""
    indicator: str
    signal_type: str  # "BUY", "SELL", "STRONG_BUY", "STRONG_SELL", "HOLD"
    strength: float  # 0.0 to 1.0
    price: float
    reason: str
    
    def __str__(self):
        return f"{self.indicator}: {self.signal_type} ({self.strength:.0%}) - {self.reason}"


class TopBottomFinder:
    """TC Top & Bottom Finder - Identifies market tops and bottoms.
    
    Uses a multi-layer approximation algorithm with Laguerre filters
    to identify potential reversal points.
    """
    
    def __init__(self, signal_strength: int = 10):
        self.signal_strength = signal_strength
    
    def _laguerre_filter(self, data: np.ndarray, gamma: float) -> np.ndarray:
        """Apply Laguerre filter (approximation function from PineScript)."""
        n = len(data)
        l0 = np.zeros(n)
        l1 = np.zeros(n)
        l2 = np.zeros(n)
        l3 = np.zeros(n)
        result = np.zeros(n)
        
        for i in range(1, n):
            l0[i] = (1 - gamma) * data[i] + gamma * l0[i-1]
            l1[i] = -gamma * l0[i] + l0[i-1] + gamma * l1[i-1]
            l2[i] = -gamma * l1[i] + l1[i-1] + gamma * l2[i-1]
            l3[i] = -gamma * l2[i] + l2[i-1] + gamma * l3[i-1]
            result[i] = (l0[i] + 2*l1[i] + 2*l2[i] + l3[i]) / 6
        
        return result
    
    def _calculate_bands(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate the approximation bands."""
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        
        # True range
        tr = np.maximum(highs - lows, 
                       np.maximum(np.abs(highs - np.roll(df['close'].values, 1)),
                                 np.abs(lows - np.roll(df['close'].values, 1))))
        
        # Multiple gamma values for smoothing
        gammas = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 
                  0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
        
        # Calculate approximations
        approx_sum = np.zeros(len(opens))
        tr_approx_sum = np.zeros(len(opens))
        
        for gamma in gammas:
            approx_sum += self._laguerre_filter(opens, gamma)
            tr_approx_sum += self._laguerre_filter(tr, gamma)
        
        amlag = approx_sum / len(gammas)
        inapprox = tr_approx_sum / len(gammas)
        
        # Golden ratio multiplier
        phi = 1.618
        upper_band = amlag + 2 * inapprox * phi
        lower_band = amlag - 2 * inapprox * phi
        
        return amlag, upper_band, lower_band
    
    def _detect_reversals(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Detect bullish and bearish reversals."""
        closes = df['close'].values
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        
        n = len(closes)
        bullish = np.zeros(n, dtype=bool)
        bearish = np.zeros(n, dtype=bool)
        
        bindex = 0
        sindex = 0
        
        for i in range(4, n):
            if closes[i] > closes[i-4]:
                bindex += 1
            if closes[i] < closes[i-4]:
                sindex += 1
            
            # Bearish reversal
            if bindex > 2 and closes[i] < opens[i]:
                if highs[i] >= np.max(highs[max(0, i-self.signal_strength):i+1]):
                    bearish[i] = True
                    bindex = 0
            
            # Bullish reversal
            if sindex > 2 and closes[i] > opens[i]:
                if lows[i] <= np.min(lows[max(0, i-self.signal_strength):i+1]):
                    bullish[i] = True
                    sindex = 0
        
        return bullish, bearish
    
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Analyze price data for top/bottom signals."""
        if len(df) < 20:
            return Signal("TopBottomFinder", "HOLD", 0, df['close'].iloc[-1], "Insufficient data")
        
        amlag, upper_band, lower_band = self._calculate_bands(df)
        bullish, bearish = self._detect_reversals(df)
        
        current_price = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        # Check for strong signals (price crossing bands)
        prev_high = df['high'].iloc[-2]
        prev_low = df['low'].iloc[-2]
        
        # Strong buy: price crosses above lower band
        cross_up = current_low > lower_band[-2] and prev_low <= lower_band[-2]
        # Strong sell: price crosses below upper band
        cross_down = current_high < upper_band[-2] and prev_high >= upper_band[-2]
        
        if cross_up:
            return Signal("TopBottomFinder", "STRONG_BUY", 0.9, current_price, 
                         "Price crossed above lower band - strong reversal")
        
        if cross_down:
            return Signal("TopBottomFinder", "STRONG_SELL", 0.9, current_price,
                         "Price crossed below upper band - strong reversal")
        
        if bullish[-1]:
            return Signal("TopBottomFinder", "BUY", 0.7, current_price,
                         "Bullish reversal pattern detected")
        
        if bearish[-1]:
            return Signal("TopBottomFinder", "SELL", 0.7, current_price,
                         "Bearish reversal pattern detected")
        
        # Check proximity to bands
        band_range = upper_band[-1] - lower_band[-1]
        if band_range > 0:
            position = (current_price - lower_band[-1]) / band_range
            
            if position < 0.2:
                return Signal("TopBottomFinder", "BUY", 0.5, current_price,
                             f"Price near lower band ({position:.0%})")
            elif position > 0.8:
                return Signal("TopBottomFinder", "SELL", 0.5, current_price,
                             f"Price near upper band ({position:.0%})")
        
        return Signal("TopBottomFinder", "HOLD", 0, current_price, "No signal")


class BreakoutDetector:
    """TC Breakout Detector - Identifies volatility breakouts.
    
    Uses Parkinson volatility and RSI to detect breakout zones.
    """
    
    def __init__(self, volatility_length: int = 8):
        self.volatility_length = volatility_length
    
    def _parkinson_volatility(self, highs: np.ndarray, lows: np.ndarray, length: int) -> np.ndarray:
        """Calculate Parkinson volatility estimator."""
        n = len(highs)
        result = np.zeros(n)
        
        for i in range(length, n):
            log_hl = np.log(highs[i-length:i] / lows[i-length:i])
            sum_sq = np.sum(log_hl ** 2)
            result[i] = np.sqrt(sum_sq / (length * 4 * np.log(2)))
        
        return result
    
    def _rsi(self, data: np.ndarray, length: int = 14) -> np.ndarray:
        """Calculate RSI."""
        n = len(data)
        result = np.full(n, 50.0)
        
        if n < length + 1:
            return result
        
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.zeros(n-1)
        avg_loss = np.zeros(n-1)
        
        # Initial SMA
        avg_gain[length-1] = np.mean(gains[:length])
        avg_loss[length-1] = np.mean(losses[:length])
        
        # RMA (Wilder's smoothing)
        for i in range(length, n-1):
            avg_gain[i] = (avg_gain[i-1] * (length-1) + gains[i]) / length
            avg_loss[i] = (avg_loss[i-1] * (length-1) + losses[i]) / length
        
        rs = np.where(avg_loss > 0, avg_gain / avg_loss, 100)
        result[1:] = 100 - (100 / (1 + rs))
        
        return result
    
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Analyze for breakout signals."""
        if len(df) < self.volatility_length + 14:
            return Signal("BreakoutDetector", "HOLD", 0, df['close'].iloc[-1], "Insufficient data")
        
        highs = df['high'].values
        lows = df['low'].values
        hlc3 = (df['high'] + df['low'] + df['close']).values / 3
        
        # Calculate Parkinson volatility
        pv = self._parkinson_volatility(highs, lows, self.volatility_length)
        
        # Calculate RSI of volatility
        vol_rsi = self._rsi(pv, self.volatility_length)
        
        current_vol_rsi = vol_rsi[-1]
        prev_vol_rsi = vol_rsi[-2] if len(vol_rsi) > 1 else current_vol_rsi
        current_price = df['close'].iloc[-1]
        
        # Breakout zone: RSI crosses below 15 (low volatility = potential breakout)
        if current_vol_rsi < 15 and prev_vol_rsi >= 15:
            return Signal("BreakoutDetector", "BUY", 0.8, current_price,
                         f"Entering breakout zone (Vol RSI: {current_vol_rsi:.1f})")
        
        if current_vol_rsi < 30:
            strength = (30 - current_vol_rsi) / 30
            return Signal("BreakoutDetector", "BUY", strength * 0.6, current_price,
                         f"In breakout zone (Vol RSI: {current_vol_rsi:.1f})")
        
        return Signal("BreakoutDetector", "HOLD", 0, current_price,
                     f"No breakout (Vol RSI: {current_vol_rsi:.1f})")


class MarketReversals:
    """TC Market Reversals - CCI-based reversal detector.
    
    Uses modified CCI to identify overbought/oversold conditions.
    """
    
    def __init__(self, length: int = 20, overbought: float = 225, oversold: float = -225):
        self.length = length
        self.overbought = overbought
        self.oversold = oversold
    
    def _cci(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate modified CCI."""
        ohlc4 = (df['open'] + df['high'] + df['low'] + df['close']).values / 4
        
        n = len(ohlc4)
        result = np.zeros(n)
        
        for i in range(self.length, n):
            window = ohlc4[i-self.length:i]
            ma = np.mean(window)
            mean_dev = np.mean(np.abs(window - ma))
            
            if mean_dev > 0:
                result[i] = (ohlc4[i] - ma) / (0.015 * mean_dev)
        
        # Apply multiplier from original indicator
        return result * 1.277
    
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Analyze for reversal signals."""
        if len(df) < self.length + 1:
            return Signal("MarketReversals", "HOLD", 0, df['close'].iloc[-1], "Insufficient data")
        
        cci = self._cci(df)
        current_cci = cci[-1]
        current_price = df['close'].iloc[-1]
        
        if current_cci < self.oversold:
            strength = min(1.0, abs(current_cci - self.oversold) / 100)
            return Signal("MarketReversals", "BUY", 0.6 + strength * 0.3, current_price,
                         f"Oversold (CCI: {current_cci:.0f}) - Watch for pump")
        
        if current_cci > self.overbought:
            strength = min(1.0, (current_cci - self.overbought) / 100)
            return Signal("MarketReversals", "SELL", 0.6 + strength * 0.3, current_price,
                         f"Overbought (CCI: {current_cci:.0f}) - Watch for drop")
        
        return Signal("MarketReversals", "HOLD", 0, current_price,
                     f"Neutral (CCI: {current_cci:.0f})")


class TrendDashboard:
    """TC Trend Dashboard - Multi-indicator trend analysis.
    
    Combines RSI, Stochastic, MACD, and multiple MAs for trend confirmation.
    """
    
    def __init__(self):
        self.rsi_length = 14
        self.stoch_k = 14
        self.stoch_d = 3
        self.stoch_smooth = 3
        self.macd_fast = 12
        self.macd_slow = 25
        self.macd_signal = 9
    
    def _rsi(self, closes: np.ndarray, length: int = 14) -> float:
        """Calculate current RSI."""
        if len(closes) < length + 1:
            return 50.0
        
        deltas = np.diff(closes[-length-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _stochastic(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[float, float]:
        """Calculate Stochastic K and D."""
        if len(closes) < self.stoch_k + self.stoch_smooth:
            return 50.0, 50.0
        
        # Calculate %K
        k_values = []
        for i in range(self.stoch_smooth):
            idx = -(i + 1)
            window_high = np.max(highs[idx-self.stoch_k:idx] if idx < -1 else highs[-self.stoch_k:])
            window_low = np.min(lows[idx-self.stoch_k:idx] if idx < -1 else lows[-self.stoch_k:])
            
            if window_high - window_low > 0:
                k = 100 * (closes[idx] - window_low) / (window_high - window_low)
            else:
                k = 50.0
            k_values.append(k)
        
        k = np.mean(k_values)
        d = k  # Simplified - would need more history for proper D
        
        return k, d
    
    def _macd(self, closes: np.ndarray) -> Tuple[float, float]:
        """Calculate MACD and signal."""
        if len(closes) < self.macd_slow + self.macd_signal:
            return 0.0, 0.0
        
        # EMA calculation
        def ema(data, period):
            alpha = 2 / (period + 1)
            result = np.zeros(len(data))
            result[0] = data[0]
            for i in range(1, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
            return result
        
        fast_ema = ema(closes, self.macd_fast)
        slow_ema = ema(closes, self.macd_slow)
        macd_line = fast_ema - slow_ema
        signal_line = ema(macd_line, self.macd_signal)
        
        return macd_line[-1], signal_line[-1]
    
    def _sma(self, data: np.ndarray, period: int) -> float:
        """Calculate SMA."""
        if len(data) < period:
            return data[-1] if len(data) > 0 else 0
        return np.mean(data[-period:])
    
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Analyze trend using multiple indicators."""
        if len(df) < 200:
            return Signal("TrendDashboard", "HOLD", 0, df['close'].iloc[-1], "Insufficient data")
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        current_price = closes[-1]
        
        # Calculate all indicators
        rsi = self._rsi(closes)
        stoch_k, stoch_d = self._stochastic(highs, lows, closes)
        macd, signal = self._macd(closes)
        ma50 = self._sma(closes, 50)
        ma100 = self._sma(closes, 100)
        ma200 = self._sma(closes, 200)
        
        # Score each indicator
        bullish_count = 0
        total = 6
        
        if rsi > 50: bullish_count += 1
        if stoch_k > stoch_d: bullish_count += 1
        if macd > signal: bullish_count += 1
        if current_price > ma50: bullish_count += 1
        if current_price > ma100: bullish_count += 1
        if current_price > ma200: bullish_count += 1
        
        score = bullish_count / total
        
        details = f"RSI:{rsi:.0f} Stoch:{stoch_k:.0f} MACD:{'↑' if macd > signal else '↓'} "
        details += f"50MA:{'↑' if current_price > ma50 else '↓'} "
        details += f"100MA:{'↑' if current_price > ma100 else '↓'} "
        details += f"200MA:{'↑' if current_price > ma200 else '↓'}"
        
        if score >= 0.8:
            return Signal("TrendDashboard", "STRONG_BUY", score, current_price,
                         f"Strong uptrend ({bullish_count}/{total}) - {details}")
        elif score >= 0.6:
            return Signal("TrendDashboard", "BUY", score, current_price,
                         f"Uptrend ({bullish_count}/{total}) - {details}")
        elif score <= 0.2:
            return Signal("TrendDashboard", "STRONG_SELL", 1 - score, current_price,
                         f"Strong downtrend ({bullish_count}/{total}) - {details}")
        elif score <= 0.4:
            return Signal("TrendDashboard", "SELL", 1 - score, current_price,
                         f"Downtrend ({bullish_count}/{total}) - {details}")
        
        return Signal("TrendDashboard", "HOLD", 0.5, current_price,
                     f"Neutral ({bullish_count}/{total}) - {details}")


class WhaleMoneyFlow:
    """TC Whale Money Flow - Detects institutional money flow.
    
    Compares price action to volume-weighted money flow to detect
    whale accumulation or distribution.
    """
    
    def __init__(self, length: int = 14):
        self.length = length
    
    def _money_flow(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate whale money flow and price RSI."""
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['volume'].values
        
        n = len(closes)
        
        # Chaikin Money Flow adjustment
        adjustment = np.zeros(n)
        for i in range(n):
            if highs[i] != lows[i]:
                adjustment[i] = ((2 * closes[i] - lows[i] - highs[i]) / (highs[i] - lows[i])) * volumes[i]
        
        # Whale Money Flow (10-period)
        wmf = np.zeros(n)
        for i in range(10, n):
            vol_sum = np.sum(volumes[i-10:i])
            if vol_sum > 0:
                wmf[i] = np.sum(adjustment[i-10:i]) / vol_sum
        
        # Volume-weighted RSI
        upper = np.zeros(n)
        lower = np.zeros(n)
        
        for i in range(1, n):
            change = closes[i] - closes[i-1]
            if change > 0:
                upper[i] = volumes[i] * closes[i]
            elif change < 0:
                lower[i] = volumes[i] * closes[i]
        
        money_strength = np.zeros(n)
        for i in range(self.length, n):
            upper_sum = np.sum(upper[i-self.length:i])
            lower_sum = np.sum(lower[i-self.length:i])
            
            if lower_sum == 0:
                money_strength[i] = 100
            elif upper_sum == 0:
                money_strength[i] = 0
            else:
                money_strength[i] = 100 - (100 / (1 + upper_sum / lower_sum))
        
        # Price RSI (12-period)
        price_rsi = np.zeros(n)
        for i in range(12, n):
            gains = []
            losses = []
            for j in range(i-12, i):
                change = closes[j+1] - closes[j] if j+1 < n else 0
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(-change)
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                price_rsi[i] = 100
            elif avg_gain == 0:
                price_rsi[i] = 0
            else:
                price_rsi[i] = 100 - (100 / (1 + avg_gain / avg_loss))
        
        whale_flow = money_strength + wmf
        
        return whale_flow, price_rsi
    
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Analyze whale money flow."""
        if len(df) < self.length + 10:
            return Signal("WhaleMoneyFlow", "HOLD", 0, df['close'].iloc[-1], "Insufficient data")
        
        whale_flow, price_rsi = self._money_flow(df)
        
        current_whale = whale_flow[-1]
        current_price_rsi = price_rsi[-1]
        current_price = df['close'].iloc[-1]
        
        # Divergence detection
        # Bullish: Whale flow rising while price falling
        # Bearish: Whale flow falling while price rising
        
        divergence = current_whale - current_price_rsi
        
        if divergence > 20:  # Whale accumulation
            strength = min(1.0, divergence / 50)
            return Signal("WhaleMoneyFlow", "BUY", 0.6 + strength * 0.3, current_price,
                         f"Whale accumulation detected (Flow: {current_whale:.0f} vs Price: {current_price_rsi:.0f})")
        
        if divergence < -20:  # Whale distribution
            strength = min(1.0, abs(divergence) / 50)
            return Signal("WhaleMoneyFlow", "SELL", 0.6 + strength * 0.3, current_price,
                         f"Whale distribution detected (Flow: {current_whale:.0f} vs Price: {current_price_rsi:.0f})")
        
        return Signal("WhaleMoneyFlow", "HOLD", 0, current_price,
                     f"No divergence (Flow: {current_whale:.0f}, Price: {current_price_rsi:.0f})")


class SupportResistance:
    """TC Support/Resistance Levels - Identifies key price levels.
    
    Uses pivot points to identify support and resistance levels.
    """
    
    def __init__(self, pivot_length: int = 12):
        self.pivot_length = pivot_length
    
    def _find_pivots(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """Find pivot highs and lows."""
        highs = df['high'].values
        lows = df['low'].values
        n = len(highs)
        
        resistance_levels = []
        support_levels = []
        
        for i in range(self.pivot_length, n - self.pivot_length):
            # Pivot high
            is_pivot_high = True
            for j in range(i - self.pivot_length, i + self.pivot_length + 1):
                if j != i and highs[j] >= highs[i]:
                    is_pivot_high = False
                    break
            if is_pivot_high:
                resistance_levels.append(highs[i])
            
            # Pivot low
            is_pivot_low = True
            for j in range(i - self.pivot_length, i + self.pivot_length + 1):
                if j != i and lows[j] <= lows[i]:
                    is_pivot_low = False
                    break
            if is_pivot_low:
                support_levels.append(lows[i])
        
        return resistance_levels, support_levels
    
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Analyze support/resistance levels."""
        if len(df) < self.pivot_length * 2 + 1:
            return Signal("SupportResistance", "HOLD", 0, df['close'].iloc[-1], "Insufficient data")
        
        resistance_levels, support_levels = self._find_pivots(df)
        current_price = df['close'].iloc[-1]
        
        if not resistance_levels and not support_levels:
            return Signal("SupportResistance", "HOLD", 0, current_price, "No levels found")
        
        # Find nearest levels
        nearest_resistance = None
        nearest_support = None
        
        for r in sorted(resistance_levels, reverse=True):
            if r > current_price:
                nearest_resistance = r
                break
        
        for s in sorted(support_levels):
            if s < current_price:
                nearest_support = s
                break
        
        # Calculate position between levels
        if nearest_resistance and nearest_support:
            range_size = nearest_resistance - nearest_support
            if range_size > 0:
                position = (current_price - nearest_support) / range_size
                
                if position < 0.2:
                    return Signal("SupportResistance", "BUY", 0.7, current_price,
                                 f"Near support ${nearest_support:.2f} (R: ${nearest_resistance:.2f})")
                elif position > 0.8:
                    return Signal("SupportResistance", "SELL", 0.7, current_price,
                                 f"Near resistance ${nearest_resistance:.2f} (S: ${nearest_support:.2f})")
        
        details = f"S: ${nearest_support:.2f}" if nearest_support else "S: N/A"
        details += f" | R: ${nearest_resistance:.2f}" if nearest_resistance else " | R: N/A"
        
        return Signal("SupportResistance", "HOLD", 0, current_price, details)


class TradesInFavor:
    """TC Trades In Favor - Probability-based pump/drop prediction.
    
    Calculates probability of price pump or drop based on volume-weighted
    trend analysis. Returns 0-100 where:
    - 0-20: 80-99% chance of pump (strong buy zone)
    - 20-50: Moderate pump probability
    - 50: Neutral
    - 50-80: Moderate drop probability
    - 80-100: 80-99% chance of drop (strong sell zone)
    """
    
    def __init__(self):
        pass
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate the Trades In Favor value (0-100)."""
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        volumes = df['volume'].values
        
        n = len(closes)
        if n < 20:
            return 50.0  # Neutral
        
        # Calculate OHLC4
        ohlc4 = (opens + highs + lows + closes) / 4
        
        # Trend strength calculation (Chaikin-style)
        calculations = np.zeros(n)
        for i in range(n):
            if highs[i] != lows[i]:
                calculations[i] = ((2 * closes[i] - lows[i] - highs[i]) / (highs[i] - lows[i])) * volumes[i]
        
        # Volume-weighted trend (8-period for short-term)
        toptrend = 0.0
        lowertrend = 0.0
        
        for i in range(max(0, n-8), n):
            change = ohlc4[i] - ohlc4[i-1] if i > 0 else 0
            if change > 0:
                toptrend += volumes[i] * ohlc4[i]
            elif change < 0:
                lowertrend += volumes[i] * ohlc4[i]
        
        # Calculate trendline (RSI-style)
        if lowertrend == 0:
            trendline = 100.0
        elif toptrend == 0:
            trendline = 0.0
        else:
            trendline = 100.0 - (100.0 / (1.0 + toptrend / lowertrend))
        
        # Second trend calculation (20-period for confirmation)
        toptrend2 = 0.0
        lowertrend2 = 0.0
        
        for i in range(max(0, n-20), n):
            change = closes[i] - closes[i-1] if i > 0 else 0
            if change > 0:
                toptrend2 += volumes[i] * closes[i]
            elif change < 0:
                lowertrend2 += volumes[i] * closes[i]
        
        if lowertrend2 == 0:
            trendline2 = 100.0
        elif toptrend2 == 0:
            trendline2 = 0.0
        else:
            trendline2 = 100.0 - (100.0 / (1.0 + toptrend2 / lowertrend2))
        
        # Trend strength from calculations
        vol_sum = np.sum(volumes[-1:])
        if vol_sum > 0:
            trendstrength = np.sum(calculations[-1:]) / vol_sum
            trendstrength2 = np.sum(calculations[-1:]) / vol_sum
        else:
            trendstrength = 0
            trendstrength2 = 0
        
        # Combined TC value
        if trendline2 != 0:
            tc = trendline + trendstrength / trendline2 + trendstrength2
        else:
            tc = trendline + trendstrength + trendstrength2
        
        # Clamp to 0-100
        return max(0, min(100, tc))
    
    def get_probability(self, tc_value: float) -> tuple[str, float]:
        """Convert TC value to probability and direction."""
        if tc_value >= 99:
            return "DROP", 0.99
        elif tc_value >= 81:
            return "DROP", (tc_value - 50) / 50
        elif tc_value > 50:
            return "DROP", (tc_value - 50) / 50
        elif tc_value <= 1:
            return "PUMP", 0.99
        elif tc_value <= 19:
            return "PUMP", (50 - tc_value) / 50
        elif tc_value < 50:
            return "PUMP", (50 - tc_value) / 50
        else:
            return "NEUTRAL", 0.5
    
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Analyze for pump/drop probability."""
        if len(df) < 20:
            return Signal("TradesInFavor", "HOLD", 0, df['close'].iloc[-1], "Insufficient data")
        
        tc = self._calculate_trend_strength(df)
        direction, probability = self.get_probability(tc)
        current_price = df['close'].iloc[-1]
        
        # Strong signals (>80% probability)
        if direction == "PUMP" and probability >= 0.8:
            return Signal("TradesInFavor", "STRONG_BUY", probability, current_price,
                         f"🟢 {probability:.0%} chance of pump (TC: {tc:.1f})")
        
        if direction == "DROP" and probability >= 0.8:
            return Signal("TradesInFavor", "STRONG_SELL", probability, current_price,
                         f"🔴 {probability:.0%} chance of drop (TC: {tc:.1f})")
        
        # Moderate signals (60-80%)
        if direction == "PUMP" and probability >= 0.6:
            return Signal("TradesInFavor", "BUY", probability, current_price,
                         f"{probability:.0%} chance of pump (TC: {tc:.1f})")
        
        if direction == "DROP" and probability >= 0.6:
            return Signal("TradesInFavor", "SELL", probability, current_price,
                         f"{probability:.0%} chance of drop (TC: {tc:.1f})")
        
        return Signal("TradesInFavor", "HOLD", 0.5, current_price,
                     f"Neutral - {probability:.0%} {direction.lower()} (TC: {tc:.1f})")


class AdvancedSignalGenerator:
    """Combines all indicators for comprehensive signal generation."""
    
    def __init__(self):
        self.top_bottom = TopBottomFinder()
        self.breakout = BreakoutDetector()
        self.reversals = MarketReversals()
        self.trend = TrendDashboard()
        self.whale = WhaleMoneyFlow()
        self.sr_levels = SupportResistance()
        self.trades_in_favor = TradesInFavor()
    
    def analyze_all(self, df: pd.DataFrame) -> Dict[str, Signal]:
        """Run all indicators and return signals."""
        return {
            "top_bottom": self.top_bottom.analyze(df),
            "breakout": self.breakout.analyze(df),
            "reversals": self.reversals.analyze(df),
            "trend": self.trend.analyze(df),
            "whale": self.whale.analyze(df),
            "support_resistance": self.sr_levels.analyze(df),
            "trades_in_favor": self.trades_in_favor.analyze(df),
        }
    
    def get_consensus(self, df: pd.DataFrame) -> Signal:
        """Get consensus signal from all indicators."""
        signals = self.analyze_all(df)
        
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        weights = {
            "top_bottom": 2.0,
            "breakout": 1.5,
            "reversals": 1.5,
            "trend": 1.0,
            "whale": 2.0,
            "support_resistance": 1.0,
            "trades_in_favor": 3.0,  # Highest weight - probability-based
        }
        
        reasons = []
        
        for name, signal in signals.items():
            weight = weights.get(name, 1.0)
            
            if signal.signal_type in ["BUY", "STRONG_BUY"]:
                multiplier = 1.5 if "STRONG" in signal.signal_type else 1.0
                buy_score += signal.strength * weight * multiplier
                if signal.strength > 0.5:
                    reasons.append(f"{name}: {signal.signal_type}")
            elif signal.signal_type in ["SELL", "STRONG_SELL"]:
                multiplier = 1.5 if "STRONG" in signal.signal_type else 1.0
                sell_score += signal.strength * weight * multiplier
                if signal.strength > 0.5:
                    reasons.append(f"{name}: {signal.signal_type}")
            
            total_weight += weight
        
        current_price = df['close'].iloc[-1]
        
        if total_weight == 0:
            return Signal("Consensus", "HOLD", 0, current_price, "No signals")
        
        buy_pct = buy_score / total_weight
        sell_pct = sell_score / total_weight
        
        if buy_pct > sell_pct and buy_pct > 0.5:
            signal_type = "STRONG_BUY" if buy_pct > 0.7 else "BUY"
            return Signal("Consensus", signal_type, buy_pct, current_price,
                         f"{len([r for r in reasons if 'BUY' in r])}/6 indicators bullish: {', '.join(reasons[:3])}")
        
        if sell_pct > buy_pct and sell_pct > 0.5:
            signal_type = "STRONG_SELL" if sell_pct > 0.7 else "SELL"
            return Signal("Consensus", signal_type, sell_pct, current_price,
                         f"{len([r for r in reasons if 'SELL' in r])}/6 indicators bearish: {', '.join(reasons[:3])}")
        
        return Signal("Consensus", "HOLD", max(buy_pct, sell_pct), current_price,
                     f"Mixed signals (Buy: {buy_pct:.0%}, Sell: {sell_pct:.0%})")
