"""The band snap only fades a closed 15-minute tag, and it leaves other setups alone."""

import sys
import types
from datetime import datetime, timedelta

import pandas as pd


class _Unused:
    pass


def _stub(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


try:
    import sklearn.ensemble  # noqa: F401
except ImportError:
    _stub("sklearn")
    _stub("sklearn.ensemble", RandomForestClassifier=_Unused)
    _stub("sklearn.model_selection", train_test_split=_Unused, cross_val_score=_Unused)
    _stub("sklearn.preprocessing", StandardScaler=_Unused)
    _stub("sklearn.metrics", classification_report=_Unused, accuracy_score=_Unused)

from quantshift_core.candles import AttachedFrame
from quantshift_core.strategies.band_snap import BandSnapSetup
from quantshift_core.strategies.base_strategy import Account, Position, SignalType


def _host(closes, last_low=None, last_high=None):
    start = datetime(2026, 1, 1)
    rows = []
    for index, close in enumerate(closes):
        low = close - 0.3
        high = close + 0.3
        if index == len(closes) - 1:
            if last_low is not None:
                low = last_low
            if last_high is not None:
                high = last_high
        rows.append({
            "timestamp": start + timedelta(minutes=15 * index),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1000,
        })
    frame = pd.DataFrame(rows).set_index("timestamp")
    host = frame.copy()
    host.attrs["noise"] = AttachedFrame(frame)
    host.symbol = "BTC-USD"
    return host


def _long_host():
    closes = [100 + ((index % 5) - 2) * 1.5 for index in range(40)]
    for _ in range(5):
        series = pd.Series(closes, dtype=float)
        mid = float(series.rolling(20).mean().iloc[-1])
        width = float(series.rolling(20).std().iloc[-1])
        lower = mid - (2.0 * width)
        closes[-1] = (mid + lower) / 2.0
    series = pd.Series(closes, dtype=float)
    lower = float(series.rolling(20).mean().iloc[-1] - 2.0 * series.rolling(20).std().iloc[-1])
    return _host(closes, last_low=lower - 2.0)


def _short_host():
    closes = [100 + ((index % 5) - 2) * 1.5 for index in range(40)]
    for _ in range(5):
        series = pd.Series(closes, dtype=float)
        mid = float(series.rolling(20).mean().iloc[-1])
        width = float(series.rolling(20).std().iloc[-1])
        upper = mid + (2.0 * width)
        closes[-1] = (mid + upper) / 2.0
    series = pd.Series(closes, dtype=float)
    upper = float(series.rolling(20).mean().iloc[-1] + 2.0 * series.rolling(20).std().iloc[-1])
    return _host(closes, last_high=upper + 2.0)


def _account():
    return Account(equity=10000, cash=10000, buying_power=10000, portfolio_value=10000)


def test_a_tag_of_the_lower_band_buys_back_toward_the_middle():
    strategy = BandSnapSetup(config={"enable_shorts": False, "min_reward_pct": 0.001, "risk_per_trade": 0.0025})
    signals = strategy.generate_signals(_long_host(), _account(), [])
    assert len(signals) == 1
    signal = signals[0]
    assert signal.signal_type == SignalType.BUY
    assert signal.reason == "band snap long"
    assert signal.stop_loss < signal.price < signal.take_profit
    assert signal.position_size > 0


def test_a_snap_smaller_than_the_fee_is_skipped():
    strategy = BandSnapSetup(config={"enable_shorts": False, "min_reward_pct": 0.5})
    assert strategy.generate_signals(_long_host(), _account(), []) == []


def test_coinbase_does_not_short_the_upper_band():
    strategy = BandSnapSetup(config={"enable_shorts": False, "min_reward_pct": 0.001})
    assert strategy.generate_signals(_short_host(), _account(), []) == []


def test_kraken_can_short_the_upper_band():
    strategy = BandSnapSetup(config={"enable_shorts": True, "min_reward_pct": 0.001, "risk_per_trade": 0.0025})
    signals = strategy.generate_signals(_short_host(), _account(), [])
    assert len(signals) == 1
    signal = signals[0]
    assert signal.signal_type == SignalType.SELL
    assert signal.take_profit < signal.price < signal.stop_loss


def test_a_name_held_by_another_setup_is_left_alone():
    held = Position(
        symbol="BTC-USD",
        quantity=1,
        entry_price=100,
        current_price=100,
        market_value=100,
        unrealized_pl=0,
        unrealized_plpc=0,
        side="long",
        metadata={"strategy": "TradeConfidentSetup", "opened_at": datetime.utcnow().isoformat()},
    )
    strategy = BandSnapSetup(config={"enable_shorts": False, "min_reward_pct": 0.001})
    assert strategy.generate_signals(_long_host(), _account(), [held]) == []


def test_an_open_band_snap_exits_after_three_hours():
    opened = (datetime.utcnow() - timedelta(hours=4)).replace(microsecond=0).isoformat()
    held = Position(
        symbol="BTC-USD",
        quantity=1.25,
        entry_price=100,
        current_price=101,
        market_value=126.25,
        unrealized_pl=1.25,
        unrealized_plpc=0.01,
        side="long",
        metadata={"strategy": "BandSnapSetup", "opened_at": opened},
    )
    host = _long_host()
    host.attrs["noise"].frame.attrs["mark_price"] = 101
    strategy = BandSnapSetup(config={"max_hold_minutes": 180})
    signals = strategy.generate_signals(host, _account(), [held])
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.SELL
    assert signals[0].reason == "band snap time stop"
    assert signals[0].position_size == 1.25
