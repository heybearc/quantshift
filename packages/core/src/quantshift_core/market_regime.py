"""
Market Regime Detection System

Detects market conditions and classifies them into regimes:
- Bull Trending: Uptrend + low volatility
- Bear Trending: Downtrend + low volatility  
- High Vol Choppy: High volatility + no clear trend
- Low Vol Range: Low volatility + sideways
- Crisis: Extreme volatility or VIX spike

Uses multiple indicators:
- Trend: 50-day SMA slope
- Volatility: 20-day ATR / 100-day ATR ratio
- Breadth: % of stocks above 200-day MA (if available)
- Fear: VIX level (if available)
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np
import structlog

logger = structlog.get_logger()


class MarketRegime(Enum):
    """Market regime classifications."""
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    HIGH_VOL_CHOPPY = "high_vol_choppy"
    LOW_VOL_RANGE = "low_vol_range"
    CRISIS = "crisis"
    UNKNOWN = "unknown"


class MarketRegimeDetector:
    """
    Detects and classifies market regimes.
    
    Regime determination:
    1. Calculate trend strength (50-day SMA slope)
    2. Calculate volatility ratio (20-day ATR / 100-day ATR)
    3. Optionally use VIX and market breadth
    4. Classify into one of 5 regimes
    5. Require 3 consecutive days to confirm regime change
    """
    
    def __init__(
        self,
        trend_threshold: float = 0.5,  # degrees per day
        high_vol_threshold: float = 1.5,  # ATR ratio
        low_vol_threshold: float = 0.8,  # ATR ratio
        crisis_vol_threshold: float = 2.0,  # ATR ratio
        crisis_vix_threshold: float = 30.0,  # VIX level
        confirmation_days: int = 3
    ):
        """
        Initialize regime detector.
        
        Args:
            trend_threshold: Minimum slope (degrees/day) to consider trending
            high_vol_threshold: ATR ratio above this = high volatility
            low_vol_threshold: ATR ratio below this = low volatility
            crisis_vol_threshold: ATR ratio above this = crisis
            crisis_vix_threshold: VIX level above this = crisis
            confirmation_days: Days required to confirm regime change
        """
        self.trend_threshold = trend_threshold
        self.high_vol_threshold = high_vol_threshold
        self.low_vol_threshold = low_vol_threshold
        self.crisis_vol_threshold = crisis_vol_threshold
        self.crisis_vix_threshold = crisis_vix_threshold
        self.confirmation_days = confirmation_days
        
        self.current_regime = MarketRegime.UNKNOWN
        self.regime_history = []
        self.pending_regime = None
        self.pending_days = 0
        
        self.logger = logger.bind(component="MarketRegimeDetector")
        
        self.logger.info(
            "regime_detector_initialized",
            trend_threshold=trend_threshold,
            high_vol_threshold=high_vol_threshold,
            confirmation_days=confirmation_days
        )
    
    def calculate_trend_slope(self, prices: pd.Series, period: int = 50) -> float:
        """
        Calculate trend slope in degrees per day.
        
        Uses linear regression on the last N days of prices.
        Returns slope in degrees per day.
        """
        if len(prices) < period:
            return 0.0
        
        recent_prices = prices.iloc[-period:]
        x = np.arange(len(recent_prices))
        y = recent_prices.values
        
        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        # Convert to degrees per day
        # slope is price change per day
        # degrees = arctan(slope / avg_price) * 180 / pi
        avg_price = recent_prices.mean()
        degrees = np.arctan(slope / avg_price) * 180 / np.pi
        
        return degrees
    
    def calculate_volatility_ratio(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        short_period: int = 20,
        long_period: int = 100
    ) -> float:
        """
        Calculate volatility ratio (short-term ATR / long-term ATR).
        
        Ratio > 1.5 = high volatility
        Ratio < 0.8 = low volatility
        """
        if len(close) < long_period:
            return 1.0
        
        # Calculate True Range
        high_low = high - low
        high_close = abs(high - close.shift(1))
        low_close = abs(low - close.shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate ATRs
        atr_short = tr.rolling(window=short_period).mean().iloc[-1]
        atr_long = tr.rolling(window=long_period).mean().iloc[-1]
        
        if atr_long == 0:
            return 1.0
        
        ratio = atr_short / atr_long
        return ratio
    
    def classify_regime(
        self,
        trend_slope: float,
        vol_ratio: float,
        vix: Optional[float] = None
    ) -> MarketRegime:
        """
        Classify market regime based on indicators.
        
        Args:
            trend_slope: Trend slope in degrees per day
            vol_ratio: Volatility ratio (short ATR / long ATR)
            vix: VIX level (optional)
            
        Returns:
            MarketRegime classification
        """
        # Crisis detection (highest priority)
        if vol_ratio > self.crisis_vol_threshold:
            return MarketRegime.CRISIS
        if vix is not None and vix > self.crisis_vix_threshold:
            return MarketRegime.CRISIS
        
        # High volatility choppy
        if vol_ratio > self.high_vol_threshold:
            return MarketRegime.HIGH_VOL_CHOPPY
        
        # Low volatility range
        if vol_ratio < self.low_vol_threshold and abs(trend_slope) < self.trend_threshold:
            return MarketRegime.LOW_VOL_RANGE
        
        # Trending markets
        if abs(trend_slope) >= self.trend_threshold:
            if trend_slope > 0:
                return MarketRegime.BULL_TRENDING
            else:
                return MarketRegime.BEAR_TRENDING
        
        # Default to choppy if no clear regime
        return MarketRegime.HIGH_VOL_CHOPPY
    
    def detect_regime(
        self,
        market_data: pd.DataFrame,
        vix_data: Optional[pd.DataFrame] = None
    ) -> Tuple[MarketRegime, Dict]:
        """
        Detect current market regime.
        
        Args:
            market_data: DataFrame with OHLC data
            vix_data: Optional DataFrame with VIX data
            
        Returns:
            Tuple of (regime, indicators_dict)
        """
        # Calculate indicators
        trend_slope = self.calculate_trend_slope(market_data['Close'])
        vol_ratio = self.calculate_volatility_ratio(
            market_data['High'],
            market_data['Low'],
            market_data['Close']
        )
        
        vix = None
        if vix_data is not None and len(vix_data) > 0:
            vix = vix_data['Close'].iloc[-1]
        
        # Classify regime
        detected_regime = self.classify_regime(trend_slope, vol_ratio, vix)
        
        # Regime confirmation logic
        if detected_regime != self.current_regime:
            if detected_regime == self.pending_regime:
                self.pending_days += 1
                
                if self.pending_days >= self.confirmation_days:
                    # Regime change confirmed
                    old_regime = self.current_regime
                    self.current_regime = detected_regime
                    self.pending_regime = None
                    self.pending_days = 0
                    
                    self.regime_history.append({
                        'timestamp': datetime.utcnow(),
                        'regime': detected_regime,
                        'trend_slope': trend_slope,
                        'vol_ratio': vol_ratio,
                        'vix': vix
                    })
                    
                    self.logger.info(
                        "regime_change_confirmed",
                        old_regime=old_regime.value,
                        new_regime=detected_regime.value,
                        trend_slope=trend_slope,
                        vol_ratio=vol_ratio
                    )
            else:
                # New pending regime
                self.pending_regime = detected_regime
                self.pending_days = 1
                
                self.logger.debug(
                    "regime_change_pending",
                    current=self.current_regime.value,
                    pending=detected_regime.value,
                    days=1
                )
        else:
            # Regime unchanged, reset pending
            self.pending_regime = None
            self.pending_days = 0
        
        indicators = {
            'regime': self.current_regime,
            'pending_regime': self.pending_regime,
            'pending_days': self.pending_days,
            'trend_slope': trend_slope,
            'vol_ratio': vol_ratio,
            'vix': vix,
            'confidence': 1.0 - (self.pending_days / self.confirmation_days) if self.pending_regime else 1.0
        }
        
        return self.current_regime, indicators
    
    def get_regime_allocation(self, regime: Optional[MarketRegime] = None) -> Dict[str, float]:
        """
        Get recommended strategy allocation for current or specified regime.
        
        Returns:
            Dict mapping strategy name to allocation percentage (0-1)
        """
        if regime is None:
            regime = self.current_regime
        
        # Default allocations by regime
        allocations = {
            MarketRegime.BULL_TRENDING: {
                'BollingerBounce': 0.30,
                'RSIMeanReversion': 0.70  # Favor mean reversion in strong trends
            },
            MarketRegime.BEAR_TRENDING: {
                'BollingerBounce': 0.40,
                'RSIMeanReversion': 0.60
            },
            MarketRegime.HIGH_VOL_CHOPPY: {
                'BollingerBounce': 0.70,  # Bollinger excels in choppy markets
                'RSIMeanReversion': 0.30
            },
            MarketRegime.LOW_VOL_RANGE: {
                'BollingerBounce': 0.50,
                'RSIMeanReversion': 0.50  # Equal allocation in range-bound
            },
            MarketRegime.CRISIS: {
                'BollingerBounce': 0.20,  # Minimal trading in crisis
                'RSIMeanReversion': 0.20  # 60% cash
            },
            MarketRegime.UNKNOWN: {
                'BollingerBounce': 0.60,  # Default allocation
                'RSIMeanReversion': 0.40
            }
        }
        
        return allocations.get(regime, allocations[MarketRegime.UNKNOWN])
    
    def get_risk_multiplier(self, regime: Optional[MarketRegime] = None) -> float:
        """
        Get risk multiplier for position sizing based on regime.
        
        Returns:
            Multiplier for risk per trade (1.0 = normal, 0.5 = half size, etc.)
        """
        if regime is None:
            regime = self.current_regime
        
        risk_multipliers = {
            MarketRegime.BULL_TRENDING: 1.0,
            MarketRegime.BEAR_TRENDING: 0.8,
            MarketRegime.HIGH_VOL_CHOPPY: 0.5,
            MarketRegime.LOW_VOL_RANGE: 1.0,
            MarketRegime.CRISIS: 0.25,
            MarketRegime.UNKNOWN: 1.0
        }
        
        return risk_multipliers.get(regime, 1.0)
