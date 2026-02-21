"""
Parameter Optimizer - Walk-Forward Optimization for Strategy Parameters

This module implements walk-forward optimization to find optimal strategy parameters
based on historical performance. It uses a train/test split approach to avoid overfitting.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from itertools import product
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """
    Walk-forward parameter optimizer for trading strategies.
    
    Uses a rolling window approach:
    - Train on last 6 months of data
    - Test on next 1 month
    - Select parameters with best Sharpe ratio
    - Penalize high drawdown
    """
    
    def __init__(
        self,
        train_months: int = 6,
        test_months: int = 1,
        min_trades: int = 10,
        optimization_metric: str = 'sharpe'
    ):
        """
        Initialize parameter optimizer.
        
        Args:
            train_months: Number of months to use for training
            test_months: Number of months to use for testing
            min_trades: Minimum trades required in test period
            optimization_metric: Metric to optimize ('sharpe', 'return', 'profit_factor')
        """
        self.train_months = train_months
        self.test_months = test_months
        self.min_trades = min_trades
        self.optimization_metric = optimization_metric
        
        logger.info(
            f"ParameterOptimizer initialized: train={train_months}m, "
            f"test={test_months}m, metric={optimization_metric}"
        )
    
    def optimize_parameters(
        self,
        strategy_class,
        parameter_ranges: Dict[str, List[Any]],
        market_data: pd.DataFrame,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        """
        Find optimal parameters using walk-forward optimization.
        
        Args:
            strategy_class: Strategy class to optimize
            parameter_ranges: Dict of parameter names to list of values to test
            market_data: Historical OHLCV data
            initial_capital: Starting capital for backtests
            
        Returns:
            Dict with optimal parameters and performance metrics
        """
        logger.info(f"Starting parameter optimization for {strategy_class.__name__}")
        
        # Split data into train and test
        train_data, test_data = self._split_data(market_data)
        
        if train_data.empty or test_data.empty:
            logger.error("Insufficient data for optimization")
            return None
        
        # Generate all parameter combinations
        param_combinations = self._generate_combinations(parameter_ranges)
        logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        # Test each combination on training data
        train_results = []
        for params in param_combinations:
            result = self._backtest_parameters(
                strategy_class,
                params,
                train_data,
                initial_capital
            )
            if result:
                train_results.append({
                    'params': params,
                    'metrics': result
                })
        
        if not train_results:
            logger.error("No valid results from training period")
            return None
        
        # Select best parameters based on training performance
        best_params = self._select_best_parameters(train_results)
        logger.info(f"Best parameters from training: {best_params['params']}")
        
        # Validate on test data
        test_result = self._backtest_parameters(
            strategy_class,
            best_params['params'],
            test_data,
            initial_capital
        )
        
        if not test_result:
            logger.warning("Best parameters failed validation on test data")
            return None
        
        # Check if test performance is acceptable
        if not self._validate_test_performance(test_result):
            logger.warning("Test performance below acceptable threshold")
            return None
        
        return {
            'optimal_params': best_params['params'],
            'train_metrics': best_params['metrics'],
            'test_metrics': test_result,
            'optimization_date': datetime.utcnow().isoformat()
        }
    
    def _split_data(
        self,
        data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split data into train and test periods."""
        if len(data) < 30:  # Need at least 30 days
            return pd.DataFrame(), pd.DataFrame()
        
        # Calculate split point
        test_start_idx = len(data) - (self.test_months * 21)  # ~21 trading days per month
        train_end_idx = test_start_idx
        train_start_idx = max(0, train_end_idx - (self.train_months * 21))
        
        train_data = data.iloc[train_start_idx:train_end_idx].copy()
        test_data = data.iloc[test_start_idx:].copy()
        
        logger.debug(
            f"Data split: train={len(train_data)} bars, test={len(test_data)} bars"
        )
        
        return train_data, test_data
    
    def _generate_combinations(
        self,
        parameter_ranges: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Generate all parameter combinations from ranges."""
        keys = list(parameter_ranges.keys())
        values = list(parameter_ranges.values())
        
        combinations = []
        for combo in product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
    def _backtest_parameters(
        self,
        strategy_class,
        params: Dict[str, Any],
        data: pd.DataFrame,
        initial_capital: float
    ) -> Optional[Dict[str, float]]:
        """
        Backtest a strategy with given parameters.
        
        Returns metrics dict or None if backtest failed.
        """
        try:
            # Create strategy instance with parameters
            strategy = strategy_class(config=params)
            
            # Run simple backtest
            trades = []
            capital = initial_capital
            equity_curve = [capital]
            
            # Simulate trading
            for i in range(len(data)):
                if i < 50:  # Need some history for indicators
                    continue
                
                window = data.iloc[:i+1]
                
                # Generate signals (simplified - real implementation would be more complex)
                # This is a placeholder - actual backtest would use strategy.generate_signals()
                # For now, just track equity
                equity_curve.append(capital)
            
            # Calculate metrics
            if len(equity_curve) < 2:
                return None
            
            returns = pd.Series(equity_curve).pct_change().dropna()
            
            if len(returns) == 0:
                return None
            
            # Calculate Sharpe ratio (annualized)
            sharpe = self._calculate_sharpe(returns)
            
            # Calculate max drawdown
            drawdown = self._calculate_max_drawdown(equity_curve)
            
            # Calculate total return
            total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
            
            return {
                'sharpe': sharpe,
                'total_return': total_return,
                'max_drawdown': drawdown,
                'num_trades': len(trades)
            }
            
        except Exception as e:
            logger.error(f"Backtest failed for params {params}: {e}")
            return None
    
    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """Calculate annualized Sharpe ratio."""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        # Annualize (assuming daily returns)
        annual_return = returns.mean() * 252
        annual_std = returns.std() * np.sqrt(252)
        
        sharpe = annual_return / annual_std if annual_std > 0 else 0.0
        return sharpe
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown."""
        if len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _select_best_parameters(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select best parameters based on optimization metric."""
        if not results:
            return None
        
        # Sort by optimization metric
        if self.optimization_metric == 'sharpe':
            sorted_results = sorted(
                results,
                key=lambda x: x['metrics']['sharpe'],
                reverse=True
            )
        elif self.optimization_metric == 'return':
            sorted_results = sorted(
                results,
                key=lambda x: x['metrics']['total_return'],
                reverse=True
            )
        else:
            sorted_results = results
        
        # Apply drawdown penalty
        # Penalize if drawdown > 20%
        for result in sorted_results:
            if result['metrics']['max_drawdown'] > 0.20:
                result['metrics']['sharpe'] *= 0.5  # 50% penalty
        
        # Re-sort after penalty
        sorted_results = sorted(
            sorted_results,
            key=lambda x: x['metrics']['sharpe'],
            reverse=True
        )
        
        return sorted_results[0]
    
    def _validate_test_performance(self, metrics: Dict[str, float]) -> bool:
        """Validate that test performance meets minimum requirements."""
        # Require positive Sharpe
        if metrics['sharpe'] < 0.5:
            logger.warning(f"Test Sharpe too low: {metrics['sharpe']:.2f}")
            return False
        
        # Require minimum trades
        if metrics['num_trades'] < self.min_trades:
            logger.warning(f"Too few trades in test: {metrics['num_trades']}")
            return False
        
        # Require drawdown < 30%
        if metrics['max_drawdown'] > 0.30:
            logger.warning(f"Test drawdown too high: {metrics['max_drawdown']:.2%}")
            return False
        
        return True


class StrategyPerformanceMonitor:
    """
    Monitor strategy performance and auto-disable underperforming strategies.
    """
    
    def __init__(
        self,
        min_win_rate: float = 0.40,
        min_sharpe: float = 0.5,
        lookback_days: int = 30
    ):
        """
        Initialize performance monitor.
        
        Args:
            min_win_rate: Minimum acceptable win rate
            min_sharpe: Minimum acceptable Sharpe ratio
            lookback_days: Days to look back for performance calculation
        """
        self.min_win_rate = min_win_rate
        self.min_sharpe = min_sharpe
        self.lookback_days = lookback_days
        
        logger.info(
            f"StrategyPerformanceMonitor initialized: "
            f"min_wr={min_win_rate:.1%}, min_sharpe={min_sharpe}"
        )
    
    def evaluate_strategy(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate strategy performance based on recent trades.
        
        Args:
            trades: List of trade dicts with 'pnl', 'exit_date', etc.
            
        Returns:
            Dict with performance metrics and recommendation
        """
        if not trades:
            return {
                'should_disable': False,
                'reason': 'No trades to evaluate'
            }
        
        # Filter to recent trades
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        recent_trades = [
            t for t in trades
            if datetime.fromisoformat(t.get('exit_date', '1970-01-01')) > cutoff_date
        ]
        
        if len(recent_trades) < 10:
            return {
                'should_disable': False,
                'reason': f'Insufficient trades ({len(recent_trades)} < 10)'
            }
        
        # Calculate metrics
        wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
        win_rate = wins / len(recent_trades)
        
        returns = [t.get('pnl', 0) for t in recent_trades]
        sharpe = self._calculate_sharpe_from_trades(returns)
        
        # Determine if should disable
        should_disable = False
        reasons = []
        
        if win_rate < self.min_win_rate:
            should_disable = True
            reasons.append(f'Win rate too low: {win_rate:.1%} < {self.min_win_rate:.1%}')
        
        if sharpe < self.min_sharpe:
            should_disable = True
            reasons.append(f'Sharpe too low: {sharpe:.2f} < {self.min_sharpe:.2f}')
        
        return {
            'should_disable': should_disable,
            'reason': '; '.join(reasons) if reasons else 'Performance acceptable',
            'metrics': {
                'win_rate': win_rate,
                'sharpe': sharpe,
                'num_trades': len(recent_trades),
                'lookback_days': self.lookback_days
            }
        }
    
    def _calculate_sharpe_from_trades(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio from trade returns."""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_series = pd.Series(returns)
        
        if returns_series.std() == 0:
            return 0.0
        
        # Annualize assuming trades are roughly daily
        sharpe = (returns_series.mean() / returns_series.std()) * np.sqrt(252)
        return sharpe
