"""Equity exits stay inside the shares already held."""

from quantshift_core.drawdown import drawdown_percent
from quantshift_core.equity_exits import (
    add_stop,
    broker_side,
    exit_instruction,
    order_is_working,
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


def test_a_held_order_is_still_working_and_a_canceled_order_is_not():
    assert order_is_working("held")
    assert order_is_working("new")
    assert order_is_working(None)
    assert not order_is_working("canceled")
    assert not order_is_working("filled")


def test_drawdown_uses_account_capital_instead_of_the_profit_peak():
    # An $8 peak and a later $19 loss is 237% of that peak, and 0.19% of a $10,000 account.
    assert drawdown_percent(8, -11, 10000) < 1
    assert round(drawdown_percent(8, -11, 10000), 2) == 0.19
    assert drawdown_percent(18.71, 18.71, 10000) == 0


def test_protective_stop_matches_the_position_side():
    book = {}
    add_stop(book, "AAPL", "sell", 90)
    add_stop(book, "AAPL", "sell", 95)
    add_stop(book, "AAPL", "buy", 110)
    assert stop_for_position(book, "AAPL", "long") == 95
    assert stop_for_position(book, "AAPL", "short") == 110
