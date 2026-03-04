"""
Position Limits - Hard-Coded Risk Management

This module enforces hard position limits to protect capital.
These limits are CODE-ENFORCED and cannot be overridden by configuration.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PositionLimitViolation:
    """Represents a position limit violation."""
    limit_type: str
    current_value: float
    limit_value: float
    message: str
    severity: str  # 'warning' or 'critical'


class PositionLimits:
    """
    Hard-coded position limits for risk management.
    
    These limits are CODE-ENFORCED and cannot be changed via configuration.
    To change these limits, you must modify this source code and deploy.
    
    This is intentional - it prevents accidental or malicious configuration
    changes from exposing the account to excessive risk.
    """
    
    # HARD LIMITS - DO NOT CHANGE WITHOUT CAREFUL CONSIDERATION
    MAX_POSITION_PCT = 0.10  # 10% max per position
    MAX_POSITIONS = 5  # Max 5 positions total
    MAX_DAILY_LOSS_PCT = 0.03  # 3% daily loss limit
    MAX_TOTAL_RISK_PCT = 0.15  # 15% total portfolio risk
    MIN_POSITION_VALUE = 100.0  # Minimum $100 per position
    MAX_POSITION_VALUE = 50000.0  # Maximum $50,000 per position
    
    def __init__(self):
        """Initialize position limits tracker."""
        self._daily_loss = 0.0
        self._last_reset_date = date.today()
        self._circuit_breaker_open = False
        
        logger.info(
            "position_limits_initialized",
            max_position_pct=self.MAX_POSITION_PCT,
            max_positions=self.MAX_POSITIONS,
            max_daily_loss_pct=self.MAX_DAILY_LOSS_PCT,
            max_total_risk_pct=self.MAX_TOTAL_RISK_PCT,
            min_position_value=self.MIN_POSITION_VALUE,
            max_position_value=self.MAX_POSITION_VALUE
        )
    
    def reset_daily_limits(self) -> None:
        """Reset daily limits (called at start of each trading day)."""
        today = date.today()
        if today > self._last_reset_date:
            self._daily_loss = 0.0
            self._last_reset_date = today
            self._circuit_breaker_open = False
            logger.info("daily_limits_reset", date=today.isoformat())
    
    def record_trade_pnl(self, pnl: float) -> None:
        """
        Record P&L from a closed trade.
        
        Args:
            pnl: Profit/loss from the trade (negative for losses)
        """
        self.reset_daily_limits()  # Auto-reset if new day
        
        if pnl < 0:
            self._daily_loss += abs(pnl)
            logger.info(
                "daily_loss_updated",
                trade_loss=pnl,
                total_daily_loss=self._daily_loss
            )
    
    def validate_new_position(
        self,
        position_value: float,
        portfolio_value: float,
        current_positions: int,
        total_risk: float
    ) -> Optional[PositionLimitViolation]:
        """
        Validate a new position against all limits.
        
        Args:
            position_value: Dollar value of proposed position
            portfolio_value: Total portfolio value
            current_positions: Number of currently open positions
            total_risk: Total portfolio risk (sum of all position risks)
            
        Returns:
            PositionLimitViolation if any limit is violated, None otherwise
        """
        self.reset_daily_limits()  # Auto-reset if new day
        
        # Check circuit breaker
        if self._circuit_breaker_open:
            return PositionLimitViolation(
                limit_type="circuit_breaker",
                current_value=self._daily_loss,
                limit_value=portfolio_value * self.MAX_DAILY_LOSS_PCT,
                message="Circuit breaker open - daily loss limit reached",
                severity="critical"
            )
        
        # Check minimum position value
        if position_value < self.MIN_POSITION_VALUE:
            return PositionLimitViolation(
                limit_type="min_position_value",
                current_value=position_value,
                limit_value=self.MIN_POSITION_VALUE,
                message=f"Position value ${position_value:.2f} below minimum ${self.MIN_POSITION_VALUE:.2f}",
                severity="warning"
            )
        
        # Check maximum position value
        if position_value > self.MAX_POSITION_VALUE:
            return PositionLimitViolation(
                limit_type="max_position_value",
                current_value=position_value,
                limit_value=self.MAX_POSITION_VALUE,
                message=f"Position value ${position_value:.2f} exceeds maximum ${self.MAX_POSITION_VALUE:.2f}",
                severity="critical"
            )
        
        # Check position size as percentage of portfolio
        position_pct = position_value / portfolio_value if portfolio_value > 0 else 0
        if position_pct > self.MAX_POSITION_PCT:
            return PositionLimitViolation(
                limit_type="max_position_pct",
                current_value=position_pct,
                limit_value=self.MAX_POSITION_PCT,
                message=f"Position size {position_pct*100:.1f}% exceeds limit {self.MAX_POSITION_PCT*100:.1f}%",
                severity="critical"
            )
        
        # Check maximum number of positions
        if current_positions >= self.MAX_POSITIONS:
            return PositionLimitViolation(
                limit_type="max_positions",
                current_value=current_positions,
                limit_value=self.MAX_POSITIONS,
                message=f"Already at maximum {self.MAX_POSITIONS} positions",
                severity="critical"
            )
        
        # Check total portfolio risk
        total_risk_pct = total_risk / portfolio_value if portfolio_value > 0 else 0
        if total_risk_pct > self.MAX_TOTAL_RISK_PCT:
            return PositionLimitViolation(
                limit_type="max_total_risk",
                current_value=total_risk_pct,
                limit_value=self.MAX_TOTAL_RISK_PCT,
                message=f"Total portfolio risk {total_risk_pct*100:.1f}% exceeds limit {self.MAX_TOTAL_RISK_PCT*100:.1f}%",
                severity="critical"
            )
        
        # Check daily loss limit
        daily_loss_pct = self._daily_loss / portfolio_value if portfolio_value > 0 else 0
        if daily_loss_pct >= self.MAX_DAILY_LOSS_PCT:
            self._circuit_breaker_open = True
            logger.critical(
                "circuit_breaker_triggered",
                daily_loss=self._daily_loss,
                daily_loss_pct=daily_loss_pct,
                limit_pct=self.MAX_DAILY_LOSS_PCT
            )
            return PositionLimitViolation(
                limit_type="daily_loss_limit",
                current_value=daily_loss_pct,
                limit_value=self.MAX_DAILY_LOSS_PCT,
                message=f"Daily loss {daily_loss_pct*100:.1f}% reached limit {self.MAX_DAILY_LOSS_PCT*100:.1f}% - circuit breaker triggered",
                severity="critical"
            )
        
        # All checks passed
        return None
    
    def get_status(self, portfolio_value: float) -> Dict[str, Any]:
        """
        Get current status of all limits.
        
        Args:
            portfolio_value: Total portfolio value
            
        Returns:
            Dictionary with current status of all limits
        """
        self.reset_daily_limits()  # Auto-reset if new day
        
        daily_loss_pct = self._daily_loss / portfolio_value if portfolio_value > 0 else 0
        
        return {
            'circuit_breaker_open': self._circuit_breaker_open,
            'daily_loss': self._daily_loss,
            'daily_loss_pct': daily_loss_pct,
            'daily_loss_limit_pct': self.MAX_DAILY_LOSS_PCT,
            'daily_loss_remaining': max(0, portfolio_value * self.MAX_DAILY_LOSS_PCT - self._daily_loss),
            'last_reset_date': self._last_reset_date.isoformat(),
            'limits': {
                'max_position_pct': self.MAX_POSITION_PCT,
                'max_positions': self.MAX_POSITIONS,
                'max_daily_loss_pct': self.MAX_DAILY_LOSS_PCT,
                'max_total_risk_pct': self.MAX_TOTAL_RISK_PCT,
                'min_position_value': self.MIN_POSITION_VALUE,
                'max_position_value': self.MAX_POSITION_VALUE
            }
        }
