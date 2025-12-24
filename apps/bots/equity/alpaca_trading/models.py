"""Shared dataclasses and type aliases used across the trading bot.

Extracted from the original *screener.py* / *strategy.py* code so they can be
re-used by multiple components without circular imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Optional

__all__ = [
    "Side",
    "Opportunity",
    "TradeRecord",
]

Side = Literal["buy", "sell"]


@dataclass(frozen=True)
class Opportunity:
    """Potential trading signal returned by the screener."""

    symbol: str
    price: float
    signal: Literal["BUY", "SELL", "HOLD"]
    reason: str
    timestamp: datetime

    # Extra analytics – optional
    atr: Optional[float] = None
    atr_pct: Optional[float] = None
    volume_ratio: Optional[float] = None


@dataclass
class TradeRecord:
    """Row in the persistent trade log."""

    timestamp: datetime
    date: str
    symbol: str
    side: Side
    qty: int
    price: float
    amount: float
    order_id: str
    status: str
    reason: str
    atr: Optional[float] = None
    atr_pct: Optional[float] = None
    volume_ratio: Optional[float] = None

    @classmethod
    def fieldnames(cls) -> List[str]:
        return [f.name for f in cls.__dataclass_fields__.values()]  # type: ignore[attr-defined]

    def as_dict(self) -> Dict[str, str | int | float]:
        """Return values serialisable by :pymod:`csv` writer."""
        d = self.__dict__.copy()
        d["timestamp"] = self.timestamp.isoformat()
        return d
