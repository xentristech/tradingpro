#!/usr/bin/env python
"""
AI NEURAL PRICE PREDICTOR - PREDICTOR DE PRECIOS CON REDES NEURONALES
====================================================================
Sistema avanzado de predicción de precios usando Neural Networks y IA
Integrado con TwelveData en tiempo real para máxima precisión
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import joblib
import warnings
warnings.filterwarnings('ignore')

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Añadir path del proyecto
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from src.data.twelvedata_client import TwelveDataClient

# Importar bibliotecas de ML
try:
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    print("⚠️ Bibliotecas de ML no disponibles. Instalando...")
    ML_AVAILABLE = False

class AINeralPricePredictor:
    """Predictor de precios usando Neural Networks avanzadas"""
    
    def __init__(self):
        # Configuración de la red neuronal
        self.neural_config = {
            'hidden_layers': (100, 50, 25),        # Capas ocultas
            'activation': 'relu',                   # Función de activación
            'solver': 'adam',                       # Optimizador
            'alpha': 0.001,                         # Regularización
            'learning_rate': 'adaptive',            # Tasa de aprendizaje adaptativa
            'max_iter': 1000,                       # Máximo de iteraciones
            'random_state': 42,                     # Semilla para reproducibilidad
            'early_stopping': True,                 # Parada temprana
            'validation_fraction': 0.1              # Fracción para validación
        }
        
        # Configuración de características técnicas
        self.feature_config = {
            'lookback_periods': 30,                 # Períodos hacia atrás
            'prediction_horizon': 5,                # Minutos hacia adelante
            'technical_indicators': [
                'sma_5', 'sma_10', 'sma_20',       # Medias móviles
                'ema_5', 'ema_10', 'ema_20',       # Medias exponenciales
                'rsi_14', 'rsi_21',                 # RSI
                'bb_upper', 'bb_lower', 'bb_mid',   # Bollinger Bands
                'macd', 'macd_signal',              # MACD
                'stoch_k', 'stoch_d',               # Estocástico
                'atr_14', 'atr_21',                 # ATR
                'volume_sma', 'price_volume'        # Volumen
            ]
        }
        
        # Cliente de datos y escaladores
        self.data_client = TwelveDataClient()
        self.price_scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        
        # Modelos y datos
        self.models = {}
        self.prediction_history = {}
        self.feature_importance = {}
        
        # Cache de datos
        self.data_cache = {}
        self.last_update = {}
        
        print("AI Neural Price Predictor inicializado")
        print(f"- Red neuronal: {self.neural_config['hidden_layers']}")
        print(f"- Características técnicas: {len(self.feature_config['technical_indicators'])}")
        print(f"- Horizonte de predicción: {self.feature_config['prediction_horizon']} minutos")
        print(f"- Lookback: {self.feature_config['lookback_periods']} períodos")
    
    def calculate_technical_indicators(self, df):
        """Calcular indicadores técnicos para las características"""
        try:
            # Verificar que tenemos las columnas necesarias
            required_cols = ['high', 'low', 'close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Columnas faltantes para indicadores técnicos: {missing_cols}")
                return df
            
            # Verificar que tenemos datos suficientes
            if len(df) < 50:
                print(f"Datos insuficientes para indicadores técnicos: {len(df)} filas")
                return df
            
            # Convertir a float
            for col in ['high', 'low', 'close', 'open', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 1. Medias móviles simples
            df['sma_5'] = df['close'].rolling(5).mean()
            df['sma_10'] = df['close'].rolling(10).mean()
            df['sma_20'] = df['close'].rolling(20).mean()
            
            # 2. Medias móviles exponenciales
            df['ema_5'] = df['close'].ewm(span=5).mean()
            df['ema_10'] = df['close'].ewm(span=10).mean()
            df['ema_20'] = df['close'].ewm(span=20).mean()
            
            # 3. RSI
            df['rsi_14'] = self._calculate_rsi(df['close'], 14)
            df['rsi_21'] = self._calculate_rsi(df['close'], 21)
            
            # 4. Bollinger Bands
            bb_period = 20
            bb_std = 2
            sma_bb = df['close'].rolling(bb_period).mean()
            std_bb = df['close'].rolling(bb_period).std()
            df['bb_upper'] = sma_bb + (std_bb * bb_std)
            df['bb_lower'] = sma_bb - (std_bb * bb_std)
            df['bb_mid'] = sma_bb
            
            # 5. MACD
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema12 - ema26
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            
            # 6. Estocástico
            low_14 = df['low'].rolling(14).min()
            high_14 = df['high'].rolling(14).max()
            df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
            df['stoch_d'] = df['stoch_k'].rolling(3).mean()
            
            # 7. ATR (Average True Range)
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            df['atr_14'] = df['tr'].rolling(14).mean()
            df['atr_21'] = df['tr'].rolling(21).mean()
            
            # 8. Indicadores de volumen
            df['volume_sma'] = df['volume'].rolling(20).mean()
            df['price_volume'] = df['close'] * df['volume']
            
            # Limpiar columnas temporales
            df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1, inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error calculando indicadores técnicos: {e}")
            return df
    
    def _calculate_rsi(self, prices, period=14):
        """Calcular RSI (Relative Strength Index)"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def get_market_data(self, symbol, intervals=['1min'], outputsize=100):
        """Obtener datos de mercado desde TwelveData"""
        try:
            all_data = {}
            
            for interval in intervals:
                # Verificar cache
                cache_key = f"{symbol}_{interval}"
                if cache_key in self.data_cache:
                    last_update = self.last_update.get(cache_key, datetime.min)
                    if (datetime.now() - last_update).total_seconds() < 60:  # Cache de 1 minuto
                        all_data[interval] = self.data_cache[cache_key]
                        continue
                
                # Obtener datos frescos
                data = self.data_client.get_time_series(
                    symbol=symbol,
                    interval=interval,
                    outputsize=outputsize
                )
                
                if data and 'values' in data:
                    df = pd.DataFrame(data['values'])
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df.sort_values('datetime')
                    df.reset_index(drop=True, inplace=True)
                    
                    # Calcular indicadores técnicos
                    df = self.calculate_technical_indicators(df)
                    
                    all_data[interval] = df
                    
                    # Actualizar cache
                    self.data_cache[cache_key] = df
                    self.last_update[cache_key] = datetime.now()
                else:
                    print(f"No se pudieron obtener datos para {symbol} {interval}")
            
            return all_data
            
        except Exception as e:
            print(f"Error obteniendo datos de mercado: {e}")
            return {}
    
    def prepare_features_targets(self, df):
        """Preparar características y objetivos para el modelo"""
        try:
            features = []
            targets = []
            
            lookback = self.feature_config['lookback_periods']
            horizon = self.feature_config['prediction_horizon']
            
            # Seleccionar columnas de características
            feature_columns = []
            for indicator in self.feature_config['technical_indicators']:
                if indicator in df.columns:
                    feature_columns.append(indicator)
            
            # Añadir precio de cierre como característica principal
            if 'close' in df.columns:
                feature_columns.insert(0, 'close')
            
            if len(feature_columns) == 0:
                print("No se encontraron características válidas")
                return None, None
            
            # Crear secuencias de características y objetivos
            for i in range(lookback, len(df) - horizon):
                # Características: ventana deslizante de lookback períodos
                feature_window = []
                for col in feature_columns:
                    if col in df.columns:
                        window_data = df[col].iloc[i-lookback:i].values
                        if len(window_data) == lookback and not np.isnan(window_data).any():
                            feature_window.extend(window_data)
                
                if len(feature_window) > 0:
                    features.append(feature_window)
                    
                    # Objetivo: precio futuro
                    future_price = df['close'].iloc[i + horizon]
                    if not np.isnan(future_price):
                        targets.append(future_price)
                    else:
                        features.pop()  # Remover la característica si el objetivo es NaN
            
            if len(features) == 0 or len(targets) == 0:
                print("No se pudieron crear características válidas")
                return None, None
            
            return np.array(features), np.array(targets)
            
        except Exception as e:
            print(f"Error preparando características: {e}")
            return None, None
    
    def train_neural_network(self, symbol, retrain=False):
        """Entrenar red neuronal para un símbolo específico"""
        try:
            print(f"\n🧠 Entrenando red neuronal para {symbol}...")
            
            # Verificar si ya tenemos un modelo entrenado
            if symbol in self.models and not retrain:
                print(f"Modelo ya entrenado para {symbol}")
                return True
            
            # Obtener datos históricos más extensos para entrenamiento
            market_data = self.get_market_data(symbol, ['1min'], outputsize=500)
            
            if '1min' not in market_data:
                print(f"No se pudieron obtener datos para {symbol}")
                return False
            
            df = market_data['1min']
            
            if len(df) < 100:
                print(f"Datos insuficientes para entrenar: {len(df)} filas")
                return False
            
            # Preparar características y objetivos
            X, y = self.prepare_features_targets(df)
            
            if X is None or y is None:
                print("Error preparando datos de entrenamiento")
                return False
            
            print(f"Dataset preparado: {X.shape[0]} muestras, {X.shape[1]} características")
            
            # Dividir en entrenamiento y prueba
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Escalar características
            scaler_key = f"{symbol}_feature_scaler"
            if scaler_key not in self.__dict__:
                self.__dict__[scaler_key] = MinMaxScaler()
            
            X_train_scaled = self.__dict__[scaler_key].fit_transform(X_train)
            X_test_scaled = self.__dict__[scaler_key].transform(X_test)
            
            # Escalar objetivos
            price_scaler_key = f"{symbol}_price_scaler"
            if price_scaler_key not in self.__dict__:
                self.__dict__[price_scaler_key] = MinMaxScaler()
            
            y_train_scaled = self.__dict__[price_scaler_key].fit_transform(y_train.reshape(-1, 1)).ravel()
            y_test_scaled = self.__dict__[price_scaler_key].transform(y_test.reshape(-1, 1)).ravel()
            
            # Crear y entrenar modelo
            model = MLPRegressor(**self.neural_config)
            
            print("Entrenando red neuronal...")
            start_time = time.time()
            model.fit(X_train_scaled, y_train_scaled)
            training_time = time.time() - start_time
            
            # Evaluar modelo
            y_pred_scaled = model.predict(X_test_scaled)
            y_pred = self.__dict__[price_scaler_key].inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
            
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Calcular precisión direccional
            y_test_direction = np.diff(y_test) > 0
            y_pred_direction = np.diff(y_pred) > 0
            directional_accuracy = np.mean(y_test_direction == y_pred_direction) * 100
            
            # Guardar modelo y métricas
            self.models[symbol] = {
                'model': model,
                'feature_scaler': self.__dict__[scaler_key],
                'price_scaler': self.__dict__[price_scaler_key],
                'metrics': {
                    'mse': mse,
                    'mae': mae,
                    'rmse': rmse,
                    'directional_accuracy': directional_accuracy,
                    'training_time': training_time,
                    'training_samples': len(X_train),
                    'test_samples': len(X_test)
                },
                'trained_at': datetime.now()
            }
            
            print(f"✅ Entrenamiento completado en {training_time:.2f}s")
            print(f"📊 Métricas del modelo:")
            print(f"   RMSE: {rmse:.2f}")
            print(f"   MAE: {mae:.2f}")
            print(f"   Precisión direccional: {directional_accuracy:.1f}%")
            print(f"   Muestras entrenamiento: {len(X_train)}")
            print(f"   Muestras prueba: {len(X_test)}")
            
            return True
            
        except Exception as e:
            print(f"Error entrenando red neuronal: {e}")
            return False
    
    def predict_price(self, symbol, current_data=None):
        """Predecir precio futuro usando la red neuronal entrenada"""
        try:
            if symbol not in self.models:
                print(f"Modelo no disponible para {symbol}")
                return None
            
            model_data = self.models[symbol]
            model = model_data['model']
            feature_scaler = model_data['feature_scaler']
            price_scaler = model_data['price_scaler']
            
            # Obtener datos actuales si no se proporcionaron
            if current_data is None:
                market_data = self.get_market_data(symbol, ['1min'], outputsize=100)
                if '1min' not in market_data:
                    print(f"No se pudieron obtener datos actuales para {symbol}")
                    return None
                current_data = market_data['1min']
            
            if len(current_data) < self.feature_config['lookback_periods']:
                print("Datos insuficientes para predicción")
                return None
            
            # Preparar características actuales
            lookback = self.feature_config['lookback_periods']
            feature_columns = []
            for indicator in self.feature_config['technical_indicators']:
                if indicator in current_data.columns:
                    feature_columns.append(indicator)
            
            if 'close' in current_data.columns:
                feature_columns.insert(0, 'close')
            
            # Crear ventana de características
            current_features = []
            for col in feature_columns:
                if col in current_data.columns:
                    window_data = current_data[col].tail(lookback).values
                    if len(window_data) == lookback and not np.isnan(window_data).any():
                        current_features.extend(window_data)
            
            if len(current_features) == 0:
                print("No se pudieron extraer características válidas")
                return None
            
            # Realizar predicción
            current_features = np.array(current_features).reshape(1, -1)
            current_features_scaled = feature_scaler.transform(current_features)
            
            pred_scaled = model.predict(current_features_scaled)
            predicted_price = price_scaler.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]
            
            # Información adicional
            current_price = current_data['close'].iloc[-1]
            price_change = predicted_price - current_price
            price_change_pct = (price_change / current_price) * 100
            
            # Confianza basada en métricas del modelo
            metrics = model_data['metrics']
            confidence = min(metrics['directional_accuracy'], 100)
            
            prediction_result = {
                'symbol': symbol,
                'current_price': current_price,
                'predicted_price': predicted_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'confidence': confidence,
                'direction': 'ALCISTA' if price_change > 0 else 'BAJISTA',
                'horizon_minutes': self.feature_config['prediction_horizon'],
                'timestamp': datetime.now(),
                'model_metrics': metrics
            }
            
            # Guardar en historial
            if symbol not in self.prediction_history:
                self.prediction_history[symbol] = []
            self.prediction_history[symbol].append(prediction_result)
            
            # Mantener solo las últimas 100 predicciones
            if len(self.prediction_history[symbol]) > 100:
                self.prediction_history[symbol].pop(0)
            
            return prediction_result
            
        except Exception as e:
            print(f"Error realizando predicción: {e}")
            return None
    
    def run_prediction_analysis(self, symbols=['BTC/USD']):
        """Ejecutar análisis de predicción para múltiples símbolos"""
        try:
            print(f"\n🎯 ANÁLISIS DE PREDICCIÓN CON NEURAL NETWORKS")
            print("=" * 60)
            
            results = {}
            
            for symbol in symbols:
                print(f"\n📈 Analizando {symbol}...")
                
                # Entrenar modelo si no existe
                if symbol not in self.models:
                    trained = self.train_neural_network(symbol)
                    if not trained:
                        print(f"No se pudo entrenar modelo para {symbol}")
                        continue
                
                # Realizar predicción
                prediction = self.predict_price(symbol)
                
                if prediction:
                    results[symbol] = prediction
                    
                    print(f"🔮 PREDICCIÓN {symbol}:")
                    print(f"   Precio actual: ${prediction['current_price']:,.2f}")
                    print(f"   Precio predicho: ${prediction['predicted_price']:,.2f}")
                    print(f"   Cambio: {prediction['price_change']:+.2f} ({prediction['price_change_pct']:+.2f}%)")
                    print(f"   Dirección: {prediction['direction']}")
                    print(f"   Confianza: {prediction['confidence']:.1f}%")
                    print(f"   Horizonte: {prediction['horizon_minutes']} minutos")
                    
                    # Mostrar métricas del modelo
                    metrics = prediction['model_metrics']
                    print(f"   📊 Modelo RMSE: {metrics['rmse']:.2f}")
                    print(f"   🎯 Precisión direccional: {metrics['directional_accuracy']:.1f}%")
                else:
                    print(f"No se pudo generar predicción para {symbol}")
            
            print(f"\n" + "=" * 60)
            return results
            
        except Exception as e:
            print(f"Error en análisis de predicción: {e}")
            return {}

def main():
    print("=" * 80)
    print("    AI NEURAL PRICE PREDICTOR")
    print("=" * 80)
    print("Sistema de predicción de precios con redes neuronales avanzadas")
    print("- Análisis técnico multi-dimensional")
    print("- Predicción direccional inteligente")
    print("- Integración con TwelveData en tiempo real")
    print("- Modelos adaptativos por símbolo")
    print()
    
    predictor = AINeralPricePredictor()
    
    try:
        cycle = 0
        symbols = ['BTC/USD']  # Comenzar solo con Bitcoin
        
        while True:
            cycle += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n[CICLO AI #{cycle:03d}] {current_time}")
            
            # Ejecutar predicciones
            results = predictor.run_prediction_analysis(symbols)
            
            if results:
                print(f"\n🎯 RESUMEN DE PREDICCIONES:")
                for symbol, pred in results.items():
                    direction_icon = "📈" if pred['direction'] == 'ALCISTA' else "📉"
                    print(f"   {direction_icon} {symbol}: {pred['price_change_pct']:+.2f}% ({pred['confidence']:.1f}% confianza)")
            
            print(f"\n⏰ Próximo análisis en 5 minutos...")
            print("Presiona Ctrl+C para detener")
            time.sleep(300)  # 5 minutos
            
    except KeyboardInterrupt:
        print("\n\n🛑 AI Neural Price Predictor detenido por usuario")
    except Exception as e:
        print(f"❌ Error en sistema: {e}")
    finally:
        print("AI Neural Price Predictor finalizado")

if __name__ == "__main__":
    if not ML_AVAILABLE:
        print("Instalando bibliotecas de Machine Learning necesarias...")
        os.system("pip install scikit-learn joblib")
    main()