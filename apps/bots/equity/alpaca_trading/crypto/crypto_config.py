"""Crypto trading configuration.

Separate config for crypto-specific parameters since crypto markets
behave differently than equities.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class CryptoConfig:
    """Configuration for crypto trading."""
    
    # Supported crypto symbols (Alpaca format)
    symbols: List[str] = field(default_factory=lambda: [
        "BTC/USD",   # Bitcoin
        "ETH/USD",   # Ethereum
        "DOGE/USD",  # Dogecoin
        "LTC/USD",   # Litecoin
        "AVAX/USD",  # Avalanche
        "LINK/USD",  # Chainlink
        "UNI/USD",   # Uniswap
        "SOL/USD",   # Solana
    ])
    
    # Position sizing
    max_positions: int = 3
    position_size_usd: float = 500.0  # USD per position
    max_portfolio_pct: float = 0.10   # Max 10% of portfolio per coin
    
    # Risk management (tighter for crypto volatility)
    stop_loss_pct: float = 0.03       # 3% stop loss
    take_profit_pct: float = 0.06     # 6% take profit (2:1 R:R)
    trailing_stop_pct: float = 0.02   # 2% trailing stop
    
    # RSI Strategy parameters
    rsi_period: int = 14
    rsi_oversold: float = 30.0        # Buy signal
    rsi_overbought: float = 70.0      # Sell signal
    
    # Bollinger Band parameters
    bb_period: int = 20
    bb_std_dev: float = 2.0
    
    # Momentum parameters
    momentum_period: int = 10
    momentum_threshold: float = 0.02  # 2% momentum threshold
    
    # Trading schedule (crypto is 24/7 but we can limit)
    trading_enabled: bool = True
    check_interval_minutes: int = 5   # Check every 5 minutes
    
    # Data exchange for quotes
    crypto_exchange: str = "CBSE"     # Coinbase for Alpaca crypto data
    
    def __post_init__(self):
        """Load overrides from environment variables."""
        if os.getenv("CRYPTO_SYMBOLS"):
            self.symbols = os.getenv("CRYPTO_SYMBOLS").split(",")
        if os.getenv("CRYPTO_POSITION_SIZE"):
            self.position_size_usd = float(os.getenv("CRYPTO_POSITION_SIZE"))
        if os.getenv("CRYPTO_MAX_POSITIONS"):
            self.max_positions = int(os.getenv("CRYPTO_MAX_POSITIONS"))
        if os.getenv("CRYPTO_STOP_LOSS"):
            self.stop_loss_pct = float(os.getenv("CRYPTO_STOP_LOSS"))
        if os.getenv("CRYPTO_TAKE_PROFIT"):
            self.take_profit_pct = float(os.getenv("CRYPTO_TAKE_PROFIT"))


# Singleton instance
crypto_config = CryptoConfig()
