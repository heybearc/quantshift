"""Equity paper book uses the washout and the volatility break, long only."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yaml

from quantshift_core.candles import attached_frame
from quantshift_core.executors.alpaca_executor import AlpacaExecutor
from quantshift_core.strategies.base_strategy import BaseStrategy


ROOT = Path(__file__).resolve().parents[3]


class _Quiet(BaseStrategy):
    def generate_signals(self, market_data, account, positions):
        return []

    def calculate_position_size(self, signal, account, atr=None):
        return 0


def _ohlc(index):
    frame = pd.DataFrame(
        {
            "open": 10.0,
            "high": 11.0,
            "low": 9.0,
            "close": 10.5,
            "volume": 1000.0,
        },
        index=index,
    )
    return frame


class _Data:
    def __init__(self, frames):
        self.frames = frames
        self.calls = []

    def get_stock_bars(self, request):
        self.calls.append(request.timeframe)
        symbol = request.symbol_or_symbols
        if isinstance(symbol, list):
            symbol = symbol[0]
        frame = self.frames[str(request.timeframe)].copy()

        class _Bars:
            df = frame

        return _Bars()


def test_equity_config_is_the_two_long_setups():
    config = yaml.safe_load((ROOT / "config" / "equity_config.yaml").read_text())
    kinds = [item["type"] for item in config["strategies"]]
    assert kinds == ["TradeConfidentSetup", "VolatilityBreakoutSetup"]
    for item in config["strategies"]:
        assert item["params"]["enable_shorts"] is False
        assert item["params"]["max_notional"] == 0.05
    allocation = config["orchestrator"]["capital_allocation"]
    assert set(allocation) == {"TradeConfidentSetup", "VolatilityBreakoutSetup"}
    assert config["orchestrator"]["use_strategy_contest"] is True
    assert "BandSnapSetup" not in kinds


def test_daily_bars_carry_the_last_finished_hour():
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    daily_index = pd.date_range(end=now - timedelta(days=3), periods=5, freq="D", tz="UTC")
    hourly_index = pd.date_range(end=now, periods=40, freq="h", tz="UTC")
    from alpaca.data.timeframe import TimeFrame

    data = _Data(
        {
            str(TimeFrame.Day): _ohlc(daily_index),
            str(TimeFrame.Hour): _ohlc(hourly_index),
        }
    )
    executor = AlpacaExecutor(_Quiet(), object(), data_client=data, symbols=["AAPL"])
    frame = executor.get_market_data("AAPL", days=450)
    entry = attached_frame(frame, "entry")
    assert entry is not None
    opened = entry.index[-1].tz_convert("UTC").to_pydatetime().replace(tzinfo=None)
    assert opened + timedelta(hours=1) <= datetime.utcnow()
