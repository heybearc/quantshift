"""Crypto trading strategies."""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import structlog

logger = structlog.get_logger()


class CryptoStrategy:
    """Base crypto trading strategy."""

    def __init__(self, product_id: str = "BTC-USD") -> None:
        """Initialize strategy."""
        self.product_id = product_id
        logger.info("strategy_initialized", product_id=product_id)

    def calculate_indicators(self, candles: List[Dict]) -> pd.DataFrame:
        """Calculate technical indicators from candles."""
        if not candles:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df['start'] = pd.to_datetime(pd.to_numeric(df['start'], errors='coerce'), unit='s')
        df = df.sort_values('start')
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        # Calculate moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Calculate EMA
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # Calculate MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Calculate ATR (Average True Range)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        return df

    def generate_signal(self, df: pd.DataFrame) -> Optional[str]:
        """Generate trading signal based on indicators."""
        if df.empty or len(df) < 200:
            return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Moving Average Crossover Strategy
        if latest['sma_20'] > latest['sma_50'] and prev['sma_20'] <= prev['sma_50']:
            # Golden cross
            if latest['rsi'] < 70:  # Not overbought
                logger.info("signal_generated", signal="BUY", reason="golden_cross")
                return "BUY"
        
        elif latest['sma_20'] < latest['sma_50'] and prev['sma_20'] >= prev['sma_50']:
            # Death cross
            if latest['rsi'] > 30:  # Not oversold
                logger.info("signal_generated", signal="SELL", reason="death_cross")
                return "SELL"
        
        # RSI Strategy
        if latest['rsi'] < 30 and prev['rsi'] >= 30:
            # Oversold
            logger.info("signal_generated", signal="BUY", reason="rsi_oversold")
            return "BUY"
        
        elif latest['rsi'] > 70 and prev['rsi'] <= 70:
            # Overbought
            logger.info("signal_generated", signal="SELL", reason="rsi_overbought")
            return "SELL"
        
        # MACD Strategy
        if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            # MACD bullish crossover
            logger.info("signal_generated", signal="BUY", reason="macd_bullish")
            return "BUY"
        
        elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            # MACD bearish crossover
            logger.info("signal_generated", signal="SELL", reason="macd_bearish")
            return "SELL"
        
        return None

    def calculate_position_size(
        self,
        account_balance: float,
        current_price: float,
        atr: float,
        risk_percent: float = 0.02
    ) -> float:
        """Calculate position size based on ATR and risk."""
        risk_amount = account_balance * risk_percent
        
        # Use 2x ATR as stop loss distance
        stop_distance = atr * 2
        
        # Calculate position size
        position_size = risk_amount / stop_distance
        
        # Convert to crypto units
        crypto_size = position_size / current_price
        
        logger.info(
            "position_size_calculated",
            account_balance=account_balance,
            risk_amount=risk_amount,
            stop_distance=stop_distance,
            crypto_size=crypto_size
        )
        
        return crypto_size
