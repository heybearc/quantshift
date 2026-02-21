#!/usr/bin/env python3
"""
Train ML Regime Classifier

This script trains the ML-based regime classifier on historical SPY data.
Run this monthly to retrain the model with fresh data.

Usage:
    python train_ml_regime_classifier.py [--days 730]
"""

import sys
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, '/opt/quantshift/packages/core/src')

from quantshift_core.ml_regime_classifier import MLRegimeClassifier
import yfinance as yf
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_training_data(symbol: str = 'SPY', days: int = 730):
    """Fetch historical data for training."""
    logger.info(f"Fetching {days} days of {symbol} data from Yahoo Finance")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start_date, end=end_date)
    
    # Normalize column names
    data.columns = [col.lower() for col in data.columns]
    
    logger.info(f"Fetched {len(data)} bars of data")
    
    return data


def main():
    parser = argparse.ArgumentParser(description='Train ML Regime Classifier')
    parser.add_argument(
        '--days',
        type=int,
        default=730,
        help='Days of historical data to use (default: 730 = 2 years)'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='SPY',
        help='Symbol to train on (default: SPY)'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        default='/opt/quantshift/models/regime_classifier.pkl',
        help='Path to save trained model'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("ML Regime Classifier Training")
    logger.info("=" * 60)
    
    # Fetch data
    data = fetch_training_data(args.symbol, args.days)
    
    if data.empty:
        logger.error("Failed to fetch training data")
        return 1
    
    # Initialize classifier
    classifier = MLRegimeClassifier(model_path=args.model_path)
    
    # Train
    logger.info("Starting training...")
    results = classifier.train(data, lookback_days=args.days)
    
    if not results.get('success'):
        logger.error(f"Training failed: {results.get('error')}")
        return 1
    
    # Print results
    logger.info("=" * 60)
    logger.info("Training Results")
    logger.info("=" * 60)
    logger.info(f"Train Accuracy: {results['train_accuracy']:.3f}")
    logger.info(f"Test Accuracy: {results['test_accuracy']:.3f}")
    logger.info(f"CV Mean Accuracy: {results['cv_mean_accuracy']:.3f} ± {results['cv_std_accuracy']:.3f}")
    logger.info("")
    logger.info("Top 5 Features:")
    for feature, importance in sorted(
        results['feature_importance'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        logger.info(f"  {feature}: {importance:.3f}")
    
    logger.info("")
    logger.info("Classification Report:")
    logger.info(results['classification_report'])
    
    logger.info("=" * 60)
    logger.info(f"Model saved to: {args.model_path}")
    logger.info("Training complete!")
    logger.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
