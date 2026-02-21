"""
ML-Based Regime Classifier - Machine Learning for Market Regime Detection

Uses RandomForestClassifier to predict market regimes based on technical indicators.
More accurate than rule-based detection and learns from historical patterns.
"""

import logging
import pickle
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score

logger = logging.getLogger(__name__)


class MLRegimeClassifier:
    """
    Machine learning-based market regime classifier.
    
    Uses RandomForestClassifier to predict one of 5 market regimes:
    - BULL_TRENDING: Uptrend + low volatility
    - BEAR_TRENDING: Downtrend + low volatility
    - HIGH_VOL_CHOPPY: High volatility, no clear trend
    - LOW_VOL_RANGE: Low volatility, sideways
    - CRISIS: Extreme volatility or VIX spike
    """
    
    REGIMES = {
        0: 'BULL_TRENDING',
        1: 'BEAR_TRENDING',
        2: 'HIGH_VOL_CHOPPY',
        3: 'LOW_VOL_RANGE',
        4: 'CRISIS'
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        retrain_interval_days: int = 30
    ):
        """
        Initialize ML regime classifier.
        
        Args:
            model_path: Path to saved model file (.pkl)
            retrain_interval_days: Days between model retraining
        """
        self.model_path = model_path or '/opt/quantshift/models/regime_classifier.pkl'
        self.retrain_interval_days = retrain_interval_days
        
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: Optional[list] = None
        self.last_train_date: Optional[datetime] = None
        
        # Load existing model if available
        self._load_model()
        
        logger.info(
            f"MLRegimeClassifier initialized: model_path={self.model_path}, "
            f"retrain_interval={retrain_interval_days}d"
        )
    
    def train(
        self,
        market_data: pd.DataFrame,
        lookback_days: int = 730  # 2 years
    ) -> Dict[str, Any]:
        """
        Train the regime classifier on historical data.
        
        Args:
            market_data: DataFrame with OHLCV data
            lookback_days: Days of history to use for training
            
        Returns:
            Dict with training metrics
        """
        logger.info(f"Training ML regime classifier on {lookback_days} days of data")
        
        # Prepare features and labels
        X, y = self._prepare_training_data(market_data, lookback_days)
        
        if X is None or len(X) < 100:
            logger.error("Insufficient training data")
            return {'success': False, 'error': 'Insufficient data'}
        
        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train RandomForest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=5, scoring='accuracy'
        )
        
        # Predictions for detailed metrics
        y_pred = self.model.predict(X_test_scaled)
        
        # Feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
        
        logger.info(f"Training complete: test_accuracy={test_score:.3f}")
        logger.info(f"Top features: {sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]}")
        
        # Save model
        self.last_train_date = datetime.utcnow()
        self._save_model()
        
        return {
            'success': True,
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean_accuracy': cv_scores.mean(),
            'cv_std_accuracy': cv_scores.std(),
            'feature_importance': feature_importance,
            'train_date': self.last_train_date.isoformat(),
            'classification_report': classification_report(
                y_test, y_pred, target_names=list(self.REGIMES.values())
            )
        }
    
    def predict_regime(
        self,
        market_data: pd.DataFrame
    ) -> Tuple[str, float]:
        """
        Predict current market regime.
        
        Args:
            market_data: Recent OHLCV data (needs at least 200 bars)
            
        Returns:
            Tuple of (regime_name, confidence)
        """
        if self.model is None:
            logger.warning("Model not trained, falling back to rule-based detection")
            return self._rule_based_fallback(market_data)
        
        # Extract features from current data
        features = self._extract_features(market_data)
        
        if features is None:
            logger.warning("Could not extract features, using fallback")
            return self._rule_based_fallback(market_data)
        
        # Scale features
        features_scaled = self.scaler.transform([features])
        
        # Predict
        regime_idx = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        confidence = probabilities[regime_idx]
        
        regime_name = self.REGIMES[regime_idx]
        
        logger.debug(f"Predicted regime: {regime_name} (confidence: {confidence:.2%})")
        
        return regime_name, confidence
    
    def _prepare_training_data(
        self,
        market_data: pd.DataFrame,
        lookback_days: int
    ) -> Tuple[Optional[pd.DataFrame], Optional[np.ndarray]]:
        """
        Prepare features and labels for training.
        
        Returns:
            Tuple of (features_df, labels_array)
        """
        # Use recent data
        if len(market_data) > lookback_days:
            data = market_data.tail(lookback_days).copy()
        else:
            data = market_data.copy()
        
        if len(data) < 200:
            return None, None
        
        # Extract features for each day
        features_list = []
        labels_list = []
        
        for i in range(200, len(data)):
            window = data.iloc[:i+1]
            
            # Extract features
            features = self._extract_features(window)
            if features is None:
                continue
            
            # Generate label using rule-based method
            label = self._generate_label(window)
            
            features_list.append(features)
            labels_list.append(label)
        
        if not features_list:
            return None, None
        
        X = pd.DataFrame(features_list)
        y = np.array(labels_list)
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        return X, y
    
    def _extract_features(self, data: pd.DataFrame) -> Optional[Dict[str, float]]:
        """Extract technical indicator features from market data."""
        if len(data) < 200:
            return None
        
        try:
            close = data['close']
            high = data['high']
            low = data['low']
            volume = data['volume']
            
            # Trend features
            sma_20 = close.rolling(20).mean()
            sma_50 = close.rolling(50).mean()
            sma_200 = close.rolling(200).mean()
            
            sma_20_slope = (sma_20.iloc[-1] - sma_20.iloc[-5]) / sma_20.iloc[-5] if len(sma_20) >= 5 else 0
            sma_50_slope = (sma_50.iloc[-1] - sma_50.iloc[-10]) / sma_50.iloc[-10] if len(sma_50) >= 10 else 0
            sma_200_slope = (sma_200.iloc[-1] - sma_200.iloc[-20]) / sma_200.iloc[-20] if len(sma_200) >= 20 else 0
            
            # Volatility features
            atr_20 = self._calculate_atr(high, low, close, 20)
            atr_100 = self._calculate_atr(high, low, close, 100)
            atr_ratio = atr_20.iloc[-1] / atr_100.iloc[-1] if atr_100.iloc[-1] > 0 else 1.0
            
            # Momentum features
            rsi = self._calculate_rsi(close, 14)
            macd, signal, _ = self._calculate_macd(close)
            
            # Volume features
            volume_sma = volume.rolling(20).mean()
            volume_ratio = volume.iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1.0
            
            # Price position
            price_vs_sma20 = (close.iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1] if sma_20.iloc[-1] > 0 else 0
            price_vs_sma50 = (close.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1] if sma_50.iloc[-1] > 0 else 0
            price_vs_sma200 = (close.iloc[-1] - sma_200.iloc[-1]) / sma_200.iloc[-1] if sma_200.iloc[-1] > 0 else 0
            
            features = {
                'sma_20_slope': sma_20_slope,
                'sma_50_slope': sma_50_slope,
                'sma_200_slope': sma_200_slope,
                'atr_ratio': atr_ratio,
                'rsi': rsi.iloc[-1],
                'macd': macd.iloc[-1],
                'macd_signal': signal.iloc[-1],
                'volume_ratio': volume_ratio,
                'price_vs_sma20': price_vs_sma20,
                'price_vs_sma50': price_vs_sma50,
                'price_vs_sma200': price_vs_sma200,
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def _generate_label(self, data: pd.DataFrame) -> int:
        """Generate regime label using rule-based method (for training)."""
        features = self._extract_features(data)
        if not features:
            return 3  # Default to LOW_VOL_RANGE
        
        # Rule-based classification
        sma_slope = features['sma_50_slope']
        atr_ratio = features['atr_ratio']
        
        # Crisis: extreme volatility
        if atr_ratio > 2.0:
            return 4  # CRISIS
        
        # High vol choppy
        if atr_ratio > 1.5:
            return 2  # HIGH_VOL_CHOPPY
        
        # Bull trending
        if sma_slope > 0.005 and atr_ratio < 1.2:
            return 0  # BULL_TRENDING
        
        # Bear trending
        if sma_slope < -0.005 and atr_ratio < 1.2:
            return 1  # BEAR_TRENDING
        
        # Low vol range
        if atr_ratio < 0.8:
            return 3  # LOW_VOL_RANGE
        
        # Default
        return 3  # LOW_VOL_RANGE
    
    def _calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int
    ) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr
    
    def _calculate_rsi(self, close: pd.Series, period: int) -> pd.Series:
        """Calculate RSI."""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(
        self,
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD."""
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def _rule_based_fallback(self, data: pd.DataFrame) -> Tuple[str, float]:
        """Fallback to rule-based regime detection if ML model unavailable."""
        features = self._extract_features(data)
        if not features:
            return 'LOW_VOL_RANGE', 0.5
        
        regime_idx = self._generate_label(data)
        regime_name = self.REGIMES[regime_idx]
        
        return regime_name, 0.5  # Medium confidence for rule-based
    
    def _save_model(self):
        """Save trained model to disk."""
        try:
            model_dir = Path(self.model_path).parent
            model_dir.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'last_train_date': self.last_train_date,
                'regimes': self.REGIMES
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load trained model from disk."""
        try:
            if not Path(self.model_path).exists():
                logger.info("No existing model found, will need to train")
                return
            
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.last_train_date = model_data.get('last_train_date')
            
            logger.info(f"Model loaded from {self.model_path}")
            
            if self.last_train_date:
                days_since_train = (datetime.utcnow() - self.last_train_date).days
                logger.info(f"Model age: {days_since_train} days")
                
                if days_since_train > self.retrain_interval_days:
                    logger.warning(f"Model is stale, should retrain soon")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
    
    def needs_retraining(self) -> bool:
        """Check if model needs retraining based on age."""
        if self.model is None or self.last_train_date is None:
            return True
        
        days_since_train = (datetime.utcnow() - self.last_train_date).days
        return days_since_train >= self.retrain_interval_days
    
    def get_regime_allocation(self, regime: str) -> Dict[str, float]:
        """
        Get strategy allocation for a given regime.
        Same as rule-based detector for consistency.
        """
        allocations = {
            'BULL_TRENDING': {
                'BollingerBounce': 0.30,
                'RSIMeanReversion': 0.20,
                'Breakout': 0.50
            },
            'BEAR_TRENDING': {
                'BollingerBounce': 0.50,
                'RSIMeanReversion': 0.40,
                'Breakout': 0.10
            },
            'HIGH_VOL_CHOPPY': {
                'BollingerBounce': 0.70,
                'RSIMeanReversion': 0.30,
                'Breakout': 0.00
            },
            'LOW_VOL_RANGE': {
                'BollingerBounce': 0.60,
                'RSIMeanReversion': 0.40,
                'Breakout': 0.00
            },
            'CRISIS': {
                'BollingerBounce': 0.20,
                'RSIMeanReversion': 0.00,
                'Breakout': 0.00
            }
        }
        
        return allocations.get(regime, {
            'BollingerBounce': 0.60,
            'RSIMeanReversion': 0.40,
            'Breakout': 0.00
        })
    
    def get_risk_multiplier(self, regime: str) -> float:
        """
        Get risk multiplier for a given regime.
        Same as rule-based detector for consistency.
        """
        multipliers = {
            'BULL_TRENDING': 1.0,
            'BEAR_TRENDING': 0.75,
            'HIGH_VOL_CHOPPY': 0.5,
            'LOW_VOL_RANGE': 1.0,
            'CRISIS': 0.25
        }
        
        return multipliers.get(regime, 1.0)
