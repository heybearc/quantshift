"""The sprint break takes a 15-minute range break only when the target clears 1%."""

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
from quantshift_core.strategies.base_strategy import Account, Position, SignalType
from quantshift_core.strategies.sprint_break import SprintBreakSetup


def _host(rows):
    frame = pd.DataFrame(rows).set_index("timestamp")
    host = frame.copy()
    host.attrs["noise"] = AttachedFrame(frame)
    host.symbol = "XBTUSD"
    return host


def _rows(count, close=100.0, high=100.4, low=99.6):
    start = datetime(2026, 1, 1)
    rows = []
    for index in range(count):
        rows.append({
            "timestamp": start + timedelta(minutes=15 * index),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1000,
        })
    return rows


def _account():
    return Account(equity=5000.0, cash=5000.0, buying_power=5000.0)


def test_long_break_with_room_is_taken():
    rows = _rows(9)
    rows[-1]["close"] = 101.5
    rows[-1]["high"] = 101.6
    rows[-1]["low"] = 100.0
    signals = SprintBreakSetup({"enable_shorts": True, "min_reward_pct": 0.01}).generate_signals(
        _host(rows), _account(), []
    )
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.BUY
    assert signals[0].take_profit > signals[0].price
    assert (signals[0].take_profit - signals[0].price) / signals[0].price >= 0.01


def test_tight_break_is_refused():
    rows = _rows(9)
    rows[-1]["close"] = 100.5
    rows[-1]["high"] = 100.55
    rows[-1]["low"] = 100.35
    signals = SprintBreakSetup({"enable_shorts": True, "min_reward_pct": 0.01}).generate_signals(
        _host(rows), _account(), []
    )
    assert signals == []


def test_short_break_with_room_is_taken():
    rows = _rows(9)
    rows[-1]["close"] = 98.5
    rows[-1]["low"] = 98.4
    rows[-1]["high"] = 100.0
    signals = SprintBreakSetup({"enable_shorts": True, "min_reward_pct": 0.01}).generate_signals(
        _host(rows), _account(), []
    )
    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.SELL
    assert signals[0].take_profit < signals[0].price


def test_shorts_stay_off_when_disabled():
    rows = _rows(9)
    rows[-1]["close"] = 98.5
    rows[-1]["low"] = 98.4
    rows[-1]["high"] = 100.0
    signals = SprintBreakSetup({"enable_shorts": False, "min_reward_pct": 0.01}).generate_signals(
        _host(rows), _account(), []
    )
    assert signals == []


def test_open_sprint_closes_after_the_hold():
    rows = _rows(9)
    held = Position(
        symbol="XBTUSD",
        quantity=1,
        entry_price=100,
        current_price=100,
        market_value=100,
        unrealized_pl=0,
        unrealized_plpc=0,
        side="long",
        metadata={
            "strategy": "SprintBreakSetup",
            "opened_at": (datetime.utcnow() - timedelta(minutes=120)).isoformat(),
        },
    )
    signals = SprintBreakSetup({"max_hold_minutes": 90}).generate_signals(_host(rows), _account(), [held])
    assert len(signals) == 1
    assert signals[0].reason == "sprint break time stop"
    assert signals[0].signal_type == SignalType.SELL
