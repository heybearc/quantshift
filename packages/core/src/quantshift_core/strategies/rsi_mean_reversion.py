"""
RSI Mean Reversion Strategy - Broker-Agnostic Implementation

Mean reversion strategy using RSI oversold/overbought levels.
Generates BUY signals when RSI crosses below 30 (oversold),
and SELL signals when RSI crosses above 70 (overbought).

Backtest Results (3 years, SPY/QQQ/AAPL/MSFT):
- Win Rate: 57.5%
- Total Return: 16.82%
- Profit Factor: 1.99x
- Max Drawdown: -3.11%
- Total Trades: 40
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


class RSIMeanReversion(BaseStrategy):
    """
    RSI Mean Reversion strategy.
    
    Parameters:
        rsi_period: RSI calculation period (default: 14)
        rsi_oversold: RSI oversold threshold for entry (default: 30)
        rsi_overbought: RSI overbought threshold for exit (default: 70)
        atr_period: ATR calculation period (default: 14)
        atr_sl_multiplier: ATR multiplier for stop loss (default: 2.0)
        atr_tp_multiplier: ATR multiplier for take profit (default: 3.0)
        risk_per_trade: Risk percentage per trade (default: 0.01 = 1%)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize RSI Mean Reversion strategy."""
        super().__init__(config)
        
        # Strategy parameters
        self.rsi_period = self.get_config('rsi_period', 14)
        self.rsi_oversold = self.get_config('rsi_oversold', 30)
        self.rsi_overbought = self.get_config('rsi_overbought', 70)
        self.atr_period = self.get_config('atr_period', 14)
        self.atr_sl_multiplier = self.get_config('atr_sl_multiplier', 2.0)
        self.atr_tp_multiplier = self.get_config('atr_tp_multiplier', 3.0)
        self.risk_per_trade = self.get_config('risk_per_trade', 0.01)
        
        self.logger.info(
            "strategy_initialized",
            rsi_period=self.rsi_period,
            rsi_oversold=self.rsi_oversold,
            rsi_overbought=self.rsi_overbought,
            risk_per_trade=self.risk_per_trade
        )
    
    def generate_signals(
        self,
        market_data: pd.DataFrame,
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """
        Generate trading signals based on RSI mean reversion.
        
        Args:
            market_data: DataFrame with columns: open, high, low, close, volume
            account: Current account information
            positions: Current open positions
            
        Returns:
            List of trading signals
        """
        signals = []
        
        # Validate data
        required_periods = max(self.rsi_period, self.atr_period)
        if len(market_data) < required_periods + 1:
            self.logger.warning(
                "insufficient_data",
                required=required_periods + 1,
                available=len(market_data)
            )
            return signals
        
        # Calculate indicators
        df = market_data.copy()
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=self.rsi_period).mean()
        loss = -delta.where(delta < 0, 0.0).rolling(window=self.rsi_period).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1
        )
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        
        # Get valid data
        valid_df = df.dropna(subset=['rsi', 'atr'])
        
        if len(valid_df) < 2:
            self.logger.warning("insufficient_valid_data")
            return signals
        
        # Get latest and previous data points
        latest = valid_df.iloc[-1]
        prev = valid_df.iloc[-2]
        
        # Get symbol from index or metadata
        symbol = self._get_symbol_from_data(market_data)
        
        # Check if we have a position in this symbol
        has_position = any(pos.symbol == symbol for pos in positions)
        
        # Entry signal: RSI crosses below oversold threshold
        if not has_position:
            if latest['rsi'] < self.rsi_oversold and prev['rsi'] >= self.rsi_oversold:
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
                stop_loss = latest['close'] - (atr * self.atr_sl_multiplier)
                take_profit = latest['close'] + (atr * self.atr_tp_multiplier)
                
                signal = Signal(
                    signal_type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=1.0,
                    reason=f"RSI oversold: {latest['rsi']:.1f} < {self.rsi_oversold}",
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    metadata={
                        'rsi': latest['rsi'],
                        'rsi_prev': prev['rsi'],
                        'atr': atr
                    }
                )
                
                if self.validate_signal(signal, account, positions):
                    signals.append(signal)
                    self.logger.info(
                        "buy_signal_generated",
                        symbol=symbol,
                        price=latest['close'],
                        rsi=latest['rsi'],
                        position_size=position_size
                    )
        
        # Exit signal: RSI crosses above overbought threshold
        elif has_position:
            position = next(pos for pos in positions if pos.symbol == symbol)
            
            if latest['rsi'] > self.rsi_overbought and prev['rsi'] <= self.rsi_overbought:
                signal = Signal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.utcnow(),
                    price=latest['close'],
                    confidence=1.0,
                    reason=f"RSI overbought: {latest['rsi']:.1f} > {self.rsi_overbought}",
                    position_size=int(position.quantity),
                    metadata={
                        'rsi': latest['rsi'],
                        'rsi_prev': prev['rsi'],
                        'entry_price': position.entry_price,
                        'unrealized_pl': position.unrealized_pl
                    }
                )
                
                signals.append(signal)
                self.logger.info(
                    "sell_signal_generated",
                    symbol=symbol,
                    price=latest['close'],
                    rsi=latest['rsi'],
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
        Position size = (Account Equity * Risk %) / (ATR * multiplier)
        """
        if atr is None or atr == 0:
            self.logger.warning("atr_not_available", using_default=True)
            # Fallback: use 1% of account as position value
            position_value = account.equity * self.risk_per_trade
            return int(position_value / signal.price)
        
        # Calculate risk amount
        risk_amount = account.equity * self.risk_per_trade
        
        # Position size based on ATR (risk per share = ATR * multiplier)
        risk_per_share = atr * self.atr_sl_multiplier
        position_size = int(risk_amount / risk_per_share)
        
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
