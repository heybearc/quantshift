"""Learn strategy settings from history the bot is already allowed to trade.

A lesson uses one strategy and one symbol. Held names come first, then the
qualified universe, so the book is studied before names the bot has not
bought. Risk per trade is never searched. A lesson is kept only when the
later part of the history beats the settings the bot is using now.
"""

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


_LOCKED = {"risk_per_trade", "max_positions"}
_PREFERRED = ("period", "window", "threshold", "multiplier", "std")


def symbol_pool(held: Sequence[str], universe: Sequence[str]) -> List[str]:
    """Held symbols first, then qualified names that are not already held."""
    pool: List[str] = []
    for symbol in list(held) + list(universe):
        if symbol and symbol not in pool:
            pool.append(symbol)
    return pool


def tunable_ranges(params: Dict[str, Any], limit: int = 2) -> Dict[str, List[Any]]:
    """A few neighboring values around the live settings. Risk stays fixed."""
    ranked: List[Tuple[int, str, Any]] = []
    for key, value in params.items():
        if key in _LOCKED or isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        score = sum(1 for token in _PREFERRED if token in key)
        ranked.append((score, key, value))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    ranges: Dict[str, List[Any]] = {}
    for _, key, value in ranked[:limit]:
        ranges[key] = _neighbors(key, value)
    return ranges


def smooth_allocation(base: Dict[str, float], learned: Dict[str, float], keep: float = 0.5) -> Dict[str, float]:
    """Keep half of a fresh regime allocation and half of what the exams have learned."""
    names = list(dict.fromkeys(list(base) + list(learned)))
    mixed = {
        name: keep * float(base.get(name) or 0) + (1 - keep) * float(learned.get(name) or 0)
        for name in names
    }
    total = sum(mixed.values()) or 1.0
    return {name: weight / total for name, weight in mixed.items()}


def blend_allocation(
    allocation: Dict[str, float],
    scores: Dict[str, Optional[float]],
    floor: float = 0.08,
    cap: float = 0.30,
    step: float = 0.04,
) -> Dict[str, float]:
    """Move a small slice of capital from the weakest scored strategy to the strongest.

    One symbol cannot take the whole book. A strategy stays between the floor
    and the cap, and equal scores leave the allocation unchanged.
    """
    names = [name for name in allocation if name]
    if not names:
        return {}
    weights = {name: max(float(allocation.get(name) or 0), 0.0) for name in names}
    total = sum(weights.values()) or 1.0
    weights = {name: weight / total for name, weight in weights.items()}
    known = {
        name: float(scores[name])
        for name in names
        if isinstance(scores.get(name), (int, float))
    }
    if len(known) < 2 or len(set(known.values())) < 2:
        return weights
    ranked = sorted(known, key=lambda name: known[name], reverse=True)
    best, worst = ranked[0], ranked[-1]
    move = min(step, weights[worst] - floor, cap - weights[best])
    if move > 0:
        weights[best] += move
        weights[worst] -= move
    return weights


def lesson_is_better(current: Optional[Dict[str, float]], candidate: Optional[Dict[str, float]]) -> bool:
    """True when the candidate held up on the later history better than today."""
    if not candidate or candidate.get("num_trades", 0) < 1:
        return False
    if candidate.get("max_drawdown", 1) > 0.30:
        return False
    current_sharpe = -1.0 if not current else float(current.get("sharpe", -1.0))
    current_drawdown = 1.0 if not current else float(current.get("max_drawdown", 1.0))
    if float(candidate.get("sharpe", -1.0)) <= current_sharpe:
        return False
    if float(candidate.get("max_drawdown", 1.0)) > current_drawdown + 0.05:
        return False
    return True


def exam_settings(strategy_class, base_params: Dict[str, Any], market_data, starting_capital: float) -> Optional[Dict[str, float]]:
    """Score the live settings on the recent history. This is the strategy comparison."""
    if market_data is None or len(market_data) < 80:
        return None
    from .backtesting import run_strategy_backtest

    window = market_data.iloc[-120:].copy()
    symbol = getattr(market_data, "symbol", None)
    if symbol and not getattr(window, "symbol", None):
        try:
            window.symbol = symbol
        except Exception:
            pass
    try:
        strategy = strategy_class(config=dict(base_params))
    except Exception:
        return None
    return run_strategy_backtest(strategy, window, starting_capital)


def learn_settings(
    strategy_class,
    base_params: Dict[str, Any],
    market_data,
    starting_capital: float,
) -> Optional[Dict[str, Any]]:
    """Return the merged settings to adopt, or None when the lesson is no better."""
    if market_data is None or len(market_data) < 80:
        return None
    ranges = tunable_ranges(base_params)
    if not ranges:
        return None

    from .parameter_optimizer import ParameterOptimizer

    optimizer = ParameterOptimizer(min_trades=1)
    bound = _bind(strategy_class, base_params)
    train, test = optimizer._split_data(market_data)
    if train.empty or test.empty:
        return None
    current = optimizer._backtest_parameters(strategy_class, dict(base_params), test, starting_capital)
    found = optimizer.optimize_parameters(
        strategy_class=bound,
        parameter_ranges=ranges,
        market_data=market_data,
        initial_capital=starting_capital,
        validate=False,
    )
    if not found or not lesson_is_better(current, found.get("test_metrics")):
        return None
    merged = dict(base_params)
    merged.update(found["optimal_params"])
    for key in _LOCKED:
        if key in base_params:
            merged[key] = base_params[key]
    return {
        "params": merged,
        "tuned": found["optimal_params"],
        "test_metrics": found["test_metrics"],
        "current_metrics": current,
    }


def _neighbors(key: str, value: float) -> List[Any]:
    number = float(value)
    if isinstance(value, int) or number >= 2:
        step = max(1, int(round(abs(number) * 0.2)))
        raw = [number - step, number, number + step]
        values = sorted({int(round(item)) if isinstance(value, int) else round(item, 4) for item in raw})
    else:
        values = sorted({round(number * factor, 4) for factor in (0.8, 1.0, 1.2)})
    kept = [item for item in values if item > 0]
    if isinstance(value, int):
        return [int(item) for item in kept]
    return kept


def _bind(strategy_class, base_params: Dict[str, Any]):
    """Grid search only varies a few keys. The rest stay at the live settings."""

    class Bound(strategy_class):
        def __init__(self, config=None):
            merged = dict(base_params)
            merged.update(config or {})
            super().__init__(config=merged)

    Bound.__name__ = strategy_class.__name__
    return Bound
