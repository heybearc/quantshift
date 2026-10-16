"""The crypto setup only fires when the zone, the bar, the pivot, and the payoff line up."""

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

from quantshift_core.strategies.base_strategy import Account, Position, SignalType
from quantshift_core.strategies.trade_confident import (
    TradeConfidentSetup,
    reversal_bar,
    trades_in_favor,
    trend_agrees,
    whale_contradicts,
)
from quantshift_core.strategy_orchestrator import _scale_size


def _frame(closes, spread=1.0):
    start = datetime(2024, 1, 1)
    rows = []
    for index, close in enumerate(closes):
        rows.append({
            "timestamp": start + timedelta(days=index),
            "open": close - 0.2,
            "high": close + spread,
            "low": close - spread,
            "close": close,
            "volume": 1000 + index,
        })
    frame = pd.DataFrame(rows).set_index("timestamp")
    return frame


def _mostly(direction: int) -> list:
    closes = []
    price = 100.0
    for index in range(40):
        step = 0.35 * direction
        if index in (25, 26):
            step = -0.2 * direction
        price += step
        closes.append(price)
    return closes


def test_a_falling_market_is_the_long_zone():
    reading = trades_in_favor(_frame(_mostly(-1)))
    assert reading is not None
    assert reading < 20


def test_a_rising_market_is_the_short_zone():
    reading = trades_in_favor(_frame(_mostly(1)))
    assert reading is not None
    assert reading > 80


def test_reversal_buy_requires_a_down_stretch_and_an_up_close_at_the_low():
    closes = [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 8.2]
    frame = _frame(closes, spread=0.4)
    # Earlier bars close red so the count is not reset before the last bar.
    frame["open"] = frame["close"] + 0.3
    frame.iloc[-1, frame.columns.get_loc("open")] = 8.0
    frame.iloc[-1, frame.columns.get_loc("close")] = 8.6
    frame.iloc[-1, frame.columns.get_loc("low")] = 7.4
    frame.iloc[-1, frame.columns.get_loc("high")] = 8.8
    assert reversal_bar(frame) == 1


def test_target_must_be_at_least_twice_the_risk():
    strategy = TradeConfidentSetup(config={"risk_per_trade": 0.01, "enable_shorts": False})
    account = Account(equity=10000, cash=10000, buying_power=10000)
    too_close = strategy._order("BTC-USD", SignalType.BUY, 100, 99, 101, 1, account, "long")
    assert too_close == []
    wide = strategy._order("BTC-USD", SignalType.BUY, 100, 98, 110, 1, account, "long")
    assert len(wide) == 1
    assert wide[0].stop_loss < 98
    assert wide[0].take_profit == 110
    assert wide[0].position_size * 100 <= 10000 * 0.20 + 1e-6


def test_coinbase_does_not_open_a_short():
    strategy = TradeConfidentSetup(config={"enable_shorts": False})
    assert strategy.shorts_enabled() is False


def test_whole_shares_stay_whole_and_coin_fractions_stay_fractions():
    assert _scale_size(10, 0.5) == 5
    assert _scale_size(0.2, 0.5) == 0.1


def test_an_open_position_is_left_alone():
    strategy = TradeConfidentSetup(config={})
    frame = _frame([100, 101, 102, 103, 104])
    frame.symbol = "BTC-USD"
    held = Position(
        symbol="BTC-USD",
        quantity=1,
        entry_price=100,
        current_price=101,
        market_value=101,
        unrealized_pl=1,
        unrealized_plpc=0.01,
        side="long",
    )
    account = Account(equity=10000, cash=10000, buying_power=10000)
    assert strategy.generate_signals(frame, account, [held]) == []


def test_trend_needs_a_full_daily_history():
    assert trend_agrees(_frame([100 + index for index in range(50)]), "long") is False


def test_whale_money_against_a_rising_price_blocks_the_long():
    start = datetime(2024, 1, 1)
    rows = []
    price = 100.0
    for index in range(30):
        down_bar = index % 4 == 3
        price += -1.0 if down_bar else 1.2
        rows.append({
            "timestamp": start + timedelta(days=index),
            "open": price - 0.2,
            "high": price + 1,
            "low": price - 1,
            "close": price if not down_bar else price - 0.8,
            "volume": 50 if not down_bar else 5000,
        })
    frame = pd.DataFrame(rows).set_index("timestamp")
    assert whale_contradicts(frame, "long") is True
