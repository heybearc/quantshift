"""
Keltner Channel Strategy - Volatility-Based Trading

Uses Keltner Channels (EMA + ATR bands) to identify overbought/oversold conditions
and trend strength. More responsive than Bollinger Bands for trending markets.

Entry Signals:
- BUY: Price touches lower Keltner band + RSI < 40
- SELL: Price touches upper Keltner band + RSI > 60

Enhanced with:
- ATR-based position sizing
- Volume confirmation
- Trend filter using EMA slope
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


class KeltnerChannelStrategy(BaseStrategy):
    """
    Keltner Channel mean reversion/trend strategy.
    
    Parameters:
        ema_period: EMA period for center line (default: 20)
        atr_period: ATR calculation period (default: 14)
        atr_multiplier: ATR multiplier for bands (default: 2.0)
        rsi_period: RSI period (default: 14)
        rsi_buy_threshold: RSI threshold for buy (default: 40)
        rsi_sell_threshold: RSI threshold for sell (default: 60)
        risk_per_trade: Risk percentage per trade (default: 0.02)
        volume_confirmation: Require volume confirmation (default: True)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Keltner Channel strategy."""
        super().__init__(config)
        
        self.ema_period = self.get_config('ema_period', 20)
        self.atr_period = self.get_config('atr_period', 14)
        self.atr_multiplier = self.get_config('atr_multiplier', 2.0)
        self.rsi_period = self.get_config('rsi_period', 14)
        self.rsi_buy_threshold = self.get_config('rsi_buy_threshold', 40)
        self.rsi_sell_threshold = self.get_config('rsi_sell_threshold', 60)
        self.risk_per_trade = self.get_config('risk_per_trade', 0.02)
        self.volume_confirmation = self.get_config('volume_confirmation', True)
        
        self.logger.info(
            "strategy_initialized",
            ema_period=self.ema_period,
            atr_multiplier=self.atr_multiplier,
            risk_per_trade=self.risk_per_trade
        )
    
    def generate_signals(
        self,
        market_data: pd.DataFrame,
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """Generate trading signals based on Keltner Channels."""
        signals = []
        
        if len(market_data) < max(self.ema_period, self.atr_period, self.rsi_period) + 1:
            self.logger.warning("insufficient_data")
            return signals
        
        df = market_data.copy()
        
        # Calculate EMA (center line)
        df['ema'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        
        # Calculate ATR
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1
        )
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        
        # Calculate Keltner Channels
        df['upper_band'] = df['ema'] + (self.atr_multiplier * df['atr'])
        df['lower_band'] = df['ema'] - (self.atr_multiplier * df['atr'])
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume filter
        if self.volume_confirmation:
            df['avg_volume'] = df['volume'].rolling(window=20).mean()
        
        valid_df = df.dropna()
        if len(valid_df) < 2:
            return signals
        
        latest = valid_df.iloc[-1]
        symbol = self._get_symbol_from_data(market_data)
        has_position = any(pos.symbol == symbol for pos in positions)
        
        # BUY Signal: Price at/below lower band + RSI oversold
        if not has_position:
            if (latest['close'] <= latest['lower_band'] and 
                latest['rsi'] < self.rsi_buy_threshold):
                
                # Volume confirmation
                if self.volume_confirmation and latest['volume'] <= latest['avg_volume']:
                    self.logger.debug("buy_signal_filtered_volume", symbol=symbol)
                    return signals
                
                atr = latest['atr']
                position_size = self.calculate_position_size(
                    Signal(SignalType.BUY, symbol, datetime.utcnow(), latest['close']),
                    account,
                    atr
                )
                
                stop_loss = self.calculate_stop_loss(
                    Signal(SignalType.BUY, symbol, datetime.utcnow(), latest['close']),
                    atr
                )
                
                take_profit = self.calculate_take_profit(
                    Signal(SignalType.BUY, symbol, datetime.utcnow(), latest['close']),
                    stop_loss
                )
                
                signal = Signal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=1.0,
                    reason=f"Keltner lower band touch + RSI {latest['rsi']:.1f}",
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    metadata={
                        'ema': latest['ema'],
                        'upper_band': latest['upper_band'],
                        'lower_band': latest['lower_band'],
                        'rsi': latest['rsi'],
                        'atr': atr
                    }
                )
                
                if self.validate_signal(signal, account, positions):
                    signals.append(signal)
                    self.logger.info("buy_signal_generated", symbol=symbol, price=latest['close'])
        
        # SELL Signal: Price at/above upper band + RSI overbought
        elif has_position:
            if (latest['close'] >= latest['upper_band'] and 
                latest['rsi'] > self.rsi_sell_threshold):
                
                position = next(pos for pos in positions if pos.symbol == symbol)
                
                signal = Signal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=1.0,
                    reason=f"Keltner upper band touch + RSI {latest['rsi']:.1f}",
                    position_size=int(position.quantity),
                    metadata={
                        'ema': latest['ema'],
                        'upper_band': latest['upper_band'],
                        'lower_band': latest['lower_band'],
                        'rsi': latest['rsi'],
                        'entry_price': position.entry_price,
                        'unrealized_pl': position.unrealized_pl
                    }
                )
                
                signals.append(signal)
                self.logger.info("sell_signal_generated", symbol=symbol, price=latest['close'])
        
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
        position_size = int(risk_amount / atr)
        max_size = int(account.buying_power / signal.price)
        position_size = min(position_size, max_size)
        return max(position_size, 1)
    
    def _get_symbol_from_data(self, market_data: pd.DataFrame) -> str:
        """Extract symbol from market data."""
        if hasattr(market_data.index, 'get_level_values'):
            if 'symbol' in market_data.index.names:
                return market_data.index.get_level_values('symbol')[0]
        if hasattr(market_data, 'symbol'):
            return market_data.symbol
        return "UNKNOWN"
