"""
RL Trading Environment - OpenAI Gym Compatible

Custom trading environment for reinforcement learning agents.
Allows RL agents to learn optimal position sizing and trade timing.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import structlog

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    import gym
    from gym import spaces

logger = structlog.get_logger()


class TradingEnvironment(gym.Env):
    """
    OpenAI Gym environment for trading.
    
    State: Price data, indicators, regime, sentiment, portfolio state
    Actions: Position size (0-100% of allocated capital)
    Reward: Sharpe ratio over rolling window
    """
    
    metadata = {'render.modes': ['human']}
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 100000,
        max_position_size: float = 1.0,
        transaction_cost: float = 0.001,
        reward_window: int = 30,
        features: Optional[List[str]] = None
    ):
        """
        Initialize trading environment.
        
        Args:
            data: Historical OHLCV data with indicators
            initial_balance: Starting capital
            max_position_size: Max position as fraction of capital (0-1)
            transaction_cost: Transaction cost as fraction (0.001 = 0.1%)
            reward_window: Days to calculate Sharpe ratio reward
            features: List of feature column names to use
        """
        super().__init__()
        
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.max_position_size = max_position_size
        self.transaction_cost = transaction_cost
        self.reward_window = reward_window
        
        # Feature columns
        if features is None:
            self.features = [
                'close', 'volume', 'sma_20', 'sma_50', 'sma_200',
                'rsi', 'macd', 'atr', 'bb_upper', 'bb_lower'
            ]
        else:
            self.features = features
        
        # Validate features exist
        missing_features = [f for f in self.features if f not in self.data.columns]
        if missing_features:
            logger.warning(
                "missing_features",
                features=missing_features,
                available=list(self.data.columns)
            )
            self.features = [f for f in self.features if f in self.data.columns]
        
        # State space: features + portfolio state (position, cash, equity)
        self.num_features = len(self.features) + 3
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.num_features,),
            dtype=np.float32
        )
        
        # Action space: position size (0 to max_position_size)
        self.action_space = spaces.Box(
            low=0.0,
            high=self.max_position_size,
            shape=(1,),
            dtype=np.float32
        )
        
        # Episode state
        self.current_step = 0
        self.balance = initial_balance
        self.position = 0.0  # Current position size (shares)
        self.entry_price = 0.0
        self.equity_curve = []
        self.returns = []
        self.trades = []
        
        logger.info(
            "trading_env_initialized",
            data_length=len(self.data),
            features=len(self.features),
            initial_balance=initial_balance
        )
    
    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict]:
        """Reset environment to initial state."""
        super().reset(seed=seed)
        
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0.0
        self.entry_price = 0.0
        self.equity_curve = [self.initial_balance]
        self.returns = []
        self.trades = []
        
        return self._get_observation(), {}
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: Position size (0 to max_position_size)
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        # Get current price
        current_price = self.data.iloc[self.current_step]['close']
        
        # Parse action (position size as fraction of capital)
        target_position_pct = float(action[0])
        target_position_pct = np.clip(target_position_pct, 0, self.max_position_size)
        
        # Calculate target position in shares
        available_capital = self.balance + (self.position * current_price if self.position > 0 else 0)
        target_position_value = available_capital * target_position_pct
        target_position_shares = target_position_value / current_price if current_price > 0 else 0
        
        # Execute trade if position changes
        reward = 0.0
        if abs(target_position_shares - self.position) > 0.01:  # Minimum trade size
            # Close existing position
            if self.position != 0:
                exit_value = self.position * current_price
                pnl = exit_value - (self.position * self.entry_price)
                transaction_cost = exit_value * self.transaction_cost
                self.balance += exit_value - transaction_cost
                
                self.trades.append({
                    'step': self.current_step,
                    'type': 'close',
                    'shares': self.position,
                    'price': current_price,
                    'pnl': pnl - transaction_cost
                })
                
                self.position = 0
                self.entry_price = 0
            
            # Open new position
            if target_position_shares > 0:
                position_value = target_position_shares * current_price
                transaction_cost = position_value * self.transaction_cost
                
                if self.balance >= position_value + transaction_cost:
                    self.position = target_position_shares
                    self.entry_price = current_price
                    self.balance -= (position_value + transaction_cost)
                    
                    self.trades.append({
                        'step': self.current_step,
                        'type': 'open',
                        'shares': self.position,
                        'price': current_price,
                        'cost': transaction_cost
                    })
        
        # Calculate current equity
        position_value = self.position * current_price if self.position > 0 else 0
        current_equity = self.balance + position_value
        self.equity_curve.append(current_equity)
        
        # Calculate return
        if len(self.equity_curve) > 1:
            ret = (self.equity_curve[-1] - self.equity_curve[-2]) / self.equity_curve[-2]
            self.returns.append(ret)
        
        # Calculate reward (Sharpe ratio over window)
        if len(self.returns) >= self.reward_window:
            recent_returns = self.returns[-self.reward_window:]
            mean_return = np.mean(recent_returns)
            std_return = np.std(recent_returns)
            
            if std_return > 0:
                sharpe = (mean_return / std_return) * np.sqrt(252)  # Annualized
                reward = sharpe
            else:
                reward = 0.0
        else:
            # Early in episode, use simple return
            reward = self.returns[-1] if self.returns else 0.0
        
        # Move to next step
        self.current_step += 1
        
        # Check if episode is done
        terminated = self.current_step >= len(self.data) - 1
        truncated = current_equity < self.initial_balance * 0.5  # Stop if lost 50%
        
        # Info dict
        info = {
            'equity': current_equity,
            'position': self.position,
            'balance': self.balance,
            'num_trades': len(self.trades),
            'total_return': (current_equity - self.initial_balance) / self.initial_balance
        }
        
        return self._get_observation(), reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """Get current state observation."""
        if self.current_step >= len(self.data):
            self.current_step = len(self.data) - 1
        
        # Get feature values
        row = self.data.iloc[self.current_step]
        feature_values = [row[f] for f in self.features]
        
        # Normalize features (simple min-max)
        feature_values = [float(v) if not pd.isna(v) else 0.0 for v in feature_values]
        
        # Add portfolio state
        current_price = row['close']
        position_value = self.position * current_price if self.position > 0 else 0
        total_equity = self.balance + position_value
        
        portfolio_state = [
            self.position / 100 if self.position > 0 else 0,  # Normalized position
            self.balance / self.initial_balance,  # Normalized cash
            total_equity / self.initial_balance  # Normalized equity
        ]
        
        observation = np.array(feature_values + portfolio_state, dtype=np.float32)
        
        return observation
    
    def render(self, mode='human'):
        """Render environment state."""
        if mode == 'human':
            current_price = self.data.iloc[self.current_step]['close']
            position_value = self.position * current_price
            total_equity = self.balance + position_value
            
            print(f"\n=== Step {self.current_step} ===")
            print(f"Price: ${current_price:.2f}")
            print(f"Position: {self.position:.2f} shares (${position_value:.2f})")
            print(f"Cash: ${self.balance:.2f}")
            print(f"Total Equity: ${total_equity:.2f}")
            print(f"Return: {((total_equity - self.initial_balance) / self.initial_balance * 100):.2f}%")
            print(f"Trades: {len(self.trades)}")
    
    def get_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics for the episode."""
        if len(self.equity_curve) < 2:
            return {}
        
        # Calculate returns
        returns = pd.Series(self.equity_curve).pct_change().dropna()
        
        # Total return
        total_return = (self.equity_curve[-1] - self.equity_curve[0]) / self.equity_curve[0]
        
        # Sharpe ratio
        if len(returns) > 0 and returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe = 0.0
        
        # Max drawdown
        peak = self.equity_curve[0]
        max_dd = 0.0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)
        
        # Win rate
        winning_trades = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
        total_trades = len([t for t in self.trades if 'pnl' in t])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'num_trades': len(self.trades),
            'win_rate': win_rate,
            'final_equity': self.equity_curve[-1]
        }


def prepare_training_data(
    symbol: str = 'SPY',
    days: int = 730,
    add_indicators: bool = True
) -> pd.DataFrame:
    """
    Prepare historical data for RL training.
    
    Args:
        symbol: Trading symbol
        days: Days of historical data
        add_indicators: Add technical indicators
        
    Returns:
        DataFrame with OHLCV + indicators
    """
    import yfinance as yf
    
    # Fetch data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start_date, end=end_date)
    
    # Normalize column names
    data.columns = [col.lower() for col in data.columns]
    
    if add_indicators:
        # Add technical indicators
        data['sma_20'] = data['close'].rolling(20).mean()
        data['sma_50'] = data['close'].rolling(50).mean()
        data['sma_200'] = data['close'].rolling(200).mean()
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = data['close'].ewm(span=12).mean()
        ema_26 = data['close'].ewm(span=26).mean()
        data['macd'] = ema_12 - ema_26
        data['macd_signal'] = data['macd'].ewm(span=9).mean()
        
        # ATR
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(14).mean()
        
        # Bollinger Bands
        bb_sma = data['close'].rolling(20).mean()
        bb_std = data['close'].rolling(20).std()
        data['bb_upper'] = bb_sma + (bb_std * 2)
        data['bb_lower'] = bb_sma - (bb_std * 2)
    
    # Drop NaN rows
    data = data.dropna()
    
    logger.info(
        "training_data_prepared",
        symbol=symbol,
        rows=len(data),
        features=list(data.columns)
    )
    
    return data
