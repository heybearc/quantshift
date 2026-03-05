"""
Donchian Breakout Strategy - Turtle Trading System

Classic trend-following strategy based on Donchian Channels (price breakouts).
Buys on breakout above N-period high, sells on breakout below N-period low.

This is the foundation of the famous Turtle Trading system - one of the most
profitable trend-following strategies in history.

Entry Signals:
- BUY: Price breaks above 20-period high + volume confirmation
- SELL: Price breaks below 10-period low (exit signal)

Enhanced with:
- ATR-based position sizing (Turtle method)
- ATR-based trailing stops
- Volume confirmation
- Trend strength filter
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


class DonchianBreakoutStrategy(BaseStrategy):
    """
    Donchian Channel breakout strategy (Turtle Trading).
    
    Parameters:
        entry_period: Period for entry breakout (default: 20)
        exit_period: Period for exit breakout (default: 10)
        atr_period: ATR calculation period (default: 14)
        atr_sl_multiplier: ATR multiplier for stop loss (default: 2.0)
        atr_trail_multiplier: ATR multiplier for trailing stop (default: 3.0)
        risk_per_trade: Risk percentage per trade (default: 0.02)
        volume_confirmation: Require volume > average (default: True)
        min_atr_filter: Minimum ATR for volatility filter (default: 0.0)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Donchian Breakout strategy."""
        super().__init__(config)
        
        self.entry_period = self.get_config('entry_period', 20)
        self.exit_period = self.get_config('exit_period', 10)
        self.atr_period = self.get_config('atr_period', 14)
        self.atr_sl_multiplier = self.get_config('atr_sl_multiplier', 2.0)
        self.atr_trail_multiplier = self.get_config('atr_trail_multiplier', 3.0)
        self.risk_per_trade = self.get_config('risk_per_trade', 0.02)
        self.volume_confirmation = self.get_config('volume_confirmation', True)
        self.min_atr_filter = self.get_config('min_atr_filter', 0.0)
        
        self.logger.info(
            "strategy_initialized",
            entry_period=self.entry_period,
            exit_period=self.exit_period,
            risk_per_trade=self.risk_per_trade
        )
    
    def generate_signals(
        self,
        market_data: pd.DataFrame,
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """Generate trading signals based on Donchian Channel breakouts."""
        signals = []
        
        required_data = max(self.entry_period, self.exit_period, self.atr_period) + 1
        if len(market_data) < required_data:
            self.logger.warning("insufficient_data", required=required_data, available=len(market_data))
            return signals
        
        df = market_data.copy()
        
        # Calculate Donchian Channels
        df['entry_high'] = df['high'].rolling(window=self.entry_period).max()
        df['entry_low'] = df['low'].rolling(window=self.entry_period).min()
        df['exit_high'] = df['high'].rolling(window=self.exit_period).max()
        df['exit_low'] = df['low'].rolling(window=self.exit_period).min()
        
        # Calculate ATR for position sizing and stops
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1
        )
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        
        # Volume metrics
        if self.volume_confirmation:
            df['avg_volume'] = df['volume'].rolling(window=20).mean()
        
        # Calculate channel width (volatility measure)
        df['channel_width'] = df['entry_high'] - df['entry_low']
        df['channel_width_pct'] = (df['channel_width'] / df['close']) * 100
        
        valid_df = df.dropna()
        if len(valid_df) < 2:
            return signals
        
        latest = valid_df.iloc[-1]
        prev = valid_df.iloc[-2]
        symbol = self._get_symbol_from_data(market_data)
        has_position = any(pos.symbol == symbol for pos in positions)
        
        # BUY Signal: Breakout above entry_high
        if not has_position:
            # Check for breakout
            breakout = (latest['close'] > latest['entry_high'] and 
                       prev['close'] <= prev['entry_high'])
            
            if breakout:
                # ATR filter (avoid low volatility periods)
                if latest['atr'] < self.min_atr_filter:
                    self.logger.debug("breakout_filtered_low_volatility", symbol=symbol, atr=latest['atr'])
                    return signals
                
                # Volume confirmation
                if self.volume_confirmation and latest['volume'] <= latest['avg_volume']:
                    self.logger.debug("breakout_filtered_volume", symbol=symbol)
                    return signals
                
                atr = latest['atr']
                position_size = self.calculate_position_size(
                    Signal(SignalType.BUY, symbol, datetime.utcnow(), latest['close']),
                    account,
                    atr
                )
                
                # Turtle-style stop: 2 ATR below entry
                stop_loss = latest['close'] - (self.atr_sl_multiplier * atr)
                
                # Take profit: 3 ATR above entry (or use trailing stop)
                take_profit = latest['close'] + (self.atr_trail_multiplier * atr)
                
                signal = Signal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=min(latest['channel_width_pct'] / 5.0, 1.0),  # Higher confidence for wider channels
                    reason=f"Donchian {self.entry_period}-period breakout, ATR: {atr:.2f}",
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    metadata={
                        'entry_high': latest['entry_high'],
                        'entry_low': latest['entry_low'],
                        'atr': atr,
                        'channel_width_pct': latest['channel_width_pct'],
                        'volume_ratio': latest['volume'] / latest['avg_volume'] if self.volume_confirmation else None
                    }
                )
                
                if self.validate_signal(signal, account, positions):
                    signals.append(signal)
                    self.logger.info(
                        "buy_signal_generated",
                        symbol=symbol,
                        price=latest['close'],
                        entry_high=latest['entry_high'],
                        atr=atr
                    )
        
        # SELL Signal: Breakdown below exit_low
        elif has_position:
            position = next(pos for pos in positions if pos.symbol == symbol)
            
            # Exit on breakdown below exit_low
            breakdown = (latest['close'] < latest['exit_low'] and 
                        prev['close'] >= prev['exit_low'])
            
            if breakdown:
                signal = Signal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=1.0,
                    reason=f"Donchian {self.exit_period}-period breakdown exit",
                    position_size=int(position.quantity),
                    metadata={
                        'exit_low': latest['exit_low'],
                        'entry_price': position.entry_price,
                        'unrealized_pl': position.unrealized_pl,
                        'holding_bars': len(valid_df)  # Approximate
                    }
                )
                
                signals.append(signal)
                self.logger.info(
                    "sell_signal_generated",
                    symbol=symbol,
                    price=latest['close'],
                    exit_low=latest['exit_low'],
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
        Calculate position size using Turtle Trading method.
        
        Position size = (Account Equity * Risk %) / (ATR * ATR Multiplier)
        This ensures consistent dollar risk per trade.
        """
        if atr is None or atr == 0:
            self.logger.warning("atr_not_available", using_default=True)
            position_value = account.equity * self.risk_per_trade
            return int(position_value / signal.price)
        
        # Turtle method: risk fixed % of equity per trade
        risk_amount = account.equity * self.risk_per_trade
        
        # Position size based on ATR stop distance
        stop_distance = self.atr_sl_multiplier * atr
        position_size = int(risk_amount / stop_distance)
        
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
            atr=atr,
            stop_distance=stop_distance
        )
        
        return position_size
    
    def calculate_stop_loss(self, signal: Signal, atr: Optional[float] = None) -> float:
        """Calculate stop loss using ATR."""
        if atr is None or atr == 0:
            return signal.price * 0.96
        return signal.price - (self.atr_sl_multiplier * atr)
    
    def calculate_take_profit(self, signal: Signal, stop_loss: Optional[float] = None) -> float:
        """Calculate take profit using ATR."""
        if stop_loss is None:
            return signal.price * 1.06
        risk = signal.price - stop_loss
        return signal.price + (risk * (self.atr_trail_multiplier / self.atr_sl_multiplier))
    
    def _get_symbol_from_data(self, market_data: pd.DataFrame) -> str:
        """Extract symbol from market data."""
        if hasattr(market_data.index, 'get_level_values'):
            if 'symbol' in market_data.index.names:
                return market_data.index.get_level_values('symbol')[0]
        if hasattr(market_data, 'symbol'):
            return market_data.symbol
        return "UNKNOWN"
