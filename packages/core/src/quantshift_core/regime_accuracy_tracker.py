"""
Regime Prediction Accuracy Tracker

Tracks ML regime classifier accuracy in production by comparing predictions
with actual market behavior. Compares ML vs rule-based regime detection.

Author: QuantShift Team
Created: 2026-03-04
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import structlog
import json
from pathlib import Path

logger = structlog.get_logger(__name__)


class RegimeAccuracyTracker:
    """
    Track regime prediction accuracy in production.
    
    Compares ML regime predictions with rule-based predictions and
    tracks which method performs better over time.
    """
    
    def __init__(
        self,
        db_manager: Any,
        accuracy_window_days: int = 30,
        comparison_interval_hours: int = 24
    ):
        """
        Initialize regime accuracy tracker.
        
        Args:
            db_manager: Database manager
            accuracy_window_days: Days to calculate accuracy over
            comparison_interval_hours: Hours between ML vs rule comparison
        """
        self.db_manager = db_manager
        self.accuracy_window_days = accuracy_window_days
        self.comparison_interval_hours = comparison_interval_hours
        
        self.last_comparison_time: Optional[datetime] = None
        
        logger.info(
            "regime_accuracy_tracker_initialized",
            window_days=accuracy_window_days,
            comparison_interval=comparison_interval_hours
        )
    
    def record_regime_prediction(
        self,
        bot_name: str,
        regime_ml: str,
        regime_rule_based: str,
        ml_confidence: float,
        market_indicators: Dict[str, float]
    ):
        """
        Record a regime prediction for later accuracy analysis.
        
        Args:
            bot_name: Bot name
            regime_ml: ML-predicted regime
            regime_rule_based: Rule-based predicted regime
            ml_confidence: ML prediction confidence (0-1)
            market_indicators: Market indicators at prediction time
        """
        try:
            with self.db_manager.session() as session:
                session.execute(
                    """
                    INSERT INTO regime_predictions
                    (bot_name, timestamp, regime_ml, regime_rule_based, 
                     ml_confidence, market_indicators, actual_regime, validated)
                    VALUES (:bot_name, :timestamp, :regime_ml, :regime_rule_based,
                            :ml_confidence, :market_indicators, NULL, FALSE)
                    """,
                    {
                        'bot_name': bot_name,
                        'timestamp': datetime.utcnow(),
                        'regime_ml': regime_ml,
                        'regime_rule_based': regime_rule_based,
                        'ml_confidence': ml_confidence,
                        'market_indicators': json.dumps(market_indicators)
                    }
                )
                session.commit()
            
            logger.debug(
                "regime_prediction_recorded",
                bot=bot_name,
                ml_regime=regime_ml,
                rule_regime=regime_rule_based,
                confidence=f"{ml_confidence:.2%}"
            )
            
        except Exception as e:
            logger.error("failed_to_record_regime_prediction", error=str(e))
    
    def validate_predictions(self, bot_name: str) -> Dict[str, Any]:
        """
        Validate past regime predictions based on actual market behavior.
        
        Looks at predictions from 1-7 days ago and validates them based on
        subsequent market performance.
        
        Args:
            bot_name: Bot name
            
        Returns:
            Dict with validation results
        """
        try:
            # Get unvalidated predictions from 1-7 days ago
            cutoff_start = datetime.utcnow() - timedelta(days=7)
            cutoff_end = datetime.utcnow() - timedelta(days=1)
            
            with self.db_manager.session() as session:
                predictions = session.execute(
                    """
                    SELECT id, timestamp, regime_ml, regime_rule_based, market_indicators
                    FROM regime_predictions
                    WHERE bot_name = :bot_name 
                      AND validated = FALSE
                      AND timestamp BETWEEN :start AND :end
                    ORDER BY timestamp ASC
                    """,
                    {
                        'bot_name': bot_name,
                        'start': cutoff_start,
                        'end': cutoff_end
                    }
                ).fetchall()
                
                validated_count = 0
                ml_correct = 0
                rule_correct = 0
                
                for pred in predictions:
                    pred_id, timestamp, regime_ml, regime_rule, indicators_json = pred
                    
                    # Determine actual regime based on subsequent market behavior
                    actual_regime = self._determine_actual_regime(
                        bot_name, 
                        timestamp,
                        json.loads(indicators_json) if indicators_json else {}
                    )
                    
                    if actual_regime:
                        # Update prediction with actual regime
                        session.execute(
                            """
                            UPDATE regime_predictions
                            SET actual_regime = :actual, validated = TRUE, validated_at = :validated_at
                            WHERE id = :id
                            """,
                            {
                                'actual': actual_regime,
                                'validated_at': datetime.utcnow(),
                                'id': pred_id
                            }
                        )
                        
                        validated_count += 1
                        
                        if regime_ml == actual_regime:
                            ml_correct += 1
                        
                        if regime_rule == actual_regime:
                            rule_correct += 1
                
                session.commit()
                
                ml_accuracy = (ml_correct / validated_count * 100) if validated_count > 0 else 0
                rule_accuracy = (rule_correct / validated_count * 100) if validated_count > 0 else 0
                
                logger.info(
                    "regime_predictions_validated",
                    bot=bot_name,
                    validated=validated_count,
                    ml_accuracy=f"{ml_accuracy:.1f}%",
                    rule_accuracy=f"{rule_accuracy:.1f}%"
                )
                
                return {
                    'validated_count': validated_count,
                    'ml_correct': ml_correct,
                    'ml_accuracy': ml_accuracy,
                    'rule_correct': rule_correct,
                    'rule_accuracy': rule_accuracy
                }
                
        except Exception as e:
            logger.error("failed_to_validate_predictions", error=str(e))
            return {
                'validated_count': 0,
                'ml_accuracy': 0,
                'rule_accuracy': 0
            }
    
    def _determine_actual_regime(
        self,
        bot_name: str,
        prediction_time: datetime,
        indicators: Dict[str, float]
    ) -> Optional[str]:
        """
        Determine actual regime based on subsequent market behavior.
        
        Looks at market performance in the 1-3 days after prediction
        to determine what the actual regime was.
        
        Returns:
            Actual regime name or None if cannot determine
        """
        try:
            # Get market data for 1-3 days after prediction
            start_time = prediction_time + timedelta(days=1)
            end_time = prediction_time + timedelta(days=3)
            
            # Fetch actual market performance
            # This is simplified - real implementation would analyze actual price movement
            # For now, use a heuristic based on subsequent regime changes
            
            with self.db_manager.session() as session:
                # Get regime changes after this prediction
                result = session.execute(
                    """
                    SELECT regime, COUNT(*) as count
                    FROM regime_history
                    WHERE bot_name = :bot_name
                      AND timestamp BETWEEN :start AND :end
                    GROUP BY regime
                    ORDER BY count DESC
                    LIMIT 1
                    """,
                    {
                        'bot_name': bot_name,
                        'start': start_time,
                        'end': end_time
                    }
                ).fetchone()
                
                if result:
                    return result[0]
                else:
                    return None
                    
        except Exception as e:
            logger.error("failed_to_determine_actual_regime", error=str(e))
            return None
    
    def get_accuracy_comparison(
        self,
        bot_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get ML vs rule-based accuracy comparison.
        
        Args:
            bot_name: Bot name
            days: Days to look back
            
        Returns:
            Dict with comparison metrics
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            with self.db_manager.session() as session:
                # Get validated predictions
                results = session.execute(
                    """
                    SELECT 
                        regime_ml, regime_rule_based, actual_regime,
                        ml_confidence
                    FROM regime_predictions
                    WHERE bot_name = :bot_name
                      AND validated = TRUE
                      AND timestamp >= :cutoff
                    """,
                    {
                        'bot_name': bot_name,
                        'cutoff': cutoff
                    }
                ).fetchall()
                
                if not results:
                    return {
                        'total_predictions': 0,
                        'ml_accuracy': 0,
                        'rule_accuracy': 0,
                        'ml_better': False,
                        'confidence_correlation': 0
                    }
                
                total = len(results)
                ml_correct = sum(1 for r in results if r[0] == r[2])
                rule_correct = sum(1 for r in results if r[1] == r[2])
                
                ml_accuracy = (ml_correct / total * 100) if total > 0 else 0
                rule_accuracy = (rule_correct / total * 100) if total > 0 else 0
                
                # Calculate confidence correlation
                # (Do high-confidence predictions tend to be more accurate?)
                high_conf_predictions = [r for r in results if r[3] > 0.8]
                high_conf_correct = sum(1 for r in high_conf_predictions if r[0] == r[2])
                high_conf_accuracy = (high_conf_correct / len(high_conf_predictions) * 100) if high_conf_predictions else 0
                
                return {
                    'total_predictions': total,
                    'ml_correct': ml_correct,
                    'ml_accuracy': ml_accuracy,
                    'rule_correct': rule_correct,
                    'rule_accuracy': rule_accuracy,
                    'ml_better': ml_accuracy > rule_accuracy,
                    'accuracy_difference': ml_accuracy - rule_accuracy,
                    'high_confidence_predictions': len(high_conf_predictions),
                    'high_confidence_accuracy': high_conf_accuracy,
                    'confidence_correlation': high_conf_accuracy - ml_accuracy
                }
                
        except Exception as e:
            logger.error("failed_to_get_accuracy_comparison", error=str(e))
            return {
                'total_predictions': 0,
                'ml_accuracy': 0,
                'rule_accuracy': 0
            }
    
    def should_run_comparison(self) -> bool:
        """Check if it's time to run ML vs rule comparison."""
        if self.last_comparison_time is None:
            return True
        
        hours_since = (datetime.utcnow() - self.last_comparison_time).total_seconds() / 3600
        return hours_since >= self.comparison_interval_hours
    
    def run_comparison_analysis(self, bot_name: str) -> Dict[str, Any]:
        """
        Run full comparison analysis between ML and rule-based.
        
        Returns:
            Dict with analysis results and recommendation
        """
        # Validate recent predictions
        validation_results = self.validate_predictions(bot_name)
        
        # Get accuracy comparison
        comparison = self.get_accuracy_comparison(bot_name, days=self.accuracy_window_days)
        
        # Update last comparison time
        self.last_comparison_time = datetime.utcnow()
        
        # Generate recommendation
        recommendation = self._generate_recommendation(comparison)
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'validation': validation_results,
            'comparison': comparison,
            'recommendation': recommendation
        }
        
        logger.info(
            "regime_comparison_analysis_complete",
            bot=bot_name,
            ml_accuracy=f"{comparison['ml_accuracy']:.1f}%",
            rule_accuracy=f"{comparison['rule_accuracy']:.1f}%",
            recommendation=recommendation
        )
        
        return results
    
    def _generate_recommendation(self, comparison: Dict[str, Any]) -> str:
        """Generate recommendation based on comparison results."""
        ml_acc = comparison['ml_accuracy']
        rule_acc = comparison['rule_accuracy']
        diff = comparison.get('accuracy_difference', 0)
        
        if comparison['total_predictions'] < 20:
            return "Insufficient data for recommendation (need 20+ validated predictions)"
        
        if ml_acc > rule_acc + 5:
            return f"ML performing significantly better (+{diff:.1f}%). Continue using ML."
        elif rule_acc > ml_acc + 5:
            return f"Rule-based performing better (+{abs(diff):.1f}%). Consider switching to rule-based or retraining ML model."
        else:
            return f"ML and rule-based performing similarly (diff: {diff:.1f}%). Continue current approach."
