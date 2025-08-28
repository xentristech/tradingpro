"""
ML Predictor - Sistema de Predicción con Machine Learning
Implementa modelos de ML para predicción de precios
Version: 3.0.0
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import joblib
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import xgboost as xgb
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn o XGBoost no disponible")

logger = logging.getLogger(__name__)

class MLPredictor:
    """
    Sistema de predicción usando Machine Learning
    Combina múltiples modelos para mejor precisión
    """
    
    def __init__(self, model_dir: str = 'storage/models'):
        """
        Inicializa el predictor ML
        Args:
            model_dir: Directorio para guardar/cargar modelos
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_performance = {}
        
        # Configuración de modelos
        self.model_configs = {
            'xgboost': {
                'enabled': SKLEARN_AVAILABLE,
                'weight': 0.4,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 5,
                    'learning_rate': 0.1,
                    'objective': 'multi:softprob'
                }
            },
            'random_forest': {
                'enabled': SKLEARN_AVAILABLE,
                'weight': 0.3,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5
                }
            },
            'gradient_boosting': {
                'enabled': SKLEARN_AVAILABLE,
                'weight': 0.3,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 5,
                    'learning_rate': 0.1
                }
            }
        }
        
        # Cargar modelos existentes
        self.load_models()
        
        logger.info(f"MLPredictor inicializado con {len(self.models)} modelos")
    
    def predict(self, data: pd.DataFrame) -> Optional[Dict]:
        """
        Genera predicción basada en los datos
        Args:
            data: DataFrame con datos OHLCV e indicadores
        Returns:
            Dict con predicción y confianza
        """
        if not SKLEARN_AVAILABLE or data is None or len(data) < 50:
            return None
        
        try:
            # Preparar features
            features = self._prepare_features(data)
            
            if features is None:
                return None
            
            # Si no hay modelos entrenados, entrenar con datos históricos
            if not self.models:
                logger.info("No hay modelos entrenados, entrenando con datos actuales...")
                self.train(data)
                if not self.models:
                    return None
            
            # Generar predicciones de cada modelo
            predictions = []
            confidences = []
            
            for model_name, model in self.models.items():
                if model_name in self.scalers:
                    # Escalar features
                    X_scaled = self.scalers[model_name].transform(features.reshape(1, -1))
                    
                    # Predecir
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X_scaled)[0]
                        pred_class = np.argmax(proba)
                        confidence = proba[pred_class]
                    else:
                        pred_class = model.predict(X_scaled)[0]
                        confidence = 0.5  # Default confidence
                    
                    # Obtener peso del modelo
                    weight = self.model_configs.get(model_name, {}).get('weight', 0.33)
                    
                    predictions.append((pred_class, weight))
                    confidences.append(confidence * weight)
            
            if not predictions:
                return None
            
            # Consolidar predicciones
            weighted_pred = sum(pred * weight for pred, weight in predictions)
            total_weight = sum(weight for _, weight in predictions)
            
            if total_weight > 0:
                final_pred = weighted_pred / total_weight
                final_confidence = sum(confidences) / total_weight
            else:
                return None
            
            # Interpretar predicción
            if final_pred < 0.4:
                direction = 'sell'
                strength = 1 - final_pred
            elif final_pred > 0.6:
                direction = 'buy'
                strength = final_pred
            else:
                direction = 'neutral'
                strength = 0.5
            
            # Calcular niveles de precio esperados
            current_price = data['close'].iloc[-1]
            atr = data['atr'].iloc[-1] if 'atr' in data.columns else (data['high'].iloc[-1] - data['low'].iloc[-1])
            
            if direction == 'buy':
                target = current_price + (atr * 2)
                stop = current_price - atr
            elif direction == 'sell':
                target = current_price - (atr * 2)
                stop = current_price + atr
            else:
                target = current_price
                stop = current_price
            
            result = {
                'direction': direction,
                'strength': float(strength),
                'confidence': float(final_confidence),
                'target_price': float(target),
                'stop_loss': float(stop),
                'models_used': len(predictions),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Predicción ML: {direction} (confianza: {final_confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return None
    
    def train(self, data: pd.DataFrame, save_models: bool = True) -> Dict:
        """
        Entrena los modelos con datos históricos
        Args:
            data: DataFrame con datos históricos
            save_models: Si guardar los modelos entrenados
        Returns:
            Dict con métricas de performance
        """
        if not SKLEARN_AVAILABLE or data is None or len(data) < 100:
            logger.warning("No se puede entrenar: datos insuficientes o librerías no disponibles")
            return {}
        
        try:
            logger.info("Preparando datos para entrenamiento...")
            
            # Preparar dataset
            X, y = self._prepare_training_data(data)
            
            if X is None or y is None or len(X) < 50:
                logger.warning("Datos insuficientes para entrenamiento")
                return {}
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            results = {}
            
            # Entrenar cada modelo
            for model_name, config in self.model_configs.items():
                if not config['enabled']:
                    continue
                
                logger.info(f"Entrenando {model_name}...")
                
                try:
                    # Escalar datos
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)
                    
                    # Crear y entrenar modelo
                    if model_name == 'xgboost':
                        model = xgb.XGBClassifier(**config['params'])
                    elif model_name == 'random_forest':
                        model = RandomForestClassifier(**config['params'])
                    elif model_name == 'gradient_boosting':
                        model = GradientBoostingClassifier(**config['params'])
                    else:
                        continue
                    
                    model.fit(X_train_scaled, y_train)
                    
                    # Evaluar modelo
                    train_score = model.score(X_train_scaled, y_train)
                    test_score = model.score(X_test_scaled, y_test)
                    
                    # Guardar modelo y scaler
                    self.models[model_name] = model
                    self.scalers[model_name] = scaler
                    
                    # Guardar feature importance
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[model_name] = model.feature_importances_
                    
                    # Guardar métricas
                    results[model_name] = {
                        'train_accuracy': float(train_score),
                        'test_accuracy': float(test_score),
                        'samples_trained': len(X_train)
                    }
                    
                    logger.info(f"{model_name} - Train: {train_score:.3f}, Test: {test_score:.3f}")
                    
                except Exception as e:
                    logger.error(f"Error entrenando {model_name}: {e}")
            
            # Guardar modelos si se requiere
            if save_models and results:
                self.save_models()
            
            self.model_performance = results
            return results
            
        except Exception as e:
            logger.error(f"Error en entrenamiento: {e}")
            return {}
    
    def _prepare_features(self, data: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Prepara features para predicción
        Args:
            data: DataFrame con datos
        Returns:
            Array de features o None
        """
        try:
            features = []
            
            # Precio y volumen
            if 'close' in data.columns:
                last_close = data['close'].iloc[-1]
                features.append(last_close)
                
                # Cambio porcentual
                if len(data) > 1:
                    pct_change = (last_close - data['close'].iloc[-2]) / data['close'].iloc[-2]
                    features.append(pct_change)
            
            # Indicadores técnicos
            indicators = ['rsi', 'macd', 'macd_signal', 'volume_ratio']
            for ind in indicators:
                if ind in data.columns:
                    value = data[ind].iloc[-1]
                    if not pd.isna(value):
                        features.append(value)
            
            # Medias móviles
            if 'sma_20' in data.columns and 'close' in data.columns:
                sma_20 = data['sma_20'].iloc[-1]
                if not pd.isna(sma_20):
                    features.append((last_close - sma_20) / sma_20)
            
            if 'sma_50' in data.columns and 'close' in data.columns:
                sma_50 = data['sma_50'].iloc[-1]
                if not pd.isna(sma_50):
                    features.append((last_close - sma_50) / sma_50)
            
            # Bollinger Bands
            if 'bb_upper' in data.columns and 'bb_lower' in data.columns:
                bb_upper = data['bb_upper'].iloc[-1]
                bb_lower = data['bb_lower'].iloc[-1]
                
                if not pd.isna(bb_upper) and not pd.isna(bb_lower):
                    bb_position = (last_close - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                    features.append(bb_position)
            
            # Volatilidad
            if 'atr' in data.columns:
                atr = data['atr'].iloc[-1]
                if not pd.isna(atr):
                    features.append(atr / last_close if last_close > 0 else 0)
            
            # Patrones de precio (últimas 5 barras)
            if len(data) >= 5:
                recent_closes = data['close'].iloc[-5:].values
                recent_pattern = np.diff(recent_closes)
                features.extend(recent_pattern[:3])  # Solo 3 para limitar features
            
            # Verificar que tengamos suficientes features
            if len(features) < 5:
                return None
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error preparando features: {e}")
            return None
    
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Prepara datos para entrenamiento
        Args:
            data: DataFrame con datos históricos
        Returns:
            Tupla (X, y) o (None, None)
        """
        try:
            X = []
            y = []
            
            # Necesitamos al menos 20 barras para calcular indicadores
            for i in range(20, len(data) - 1):
                # Preparar features de la ventana actual
                window = data.iloc[i-19:i+1]
                features = self._prepare_features(window)
                
                if features is not None:
                    X.append(features)
                    
                    # Calcular target (siguiente movimiento)
                    current_close = data['close'].iloc[i]
                    next_close = data['close'].iloc[i + 1]
                    
                    # Clasificación: 0=bajada, 1=neutral, 2=subida
                    change_pct = (next_close - current_close) / current_close
                    
                    if change_pct < -0.001:  # Bajada > 0.1%
                        y.append(0)
                    elif change_pct > 0.001:  # Subida > 0.1%
                        y.append(2)
                    else:  # Neutral
                        y.append(1)
            
            if len(X) < 50:
                return None, None
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparando datos de entrenamiento: {e}")
            return None, None
    
    def save_models(self):
        """Guarda los modelos entrenados"""
        try:
            for model_name, model in self.models.items():
                model_path = self.model_dir / f"{model_name}_model.pkl"
                joblib.dump(model, model_path)
                
                if model_name in self.scalers:
                    scaler_path = self.model_dir / f"{model_name}_scaler.pkl"
                    joblib.dump(self.scalers[model_name], scaler_path)
            
            # Guardar metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'models': list(self.models.keys()),
                'performance': self.model_performance,
                'feature_importance': {k: v.tolist() if isinstance(v, np.ndarray) else v 
                                      for k, v in self.feature_importance.items()}
            }
            
            metadata_path = self.model_dir / 'metadata.json'
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Modelos guardados en {self.model_dir}")
            
        except Exception as e:
            logger.error(f"Error guardando modelos: {e}")
    
    def load_models(self):
        """Carga modelos previamente entrenados"""
        try:
            loaded_count = 0
            
            for model_name in self.model_configs.keys():
                model_path = self.model_dir / f"{model_name}_model.pkl"
                scaler_path = self.model_dir / f"{model_name}_scaler.pkl"
                
                if model_path.exists() and scaler_path.exists():
                    try:
                        self.models[model_name] = joblib.load(model_path)
                        self.scalers[model_name] = joblib.load(scaler_path)
                        loaded_count += 1
                        logger.info(f"Modelo {model_name} cargado")
                    except Exception as e:
                        logger.warning(f"Error cargando modelo {model_name}: {e}")
            
            # Cargar metadata
            metadata_path = self.model_dir / 'metadata.json'
            if metadata_path.exists():
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.model_performance = metadata.get('performance', {})
                    self.feature_importance = metadata.get('feature_importance', {})
            
            if loaded_count > 0:
                logger.info(f"{loaded_count} modelos cargados exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando modelos: {e}")
    
    def get_feature_importance(self, model_name: str = None) -> Dict:
        """
        Obtiene la importancia de features
        Args:
            model_name: Nombre del modelo (None = todos)
        Returns:
            Dict con importancia de features
        """
        if model_name:
            return self.feature_importance.get(model_name, {})
        return self.feature_importance
    
    def get_model_performance(self) -> Dict:
        """
        Obtiene métricas de performance de los modelos
        Returns:
            Dict con métricas
        """
        return self.model_performance

# Testing
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear predictor
    predictor = MLPredictor()
    
    # Crear datos sintéticos para prueba
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    prices = 50000 + np.cumsum(np.random.randn(200) * 100)
    
    data = pd.DataFrame({
        'datetime': dates,
        'open': prices + np.random.randn(200) * 50,
        'high': prices + np.abs(np.random.randn(200) * 100),
        'low': prices - np.abs(np.random.randn(200) * 100),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 200)
    })
    data.set_index('datetime', inplace=True)
    
    # Agregar indicadores
    data['sma_20'] = data['close'].rolling(20).mean()
    data['sma_50'] = data['close'].rolling(50).mean()
    data['rsi'] = 50 + np.random.randn(200) * 20
    data['macd'] = np.random.randn(200) * 10
    data['macd_signal'] = data['macd'].rolling(9).mean()
    data['bb_middle'] = data['close'].rolling(20).mean()
    data['bb_upper'] = data['bb_middle'] + data['close'].rolling(20).std() * 2
    data['bb_lower'] = data['bb_middle'] - data['close'].rolling(20).std() * 2
    data['atr'] = np.random.rand(200) * 100 + 50
    data['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
    
    if SKLEARN_AVAILABLE:
        # Entrenar modelos
        print("\n📚 ENTRENANDO MODELOS...")
        results = predictor.train(data)
        
        if results:
            print("\n📊 RESULTADOS DE ENTRENAMIENTO:")
            for model, metrics in results.items():
                print(f"\n{model}:")
                for metric, value in metrics.items():
                    print(f"  {metric}: {value:.3f}" if isinstance(value, float) else f"  {metric}: {value}")
        
        # Hacer predicción
        print("\n🔮 GENERANDO PREDICCIÓN...")
        prediction = predictor.predict(data.tail(50))
        
        if prediction:
            print(f"\nDirección: {prediction['direction']}")
            print(f"Fuerza: {prediction['strength']:.2f}")
            print(f"Confianza: {prediction['confidence']:.2f}")
            print(f"Target: ${prediction['target_price']:.2f}")
            print(f"Stop Loss: ${prediction['stop_loss']:.2f}")
            print(f"Modelos usados: {prediction['models_used']}")
        else:
            print("No se pudo generar predicción")
    else:
        print("❌ Scikit-learn no está instalado. Instalar con: pip install scikit-learn xgboost")
