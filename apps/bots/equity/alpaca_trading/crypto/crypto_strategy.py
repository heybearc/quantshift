"""Crypto trading strategies.

Implements crypto-optimized strategies that work well with 24/7 volatile markets:
- RSI (Relative Strength Index) - mean reversion
- Bollinger Bands - volatility breakouts
- Momentum - trend following
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd

from .crypto_config import crypto_config

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal from a strategy."""
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    strength: float  # 0.0 to 1.0
    reason: str
    price: float
    timestamp: datetime
    strategy: str
    
    def __str__(self):
        return f"{self.action} {self.symbol} @ ${self.price:.2f} ({self.reason})"


class CryptoStrategy(ABC):
    """Base class for crypto trading strategies."""
    
    def __init__(self, name: str):
        self.name = name
        self.config = crypto_config
    
    @abstractmethod
    def analyze(self, symbol: str, df: pd.DataFrame, current_price: float) -> Signal:
        """Analyze price data and generate a trading signal."""
        pass
    
    def calculate_position_size(self, price: float, portfolio_value: float) -> float:
        """Calculate position size based on config."""
        max_by_fixed = self.config.position_size_usd / price
        max_by_pct = (portfolio_value * self.config.max_portfolio_pct) / price
        return min(max_by_fixed, max_by_pct)


class RSIStrategy(CryptoStrategy):
    """RSI-based mean reversion strategy.
    
    Buy when RSI < oversold threshold (default 30)
    Sell when RSI > overbought threshold (default 70)
    """
    
    def __init__(self):
        super().__init__("RSI")
        self.period = self.config.rsi_period
        self.oversold = self.config.rsi_oversold
        self.overbought = self.config.rsi_overbought
    
    def calculate_rsi(self, prices: pd.Series) -> float:
        """Calculate RSI for the given price series."""
        if len(prices) < self.period + 1:
            return 50.0  # Neutral if not enough data
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def analyze(self, symbol: str, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate signal based on RSI."""
        if df.empty or len(df) < self.period + 1:
            return Signal(
                symbol=symbol,
                action="HOLD",
                strength=0.0,
                reason="Insufficient data",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        
        rsi = self.calculate_rsi(df["close"])
        
        if rsi < self.oversold:
            strength = (self.oversold - rsi) / self.oversold
            return Signal(
                symbol=symbol,
                action="BUY",
                strength=min(strength, 1.0),
                reason=f"RSI oversold at {rsi:.1f}",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        elif rsi > self.overbought:
            strength = (rsi - self.overbought) / (100 - self.overbought)
            return Signal(
                symbol=symbol,
                action="SELL",
                strength=min(strength, 1.0),
                reason=f"RSI overbought at {rsi:.1f}",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        else:
            return Signal(
                symbol=symbol,
                action="HOLD",
                strength=0.0,
                reason=f"RSI neutral at {rsi:.1f}",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )


class BollingerStrategy(CryptoStrategy):
    """Bollinger Bands volatility strategy.
    
    Buy when price touches lower band (oversold)
    Sell when price touches upper band (overbought)
    """
    
    def __init__(self):
        super().__init__("Bollinger")
        self.period = self.config.bb_period
        self.std_dev = self.config.bb_std_dev
    
    def calculate_bands(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate Bollinger Bands."""
        if len(prices) < self.period:
            return {"upper": 0, "middle": 0, "lower": 0, "width": 0}
        
        middle = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()
        
        upper = middle + (std * self.std_dev)
        lower = middle - (std * self.std_dev)
        
        return {
            "upper": float(upper.iloc[-1]),
            "middle": float(middle.iloc[-1]),
            "lower": float(lower.iloc[-1]),
            "width": float((upper.iloc[-1] - lower.iloc[-1]) / middle.iloc[-1]) if middle.iloc[-1] > 0 else 0
        }
    
    def analyze(self, symbol: str, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate signal based on Bollinger Bands."""
        if df.empty or len(df) < self.period:
            return Signal(
                symbol=symbol,
                action="HOLD",
                strength=0.0,
                reason="Insufficient data",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        
        bands = self.calculate_bands(df["close"])
        
        if bands["lower"] == 0:
            return Signal(
                symbol=symbol,
                action="HOLD",
                strength=0.0,
                reason="Cannot calculate bands",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        
        # Calculate position within bands (0 = lower, 1 = upper)
        band_range = bands["upper"] - bands["lower"]
        if band_range > 0:
            position = (current_price - bands["lower"]) / band_range
        else:
            position = 0.5
        
        if current_price <= bands["lower"]:
            strength = min(1.0, (bands["lower"] - current_price) / bands["lower"] * 10)
            return Signal(
                symbol=symbol,
                action="BUY",
                strength=strength,
                reason=f"Price at lower band (${bands['lower']:.2f})",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        elif current_price >= bands["upper"]:
            strength = min(1.0, (current_price - bands["upper"]) / bands["upper"] * 10)
            return Signal(
                symbol=symbol,
                action="SELL",
                strength=strength,
                reason=f"Price at upper band (${bands['upper']:.2f})",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        else:
            return Signal(
                symbol=symbol,
                action="HOLD",
                strength=0.0,
                reason=f"Price within bands ({position:.0%} from lower)",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )


class MomentumStrategy(CryptoStrategy):
    """Momentum-based trend following strategy.
    
    Buy when momentum is strongly positive
    Sell when momentum is strongly negative
    """
    
    def __init__(self):
        super().__init__("Momentum")
        self.period = self.config.momentum_period
        self.threshold = self.config.momentum_threshold
    
    def calculate_momentum(self, prices: pd.Series) -> float:
        """Calculate momentum as percentage change over period."""
        if len(prices) < self.period + 1:
            return 0.0
        
        current = prices.iloc[-1]
        past = prices.iloc[-self.period - 1]
        
        if past > 0:
            return (current - past) / past
        return 0.0
    
    def analyze(self, symbol: str, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate signal based on momentum."""
        if df.empty or len(df) < self.period + 1:
            return Signal(
                symbol=symbol,
                action="HOLD",
                strength=0.0,
                reason="Insufficient data",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        
        momentum = self.calculate_momentum(df["close"])
        
        if momentum > self.threshold:
            strength = min(1.0, momentum / (self.threshold * 2))
            return Signal(
                symbol=symbol,
                action="BUY",
                strength=strength,
                reason=f"Strong upward momentum ({momentum:.1%})",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        elif momentum < -self.threshold:
            strength = min(1.0, abs(momentum) / (self.threshold * 2))
            return Signal(
                symbol=symbol,
                action="SELL",
                strength=strength,
                reason=f"Strong downward momentum ({momentum:.1%})",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
        else:
            return Signal(
                symbol=symbol,
                action="HOLD",
                strength=0.0,
                reason=f"Weak momentum ({momentum:.1%})",
                price=current_price,
                timestamp=datetime.now(),
                strategy=self.name
            )
