"""
Evolutionary Machine Learning System with Online Learning and Drift Detection
Author: Trading Pro System
Version: 3.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import joblib
import json
from abc import ABC, abstractmethod

# ML libraries
try:
    import xgboost as xgb
    from sklearn.ensemble import RandomForestRegressor, VotingRegressor
    from sklearn.linear_model import SGDRegressor
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import optuna
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    logging.warning("ML libraries not available. Install xgboost, scikit-learn, optuna")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of ML models"""
    XGBOOST = "xgboost"
    RANDOM_FOREST = "random_forest"
    LINEAR = "linear"
    LSTM = "lstm"
    ENSEMBLE = "ensemble"


class DriftType(Enum):
    """Types of concept drift"""
    NONE = "none"
    GRADUAL = "gradual"
    SUDDEN = "sudden"
    RECURRING = "recurring"


@dataclass
class ModelConfig:
    """Configuration for ML models"""
    model_type: ModelType
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    retrain_frequency: int = 1000  # Samples between retraining
    drift_threshold: float = 0.1  # Threshold for drift detection
    performance_window: int = 100  # Window for performance tracking
    feature_importance_threshold: float = 0.01
    ensemble_weight: float = 1.0
    use_online_learning: bool = True
    adaptive_learning_rate: bool = True


@dataclass
class PerformanceMetrics:
    """Model performance metrics"""
    mse: float = 0.0
    mae: float = 0.0
    r2: float = 0.0
    sharpe_ratio: float = 0.0
    accuracy_trend: List[float] = field(default_factory=list)
    prediction_confidence: float = 0.0
    feature_importance: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DriftDetectionResult:
    """Drift detection result"""
    drift_detected: bool = False
    drift_type: DriftType = DriftType.NONE
    drift_magnitude: float = 0.0
    confidence: float = 0.0
    affected_features: List[str] = field(default_factory=list)
    recommended_action: str = "continue"
    timestamp: datetime = field(default_factory=datetime.now)


class BaseModel(ABC):
    """Base class for ML models"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.scaler = None
        self.is_fitted = False
        self.performance = PerformanceMetrics()
        self.feature_names = []
        self.training_history = []

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit the model"""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        pass

    @abstractmethod
    def partial_fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Incremental learning"""
        pass

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.is_fitted:
            return {}

        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            return dict(zip(self.feature_names, importance))
        return {}

    def save_model(self, filepath: str) -> None:
        """Save model to file"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'config': self.config,
            'performance': self.performance,
            'feature_names': self.feature_names,
            'is_fitted': self.is_fitted
        }
        joblib.dump(model_data, filepath)

    def load_model(self, filepath: str) -> None:
        """Load model from file"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.config = model_data['config']
        self.performance = model_data['performance']
        self.feature_names = model_data['feature_names']
        self.is_fitted = model_data['is_fitted']


class XGBoostModel(BaseModel):
    """XGBoost implementation"""

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit XGBoost model"""
        if not HAS_ML_LIBS:
            raise ImportError("XGBoost not available")

        self.feature_names = list(X.columns)

        # Scale features
        if self.scaler is None:
            self.scaler = RobustScaler()
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )

        # Default hyperparameters
        default_params = {
            'objective': 'reg:squarederror',
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }

        params = {**default_params, **self.config.hyperparameters}

        # Create and fit model
        self.model = xgb.XGBRegressor(**params)
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        logger.info(f"XGBoost model fitted with {len(X)} samples")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        X_scaled = pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index
        )

        return self.model.predict(X_scaled)

    def partial_fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Incremental learning using warm start"""
        if not self.is_fitted:
            self.fit(X, y)
            return

        # Add new data to training set and retrain
        # Note: XGBoost doesn't have true incremental learning
        # This is a simplified approach
        X_scaled = pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index
        )

        # Could implement more sophisticated incremental learning here
        logger.info(f"XGBoost partial fit with {len(X)} new samples")


class RandomForestModel(BaseModel):
    """Random Forest implementation"""

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit Random Forest model"""
        if not HAS_ML_LIBS:
            raise ImportError("Scikit-learn not available")

        self.feature_names = list(X.columns)

        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )

        # Default hyperparameters
        default_params = {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'n_jobs': -1
        }

        params = {**default_params, **self.config.hyperparameters}

        # Create and fit model
        self.model = RandomForestRegressor(**params)
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        logger.info(f"Random Forest model fitted with {len(X)} samples")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        X_scaled = pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index
        )

        return self.model.predict(X_scaled)

    def partial_fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Partial fit using warm start"""
        if not self.is_fitted:
            self.fit(X, y)
            return

        # Random Forest doesn't support true incremental learning
        # This would need a more sophisticated approach
        logger.info(f"Random Forest partial fit with {len(X)} new samples")


class LinearModel(BaseModel):
    """Linear model with SGD for online learning"""

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit linear model"""
        if not HAS_ML_LIBS:
            raise ImportError("Scikit-learn not available")

        self.feature_names = list(X.columns)

        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )

        # Default hyperparameters
        default_params = {
            'loss': 'squared_error',
            'learning_rate': 'adaptive',
            'eta0': 0.01,
            'random_state': 42
        }

        params = {**default_params, **self.config.hyperparameters}

        # Create and fit model
        self.model = SGDRegressor(**params)
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        logger.info(f"Linear model fitted with {len(X)} samples")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        X_scaled = pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index
        )

        return self.model.predict(X_scaled)

    def partial_fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Incremental learning"""
        if not self.is_fitted:
            self.fit(X, y)
            return

        X_scaled = pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index
        )

        self.model.partial_fit(X_scaled, y)
        logger.info(f"Linear model partial fit with {len(X)} new samples")


class DriftDetector:
    """Concept drift detection using statistical tests"""

    def __init__(self, window_size: int = 100, threshold: float = 0.1):
        """
        Initialize drift detector

        Args:
            window_size: Size of sliding window for comparison
            threshold: Threshold for drift detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.reference_window = deque(maxlen=window_size)
        self.current_window = deque(maxlen=window_size)
        self.drift_history = []

    def add_sample(self, prediction: float, actual: float) -> DriftDetectionResult:
        """
        Add sample and check for drift

        Args:
            prediction: Model prediction
            actual: Actual value

        Returns:
            DriftDetectionResult
        """
        error = abs(prediction - actual)
        self.current_window.append(error)

        # Need enough samples for comparison
        if len(self.current_window) < self.window_size:
            return DriftDetectionResult()

        # Initialize reference window if empty
        if len(self.reference_window) == 0:
            self.reference_window = self.current_window.copy()
            return DriftDetectionResult()

        # Perform drift test
        drift_result = self._perform_drift_test()

        # Update reference window if no drift
        if not drift_result.drift_detected:
            # Gradually update reference window
            self.reference_window.extend(list(self.current_window)[-10:])

        self.drift_history.append(drift_result)
        return drift_result

    def _perform_drift_test(self) -> DriftDetectionResult:
        """Perform statistical test for drift detection"""
        from collections import deque
        import scipy.stats as stats

        ref_data = list(self.reference_window)
        curr_data = list(self.current_window)

        # Kolmogorov-Smirnov test
        try:
            ks_stat, p_value = stats.ks_2samp(ref_data, curr_data)

            drift_detected = ks_stat > self.threshold
            drift_magnitude = ks_stat
            confidence = 1 - p_value

            drift_type = DriftType.NONE
            if drift_detected:
                # Simple heuristic for drift type
                ref_mean = np.mean(ref_data)
                curr_mean = np.mean(curr_data)

                if abs(curr_mean - ref_mean) > np.std(ref_data):
                    drift_type = DriftType.SUDDEN
                else:
                    drift_type = DriftType.GRADUAL

            recommended_action = "retrain" if drift_detected else "continue"

            return DriftDetectionResult(
                drift_detected=drift_detected,
                drift_type=drift_type,
                drift_magnitude=drift_magnitude,
                confidence=confidence,
                recommended_action=recommended_action
            )

        except Exception as e:
            logger.warning(f"Drift test failed: {e}")
            return DriftDetectionResult()


class EvolutionaryMLSystem:
    """
    Main evolutionary ML system with ensemble and adaptation
    """

    def __init__(self, initial_models: List[ModelConfig] = None):
        """
        Initialize evolutionary ML system

        Args:
            initial_models: List of initial model configurations
        """
        self.models = {}
        self.ensemble_weights = {}
        self.drift_detectors = {}
        self.performance_history = {}
        self.feature_engineer = None
        self.current_features = []
        self.prediction_cache = {}

        # Initialize models
        if initial_models:
            for i, config in enumerate(initial_models):
                self.add_model(f"model_{i}", config)
        else:
            # Default models
            self._create_default_models()

    def _create_default_models(self):
        """Create default model ensemble"""
        # XGBoost model
        xgb_config = ModelConfig(
            model_type=ModelType.XGBOOST,
            hyperparameters={
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1
            }
        )
        self.add_model("xgboost", xgb_config)

        # Random Forest model
        rf_config = ModelConfig(
            model_type=ModelType.RANDOM_FOREST,
            hyperparameters={
                'n_estimators': 50,
                'max_depth': 8
            }
        )
        self.add_model("random_forest", rf_config)

        # Linear model
        linear_config = ModelConfig(
            model_type=ModelType.LINEAR,
            hyperparameters={
                'learning_rate': 'adaptive',
                'eta0': 0.01
            }
        )
        self.add_model("linear", linear_config)

    def add_model(self, name: str, config: ModelConfig):
        """Add a new model to the ensemble"""
        if config.model_type == ModelType.XGBOOST:
            model = XGBoostModel(config)
        elif config.model_type == ModelType.RANDOM_FOREST:
            model = RandomForestModel(config)
        elif config.model_type == ModelType.LINEAR:
            model = LinearModel(config)
        else:
            raise ValueError(f"Unsupported model type: {config.model_type}")

        self.models[name] = model
        self.ensemble_weights[name] = config.ensemble_weight
        self.drift_detectors[name] = DriftDetector()
        self.performance_history[name] = []

        logger.info(f"Added model: {name} ({config.model_type.value})")

    def fit(self, X: pd.DataFrame, y: pd.Series, model_names: List[str] = None):
        """
        Fit models on training data

        Args:
            X: Feature matrix
            y: Target vector
            model_names: Specific models to fit (if None, fit all)
        """
        if model_names is None:
            model_names = list(self.models.keys())

        self.current_features = list(X.columns)

        for name in model_names:
            if name in self.models:
                try:
                    logger.info(f"Fitting model: {name}")
                    self.models[name].fit(X, y)

                    # Evaluate performance
                    predictions = self.models[name].predict(X)
                    performance = self._evaluate_performance(y, predictions)
                    self.models[name].performance = performance

                except Exception as e:
                    logger.error(f"Failed to fit model {name}: {e}")

        # Update ensemble weights based on performance
        self._update_ensemble_weights()

    def predict(self, X: pd.DataFrame, use_ensemble: bool = True) -> Dict[str, Any]:
        """
        Make predictions using ensemble or individual models

        Args:
            X: Feature matrix
            use_ensemble: Whether to use ensemble prediction

        Returns:
            Dictionary with predictions and metadata
        """
        if not self.models:
            raise ValueError("No models available for prediction")

        individual_predictions = {}
        weights = []
        predictions_array = []

        for name, model in self.models.items():
            if model.is_fitted:
                try:
                    pred = model.predict(X)
                    individual_predictions[name] = pred

                    if use_ensemble:
                        predictions_array.append(pred)
                        weights.append(self.ensemble_weights[name])

                except Exception as e:
                    logger.warning(f"Prediction failed for model {name}: {e}")

        if not individual_predictions:
            raise ValueError("No fitted models available")

        # Calculate ensemble prediction
        if use_ensemble and len(predictions_array) > 1:
            # Weighted average
            weights = np.array(weights)
            weights = weights / weights.sum()  # Normalize weights

            ensemble_pred = np.average(predictions_array, axis=0, weights=weights)
            confidence = self._calculate_prediction_confidence(predictions_array, weights)
        else:
            # Use best performing model
            best_model = max(
                individual_predictions.keys(),
                key=lambda x: self.ensemble_weights[x]
            )
            ensemble_pred = individual_predictions[best_model]
            confidence = 0.7  # Default confidence

        return {
            'ensemble_prediction': ensemble_pred,
            'individual_predictions': individual_predictions,
            'confidence': confidence,
            'model_weights': dict(zip(self.models.keys(), weights)) if use_ensemble else {},
            'timestamp': datetime.now()
        }

    def partial_fit(self, X: pd.DataFrame, y: pd.Series, model_names: List[str] = None):
        """
        Incremental learning on new data

        Args:
            X: New feature data
            y: New target data
            model_names: Specific models to update
        """
        if model_names is None:
            model_names = list(self.models.keys())

        for name in model_names:
            if name in self.models and self.models[name].is_fitted:
                try:
                    # Make prediction before updating
                    pred = self.models[name].predict(X)

                    # Check for drift
                    for i, (prediction, actual) in enumerate(zip(pred, y)):
                        drift_result = self.drift_detectors[name].add_sample(prediction, actual)

                        if drift_result.drift_detected:
                            logger.warning(f"Drift detected in {name}: {drift_result.drift_type.value}")

                            if drift_result.recommended_action == "retrain":
                                self._retrain_model(name, X, y)
                                continue

                    # Partial fit
                    self.models[name].partial_fit(X, y)

                    # Update performance metrics
                    performance = self._evaluate_performance(y, pred)
                    self.performance_history[name].append(performance)

                except Exception as e:
                    logger.error(f"Partial fit failed for model {name}: {e}")

        # Update ensemble weights
        self._update_ensemble_weights()

    def optimize_hyperparameters(self, X: pd.DataFrame, y: pd.Series,
                                model_name: str, n_trials: int = 50) -> Dict[str, Any]:
        """
        Optimize hyperparameters using Optuna

        Args:
            X: Training features
            y: Training targets
            model_name: Model to optimize
            n_trials: Number of optimization trials

        Returns:
            Best hyperparameters
        """
        if not HAS_ML_LIBS:
            logger.warning("Optuna not available for hyperparameter optimization")
            return {}

        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model = self.models[model_name]

        def objective(trial):
            """Objective function for optimization"""
            if model.config.model_type == ModelType.XGBOOST:
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
                }
            elif model.config.model_type == ModelType.RANDOM_FOREST:
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                    'max_depth': trial.suggest_int('max_depth', 5, 20),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5)
                }
            else:
                return 0  # Skip optimization for other models

            # Create temporary model with trial parameters
            temp_config = ModelConfig(
                model_type=model.config.model_type,
                hyperparameters=params
            )

            if model.config.model_type == ModelType.XGBOOST:
                temp_model = XGBoostModel(temp_config)
            else:
                temp_model = RandomForestModel(temp_config)

            # Cross-validation
            tscv = TimeSeriesSplit(n_splits=3)
            scores = []

            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                temp_model.fit(X_train, y_train)
                pred = temp_model.predict(X_val)
                score = mean_squared_error(y_val, pred)
                scores.append(score)

            return np.mean(scores)

        # Run optimization
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials)

        # Update model with best parameters
        best_params = study.best_params
        model.config.hyperparameters.update(best_params)

        logger.info(f"Hyperparameter optimization completed for {model_name}")
        logger.info(f"Best parameters: {best_params}")
        logger.info(f"Best score: {study.best_value}")

        return best_params

    def _retrain_model(self, model_name: str, X: pd.DataFrame, y: pd.Series):
        """Retrain a specific model"""
        if model_name in self.models:
            logger.info(f"Retraining model: {model_name}")
            self.models[model_name].fit(X, y)

            # Reset drift detector
            self.drift_detectors[model_name] = DriftDetector()

    def _evaluate_performance(self, y_true: pd.Series, y_pred: np.ndarray) -> PerformanceMetrics:
        """Evaluate model performance"""
        metrics = PerformanceMetrics()

        try:
            metrics.mse = mean_squared_error(y_true, y_pred)
            metrics.mae = mean_absolute_error(y_true, y_pred)
            metrics.r2 = r2_score(y_true, y_pred)

            # Calculate Sharpe-like ratio for predictions
            returns = pd.Series(y_pred).pct_change().dropna()
            if len(returns) > 0 and returns.std() > 0:
                metrics.sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)

            metrics.prediction_confidence = max(0, min(1, metrics.r2))

        except Exception as e:
            logger.warning(f"Performance evaluation failed: {e}")

        return metrics

    def _update_ensemble_weights(self):
        """Update ensemble weights based on recent performance"""
        total_performance = 0
        performance_scores = {}

        for name, model in self.models.items():
            if model.is_fitted:
                # Use R² as performance metric (higher is better)
                score = max(0, model.performance.r2)
                performance_scores[name] = score
                total_performance += score

        # Normalize weights
        if total_performance > 0:
            for name in performance_scores:
                self.ensemble_weights[name] = performance_scores[name] / total_performance
        else:
            # Equal weights if no performance data
            equal_weight = 1.0 / len(self.models)
            for name in self.models:
                self.ensemble_weights[name] = equal_weight

        logger.info(f"Updated ensemble weights: {self.ensemble_weights}")

    def _calculate_prediction_confidence(self, predictions: List[np.ndarray],
                                       weights: np.ndarray) -> float:
        """Calculate confidence based on prediction agreement"""
        if len(predictions) <= 1:
            return 0.7  # Default confidence

        # Calculate variance of predictions
        prediction_std = np.std(predictions, axis=0).mean()

        # Lower variance = higher confidence
        confidence = max(0.1, min(0.95, 1.0 - prediction_std))

        return confidence

    def get_ensemble_summary(self) -> Dict[str, Any]:
        """Get summary of ensemble state"""
        summary = {
            'models': {},
            'ensemble_weights': self.ensemble_weights.copy(),
            'total_models': len(self.models),
            'fitted_models': sum(1 for m in self.models.values() if m.is_fitted),
            'last_updated': datetime.now()
        }

        for name, model in self.models.items():
            summary['models'][name] = {
                'type': model.config.model_type.value,
                'is_fitted': model.is_fitted,
                'performance': {
                    'r2': model.performance.r2,
                    'mse': model.performance.mse,
                    'sharpe': model.performance.sharpe_ratio
                },
                'feature_importance': model.get_feature_importance()
            }

        return summary

    def save_system(self, directory: str):
        """Save the entire ML system"""
        import os
        os.makedirs(directory, exist_ok=True)

        # Save each model
        for name, model in self.models.items():
            model_path = os.path.join(directory, f"{name}_model.pkl")
            model.save_model(model_path)

        # Save system state
        system_state = {
            'ensemble_weights': self.ensemble_weights,
            'current_features': self.current_features,
            'performance_history': self.performance_history
        }

        state_path = os.path.join(directory, "system_state.json")
        with open(state_path, 'w') as f:
            json.dump(system_state, f, default=str)

        logger.info(f"ML system saved to {directory}")

    def load_system(self, directory: str):
        """Load the entire ML system"""
        import os

        # Load system state
        state_path = os.path.join(directory, "system_state.json")
        with open(state_path, 'r') as f:
            system_state = json.load(f)

        self.ensemble_weights = system_state['ensemble_weights']
        self.current_features = system_state['current_features']
        self.performance_history = system_state['performance_history']

        # Load models
        for model_file in os.listdir(directory):
            if model_file.endswith('_model.pkl'):
                name = model_file.replace('_model.pkl', '')
                model_path = os.path.join(directory, model_file)

                # Determine model type and create instance
                # This is simplified - in practice, you'd save the config too
                config = ModelConfig(model_type=ModelType.XGBOOST)  # Default
                model = XGBoostModel(config)
                model.load_model(model_path)

                self.models[name] = model
                self.drift_detectors[name] = DriftDetector()

        logger.info(f"ML system loaded from {directory}")


# Example usage
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    n_samples = 1000

    # Features
    X = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
        'feature_4': np.random.randn(n_samples)
    })

    # Target (with some relationship to features)
    y = pd.Series(
        X['feature_1'] * 0.5 + X['feature_2'] * 0.3 +
        X['feature_3'] * 0.2 + np.random.randn(n_samples) * 0.1
    )

    # Initialize ML system
    ml_system = EvolutionaryMLSystem()

    # Train models
    train_size = int(0.8 * len(X))
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    print("Training models...")
    ml_system.fit(X_train, y_train)

    # Make predictions
    print("Making predictions...")
    result = ml_system.predict(X_test)

    print(f"\nEnsemble Prediction Shape: {result['ensemble_prediction'].shape}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Model Weights: {result['model_weights']}")

    # Simulate online learning
    print("\nSimulating online learning...")
    for i in range(0, len(X_test), 10):
        batch_X = X_test[i:i+10]
        batch_y = y_test[i:i+10]

        if len(batch_X) > 0:
            ml_system.partial_fit(batch_X, batch_y)

    # Get system summary
    summary = ml_system.get_ensemble_summary()
    print(f"\nSystem Summary:")
    print(f"Total Models: {summary['total_models']}")
    print(f"Fitted Models: {summary['fitted_models']}")
    print(f"Ensemble Weights: {summary['ensemble_weights']}")

    for name, model_info in summary['models'].items():
        print(f"\n{name.upper()}:")
        print(f"  R²: {model_info['performance']['r2']:.3f}")
        print(f"  MSE: {model_info['performance']['mse']:.3f}")
        print(f"  Sharpe: {model_info['performance']['sharpe']:.3f}")