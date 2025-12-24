"""Data-access helpers for Alpaca.

This is an *extraction* from the original monolithic `screener.py`.  The goal is
not to change behaviour but simply to lift low-level routines into their own
module so they can be reused by both the real-time screener and future backtest
code.

All functions accept a `tradeapi.REST` client so that the caller can decide
whether to use live, paper, or sandbox credentials.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
from alpaca_trade_api import REST, TimeFrame

from .logging import logging as _logging  # reuse configured root

logger = _logging.getLogger(__name__)

__all__ = [
    "get_market_data",
    "calc_sma",
    "calc_atr",
    "MultiSourceDataProvider",
    "create_data_provider",
]


class MultiSourceDataProvider:
    """Multi-source data provider for fetching market data from various sources.
    
    Currently uses Alpaca as the primary data source.
    """
    
    def __init__(self, api: REST):
        self.api = api
    
    def get_bars(self, symbol: str, timeframe: TimeFrame, start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch OHLCV bars for a symbol."""
        try:
            bars = self.api.get_bars(symbol, timeframe, start=start, end=end, adjustment="all").df
            if not bars.empty:
                bars.index = bars.index.tz_localize(None)
            return bars
        except Exception as exc:
            logger.error("Error fetching bars for %s: %s", symbol, exc)
            return pd.DataFrame()
    
    def get_latest_quote(self, symbol: str) -> dict:
        """Get the latest quote for a symbol."""
        try:
            quote = self.api.get_latest_quote(symbol)
            return {
                "bid": float(quote.bid_price) if quote.bid_price else 0,
                "ask": float(quote.ask_price) if quote.ask_price else 0,
                "last": float(quote.ask_price) if quote.ask_price else 0,
            }
        except Exception as exc:
            logger.error("Error fetching quote for %s: %s", symbol, exc)
            return {"bid": 0, "ask": 0, "last": 0}


def create_data_provider(api: REST) -> MultiSourceDataProvider:
    """Factory function to create a data provider instance."""
    return MultiSourceDataProvider(api)


def get_market_data(api: REST, symbol: str, days: int = 90) -> pd.DataFrame:
    """Fetch OHLCV candles for *symbol* over *days* trading days."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    try:
        bars = api.get_bars(symbol, TimeFrame.Day, start=start, end=end, adjustment="all").df
        bars.index = bars.index.tz_localize(None)  # Strip timezone for math
        return bars
    except Exception as exc:  # noqa: BLE001
        logger.error("Error fetching market data for %s: %s", symbol, exc, exc_info=True)
        raise


def calc_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average, window in periods (no centre)."""
    return series.rolling(window=window, min_periods=window).mean()


def calc_atr(df: pd.DataFrame, period: int = 14) -> float:
    """Average True Range.

    Returns the *latest* ATR value, not the full series, because callers mostly
    want a single number to base position sizing on.
    """
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return float(atr.iloc[-1])
