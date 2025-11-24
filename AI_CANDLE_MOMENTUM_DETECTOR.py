#!/usr/bin/env python
"""
AI CANDLE MOMENTUM DETECTOR - DETECTOR DE VELAS CON MOMENTO IA
==============================================================
Sistema inteligente que detecta velas fuertes con momento usando MT5
Monitoreo constante para detectar oportunidades inesperadas
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

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

class AICandleMomentumDetector:
    """Detector inteligente de velas con momento fuerte usando MT5"""
    
    def __init__(self):
        self.mt5_connected = False
        self.symbols = ['BTCUSDm', 'EURUSDm', 'GBPUSDm', 'XAUUSDm']  # Solo símbolos del broker
        
        # Configuración IA para detección de velas fuertes
        self.momentum_config = {
            'min_body_size_pct': 0.6,       # Mínimo 60% del rango total debe ser cuerpo
            'min_range_pips': 50,           # Rango mínimo en pips para considerar fuerte
            'volume_multiplier': 1.5,       # Volumen debe ser 1.5x el promedio
            'momentum_threshold': 0.8,      # Umbral de momentum (0-1)
            'atr_multiplier': 2.0,          # Vela debe ser 2x el ATR promedio
            'min_confidence': 75,           # Confianza mínima IA para alertar
        }
        
        # Cache para análisis
        self.last_candles = {}
        self.atr_cache = {}
        self.volume_avg_cache = {}
        
        self.connect_mt5()
        print("AI Candle Momentum Detector inicializado")
        print(f"- Monitoreando {len(self.symbols)} símbolos en tiempo real")
        print("- Detección de velas fuertes con momento usando MT5")
        print("- Análisis IA para validación de oportunidades")
    
    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                print("❌ Error conectando MT5")
                return False
            
            account_info = mt5.account_info()
            if account_info:
                print(f"✅ MT5 conectado - Cuenta: {account_info.login}")
                print(f"   Balance: ${account_info.balance:.2f}")
                self.mt5_connected = True
                return True
            else:
                print("❌ Error obteniendo info de cuenta MT5")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando MT5: {e}")
            return False
    
    def get_current_candle_data(self, symbol, timeframe=mt5.TIMEFRAME_M1, count=50):
        """Obtener datos actuales de velas desde MT5"""
        try:
            if not self.mt5_connected:
                return None
            
            # Obtener velas recientes
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return None
            
            return rates
            
        except Exception as e:
            print(f"Error obteniendo datos de {symbol}: {e}")
            return None
    
    def calculate_atr(self, rates, period=14):
        """Calcular ATR (Average True Range)"""
        try:
            if len(rates) < period + 1:
                return 0
            
            high_low = rates['high'] - rates['low']
            high_close_prev = np.abs(rates['high'] - np.roll(rates['close'], 1))
            low_close_prev = np.abs(rates['low'] - np.roll(rates['close'], 1))
            
            true_ranges = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
            
            # Excluir el primer elemento (no válido por el roll)
            atr = np.mean(true_ranges[1:period+1])
            return atr
            
        except Exception as e:
            print(f"Error calculando ATR: {e}")
            return 0
    
    def calculate_volume_average(self, rates, period=20):
        """Calcular promedio de volumen"""
        try:
            if len(rates) < period:
                return 0
            
            volumes = rates['tick_volume'][-period:]
            return np.mean(volumes)
            
        except Exception as e:
            print(f"Error calculando volumen promedio: {e}")
            return 0
    
    def analyze_candle_strength(self, symbol, current_candle, rates):
        """Analizar la fuerza de la vela actual con IA"""
        try:
            # Obtener datos de la vela
            candle_open = current_candle['open']
            candle_high = current_candle['high']
            candle_low = current_candle['low']
            candle_close = current_candle['close']
            candle_volume = current_candle['tick_volume']
            
            # 1. Calcular rango total y cuerpo de la vela
            total_range = candle_high - candle_low
            body_size = abs(candle_close - candle_open)
            
            if total_range == 0:
                return None
            
            body_ratio = body_size / total_range
            
            # 2. Determinar dirección
            direction = 'ALCISTA' if candle_close > candle_open else 'BAJISTA'
            
            # 3. Calcular ATR para contexto
            atr = self.calculate_atr(rates)
            if atr == 0:
                return None
            
            atr_multiplier = total_range / atr
            
            # 4. Calcular volumen vs promedio
            volume_avg = self.calculate_volume_average(rates)
            if volume_avg == 0:
                return None
            
            volume_ratio = candle_volume / volume_avg
            
            # 5. Convertir rango a pips (aproximado)
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                pip_value = 0.0001  # Default para forex
            else:
                pip_value = symbol_info.point * 10 if symbol_info.digits == 5 else symbol_info.point
            
            range_pips = total_range / pip_value
            
            # 6. SCORING IA PARA FUERZA DE VELA
            strength_score = 0
            signals = []
            
            # Score por tamaño del cuerpo
            if body_ratio >= self.momentum_config['min_body_size_pct']:
                strength_score += 25
                signals.append(f"CUERPO_FUERTE({body_ratio*100:.1f}%)")
            
            # Score por rango en pips
            if range_pips >= self.momentum_config['min_range_pips']:
                strength_score += 20
                signals.append(f"RANGO_ALTO({range_pips:.1f}pips)")
            
            # Score por ATR multiplier
            if atr_multiplier >= self.momentum_config['atr_multiplier']:
                strength_score += 25
                signals.append(f"ATR_EXCEPCIONAL({atr_multiplier:.1f}x)")
            
            # Score por volumen
            if volume_ratio >= self.momentum_config['volume_multiplier']:
                strength_score += 20
                signals.append(f"VOLUMEN_ALTO({volume_ratio:.1f}x)")
            
            # Score por momentum (combinación de factores)
            momentum_score = (body_ratio + (atr_multiplier / 3) + (volume_ratio / 2)) / 3
            if momentum_score >= self.momentum_config['momentum_threshold']:
                strength_score += 10
                signals.append(f"MOMENTUM_FUERTE({momentum_score:.2f})")
            
            # Determinar tipo de vela especial
            candle_type = "NORMAL"
            if body_ratio >= 0.8 and atr_multiplier >= 2.5:
                candle_type = "MARUBOZU"
            elif body_ratio >= 0.7 and volume_ratio >= 2.0:
                candle_type = "ENGULFING"
            elif atr_multiplier >= 3.0:
                candle_type = "BREAKOUT"
            
            # Calcular nivel de riesgo (1-10)
            risk_level = min(10, max(1, int(atr_multiplier)))
            
            return {
                'symbol': symbol,
                'direction': direction,
                'strength_score': strength_score,
                'candle_type': candle_type,
                'body_ratio': body_ratio * 100,
                'range_pips': range_pips,
                'atr_multiplier': atr_multiplier,
                'volume_ratio': volume_ratio,
                'momentum_score': momentum_score,
                'risk_level': risk_level,
                'signals': signals,
                'timestamp': datetime.now(),
                'candle_data': {
                    'open': candle_open,
                    'high': candle_high,
                    'low': candle_low,
                    'close': candle_close,
                    'volume': candle_volume
                }
            }
            
        except Exception as e:
            print(f"Error analizando vela de {symbol}: {e}")
            return None
    
    def scan_all_symbols(self):
        """Escanear todos los símbolos buscando velas fuertes"""
        strong_candles = []
        
        print(f"🔍 ESCANEANDO VELAS FUERTES - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        for symbol in self.symbols:
            print(f"📊 Analizando {symbol}...", end=" ")
            
            # Obtener datos de MT5
            rates = self.get_current_candle_data(symbol)
            if rates is None or len(rates) < 20:
                print("❌ Sin datos")
                continue
            
            # Analizar la vela más reciente (que ya está cerrada)
            current_candle = rates[-2]  # -1 es la vela actual, -2 es la última cerrada
            
            analysis = self.analyze_candle_strength(symbol, current_candle, rates)
            if analysis is None:
                print("❌ Error análisis")
                continue
            
            # Verificar si es una vela fuerte
            if analysis['strength_score'] >= self.momentum_config['min_confidence']:
                strong_candles.append(analysis)
                print(f"🚨 VELA FUERTE ({analysis['strength_score']}%)")
            else:
                print(f"✅ Normal ({analysis['strength_score']}%)")
            
            time.sleep(0.1)  # Pequeña pausa entre símbolos
        
        return strong_candles
    
    def display_strong_candles(self, candles):
        """Mostrar velas fuertes detectadas"""
        if not candles:
            print("❌ NO SE DETECTARON VELAS FUERTES")
            return
        
        print(f"\n🚨 VELAS FUERTES DETECTADAS: {len(candles)}")
        print("=" * 80)
        
        for i, candle in enumerate(candles, 1):
            direction_icon = "🔥" if candle['direction'] == 'ALCISTA' else "❄️"
            risk_icon = "🟢" if candle['risk_level'] <= 3 else "🟡" if candle['risk_level'] <= 6 else "🔴"
            
            print(f"\n{i}. {direction_icon} {candle['symbol']} - {candle['candle_type']} {candle['direction']}")
            print(f"   💎 Score IA: {candle['strength_score']}% | {risk_icon} Riesgo: {candle['risk_level']}/10")
            print(f"   📊 Cuerpo: {candle['body_ratio']:.1f}% | Rango: {candle['range_pips']:.1f} pips")
            print(f"   ⚡ ATR: {candle['atr_multiplier']:.1f}x | Volumen: {candle['volume_ratio']:.1f}x")
            print(f"   🎯 Momentum: {candle['momentum_score']:.2f}")
            print(f"   💰 OHLC: {candle['candle_data']['open']:.4f} | {candle['candle_data']['high']:.4f} | {candle['candle_data']['low']:.4f} | {candle['candle_data']['close']:.4f}")
            
            if candle['signals']:
                print(f"   🚨 Señales: {' | '.join(candle['signals'][:4])}")  # Mostrar max 4 señales
        
        print("\n" + "=" * 80)
    
    def get_strongest_candle(self, candles):
        """Obtener la vela más fuerte"""
        if not candles:
            return None
        
        return max(candles, key=lambda x: x['strength_score'])
    
    def run_continuous_monitoring(self, scan_interval=15):
        """Ejecutar monitoreo continuo"""
        try:
            cycle = 0
            print(f"\n🚀 INICIANDO MONITOREO CONTINUO DE VELAS FUERTES")
            print(f"⏰ Intervalo de escaneo: {scan_interval} segundos")
            print("Presiona Ctrl+C para detener")
            print("=" * 80)
            
            while True:
                cycle += 1
                cycle_start = datetime.now()
                
                print(f"\n🔄 CICLO #{cycle:03d} - {cycle_start.strftime('%H:%M:%S')}")
                
                # Escanear velas fuertes
                strong_candles = self.scan_all_symbols()
                
                # Mostrar resultados
                if strong_candles:
                    self.display_strong_candles(strong_candles)
                    
                    # Mostrar la más fuerte
                    strongest = self.get_strongest_candle(strong_candles)
                    if strongest:
                        print(f"\n⭐ VELA MÁS FUERTE DEL CICLO:")
                        print(f"   🎯 {strongest['symbol']} - {strongest['candle_type']} {strongest['direction']}")
                        print(f"   💎 Score: {strongest['strength_score']}% | ATR: {strongest['atr_multiplier']:.1f}x")
                        print(f"   📊 Rango: {strongest['range_pips']:.1f} pips | Momentum: {strongest['momentum_score']:.2f}")
                else:
                    print("✅ No se detectaron velas fuertes en este ciclo")
                
                # Estadísticas del ciclo
                scan_time = (datetime.now() - cycle_start).total_seconds()
                print(f"\n📈 ESTADÍSTICAS DEL CICLO:")
                print(f"   Símbolos escaneados: {len(self.symbols)}")
                print(f"   Velas fuertes: {len(strong_candles)}")
                print(f"   Tiempo de escaneo: {scan_time:.1f}s")
                if strong_candles:
                    avg_score = sum(c['strength_score'] for c in strong_candles) / len(strong_candles)
                    print(f"   Score promedio: {avg_score:.1f}%")
                
                print(f"\n⏰ Próximo escaneo en {scan_interval} segundos...")
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoreo detenido por usuario")
        except Exception as e:
            print(f"❌ Error en monitoreo: {e}")
        finally:
            if self.mt5_connected:
                mt5.shutdown()
            print("AI Candle Momentum Detector finalizado")

def main():
    print("=" * 80)
    print("    AI CANDLE MOMENTUM DETECTOR - VELAS FUERTES CON IA")
    print("=" * 80)
    print("Sistema de detección inteligente de velas con momento fuerte")
    print("- Análisis en tiempo real usando MT5")
    print("- Detección de patrones: MARUBOZU, ENGULFING, BREAKOUT")
    print("- Scoring IA basado en: Cuerpo, ATR, Volumen, Momentum")
    print("- Monitoreo continuo para oportunidades inesperadas")
    print()
    
    detector = AICandleMomentumDetector()
    
    if not detector.mt5_connected:
        print("❌ No se pudo conectar a MT5. Sistema no disponible.")
        return
    
    try:
        # Ejecutar un escaneo inicial
        print("🔍 ESCANEO INICIAL...")
        strong_candles = detector.scan_all_symbols()
        detector.display_strong_candles(strong_candles)
        
        if strong_candles:
            print(f"\n✅ Encontradas {len(strong_candles)} velas fuertes")
        else:
            print("\n📊 No hay velas fuertes en este momento")
        
        print("\n" + "=" * 60)
        print("¿Desea iniciar monitoreo continuo? (Enter para continuar, Ctrl+C para salir)")
        input()
        
        # Iniciar monitoreo continuo
        detector.run_continuous_monitoring(scan_interval=15)
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido por usuario")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()