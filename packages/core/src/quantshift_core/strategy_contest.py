"""Journal every equity candidate on one finished bar, then keep one book order.

Shadow candidates are scored from the same closes. Their signal is recorded
and dropped. Risk limits still run on whatever this returns.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .strategies.base_strategy import Signal, SignalType
from .strategy_ranker import choose_buy, normalize_close, regime_name, score_closes


def run_contest(
    live_signals: List[Signal],
    shadows: list,
    market_data: Dict[str, Any],
    account: Any,
    positions: list,
    regime: Any,
    closes: Iterable[Any],
    book_names: List[str],
    min_closes: int = 30,
) -> tuple:
    """Return the signals the book may still send, plus the journal."""
    scored_closes = [close for close in (normalize_close(row) for row in closes) if close]
    regime_key = regime_name(regime)
    names = list(dict.fromkeys(list(book_names) + [strategy.name for strategy in shadows]))
    scores = {name: score_closes(scored_closes, name, regime_key) for name in names}

    shadow_signals: Dict[str, List[Signal]] = {name: [] for name in names}
    errors: Dict[str, str] = {}
    tradable = [symbol for symbol in market_data if not str(symbol).startswith("_regime_")]

    for strategy in shadows:
        if strategy.name in errors:
            continue
        for symbol in tradable:
            data = market_data[symbol]
            try:
                if not getattr(data, "symbol", None):
                    data.symbol = symbol
            except Exception:
                pass
            try:
                found = strategy.generate_signals(data, account, positions) or []
            except Exception as exc:
                errors[strategy.name] = str(exc)
                break
            for signal in found:
                if signal.metadata is None:
                    signal.metadata = {}
                signal.metadata.setdefault("strategy", strategy.name)
                shadow_signals.setdefault(strategy.name, []).append(signal)

    live_by_symbol: Dict[str, List[Signal]] = {}
    for signal in live_signals:
        live_by_symbol.setdefault(signal.symbol, []).append(signal)

    kept: List[Signal] = []
    orders = []
    stood_down = []
    shadow_winners = []
    fired = {name: 0 for name in names}
    skipped = {name: 0 for name in names}

    for symbol in tradable:
        live = live_by_symbol.get(symbol, [])
        symbol_shadows = []
        for name, signals in shadow_signals.items():
            symbol_shadows.extend(signal for signal in signals if signal.symbol == symbol)
        present = set()
        for signal in live + symbol_shadows:
            name = (signal.metadata or {}).get("strategy")
            if name:
                present.add(name)
                fired[name] = fired.get(name, 0) + 1
        for name in names:
            if name not in present:
                skipped[name] = skipped.get(name, 0) + 1

        kept.extend(signal for signal in live if signal.signal_type != SignalType.BUY)
        choice = choose_buy(live, scores, min_closes)
        kept.extend(choice["signals"])
        if choice["reason"] == "scored" and choice["signals"]:
            orders.append({
                "symbol": symbol,
                "strategy": choice["strategy"],
                "expectancy": choice["score"]["expectancy"],
                "closes": choice["score"]["closes"],
                "hit_rate": choice["score"]["hit_rate"],
            })
        elif choice["reason"] == "stood_down":
            stood_down.append({"symbol": symbol, "strategy": choice["strategy"]})

        winner = _shadow_winner(symbol_shadows, scores, min_closes)
        if winner and winner["strategy"] not in book_names:
            shadow_winners.append({"symbol": symbol, **winner})

    by_strategy = {}
    for name in names:
        score = scores.get(name)
        by_strategy[name] = {
            "signals": fired.get(name, 0),
            "skips": skipped.get(name, 0),
            "error": errors.get(name),
            "closes": None if not score else score["closes"],
            "expectancy": None if not score else score["expectancy"],
            "hit_rate": None if not score else score["hit_rate"],
            "profit_factor": None if not score else score["profit_factor"],
            "on_book": name in book_names,
        }

    journal = {
        "regime": regime_key,
        "min_closes": min_closes,
        "symbols": len(tradable),
        "orders": orders,
        "stood_down": stood_down,
        "shadow_winners": shadow_winners,
        "by_strategy": by_strategy,
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    return kept, journal


def _shadow_winner(signals: List[Signal], scores: Dict[str, Optional[Dict[str, Any]]], min_closes: int) -> Optional[Dict[str, Any]]:
    choice = choose_buy(signals, scores, min_closes)
    if choice["reason"] != "scored":
        return None
    score = choice["score"]
    return {
        "strategy": choice["strategy"],
        "expectancy": score["expectancy"],
        "closes": score["closes"],
        "hit_rate": score["hit_rate"],
    }
