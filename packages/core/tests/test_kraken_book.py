"""Kraken book rules: curated-list refresh, short trailing stops, saved targets."""

from quantshift_core.position_tracker import PositionTracker
from quantshift_core.symbol_universe import refresh_curated_symbols


def test_refresh_drops_delisted_and_thin_names_and_ranks_the_rest():
    selected = refresh_curated_symbols(
        ["XBTUSD", "GONEUSD", "THINUSD", "ETHUSD"],
        {"XBTUSD": 1_000_000, "THINUSD": 10, "ETHUSD": 5_000_000},
        max_symbols=2,
        min_volume=1_000_000,
        listed={"XBTUSD", "THINUSD", "ETHUSD"},
    )
    assert selected == ["ETHUSD", "XBTUSD"]


def test_refresh_keeps_curated_order_when_volume_is_unknown():
    selected = refresh_curated_symbols(
        ["SOLUSD", "ADAUSD", "XBTUSD"],
        {},
        max_symbols=2,
        min_volume=1_000_000,
        listed=None,
    )
    assert selected == ["SOLUSD", "ADAUSD"]


def test_short_trail_arms_when_price_falls_and_tightens_downward():
    tracker = PositionTracker(
        symbol="SOLUSD",
        bot_name="quantshift-kraken",
        entry_price=100,
        current_price=100,
        quantity=1,
        original_stop_loss=110,
        current_stop_loss=110,
        high_water_mark=100,
        side="short",
    )
    tracker.update_price(97)
    assert tracker.high_water_mark == 97
    assert tracker.should_activate_trailing_stop(0.015)
    stop = tracker.calculate_trailing_stop_price(2.0, atr=1.0, min_trail_distance_pct=0.008)
    assert stop > 97
    assert tracker.should_update_stop(stop, only_improve=True)
    assert not tracker.should_update_stop(111, only_improve=True)


def test_long_trail_still_moves_up():
    tracker = PositionTracker(
        symbol="SOLUSD",
        bot_name="quantshift-kraken",
        entry_price=100,
        current_price=100,
        quantity=1,
        original_stop_loss=90,
        current_stop_loss=90,
        high_water_mark=100,
        side="long",
    )
    tracker.update_price(103)
    assert tracker.should_activate_trailing_stop(0.015)
    stop = tracker.calculate_trailing_stop_price(2.0, atr=1.0, min_trail_distance_pct=0.008)
    assert stop < 103
    assert tracker.should_update_stop(stop, only_improve=True)
