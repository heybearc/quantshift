"""Position sizing strategies including Kelly Criterion."""

from typing import Dict, Optional
import numpy as np
import structlog

logger = structlog.get_logger()


class PositionSizer:
    """Calculate optimal position sizes based on various strategies."""

    def __init__(
        self,
        account_balance: float,
        max_position_pct: float = 0.20,
        max_portfolio_risk: float = 0.06
    ) -> None:
        """Initialize position sizer."""
        self.account_balance = account_balance
        self.max_position_pct = max_position_pct
        self.max_portfolio_risk = max_portfolio_risk

    def fixed_fractional(
        self,
        entry_price: float,
        stop_loss: float,
        risk_per_trade: float = 0.02
    ) -> int:
        """
        Fixed fractional position sizing.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            risk_per_trade: Percentage of account to risk (0.02 = 2%)
            
        Returns:
            Number of shares to buy
        """
        risk_amount = self.account_balance * risk_per_trade
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            logger.warning("zero_risk_per_share", entry_price=entry_price, stop_loss=stop_loss)
            return 0
        
        position_size = int(risk_amount / risk_per_share)
        
        # Cap at max position percentage
        max_shares = int((self.account_balance * self.max_position_pct) / entry_price)
        position_size = min(position_size, max_shares)
        
        logger.debug(
            "fixed_fractional_sizing",
            position_size=position_size,
            risk_amount=risk_amount,
            risk_per_share=risk_per_share
        )
        
        return position_size

    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        entry_price: float,
        kelly_fraction: float = 0.25
    ) -> int:
        """
        Kelly Criterion position sizing.
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount (positive number)
            entry_price: Entry price for the trade
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly)
            
        Returns:
            Number of shares to buy
        """
        if avg_loss == 0 or win_rate == 0 or win_rate == 1:
            logger.warning("invalid_kelly_inputs", win_rate=win_rate, avg_loss=avg_loss)
            return self.fixed_fractional(entry_price, entry_price * 0.98)
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win rate, q = loss rate, b = win/loss ratio
        win_loss_ratio = avg_win / avg_loss
        kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Apply Kelly fraction (conservative)
        kelly_pct = max(0, kelly_pct * kelly_fraction)
        
        # Cap at max position percentage
        kelly_pct = min(kelly_pct, self.max_position_pct)
        
        # Calculate position size
        position_value = self.account_balance * kelly_pct
        position_size = int(position_value / entry_price)
        
        logger.info(
            "kelly_criterion_sizing",
            kelly_pct=kelly_pct * 100,
            position_size=position_size,
            win_rate=win_rate * 100,
            win_loss_ratio=win_loss_ratio
        )
        
        return position_size

    def atr_based(
        self,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0,
        risk_per_trade: float = 0.02
    ) -> int:
        """
        ATR-based position sizing.
        
        Args:
            entry_price: Entry price for the trade
            atr: Average True Range
            atr_multiplier: ATR multiplier for stop loss (2.0 = 2x ATR)
            risk_per_trade: Percentage of account to risk
            
        Returns:
            Number of shares to buy
        """
        stop_distance = atr * atr_multiplier
        stop_loss = entry_price - stop_distance
        
        return self.fixed_fractional(entry_price, stop_loss, risk_per_trade)

    def volatility_adjusted(
        self,
        entry_price: float,
        volatility: float,
        base_risk: float = 0.02
    ) -> int:
        """
        Volatility-adjusted position sizing.
        
        Higher volatility = smaller position size
        Lower volatility = larger position size
        
        Args:
            entry_price: Entry price for the trade
            volatility: Historical volatility (standard deviation)
            base_risk: Base risk percentage
            
        Returns:
            Number of shares to buy
        """
        # Normalize volatility (assume 0.02 = 2% is baseline)
        baseline_vol = 0.02
        vol_adjustment = baseline_vol / max(volatility, 0.001)
        
        # Adjust risk based on volatility
        adjusted_risk = base_risk * vol_adjustment
        adjusted_risk = min(adjusted_risk, self.max_position_pct)
        
        position_value = self.account_balance * adjusted_risk
        position_size = int(position_value / entry_price)
        
        logger.debug(
            "volatility_adjusted_sizing",
            volatility=volatility,
            adjusted_risk=adjusted_risk,
            position_size=position_size
        )
        
        return position_size


class RiskManager:
    """Portfolio-level risk management."""

    def __init__(
        self,
        max_portfolio_risk: float = 0.06,
        max_correlated_risk: float = 0.10,
        max_sector_exposure: float = 0.30
    ) -> None:
        """Initialize risk manager."""
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlated_risk = max_correlated_risk
        self.max_sector_exposure = max_sector_exposure

    def calculate_portfolio_risk(
        self,
        positions: Dict[str, Dict],
        account_balance: float
    ) -> float:
        """
        Calculate total portfolio risk.
        
        Args:
            positions: Dictionary of current positions
            account_balance: Current account balance
            
        Returns:
            Portfolio risk as percentage of account
        """
        total_risk = 0.0
        
        for symbol, position in positions.items():
            # Calculate risk for this position
            position_value = position["quantity"] * position["current_price"]
            stop_distance = abs(position["current_price"] - position.get("stop_loss", 0))
            position_risk = position["quantity"] * stop_distance
            
            total_risk += position_risk
        
        portfolio_risk_pct = total_risk / account_balance if account_balance > 0 else 0
        
        logger.debug("portfolio_risk_calculated", risk_pct=portfolio_risk_pct * 100)
        
        return portfolio_risk_pct

    def can_open_position(
        self,
        positions: Dict[str, Dict],
        account_balance: float,
        new_position_risk: float
    ) -> bool:
        """
        Check if new position can be opened without exceeding risk limits.
        
        Args:
            positions: Current positions
            account_balance: Current account balance
            new_position_risk: Risk amount for new position
            
        Returns:
            True if position can be opened
        """
        current_risk = self.calculate_portfolio_risk(positions, account_balance)
        new_risk_pct = new_position_risk / account_balance
        total_risk = current_risk + new_risk_pct
        
        if total_risk > self.max_portfolio_risk:
            logger.warning(
                "portfolio_risk_exceeded",
                current_risk=current_risk * 100,
                new_risk=new_risk_pct * 100,
                total_risk=total_risk * 100,
                max_risk=self.max_portfolio_risk * 100
            )
            return False
        
        return True

    def calculate_position_correlation(
        self,
        symbol1: str,
        symbol2: str,
        price_data: Dict[str, list]
    ) -> float:
        """
        Calculate correlation between two positions.
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            price_data: Dictionary of price history for symbols
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if symbol1 not in price_data or symbol2 not in price_data:
            return 0.0
        
        prices1 = np.array(price_data[symbol1])
        prices2 = np.array(price_data[symbol2])
        
        if len(prices1) < 2 or len(prices2) < 2:
            return 0.0
        
        # Calculate returns
        returns1 = np.diff(prices1) / prices1[:-1]
        returns2 = np.diff(prices2) / prices2[:-1]
        
        # Calculate correlation
        correlation = np.corrcoef(returns1, returns2)[0, 1]
        
        return correlation if not np.isnan(correlation) else 0.0

    def check_sector_exposure(
        self,
        positions: Dict[str, Dict],
        sector_map: Dict[str, str],
        account_balance: float
    ) -> Dict[str, float]:
        """
        Check sector exposure limits.
        
        Args:
            positions: Current positions
            sector_map: Mapping of symbols to sectors
            account_balance: Current account balance
            
        Returns:
            Dictionary of sector exposures
        """
        sector_exposure: Dict[str, float] = {}
        
        for symbol, position in positions.items():
            sector = sector_map.get(symbol, "Unknown")
            position_value = position["quantity"] * position["current_price"]
            
            if sector not in sector_exposure:
                sector_exposure[sector] = 0.0
            
            sector_exposure[sector] += position_value
        
        # Convert to percentages
        for sector in sector_exposure:
            sector_exposure[sector] = sector_exposure[sector] / account_balance
        
        # Check limits
        for sector, exposure in sector_exposure.items():
            if exposure > self.max_sector_exposure:
                logger.warning(
                    "sector_exposure_exceeded",
                    sector=sector,
                    exposure=exposure * 100,
                    max_exposure=self.max_sector_exposure * 100
                )
        
        return sector_exposure
