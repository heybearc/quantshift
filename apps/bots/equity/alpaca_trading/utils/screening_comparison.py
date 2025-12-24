"""
A/B Testing utility for comparing old vs new screening criteria.
Allows side-by-side comparison of screening results to measure optimization impact.
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import pandas as pd
import json

logger = logging.getLogger(__name__)

class ScreeningComparison:
    """Compare screening results between different criteria configurations."""
    
    def __init__(self):
        self.comparison_results = []
    
    def compare_criteria(self, screener, symbols_to_test: List[str] = None) -> Dict[str, Any]:
        """
        Compare old vs new screening criteria on the same set of stocks.
        
        Args:
            screener: StockScreener instance with new criteria
            symbols_to_test: Optional list of specific symbols to test
            
        Returns:
            Dict with comparison results
        """
        logger.info("🔬 Starting A/B comparison: Old vs New screening criteria")
        
        # Store current (new) thresholds
        new_thresholds = {
            'rvol_fresh': screener.rvol_fresh_threshold,
            'rvol_continuation': screener.rvol_continuation_threshold,
            'institutional': screener.institutional_ownership_threshold,
            'short_interest': screener.short_interest_threshold
        }
        
        # Old criteria thresholds
        old_thresholds = {
            'rvol_fresh': 1.5,
            'rvol_continuation': 0.8,
            'institutional': 60.0,
            'short_interest': 10.0
        }
        
        # Get test stocks
        if symbols_to_test is None:
            stocks = screener.get_active_stocks(limit=100)  # Test on subset for speed
            symbols_to_test = [s['symbol'] for s in stocks[:50]]  # First 50 for comparison
        
        logger.info(f"Testing {len(symbols_to_test)} stocks with both criteria sets")
        
        # Test with NEW criteria (current settings)
        new_results = self._test_criteria_set(screener, symbols_to_test, new_thresholds, "New")
        
        # Test with OLD criteria
        old_results = self._test_criteria_set(screener, symbols_to_test, old_thresholds, "Old")
        
        # Compare results
        comparison = self._analyze_comparison(old_results, new_results, symbols_to_test)
        
        # Store for historical tracking
        self.comparison_results.append({
            'timestamp': datetime.utcnow().isoformat(),
            'comparison': comparison,
            'old_thresholds': old_thresholds,
            'new_thresholds': new_thresholds
        })
        
        return comparison
    
    def _test_criteria_set(self, screener, symbols: List[str], thresholds: Dict[str, float], label: str) -> Dict[str, Any]:
        """Test a specific set of criteria on given symbols."""
        logger.info(f"Testing {label} criteria...")
        
        # Temporarily set thresholds
        original_thresholds = {
            'rvol_fresh': screener.rvol_fresh_threshold,
            'rvol_continuation': screener.rvol_continuation_threshold,
            'institutional': screener.institutional_ownership_threshold,
            'short_interest': screener.short_interest_threshold
        }
        
        # Apply test thresholds
        screener.rvol_fresh_threshold = thresholds['rvol_fresh']
        screener.rvol_continuation_threshold = thresholds['rvol_continuation']
        screener.institutional_ownership_threshold = thresholds['institutional']
        screener.short_interest_threshold = thresholds['short_interest']
        
        accepted_stocks = []
        rejected_stocks = []
        detailed_results = {}
        
        for symbol in symbols:
            try:
                # Check MA crossover
                ma_result = screener.check_ma_crossover(symbol, mode='auto')
                
                if ma_result:
                    # Get market data and apply enhanced filters
                    bars = screener.get_market_data(symbol)
                    if bars is not None:
                        enhanced_filters = screener.enhanced_stock_filter(symbol, bars)
                        
                        detailed_results[symbol] = {
                            'ma_crossover': True,
                            'enhanced_filters': enhanced_filters,
                            'accepted': enhanced_filters['all_filters_pass']
                        }
                        
                        if enhanced_filters['all_filters_pass']:
                            accepted_stocks.append(symbol)
                        else:
                            rejected_stocks.append(symbol)
                    else:
                        detailed_results[symbol] = {'ma_crossover': True, 'enhanced_filters': None, 'accepted': False}
                        rejected_stocks.append(symbol)
                else:
                    detailed_results[symbol] = {'ma_crossover': False, 'enhanced_filters': None, 'accepted': False}
                    rejected_stocks.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error testing {symbol} with {label} criteria: {e}")
                detailed_results[symbol] = {'error': str(e), 'accepted': False}
                rejected_stocks.append(symbol)
        
        # Restore original thresholds
        screener.rvol_fresh_threshold = original_thresholds['rvol_fresh']
        screener.rvol_continuation_threshold = original_thresholds['rvol_continuation']
        screener.institutional_ownership_threshold = original_thresholds['institutional']
        screener.short_interest_threshold = original_thresholds['short_interest']
        
        return {
            'accepted': accepted_stocks,
            'rejected': rejected_stocks,
            'detailed_results': detailed_results,
            'acceptance_rate': len(accepted_stocks) / len(symbols) * 100 if symbols else 0
        }
    
    def _analyze_comparison(self, old_results: Dict, new_results: Dict, all_symbols: List[str]) -> Dict[str, Any]:
        """Analyze the differences between old and new criteria results."""
        
        old_accepted = set(old_results['accepted'])
        new_accepted = set(new_results['accepted'])
        
        # Find differences
        only_new_accepted = new_accepted - old_accepted  # Stocks accepted only by new criteria
        only_old_accepted = old_accepted - new_accepted  # Stocks accepted only by old criteria
        both_accepted = old_accepted & new_accepted      # Stocks accepted by both
        
        # Calculate metrics
        old_acceptance_rate = len(old_accepted) / len(all_symbols) * 100
        new_acceptance_rate = len(new_accepted) / len(all_symbols) * 100
        improvement_rate = new_acceptance_rate - old_acceptance_rate
        
        # Detailed analysis of newly accepted stocks
        newly_accepted_analysis = {}
        for symbol in only_new_accepted:
            if symbol in new_results['detailed_results']:
                filters = new_results['detailed_results'][symbol].get('enhanced_filters', {})
                newly_accepted_analysis[symbol] = {
                    'rvol': filters.get('rvol', 0),
                    'institutional_pct': filters.get('institutional_ownership_pct', 0),
                    'short_interest_pct': filters.get('short_interest_pct', 0),
                    'atr_pct': filters.get('atr_pct', 0)
                }
        
        comparison = {
            'summary': {
                'total_symbols_tested': len(all_symbols),
                'old_accepted_count': len(old_accepted),
                'new_accepted_count': len(new_accepted),
                'old_acceptance_rate': old_acceptance_rate,
                'new_acceptance_rate': new_acceptance_rate,
                'improvement_rate': improvement_rate,
                'additional_opportunities': len(only_new_accepted),
                'lost_opportunities': len(only_old_accepted)
            },
            'differences': {
                'only_new_accepted': list(only_new_accepted),
                'only_old_accepted': list(only_old_accepted),
                'both_accepted': list(both_accepted),
                'newly_accepted_analysis': newly_accepted_analysis
            },
            'detailed_breakdown': {
                'old_results': old_results,
                'new_results': new_results
            }
        }
        
        # Log summary
        logger.info("📊 A/B Comparison Results:")
        logger.info(f"  • Old criteria acceptance rate: {old_acceptance_rate:.1f}%")
        logger.info(f"  • New criteria acceptance rate: {new_acceptance_rate:.1f}%")
        logger.info(f"  • Improvement: {improvement_rate:+.1f} percentage points")
        logger.info(f"  • Additional opportunities: {len(only_new_accepted)}")
        logger.info(f"  • Lost opportunities: {len(only_old_accepted)}")
        
        if only_new_accepted:
            logger.info(f"  • Newly accepted stocks: {', '.join(list(only_new_accepted)[:5])}{'...' if len(only_new_accepted) > 5 else ''}")
        
        return comparison
    
    def save_comparison_history(self, filepath: str):
        """Save comparison history to JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.comparison_results, f, indent=2)
            logger.info(f"Comparison history saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving comparison history: {e}")
    
    def load_comparison_history(self, filepath: str):
        """Load comparison history from JSON file."""
        try:
            with open(filepath, 'r') as f:
                self.comparison_results = json.load(f)
            logger.info(f"Comparison history loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading comparison history: {e}")
            self.comparison_results = []
