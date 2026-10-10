"""Read-only snapshot of why a signal was produced.

This does not change the signal. Callers attach it to the order record.
"""

from typing import Any, Dict, Optional


def decision_snapshot(signal: Any) -> Dict[str, Any]:
    meta = signal.metadata or {}
    return {
        "strategy": meta.get("strategy") or "",
        "regime": meta.get("regime"),
        "regime_confidence": _num(meta.get("regime_confidence")),
        "sentiment_score": _num(meta.get("sentiment_score")),
        "trend_slope": _num(meta.get("trend_slope")),
        "volatility": _num(meta.get("volatility")),
        "market_breadth": _num(meta.get("market_breadth")),
        "vix": _num(meta.get("vix")),
        "signal_reason": getattr(signal, "reason", "") or "",
    }


def decision_reason(signal: Any) -> str:
    snap = decision_snapshot(signal)
    parts = []
    if snap["strategy"]:
        parts.append(str(snap["strategy"]))
    if snap["signal_reason"]:
        parts.append(str(snap["signal_reason"]))
    if snap["regime"]:
        confidence = snap["regime_confidence"]
        confidence_text = f" {confidence * 100:.0f}%" if confidence is not None else ""
        parts.append(f"regime {snap['regime']}{confidence_text}")
    if snap["sentiment_score"] is not None:
        parts.append(f"sentiment {snap['sentiment_score']:+.2f}")
    return " · ".join(parts)


def _num(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
