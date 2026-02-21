"""
Executors - Broker-Specific Strategy Execution

This module provides broker-specific executors that implement the same interface
for executing broker-agnostic strategies across different trading platforms.
"""

from .alpaca_executor import AlpacaExecutor
from .coinbase_executor import CoinbaseExecutor

__all__ = [
    'AlpacaExecutor',
    'CoinbaseExecutor',
]
