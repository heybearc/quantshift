"""Stable order ids for one trading decision.

The same bot, symbol, side, bar, and leg always produce the same id, so a
restart submits the order the broker already accepted instead of a second one.
"""

import hashlib
import uuid


def decision_key(bot_name: str, symbol: str, side: str, bar_time: str, leg: str) -> str:
    """Canonical identity for one order leg."""
    return "|".join(
        [
            str(bot_name or "").strip(),
            str(symbol or "").strip(),
            str(side or "").strip().lower(),
            str(bar_time or "").strip(),
            str(leg or "entry").strip(),
        ]
    )


def alpaca_client_order_id(bot_name: str, symbol: str, side: str, bar_time: str, leg: str) -> str:
    """Alpaca client order id. Hex, at most 48 characters, stable for this decision."""
    digest = hashlib.sha256(decision_key(bot_name, symbol, side, bar_time, leg).encode()).hexdigest()
    return f"qs{digest[:46]}"


def coinbase_client_order_id(bot_name: str, symbol: str, side: str, bar_time: str, leg: str) -> str:
    """Coinbase client order id. UUID5, stable for this decision."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, decision_key(bot_name, symbol, side, bar_time, leg)))


def kraken_userref(bot_name: str, symbol: str, side: str, bar_time: str, leg: str) -> int:
    """Kraken userref. Positive 31-bit int, stable for this decision."""
    digest = hashlib.sha256(decision_key(bot_name, symbol, side, bar_time, leg).encode()).digest()
    return (int.from_bytes(digest[:4], "big") & 0x7FFFFFFF) or 1


def kraken_txid_for_userref(order_book: dict, userref: int) -> str | None:
    """Return the txid for this userref. A canceled or expired order does not count."""
    skipped = {"canceled", "cancelled", "expired"}
    for txid, order in (order_book or {}).items():
        if not isinstance(order, dict):
            continue
        if str(order.get("status") or "").lower() in skipped:
            continue
        try:
            seen = int(order.get("userref") or 0)
        except (TypeError, ValueError):
            continue
        if seen == int(userref):
            return str(txid)
    return None
