"""
VWAP Reversion Strategy - Volume-Weighted Mean Reversion

Uses VWAP (Volume-Weighted Average Price) as a dynamic support/resistance level.
Excellent for intraday trading and identifying institutional price levels.

Entry Signals:
- BUY: Price drops significantly below VWAP (oversold) + volume spike
- SELL: Price rises significantly above VWAP (overbought) + volume spike

Enhanced with:
- Standard deviation bands around VWAP
- Volume profile analysis
- ATR-based position sizing
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


class VWAPReversionStrategy(BaseStrategy):
    """
    VWAP mean reversion strategy with volume confirmation.
    
    Parameters:
        vwap_std_multiplier: Standard deviation multiplier for bands (default: 2.0)
        volume_spike_threshold: Volume spike multiplier (default: 1.5)
        atr_period: ATR calculation period (default: 14)
        atr_sl_multiplier: ATR multiplier for stop loss (default: 2.0)
        atr_tp_multiplier: ATR multiplier for take profit (default: 3.0)
        risk_per_trade: Risk percentage per trade (default: 0.02)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize VWAP Reversion strategy."""
        super().__init__(config)
        
        self.vwap_std_multiplier = self.get_config('vwap_std_multiplier', 2.0)
        self.volume_spike_threshold = self.get_config('volume_spike_threshold', 1.5)
        self.atr_period = self.get_config('atr_period', 14)
        self.atr_sl_multiplier = self.get_config('atr_sl_multiplier', 2.0)
        self.atr_tp_multiplier = self.get_config('atr_tp_multiplier', 3.0)
        self.risk_per_trade = self.get_config('risk_per_trade', 0.02)
        
        self.logger.info(
            "strategy_initialized",
            vwap_std_multiplier=self.vwap_std_multiplier,
            volume_spike_threshold=self.volume_spike_threshold,
            risk_per_trade=self.risk_per_trade
        )
    
    def generate_signals(
        self,
        market_data: pd.DataFrame,
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """Generate trading signals based on VWAP deviation."""
        signals = []
        
        if len(market_data) < self.atr_period + 20:
            self.logger.warning("insufficient_data")
            return signals
        
        df = market_data.copy()
        
        # Calculate VWAP
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (df['typical_price'] * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Calculate VWAP standard deviation bands
        df['vwap_deviation'] = df['typical_price'] - df['vwap']
        df['vwap_std'] = df['vwap_deviation'].rolling(window=20).std()
        df['vwap_upper'] = df['vwap'] + (self.vwap_std_multiplier * df['vwap_std'])
        df['vwap_lower'] = df['vwap'] - (self.vwap_std_multiplier * df['vwap_std'])
        
        # Calculate ATR
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1
        )
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        
        # Calculate volume metrics
        df['avg_volume'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['avg_volume']
        
        valid_df = df.dropna()
        if len(valid_df) < 2:
            return signals
        
        latest = valid_df.iloc[-1]
        symbol = self._get_symbol_from_data(market_data)
        has_position = any(pos.symbol == symbol for pos in positions)
        
        # BUY Signal: Price below VWAP lower band + volume spike
        if not has_position:
            if (latest['close'] < latest['vwap_lower'] and 
                latest['volume_ratio'] >= self.volume_spike_threshold):
                
                atr = latest['atr']
                position_size = self.calculate_position_size(
                    Signal(SignalType.BUY, symbol, datetime.utcnow(), latest['close']),
                    account,
                    atr
                )
                
                stop_loss = latest['close'] - (self.atr_sl_multiplier * atr)
                take_profit = latest['close'] + (self.atr_tp_multiplier * atr)
                
                signal = Signal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=min(latest['volume_ratio'] / self.volume_spike_threshold, 1.0),
                    reason=f"Price below VWAP lower band, volume spike {latest['volume_ratio']:.1f}x",
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    metadata={
                        'vwap': latest['vwap'],
                        'vwap_lower': latest['vwap_lower'],
                        'vwap_upper': latest['vwap_upper'],
                        'volume_ratio': latest['volume_ratio'],
                        'atr': atr,
                        'deviation_pct': ((latest['close'] - latest['vwap']) / latest['vwap']) * 100
                    }
                )
                
                if self.validate_signal(signal, account, positions):
                    signals.append(signal)
                    self.logger.info(
                        "buy_signal_generated",
                        symbol=symbol,
                        price=latest['close'],
                        vwap=latest['vwap'],
                        volume_ratio=latest['volume_ratio']
                    )
        
        # SELL Signal: Price above VWAP upper band + volume spike OR mean reversion to VWAP
        elif has_position:
            position = next(pos for pos in positions if pos.symbol == symbol)
            
            # Exit on upper band touch with volume OR reversion to VWAP
            if ((latest['close'] > latest['vwap_upper'] and 
                 latest['volume_ratio'] >= self.volume_spike_threshold) or
                (latest['close'] >= latest['vwap'] and position.unrealized_pl > 0)):
                
                signal = Signal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=1.0,
                    reason=f"VWAP reversion target reached, P&L: ${position.unrealized_pl:.2f}",
                    position_size=int(position.quantity),
                    metadata={
                        'vwap': latest['vwap'],
                        'vwap_upper': latest['vwap_upper'],
                        'volume_ratio': latest['volume_ratio'],
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
        """Calculate position size using ATR-based risk management."""
        if atr is None or atr == 0:
            position_value = account.equity * self.risk_per_trade
            return int(position_value / signal.price)
        
        risk_amount = account.equity * self.risk_per_trade
        position_size = int(risk_amount / (self.atr_sl_multiplier * atr))
        max_size = int(account.buying_power / signal.price)
        position_size = min(position_size, max_size)
        return max(position_size, 1)
    
    def calculate_stop_loss(self, signal: Signal, atr: Optional[float] = None) -> float:
        """Calculate stop loss using ATR."""
        if atr is None or atr == 0:
            return signal.price * 0.98
        return signal.price - (self.atr_sl_multiplier * atr)
    
    def calculate_take_profit(self, signal: Signal, stop_loss: Optional[float] = None) -> float:
        """Calculate take profit using risk/reward ratio."""
        if stop_loss is None:
            return signal.price * 1.04
        risk = signal.price - stop_loss
        return signal.price + (risk * (self.atr_tp_multiplier / self.atr_sl_multiplier))
    
    def _get_symbol_from_data(self, market_data: pd.DataFrame) -> str:
        """Extract symbol from market data."""
        if hasattr(market_data.index, 'get_level_values'):
            if 'symbol' in market_data.index.names:
                return market_data.index.get_level_values('symbol')[0]
        if hasattr(market_data, 'symbol'):
            return market_data.symbol
        return "UNKNOWN"
