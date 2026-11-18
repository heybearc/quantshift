"""The equity contest scores real closes and does not add a new strategy family."""

from datetime import datetime, timezone

import pandas as pd

from quantshift_core.strategies.base_strategy import Account, BaseStrategy, Signal, SignalType
from quantshift_core.strategy_catalog import equity_catalog, held_back, shadow_strategies
from quantshift_core.strategy_contest import run_contest
from quantshift_core.strategy_ranker import choose_buy, normalize_close, score_closes


class _Buy(BaseStrategy):
    def __init__(self, symbol="AAPL", confidence=0.5):
        super().__init__({})
        self.symbol = symbol
        self.confidence = confidence

    def generate_signals(self, market_data, account, positions):
        return [
            Signal(
                signal_type=SignalType.BUY,
                symbol=self.symbol,
                timestamp=datetime.now(timezone.utc),
                price=10.0,
                confidence=self.confidence,
                metadata={"strategy": self.name},
            )
        ]

    def calculate_position_size(self, signal, account, atr=None):
        return 1


def _closes():
    return [
        {"strategy": "TradeConfidentSetup", "pnl": 5, "regime": "bull_trending"},
        {"strategy": "TradeConfidentSetup", "pnl": 4, "regime": "bull_trending"},
        {"strategy": "TradeConfidentSetup", "pnl": 20, "entry_reason": "regime bear_trending 80%"},
        {"strategy": "VolatilityBreakoutSetup", "pnl": -1, "regime": "bull_trending"},
        {"strategy": "VolatilityBreakoutSetup", "pnl": -2, "regime": "bull_trending"},
        {"strategy": "BollingerBounce", "pnl": 9, "regime": "bull_trending"},
        {"strategy": "BollingerBounce", "pnl": 8, "regime": "bull_trending"},
    ]


def test_catalog_covers_the_existing_families_and_holds_the_models():
    entries = equity_catalog()
    assert [entry.name for entry in entries] == [
        "BollingerBounce",
        "RSIMeanReversion",
        "VWAPReversionStrategy",
        "KeltnerChannelStrategy",
        "MACrossoverStrategy",
        "BreakoutMomentum",
        "DonchianBreakoutStrategy",
        "TradeConfidentSetup",
        "VolatilityBreakoutSetup",
    ]
    assert [entry.name for entry in entries if entry.executable] == [
        "TradeConfidentSetup",
        "VolatilityBreakoutSetup",
    ]
    roles = {entry.role for entry in entries}
    assert roles == {"mean_reversion", "trend", "breakout", "washout", "volatility_break"}
    blocked = held_back()
    assert "price_direction" in blocked
    assert "rl_position_sizer" in blocked
    assert "kelly_position_sizer" in blocked
    assert "BandSnapSetup" in blocked
    assert "SprintBreakSetup" in blocked
    shadows = shadow_strategies()
    assert len(shadows) == 7
    assert all(strategy.shorts_enabled() is False for strategy in shadows)


def test_a_close_scores_only_inside_its_regime():
    closes = [normalize_close(row) for row in _closes()]
    bull = score_closes(closes, "TradeConfidentSetup", "bull_trending")
    bear = score_closes(closes, "TradeConfidentSetup", "bear_trending")
    assert bull["closes"] == 2
    assert bull["expectancy"] == 4.5
    assert bear["closes"] == 1
    assert score_closes(closes, "TradeConfidentSetup", None) is None


def test_unscored_signals_stay_with_the_book():
    wash = Signal(
        SignalType.BUY,
        "AAPL",
        datetime.now(timezone.utc),
        10,
        confidence=0.2,
        metadata={"strategy": "TradeConfidentSetup"},
    )
    vol = Signal(
        SignalType.BUY,
        "AAPL",
        datetime.now(timezone.utc),
        10,
        confidence=0.9,
        metadata={"strategy": "VolatilityBreakoutSetup"},
    )
    choice = choose_buy(
        [wash, vol],
        {"TradeConfidentSetup": None, "VolatilityBreakoutSetup": None},
        30,
    )
    assert choice["reason"] == "unscored"
    assert choice["signals"] == [wash, vol]


def test_a_losing_scored_setup_stands_down():
    vol = Signal(
        SignalType.BUY,
        "AAPL",
        datetime.now(timezone.utc),
        10,
        metadata={"strategy": "VolatilityBreakoutSetup"},
    )
    score = score_closes(
        [normalize_close(row) for row in _closes()],
        "VolatilityBreakoutSetup",
        "bull_trending",
    )
    choice = choose_buy([vol], {"VolatilityBreakoutSetup": score}, 2)
    assert choice["reason"] == "stood_down"
    assert choice["signals"] == []


def test_the_book_keeps_the_scored_setup_and_journals_the_shadow():
    wash = _Buy(confidence=0.2)
    wash.name = "TradeConfidentSetup"
    vol = _Buy(confidence=0.9)
    vol.name = "VolatilityBreakoutSetup"
    shadow = _Buy(confidence=0.99)
    shadow.name = "BollingerBounce"
    frame = pd.DataFrame({"close": [10.0, 11.0]})
    account = Account(10000, 10000, 10000)
    live = wash.generate_signals(frame, account, []) + vol.generate_signals(frame, account, [])
    signals, journal = run_contest(
        live_signals=live,
        shadows=[shadow],
        market_data={"AAPL": frame},
        account=account,
        positions=[],
        regime="bull_trending",
        closes=_closes(),
        book_names=["TradeConfidentSetup", "VolatilityBreakoutSetup"],
        min_closes=2,
    )
    assert len(signals) == 1
    assert signals[0].metadata["strategy"] == "TradeConfidentSetup"
    assert signals[0].metadata["contest"] == "scored"
    assert signals[0].metadata["contest_closes"] == 2
    assert journal["shadow_winners"][0]["strategy"] == "BollingerBounce"
    assert journal["shadow_winners"][0]["symbol"] == "AAPL"
    assert journal["by_strategy"]["BollingerBounce"]["on_book"] is False
    assert journal["by_strategy"]["TradeConfidentSetup"]["on_book"] is True
