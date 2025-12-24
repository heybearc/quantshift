"""Trading strategy framework with multiple strategy support."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd
import numpy as np
import structlog

from quantshift_core.indicators import TechnicalIndicators, MultiTimeframeAnalyzer
from quantshift_core.position_sizing import PositionSizer

logger = structlog.get_logger()


class Signal(Enum):
    """Trading signals."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy(ABC):
    """Base class for trading strategies."""

    def __init__(self, name: str, capital_allocation: float = 1.0):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name
            capital_allocation: Percentage of capital allocated (0-1)
        """
        self.name = name
        self.capital_allocation = capital_allocation
        self.indicators = TechnicalIndicators()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.trades: List[Dict] = []
        self.active_positions: Dict[str, Dict] = {}

    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        daily_data: Optional[pd.DataFrame] = None,
        hourly_data: Optional[pd.DataFrame] = None
    ) -> Signal:
        """
        Generate trading signal.
        
        Args:
            symbol: Trading symbol
            data: Current timeframe OHLCV data
            daily_data: Daily timeframe data (optional)
            hourly_data: Hourly timeframe data (optional)
            
        Returns:
            Signal (BUY, SELL, or HOLD)
        """
        pass

    @abstractmethod
    def calculate_stop_loss(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate stop loss price."""
        pass

    @abstractmethod
    def calculate_take_profit(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate take profit price."""
        pass

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        account_balance: float,
        sizer: PositionSizer
    ) -> int:
        """
        Calculate position size using position sizer.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            account_balance: Current account balance
            sizer: PositionSizer instance
            
        Returns:
            Number of shares to buy
        """
        # Adjust account balance by capital allocation
        allocated_capital = account_balance * self.capital_allocation
        
        # Create temporary sizer with allocated capital
        temp_sizer = PositionSizer(
            account_balance=allocated_capital,
            max_position_pct=sizer.max_position_pct,
            max_portfolio_risk=sizer.max_portfolio_risk
        )
        
        return temp_sizer.fixed_fractional(entry_price, stop_loss)

    def record_trade(self, trade: Dict) -> None:
        """Record a trade for performance tracking."""
        self.trades.append(trade)
        logger.info("trade_recorded", strategy=self.name, **trade)

    def get_performance_metrics(self) -> Dict:
        """Calculate strategy performance metrics."""
        if not self.trades:
            return {"error": "No trades recorded"}
        
        closed_trades = [t for t in self.trades if t.get("action") == "SELL"]
        if not closed_trades:
            return {"error": "No closed trades"}
        
        winning_trades = [t for t in closed_trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in closed_trades if t.get("pnl", 0) <= 0]
        
        total_trades = len(closed_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t.get("pnl", 0) for t in winning_trades)
        total_loss = abs(sum(t.get("pnl", 0) for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return {
            "strategy": self.name,
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate * 100,
            "profit_factor": profit_factor,
            "total_pnl": sum(t.get("pnl", 0) for t in closed_trades)
        }


class MovingAverageCrossover(Strategy):
    """Moving Average Crossover strategy."""

    def __init__(
        self,
        capital_allocation: float = 0.33,
        fast_period: int = 20,
        slow_period: int = 50,
        atr_multiplier: float = 2.0
    ):
        """Initialize MA Crossover strategy."""
        super().__init__("MA_Crossover", capital_allocation)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.atr_multiplier = atr_multiplier

    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        daily_data: Optional[pd.DataFrame] = None,
        hourly_data: Optional[pd.DataFrame] = None
    ) -> Signal:
        """Generate signal based on MA crossover."""
        if len(data) < self.slow_period:
            return Signal.HOLD
        
        # Calculate moving averages
        fast_ma = self.indicators.sma(data['close'], self.fast_period)
        slow_ma = self.indicators.sma(data['close'], self.slow_period)
        
        current_fast = fast_ma.iloc[-1]
        current_slow = slow_ma.iloc[-1]
        prev_fast = fast_ma.iloc[-2]
        prev_slow = slow_ma.iloc[-2]
        
        # Check multi-timeframe if available
        if daily_data is not None and hourly_data is not None:
            should_trade, reason = self.mtf_analyzer.should_trade(
                symbol, daily_data, hourly_data, data, "long"
            )
            if not should_trade:
                logger.debug("mtf_rejected", strategy=self.name, reason=reason)
                return Signal.HOLD
        
        # Golden cross (fast crosses above slow)
        if current_fast > current_slow and prev_fast <= prev_slow:
            # Check RSI not overbought
            rsi = self.indicators.rsi(data['close']).iloc[-1]
            if rsi < 70:
                logger.info("signal_generated", strategy=self.name, signal="BUY", reason="golden_cross")
                return Signal.BUY
        
        # Death cross (fast crosses below slow)
        elif current_fast < current_slow and prev_fast >= prev_slow:
            # Check RSI not oversold
            rsi = self.indicators.rsi(data['close']).iloc[-1]
            if rsi > 30:
                logger.info("signal_generated", strategy=self.name, signal="SELL", reason="death_cross")
                return Signal.SELL
        
        return Signal.HOLD

    def calculate_stop_loss(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate stop loss using ATR."""
        atr = self.indicators.atr(data['high'], data['low'], data['close']).iloc[-1]
        return entry_price - (atr * self.atr_multiplier)

    def calculate_take_profit(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate take profit using ATR."""
        atr = self.indicators.atr(data['high'], data['low'], data['close']).iloc[-1]
        return entry_price + (atr * self.atr_multiplier * 1.5)


class MeanReversion(Strategy):
    """Mean Reversion strategy using RSI and Bollinger Bands."""

    def __init__(
        self,
        capital_allocation: float = 0.33,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        bb_period: int = 20,
        bb_std: float = 2.0
    ):
        """Initialize Mean Reversion strategy."""
        super().__init__("Mean_Reversion", capital_allocation)
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_period = bb_period
        self.bb_std = bb_std

    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        daily_data: Optional[pd.DataFrame] = None,
        hourly_data: Optional[pd.DataFrame] = None
    ) -> Signal:
        """Generate signal based on mean reversion."""
        if len(data) < max(self.rsi_period, self.bb_period):
            return Signal.HOLD
        
        # Calculate indicators
        rsi = self.indicators.rsi(data['close'], self.rsi_period)
        bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(
            data['close'], self.bb_period, self.bb_std
        )
        
        current_price = data['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        
        # Oversold condition (buy signal)
        if current_rsi < self.rsi_oversold and prev_rsi >= self.rsi_oversold:
            # Confirm with Bollinger Band
            if current_price <= bb_lower.iloc[-1]:
                logger.info("signal_generated", strategy=self.name, signal="BUY", reason="oversold_bb_lower")
                return Signal.BUY
        
        # Overbought condition (sell signal)
        elif current_rsi > self.rsi_overbought and prev_rsi <= self.rsi_overbought:
            # Confirm with Bollinger Band
            if current_price >= bb_upper.iloc[-1]:
                logger.info("signal_generated", strategy=self.name, signal="SELL", reason="overbought_bb_upper")
                return Signal.SELL
        
        # Mean reversion from extremes
        if current_price < bb_lower.iloc[-1] and current_rsi < 35:
            logger.info("signal_generated", strategy=self.name, signal="BUY", reason="extreme_oversold")
            return Signal.BUY
        
        if current_price > bb_upper.iloc[-1] and current_rsi > 65:
            logger.info("signal_generated", strategy=self.name, signal="SELL", reason="extreme_overbought")
            return Signal.SELL
        
        return Signal.HOLD

    def calculate_stop_loss(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate stop loss using Bollinger Bands."""
        _, bb_middle, bb_lower = self.indicators.bollinger_bands(
            data['close'], self.bb_period, self.bb_std
        )
        # Stop loss below lower band
        return bb_lower.iloc[-1] * 0.98

    def calculate_take_profit(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate take profit at middle band."""
        _, bb_middle, _ = self.indicators.bollinger_bands(
            data['close'], self.bb_period, self.bb_std
        )
        # Take profit at middle band
        return bb_middle.iloc[-1]


class Breakout(Strategy):
    """Breakout strategy using volume and resistance levels."""

    def __init__(
        self,
        capital_allocation: float = 0.34,
        lookback_period: int = 20,
        volume_multiplier: float = 1.5,
        atr_multiplier: float = 2.5
    ):
        """Initialize Breakout strategy."""
        super().__init__("Breakout", capital_allocation)
        self.lookback_period = lookback_period
        self.volume_multiplier = volume_multiplier
        self.atr_multiplier = atr_multiplier

    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        daily_data: Optional[pd.DataFrame] = None,
        hourly_data: Optional[pd.DataFrame] = None
    ) -> Signal:
        """Generate signal based on breakouts."""
        if len(data) < self.lookback_period:
            return Signal.HOLD
        
        # Get support/resistance levels
        levels = self.mtf_analyzer.get_support_resistance(data, self.lookback_period)
        
        current_price = data['close'].iloc[-1]
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(window=self.lookback_period).mean().iloc[-1]
        
        # Calculate ADX for trend strength
        adx = self.indicators.adx(data['high'], data['low'], data['close']).iloc[-1]
        
        # Volume confirmation
        volume_confirmed = current_volume > (avg_volume * self.volume_multiplier)
        
        # Resistance breakout (buy signal)
        if levels['resistance']:
            nearest_resistance = min(levels['resistance'], key=lambda x: abs(x - current_price))
            
            if current_price > nearest_resistance and volume_confirmed and adx > 25:
                logger.info(
                    "signal_generated",
                    strategy=self.name,
                    signal="BUY",
                    reason="resistance_breakout",
                    resistance=nearest_resistance,
                    adx=adx
                )
                return Signal.BUY
        
        # Support breakdown (sell signal)
        if levels['support']:
            nearest_support = min(levels['support'], key=lambda x: abs(x - current_price))
            
            if current_price < nearest_support and volume_confirmed and adx > 25:
                logger.info(
                    "signal_generated",
                    strategy=self.name,
                    signal="SELL",
                    reason="support_breakdown",
                    support=nearest_support,
                    adx=adx
                )
                return Signal.SELL
        
        return Signal.HOLD

    def calculate_stop_loss(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate stop loss using ATR."""
        atr = self.indicators.atr(data['high'], data['low'], data['close']).iloc[-1]
        return entry_price - (atr * self.atr_multiplier)

    def calculate_take_profit(self, entry_price: float, data: pd.DataFrame) -> float:
        """Calculate take profit using ATR."""
        atr = self.indicators.atr(data['high'], data['low'], data['close']).iloc[-1]
        return entry_price + (atr * self.atr_multiplier * 2.0)
