"""
Strategy Orchestrator - Multi-Strategy Execution Manager

Manages multiple trading strategies simultaneously with capital allocation,
conflict resolution, performance tracking, and market regime adaptation.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd
import structlog

from .strategies.base_strategy import BaseStrategy, Signal, SignalType, Account, Position
from .market_regime import MarketRegimeDetector, MarketRegime
from .risk_manager import RiskManager, CircuitBreakerStatus
from .ml_regime_classifier import MLRegimeClassifier

logger = structlog.get_logger()


class StrategyOrchestrator:
    """
    Orchestrates multiple trading strategies with capital allocation.
    
    Responsibilities:
    - Manage multiple strategies simultaneously
    - Allocate capital per strategy (static or regime-based)
    - Aggregate signals from all strategies
    - Resolve conflicts (multiple strategies signaling same symbol)
    - Track performance per strategy
    - Adapt to market regimes
    - Enforce portfolio-level risk limits
    """
    
    def __init__(
        self,
        strategies: List[BaseStrategy],
        capital_allocation: Optional[Dict[str, float]] = None,
        use_regime_detection: bool = False,
        regime_detector: Optional[MarketRegimeDetector] = None,
        use_ml_regime: bool = False,
        ml_regime_classifier: Optional[MLRegimeClassifier] = None,
        use_risk_management: bool = True,
        risk_manager: Optional[RiskManager] = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            strategies: List of strategy instances
            capital_allocation: Dict mapping strategy name to allocation % (0-1)
                               If None, equal allocation across all strategies
            use_regime_detection: Enable dynamic allocation based on market regime
            regime_detector: MarketRegimeDetector instance (created if None and use_regime_detection=True)
            use_ml_regime: Use ML-based regime classifier instead of rule-based
            ml_regime_classifier: MLRegimeClassifier instance (created if None and use_ml_regime=True)
            use_risk_management: Enable portfolio-level risk management
            risk_manager: RiskManager instance (created if None and use_risk_management=True)
        """
        self.name = "MultiStrategy"  # For compatibility with AlpacaExecutor
        self.strategies = strategies
        self.use_regime_detection = use_regime_detection
        self.use_ml_regime = use_ml_regime
        self.use_risk_management = use_risk_management
        self.logger = logger.bind(orchestrator="StrategyOrchestrator")
        
        # Initialize regime detector if needed
        if use_regime_detection:
            if use_ml_regime:
                # Use ML-based regime classifier
                self.ml_regime_classifier = ml_regime_classifier or MLRegimeClassifier()
                self.regime_detector = None
                self.logger.info("Using ML-based regime classifier")
            else:
                # Use rule-based regime detector
                self.regime_detector = regime_detector or MarketRegimeDetector()
                self.ml_regime_classifier = None
                self.logger.info("Using rule-based regime detector")
            
            self.base_allocation = capital_allocation  # Store base allocation
            self.capital_allocation = capital_allocation or self._equal_allocation()
        else:
            self.regime_detector = None
            self.ml_regime_classifier = None
            self.base_allocation = None
            # Set capital allocation
            if capital_allocation is None:
                # Equal allocation
                allocation_pct = 1.0 / len(strategies)
                self.capital_allocation = {
                    strategy.name: allocation_pct for strategy in strategies
                }
            else:
                self.capital_allocation = capital_allocation
        
        # Initialize risk manager if needed
        if use_risk_management:
            self.risk_manager = risk_manager or RiskManager()
        else:
            self.risk_manager = None
            
        # Validate allocation sums to 1.0
        total_allocation = sum(self.capital_allocation.values())
        if not (0.99 <= total_allocation <= 1.01):  # Allow small floating point error
            raise ValueError(f"Capital allocation must sum to 1.0, got {total_allocation}")
        
        self.current_regime = MarketRegime.UNKNOWN
        self.regime_risk_multiplier = 1.0
        
        self.logger.info(
            "orchestrator_initialized",
            num_strategies=len(strategies),
            strategies=[s.name for s in strategies],
            allocation=self.capital_allocation,
            regime_detection=use_regime_detection,
            risk_management=use_risk_management
        )
    
    def _equal_allocation(self) -> Dict[str, float]:
        """Create equal allocation across all strategies."""
        allocation_pct = 1.0 / len(self.strategies)
        return {strategy.name: allocation_pct for strategy in self.strategies}
    
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
        
        # Update regime detection if enabled
        if self.use_regime_detection:
            # Use SPY data for regime detection (or first symbol if SPY not available)
            regime_symbol = 'SPY' if 'SPY' in market_data else list(market_data.keys())[0]
            regime_data = market_data[regime_symbol]
            
            # Detect current regime (ML or rule-based)
            if self.use_ml_regime and self.ml_regime_classifier:
                # ML-based regime detection
                regime_name, confidence = self.ml_regime_classifier.predict_regime(regime_data)
                regime = MarketRegime[regime_name]
                
                # Get allocation and risk multiplier from ML classifier
                allocation_dict = self.ml_regime_classifier.get_regime_allocation(regime_name)
                risk_multiplier = self.ml_regime_classifier.get_risk_multiplier(regime_name)
                
                indicators = {'ml_confidence': confidence, 'regime': regime_name}
            else:
                # Rule-based regime detection
                regime, indicators = self.regime_detector.detect_regime(regime_data)
                allocation_dict = self.regime_detector.get_regime_allocation(regime)
                risk_multiplier = self.regime_detector.get_risk_multiplier(regime)
            
            # Update allocation if regime changed
            if regime != self.current_regime:
                self.current_regime = regime
                self.capital_allocation = allocation_dict
                self.regime_risk_multiplier = risk_multiplier
                
                self.logger.info(
                    "regime_allocation_updated",
                    regime=regime.value if hasattr(regime, 'value') else regime,
                    method='ml' if self.use_ml_regime else 'rule_based',
                    allocation=self.capital_allocation,
                    risk_multiplier=self.regime_risk_multiplier,
                    indicators=indicators
                )
        
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
                    
                    # Tag signals with strategy name and apply regime risk adjustment
                    for signal in signals:
                        if signal.metadata is None:
                            signal.metadata = {}
                        signal.metadata['strategy'] = strategy.name
                        signal.metadata['capital_allocation'] = self.capital_allocation[strategy.name]
                        
                        # Apply regime risk multiplier to position size
                        if self.use_regime_detection and signal.position_size:
                            original_size = signal.position_size
                            signal.position_size = int(signal.position_size * self.regime_risk_multiplier)
                            signal.metadata['regime'] = self.current_regime.value
                            signal.metadata['risk_multiplier'] = self.regime_risk_multiplier
                            signal.metadata['original_position_size'] = original_size
                    
                    all_signals.extend(signals)
                    
            except Exception as e:
                self.logger.error(
                    "strategy_error",
                    strategy=strategy.name,
                    error=str(e)
                )
        
        # Resolve conflicts
        resolved_signals = self._resolve_conflicts(all_signals)
        
        # Validate signals against risk limits
        if self.use_risk_management and self.risk_manager:
            validated_signals = []
            rejected_count = 0
            
            for signal in resolved_signals:
                is_valid, reason = self.risk_manager.validate_signal(
                    signal,
                    account,
                    positions,
                    market_data
                )
                
                if is_valid:
                    validated_signals.append(signal)
                else:
                    rejected_count += 1
                    self.logger.warning(
                        "signal_rejected_by_risk_manager",
                        symbol=signal.symbol,
                        signal_type=signal.signal_type.value,
                        reason=reason
                    )
            
            self.logger.info(
                "signals_generated",
                total_signals=len(all_signals),
                resolved_signals=len(resolved_signals),
                validated_signals=len(validated_signals),
                rejected_by_risk=rejected_count
            )
            
            return validated_signals
        else:
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
