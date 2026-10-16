"""Candle window helpers shared by paper executors."""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd


class AttachedFrame:
    """A second timeframe hung on a candle frame.

    Pandas compares ``attrs`` while it joins columns. A raw frame in that
    dictionary makes the comparison blow up, so the extra bars sit behind
    an equality check that returns a plain true or false.
    """

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AttachedFrame) and self.frame is other.frame


def drop_forming_candle(frame: pd.DataFrame, bar_seconds: int, now: Optional[datetime] = None) -> pd.DataFrame:
    """Remove the last row when that bar has not closed yet.

    Strategies read the last row as a finished signal. An hourly bar that is
    still printing will change every minute and can enter and exit the same name
    before the hour is over.
    """
    if frame is None or len(frame) == 0 or bar_seconds <= 0:
        return frame
    last = frame.index[-1]
    opened = last.to_pydatetime() if hasattr(last, "to_pydatetime") else last
    if getattr(opened, "tzinfo", None) is not None:
        opened = opened.replace(tzinfo=None)
    clock = now or datetime.utcnow()
    if getattr(clock, "tzinfo", None) is not None:
        clock = clock.replace(tzinfo=None)
    if opened + timedelta(seconds=bar_seconds) > clock:
        return frame.iloc[:-1]
    return frame
