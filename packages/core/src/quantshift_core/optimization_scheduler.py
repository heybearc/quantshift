"""
Optimization Scheduler - Automated Parameter Re-optimization

Runs monthly parameter optimization for all strategies and applies optimal parameters.
Tracks optimization history and performance improvements.

Author: QuantShift Team
Created: 2026-03-04
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import structlog
import json
from pathlib import Path

from .parameter_optimizer import ParameterOptimizer
from .strategy_performance_tracker import StrategyPerformanceMonitor

logger = structlog.get_logger(__name__)


class OptimizationScheduler:
    """
    Automated parameter optimization scheduler.
    
    Runs monthly re-optimization of strategy parameters and applies
    the best parameters to live strategies.
    """
    
    def __init__(
        self,
        db_manager: Any,
        optimization_interval_days: int = 30,
        min_trades_required: int = 50,
        optimization_history_path: str = '/opt/quantshift/data/optimization_history.json'
    ):
        """
        Initialize optimization scheduler.
        
        Args:
            db_manager: Database manager for fetching trade history
            optimization_interval_days: Days between optimizations (default 30)
            min_trades_required: Minimum trades needed to run optimization
            optimization_history_path: Path to store optimization history
        """
        self.db_manager = db_manager
        self.optimization_interval_days = optimization_interval_days
        self.min_trades_required = min_trades_required
        self.optimization_history_path = optimization_history_path
        
        self.optimizer = ParameterOptimizer(
            train_months=6,
            test_months=1,
            min_trades=10,
            optimization_metric='sharpe'
        )
        
        self.last_optimization_date: Dict[str, datetime] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Load optimization history
        self._load_history()
        
        logger.info(
            "optimization_scheduler_initialized",
            interval_days=optimization_interval_days,
            min_trades=min_trades_required
        )
    
    def should_optimize(self, strategy_name: str, bot_name: str) -> bool:
        """
        Check if strategy should be re-optimized.
        
        Args:
            strategy_name: Name of strategy to check
            bot_name: Bot name
            
        Returns:
            True if optimization is due
        """
        key = f"{bot_name}:{strategy_name}"
        
        # Check if we have enough trades
        try:
            trades = self.db_manager.get_closed_trades(
                bot_name=bot_name,
                strategy_name=strategy_name,
                limit=self.min_trades_required
            )
            
            if len(trades) < self.min_trades_required:
                logger.debug(
                    "insufficient_trades_for_optimization",
                    strategy=strategy_name,
                    trades=len(trades),
                    required=self.min_trades_required
                )
                return False
        except Exception as e:
            logger.error("failed_to_check_trades", error=str(e))
            return False
        
        # Check if optimization is due
        if key not in self.last_optimization_date:
            logger.info(
                "first_optimization_due",
                strategy=strategy_name,
                bot=bot_name
            )
            return True
        
        last_opt = self.last_optimization_date[key]
        days_since = (datetime.utcnow() - last_opt).days
        
        if days_since >= self.optimization_interval_days:
            logger.info(
                "optimization_due",
                strategy=strategy_name,
                bot=bot_name,
                days_since=days_since
            )
            return True
        
        return False
    
    def optimize_strategy(
        self,
        strategy_class: Any,
        strategy_name: str,
        bot_name: str,
        parameter_ranges: Dict[str, List[Any]],
        current_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Run parameter optimization for a strategy.
        
        Args:
            strategy_class: Strategy class to optimize
            strategy_name: Name of strategy
            bot_name: Bot name
            parameter_ranges: Parameter ranges to test
            current_params: Current parameter values
            
        Returns:
            Dict with optimal parameters and metrics, or None if failed
        """
        logger.info(
            "starting_optimization",
            strategy=strategy_name,
            bot=bot_name,
            param_ranges=parameter_ranges
        )
        
        try:
            # Fetch market data for optimization
            # This is a simplified version - real implementation would fetch actual market data
            market_data = self._fetch_market_data(bot_name, strategy_name)
            
            if market_data is None or len(market_data) < 200:
                logger.error("insufficient_market_data", strategy=strategy_name)
                return None
            
            # Run optimization
            result = self.optimizer.optimize_parameters(
                strategy_class=strategy_class,
                parameter_ranges=parameter_ranges,
                market_data=market_data,
                initial_capital=100000
            )
            
            if result is None:
                logger.warning("optimization_failed", strategy=strategy_name)
                return None
            
            # Compare with current performance
            improvement = self._calculate_improvement(
                result['test_metrics'],
                current_params
            )
            
            # Record optimization
            key = f"{bot_name}:{strategy_name}"
            self.last_optimization_date[key] = datetime.utcnow()
            
            optimization_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'bot_name': bot_name,
                'strategy_name': strategy_name,
                'current_params': current_params,
                'optimal_params': result['optimal_params'],
                'train_metrics': result['train_metrics'],
                'test_metrics': result['test_metrics'],
                'improvement_pct': improvement,
                'applied': False
            }
            
            self.optimization_history.append(optimization_record)
            self._save_history()
            
            logger.info(
                "optimization_complete",
                strategy=strategy_name,
                bot=bot_name,
                optimal_params=result['optimal_params'],
                test_sharpe=result['test_metrics']['sharpe'],
                improvement=f"{improvement:.1f}%"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "optimization_error",
                strategy=strategy_name,
                error=str(e)
            )
            return None
    
    def apply_optimal_parameters(
        self,
        strategy_name: str,
        bot_name: str,
        optimal_params: Dict[str, Any]
    ) -> bool:
        """
        Apply optimal parameters to a strategy.
        
        Args:
            strategy_name: Name of strategy
            bot_name: Bot name
            optimal_params: Optimal parameters to apply
            
        Returns:
            True if successfully applied
        """
        try:
            # Store in database
            with self.db_manager.session() as session:
                session.execute(
                    """
                    INSERT INTO strategy_parameters 
                    (bot_name, strategy_name, parameters, applied_at, source)
                    VALUES (:bot_name, :strategy_name, :parameters, :applied_at, :source)
                    ON CONFLICT (bot_name, strategy_name) 
                    DO UPDATE SET 
                        parameters = :parameters,
                        applied_at = :applied_at,
                        source = :source
                    """,
                    {
                        'bot_name': bot_name,
                        'strategy_name': strategy_name,
                        'parameters': json.dumps(optimal_params),
                        'applied_at': datetime.utcnow(),
                        'source': 'automated_optimization'
                    }
                )
                session.commit()
            
            # Mark as applied in history
            for record in reversed(self.optimization_history):
                if (record['bot_name'] == bot_name and 
                    record['strategy_name'] == strategy_name and
                    not record['applied']):
                    record['applied'] = True
                    record['applied_at'] = datetime.utcnow().isoformat()
                    break
            
            self._save_history()
            
            logger.info(
                "optimal_parameters_applied",
                strategy=strategy_name,
                bot=bot_name,
                params=optimal_params
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "failed_to_apply_parameters",
                strategy=strategy_name,
                error=str(e)
            )
            return False
    
    def get_optimization_history(
        self,
        strategy_name: Optional[str] = None,
        bot_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get optimization history.
        
        Args:
            strategy_name: Filter by strategy name
            bot_name: Filter by bot name
            limit: Maximum records to return
            
        Returns:
            List of optimization records
        """
        filtered = self.optimization_history
        
        if strategy_name:
            filtered = [r for r in filtered if r['strategy_name'] == strategy_name]
        
        if bot_name:
            filtered = [r for r in filtered if r['bot_name'] == bot_name]
        
        # Sort by timestamp descending
        filtered = sorted(
            filtered,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        return filtered[:limit]
    
    def _fetch_market_data(self, bot_name: str, strategy_name: str) -> Any:
        """
        Fetch market data for optimization.
        
        This is a placeholder - real implementation would fetch
        actual OHLCV data from database or data provider.
        """
        # TODO: Implement actual market data fetching
        logger.warning("market_data_fetch_not_implemented")
        return None
    
    def _calculate_improvement(
        self,
        new_metrics: Dict[str, float],
        current_params: Dict[str, Any]
    ) -> float:
        """Calculate percentage improvement in Sharpe ratio."""
        # This is simplified - would need to backtest current params
        # For now, assume baseline Sharpe of 1.0
        baseline_sharpe = 1.0
        new_sharpe = new_metrics.get('sharpe', 0)
        
        if baseline_sharpe <= 0:
            return 0.0
        
        improvement = ((new_sharpe - baseline_sharpe) / baseline_sharpe) * 100
        return improvement
    
    def _load_history(self):
        """Load optimization history from disk."""
        try:
            path = Path(self.optimization_history_path)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.optimization_history = data.get('history', [])
                    
                    # Rebuild last_optimization_date
                    for record in self.optimization_history:
                        key = f"{record['bot_name']}:{record['strategy_name']}"
                        timestamp = datetime.fromisoformat(record['timestamp'])
                        
                        if key not in self.last_optimization_date or timestamp > self.last_optimization_date[key]:
                            self.last_optimization_date[key] = timestamp
                
                logger.info(
                    "optimization_history_loaded",
                    records=len(self.optimization_history)
                )
        except Exception as e:
            logger.warning("failed_to_load_history", error=str(e))
            self.optimization_history = []
    
    def _save_history(self):
        """Save optimization history to disk."""
        try:
            path = Path(self.optimization_history_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'history': self.optimization_history,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("optimization_history_saved")
            
        except Exception as e:
            logger.error("failed_to_save_history", error=str(e))
