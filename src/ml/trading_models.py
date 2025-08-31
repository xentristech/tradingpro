"""
Machine Learning Models for Algorithmic Trading
Includes XGBoost, LSTM, and ensemble methods for price prediction
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
import joblib
from datetime import datetime, timedelta

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class MLPrediction:
    """ML model prediction result"""
    predicted_price: float
    predicted_direction: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    feature_importance: Dict[str, float]
    model_name: str

class TradingMLPipeline:
    """
    Complete ML pipeline for trading signal generation
    """
    
    def __init__(self, 
                 lookback_period: int = 50,
                 prediction_horizon: int = 5,
                 train_test_split: float = 0.8):
        """
        Initialize ML pipeline
        
        Args:
            lookback_period: Number of periods for feature generation
            prediction_horizon: Periods ahead to predict
            train_test_split: Train/test data split ratio
        """
        self.lookback_period = lookback_period
        self.prediction_horizon = prediction_horizon
        self.train_test_split = train_test_split
        
        # Models will be initialized when training
        self.models = {}
        self.feature_columns = []
        self.scaler = None
        
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create advanced features for ML models
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with engineered features
        """
        features = pd.DataFrame(index=data.index)
        
        # Price features
        features['returns'] = data['close'].pct_change()
        features['log_returns'] = np.log(data['close'] / data['close'].shift(1))
        features['price_to_sma20'] = data['close'] / data['close'].rolling(20).mean()
        features['price_to_sma50'] = data['close'] / data['close'].rolling(50).mean()
        
        # Volatility features
        features['volatility_20'] = features['returns'].rolling(20).std()
        features['volatility_50'] = features['returns'].rolling(50).std()
        features['volatility_ratio'] = features['volatility_20'] / features['volatility_50']
        
        # Volume features
        features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
        features['volume_trend'] = data['volume'].rolling(5).mean() / data['volume'].rolling(20).mean()
        
        # Technical indicators
        features['rsi'] = self._calculate_rsi(data['close'])
        features['macd'], features['macd_signal'] = self._calculate_macd(data['close'])
        features['bb_upper'], features['bb_lower'], features['bb_ratio'] = self._calculate_bollinger_bands(data['close'])
        
        # Market microstructure (if available)
        if 'bid' in data.columns and 'ask' in data.columns:
            features['spread'] = data['ask'] - data['bid']
            features['spread_pct'] = features['spread'] / data['close']
            features['mid_price'] = (data['bid'] + data['ask']) / 2
            features['price_to_mid'] = data['close'] / features['mid_price']
        
        # Lag features
        for lag in [1, 5, 10, 20]:
            features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
            features[f'volume_lag_{lag}'] = features['volume_ratio'].shift(lag)
        
        # Rolling statistics
        for window in [5, 10, 20]:
            features[f'return_mean_{window}'] = features['returns'].rolling(window).mean()
            features[f'return_std_{window}'] = features['returns'].rolling(window).std()
            features[f'return_skew_{window}'] = features['returns'].rolling(window).skew()
            features[f'return_kurt_{window}'] = features['returns'].rolling(window).kurt()
        
        # Time features (if datetime index)
        if isinstance(data.index, pd.DatetimeIndex):
            features['hour'] = data.index.hour
            features['day_of_week'] = data.index.dayofweek
            features['day_of_month'] = data.index.day
            features['month'] = data.index.month
            features['quarter'] = data.index.quarter
            
            # Cyclical encoding for time features
            features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
            features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
            features['dow_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
            features['dow_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)
        
        # Market regime features
        features['trend_strength'] = self._calculate_trend_strength(data['close'])
        features['regime'] = self._detect_regime(features['returns'])
        
        # Drop NaN values
        features = features.dropna()
        
        return features
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD and signal line"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        rolling_mean = prices.rolling(window).mean()
        rolling_std = prices.rolling(window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        bb_ratio = (prices - lower_band) / (upper_band - lower_band)
        return upper_band, lower_band, bb_ratio
    
    def _calculate_trend_strength(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """Calculate trend strength using linear regression"""
        def trend(x):
            if len(x) < 2:
                return 0
            y = np.arange(len(x))
            coef = np.polyfit(y, x, 1)[0]
            return coef / np.mean(x) if np.mean(x) != 0 else 0
        
        return prices.rolling(window).apply(trend, raw=False)
    
    def _detect_regime(self, returns: pd.Series, window: int = 50) -> pd.Series:
        """Detect market regime"""
        def classify_regime(x):
            if len(x) < 2:
                return 0
            vol = x.std()
            trend = x.mean()
            
            if vol < np.percentile(returns.rolling(window).std().dropna(), 30):
                return 1  # Low volatility
            elif vol > np.percentile(returns.rolling(window).std().dropna(), 70):
                return 3  # High volatility
            else:
                return 2  # Normal volatility
        
        return returns.rolling(window).apply(classify_regime, raw=False)
    
    def prepare_data(self, features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for ML models
        
        Returns:
            X, y arrays for training
        """
        # Create target variable (future returns)
        y = features['returns'].shift(-self.prediction_horizon)
        
        # Remove target from features
        X = features.drop(['returns'], axis=1, errors='ignore')
        
        # Align X and y
        valid_idx = y.notna()
        X = X[valid_idx]
        y = y[valid_idx]
        
        # Convert categorical features if any
        for col in X.select_dtypes(include=['object']).columns:
            X[col] = pd.Categorical(X[col]).codes
        
        return X.values, y.values
    
    def train_xgboost(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Train XGBoost model"""
        try:
            import xgboost as xgb
            
            # Convert to classification problem
            y_class = np.where(y_train > 0, 1, 0)
            
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.01,
                objective='binary:logistic',
                use_label_encoder=False,
                random_state=42
            )
            
            model.fit(X_train, y_class)
            
            logger.info("XGBoost model trained successfully")
            return model
            
        except ImportError:
            logger.warning("XGBoost not installed. Skipping XGBoost model.")
            return None
    
    def train_random_forest(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Train Random Forest model"""
        from sklearn.ensemble import RandomForestClassifier
        
        # Convert to classification problem
        y_class = np.where(y_train > 0, 1, 0)
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_class)
        
        logger.info("Random Forest model trained successfully")
        return model
    
    def train_neural_network(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Train simple neural network"""
        try:
            from sklearn.neural_network import MLPClassifier
            
            # Convert to classification problem
            y_class = np.where(y_train > 0, 1, 0)
            
            model = MLPClassifier(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                solver='adam',
                max_iter=500,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )
            
            model.fit(X_train, y_class)
            
            logger.info("Neural Network model trained successfully")
            return model
            
        except Exception as e:
            logger.warning(f"Failed to train neural network: {e}")
            return None
    
    def train_ensemble(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train ensemble of models
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary of trained models
        """
        # Create features
        features = self.create_features(data)
        self.feature_columns = features.columns.tolist()
        
        # Prepare data
        X, y = self.prepare_data(features)
        
        # Split data
        split_idx = int(len(X) * self.train_test_split)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Normalize features
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        X_train = self.scaler.fit_transform(X_train)
        X_test = self.scaler.transform(X_test)
        
        # Train models
        models = {}
        
        # XGBoost
        xgb_model = self.train_xgboost(X_train, y_train)
        if xgb_model:
            models['xgboost'] = xgb_model
        
        # Random Forest
        rf_model = self.train_random_forest(X_train, y_train)
        models['random_forest'] = rf_model
        
        # Neural Network
        nn_model = self.train_neural_network(X_train, y_train)
        if nn_model:
            models['neural_network'] = nn_model
        
        # Evaluate models
        for name, model in models.items():
            if model:
                score = model.score(X_test, np.where(y_test > 0, 1, 0))
                logger.info(f"{name} accuracy: {score:.4f}")
        
        self.models = models
        return models
    
    def predict(self, current_data: pd.DataFrame) -> MLPrediction:
        """
        Make prediction using ensemble of models
        
        Args:
            current_data: Current market data
            
        Returns:
            MLPrediction object
        """
        if not self.models:
            raise ValueError("Models not trained. Call train_ensemble first.")
        
        # Create features
        features = self.create_features(current_data)
        
        # Ensure we have the same features as training
        X = features[self.feature_columns].iloc[-1:].values
        
        # Scale features
        if self.scaler:
            X = self.scaler.transform(X)
        
        # Get predictions from each model
        predictions = []
        confidences = []
        
        for name, model in self.models.items():
            if model:
                # Get prediction
                pred = model.predict(X)[0]
                predictions.append(pred)
                
                # Get confidence (probability)
                if hasattr(model, 'predict_proba'):
                    prob = model.predict_proba(X)[0]
                    confidence = max(prob)
                    confidences.append(confidence)
                else:
                    confidences.append(0.5)
        
        # Ensemble prediction (majority vote)
        ensemble_pred = 1 if sum(predictions) > len(predictions) / 2 else 0
        
        # Average confidence
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        # Determine direction
        if ensemble_pred == 1 and avg_confidence > 0.6:
            direction = 'BUY'
        elif ensemble_pred == 0 and avg_confidence > 0.6:
            direction = 'SELL'
        else:
            direction = 'HOLD'
        
        # Feature importance (from first model with feature_importances_)
        feature_importance = {}
        for name, model in self.models.items():
            if hasattr(model, 'feature_importances_'):
                for i, importance in enumerate(model.feature_importances_):
                    if i < len(self.feature_columns):
                        feature_importance[self.feature_columns[i]] = float(importance)
                break
        
        # Predicted price (simplified - could use regression models)
        current_price = current_data['close'].iloc[-1]
        expected_return = 0.001 if ensemble_pred == 1 else -0.001  # Simplified
        predicted_price = current_price * (1 + expected_return)
        
        return MLPrediction(
            predicted_price=predicted_price,
            predicted_direction=direction,
            confidence=avg_confidence,
            feature_importance=feature_importance,
            model_name='ensemble'
        )
    
    def save_models(self, path: str):
        """Save trained models to disk"""
        model_data = {
            'models': self.models,
            'feature_columns': self.feature_columns,
            'scaler': self.scaler,
            'lookback_period': self.lookback_period,
            'prediction_horizon': self.prediction_horizon
        }
        joblib.dump(model_data, path)
        logger.info(f"Models saved to {path}")
    
    def load_models(self, path: str):
        """Load trained models from disk"""
        model_data = joblib.load(path)
        self.models = model_data['models']
        self.feature_columns = model_data['feature_columns']
        self.scaler = model_data['scaler']
        self.lookback_period = model_data['lookback_period']
        self.prediction_horizon = model_data['prediction_horizon']
        logger.info(f"Models loaded from {path}")

# Additional ML utilities
class MarketRegimeDetector:
    """
    Detect market regimes using Hidden Markov Models or clustering
    """
    
    def __init__(self, n_regimes: int = 3):
        """
        Initialize regime detector
        
        Args:
            n_regimes: Number of market regimes to detect
        """
        self.n_regimes = n_regimes
        self.model = None
        
    def fit(self, returns: pd.Series) -> np.ndarray:
        """
        Fit regime detection model
        
        Args:
            returns: Series of returns
            
        Returns:
            Array of regime labels
        """
        try:
            from sklearn.mixture import GaussianMixture
            
            # Prepare features for regime detection
            features = pd.DataFrame()
            features['returns'] = returns
            features['volatility'] = returns.rolling(20).std()
            features['skew'] = returns.rolling(20).skew()
            features = features.dropna()
            
            # Fit Gaussian Mixture Model
            self.model = GaussianMixture(
                n_components=self.n_regimes,
                covariance_type='full',
                random_state=42
            )
            
            regimes = self.model.fit_predict(features)
            
            logger.info(f"Market regimes detected: {np.unique(regimes)}")
            return regimes
            
        except ImportError:
            logger.warning("scikit-learn not fully installed. Using simple regime detection.")
            
            # Simple regime detection based on volatility
            vol = returns.rolling(20).std()
            regimes = pd.cut(vol, bins=self.n_regimes, labels=False)
            return regimes.fillna(0).values
    
    def predict_regime(self, returns: pd.Series) -> int:
        """
        Predict current market regime
        
        Args:
            returns: Recent returns
            
        Returns:
            Current regime label
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit first.")
        
        features = pd.DataFrame()
        features['returns'] = returns.iloc[-20:]
        features['volatility'] = returns.iloc[-20:].std()
        features['skew'] = returns.iloc[-20:].skew()
        
        return self.model.predict(features.iloc[-1:].values.reshape(1, -1))[0]
