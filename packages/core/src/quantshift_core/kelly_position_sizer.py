"""
Kelly Criterion Position Sizing

Implements the Kelly Criterion for optimal position sizing based on historical
win rate and profit/loss statistics. Uses fractional Kelly for safety.

Author: QuantShift Team
Created: 2026-03-04
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TradeStats:
    """Statistics for Kelly Criterion calculation"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit: float
    total_loss: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float


class KellyPositionSizer:
    """
    Kelly Criterion Position Sizer
    
    Calculates optimal position size using the Kelly Criterion formula:
    Kelly % = (Win Rate × Avg Win - (1 - Win Rate) × Avg Loss) / Avg Win
    
    Uses fractional Kelly (default 0.25) for safety and requires minimum
    trade history for reliable calculations.
    """
    
    def __init__(
        self,
        kelly_fraction: float = 0.25,
        min_trades_required: int = 20,
        lookback_trades: int = 30,
        default_risk_pct: float = 0.01,
        max_position_size_pct: float = 0.05,
        logger_instance: Optional[structlog.BoundLogger] = None
    ):
        """
        Initialize Kelly Position Sizer
        
        Args:
            kelly_fraction: Fraction of Kelly to use (0.25 = 25% Kelly for safety)
            min_trades_required: Minimum trades needed for Kelly calculation
            lookback_trades: Number of recent trades to analyze
            default_risk_pct: Default risk % if insufficient data (1% = 0.01)
            max_position_size_pct: Maximum position size as % of portfolio (5% = 0.05)
            logger_instance: Optional logger instance
        """
        self.kelly_fraction = kelly_fraction
        self.min_trades_required = min_trades_required
        self.lookback_trades = lookback_trades
        self.default_risk_pct = default_risk_pct
        self.max_position_size_pct = max_position_size_pct
        self.logger = logger_instance or logger
        
        self.logger.info(
            "kelly_sizer_initialized",
            kelly_fraction=kelly_fraction,
            min_trades=min_trades_required,
            lookback=lookback_trades,
            default_risk=default_risk_pct,
            max_position=max_position_size_pct
        )
    
    def calculate_trade_stats(self, trades: List[Dict]) -> Optional[TradeStats]:
        """
        Calculate trade statistics from historical trades
        
        Args:
            trades: List of trade dictionaries with 'pnl' and 'exit_time' fields
            
        Returns:
            TradeStats object or None if insufficient data
        """
        if not trades or len(trades) < self.min_trades_required:
            self.logger.warning(
                "insufficient_trades_for_kelly",
                trade_count=len(trades) if trades else 0,
                required=self.min_trades_required
            )
            return None
        
        # Use most recent trades within lookback window
        recent_trades = sorted(trades, key=lambda x: x.get('exit_time', ''), reverse=True)
        recent_trades = recent_trades[:self.lookback_trades]
        
        winning_trades = [t for t in recent_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in recent_trades if t.get('pnl', 0) < 0]
        
        total_trades = len(recent_trades)
        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        
        if total_trades == 0:
            return None
        
        # Calculate statistics
        total_profit = sum(t.get('pnl', 0) for t in winning_trades)
        total_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        
        win_rate = num_wins / total_trades if total_trades > 0 else 0
        avg_win = total_profit / num_wins if num_wins > 0 else 0
        avg_loss = total_loss / num_losses if num_losses > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        stats = TradeStats(
            total_trades=total_trades,
            winning_trades=num_wins,
            losing_trades=num_losses,
            total_profit=total_profit,
            total_loss=total_loss,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor
        )
        
        self.logger.info(
            "trade_stats_calculated",
            total_trades=total_trades,
            win_rate=f"{win_rate:.2%}",
            avg_win=f"${avg_win:.2f}",
            avg_loss=f"${avg_loss:.2f}",
            profit_factor=f"{profit_factor:.2f}"
        )
        
        return stats
    
    def calculate_kelly_percentage(self, stats: TradeStats) -> float:
        """
        Calculate Kelly Criterion percentage
        
        Formula: Kelly % = (Win Rate × Avg Win - (1 - Win Rate) × Avg Loss) / Avg Win
        
        Args:
            stats: TradeStats object with win rate and profit/loss statistics
            
        Returns:
            Kelly percentage (0.0 to 1.0)
        """
        if stats.avg_win <= 0:
            self.logger.warning("kelly_calc_invalid_avg_win", avg_win=stats.avg_win)
            return 0.0
        
        # Kelly Criterion formula
        kelly_pct = (
            (stats.win_rate * stats.avg_win - (1 - stats.win_rate) * stats.avg_loss) 
            / stats.avg_win
        )
        
        # Apply fractional Kelly for safety
        fractional_kelly = kelly_pct * self.kelly_fraction
        
        # Ensure non-negative
        fractional_kelly = max(0.0, fractional_kelly)
        
        # Cap at maximum position size
        fractional_kelly = min(fractional_kelly, self.max_position_size_pct)
        
        self.logger.info(
            "kelly_percentage_calculated",
            raw_kelly=f"{kelly_pct:.2%}",
            fractional_kelly=f"{fractional_kelly:.2%}",
            kelly_fraction=self.kelly_fraction
        )
        
        return fractional_kelly
    
    def get_position_size(
        self,
        account_value: float,
        entry_price: float,
        stop_loss_price: float,
        trades: List[Dict],
        strategy_name: Optional[str] = None
    ) -> Tuple[int, float, str]:
        """
        Calculate position size using Kelly Criterion
        
        Args:
            account_value: Current account value
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            trades: Historical trades for statistics
            strategy_name: Optional strategy name for logging
            
        Returns:
            Tuple of (shares, risk_amount, method_used)
            - shares: Number of shares to buy
            - risk_amount: Dollar amount at risk
            - method_used: "kelly" or "fixed_fractional"
        """
        # Calculate trade statistics
        stats = self.calculate_trade_stats(trades)
        
        # Use Kelly if we have sufficient data
        if stats and stats.total_trades >= self.min_trades_required:
            kelly_pct = self.calculate_kelly_percentage(stats)
            
            # Calculate position size based on Kelly percentage
            position_value = account_value * kelly_pct
            shares = int(position_value / entry_price)
            
            # Calculate actual risk
            risk_per_share = abs(entry_price - stop_loss_price)
            risk_amount = shares * risk_per_share
            
            self.logger.info(
                "kelly_position_calculated",
                strategy=strategy_name,
                kelly_pct=f"{kelly_pct:.2%}",
                position_value=f"${position_value:.2f}",
                shares=shares,
                risk_amount=f"${risk_amount:.2f}",
                method="kelly"
            )
            
            return shares, risk_amount, "kelly"
        
        else:
            # Fallback to fixed fractional risk
            risk_per_share = abs(entry_price - stop_loss_price)
            if risk_per_share <= 0:
                self.logger.warning("invalid_stop_loss", entry=entry_price, stop=stop_loss_price)
                return 0, 0.0, "invalid"
            
            risk_amount = account_value * self.default_risk_pct
            shares = int(risk_amount / risk_per_share)
            
            self.logger.info(
                "fixed_fractional_position",
                strategy=strategy_name,
                risk_pct=f"{self.default_risk_pct:.2%}",
                shares=shares,
                risk_amount=f"${risk_amount:.2f}",
                method="fixed_fractional",
                reason="insufficient_trades"
            )
            
            return shares, risk_amount, "fixed_fractional"
    
    def get_kelly_stats_summary(self, trades: List[Dict]) -> Dict:
        """
        Get summary of Kelly statistics for reporting
        
        Args:
            trades: Historical trades
            
        Returns:
            Dictionary with Kelly statistics
        """
        stats = self.calculate_trade_stats(trades)
        
        if not stats:
            return {
                "has_sufficient_data": False,
                "trade_count": len(trades) if trades else 0,
                "required_trades": self.min_trades_required,
                "method": "fixed_fractional",
                "default_risk_pct": self.default_risk_pct
            }
        
        kelly_pct = self.calculate_kelly_percentage(stats)
        
        return {
            "has_sufficient_data": True,
            "trade_count": stats.total_trades,
            "win_rate": stats.win_rate,
            "avg_win": stats.avg_win,
            "avg_loss": stats.avg_loss,
            "profit_factor": stats.profit_factor,
            "raw_kelly_pct": kelly_pct / self.kelly_fraction,  # Reverse fractional
            "fractional_kelly_pct": kelly_pct,
            "kelly_fraction": self.kelly_fraction,
            "method": "kelly"
        }
