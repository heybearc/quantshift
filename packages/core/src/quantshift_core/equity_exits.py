"""Long-only equity exit rules.

Alpaca reports a short with a positive share count and a separate side.
A market sell larger than the long, or a sell while flat, opens a short.
These helpers keep an exit inside the shares already held.
"""

from typing import Any, Dict, Optional


def _label(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "").lower()


def broker_side(qty: float, side: Any) -> str:
    """Use the broker side. Fall back to the sign of qty only when side is absent."""
    label = _label(side)
    if label in ("long", "short"):
        return label
    return "long" if float(qty) > 0 else "short"


def signed_quantity(qty: float, side: str) -> float:
    """Positive for a long, negative for a short."""
    size = abs(float(qty))
    return size if side == "long" else -size


def qty_text(qty: float) -> str:
    """Share count as Alpaca expects it on a close request."""
    if abs(qty - round(qty)) < 1e-9:
        return str(int(round(qty)))
    return f"{qty:.8f}".rstrip("0").rstrip(".")


def add_stop(book: Dict[str, Dict[str, float]], symbol: str, order_side: Any, stop_price: Any) -> None:
    """Keep the tightest protective stop. A sell stop protects a long; a buy stop protects a short."""
    if not symbol or stop_price is None:
        return
    label = _label(order_side)
    if label not in ("buy", "sell"):
        return
    price = float(stop_price)
    slot = book.setdefault(symbol, {})
    if label == "sell":
        slot["sell"] = price if "sell" not in slot else max(slot["sell"], price)
    else:
        slot["buy"] = price if "buy" not in slot else min(slot["buy"], price)


def stop_for_position(book: Dict[str, Dict[str, float]], symbol: str, position_side: str) -> Optional[float]:
    slot = book.get(symbol) or {}
    if position_side == "long":
        return slot.get("sell")
    if position_side == "short":
        return slot.get("buy")
    return None


def exit_instruction(position_side: Optional[str], held_qty: float, requested_qty: Optional[float]) -> Optional[Dict[str, Any]]:
    """Order that reduces the current position. None when flat, so a sell cannot open a short."""
    if position_side not in ("long", "short"):
        return None
    held = abs(float(held_qty))
    if held <= 0:
        return None
    if requested_qty is None or float(requested_qty) == 0:
        requested = held
    else:
        requested = abs(float(requested_qty))
    qty = min(requested, held)
    if qty <= 0:
        return None
    return {"side": "sell" if position_side == "long" else "buy", "qty": qty}
