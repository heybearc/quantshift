"""Crypto book rules: finished hours only, and one alt bet at a time."""

from datetime import datetime
from types import SimpleNamespace

import pandas as pd

from quantshift_core.candles import drop_forming_candle
from quantshift_core.risk_manager import RiskManager


def _hourly(step: float) -> pd.DataFrame:
    index = pd.date_range("2026-10-01", periods=80, freq="h")
    close = [100 + (i * step) for i in range(80)]
    return pd.DataFrame({"close": close}, index=index)


def test_forming_hour_is_not_a_signal_bar():
    index = pd.to_datetime(["2026-10-15 12:00", "2026-10-15 13:00", "2026-10-15 14:00"])
    frame = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=index)
    kept = drop_forming_candle(frame, 3600, now=datetime(2026, 10, 15, 14, 30))
    assert list(kept["close"]) == [1.0, 2.0]


def test_closed_hour_stays():
    index = pd.to_datetime(["2026-10-15 12:00", "2026-10-15 13:00"])
    frame = pd.DataFrame({"close": [1.0, 2.0]}, index=index)
    kept = drop_forming_candle(frame, 3600, now=datetime(2026, 10, 15, 15, 5))
    assert list(kept["close"]) == [1.0, 2.0]


def test_correlated_alt_is_blocked_from_lowercase_closes():
    risk = RiskManager(max_position_correlation=0.8)
    market = {"ETH-USD": _hourly(1.0), "SOL-USD": _hourly(1.0)}
    held = [SimpleNamespace(symbol="ETH-USD")]
    reason = risk.correlation_block_reason(held, "SOL-USD", market)
    assert reason is not None
    assert "ETH-USD" in reason


def test_uncorrelated_name_is_allowed():
    risk = RiskManager(max_position_correlation=0.8)
    left = _hourly(1.0)
    right = _hourly(1.0)
    right["close"] = [100 + ((-1) ** i) for i in range(80)]
    market = {"ETH-USD": left, "BTC-USD": right}
    held = [SimpleNamespace(symbol="ETH-USD")]
    reason = risk.correlation_block_reason(held, "BTC-USD", market)
    assert reason is None
