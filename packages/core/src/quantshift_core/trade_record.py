"""Decide whether a filled order opens a trade or closes one."""

from typing import Any, Dict


def is_closing_fill(order: Any) -> bool:
    """A reduce-only fill closes the open trade. A new buy or short does not."""
    if not isinstance(order, dict):
        return False
    if order.get("closing") is True:
        return True
    return order.get("realized_pnl") is not None
