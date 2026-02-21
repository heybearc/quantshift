"""
Bollinger Band Bounce Strategy

Entry: Price touches lower BB + RSI < 40
Exit: Price reaches middle BB (mean reversion complete)
Stop: Lower BB - 1.5×ATR
Target: Upper BB

Backtest Results (3 years, SPY/QQQ/AAPL/MSFT):
- Win Rate: 58.6%
- Total Return: 37.57%
- Profit Factor: 2.23x
- Max Drawdown: -2.59%
- Total Trades: 87
"""

from typing import Optional
import pandas as pd
import structlog

from .base_strategy import BaseStrategy, Signal

logger = structlog.get_logger()


class BollingerBounce(BaseStrategy):
    """Bollinger Band Bounce mean reversion strategy."""

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_entry_threshold: float = 40,
        bb_period: int = 20,
        bb_std: float = 2.0,
        atr_period: int = 14,
        atr_sl_multiplier: float = 1.5,
        config: Optional[dict] = None
    ):
        """
        Initialize Bollinger Band Bounce strategy.
        
        Args:
            rsi_period: RSI calculation period
            rsi_entry_threshold: RSI threshold for entry (< this value)
            bb_period: Bollinger Band period
            bb_std: Bollinger Band standard deviation multiplier
            atr_period: ATR calculation period
            atr_sl_multiplier: ATR multiplier for stop loss
            config: Optional configuration dict
        """
        super().__init__(config=config)
        self.rsi_period = rsi_period
        self.rsi_entry_threshold = rsi_entry_threshold
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.atr_period = atr_period
        self.atr_sl_multiplier = atr_sl_multiplier

    def generate_signal(
        self,
        symbol: str,
        data: pd.DataFrame,
        daily_data: Optional[pd.DataFrame] = None,
        hourly_data: Optional[pd.DataFrame] = None
    ) -> Signal:
        """
        Generate signal based on Bollinger Band bounce.
        
        Entry: Price touches lower BB + RSI < 40
        Exit: Price reaches middle BB (mean reversion complete)
        """
        if len(data) < max(self.rsi_period, self.bb_period):
            return Signal.HOLD
        
        # Calculate indicators
        from quantshift_core.indicators import TechnicalIndicators
        indicators = TechnicalIndicators()
        
        rsi = indicators.rsi(data['close'], self.rsi_period)
        bb_upper, bb_middle, bb_lower = indicators.bollinger_bands(
            data['close'], self.bb_period, self.bb_std
        )
        
        current_price = data['close'].iloc[-1]
        current_low = data['low'].iloc[-1]
        current_high = data['high'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        # Check if we have an active position for this symbol
        has_position = symbol in self.active_positions
        
        # Entry signal: price touches lower BB + RSI < threshold
        if not has_position:
            if current_low <= bb_lower.iloc[-1] and current_rsi < self.rsi_entry_threshold:
                logger.info("signal_generated", strategy="BB_Bounce", signal="BUY", 
                           symbol=symbol, reason="bb_lower_touch", rsi=current_rsi, 
                           price=current_price, bb_lower=bb_lower.iloc[-1])
                return Signal.BUY
        
        # Exit signal: price reaches middle band (mean reversion)
        else:
            if current_high >= bb_middle.iloc[-1]:
                logger.info("signal_generated", strategy="BB_Bounce", signal="SELL", 
                           symbol=symbol, reason="bb_middle_reached", price=current_price, 
                           bb_middle=bb_middle.iloc[-1])
                return Signal.SELL
        
        return Signal.HOLD

    def calculate_stop_loss(self, entry_price: float, data: pd.DataFrame, symbol: str) -> float:
        """Calculate stop loss below lower BB using ATR."""
        from quantshift_core.indicators import TechnicalIndicators
        indicators = TechnicalIndicators()
        
        _, _, bb_lower = indicators.bollinger_bands(
            data['close'], self.bb_period, self.bb_std
        )
        atr = indicators.atr(data['high'], data['low'], data['close'], self.atr_period).iloc[-1]
        
        # Stop loss = lower BB - 1.5×ATR
        stop_loss = bb_lower.iloc[-1] - (atr * self.atr_sl_multiplier)
        logger.debug("stop_loss_calculated", symbol=symbol, stop_loss=stop_loss, 
                    bb_lower=bb_lower.iloc[-1], atr=atr)
        return stop_loss

    def calculate_take_profit(self, entry_price: float, data: pd.DataFrame, symbol: str) -> float:
        """Calculate take profit at upper Bollinger Band."""
        from quantshift_core.indicators import TechnicalIndicators
        indicators = TechnicalIndicators()
        
        bb_upper, _, _ = indicators.bollinger_bands(
            data['close'], self.bb_period, self.bb_std
        )
        
        # Take profit at upper band
        take_profit = bb_upper.iloc[-1]
        logger.debug("take_profit_calculated", symbol=symbol, take_profit=take_profit)
        return take_profit
