"""
RL Position Sizer - Deep Reinforcement Learning for Position Sizing

Uses PPO (Proximal Policy Optimization) to learn optimal position sizes.
Features daily online learning and weekly full retraining for adaptation.
"""

import logging
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class RLPositionSizer:
    """
    Reinforcement Learning agent for position sizing.
    
    Uses PPO to learn optimal position sizes based on market conditions.
    Supports daily online learning and weekly retraining.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        retrain_interval_days: int = 7,
        online_learning: bool = True,
        fallback_size: float = 0.02
    ):
        """
        Initialize RL position sizer.
        
        Args:
            model_path: Path to saved model (.zip)
            retrain_interval_days: Days between full retraining (default: 7)
            online_learning: Enable daily online learning
            fallback_size: Fallback position size if RL fails (2% of capital)
        """
        self.model_path = model_path or '/opt/quantshift/models/rl_position_sizer.zip'
        self.retrain_interval_days = retrain_interval_days
        self.online_learning = online_learning
        self.fallback_size = fallback_size
        
        self.model = None
        self.last_train_date: Optional[datetime] = None
        self.performance_history = []
        
        # Try to load existing model
        self._load_model()
        
        # Initialize PPO if available
        if self.model is None:
            self._init_model()
        
        logger.info(
            "rl_position_sizer_initialized",
            model_path=self.model_path,
            retrain_interval=retrain_interval_days,
            online_learning=online_learning,
            model_loaded=self.model is not None
        )
    
    def _init_model(self):
        """Initialize PPO model."""
        try:
            from stable_baselines3 import PPO
            from .rl_trading_env import TradingEnvironment, prepare_training_data
            
            # Create dummy environment for model initialization
            # Use max_position_size=1.0 to match training environment
            dummy_data = prepare_training_data(symbol='SPY', days=100)
            dummy_env = TradingEnvironment(dummy_data, max_position_size=1.0)
            
            # Initialize PPO
            self.model = PPO(
                "MlpPolicy",
                dummy_env,
                learning_rate=3e-4,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                verbose=0,
                device='cpu'  # Force CPU to avoid GPU warning
            )
            
            logger.info("ppo_model_initialized")
            
        except ImportError:
            logger.warning(
                "stable_baselines3_unavailable",
                message="Install stable-baselines3 for RL agent"
            )
            self.model = None
        except Exception as e:
            logger.error("ppo_init_failed", error=str(e))
            self.model = None
    
    def get_position_size(
        self,
        market_data: pd.DataFrame,
        account_equity: float,
        current_regime: str,
        sentiment_score: float,
        signal_confidence: float = 1.0
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Get optimal position size using RL agent.
        
        Args:
            market_data: Recent market data with indicators
            account_equity: Current account equity
            current_regime: Market regime (BULL_TRENDING, etc.)
            sentiment_score: Sentiment score (-1 to +1)
            signal_confidence: Strategy signal confidence (0-1)
            
        Returns:
            Tuple of (position_size_pct, metadata)
            position_size_pct: Position size as fraction of equity (0-1)
        """
        if self.model is None:
            # Fallback to fixed sizing
            return self.fallback_size, {'method': 'fallback', 'reason': 'no_model'}
        
        try:
            # Prepare observation
            observation = self._prepare_observation(
                market_data,
                account_equity,
                current_regime,
                sentiment_score
            )
            
            # Get action from model
            action, _states = self.model.predict(observation, deterministic=True)
            
            # Extract position size (action is in [0, max_position_size])
            position_size_pct = float(action[0])
            
            # Apply signal confidence adjustment
            position_size_pct *= signal_confidence
            
            # Clip to reasonable range
            position_size_pct = np.clip(position_size_pct, 0.0, 0.1)  # Max 10% per position
            
            metadata = {
                'method': 'rl_agent',
                'raw_action': float(action[0]),
                'confidence_adjusted': position_size_pct,
                'signal_confidence': signal_confidence
            }
            
            logger.debug(
                "rl_position_sized",
                position_pct=position_size_pct,
                regime=current_regime,
                sentiment=sentiment_score
            )
            
            return position_size_pct, metadata
            
        except Exception as e:
            logger.error("rl_sizing_failed", error=str(e))
            return self.fallback_size, {'method': 'fallback', 'reason': str(e)}
    
    def _prepare_observation(
        self,
        market_data: pd.DataFrame,
        account_equity: float,
        current_regime: str,
        sentiment_score: float
    ) -> np.ndarray:
        """Prepare observation for RL model."""
        from .rl_trading_env import TradingEnvironment
        
        # Get latest row
        latest = market_data.iloc[-1]
        
        # Extract features (same as training environment)
        features = []
        feature_names = [
            'close', 'volume', 'sma_20', 'sma_50', 'sma_200',
            'rsi', 'macd', 'atr', 'bb_upper', 'bb_lower'
        ]
        
        for name in feature_names:
            value = latest.get(name, 0.0)
            features.append(float(value) if not pd.isna(value) else 0.0)
        
        # Add portfolio state (normalized)
        initial_balance = 100000  # Same as training
        features.extend([
            0.0,  # No current position (sizing for new position)
            account_equity / initial_balance,  # Normalized equity
            account_equity / initial_balance   # Normalized total
        ])
        
        # Add regime encoding (one-hot)
        regime_map = {
            'BULL_TRENDING': [1, 0, 0, 0, 0],
            'BEAR_TRENDING': [0, 1, 0, 0, 0],
            'HIGH_VOL_CHOPPY': [0, 0, 1, 0, 0],
            'LOW_VOL_RANGE': [0, 0, 0, 1, 0],
            'CRISIS': [0, 0, 0, 0, 1]
        }
        regime_encoding = regime_map.get(current_regime, [0, 0, 0, 0, 0])
        features.extend(regime_encoding)
        
        # Add sentiment
        features.append(sentiment_score)
        
        return np.array(features, dtype=np.float32)
    
    def train(
        self,
        training_data: pd.DataFrame,
        total_timesteps: int = 100000,
        save_model: bool = True
    ) -> Dict[str, Any]:
        """
        Train RL agent on historical data.
        
        Args:
            training_data: Historical OHLCV data with indicators
            total_timesteps: Number of training steps
            save_model: Save model after training
            
        Returns:
            Training metrics
        """
        if self.model is None:
            logger.error("no_model_to_train")
            return {'success': False, 'error': 'No model initialized'}
        
        try:
            from .rl_trading_env import TradingEnvironment
            
            logger.info(
                "rl_training_started",
                data_length=len(training_data),
                timesteps=total_timesteps
            )
            
            # Create training environment
            env = TradingEnvironment(
                training_data,
                initial_balance=100000,
                max_position_size=1.0,  # Max 100% of capital (will be scaled by strategy)
                transaction_cost=0.001,
                reward_window=30
            )
            
            # Train model
            self.model.set_env(env)
            self.model.learn(total_timesteps=total_timesteps, progress_bar=True)
            
            # Evaluate
            obs, _ = env.reset()
            total_reward = 0
            done = False
            
            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                total_reward += reward
                done = terminated or truncated
            
            metrics = env.get_metrics()
            metrics['total_reward'] = total_reward
            metrics['training_timesteps'] = total_timesteps
            
            # Save model
            if save_model:
                self.last_train_date = datetime.utcnow()
                self._save_model()
            
            logger.info(
                "rl_training_complete",
                sharpe=metrics.get('sharpe_ratio', 0),
                total_return=metrics.get('total_return', 0),
                win_rate=metrics.get('win_rate', 0)
            )
            
            return {'success': True, 'metrics': metrics}
            
        except Exception as e:
            logger.error("rl_training_failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    def online_learn(
        self,
        recent_trades: List[Dict[str, Any]],
        market_data: pd.DataFrame
    ) -> bool:
        """
        Perform online learning from recent trades.
        
        Args:
            recent_trades: Recent trade results
            market_data: Recent market data
            
        Returns:
            True if learning succeeded
        """
        if not self.online_learning or self.model is None:
            return False
        
        try:
            from .rl_trading_env import TradingEnvironment
            
            # Create environment from recent data
            env = TradingEnvironment(
                market_data,
                initial_balance=100000,
                max_position_size=0.1
            )
            
            # Quick learning session (fewer steps)
            self.model.set_env(env)
            self.model.learn(total_timesteps=1000, progress_bar=False)
            
            logger.info(
                "online_learning_complete",
                trades_used=len(recent_trades),
                data_length=len(market_data)
            )
            
            return True
            
        except Exception as e:
            logger.error("online_learning_failed", error=str(e))
            return False
    
    def needs_retraining(self) -> bool:
        """Check if model needs full retraining."""
        if self.model is None or self.last_train_date is None:
            return True
        
        days_since_train = (datetime.utcnow() - self.last_train_date).days
        return days_since_train >= self.retrain_interval_days
    
    def _save_model(self):
        """Save trained model to disk."""
        try:
            model_dir = Path(self.model_path).parent
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Save PPO model
            self.model.save(self.model_path)
            
            # Save metadata
            metadata = {
                'last_train_date': self.last_train_date,
                'retrain_interval_days': self.retrain_interval_days,
                'online_learning': self.online_learning
            }
            
            metadata_path = str(self.model_path).replace('.zip', '_metadata.pkl')
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info("rl_model_saved", path=self.model_path)
            
        except Exception as e:
            logger.error("rl_model_save_failed", error=str(e))
    
    def _load_model(self):
        """Load trained model from disk."""
        try:
            if not Path(self.model_path).exists():
                logger.info("no_existing_rl_model")
                return
            
            from stable_baselines3 import PPO
            
            # Load PPO model
            self.model = PPO.load(self.model_path)
            
            # Load metadata
            metadata_path = str(self.model_path).replace('.zip', '_metadata.pkl')
            if Path(metadata_path).exists():
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                    self.last_train_date = metadata.get('last_train_date')
            
            logger.info("rl_model_loaded", path=self.model_path)
            
            if self.last_train_date:
                days_since_train = (datetime.utcnow() - self.last_train_date).days
                logger.info(f"Model age: {days_since_train} days")
                
                if days_since_train > self.retrain_interval_days:
                    logger.warning("rl_model_stale", days=days_since_train)
            
        except ImportError:
            logger.warning("stable_baselines3_not_installed")
        except Exception as e:
            logger.error("rl_model_load_failed", error=str(e))
            self.model = None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of RL agent."""
        return {
            'model_loaded': self.model is not None,
            'last_train_date': self.last_train_date.isoformat() if self.last_train_date else None,
            'days_since_train': (datetime.utcnow() - self.last_train_date).days if self.last_train_date else None,
            'needs_retraining': self.needs_retraining(),
            'online_learning_enabled': self.online_learning,
            'retrain_interval_days': self.retrain_interval_days
        }
