"""Equity decisions use a finished daily bar, once."""

from datetime import datetime, timedelta, timezone

import pandas as pd

from quantshift_core.closed_bar import (
    closed_bar_already_traded,
    forming_daily_bar,
    without_forming_daily_bar,
)


def _utc(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 11, day, hour, tzinfo=timezone.utc)


def test_the_session_bar_is_still_forming_until_it_ends():
    opened = _utc(12)
    assert forming_daily_bar(opened, _utc(12, 15))
    assert not forming_daily_bar(opened, _utc(13, 1))


def test_a_forming_daily_bar_is_removed_and_a_finished_bar_stays():
    index = pd.to_datetime(["2026-11-11", "2026-11-12"], utc=True)
    frame = pd.DataFrame({"close": [100.0, 101.0]}, index=index)

    closed = without_forming_daily_bar(frame, _utc(12, 15))
    assert list(closed.index) == [index[0]]

    kept = without_forming_daily_bar(frame, _utc(13, 10))
    assert len(kept) == 2


def test_weekend_keeps_the_last_finished_session():
    index = pd.to_datetime(["2026-11-13"], utc=True)
    frame = pd.DataFrame({"close": [100.0]}, index=index)
    sunday = datetime(2026, 11, 15, 15, tzinfo=timezone.utc)
    assert len(without_forming_daily_bar(frame, sunday)) == 1


def test_a_fill_after_the_bar_closes_consumes_that_signal():
    wednesday = _utc(11)
    assert not closed_bar_already_traded(None, wednesday)
    assert not closed_bar_already_traded(_utc(11, 15), wednesday)
    assert closed_bar_already_traded(_utc(12, 14), wednesday)


def test_an_older_fill_does_not_consume_the_new_closed_bar():
    wednesday = _utc(11)
    monday_fill = wednesday - timedelta(days=2)
    assert not closed_bar_already_traded(monday_fill, wednesday)
