"""A person's desk beside the house books.

House mode watches the shared paper books. Personal mode records a stopped
bot for each venue and a symbol list. Those records do not place orders.
A strategy note stays a suggestion until someone promotes it into the catalog.
"""

import re
from typing import Dict, Iterable, List, Sequence

PERSONAL_VENUES = ("alpaca", "coinbase", "kraken")
_SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")


def normalize_symbol(symbol: str) -> str:
    """Uppercase ticker or pair. Empty when the text is not a symbol."""
    cleaned = str(symbol or "").strip().upper()
    if not _SYMBOL.match(cleaned):
        return ""
    return cleaned


def personal_bot_set() -> List[Dict[str, str]]:
    """One stopped paper bot per venue. Keys and processes come later."""
    return [
        {"venue": venue, "status": "stopped", "trading_mode": "paper"}
        for venue in PERSONAL_VENUES
    ]


def ordered_symbols(preferences: Iterable[Dict[str, str]], intent: str = "") -> List[str]:
    """Trade marks first, then research marks. Duplicates collapse."""
    trade: List[str] = []
    research: List[str] = []
    for row in preferences:
        symbol = normalize_symbol(row.get("symbol") or "")
        if not symbol:
            continue
        mark = (row.get("intent") or "research").lower()
        bucket = trade if mark == "trade" else research
        if symbol not in bucket and symbol not in trade and symbol not in research:
            bucket.append(symbol)
    if intent == "trade":
        return trade
    if intent == "research":
        return research
    return trade + research


def symbols_for_book(mode: str, house_universe: Sequence[str], preferences: Iterable[Dict[str, str]]) -> List[str]:
    """House keeps its own universe. A personal book scans the trade marks."""
    if (mode or "house").lower() != "personal":
        return [normalize_symbol(symbol) for symbol in house_universe if normalize_symbol(symbol)]
    return ordered_symbols(preferences, intent="trade")


def suggestion_can_trade(status: str) -> bool:
    """A community or engine note is not a strategy the book can run."""
    return False
