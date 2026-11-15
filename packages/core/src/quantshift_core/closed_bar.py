"""Closed daily bars for equity decisions.

Alpaca's daily request includes the session that is still printing. A strategy
that reads the last row then sees that day's low and high at the same time, and
a one-minute cycle can buy and sell the same candle. Equity entries and exits
use the last bar that has finished, and each symbol is traded once on that bar.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd

DAILY_BAR = timedelta(days=1)


def as_utc(value: datetime) -> datetime:
    """Normalize a bar or fill timestamp to UTC."""
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def forming_daily_bar(
    bar_open: datetime,
    now: datetime,
    bar_length: timedelta = DAILY_BAR,
) -> bool:
    """True when this daily bar has opened and has not finished."""
    start = as_utc(bar_open)
    clock = as_utc(now)
    return start <= clock < start + bar_length


def closed_bar_already_traded(
    last_fill: Optional[datetime],
    bar_open: datetime,
    bar_length: timedelta = DAILY_BAR,
) -> bool:
    """True when a fill already happened after this daily bar finished.

    A fill during the bar belongs to the previous completed signal. A fill
    after the bar closes is the trade that consumed this signal.
    """
    if last_fill is None:
        return False
    return as_utc(last_fill) >= as_utc(bar_open) + bar_length


def without_forming_daily_bar(frame: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """Drop the daily bar that contains `now`. A finished bar stays."""
    if frame is None or len(frame) == 0:
        return frame
    last = frame.index[-1]
    opened = last.to_pydatetime() if hasattr(last, "to_pydatetime") else last
    if forming_daily_bar(opened, now):
        return frame.iloc[:-1]
    return frame
