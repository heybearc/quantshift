"""Crypto trading module for Alpaca Trading Bot.

This module provides crypto-specific trading functionality including:
- 24/7 trading support
- Crypto-optimized strategies (RSI, Bollinger Bands, momentum)
- Multi-symbol monitoring
- Risk management for volatile assets
"""

from .crypto_trader import CryptoTrader
from .crypto_strategy import CryptoStrategy, RSIStrategy, BollingerStrategy
from .crypto_config import CryptoConfig, crypto_config

__all__ = [
    "CryptoTrader",
    "CryptoStrategy",
    "RSIStrategy", 
    "BollingerStrategy",
    "CryptoConfig",
    "crypto_config",
]
