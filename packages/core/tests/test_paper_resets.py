"""Paper-window behavior that must hold before the next four-week clock."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd

from quantshift_core.executors.coinbase_executor import CoinbaseExecutor
from quantshift_core.executors.simulated_kraken_executor import SimulatedKrakenExecutor
from quantshift_core.strategies.base_strategy import Signal, SignalType


def _coinbase():
    return CoinbaseExecutor(
        SimpleNamespace(name="Test"),
        coinbase_client=None,
        symbols=["DOGE-USD"],
        simulated_capital=10000,
        risk_config={"max_positions": 8},
    )


def _signal(kind, symbol, price, size, stop=None):
    return Signal(
        signal_type=kind,
        symbol=symbol,
        timestamp=datetime.now(timezone.utc),
        price=price,
        position_size=size,
        stop_loss=stop,
        reason="test",
    )


def test_coinbase_paper_sells_a_fractional_position():
    executor = _coinbase()
    executor._sim_positions["DOGE-USD"] = {
        "quantity": 0.4,
        "entry_price": 0.1,
        "current_price": 0.1,
    }
    executor._sim_cash = 9999.96

    order = executor.execute_signal(_signal(SignalType.SELL, "DOGE-USD", 0.12, 0))

    assert order is not None
    assert order["qty"] == 0.4
    assert "DOGE-USD" not in executor._sim_positions


def test_coinbase_paper_stop_closes_the_position():
    executor = _coinbase()
    opened = executor.execute_signal(_signal(SignalType.BUY, "DOGE-USD", 1.0, 10, stop=0.9))

    assert opened is not None
    assert executor._sim_positions["DOGE-USD"]["stop_loss"] == 0.9

    closed = executor._close_paper_brackets({"DOGE-USD": pd.DataFrame({"close": [0.85]})})

    assert len(closed) == 1
    assert "DOGE-USD" not in executor._sim_positions


def test_kraken_paper_execute_signal_opens_long_and_short():
    executor = SimulatedKrakenExecutor.__new__(SimulatedKrakenExecutor)
    executor._cash = 5000.0
    executor._positions = {}
    executor.max_leverage = 2.0
    executor.risk_config = {"max_positions": 6}
    executor._next_order_id = 1

    opened = executor.execute_signal(_signal(SignalType.BUY, "SOLUSD", 100.0, 2, stop=90))
    shorted = executor.execute_signal(_signal(SignalType.SELL, "ETHUSD", 200.0, 1))

    assert opened["status"] == "SIMULATED"
    assert executor._positions["SOLUSD"]["side"] == "long"
    assert executor._positions["SOLUSD"]["stop_loss"] == 90
    assert shorted["side"] == "SELL"
    assert executor._positions["ETHUSD"]["side"] == "short"


def test_kraken_paper_sells_a_fractional_long():
    executor = SimulatedKrakenExecutor.__new__(SimulatedKrakenExecutor)
    executor._cash = 5000.0
    executor._positions = {
        "DOGEUSD": {
            "quantity": 0.4,
            "entry_price": 0.1,
            "current_price": 0.1,
            "unrealized_pl": 0.0,
            "side": "long",
            "leverage": 2.0,
            "margin": 0.02,
        }
    }
    executor.max_leverage = 2.0
    executor.risk_config = {"max_positions": 6}
    executor._next_order_id = 1

    order = executor.execute_signal(_signal(SignalType.SELL, "DOGEUSD", 0.12, 0))

    assert order is not None
    assert order["qty"] == 0.4
    assert "DOGEUSD" not in executor._positions
