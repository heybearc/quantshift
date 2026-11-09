"""A latched daily-loss breaker clears on a new day and when the book recovers."""

from datetime import date

from quantshift_core.risk_manager import CircuitBreakerStatus, RiskManager


def test_new_day_clears_a_latched_daily_loss_breaker():
    risk = RiskManager()
    risk.current_date = date(2026, 11, 6)
    risk.daily_start_equity = 5684.0
    risk.peak_equity = 5684.0
    risk.circuit_breaker_status = CircuitBreakerStatus.TRIGGERED
    risk.circuit_breaker_reason = "Daily loss 12.0% exceeds limit 5.0%"

    status = risk.check_circuit_breakers(5002.63, date(2026, 11, 9))

    assert status == CircuitBreakerStatus.NORMAL
    assert risk.circuit_breaker_reason is None
    assert risk.daily_start_equity == 5002.63


def test_stale_latch_clears_when_the_book_is_inside_the_limit():
    risk = RiskManager()
    risk.current_date = date(2026, 11, 9)
    risk.daily_start_equity = 5002.63
    risk.peak_equity = 5002.63
    risk.circuit_breaker_status = CircuitBreakerStatus.TRIGGERED
    risk.circuit_breaker_reason = "Daily loss 12.0% exceeds limit 5.0%"

    status = risk.check_circuit_breakers(5002.63, date(2026, 11, 9))

    assert status == CircuitBreakerStatus.NORMAL
    assert risk.circuit_breaker_reason is None


def test_a_real_daily_loss_still_blocks_the_signal():
    risk = RiskManager()
    risk.current_date = date(2026, 11, 9)
    risk.daily_start_equity = 5000.0
    risk.peak_equity = 5000.0

    status = risk.check_circuit_breakers(4700.0, date(2026, 11, 9))

    assert status == CircuitBreakerStatus.TRIGGERED
    assert risk.circuit_breaker_reason is not None
    assert "Daily loss" in risk.circuit_breaker_reason
