"""Equity exits stay inside the shares already held."""

from quantshift_core.equity_exits import (
    add_stop,
    broker_side,
    exit_instruction,
    signed_quantity,
    stop_for_position,
)


def test_alpaca_short_is_not_labeled_long_when_qty_is_positive():
    assert broker_side(5, "short") == "short"
    assert signed_quantity(5, "short") == -5
    assert signed_quantity(5, "long") == 5


def test_sell_while_flat_does_not_open_a_short():
    assert exit_instruction(None, 0, 10) is None


def test_sell_cannot_exceed_the_long():
    order = exit_instruction("long", 5, 12)
    assert order == {"side": "sell", "qty": 5}


def test_sell_of_a_short_buys_to_cover():
    order = exit_instruction("short", -4, 4)
    assert order == {"side": "buy", "qty": 4}


def test_protective_stop_matches_the_position_side():
    book = {}
    add_stop(book, "AAPL", "sell", 90)
    add_stop(book, "AAPL", "sell", 95)
    add_stop(book, "AAPL", "buy", 110)
    assert stop_for_position(book, "AAPL", "long") == 95
    assert stop_for_position(book, "AAPL", "short") == 110
