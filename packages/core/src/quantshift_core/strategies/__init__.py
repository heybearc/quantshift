"""
QuantShift Strategy Framework

Broker-agnostic trading strategies that can be used with any broker (Alpaca, Coinbase, etc.)
and for backtesting.
"""

from .base_strategy import BaseStrategy, Signal, SignalType, Account, Position
from .ma_crossover import MACrossoverStrategy
from .bollinger_bounce import BollingerBounce
from .rsi_mean_reversion import RSIMeanReversion

__all__ = [
    'BaseStrategy',
    'Signal',
    'SignalType',
    'Account',
    'Position',
    'MACrossoverStrategy',
    'BollingerBounce',
    'RSIMeanReversion',
]
