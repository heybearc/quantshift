"""
Risk Manager - Portfolio-Level Risk Controls

Implements institutional-grade risk management:
- Portfolio heat tracking (total risk exposure)
- Correlation monitoring between positions
- Sector/concentration limits
- Circuit breakers (daily loss, max drawdown)
- Position size validation
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from enum import Enum
import pandas as pd
import numpy as np
import structlog

from .strategies.base_strategy import Signal, Position, Account

logger = structlog.get_logger()


class CircuitBreakerStatus(Enum):
    """Circuit breaker status."""
    NORMAL = "normal"
    WARNING = "warning"
    TRIGGERED = "triggered"


class RiskManager:
    """
    Portfolio-level risk management system.
    
    Responsibilities:
    - Track total portfolio risk exposure (heat)
    - Monitor correlation between positions
    - Enforce sector/concentration limits
    - Implement circuit breakers
    - Validate signals against risk limits
    """
    
    def __init__(
        self,
        max_portfolio_heat: float = 0.10,  # 10% max total risk
        max_position_correlation: float = 0.7,  # Block if correlation > 0.7
        max_sector_exposure: float = 0.30,  # 30% max per sector
        daily_loss_limit: float = 0.05,  # 5% daily loss limit
        max_drawdown_limit: float = 0.15,  # 15% max drawdown
        warning_threshold: float = 0.8  # Warn at 80% of limits
    ):
        """
        Initialize risk manager.
        
        Args:
            max_portfolio_heat: Maximum total portfolio risk (0-1)
            max_position_correlation: Maximum correlation between positions
            max_sector_exposure: Maximum exposure to any sector (0-1)
            daily_loss_limit: Maximum daily loss as fraction of starting equity
            max_drawdown_limit: Maximum drawdown from peak equity
            warning_threshold: Warn when approaching limits (0-1)
        """
        self.max_portfolio_heat = max_portfolio_heat
        self.max_position_correlation = max_position_correlation
        self.max_sector_exposure = max_sector_exposure
        self.daily_loss_limit = daily_loss_limit
        self.max_drawdown_limit = max_drawdown_limit
        self.warning_threshold = warning_threshold
        
        # State tracking
        self.daily_start_equity = None
        self.peak_equity = None
        self.current_date = None
        self.circuit_breaker_status = CircuitBreakerStatus.NORMAL
        self.circuit_breaker_reason = None
        
        self.logger = logger.bind(component="RiskManager")
        
        self.logger.info(
            "risk_manager_initialized",
            max_portfolio_heat=max_portfolio_heat,
            max_correlation=max_position_correlation,
            daily_loss_limit=daily_loss_limit,
            max_drawdown=max_drawdown_limit
        )
    
    def calculate_portfolio_heat(
        self,
        positions: List[Position],
        pending_signals: Optional[List[Signal]] = None
    ) -> float:
        """
        Calculate total portfolio risk exposure (heat).
        
        Heat = sum of all position risks / account equity
        Position risk = (entry_price - stop_loss) * quantity
        
        Args:
            positions: Current open positions
            pending_signals: Signals being evaluated (optional)
            
        Returns:
            Portfolio heat as fraction of equity (0-1)
        """
        total_risk = 0.0
        
        # Calculate risk from existing positions
        for pos in positions:
            if hasattr(pos, 'stop_loss') and pos.stop_loss:
                risk = abs(pos.entry_price - pos.stop_loss) * pos.quantity
                total_risk += risk
        
        # Add risk from pending signals
        if pending_signals:
            for signal in pending_signals:
                if signal.stop_loss and signal.position_size:
                    risk = abs(signal.price - signal.stop_loss) * signal.position_size
                    total_risk += risk
        
        # Calculate heat (assume we have access to equity somehow)
        # This will be passed in from the calling context
        return total_risk
    
    def calculate_position_correlation(
        self,
        positions: List[Position],
        new_symbol: str,
        market_data: Dict[str, pd.DataFrame],
        lookback_days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate correlation between new symbol and existing positions.
        
        Args:
            positions: Current open positions
            new_symbol: Symbol being considered for new position
            market_data: Historical price data for all symbols
            lookback_days: Days to use for correlation calculation
            
        Returns:
            Dict mapping existing symbol to correlation with new symbol
        """
        if new_symbol not in market_data:
            return {}
        
        correlations = {}
        new_returns = market_data[new_symbol]['Close'].pct_change().tail(lookback_days)
        
        for pos in positions:
            if pos.symbol in market_data and pos.symbol != new_symbol:
                existing_returns = market_data[pos.symbol]['Close'].pct_change().tail(lookback_days)
                
                # Calculate correlation
                correlation = new_returns.corr(existing_returns)
                if not np.isnan(correlation):
                    correlations[pos.symbol] = correlation
        
        return correlations
    
    def check_sector_exposure(
        self,
        positions: List[Position],
        new_symbol: str,
        new_value: float,
        account_equity: float,
        sector_map: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if adding new position would exceed sector exposure limits.
        
        Args:
            positions: Current open positions
            new_symbol: Symbol being considered
            new_value: Value of new position
            account_equity: Current account equity
            sector_map: Dict mapping symbol to sector
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        if sector_map is None:
            # Default sector mapping for common symbols
            sector_map = {
                'SPY': 'Equity Index',
                'QQQ': 'Tech Index',
                'AAPL': 'Technology',
                'MSFT': 'Technology',
                'GOOGL': 'Technology',
                'AMZN': 'Consumer',
                'TSLA': 'Automotive',
                'NVDA': 'Technology'
            }
        
        # Get sector for new symbol
        new_sector = sector_map.get(new_symbol, 'Unknown')
        
        # Calculate current exposure by sector
        sector_exposure = {}
        for pos in positions:
            sector = sector_map.get(pos.symbol, 'Unknown')
            value = pos.entry_price * pos.quantity
            sector_exposure[sector] = sector_exposure.get(sector, 0) + value
        
        # Add new position
        sector_exposure[new_sector] = sector_exposure.get(new_sector, 0) + new_value
        
        # Check if any sector exceeds limit
        for sector, value in sector_exposure.items():
            exposure_pct = value / account_equity
            if exposure_pct > self.max_sector_exposure:
                return False, f"Sector {sector} exposure {exposure_pct:.1%} exceeds limit {self.max_sector_exposure:.1%}"
        
        return True, None
    
    def check_circuit_breakers(
        self,
        current_equity: float,
        current_date: date
    ) -> CircuitBreakerStatus:
        """
        Check if circuit breakers should be triggered.
        
        Args:
            current_equity: Current account equity
            current_date: Current date
            
        Returns:
            Circuit breaker status
        """
        # Reset daily tracking on new day
        if self.current_date != current_date:
            self.current_date = current_date
            self.daily_start_equity = current_equity
        
        # Update peak equity
        if self.peak_equity is None or current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Check daily loss limit
        if self.daily_start_equity:
            daily_loss = (self.daily_start_equity - current_equity) / self.daily_start_equity
            if daily_loss >= self.daily_loss_limit:
                self.circuit_breaker_status = CircuitBreakerStatus.TRIGGERED
                self.circuit_breaker_reason = f"Daily loss {daily_loss:.1%} exceeds limit {self.daily_loss_limit:.1%}"
                self.logger.error(
                    "circuit_breaker_triggered",
                    reason=self.circuit_breaker_reason,
                    daily_loss=daily_loss
                )
                return self.circuit_breaker_status
            elif daily_loss >= self.daily_loss_limit * self.warning_threshold:
                self.circuit_breaker_status = CircuitBreakerStatus.WARNING
                self.circuit_breaker_reason = f"Daily loss {daily_loss:.1%} approaching limit"
        
        # Check max drawdown
        if self.peak_equity:
            drawdown = (self.peak_equity - current_equity) / self.peak_equity
            if drawdown >= self.max_drawdown_limit:
                self.circuit_breaker_status = CircuitBreakerStatus.TRIGGERED
                self.circuit_breaker_reason = f"Drawdown {drawdown:.1%} exceeds limit {self.max_drawdown_limit:.1%}"
                self.logger.error(
                    "circuit_breaker_triggered",
                    reason=self.circuit_breaker_reason,
                    drawdown=drawdown
                )
                return self.circuit_breaker_status
            elif drawdown >= self.max_drawdown_limit * self.warning_threshold:
                self.circuit_breaker_status = CircuitBreakerStatus.WARNING
                self.circuit_breaker_reason = f"Drawdown {drawdown:.1%} approaching limit"
        
        if self.circuit_breaker_status == CircuitBreakerStatus.WARNING:
            self.logger.warning(
                "circuit_breaker_warning",
                reason=self.circuit_breaker_reason
            )
        
        return self.circuit_breaker_status
    
    def validate_signal(
        self,
        signal: Signal,
        account: Account,
        positions: List[Position],
        market_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate signal against all risk limits.
        
        Args:
            signal: Trading signal to validate
            account: Current account information
            positions: Current open positions
            market_data: Historical price data (for correlation)
            
        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        # Check circuit breakers first
        cb_status = self.check_circuit_breakers(account.equity, datetime.now().date())
        if cb_status == CircuitBreakerStatus.TRIGGERED:
            return False, f"Circuit breaker triggered: {self.circuit_breaker_reason}"
        
        # Only validate BUY signals (SELL signals close positions, reducing risk)
        if signal.signal_type.value != 'BUY':
            return True, None
        
        # Calculate portfolio heat with this new signal
        total_risk = 0.0
        
        # Existing positions
        for pos in positions:
            if hasattr(pos, 'stop_loss') and pos.stop_loss:
                risk = abs(pos.entry_price - pos.stop_loss) * pos.quantity
                total_risk += risk
        
        # New signal
        if signal.stop_loss and signal.position_size:
            risk = abs(signal.price - signal.stop_loss) * signal.position_size
            total_risk += risk
        
        portfolio_heat = total_risk / account.equity
        
        if portfolio_heat > self.max_portfolio_heat:
            return False, f"Portfolio heat {portfolio_heat:.1%} exceeds limit {self.max_portfolio_heat:.1%}"
        
        # Check correlation if market data available
        if market_data and len(positions) > 0:
            correlations = self.calculate_position_correlation(
                positions,
                signal.symbol,
                market_data
            )
            
            for existing_symbol, corr in correlations.items():
                if abs(corr) > self.max_position_correlation:
                    return False, f"Correlation with {existing_symbol} ({corr:.2f}) exceeds limit {self.max_position_correlation}"
        
        # Check sector exposure
        position_value = signal.price * signal.position_size
        is_allowed, reason = self.check_sector_exposure(
            positions,
            signal.symbol,
            position_value,
            account.equity
        )
        
        if not is_allowed:
            return False, reason
        
        # All checks passed
        return True, None
    
    def get_risk_metrics(
        self,
        account: Account,
        positions: List[Position]
    ) -> Dict:
        """
        Get current risk metrics for monitoring.
        
        Returns:
            Dict with risk metrics
        """
        # Calculate portfolio heat
        total_risk = 0.0
        for pos in positions:
            if hasattr(pos, 'stop_loss') and pos.stop_loss:
                risk = abs(pos.entry_price - pos.stop_loss) * pos.quantity
                total_risk += risk
        
        portfolio_heat = total_risk / account.equity if account.equity > 0 else 0
        
        # Calculate daily P&L
        daily_pl = 0.0
        daily_pl_pct = 0.0
        if self.daily_start_equity:
            daily_pl = account.equity - self.daily_start_equity
            daily_pl_pct = daily_pl / self.daily_start_equity
        
        # Calculate drawdown
        drawdown = 0.0
        if self.peak_equity:
            drawdown = (self.peak_equity - account.equity) / self.peak_equity
        
        return {
            'portfolio_heat': portfolio_heat,
            'portfolio_heat_pct': portfolio_heat,
            'max_heat_limit': self.max_portfolio_heat,
            'heat_utilization': portfolio_heat / self.max_portfolio_heat if self.max_portfolio_heat > 0 else 0,
            'daily_pl': daily_pl,
            'daily_pl_pct': daily_pl_pct,
            'daily_loss_limit': self.daily_loss_limit,
            'drawdown': drawdown,
            'max_drawdown_limit': self.max_drawdown_limit,
            'peak_equity': self.peak_equity,
            'circuit_breaker_status': self.circuit_breaker_status.value,
            'circuit_breaker_reason': self.circuit_breaker_reason,
            'num_positions': len(positions)
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (admin only)."""
        self.circuit_breaker_status = CircuitBreakerStatus.NORMAL
        self.circuit_breaker_reason = None
        self.logger.warning("circuit_breaker_manually_reset")
