"""A personal desk records bots and symbols without joining the house book."""

from quantshift_core.user_book import (
    normalize_symbol,
    ordered_symbols,
    personal_bot_set,
    suggestion_can_trade,
    symbols_for_book,
)


def test_personal_mode_records_a_stopped_paper_bot_per_venue():
    venues = [bot["venue"] for bot in personal_bot_set()]
    assert venues == ["alpaca", "coinbase", "kraken"]
    assert all(bot["status"] == "stopped" and bot["trading_mode"] == "paper" for bot in personal_bot_set())


def test_trade_marks_lead_and_the_house_universe_stays_put():
    marks = [
        {"symbol": "msft", "intent": "research"},
        {"symbol": "NVDA", "intent": "trade"},
        {"symbol": "nvda", "intent": "trade"},
        {"symbol": "not a symbol", "intent": "trade"},
    ]
    assert ordered_symbols(marks) == ["NVDA", "MSFT"]
    assert symbols_for_book("personal", ["SPY"], marks) == ["NVDA"]
    assert symbols_for_book("house", ["SPY", "qqq"], marks) == ["SPY", "QQQ"]
    assert normalize_symbol("btc-usd") == "BTC-USD"


def test_a_suggestion_cannot_trade():
    assert suggestion_can_trade("suggestion") is False
    assert suggestion_can_trade("in_catalog") is False
