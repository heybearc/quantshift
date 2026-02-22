#!/usr/bin/env python3
"""
Train RL Position Sizing Agent

Trains a PPO agent to learn optimal position sizing from historical data.
Supports daily online learning and weekly full retraining.

Usage:
    python train_rl_agent.py [--timesteps 100000] [--days 730]
"""

import sys
import argparse
from datetime import datetime

sys.path.insert(0, '/opt/quantshift/packages/core/src')

from quantshift_core.rl_position_sizer import RLPositionSizer
from quantshift_core.rl_trading_env import prepare_training_data
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Train RL Position Sizing Agent')
    parser.add_argument(
        '--timesteps',
        type=int,
        default=100000,
        help='Training timesteps (default: 100000)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=730,
        help='Days of historical data (default: 730 = 2 years)'
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
        default='/opt/quantshift/models/rl_position_sizer.zip',
        help='Path to save trained model'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("RL Position Sizing Agent Training")
    logger.info("=" * 60)
    
    # Fetch training data
    logger.info(f"Fetching {args.days} days of {args.symbol} data...")
    data = prepare_training_data(symbol=args.symbol, days=args.days)
    
    if data.empty:
        logger.error("Failed to fetch training data")
        return 1
    
    logger.info(f"Training data: {len(data)} bars")
    
    # Initialize RL agent
    logger.info("Initializing RL agent...")
    agent = RLPositionSizer(
        model_path=args.model_path,
        retrain_interval_days=7,  # Weekly retraining
        online_learning=True  # Enable daily learning
    )
    
    # Train
    logger.info(f"Training for {args.timesteps} timesteps...")
    logger.info("This may take 5-10 minutes...")
    
    results = agent.train(
        training_data=data,
        total_timesteps=args.timesteps,
        save_model=True
    )
    
    if not results.get('success'):
        logger.error(f"Training failed: {results.get('error')}")
        return 1
    
    # Print results
    metrics = results.get('metrics', {})
    logger.info("=" * 60)
    logger.info("Training Results")
    logger.info("=" * 60)
    logger.info(f"Total Return: {metrics.get('total_return', 0):.2%}")
    logger.info(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    logger.info(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
    logger.info(f"Win Rate: {metrics.get('win_rate', 0):.2%}")
    logger.info(f"Total Trades: {metrics.get('num_trades', 0)}")
    logger.info(f"Final Equity: ${metrics.get('final_equity', 0):,.2f}")
    logger.info("")
    logger.info(f"Model saved to: {args.model_path}")
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info("=" * 60)
    
    # Performance summary
    summary = agent.get_performance_summary()
    logger.info("")
    logger.info("Agent Configuration:")
    logger.info(f"  Retrain Interval: {summary['retrain_interval_days']} days")
    logger.info(f"  Online Learning: {summary['online_learning_enabled']}")
    logger.info(f"  Last Trained: {summary['last_train_date']}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
