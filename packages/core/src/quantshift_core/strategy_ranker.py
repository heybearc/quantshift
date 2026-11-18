"""Score catalog candidates from closed trades in one regime.

A score uses realized pnl only. A backtest, a forecast, and a position size
are not a score. Fewer than the minimum closes leaves the paper book on its
current choice.
"""

import re
from typing import Any, Dict, Iterable, List, Optional

from .strategies.base_strategy import Signal, SignalType


_REGIME = re.compile(r"regime\s+([a-z0-9_]+)", re.IGNORECASE)
_STAND_DOWN_HIT_RATE = 0.35


def regime_name(value: Any) -> Optional[str]:
    """Normalize a regime enum, name, or decision sentence to the stored value."""
    if value is None:
        return None
    text = getattr(value, "value", value)
    if not isinstance(text, str):
        text = str(text)
    found = _REGIME.search(text)
    token = found.group(1) if found else text.strip()
    token = token.lower()
    if token in ("", "none", "unknown"):
        return None
    return token


def normalize_close(row: Any) -> Optional[Dict[str, Any]]:
    """One closed trade: strategy, pnl, and the regime stored on the decision."""
    if isinstance(row, dict):
        strategy = row.get("strategy") or row.get("strategy_name")
        pnl = row.get("pnl", row.get("realized_pnl"))
        regime = row.get("regime") or regime_name(row.get("entry_reason"))
    else:
        strategy = getattr(row, "strategy", None) or getattr(row, "strategy_name", None)
        pnl = getattr(row, "pnl", None)
        if pnl is None:
            pnl = getattr(row, "realized_pnl", None)
        regime = getattr(row, "regime", None) or regime_name(getattr(row, "entry_reason", None))
    if not strategy or pnl is None:
        return None
    try:
        pnl_value = float(pnl)
    except (TypeError, ValueError):
        return None
    return {
        "strategy": str(strategy),
        "pnl": pnl_value,
        "regime": regime_name(regime),
    }


def score_closes(closes: Iterable[Dict[str, Any]], strategy: str, regime: Optional[str]) -> Optional[Dict[str, Any]]:
    """Hit rate, profit factor, and expectancy for one strategy in one regime."""
    regime_key = regime_name(regime)
    if regime_key is None:
        return None
    matched = [
        close for close in closes
        if close.get("strategy") == strategy and close.get("regime") == regime_key
    ]
    if not matched:
        return None
    pnls = [float(close["pnl"]) for close in matched]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    gross_loss = abs(sum(losses))
    profit_factor = None if gross_loss == 0 else sum(wins) / gross_loss
    return {
        "closes": len(pnls),
        "wins": len(wins),
        "hit_rate": len(wins) / len(pnls),
        "profit_factor": profit_factor,
        "expectancy": sum(pnls) / len(pnls),
    }


def _trusted(score: Optional[Dict[str, Any]], min_closes: int) -> bool:
    return bool(score) and int(score["closes"]) >= min_closes


def _stood_down(score: Dict[str, Any]) -> bool:
    """Same bar the crypto book already uses: enough closes, weak hit rate, profit factor under 1."""
    factor = score.get("profit_factor")
    return (
        float(score["hit_rate"]) < _STAND_DOWN_HIT_RATE
        and factor is not None
        and float(factor) < 1
    )


def _better(score: Dict[str, Any]) -> tuple:
    factor = score.get("profit_factor")
    return (
        float(score["expectancy"]),
        -1.0 if factor is None else float(factor),
        float(score["hit_rate"]),
        int(score["closes"]),
    )


def choose_buy(signals: List[Signal], scores: Dict[str, Optional[Dict[str, Any]]], min_closes: int) -> Dict[str, Any]:
    """Pick one executable buy from real closes, or leave the book alone when none are scored."""
    buys = [signal for signal in signals if signal.signal_type == SignalType.BUY]
    if not buys:
        return {"signals": [], "reason": "no_signal", "strategy": None}

    trusted = []
    for signal in buys:
        name = (signal.metadata or {}).get("strategy")
        score = scores.get(name or "")
        if _trusted(score, min_closes):
            trusted.append((signal, score))

    if not trusted:
        return {"signals": buys, "reason": "unscored", "strategy": None}

    eligible = [(signal, score) for signal, score in trusted if not _stood_down(score)]
    if not eligible:
        return {
            "signals": [],
            "reason": "stood_down",
            "strategy": (trusted[0][0].metadata or {}).get("strategy"),
        }

    signal, score = max(eligible, key=lambda item: _better(item[1]))
    if signal.metadata is None:
        signal.metadata = {}
    signal.metadata["contest"] = "scored"
    signal.metadata["contest_closes"] = score["closes"]
    signal.metadata["contest_expectancy"] = score["expectancy"]
    signal.metadata["contest_hit_rate"] = score["hit_rate"]
    return {
        "signals": [signal],
        "reason": "scored",
        "strategy": signal.metadata.get("strategy"),
        "score": score,
    }
