#!/usr/bin/env python
"""
AI SIMPLE PREDICTOR - PREDICTOR INTELIGENTE SIMPLIFICADO
=======================================================
Predictor simplificado pero poderoso con IA para probar funcionalidades básicas
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from src.data.twelvedata_client import TwelveDataClient

class AISimplePredictor:
    """Predictor inteligente simplificado para pruebas y desarrollo"""
    
    def __init__(self):
        self.data_client = TwelveDataClient()
        print("AI Simple Predictor inicializado")
        print("- Algoritmos: Momentum, Tendencia, Volatilidad")
        print("- Integración: TwelveData en tiempo real")
        print("- Predicción: Direccional inteligente")
    
    def get_market_data(self, symbol='BTC/USD', interval='1min', count=100):
        """Obtener datos de mercado"""
        try:
            print(f"📊 Obteniendo datos de {symbol}...")
            data = self.data_client.get_time_series(symbol, interval, count)
            
            if data and 'values' in data:
                df = pd.DataFrame(data['values'])
                # Convertir datetime y ordenar
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.sort_values('datetime')
                
                # Convertir precios a float
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                print(f"✅ Datos obtenidos: {len(df)} registros")
                return df
            else:
                print("❌ No se pudieron obtener datos")
                return None
                
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calcular indicadores técnicos básicos"""
        try:
            if len(df) < 20:
                print("Datos insuficientes para indicadores")
                return df
            
            # 1. Medias móviles
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma10'] = df['close'].rolling(10).mean()
            df['ma20'] = df['close'].rolling(20).mean()
            
            # 2. RSI simplificado
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 3. Bollinger Bands
            sma20 = df['close'].rolling(20).mean()
            std20 = df['close'].rolling(20).std()
            df['bb_upper'] = sma20 + (std20 * 2)
            df['bb_lower'] = sma20 - (std20 * 2)
            
            # 4. Momentum
            df['momentum'] = df['close'] / df['close'].shift(10) - 1
            
            # 5. Volatilidad
            df['volatility'] = df['close'].rolling(10).std() / df['close'].rolling(10).mean()
            
            return df
            
        except Exception as e:
            print(f"Error calculando indicadores: {e}")
            return df
    
    def predict_direction(self, df):
        """Predecir dirección usando IA simple"""
        try:
            if len(df) < 20:
                return {'direction': 'NEUTRAL', 'confidence': 0.5, 'reason': 'Datos insuficientes'}
            
            # Obtener datos actuales (últimos valores)
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Criterios de predicción IA
            signals = []
            scores = []
            
            # 1. Análisis de tendencia (MA)
            if pd.notna(current['ma5']) and pd.notna(current['ma10']) and pd.notna(current['ma20']):
                if current['ma5'] > current['ma10'] > current['ma20']:
                    signals.append('ALCISTA_TENDENCIA')
                    scores.append(0.8)
                elif current['ma5'] < current['ma10'] < current['ma20']:
                    signals.append('BAJISTA_TENDENCIA')
                    scores.append(-0.8)
                else:
                    signals.append('NEUTRAL_TENDENCIA')
                    scores.append(0.0)
            
            # 2. Análisis RSI
            if pd.notna(current['rsi']):
                if current['rsi'] < 30:
                    signals.append('ALCISTA_RSI')
                    scores.append(0.6)
                elif current['rsi'] > 70:
                    signals.append('BAJISTA_RSI')
                    scores.append(-0.6)
                else:
                    rsi_score = (50 - current['rsi']) / 50  # Normalizar
                    signals.append('NEUTRAL_RSI')
                    scores.append(rsi_score * 0.3)
            
            # 3. Análisis Bollinger Bands
            if pd.notna(current['bb_upper']) and pd.notna(current['bb_lower']):
                if current['close'] < current['bb_lower']:
                    signals.append('ALCISTA_BB')
                    scores.append(0.7)
                elif current['close'] > current['bb_upper']:
                    signals.append('BAJISTA_BB')
                    scores.append(-0.7)
                else:
                    signals.append('NEUTRAL_BB')
                    scores.append(0.0)
            
            # 4. Análisis de momentum
            if pd.notna(current['momentum']):
                if current['momentum'] > 0.02:  # 2% momentum positivo
                    signals.append('ALCISTA_MOMENTUM')
                    scores.append(0.5)
                elif current['momentum'] < -0.02:  # 2% momentum negativo
                    signals.append('BAJISTA_MOMENTUM')
                    scores.append(-0.5)
                else:
                    signals.append('NEUTRAL_MOMENTUM')
                    scores.append(0.0)
            
            # 5. Análisis de volatilidad
            if pd.notna(current['volatility']) and pd.notna(prev['volatility']):
                vol_change = current['volatility'] - prev['volatility']
                if vol_change > 0.001:  # Aumento significativo de volatilidad
                    signals.append('ALTA_VOLATILIDAD')
                    scores.append(-0.3)  # Alta volatilidad = riesgo
                else:
                    signals.append('BAJA_VOLATILIDAD')
                    scores.append(0.2)  # Baja volatilidad = estabilidad
            
            # Calcular score final promediado
            if not scores:
                return {'direction': 'NEUTRAL', 'confidence': 0.5, 'reason': 'Sin señales válidas'}
            
            final_score = np.mean(scores)
            confidence = min(abs(final_score), 1.0)
            
            # Determinar dirección
            if final_score > 0.1:
                direction = 'ALCISTA'
            elif final_score < -0.1:
                direction = 'BAJISTA'
            else:
                direction = 'NEUTRAL'
            
            # Crear razón detallada
            positive_signals = [s for s, score in zip(signals, scores) if score > 0.1]
            negative_signals = [s for s, score in zip(signals, scores) if score < -0.1]
            
            reason_parts = []
            if positive_signals:
                reason_parts.append(f"Alcista: {', '.join(positive_signals)}")
            if negative_signals:
                reason_parts.append(f"Bajista: {', '.join(negative_signals)}")
            
            reason = " | ".join(reason_parts) if reason_parts else "Sin señales claras"
            
            return {
                'direction': direction,
                'confidence': confidence,
                'score': final_score,
                'reason': reason,
                'signals_count': len(signals),
                'current_price': float(current['close']) if pd.notna(current['close']) else 0
            }
            
        except Exception as e:
            print(f"Error en predicción: {e}")
            return {'direction': 'NEUTRAL', 'confidence': 0.5, 'reason': f'Error: {str(e)}'}
    
    def run_analysis(self, symbol='BTC/USD'):
        """Ejecutar análisis completo"""
        try:
            print(f"\n🧠 ANÁLISIS IA PARA {symbol}")
            print("=" * 50)
            
            # Obtener datos
            df = self.get_market_data(symbol)
            if df is None:
                return None
            
            # Calcular indicadores
            print("📈 Calculando indicadores técnicos...")
            df = self.calculate_indicators(df)
            
            # Hacer predicción
            print("🎯 Realizando predicción IA...")
            prediction = self.predict_direction(df)
            
            # Mostrar resultados
            print(f"\n🔮 PREDICCIÓN PARA {symbol}:")
            print(f"   💰 Precio actual: ${prediction['current_price']:,.2f}")
            print(f"   📊 Dirección: {prediction['direction']}")
            print(f"   ⚡ Confianza: {prediction['confidence']:.1%}")
            print(f"   🎯 Score IA: {prediction.get('score', 0):+.3f}")
            print(f"   📋 Señales analizadas: {prediction.get('signals_count', 0)}")
            print(f"   💡 Razón: {prediction['reason']}")
            
            # Recomendación
            if prediction['confidence'] > 0.7:
                strength = "MUY FUERTE"
                action = "OPERAR" if prediction['direction'] != 'NEUTRAL' else "ESPERAR"
            elif prediction['confidence'] > 0.5:
                strength = "MODERADA"
                action = "CONSIDERAR" if prediction['direction'] != 'NEUTRAL' else "MONITOREAR"
            else:
                strength = "DÉBIL"
                action = "ESPERAR"
            
            print(f"   🚀 Fortaleza: {strength}")
            print(f"   🎪 Recomendación: {action}")
            
            return prediction
            
        except Exception as e:
            print(f"Error en análisis: {e}")
            return None

def main():
    print("=" * 60)
    print("    AI SIMPLE PREDICTOR - PRUEBA IA")
    print("=" * 60)
    
    predictor = AISimplePredictor()
    
    try:
        # Probar con BTCUSD
        result = predictor.run_analysis('BTC/USD')
        
        if result:
            print(f"\n✅ ANÁLISIS IA COMPLETADO")
            print(f"Dirección predicha: {result['direction']}")
            print(f"Confianza: {result['confidence']:.1%}")
        else:
            print("❌ No se pudo completar el análisis")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()