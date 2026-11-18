"""Equity contest catalog.

The paper book still sends only the washout and the volatility break.
The seven older strategies are candidates: they are scored and journaled,
and they do not place orders. Band snap and sprint stay on their own books.
A price-direction model and a position sizer are not strategies, so they
are not candidates.
"""

from typing import Any, Callable, Dict, List

from .strategies.bollinger_bounce import BollingerBounce
from .strategies.breakout_momentum import BreakoutMomentum
from .strategies.donchian_breakout import DonchianBreakoutStrategy
from .strategies.keltner_channel import KeltnerChannelStrategy
from .strategies.ma_crossover import MACrossoverStrategy
from .strategies.rsi_mean_reversion import RSIMeanReversion
from .strategies.trade_confident import TradeConfidentSetup, VolatilityBreakoutSetup
from .strategies.vwap_reversion import VWAPReversionStrategy


class CatalogEntry:
    """One candidate the ranker can score."""

    def __init__(self, name: str, role: str, build: Callable, executable: bool):
        self.name = name
        self.role = role
        self.build = build
        self.executable = executable


def _build(cls, long_only: bool):
    def factory(params: Dict[str, Any] | None = None):
        config = {"enable_shorts": not long_only, "risk_per_trade": 0.015}
        config.update(params or {})
        config["risk_per_trade"] = 0.015
        if long_only:
            config["enable_shorts"] = False
        return cls(config=config)

    return factory


def equity_catalog(long_only: bool = True) -> List[CatalogEntry]:
    """Seven older strategies, then the two setups the paper book can send."""
    older = [
        ("BollingerBounce", "mean_reversion", BollingerBounce),
        ("RSIMeanReversion", "mean_reversion", RSIMeanReversion),
        ("VWAPReversionStrategy", "mean_reversion", VWAPReversionStrategy),
        ("KeltnerChannelStrategy", "mean_reversion", KeltnerChannelStrategy),
        ("MACrossoverStrategy", "trend", MACrossoverStrategy),
        ("BreakoutMomentum", "breakout", BreakoutMomentum),
        ("DonchianBreakoutStrategy", "breakout", DonchianBreakoutStrategy),
    ]
    live = [
        ("TradeConfidentSetup", "washout", TradeConfidentSetup),
        ("VolatilityBreakoutSetup", "volatility_break", VolatilityBreakoutSetup),
    ]
    entries = [
        CatalogEntry(name, role, _build(cls, long_only), False)
        for name, role, cls in older
    ]
    entries.extend(
        CatalogEntry(name, role, _build(cls, long_only), True)
        for name, role, cls in live
    )
    return entries


def shadow_strategies(long_only: bool = True) -> list:
    """The seven candidates that are journaled and never sent."""
    return [entry.build() for entry in equity_catalog(long_only) if not entry.executable]


def held_back() -> Dict[str, str]:
    """Pieces that stay out of the catalog until the ranker has real closes."""
    return {
        "BandSnapSetup": "15-minute Kraken book, not an equity candidate",
        "SprintBreakSetup": "separate sprint book",
        "price_direction": "forecasts the next bar; it has no closed trades to score",
        "rl_position_sizer": "changes size after a setup is chosen, and it is not wired to the book",
        "kelly_position_sizer": "changes size, and it stays off until a setup has enough closes",
    }
