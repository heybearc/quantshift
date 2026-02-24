"""
Breakout Momentum Strategy - Broker-Agnostic Implementation

Trend-following strategy that enters when price breaks above recent highs
with strong volume confirmation. Exits with trailing stop or breakdown.

Entry: Price breaks 20-day high + volume > 1.5x average
Exit: Trailing stop at 1.5×ATR OR price breaks 10-day low

This strategy complements mean reversion strategies by capturing trends.
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


class BreakoutMomentum(BaseStrategy):
    """
    Breakout Momentum trend-following strategy.
    
    Parameters:
        breakout_period: Period for high/low calculation (default: 20)
        volume_multiplier: Volume threshold multiplier (default: 1.5)
        atr_period: ATR calculation period (default: 14)
        atr_trail_multiplier: ATR multiplier for trailing stop (default: 1.5)
        breakdown_period: Period for breakdown exit (default: 10)
        risk_per_trade: Risk percentage per trade (default: 0.01 = 1%)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Breakout Momentum strategy."""
        super().__init__(config)
        
        # Strategy parameters
        self.breakout_period = self.get_config('breakout_period', 20)
        self.volume_multiplier = self.get_config('volume_multiplier', 1.5)
        self.atr_period = self.get_config('atr_period', 14)
        self.atr_trail_multiplier = self.get_config('atr_trail_multiplier', 1.5)
        self.breakdown_period = self.get_config('breakdown_period', 10)
        self.risk_per_trade = self.get_config('risk_per_trade', 0.01)
        
        self.logger.info(
            "strategy_initialized",
            breakout_period=self.breakout_period,
            volume_multiplier=self.volume_multiplier,
            risk_per_trade=self.risk_per_trade
        )
    
    def generate_signals(
        self,
        market_data: pd.DataFrame,
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """
        Generate trading signals based on breakout momentum.
        
        Args:
            market_data: DataFrame with columns: open, high, low, close, volume
            account: Current account information
            positions: Current open positions
            
        Returns:
            List of trading signals
        """
        signals = []
        
        # Validate data
        required_periods = max(self.breakout_period, self.atr_period)
        if len(market_data) < required_periods + 1:
            self.logger.warning(
                "insufficient_data",
                required=required_periods + 1,
                available=len(market_data)
            )
            return signals
        
        # Calculate indicators
        df = market_data.copy()
        
        # 20-day high/low for breakout detection
        df['high_20'] = df['high'].rolling(window=self.breakout_period).max()
        df['low_10'] = df['low'].rolling(window=self.breakdown_period).min()
        
        # Average volume
        df['avg_volume'] = df['volume'].rolling(window=self.breakout_period).mean()
        
        # ATR for stop loss
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1
        )
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        
        # Get valid data
        valid_df = df.dropna(subset=['high_20', 'low_10', 'avg_volume', 'atr'])
        
        if len(valid_df) < 2:
            self.logger.warning("insufficient_valid_data")
            return signals
        
        # Get latest and previous data points
        latest = valid_df.iloc[-1]
        prev = valid_df.iloc[-2]
        
        # Get symbol from index or metadata
        symbol = self._get_symbol_from_data(market_data)
        
        # Check if we have a position in this symbol
        existing_position = None
        for pos in positions:
            if pos.symbol == symbol:
                existing_position = pos
                break
        
        # Entry signal: price breaks above 20-day high + volume confirmation
        if not existing_position:
            # Check for breakout
            breakout = (
                latest['close'] > prev['high_20'] and
                latest['volume'] > (latest['avg_volume'] * self.volume_multiplier)
            )
            
            if breakout:
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
                
                # Calculate stop loss (below recent low)
                stop_loss = latest['close'] - (atr * self.atr_trail_multiplier)
                
                # Take profit at 3x risk (risk-reward ratio)
                risk_amount = latest['close'] - stop_loss
                take_profit = latest['close'] + (risk_amount * 3.0)
                
                signal = Signal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    position_size=position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'strategy': self.name,
                        'entry_reason': 'breakout_momentum',
                        'breakout_high': float(prev['high_20']),
                        'volume_ratio': float(latest['volume'] / latest['avg_volume']),
                        'atr': float(atr)
                    }
                )
                
                signals.append(signal)
                
                self.logger.info(
                    "breakout_signal_generated",
                    symbol=symbol,
                    price=latest['close'],
                    breakout_high=prev['high_20'],
                    volume_ratio=latest['volume'] / latest['avg_volume'],
                    position_size=position_size
                )
        
        # Exit signal: trailing stop hit OR breakdown below 10-day low
        else:
            atr = latest['atr']
            
            # Calculate trailing stop (1.5x ATR below current price)
            trailing_stop = latest['close'] - (atr * self.atr_trail_multiplier)
            
            # Check for exit conditions
            trailing_stop_hit = latest['low'] <= trailing_stop
            breakdown = latest['close'] < latest['low_10']
            
            if trailing_stop_hit or breakdown:
                exit_reason = 'trailing_stop' if trailing_stop_hit else 'breakdown'
                
                signal = Signal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    position_size=existing_position.quantity,
                    metadata={
                        'strategy': self.name,
                        'exit_reason': exit_reason,
                        'trailing_stop': float(trailing_stop),
                        'breakdown_low': float(latest['low_10']),
                        'atr': float(atr)
                    }
                )
                
                signals.append(signal)
                
                self.logger.info(
                    "breakout_exit_signal",
                    symbol=symbol,
                    price=latest['close'],
                    exit_reason=exit_reason,
                    position_size=existing_position.quantity
                )
        
        return signals
    
    def calculate_position_size(
        self,
        signal: Signal,
        account: Account,
        atr: float
    ) -> int:
        """
        Calculate position size based on risk per trade.
        
        Args:
            signal: Trading signal
            account: Account information
            atr: Average True Range for stop loss calculation
            
        Returns:
            Position size in shares/contracts
        """
        # Calculate risk amount (1% of account by default)
        risk_amount = account.equity * self.risk_per_trade
        
        # Calculate stop loss distance
        stop_distance = atr * self.atr_trail_multiplier
        
        # Position size = risk amount / stop distance
        if stop_distance > 0:
            position_size = int(risk_amount / stop_distance)
        else:
            position_size = 0
        
        # Ensure position size is at least 1
        return max(1, position_size)
