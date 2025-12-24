"""Strategy manager for multi-strategy portfolio management."""

from typing import Dict, List, Optional
import pandas as pd
import structlog

from quantshift_core.strategies import Strategy, Signal
from quantshift_core.position_sizing import PositionSizer, RiskManager

logger = structlog.get_logger()


class StrategyManager:
    """Manage multiple trading strategies with capital allocation."""

    def __init__(
        self,
        strategies: List[Strategy],
        account_balance: float,
        max_positions: int = 10
    ):
        """
        Initialize strategy manager.
        
        Args:
            strategies: List of Strategy instances
            account_balance: Total account balance
            max_positions: Maximum number of concurrent positions
        """
        self.strategies = strategies
        self.account_balance = account_balance
        self.max_positions = max_positions
        
        # Validate capital allocation
        total_allocation = sum(s.capital_allocation for s in strategies)
        if abs(total_allocation - 1.0) > 0.01:
            logger.warning(
                "capital_allocation_mismatch",
                total=total_allocation,
                expected=1.0
            )
        
        # Initialize components
        self.sizer = PositionSizer(account_balance)
        self.risk_manager = RiskManager()
        
        # Track positions by strategy
        self.positions: Dict[str, Dict] = {}  # symbol -> position info
        
        logger.info(
            "strategy_manager_initialized",
            strategies=[s.name for s in strategies],
            allocations=[s.capital_allocation for s in strategies]
        )

    def generate_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        daily_data: Optional[pd.DataFrame] = None,
        hourly_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Signal]:
        """
        Generate signals from all strategies.
        
        Args:
            symbol: Trading symbol
            data: Current timeframe OHLCV data
            daily_data: Daily timeframe data (optional)
            hourly_data: Hourly timeframe data (optional)
            
        Returns:
            Dictionary mapping strategy name to signal
        """
        signals = {}
        
        for strategy in self.strategies:
            try:
                signal = strategy.generate_signal(symbol, data, daily_data, hourly_data)
                signals[strategy.name] = signal
                
                if signal != Signal.HOLD:
                    logger.info(
                        "strategy_signal",
                        strategy=strategy.name,
                        symbol=symbol,
                        signal=signal.value
                    )
            except Exception as e:
                logger.error(
                    "strategy_signal_failed",
                    strategy=strategy.name,
                    symbol=symbol,
                    error=str(e)
                )
                signals[strategy.name] = Signal.HOLD
        
        return signals

    def get_consensus_signal(self, signals: Dict[str, Signal]) -> Optional[Signal]:
        """
        Get consensus signal from multiple strategies.
        
        Args:
            signals: Dictionary of strategy signals
            
        Returns:
            Consensus signal or None if no consensus
        """
        buy_count = sum(1 for s in signals.values() if s == Signal.BUY)
        sell_count = sum(1 for s in signals.values() if s == Signal.SELL)
        total_strategies = len(signals)
        
        # Require majority consensus (>50%)
        if buy_count > total_strategies / 2:
            logger.info("consensus_signal", signal="BUY", votes=buy_count, total=total_strategies)
            return Signal.BUY
        elif sell_count > total_strategies / 2:
            logger.info("consensus_signal", signal="SELL", votes=sell_count, total=total_strategies)
            return Signal.SELL
        
        logger.debug("no_consensus", buy_votes=buy_count, sell_votes=sell_count, total=total_strategies)
        return None

    def calculate_position_size(
        self,
        symbol: str,
        strategy: Strategy,
        entry_price: float,
        stop_loss: float
    ) -> int:
        """
        Calculate position size for a strategy.
        
        Args:
            symbol: Trading symbol
            strategy: Strategy instance
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Number of shares to buy
        """
        # Check if we can open new position
        position_risk = abs(entry_price - stop_loss) * 100  # Estimate for 100 shares
        
        if not self.risk_manager.can_open_position(
            self.positions,
            self.account_balance,
            position_risk
        ):
            logger.warning("position_rejected", reason="portfolio_risk_exceeded")
            return 0
        
        # Check max positions
        if len(self.positions) >= self.max_positions:
            logger.warning("position_rejected", reason="max_positions_reached")
            return 0
        
        # Calculate position size
        shares = strategy.calculate_position_size(
            symbol,
            entry_price,
            stop_loss,
            self.account_balance,
            self.sizer
        )
        
        logger.info(
            "position_size_calculated",
            strategy=strategy.name,
            symbol=symbol,
            shares=shares,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
        
        return shares

    def open_position(
        self,
        symbol: str,
        strategy: Strategy,
        entry_price: float,
        quantity: int,
        stop_loss: float,
        take_profit: float
    ) -> bool:
        """
        Open a new position.
        
        Args:
            symbol: Trading symbol
            strategy: Strategy that generated the signal
            entry_price: Entry price
            quantity: Number of shares
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            True if position opened successfully
        """
        if symbol in self.positions:
            logger.warning("position_already_exists", symbol=symbol)
            return False
        
        self.positions[symbol] = {
            "strategy": strategy.name,
            "quantity": quantity,
            "entry_price": entry_price,
            "current_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "unrealized_pnl": 0.0
        }
        
        # Record trade for strategy
        strategy.active_positions[symbol] = self.positions[symbol]
        
        logger.info(
            "position_opened",
            strategy=strategy.name,
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price
        )
        
        return True

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str = "manual"
    ) -> bool:
        """
        Close an existing position.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Reason for closing
            
        Returns:
            True if position closed successfully
        """
        if symbol not in self.positions:
            logger.warning("position_not_found", symbol=symbol)
            return False
        
        position = self.positions[symbol]
        
        # Calculate P&L
        pnl = (exit_price - position["entry_price"]) * position["quantity"]
        pnl_pct = ((exit_price - position["entry_price"]) / position["entry_price"]) * 100
        
        # Find strategy and record trade
        for strategy in self.strategies:
            if strategy.name == position["strategy"]:
                strategy.record_trade({
                    "symbol": symbol,
                    "action": "SELL",
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "quantity": position["quantity"],
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "reason": reason
                })
                
                # Remove from active positions
                if symbol in strategy.active_positions:
                    del strategy.active_positions[symbol]
                break
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(
            "position_closed",
            symbol=symbol,
            exit_price=exit_price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            reason=reason
        )
        
        return True

    def update_positions(self, market_prices: Dict[str, float]) -> None:
        """
        Update positions with current market prices.
        
        Args:
            market_prices: Dictionary of symbol -> current price
        """
        for symbol, position in self.positions.items():
            if symbol in market_prices:
                current_price = market_prices[symbol]
                position["current_price"] = current_price
                
                # Calculate unrealized P&L
                position["unrealized_pnl"] = (
                    (current_price - position["entry_price"]) * position["quantity"]
                )

    def check_stops(self, market_prices: Dict[str, float]) -> List[str]:
        """
        Check if any positions hit stop loss or take profit.
        
        Args:
            market_prices: Dictionary of symbol -> current price
            
        Returns:
            List of symbols that should be closed
        """
        to_close = []
        
        for symbol, position in self.positions.items():
            if symbol not in market_prices:
                continue
            
            current_price = market_prices[symbol]
            
            # Check stop loss
            if current_price <= position["stop_loss"]:
                logger.info("stop_loss_hit", symbol=symbol, price=current_price)
                to_close.append((symbol, current_price, "stop_loss"))
            
            # Check take profit
            elif current_price >= position["take_profit"]:
                logger.info("take_profit_hit", symbol=symbol, price=current_price)
                to_close.append((symbol, current_price, "take_profit"))
        
        return to_close

    def get_strategy_performance(self) -> List[Dict]:
        """Get performance metrics for all strategies."""
        performance = []
        
        for strategy in self.strategies:
            metrics = strategy.get_performance_metrics()
            if "error" not in metrics:
                performance.append(metrics)
        
        return performance

    def rebalance_allocations(self) -> None:
        """
        Rebalance capital allocations based on strategy performance.
        
        This is a simple implementation that increases allocation to
        winning strategies and decreases allocation to losing ones.
        """
        performance = self.get_strategy_performance()
        
        if not performance:
            return
        
        # Calculate performance scores (win rate * profit factor)
        scores = {}
        for perf in performance:
            strategy_name = perf["strategy"]
            score = (perf["win_rate"] / 100) * perf["profit_factor"]
            scores[strategy_name] = score
        
        # Normalize scores to sum to 1.0
        total_score = sum(scores.values())
        if total_score == 0:
            return
        
        # Update allocations
        for strategy in self.strategies:
            if strategy.name in scores:
                new_allocation = scores[strategy.name] / total_score
                
                # Don't change allocation too drastically (max 10% change)
                change = new_allocation - strategy.capital_allocation
                if abs(change) > 0.10:
                    change = 0.10 if change > 0 else -0.10
                
                strategy.capital_allocation = strategy.capital_allocation + change
                
                logger.info(
                    "allocation_rebalanced",
                    strategy=strategy.name,
                    old_allocation=strategy.capital_allocation - change,
                    new_allocation=strategy.capital_allocation
                )

    def get_portfolio_summary(self) -> Dict:
        """Get summary of portfolio and strategy performance."""
        total_positions = len(self.positions)
        total_unrealized_pnl = sum(p["unrealized_pnl"] for p in self.positions.values())
        
        # Get strategy breakdown
        strategy_positions = {}
        for position in self.positions.values():
            strategy_name = position["strategy"]
            if strategy_name not in strategy_positions:
                strategy_positions[strategy_name] = 0
            strategy_positions[strategy_name] += 1
        
        return {
            "total_positions": total_positions,
            "total_unrealized_pnl": total_unrealized_pnl,
            "strategy_positions": strategy_positions,
            "strategy_allocations": {s.name: s.capital_allocation for s in self.strategies},
            "strategy_performance": self.get_strategy_performance()
        }
