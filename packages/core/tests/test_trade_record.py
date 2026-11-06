"""Closing fills update the open trade. New entries do not."""

from quantshift_core.trade_record import is_closing_fill


def test_a_sell_with_realized_pnl_closes_the_trade():
    assert is_closing_fill({"symbol": "BTC-USD", "side": "SELL", "realized_pnl": 1.25})


def test_an_explicit_close_counts_even_when_the_pnl_is_a_scratch():
    assert is_closing_fill({"symbol": "AAPL", "closing": True, "realized_pnl": 0.0})


def test_a_new_buy_stays_an_open_trade():
    assert not is_closing_fill({"symbol": "AAPL", "side": "BUY", "fill_price": 10})


def test_a_new_short_is_not_a_close():
    assert not is_closing_fill({"symbol": "XBTUSD", "side": "SELL", "closing": False})
