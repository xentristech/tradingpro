#!/usr/bin/env python
"""
VELOCITY & ACCELERATION DETECTOR - DETECTOR DE VELOCIDAD Y ACELERACIÓN
=======================================================================
Sistema para medir velocidad y aceleración del precio en tiempo real
"""

import os
import sys
import time
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from collections import deque
import math

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class VelocityAccelerationDetector:
    """Detector de Velocidad y Aceleración del Precio"""

    def __init__(self):
        self.mt5_connected = False
        self.symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD', 'GBPUSD']

        # Almacenamiento de datos históricos
        self.price_history = {symbol: deque(maxlen=100) for symbol in self.symbols}
        self.time_history = {symbol: deque(maxlen=100) for symbol in self.symbols}
        self.velocity_history = {symbol: deque(maxlen=50) for symbol in self.symbols}

        # Configuración de detección
        self.detection_config = {
            'min_velocity_threshold': 0.001,  # 0.1% por minuto
            'acceleration_threshold': 0.0005,  # 0.05% por minuto²
            'spike_velocity': 0.005,          # 0.5% por minuto = movimiento rápido
            'extreme_velocity': 0.01,         # 1% por minuto = movimiento extremo
            'time_window_seconds': 60,        # Ventana de análisis
        }

        self.connect_mt5()
        print("=" * 80)
        print("    VELOCITY & ACCELERATION DETECTOR")
        print("=" * 80)
        print("Sistema de medición de velocidad y aceleración del precio")
        print("- Velocidad: Cambio de precio por unidad de tiempo")
        print("- Aceleración: Cambio de velocidad (momentum)")
        print("- Detección de spikes y movimientos extremos")
        print()

    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                print("[ERROR] No se pudo conectar MT5")
                return False

            account = mt5.account_info()
            if account:
                print(f"[OK] MT5 Conectado - Cuenta: {account.login}")
                print(f"     Balance: ${account.balance:.2f}")
                self.mt5_connected = True
                return True
        except Exception as e:
            print(f"[ERROR] Conectando MT5: {e}")
        return False

    def get_tick_data(self, symbol):
        """Obtener datos de tick en tiempo real"""
        try:
            if not self.mt5_connected:
                return None

            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return {
                    'time': datetime.now(),
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'last': tick.last if tick.last > 0 else tick.bid,
                    'volume': tick.volume,
                    'timestamp_ms': tick.time_msc
                }
            return None
        except Exception as e:
            print(f"[ERROR] Obteniendo tick {symbol}: {e}")
            return None

    def calculate_velocity(self, symbol):
        """
        Calcular velocidad del precio
        Velocidad = Δprecio / Δtiempo
        """
        try:
            if len(self.price_history[symbol]) < 2:
                return 0, "INSUFICIENTE_DATA"

            # Últimos dos puntos
            price_current = self.price_history[symbol][-1]
            price_prev = self.price_history[symbol][-2]
            time_current = self.time_history[symbol][-1]
            time_prev = self.time_history[symbol][-2]

            # Calcular delta tiempo en segundos
            delta_time = (time_current - time_prev).total_seconds()
            if delta_time == 0:
                return 0, "TIEMPO_CERO"

            # Calcular delta precio (en porcentaje)
            delta_price = ((price_current - price_prev) / price_prev) * 100

            # Velocidad en %/minuto
            velocity = (delta_price / delta_time) * 60

            # Clasificar velocidad
            abs_velocity = abs(velocity)
            if abs_velocity >= self.detection_config['extreme_velocity'] * 100:
                classification = "EXTREMA"
            elif abs_velocity >= self.detection_config['spike_velocity'] * 100:
                classification = "SPIKE"
            elif abs_velocity >= self.detection_config['min_velocity_threshold'] * 100:
                classification = "MODERADA"
            else:
                classification = "LENTA"

            return velocity, classification

        except Exception as e:
            print(f"[ERROR] Calculando velocidad {symbol}: {e}")
            return 0, "ERROR"

    def calculate_acceleration(self, symbol):
        """
        Calcular aceleración del precio
        Aceleración = Δvelocidad / Δtiempo
        """
        try:
            if len(self.velocity_history[symbol]) < 2:
                return 0, "INSUFICIENTE_VELOCIDAD"

            # Últimas dos velocidades
            vel_current = self.velocity_history[symbol][-1]
            vel_prev = self.velocity_history[symbol][-2]

            # Asumimos intervalos de tiempo constantes para simplicidad
            delta_time = 1  # 1 unidad de tiempo

            # Aceleración
            acceleration = (vel_current - vel_prev) / delta_time

            # Clasificar aceleración
            abs_acceleration = abs(acceleration)
            if abs_acceleration >= self.detection_config['acceleration_threshold'] * 200:
                classification = "FUERTE"
            elif abs_acceleration >= self.detection_config['acceleration_threshold'] * 100:
                classification = "MODERADA"
            else:
                classification = "BAJA"

            return acceleration, classification

        except Exception as e:
            print(f"[ERROR] Calculando aceleración {symbol}: {e}")
            return 0, "ERROR"

    def calculate_momentum_metrics(self, symbol):
        """Calcular métricas avanzadas de momentum"""
        try:
            if len(self.price_history[symbol]) < 10:
                return {}

            prices = list(self.price_history[symbol])[-20:]

            # 1. Rate of Change (ROC)
            if len(prices) >= 10:
                roc_10 = ((prices[-1] - prices[-10]) / prices[-10]) * 100
            else:
                roc_10 = 0

            # 2. Velocidad promedio últimos 5 puntos
            velocities = []
            for i in range(1, min(5, len(prices))):
                delta_price = ((prices[-i] - prices[-i-1]) / prices[-i-1]) * 100
                velocities.append(delta_price)

            avg_velocity = np.mean(velocities) if velocities else 0

            # 3. Volatilidad (desviación estándar)
            volatility = np.std(prices) if len(prices) > 1 else 0

            # 4. Tendencia (pendiente de regresión lineal)
            if len(prices) >= 5:
                x = np.arange(len(prices))
                coefficients = np.polyfit(x, prices, 1)
                trend_slope = coefficients[0]
                trend_direction = "ALCISTA" if trend_slope > 0 else "BAJISTA"
            else:
                trend_slope = 0
                trend_direction = "NEUTRAL"

            # 5. Impulso (magnitud del movimiento)
            price_range = max(prices) - min(prices)
            impulse = price_range / np.mean(prices) * 100 if prices else 0

            return {
                'roc_10': roc_10,
                'avg_velocity': avg_velocity,
                'volatility': volatility,
                'trend_slope': trend_slope,
                'trend_direction': trend_direction,
                'impulse': impulse
            }

        except Exception as e:
            print(f"[ERROR] Calculando métricas {symbol}: {e}")
            return {}

    def detect_momentum_patterns(self, symbol):
        """Detectar patrones de momentum"""
        patterns = []

        try:
            if len(self.velocity_history[symbol]) < 5:
                return patterns

            velocities = list(self.velocity_history[symbol])[-10:]

            # 1. Aceleración sostenida
            if len(velocities) >= 3:
                if all(velocities[i] > velocities[i-1] for i in range(-3, 0)):
                    patterns.append("ACELERACION_SOSTENIDA")
                elif all(velocities[i] < velocities[i-1] for i in range(-3, 0)):
                    patterns.append("DESACELERACION_SOSTENIDA")

            # 2. Spike de velocidad
            if velocities:
                current_vel = abs(velocities[-1])
                avg_vel = np.mean([abs(v) for v in velocities[:-1]]) if len(velocities) > 1 else 0

                if avg_vel > 0 and current_vel > avg_vel * 3:
                    patterns.append("SPIKE_VELOCIDAD")

            # 3. Cambio de dirección
            if len(velocities) >= 2:
                if velocities[-2] > 0 and velocities[-1] < 0:
                    patterns.append("REVERSA_BAJISTA")
                elif velocities[-2] < 0 and velocities[-1] > 0:
                    patterns.append("REVERSA_ALCISTA")

            # 4. Momentum extremo
            if velocities and abs(velocities[-1]) > self.detection_config['extreme_velocity'] * 100:
                patterns.append("MOMENTUM_EXTREMO")

            return patterns

        except Exception as e:
            print(f"[ERROR] Detectando patrones {symbol}: {e}")
            return patterns

    def analyze_symbol(self, symbol):
        """Análisis completo de un símbolo"""
        try:
            # Obtener tick actual
            tick_data = self.get_tick_data(symbol)
            if not tick_data:
                return None

            # Actualizar historial
            current_price = tick_data['bid']
            current_time = tick_data['time']

            self.price_history[symbol].append(current_price)
            self.time_history[symbol].append(current_time)

            # Calcular velocidad
            velocity, vel_class = self.calculate_velocity(symbol)
            self.velocity_history[symbol].append(velocity)

            # Calcular aceleración
            acceleration, acc_class = self.calculate_acceleration(symbol)

            # Métricas de momentum
            momentum_metrics = self.calculate_momentum_metrics(symbol)

            # Detectar patrones
            patterns = self.detect_momentum_patterns(symbol)

            # Score de intensidad (0-100)
            intensity_score = 0

            # Scoring basado en velocidad
            abs_vel = abs(velocity)
            if abs_vel > 1.0:  # > 1% por minuto
                intensity_score += 40
            elif abs_vel > 0.5:  # > 0.5% por minuto
                intensity_score += 25
            elif abs_vel > 0.1:  # > 0.1% por minuto
                intensity_score += 10

            # Scoring basado en aceleración
            abs_acc = abs(acceleration)
            if abs_acc > 0.5:
                intensity_score += 30
            elif abs_acc > 0.1:
                intensity_score += 15

            # Scoring por patrones
            if "MOMENTUM_EXTREMO" in patterns:
                intensity_score += 20
            if "SPIKE_VELOCIDAD" in patterns:
                intensity_score += 15
            if any("ACELERACION" in p for p in patterns):
                intensity_score += 10

            intensity_score = min(intensity_score, 100)

            return {
                'symbol': symbol,
                'price': current_price,
                'velocity': velocity,
                'velocity_class': vel_class,
                'acceleration': acceleration,
                'acceleration_class': acc_class,
                'momentum_metrics': momentum_metrics,
                'patterns': patterns,
                'intensity_score': intensity_score,
                'timestamp': current_time
            }

        except Exception as e:
            print(f"[ERROR] Analizando {symbol}: {e}")
            return None

    def display_analysis(self, analysis):
        """Mostrar análisis de forma visual"""
        if not analysis:
            return

        symbol = analysis['symbol']
        velocity = analysis['velocity']
        acceleration = analysis['acceleration']
        intensity = analysis['intensity_score']

        # Determinar iconos según dirección
        vel_icon = "🚀" if velocity > 0.5 else "📈" if velocity > 0 else "📉" if velocity < -0.5 else "🔻"
        acc_icon = "⚡" if abs(acceleration) > 0.1 else "➡️"
        intensity_icon = "🔥" if intensity > 70 else "⚠️" if intensity > 40 else "✅"

        print(f"\n{'=' * 60}")
        print(f"📊 {symbol} - ${analysis['price']:.4f}")
        print(f"{'=' * 60}")

        print(f"\n{vel_icon} VELOCIDAD: {velocity:+.3f}%/min ({analysis['velocity_class']})")
        print(f"   Interpretación: ", end="")
        if abs(velocity) > 1.0:
            print("Movimiento MUY RÁPIDO - Posible entrada institucional")
        elif abs(velocity) > 0.5:
            print("Movimiento rápido - Momentum fuerte")
        elif abs(velocity) > 0.1:
            print("Movimiento moderado - Normal")
        else:
            print("Movimiento lento - Consolidación")

        print(f"\n{acc_icon} ACELERACIÓN: {acceleration:+.3f}%/min² ({analysis['acceleration_class']})")
        print(f"   Interpretación: ", end="")
        if acceleration > 0.1:
            print("Incrementando velocidad - Momentum creciente")
        elif acceleration < -0.1:
            print("Reduciendo velocidad - Momentum decreciente")
        else:
            print("Velocidad constante")

        if analysis['momentum_metrics']:
            metrics = analysis['momentum_metrics']
            print(f"\n📈 MÉTRICAS DE MOMENTUM:")
            print(f"   ROC(10): {metrics.get('roc_10', 0):+.2f}%")
            print(f"   Velocidad promedio: {metrics.get('avg_velocity', 0):+.3f}%")
            print(f"   Volatilidad: {metrics.get('volatility', 0):.4f}")
            print(f"   Tendencia: {metrics.get('trend_direction', 'N/A')}")
            print(f"   Impulso: {metrics.get('impulse', 0):.2f}%")

        if analysis['patterns']:
            print(f"\n🎯 PATRONES DETECTADOS:")
            for pattern in analysis['patterns']:
                print(f"   • {pattern}")

        print(f"\n{intensity_icon} INTENSIDAD: {intensity}%")
        if intensity > 70:
            print("   ⚠️ ALERTA: Movimiento extremo detectado!")
        elif intensity > 40:
            print("   📍 Movimiento significativo en progreso")
        else:
            print("   ✅ Movimiento normal del mercado")

    def run_continuous_monitoring(self, interval=5):
        """Monitoreo continuo de velocidad y aceleración"""
        print(f"\n🚀 INICIANDO MONITOREO DE VELOCIDAD Y ACELERACIÓN")
        print(f"⏰ Actualización cada {interval} segundos")
        print("Presiona Ctrl+C para detener")
        print("=" * 80)

        cycle = 0
        high_intensity_alerts = []

        try:
            while True:
                cycle += 1
                print(f"\n🔄 CICLO #{cycle:03d} - {datetime.now().strftime('%H:%M:%S')}")

                for symbol in self.symbols:
                    analysis = self.analyze_symbol(symbol)

                    if analysis:
                        # Solo mostrar si hay movimiento significativo
                        if analysis['intensity_score'] > 20:
                            self.display_analysis(analysis)

                            # Guardar alertas de alta intensidad
                            if analysis['intensity_score'] > 70:
                                high_intensity_alerts.append({
                                    'time': datetime.now(),
                                    'symbol': symbol,
                                    'velocity': analysis['velocity'],
                                    'intensity': analysis['intensity_score']
                                })
                        else:
                            print(f"   {symbol}: Movimiento normal (Intensidad: {analysis['intensity_score']}%)")

                # Resumen de alertas
                if high_intensity_alerts:
                    recent_alerts = [a for a in high_intensity_alerts
                                   if (datetime.now() - a['time']).seconds < 300]
                    if recent_alerts:
                        print(f"\n🚨 ALERTAS RECIENTES (últimos 5 min):")
                        for alert in recent_alerts[-3:]:
                            print(f"   {alert['symbol']}: Velocidad {alert['velocity']:+.3f}%/min")

                print(f"\n⏰ Próxima actualización en {interval} segundos...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Monitoreo detenido por usuario")

            # Estadísticas finales
            print("\n📊 ESTADÍSTICAS DE LA SESIÓN:")
            print(f"   Ciclos ejecutados: {cycle}")
            print(f"   Alertas de alta intensidad: {len(high_intensity_alerts)}")

            if high_intensity_alerts:
                print("\n   Movimientos más intensos:")
                sorted_alerts = sorted(high_intensity_alerts,
                                     key=lambda x: x['intensity'],
                                     reverse=True)
                for alert in sorted_alerts[:3]:
                    print(f"   • {alert['symbol']}: {alert['intensity']}% intensidad")

        except Exception as e:
            print(f"[ERROR] En monitoreo: {e}")

        finally:
            if self.mt5_connected:
                mt5.shutdown()
            print("Detector de Velocidad y Aceleración finalizado")

def main():
    """Función principal"""
    detector = VelocityAccelerationDetector()

    if not detector.mt5_connected:
        print("[ERROR] No se pudo conectar con MT5")
        return

    # Ejecutar análisis inicial
    print("\n📊 ANÁLISIS INICIAL DE VELOCIDAD Y ACELERACIÓN...")

    for symbol in detector.symbols:
        # Necesitamos algunos datos históricos primero
        for _ in range(5):
            analysis = detector.analyze_symbol(symbol)
            time.sleep(0.5)

    # Mostrar análisis actual
    for symbol in detector.symbols:
        analysis = detector.analyze_symbol(symbol)
        if analysis:
            detector.display_analysis(analysis)

    print("\n" + "=" * 80)
    print("¿Iniciar monitoreo continuo? (Enter para continuar, Ctrl+C para salir)")

    try:
        input()
        detector.run_continuous_monitoring(interval=5)
    except KeyboardInterrupt:
        print("\n🛑 Sistema cancelado")

if __name__ == "__main__":
    main()