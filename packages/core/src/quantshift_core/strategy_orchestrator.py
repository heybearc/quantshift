"""
Strategy Orchestrator - Multi-Strategy Execution Manager

Manages multiple trading strategies simultaneously with capital allocation,
conflict resolution, and performance tracking.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import structlog

from .strategies.base_strategy import BaseStrategy, Signal, SignalType, Account, Position

logger = structlog.get_logger()


class StrategyOrchestrator:
    """
    Orchestrates multiple trading strategies with capital allocation.
    
    Responsibilities:
    - Manage multiple strategies simultaneously
    - Allocate capital per strategy
    - Aggregate signals from all strategies
    - Resolve conflicts (multiple strategies signaling same symbol)
    - Track performance per strategy
    """
    
    def __init__(
        self,
        strategies: List[BaseStrategy],
        capital_allocation: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            strategies: List of strategy instances
            capital_allocation: Dict mapping strategy name to allocation % (0-1)
                               If None, equal allocation across all strategies
        """
        self.name = "MultiStrategy"  # For compatibility with AlpacaExecutor
        self.strategies = strategies
        self.logger = logger.bind(orchestrator="StrategyOrchestrator")
        
        # Set capital allocation
        if capital_allocation is None:
            # Equal allocation
            allocation_pct = 1.0 / len(strategies)
            self.capital_allocation = {
                strategy.name: allocation_pct for strategy in strategies
            }
        else:
            self.capital_allocation = capital_allocation
            
        # Validate allocation sums to 1.0
        total_allocation = sum(self.capital_allocation.values())
        if not (0.99 <= total_allocation <= 1.01):  # Allow small floating point error
            raise ValueError(f"Capital allocation must sum to 1.0, got {total_allocation}")
        
        self.logger.info(
            "orchestrator_initialized",
            num_strategies=len(strategies),
            strategies=[s.name for s in strategies],
            allocation=self.capital_allocation
        )
    
    def generate_signals(
        self,
        market_data: Dict[str, Any],
        account: Account,
        positions: List[Position]
    ) -> List[Signal]:
        """
        Generate signals from all strategies and aggregate them.
        
        Args:
            market_data: Market data for all symbols (dict of symbol -> DataFrame)
            account: Current account information
            positions: Current open positions
            
        Returns:
            List of aggregated signals from all strategies
        """
        all_signals = []
        
        # Generate signals from each strategy
        for strategy in self.strategies:
            try:
                # Create virtual account with allocated capital
                allocated_account = self._create_allocated_account(
                    account, 
                    self.capital_allocation[strategy.name]
                )
                
                # Get positions managed by this strategy
                strategy_positions = [
                    pos for pos in positions 
                    if pos.metadata and pos.metadata.get('strategy') == strategy.name
                ]
                
                # Generate signals for each symbol
                for symbol, data in market_data.items():
                    signals = strategy.generate_signals(
                        data,
                        allocated_account,
                        strategy_positions
                    )
                    
                    # Tag signals with strategy name
                    for signal in signals:
                        if signal.metadata is None:
                            signal.metadata = {}
                        signal.metadata['strategy'] = strategy.name
                        signal.metadata['capital_allocation'] = self.capital_allocation[strategy.name]
                    
                    all_signals.extend(signals)
                    
            except Exception as e:
                self.logger.error(
                    "strategy_error",
                    strategy=strategy.name,
                    error=str(e)
                )
        
        # Resolve conflicts
        resolved_signals = self._resolve_conflicts(all_signals)
        
        self.logger.info(
            "signals_generated",
            total_signals=len(all_signals),
            resolved_signals=len(resolved_signals)
        )
        
        return resolved_signals
    
    def _create_allocated_account(
        self,
        account: Account,
        allocation: float
    ) -> Account:
        """
        Create a virtual account with allocated capital.
        
        Args:
            account: Original account
            allocation: Allocation percentage (0-1)
            
        Returns:
            Account with allocated capital
        """
        return Account(
            equity=account.equity * allocation,
            buying_power=account.buying_power * allocation,
            cash=account.cash * allocation
        )
    
    def _resolve_conflicts(self, signals: List[Signal]) -> List[Signal]:
        """
        Resolve conflicts when multiple strategies signal the same symbol.
        
        Current strategy: Take the signal with highest confidence.
        Future: Could implement more sophisticated conflict resolution.
        
        Args:
            signals: List of all signals
            
        Returns:
            List of resolved signals (one per symbol)
        """
        if not signals:
            return []
        
        # Group signals by symbol and type
        signal_groups: Dict[tuple, List[Signal]] = {}
        for signal in signals:
            key = (signal.symbol, signal.signal_type)
            if key not in signal_groups:
                signal_groups[key] = []
            signal_groups[key].append(signal)
        
        # Resolve conflicts
        resolved = []
        for (symbol, signal_type), group in signal_groups.items():
            if len(group) == 1:
                # No conflict
                resolved.append(group[0])
            else:
                # Multiple strategies signaling same symbol
                # Take signal with highest confidence
                best_signal = max(group, key=lambda s: s.confidence)
                
                self.logger.info(
                    "conflict_resolved",
                    symbol=symbol,
                    signal_type=signal_type.value,
                    num_conflicts=len(group),
                    strategies=[s.metadata.get('strategy') for s in group],
                    selected_strategy=best_signal.metadata.get('strategy')
                )
                
                resolved.append(best_signal)
        
        return resolved
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for each strategy.
        
        Returns:
            Dict mapping strategy name to performance metrics
        """
        performance = {}
        
        for strategy in self.strategies:
            try:
                metrics = strategy.get_performance_metrics()
                performance[strategy.name] = metrics
            except Exception as e:
                self.logger.error(
                    "performance_error",
                    strategy=strategy.name,
                    error=str(e)
                )
                performance[strategy.name] = {"error": str(e)}
        
        return performance
