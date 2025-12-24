"""Screening predicate functions extracted from the original screener logic.

These helpers are intentionally *thin* wrappers so that we do not change the
behaviour of `StockScreener` yet.  In a later refactor we will replace the
inline code inside `screener.py` with calls to these functions; for now they are
provided as a separate module so that other modules can import them without
introducing circular dependencies.
"""
from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd

MIN_PRICE_DEFAULT: Final[float] = 5.0
MAX_PRICE_DEFAULT: Final[float] = 1_000.0
MIN_VOLUME_DEFAULT: Final[int] = 500_000

__all__ = [
    "is_liquid",
    "is_price_in_range",
    "has_ma_crossover",
]


def is_liquid(df: pd.DataFrame, min_volume: int = MIN_VOLUME_DEFAULT) -> bool:
    """Return *True* if the last 20 bars meet the tiered average volume threshold.
    
    Tiered volume requirements based on price:
    - ≥ 250,000 shares if price > $15
    - ≥ 150,000 shares if $5 ≤ price ≤ $15
    - Uses 20-day average volume for stability
    """
    if df.empty or len(df) < 20:
        return False
    
    # Get 20-day average volume and latest price
    avg_volume_20d = df["volume"].tail(20).mean()
    latest_price = df["close"].iloc[-1]
    
    # Apply tiered volume requirements based on price
    if latest_price > 15.0:
        required_volume = 250_000  # Higher volume for higher-priced stocks
    elif latest_price >= 5.0:
        required_volume = 150_000  # Lower volume for mid-cap stocks
    else:
        # Below $5 - use the legacy min_volume parameter for flexibility
        required_volume = min_volume
    
    return bool(avg_volume_20d >= required_volume)


def is_price_in_range(
    df: pd.DataFrame,
    *,
    min_price: float = MIN_PRICE_DEFAULT,
    max_price: float = MAX_PRICE_DEFAULT,
) -> bool:
    """Check last close is within [min_price, max_price]."""
    last_price: float = float(df["close"].iloc[-1])
    return bool(min_price <= last_price <= max_price)


def calc_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average, window in periods (no centre)."""
    return series.rolling(window=window, min_periods=window).mean()


def has_ma_crossover(
    df: pd.DataFrame,
    *,
    short: int = 5,
    long: int = 20,
) -> bool:
    """Golden-cross detection using simple moving averages."""
    df = df.copy()
    df["sma_short"] = calc_sma(df["close"], short)
    df["sma_long"] = calc_sma(df["close"], long)

    # Drop rows with NaNs to ensure we have valid SMA values
    valid = df.dropna(subset=["sma_short", "sma_long"])
    if len(valid) < 2:
        return False
    diff = valid["sma_short"] - valid["sma_long"]
    crosses = (diff.shift() <= 0) & (diff > 0)
    # Check last two bars for a fresh bullish crossover
    return bool(crosses.iloc[-1] or crosses.iloc[-2])
