"""
Moving Average Crossover Strategy - Broker-Agnostic Implementation

Classic trend-following strategy using short and long-term moving averages.
Generates BUY signals on golden cross (short MA crosses above long MA)
and SELL signals on death cross (short MA crosses below long MA).

Enhanced with:
- ATR-based position sizing
- Volume confirmation
- Weekly trend confirmation
- Support/resistance filters
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np
import structlog

from .base_strategy import (
    BaseStrategy, Signal, SignalType, Account, Position
)

logger = structlog.get_logger()


class MACrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy with enhanced filters.
    
    Parameters:
        short_window: Short-term MA period (default: 20)
        long_window: Long-term MA period (default: 50)
        atr_period: ATR calculation period (default: 14)
        risk_per_trade: Risk percentage per trade (default: 0.02 = 2%)
        volume_confirmation: Require volume > 20-day average (default: True)
        trend_confirmation: Require weekly trend alignment (default: True)
        support_resistance_filter: Check proximity to resistance (default: True)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize MA Crossover strategy."""
        super().__init__(config)
        
        # Strategy parameters
        self.short_window = self.get_config('short_window', 20)
        self.long_window = self.get_config('long_window', 50)
        self.atr_period = self.get_config('atr_period', 14)
        self.risk_per_trade = self.get_config('risk_per_trade', 0.02)
        
        # Filter parameters
        self.volume_confirmation = self.get_config('volume_confirmation', True)
        self.trend_confirmation = self.get_config('trend_confirmation', True)
        self.support_resistance_filter = self.get_config('support_resistance_filter', True)
        self.proximity_threshold = self.get_config('proximity_threshold', 0.01)
        
        self.logger.info(
            "strategy_initialized",
            short_window=self.short_window,
            long_window=self.long_window,
            risk_per_trade=self.risk_per_trade
        )
    
    def generate_signals(
        self,
        market_data: pd.DataFrame,
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """
        Generate trading signals based on MA crossover.
        
        Args:
            market_data: DataFrame with columns: open, high, low, close, volume
            account: Current account information
            positions: Current open positions
            
        Returns:
            List of trading signals
        """
        signals = []
        
        # Validate data
        if len(market_data) < self.long_window + 1:
            self.logger.warning(
                "insufficient_data",
                required=self.long_window + 1,
                available=len(market_data)
            )
            return signals
        
        # Calculate moving averages
        df = market_data.copy()
        df['short_ma'] = df['close'].rolling(window=self.short_window, min_periods=1).mean()
        df['long_ma'] = df['close'].rolling(window=self.long_window, min_periods=1).mean()
        
        # Calculate ATR for position sizing and stops
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1
        )
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        
        # Get valid data (where both MAs are calculated)
        valid_df = df.dropna(subset=['short_ma', 'long_ma', 'atr'])
        
        if len(valid_df) < 2:
            self.logger.warning("insufficient_valid_data")
            return signals
        
        # Get latest and previous data points
        latest = valid_df.iloc[-1]
        prev = valid_df.iloc[-2]
        
        # Detect crossovers
        golden_cross = (
            prev['short_ma'] < prev['long_ma'] and 
            latest['short_ma'] > latest['long_ma']
        )
        
        death_cross = (
            prev['short_ma'] > prev['long_ma'] and 
            latest['short_ma'] < latest['long_ma']
        )
        
        # Get symbol from index or metadata
        symbol = self._get_symbol_from_data(market_data)
        
        # Check if we have a position in this symbol
        has_position = any(pos.symbol == symbol for pos in positions)
        
        # Generate BUY signal on golden cross
        if golden_cross and not has_position:
            # Apply filters
            filters_passed, filter_reason = self._apply_buy_filters(
                df, latest, market_data
            )
            
            if filters_passed:
                # Calculate position size and risk parameters
                atr = latest['atr']
                position_size = self.calculate_position_size(
                    Signal(
                        signal_type=SignalType.BUY,
                        symbol=symbol,
                        timestamp=datetime.utcnow(),
                        price=latest['close']
                    ),
                    account,
                    atr
                )
                
                # Calculate stop loss and take profit
                stop_loss = self.calculate_stop_loss(
                    Signal(
                        signal_type=SignalType.BUY,
                        symbol=symbol,
                        timestamp=datetime.utcnow(),
                        price=latest['close']
                    ),
                    atr
                )
                
                take_profit = self.calculate_take_profit(
                    Signal(
                        signal_type=SignalType.BUY,
                        symbol=symbol,
                        timestamp=datetime.utcnow(),
                        price=latest['close']
                    ),
                    stop_loss
                )
                
                signal = Signal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=1.0,
                    reason=f"Golden cross detected (MA {self.short_window}/{self.long_window})",
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    metadata={
                        'short_ma': latest['short_ma'],
                        'long_ma': latest['long_ma'],
                        'atr': atr,
                        'filters_passed': filter_reason
                    }
                )
                
                if self.validate_signal(signal, account, positions):
                    signals.append(signal)
                    self.logger.info(
                        "buy_signal_generated",
                        symbol=symbol,
                        price=latest['close'],
                        position_size=position_size
                    )
            else:
                self.logger.info(
                    "golden_cross_filtered",
                    symbol=symbol,
                    reason=filter_reason
                )
        
        # Generate SELL signal on death cross
        elif death_cross and has_position:
            position = next(pos for pos in positions if pos.symbol == symbol)
            
            signal = Signal(
                signal_type=SignalType.SELL,
                symbol=symbol,
                timestamp=datetime.utcnow(),
                price=latest['close'],
                confidence=1.0,
                reason=f"Death cross detected (MA {self.short_window}/{self.long_window})",
                position_size=int(position.quantity),
                metadata={
                    'short_ma': latest['short_ma'],
                    'long_ma': latest['long_ma'],
                    'entry_price': position.entry_price,
                    'unrealized_pl': position.unrealized_pl
                }
            )
            
            signals.append(signal)
            self.logger.info(
                "sell_signal_generated",
                symbol=symbol,
                price=latest['close'],
                unrealized_pl=position.unrealized_pl
            )
        
        return signals
    
    def calculate_position_size(
        self,
        signal: Signal,
        account: Account,
        atr: Optional[float] = None
    ) -> int:
        """
        Calculate position size using ATR-based risk management.
        
        Risk per trade is fixed percentage of account equity.
        Position size = (Account Equity * Risk %) / ATR
        """
        if atr is None or atr == 0:
            self.logger.warning("atr_not_available", using_default=True)
            # Fallback: use 2% of account as position value
            position_value = account.equity * self.risk_per_trade
            return int(position_value / signal.price)
        
        # Calculate risk amount
        risk_amount = account.equity * self.risk_per_trade
        
        # Position size based on ATR
        position_size = int(risk_amount / atr)
        
        # Ensure we don't exceed buying power
        max_size = int(account.buying_power / signal.price)
        position_size = min(position_size, max_size)
        
        # Ensure minimum position size
        position_size = max(position_size, 1)
        
        self.logger.debug(
            "position_size_calculated",
            symbol=signal.symbol,
            size=position_size,
            risk_amount=risk_amount,
            atr=atr
        )
        
        return position_size
    
    def _apply_buy_filters(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
        market_data: pd.DataFrame
    ) -> tuple[bool, str]:
        """
        Apply buy signal filters.
        
        Returns:
            (filters_passed, reason)
        """
        reasons = []
        
        # Volume confirmation
        if self.volume_confirmation:
            df['avg_volume_20'] = df['volume'].rolling(window=20).mean()
            latest_avg_vol = df['avg_volume_20'].iloc[-1]
            latest_volume = df['volume'].iloc[-1]
            
            if latest_volume <= latest_avg_vol:
                return False, "Volume confirmation failed"
            reasons.append("volume_confirmed")
        
        # Weekly trend confirmation (simplified - would need weekly data)
        if self.trend_confirmation:
            # Use longer MA as proxy for weekly trend
            df['ma_100'] = df['close'].rolling(window=100, min_periods=1).mean()
            if len(df) >= 100:
                weekly_trend_up = latest['close'] > df['ma_100'].iloc[-1]
                if not weekly_trend_up:
                    return False, "Weekly trend not aligned"
                reasons.append("weekly_trend_up")
        
        # Support/Resistance filter
        if self.support_resistance_filter:
            recent_closes = df['close'].tail(20)
            resistance_level = recent_closes.max()
            proximity = abs(latest['close'] - resistance_level) / resistance_level
            
            if proximity < self.proximity_threshold:
                return False, "Too close to resistance"
            reasons.append("clear_of_resistance")
        
        return True, ", ".join(reasons)
    
    def _get_symbol_from_data(self, market_data: pd.DataFrame) -> str:
        """Extract symbol from market data."""
        # Try to get from index
        if hasattr(market_data.index, 'get_level_values'):
            if 'symbol' in market_data.index.names:
                return market_data.index.get_level_values('symbol')[0]
        
        # Try to get from metadata or attributes
        if hasattr(market_data, 'symbol'):
            return market_data.symbol
        
        # Default fallback
        return "UNKNOWN"
