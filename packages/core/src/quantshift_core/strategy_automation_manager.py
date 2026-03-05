"""
Strategy Automation Manager - Automated Strategy Enable/Disable

Monitors strategy performance and automatically enables/disables strategies
based on performance metrics. Integrates with StrategyPerformanceMonitor
from parameter_optimizer.py.

Author: QuantShift Team
Created: 2026-03-04
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import structlog
import json

from .parameter_optimizer import StrategyPerformanceMonitor

logger = structlog.get_logger(__name__)


class StrategyAutomationManager:
    """
    Automated strategy enable/disable manager.
    
    Monitors strategy performance and automatically disables underperforming
    strategies, re-enables when performance improves.
    """
    
    def __init__(
        self,
        db_manager: Any,
        min_win_rate: float = 0.40,
        min_sharpe: float = 0.5,
        lookback_days: int = 30,
        min_trades_for_evaluation: int = 10,
        reenable_check_days: int = 7
    ):
        """
        Initialize automation manager.
        
        Args:
            db_manager: Database manager
            min_win_rate: Minimum acceptable win rate (0.40 = 40%)
            min_sharpe: Minimum acceptable Sharpe ratio
            lookback_days: Days to look back for performance
            min_trades_for_evaluation: Minimum trades needed
            reenable_check_days: Days between re-enable checks
        """
        self.db_manager = db_manager
        self.min_win_rate = min_win_rate
        self.min_sharpe = min_sharpe
        self.lookback_days = lookback_days
        self.min_trades_for_evaluation = min_trades_for_evaluation
        self.reenable_check_days = reenable_check_days
        
        self.performance_monitor = StrategyPerformanceMonitor(
            min_win_rate=min_win_rate,
            min_sharpe=min_sharpe,
            lookback_days=lookback_days
        )
        
        self.disabled_strategies: Dict[str, datetime] = {}
        
        logger.info(
            "strategy_automation_manager_initialized",
            min_win_rate=min_win_rate,
            min_sharpe=min_sharpe,
            lookback_days=lookback_days
        )
    
    def evaluate_and_update_strategies(
        self,
        bot_name: str,
        strategy_names: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate all strategies and update their enabled status.
        
        Args:
            bot_name: Bot name
            strategy_names: List of strategy names to evaluate
            
        Returns:
            Dict with evaluation results and actions taken
        """
        results = {
            'evaluated': [],
            'disabled': [],
            'enabled': [],
            'no_action': []
        }
        
        for strategy_name in strategy_names:
            try:
                action = self._evaluate_strategy(bot_name, strategy_name)
                
                results['evaluated'].append({
                    'strategy': strategy_name,
                    'action': action['action'],
                    'reason': action['reason']
                })
                
                if action['action'] == 'disable':
                    results['disabled'].append(strategy_name)
                elif action['action'] == 'enable':
                    results['enabled'].append(strategy_name)
                else:
                    results['no_action'].append(strategy_name)
                    
            except Exception as e:
                logger.error(
                    "strategy_evaluation_failed",
                    strategy=strategy_name,
                    error=str(e)
                )
        
        logger.info(
            "strategy_evaluation_complete",
            bot=bot_name,
            disabled=len(results['disabled']),
            enabled=len(results['enabled']),
            no_action=len(results['no_action'])
        )
        
        return results
    
    def _evaluate_strategy(
        self,
        bot_name: str,
        strategy_name: str
    ) -> Dict[str, str]:
        """
        Evaluate a single strategy and take action.
        
        Returns:
            Dict with action and reason
        """
        key = f"{bot_name}:{strategy_name}"
        
        # Get current enabled status
        current_status = self._get_strategy_status(bot_name, strategy_name)
        
        # Fetch recent trades
        try:
            trades = self.db_manager.get_closed_trades(
                bot_name=bot_name,
                strategy_name=strategy_name,
                limit=100
            )
            
            # Convert to format expected by performance monitor
            trade_list = [
                {
                    'pnl': trade.realized_pnl,
                    'exit_date': trade.exit_time.isoformat() if trade.exit_time else datetime.utcnow().isoformat()
                }
                for trade in trades
            ]
            
        except Exception as e:
            logger.error("failed_to_fetch_trades", strategy=strategy_name, error=str(e))
            return {'action': 'no_action', 'reason': f'Error fetching trades: {str(e)}'}
        
        # Evaluate performance
        evaluation = self.performance_monitor.evaluate_strategy(trade_list)
        
        # Decide action based on current status and evaluation
        if current_status == 'enabled':
            if evaluation['should_disable']:
                # Disable the strategy
                self._disable_strategy(bot_name, strategy_name, evaluation['reason'])
                self.disabled_strategies[key] = datetime.utcnow()
                
                return {
                    'action': 'disable',
                    'reason': evaluation['reason']
                }
            else:
                return {
                    'action': 'no_action',
                    'reason': evaluation['reason']
                }
        
        elif current_status == 'disabled':
            # Check if we should re-evaluate for re-enabling
            if key in self.disabled_strategies:
                days_disabled = (datetime.utcnow() - self.disabled_strategies[key]).days
                
                if days_disabled >= self.reenable_check_days:
                    # Re-evaluate for re-enabling
                    if not evaluation['should_disable']:
                        # Performance improved, re-enable
                        self._enable_strategy(bot_name, strategy_name, "Performance improved")
                        del self.disabled_strategies[key]
                        
                        return {
                            'action': 'enable',
                            'reason': 'Performance improved after ' + str(days_disabled) + ' days'
                        }
            
            return {
                'action': 'no_action',
                'reason': 'Strategy disabled, waiting for re-evaluation period'
            }
        
        return {'action': 'no_action', 'reason': 'Unknown status'}
    
    def _get_strategy_status(self, bot_name: str, strategy_name: str) -> str:
        """
        Get current enabled/disabled status of a strategy.
        
        Returns:
            'enabled' or 'disabled'
        """
        try:
            with self.db_manager.session() as session:
                result = session.execute(
                    """
                    SELECT enabled FROM strategy_status
                    WHERE bot_name = :bot_name AND strategy_name = :strategy_name
                    """,
                    {'bot_name': bot_name, 'strategy_name': strategy_name}
                ).fetchone()
                
                if result:
                    return 'enabled' if result[0] else 'disabled'
                else:
                    # Default to enabled if no record
                    return 'enabled'
                    
        except Exception as e:
            logger.error("failed_to_get_strategy_status", error=str(e))
            return 'enabled'  # Default to enabled on error
    
    def _disable_strategy(
        self,
        bot_name: str,
        strategy_name: str,
        reason: str
    ):
        """Disable a strategy in the database."""
        try:
            with self.db_manager.session() as session:
                session.execute(
                    """
                    INSERT INTO strategy_status 
                    (bot_name, strategy_name, enabled, disabled_reason, disabled_at, updated_at)
                    VALUES (:bot_name, :strategy_name, FALSE, :reason, :disabled_at, :updated_at)
                    ON CONFLICT (bot_name, strategy_name)
                    DO UPDATE SET
                        enabled = FALSE,
                        disabled_reason = :reason,
                        disabled_at = :disabled_at,
                        updated_at = :updated_at
                    """,
                    {
                        'bot_name': bot_name,
                        'strategy_name': strategy_name,
                        'reason': reason,
                        'disabled_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                )
                session.commit()
            
            logger.warning(
                "strategy_auto_disabled",
                bot=bot_name,
                strategy=strategy_name,
                reason=reason
            )
            
        except Exception as e:
            logger.error("failed_to_disable_strategy", error=str(e))
    
    def _enable_strategy(
        self,
        bot_name: str,
        strategy_name: str,
        reason: str
    ):
        """Enable a strategy in the database."""
        try:
            with self.db_manager.session() as session:
                session.execute(
                    """
                    INSERT INTO strategy_status 
                    (bot_name, strategy_name, enabled, enabled_reason, enabled_at, updated_at)
                    VALUES (:bot_name, :strategy_name, TRUE, :reason, :enabled_at, :updated_at)
                    ON CONFLICT (bot_name, strategy_name)
                    DO UPDATE SET
                        enabled = TRUE,
                        enabled_reason = :reason,
                        enabled_at = :enabled_at,
                        disabled_reason = NULL,
                        disabled_at = NULL,
                        updated_at = :updated_at
                    """,
                    {
                        'bot_name': bot_name,
                        'strategy_name': strategy_name,
                        'reason': reason,
                        'enabled_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                )
                session.commit()
            
            logger.info(
                "strategy_auto_enabled",
                bot=bot_name,
                strategy=strategy_name,
                reason=reason
            )
            
        except Exception as e:
            logger.error("failed_to_enable_strategy", error=str(e))
    
    def get_disabled_strategies(self, bot_name: str) -> List[Dict[str, Any]]:
        """
        Get list of currently disabled strategies.
        
        Returns:
            List of dicts with strategy info
        """
        try:
            with self.db_manager.session() as session:
                results = session.execute(
                    """
                    SELECT strategy_name, disabled_reason, disabled_at
                    FROM strategy_status
                    WHERE bot_name = :bot_name AND enabled = FALSE
                    ORDER BY disabled_at DESC
                    """,
                    {'bot_name': bot_name}
                ).fetchall()
                
                return [
                    {
                        'strategy_name': row[0],
                        'disabled_reason': row[1],
                        'disabled_at': row[2].isoformat() if row[2] else None
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error("failed_to_get_disabled_strategies", error=str(e))
            return []
    
    def manually_enable_strategy(
        self,
        bot_name: str,
        strategy_name: str
    ) -> bool:
        """
        Manually enable a strategy (admin override).
        
        Returns:
            True if successful
        """
        try:
            self._enable_strategy(bot_name, strategy_name, "Manual admin override")
            
            # Remove from disabled tracking
            key = f"{bot_name}:{strategy_name}"
            if key in self.disabled_strategies:
                del self.disabled_strategies[key]
            
            return True
            
        except Exception as e:
            logger.error("manual_enable_failed", error=str(e))
            return False
    
    def manually_disable_strategy(
        self,
        bot_name: str,
        strategy_name: str,
        reason: str = "Manual admin disable"
    ) -> bool:
        """
        Manually disable a strategy (admin override).
        
        Returns:
            True if successful
        """
        try:
            self._disable_strategy(bot_name, strategy_name, reason)
            
            # Add to disabled tracking
            key = f"{bot_name}:{strategy_name}"
            self.disabled_strategies[key] = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error("manual_disable_failed", error=str(e))
            return False
