"""The learner studies held names first and does not retune risk."""

from quantshift_core.strategy_learner import lesson_is_better, symbol_pool, tunable_ranges


def test_held_names_are_studied_before_the_qualified_list():
    pool = symbol_pool(["JPM", "BA"], ["AAPL", "JPM", "SPY"])
    assert pool[:2] == ["JPM", "BA"]
    assert pool[2:] == ["AAPL", "SPY"]


def test_risk_is_not_a_searched_setting():
    ranges = tunable_ranges({
        "rsi_period": 14,
        "atr_sl_multiplier": 2.0,
        "risk_per_trade": 0.015,
        "volume_confirmation": True,
        "max_positions": 10,
    })
    assert "risk_per_trade" not in ranges
    assert "volume_confirmation" not in ranges
    assert set(ranges) == {"rsi_period", "atr_sl_multiplier"}
    assert 14 in ranges["rsi_period"]


def test_a_lesson_must_beat_the_current_settings():
    current = {"sharpe": 0.4, "max_drawdown": 0.10, "num_trades": 4}
    assert lesson_is_better(current, {"sharpe": 0.8, "max_drawdown": 0.12, "num_trades": 4})
    assert not lesson_is_better(current, {"sharpe": 0.3, "max_drawdown": 0.05, "num_trades": 4})
    assert not lesson_is_better(current, {"sharpe": 1.2, "max_drawdown": 0.40, "num_trades": 4})
    assert not lesson_is_better(current, {"sharpe": 1.2, "max_drawdown": 0.05, "num_trades": 0})
