#!/usr/bin/env python
"""
AI ATR INTELLIGENT RISK CALCULATOR - CALCULADORA INTELIGENTE DE RIESGO CON ATR
=============================================================================
Sistema avanzado de cálculo de Stop Loss y Take Profit usando ATR con IA
Diseñado específicamente para resolver problemas de SL muy ajustados
"""

import os
import sys
import time
import MetaTrader5 as mt5
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Añadir path del proyecto
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from src.data.twelvedata_client import TwelveDataClient

class AIATRIntelligentRiskCalculator:
    """Calculadora inteligente de riesgo usando ATR y AI"""
    
    def __init__(self):
        # Cliente de datos
        self.data_client = TwelveDataClient()
        
        # Configuración AI para ATR
        self.ai_atr_config = {
            'atr_periods': [14, 21, 50],        # Múltiples períodos ATR
            'volatility_multipliers': {         # Multiplicadores por volatilidad
                'LOW': 1.5,                     # Baja volatilidad
                'MEDIUM': 2.0,                  # Volatilidad media
                'HIGH': 2.5,                    # Alta volatilidad
                'EXTREME': 3.0                  # Volatilidad extrema
            },
            'confidence_thresholds': {          # Umbrales de confianza
                'WEAK': 0.4,                    # Señal débil
                'MODERATE': 0.6,                # Señal moderada
                'STRONG': 0.75,                 # Señal fuerte
                'VERY_STRONG': 0.85             # Señal muy fuerte
            },
            'min_atr_distance': {               # Distancias mínimas por símbolo
                'BTCUSD': 200,                  # Mínimo 200 puntos para BTC
                'XAUUSD': 50,                   # Mínimo 50 puntos para oro
                'FOREX': 20                     # Mínimo 20 puntos para forex
            }
        }
        
        # Sistema de scoring AI
        self.ai_scoring = {
            'trend_momentum': 0.25,             # Peso del momentum de tendencia
            'volatility_analysis': 0.30,        # Peso del análisis de volatilidad
            'volume_confirmation': 0.20,        # Peso de confirmación de volumen
            'atr_consistency': 0.25             # Peso de consistencia ATR
        }
        
        # Historial para análisis AI
        self.market_memory = {
            'atr_history': {},                  # Historial ATR por símbolo
            'volatility_patterns': {},          # Patrones de volatilidad
            'signal_performance': {},           # Performance de señales
            'market_conditions': []             # Condiciones de mercado históricas
        }
        
        print("AI ATR Intelligent Risk Calculator inicializado")
        print("- Cálculo dinámico de ATR con múltiples períodos")
        print("- Sistema de scoring inteligente")
        print("- Análisis de volatilidad con IA")
        print("- Ajuste automático por condiciones de mercado")
    
    def calculate_multi_timeframe_atr(self, symbol, intervals=['1min', '5min', '15min']):
        """Calcular ATR en múltiples timeframes usando AI"""
        try:
            atr_data = {}
            
            for interval in intervals:
                # Obtener datos históricos
                data = self.data_client.get_time_series(
                    symbol=symbol,
                    interval=interval,
                    outputsize=100
                )
                
                if not data or 'values' not in data:
                    continue
                
                values = data['values']
                if len(values) < 50:
                    continue
                
                # Calcular ATR para diferentes períodos
                for period in self.ai_atr_config['atr_periods']:
                    atr_values = self._calculate_atr_values(values, period)
                    
                    if atr_values:
                        key = f"{interval}_{period}"
                        atr_data[key] = {
                            'current_atr': atr_values[-1],
                            'avg_atr': np.mean(atr_values[-10:]),
                            'atr_trend': self._calculate_atr_trend(atr_values),
                            'volatility_score': self._calculate_volatility_score(atr_values)
                        }
            
            return atr_data
            
        except Exception as e:
            print(f"Error calculando ATR multi-timeframe: {e}")
            return {}
    
    def _calculate_atr_values(self, candle_data, period=14):
        """Calcular valores ATR para un período específico"""
        try:
            if len(candle_data) < period + 1:
                return []
            
            true_ranges = []
            
            for i in range(1, len(candle_data)):
                current = candle_data[i]
                previous = candle_data[i-1]
                
                high = float(current['high'])
                low = float(current['low'])
                prev_close = float(previous['close'])
                
                # Calcular True Range
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            # Calcular ATR usando media móvil
            atr_values = []
            for i in range(period - 1, len(true_ranges)):
                atr = np.mean(true_ranges[i - period + 1:i + 1])
                atr_values.append(atr)
            
            return atr_values
            
        except Exception as e:
            print(f"Error calculando valores ATR: {e}")
            return []
    
    def _calculate_atr_trend(self, atr_values):
        """Calcular tendencia del ATR (creciente/decreciente)"""
        try:
            if len(atr_values) < 5:
                return 0
            
            recent_atr = np.mean(atr_values[-5:])
            older_atr = np.mean(atr_values[-10:-5]) if len(atr_values) >= 10 else atr_values[0]
            
            if older_atr == 0:
                return 0
            
            trend = (recent_atr - older_atr) / older_atr
            return trend
            
        except Exception as e:
            return 0
    
    def _calculate_volatility_score(self, atr_values):
        """Calcular score de volatilidad basado en ATR"""
        try:
            if len(atr_values) < 3:
                return 0.5  # Score neutral
            
            current_atr = atr_values[-1]
            avg_atr = np.mean(atr_values)
            std_atr = np.std(atr_values)
            
            if std_atr == 0:
                return 0.5
            
            # Normalizar score (0-1)
            z_score = (current_atr - avg_atr) / std_atr
            volatility_score = max(0, min(1, 0.5 + z_score / 4))
            
            return volatility_score
            
        except Exception as e:
            return 0.5
    
    def classify_market_volatility(self, atr_data):
        """Clasificar volatilidad de mercado usando IA"""
        try:
            if not atr_data:
                return 'MEDIUM', 0.5
            
            # Obtener scores de volatilidad de todos los timeframes
            volatility_scores = []
            for key, data in atr_data.items():
                volatility_scores.append(data['volatility_score'])
            
            if not volatility_scores:
                return 'MEDIUM', 0.5
            
            avg_volatility = np.mean(volatility_scores)
            
            # Clasificar volatilidad
            if avg_volatility < 0.3:
                classification = 'LOW'
            elif avg_volatility < 0.6:
                classification = 'MEDIUM'
            elif avg_volatility < 0.8:
                classification = 'HIGH'
            else:
                classification = 'EXTREME'
            
            return classification, avg_volatility
            
        except Exception as e:
            print(f"Error clasificando volatilidad: {e}")
            return 'MEDIUM', 0.5
    
    def calculate_ai_signal_strength(self, symbol, signal_data):
        """Calcular fortaleza de señal usando IA"""
        try:
            strength_components = {}
            
            # 1. Análisis de momentum de tendencia
            if 'rsi' in signal_data:
                rsi = signal_data['rsi']
                if rsi < 30 or rsi > 70:
                    strength_components['trend_momentum'] = 0.8
                elif rsi < 40 or rsi > 60:
                    strength_components['trend_momentum'] = 0.6
                else:
                    strength_components['trend_momentum'] = 0.4
            else:
                strength_components['trend_momentum'] = 0.5
            
            # 2. Análisis de volatilidad
            atr_data = self.calculate_multi_timeframe_atr(symbol)
            volatility_class, volatility_score = self.classify_market_volatility(atr_data)
            
            # Volatilidad media es mejor para señales
            if volatility_class == 'MEDIUM':
                strength_components['volatility_analysis'] = 0.8
            elif volatility_class in ['LOW', 'HIGH']:
                strength_components['volatility_analysis'] = 0.6
            else:
                strength_components['volatility_analysis'] = 0.4
            
            # 3. Confirmación de volumen (simulada para crypto)
            if 'volume_proxy' in signal_data:
                volume_score = min(signal_data['volume_proxy'] / 1000000, 1.0)
                strength_components['volume_confirmation'] = volume_score
            else:
                strength_components['volume_confirmation'] = 0.5
            
            # 4. Consistencia ATR
            if atr_data:
                atr_consistency = self._calculate_atr_consistency(atr_data)
                strength_components['atr_consistency'] = atr_consistency
            else:
                strength_components['atr_consistency'] = 0.5
            
            # Calcular score ponderado final
            total_strength = 0
            for component, score in strength_components.items():
                weight = self.ai_scoring.get(component, 0.25)
                total_strength += score * weight
            
            # Clasificar fortaleza
            if total_strength >= self.ai_atr_config['confidence_thresholds']['VERY_STRONG']:
                classification = 'VERY_STRONG'
            elif total_strength >= self.ai_atr_config['confidence_thresholds']['STRONG']:
                classification = 'STRONG'
            elif total_strength >= self.ai_atr_config['confidence_thresholds']['MODERATE']:
                classification = 'MODERATE'
            else:
                classification = 'WEAK'
            
            return classification, total_strength, strength_components
            
        except Exception as e:
            print(f"Error calculando fortaleza de señal: {e}")
            return 'MODERATE', 0.6, {}
    
    def _calculate_atr_consistency(self, atr_data):
        """Calcular consistencia entre ATRs de diferentes timeframes"""
        try:
            if len(atr_data) < 2:
                return 0.5
            
            # Obtener ATRs actuales normalizados
            atr_values = []
            for key, data in atr_data.items():
                if 'current_atr' in data:
                    atr_values.append(data['current_atr'])
            
            if len(atr_values) < 2:
                return 0.5
            
            # Calcular coeficiente de variación
            mean_atr = np.mean(atr_values)
            std_atr = np.std(atr_values)
            
            if mean_atr == 0:
                return 0.5
            
            cv = std_atr / mean_atr
            
            # Convertir a score de consistencia (menor CV = mayor consistencia)
            consistency_score = max(0, min(1, 1 - cv))
            
            return consistency_score
            
        except Exception as e:
            return 0.5
    
    def calculate_intelligent_sl_tp(self, symbol, signal_type, signal_strength_data, current_price):
        """Calcular SL y TP inteligentes usando ATR y AI"""
        try:
            # Obtener datos ATR
            atr_data = self.calculate_multi_timeframe_atr(symbol)
            volatility_class, volatility_score = self.classify_market_volatility(atr_data)
            
            # Determinar tipo de símbolo
            if 'BTC' in symbol:
                symbol_type = 'BTCUSD'
                min_distance = self.ai_atr_config['min_atr_distance']['BTCUSD']
            elif 'XAU' in symbol:
                symbol_type = 'XAUUSD'
                min_distance = self.ai_atr_config['min_atr_distance']['XAUUSD']
            else:
                symbol_type = 'FOREX'
                min_distance = self.ai_atr_config['min_atr_distance']['FOREX']
            
            # Obtener ATR promedio más relevante (15min_14 es bueno para trading)
            base_atr = 0
            if '15min_14' in atr_data:
                base_atr = atr_data['15min_14']['current_atr']
            elif '5min_14' in atr_data:
                base_atr = atr_data['5min_14']['current_atr']
            elif atr_data:
                # Usar el primer ATR disponible
                first_key = list(atr_data.keys())[0]
                base_atr = atr_data[first_key]['current_atr']
            
            if base_atr == 0:
                # Fallback: usar distancia fija aumentada
                if symbol_type == 'BTCUSD':
                    base_atr = current_price * 0.003  # 0.3% del precio actual
                elif symbol_type == 'XAUUSD':
                    base_atr = current_price * 0.001  # 0.1% del precio actual
                else:
                    base_atr = current_price * 0.0005  # 0.05% del precio actual
            
            # Aplicar multiplicador de volatilidad
            volatility_multiplier = self.ai_atr_config['volatility_multipliers'][volatility_class]
            
            # Ajustar por fortaleza de señal
            signal_strength_score = signal_strength_data.get('strength_score', 0.6)
            
            # Señales más fuertes pueden usar SL más ajustado
            signal_adjustment = 0.8 if signal_strength_score > 0.8 else 1.0
            
            # Calcular distancias
            sl_distance = base_atr * volatility_multiplier * signal_adjustment
            tp_distance = base_atr * volatility_multiplier * 2.0  # TP más amplio
            
            # Aplicar mínimos de seguridad
            sl_distance = max(sl_distance, min_distance)
            tp_distance = max(tp_distance, min_distance * 1.5)
            
            # Calcular precios finales
            if signal_type.upper() == 'BUY':
                sl_price = current_price - sl_distance
                tp_price = current_price + tp_distance
            else:  # SELL
                sl_price = current_price + sl_distance
                tp_price = current_price - tp_distance
            
            # Información detallada del cálculo
            calculation_info = {
                'base_atr': base_atr,
                'volatility_class': volatility_class,
                'volatility_score': volatility_score,
                'volatility_multiplier': volatility_multiplier,
                'signal_adjustment': signal_adjustment,
                'sl_distance': sl_distance,
                'tp_distance': tp_distance,
                'min_distance_applied': min_distance
            }
            
            return {
                'sl_price': sl_price,
                'tp_price': tp_price,
                'sl_distance': sl_distance,
                'tp_distance': tp_distance,
                'calculation_info': calculation_info
            }
            
        except Exception as e:
            print(f"Error calculando SL/TP inteligente: {e}")
            
            # Fallback seguro
            safety_distance = current_price * 0.01 if 'BTC' in symbol else current_price * 0.002
            
            if signal_type.upper() == 'BUY':
                return {
                    'sl_price': current_price - safety_distance,
                    'tp_price': current_price + safety_distance * 2,
                    'sl_distance': safety_distance,
                    'tp_distance': safety_distance * 2,
                    'calculation_info': {'error': str(e), 'fallback': True}
                }
            else:
                return {
                    'sl_price': current_price + safety_distance,
                    'tp_price': current_price - safety_distance * 2,
                    'sl_distance': safety_distance,
                    'tp_distance': safety_distance * 2,
                    'calculation_info': {'error': str(e), 'fallback': True}
                }
    
    def analyze_symbol_for_trading(self, symbol, signal_data=None):
        """Análisis completo de un símbolo para trading inteligente"""
        try:
            print(f"\n🧠 ANÁLISIS INTELIGENTE DE {symbol}")
            print("=" * 50)
            
            # Obtener precio actual
            if mt5.initialize():
                tick = mt5.symbol_info_tick(symbol)
                current_price = tick.bid if tick else 0
                mt5.shutdown()
            else:
                current_price = 0
            
            # Calcular ATR multi-timeframe
            print("📊 Calculando ATR multi-timeframe...")
            atr_data = self.calculate_multi_timeframe_atr(symbol)
            
            # Clasificar volatilidad
            volatility_class, volatility_score = self.classify_market_volatility(atr_data)
            
            # Calcular fortaleza de señal
            signal_strength_class, signal_strength_score, strength_components = self.calculate_ai_signal_strength(
                symbol, signal_data or {}
            )
            
            # Mostrar resultados
            print(f"\n💰 Precio actual: {current_price}")
            print(f"🌪️  Volatilidad: {volatility_class} ({volatility_score:.2f})")
            print(f"💪 Fortaleza señal: {signal_strength_class} ({signal_strength_score:.2f})")
            
            print(f"\n📈 ATR MULTI-TIMEFRAME:")
            for key, data in atr_data.items():
                print(f"  {key}: ATR={data['current_atr']:.5f}, Tendencia={data['atr_trend']:+.3f}")
            
            print(f"\n🎯 COMPONENTES DE FORTALEZA:")
            for component, score in strength_components.items():
                weight = self.ai_scoring.get(component, 0.25)
                print(f"  {component}: {score:.2f} (peso: {weight:.0%})")
            
            # Calcular SL/TP para ambas direcciones como ejemplo
            if current_price > 0:
                print(f"\n🔍 CÁLCULOS SL/TP INTELIGENTES:")
                
                signal_strength_data = {
                    'strength_score': signal_strength_score,
                    'strength_class': signal_strength_class
                }
                
                # Para BUY
                buy_calc = self.calculate_intelligent_sl_tp(symbol, 'BUY', signal_strength_data, current_price)
                print(f"\n📈 PARA SEÑAL BUY:")
                print(f"  SL: {buy_calc['sl_price']:.5f} (dist: {buy_calc['sl_distance']:.5f})")
                print(f"  TP: {buy_calc['tp_price']:.5f} (dist: {buy_calc['tp_distance']:.5f})")
                
                # Para SELL
                sell_calc = self.calculate_intelligent_sl_tp(symbol, 'SELL', signal_strength_data, current_price)
                print(f"\n📉 PARA SEÑAL SELL:")
                print(f"  SL: {sell_calc['sl_price']:.5f} (dist: {sell_calc['sl_distance']:.5f})")
                print(f"  TP: {sell_calc['tp_price']:.5f} (dist: {sell_calc['tp_distance']:.5f})")
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'atr_data': atr_data,
                'volatility_class': volatility_class,
                'volatility_score': volatility_score,
                'signal_strength_class': signal_strength_class,
                'signal_strength_score': signal_strength_score,
                'strength_components': strength_components
            }
            
        except Exception as e:
            print(f"Error en análisis completo: {e}")
            return None

def main():
    print("=" * 80)
    print("    AI ATR INTELLIGENT RISK CALCULATOR")
    print("=" * 80)
    print("Sistema inteligente de cálculo de riesgo usando ATR y AI")
    print("- Cálculo dinámico de Stop Loss y Take Profit")
    print("- Análisis multi-timeframe de volatilidad")
    print("- Sistema de scoring de fortaleza de señales")
    print("- Adaptación automática por condiciones de mercado")
    print()
    
    calculator = AIATRIntelligentRiskCalculator()
    
    try:
        while True:
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{current_time}] EJECUTANDO ANÁLISIS INTELIGENTE...")
            
            # Analizar BTCUSD (símbolo principal)
            btc_analysis = calculator.analyze_symbol_for_trading('BTC/USD')
            
            if btc_analysis:
                print(f"\n✅ Análisis completado para BTCUSD")
                print(f"   Volatilidad: {btc_analysis['volatility_class']}")
                print(f"   Score señal: {btc_analysis['signal_strength_score']:.2f}")
            
            print(f"\n⏰ Próximo análisis en 120 segundos...")
            print("Presiona Ctrl+C para detener")
            time.sleep(120)
            
    except KeyboardInterrupt:
        print("\n\n🛑 AI ATR Calculator detenido por usuario")
    except Exception as e:
        print(f"❌ Error en sistema: {e}")
    finally:
        print("AI ATR Intelligent Risk Calculator finalizado")

if __name__ == "__main__":
    main()