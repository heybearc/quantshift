"""A person's desk beside the house books.

House mode watches the shared paper books. Personal mode keeps a paper bot
per broker. A published community strategy can be tried only on that personal
paper book. An unknown broker still gets a stopped paper slot until an adapter
exists. None of these records place an order.
"""

import re
from typing import Dict, Iterable, List, Sequence

_SYMBOL = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")
_VENUE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Ready means this repo already has a paper executor. Needed means the slot
# exists and paper will be available once that adapter is written.
BROKERS = (
    {"id": "alpaca", "name": "Alpaca", "adapter": "ready"},
    {"id": "coinbase", "name": "Coinbase", "adapter": "ready"},
    {"id": "kraken", "name": "Kraken", "adapter": "ready"},
    {"id": "schwab", "name": "Charles Schwab", "adapter": "needed"},
    {"id": "ibkr", "name": "Interactive Brokers", "adapter": "needed"},
    {"id": "tradier", "name": "Tradier", "adapter": "needed"},
)
_BY_ID = {broker["id"]: broker for broker in BROKERS}


def normalize_symbol(symbol: str) -> str:
    """Uppercase ticker or pair. Empty when the text is not a symbol."""
    cleaned = str(symbol or "").strip().upper()
    if not _SYMBOL.match(cleaned):
        return ""
    return cleaned


def venue_slug(name: str) -> str:
    """A short id for a broker. Empty when the name cannot be a venue."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(name or "").strip().lower()).strip("-")
    if not _VENUE.match(slug) or not 2 <= len(slug) <= 32:
        return ""
    return slug


def describe_bot(name: str) -> Dict[str, str]:
    """A stopped paper bot. Unknown brokers wait for an adapter and stay on paper."""
    slug = name if name in _BY_ID else venue_slug(name)
    known = _BY_ID.get(slug)
    adapter = known["adapter"] if known else "needed"
    return {
        "venue": slug,
        "display_name": known["name"] if known else str(name or "").strip(),
        "status": "stopped" if adapter == "ready" else "needs_adapter",
        "trading_mode": "paper",
        "adapter": adapter,
        "paper": "true",
    }


def personal_bot_set() -> List[Dict[str, str]]:
    """The brokers whose paper executors already exist."""
    return [describe_bot(broker["id"]) for broker in BROKERS if broker["adapter"] == "ready"]


def can_try_strategy(book_mode: str, status: str, accepted_risk: bool) -> bool:
    """A published community strategy can be marked on a personal paper book only."""
    return (book_mode or "").lower() == "personal" and status == "published" and bool(accepted_risk)


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
    """Publishing a note does not by itself send an order."""
    return False
