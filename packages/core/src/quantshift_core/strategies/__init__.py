"""
QuantShift Strategy Framework

Broker-agnostic trading strategies that can be used with any broker (Alpaca, Coinbase, etc.)
and for backtesting.
"""

from .base_strategy import BaseStrategy, Signal, SignalType
from .ma_crossover import MACrossoverStrategy

__all__ = [
    'BaseStrategy',
    'Signal',
    'SignalType',
    'MACrossoverStrategy',
]
