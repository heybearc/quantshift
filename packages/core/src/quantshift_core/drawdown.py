"""Account drawdown from a cumulative P&L path.

A decline measured against the profit peak explodes once that peak is small
and a later loss takes cumulative P&L below zero. Drawdown here is the
peak-to-trough decline of account equity: starting capital plus closed P&L.
"""

from typing import Sequence


def drawdown_percent(peak_pnl: float, current_pnl: float, starting_capital: float) -> float:
    """Decline from the P&L high, as a percent of account equity. Zero at a new high."""
    if starting_capital <= 0:
        return 0.0
    peak_equity = starting_capital + float(peak_pnl)
    equity = starting_capital + float(current_pnl)
    if peak_equity <= 0 or equity >= peak_equity:
        return 0.0
    return (peak_equity - equity) / peak_equity * 100


def path_drawdown(pnls: Sequence[float], starting_capital: float) -> tuple:
    """Max and current drawdown, in percent, walking closed trades in order."""
    if starting_capital <= 0:
        return 0.0, 0.0
    cumulative = 0.0
    peak = 0.0
    worst = 0.0
    for pnl in pnls:
        cumulative += float(pnl)
        if cumulative > peak:
            peak = cumulative
        decline = drawdown_percent(peak, cumulative, starting_capital)
        if decline > worst:
            worst = decline
    current = drawdown_percent(peak, cumulative, starting_capital)
    return worst, current
