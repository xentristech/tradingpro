#!/usr/bin/env python
"""
IVI - INSTITUTIONAL VELOCITY INDEX
=================================
Indicador personalizado para detectar momentum institucional y aceleración de precio
Desarrollado por XentrisTech - Algoritmo único para detección de ballenas

FÓRMULA IVI:
IVI = (Candle_Strength * Volume_Factor * Velocity_Factor * Acceleration_Factor) / 4

Donde:
- Candle_Strength: 0-100 (basado en cuerpo, ATR, tipo de vela)
- Volume_Factor: 0-100 (volumen vs promedio)
- Velocity_Factor: 0-100 (velocidad de cambio de precio)
- Acceleration_Factor: 0-100 (aceleración del momentum)

NIVELES IVI:
- 0-25:  Normal (Sin señal)
- 25-50: Moderado (Vigilar)
- 50-75: Fuerte (Preparar entrada)
- 75-100: Extremo (Entrada inmediata)
"""

import MetaTrader5 as mt5
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class IVIIndicator:
    """
    IVI - Institutional Velocity Index
    Indicador propietario para detectar movimientos institucionales
    """

    def __init__(self):
        self.name = "IVI - Institutional Velocity Index"
        self.version = "1.0"
        self.author = "XentrisTech"

        # Configuración del indicador
        self.config = {
            'atr_period': 14,
            'volume_period': 20,
            'velocity_period': 5,      # Períodos para calcular velocidad
            'acceleration_period': 3,   # Períodos para calcular aceleración

            # Umbrales para clasificación
            'threshold_moderate': 25,
            'threshold_strong': 50,
            'threshold_extreme': 75,

            # Pesos para la fórmula IVI
            'weight_candle': 0.30,     # 30% peso estructura vela
            'weight_volume': 0.25,     # 25% peso volumen
            'weight_velocity': 0.25,   # 25% peso velocidad
            'weight_acceleration': 0.20 # 20% peso aceleración
        }

        print(f"[IVI] {self.name} v{self.version} inicializado")
        print(f"[IVI] Desarrollado por {self.author}")

    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                return False
            return True
        except:
            return False

    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_M1, count=100):
        """Obtener datos de mercado"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) < count:
                return None
            return rates
        except:
            return None

    def calculate_atr(self, rates, period=14):
        """Calcular ATR (Average True Range)"""
        try:
            if len(rates) < period + 1:
                return np.zeros(len(rates))

            high = rates['high']
            low = rates['low']
            close = rates['close']

            # True Range
            tr1 = high - low
            tr2 = np.abs(high - np.roll(close, 1))
            tr3 = np.abs(low - np.roll(close, 1))

            true_range = np.maximum(tr1, np.maximum(tr2, tr3))

            # ATR usando media móvil simple
            atr = np.zeros(len(rates))
            for i in range(period, len(rates)):
                atr[i] = np.mean(true_range[i-period+1:i+1])

            return atr
        except:
            return np.zeros(len(rates))

    def calculate_candle_strength(self, rates):
        """
        Calcular fuerza de la vela (0-100)
        Basado en: cuerpo, mechas, ATR, tipo de patrón
        """
        try:
            candle_scores = np.zeros(len(rates))
            atr = self.calculate_atr(rates, self.config['atr_period'])

            for i in range(1, len(rates)):
                if atr[i] == 0:
                    continue

                candle = rates[i]
                open_price = candle['open']
                high_price = candle['high']
                low_price = candle['low']
                close_price = candle['close']

                # 1. Tamaño del cuerpo vs rango total
                total_range = high_price - low_price
                if total_range == 0:
                    continue

                body_size = abs(close_price - open_price)
                body_ratio = body_size / total_range

                # 2. Comparación con ATR
                atr_ratio = total_range / atr[i] if atr[i] > 0 else 0

                # 3. Tipo de vela
                upper_wick = high_price - max(open_price, close_price)
                lower_wick = min(open_price, close_price) - low_price
                wick_ratio = (upper_wick + lower_wick) / total_range if total_range > 0 else 0

                # 4. Calcular score de la vela (0-100)
                score = 0

                # Score por cuerpo (0-40 puntos)
                if body_ratio >= 0.8:      # Marubozu
                    score += 40
                elif body_ratio >= 0.6:    # Cuerpo fuerte
                    score += 30
                elif body_ratio >= 0.4:    # Cuerpo moderado
                    score += 20
                else:                      # Cuerpo débil
                    score += 10

                # Score por ATR (0-30 puntos)
                if atr_ratio >= 3.0:       # Extremo
                    score += 30
                elif atr_ratio >= 2.0:     # Fuerte
                    score += 20
                elif atr_ratio >= 1.5:     # Moderado
                    score += 10

                # Score por estructura (0-30 puntos)
                if wick_ratio <= 0.2:      # Pocas mechas (institucional)
                    score += 30
                elif wick_ratio <= 0.4:    # Mechas moderadas
                    score += 20
                elif wick_ratio <= 0.6:    # Mechas normales
                    score += 10

                candle_scores[i] = min(100, score)

            return candle_scores
        except:
            return np.zeros(len(rates))

    def calculate_volume_factor(self, rates):
        """
        Calcular factor de volumen (0-100)
        Compara volumen actual vs promedio
        """
        try:
            volume_scores = np.zeros(len(rates))
            period = self.config['volume_period']

            volumes = rates['tick_volume']

            for i in range(period, len(rates)):
                current_volume = volumes[i]
                avg_volume = np.mean(volumes[i-period:i])

                if avg_volume == 0:
                    continue

                volume_ratio = current_volume / avg_volume

                # Convertir ratio a score 0-100
                if volume_ratio >= 3.0:       # Volumen extremo
                    score = 100
                elif volume_ratio >= 2.0:     # Volumen muy alto
                    score = 80
                elif volume_ratio >= 1.5:     # Volumen alto
                    score = 60
                elif volume_ratio >= 1.2:     # Volumen moderado
                    score = 40
                elif volume_ratio >= 1.0:     # Volumen normal
                    score = 20
                else:                          # Volumen bajo
                    score = 10

                volume_scores[i] = score

            return volume_scores
        except:
            return np.zeros(len(rates))

    def calculate_velocity_factor(self, rates):
        """
        Calcular factor de velocidad (0-100)
        Velocidad = cambio de precio / tiempo
        """
        try:
            velocity_scores = np.zeros(len(rates))
            period = self.config['velocity_period']

            close_prices = rates['close']

            for i in range(period, len(rates)):
                if i < period:
                    continue

                # Calcular velocidad como % cambio por período
                price_change = close_prices[i] - close_prices[i-period]
                velocity_pct = (price_change / close_prices[i-period]) * 100

                # Convertir velocidad a score 0-100
                abs_velocity = abs(velocity_pct)

                if abs_velocity >= 2.0:       # Velocidad extrema (2%+)
                    score = 100
                elif abs_velocity >= 1.0:     # Velocidad muy alta (1%+)
                    score = 80
                elif abs_velocity >= 0.5:     # Velocidad alta (0.5%+)
                    score = 60
                elif abs_velocity >= 0.2:     # Velocidad moderada (0.2%+)
                    score = 40
                elif abs_velocity >= 0.1:     # Velocidad normal (0.1%+)
                    score = 20
                else:                          # Velocidad baja
                    score = 10

                velocity_scores[i] = score

            return velocity_scores
        except:
            return np.zeros(len(rates))

    def calculate_acceleration_factor(self, rates):
        """
        Calcular factor de aceleración (0-100)
        Aceleración = cambio en la velocidad
        """
        try:
            acceleration_scores = np.zeros(len(rates))
            vel_period = self.config['velocity_period']
            acc_period = self.config['acceleration_period']

            close_prices = rates['close']

            # Primero calcular velocidades
            velocities = np.zeros(len(rates))
            for i in range(vel_period, len(rates)):
                price_change = close_prices[i] - close_prices[i-vel_period]
                velocities[i] = (price_change / close_prices[i-vel_period]) * 100

            # Luego calcular aceleraciones
            for i in range(vel_period + acc_period, len(rates)):
                velocity_change = velocities[i] - velocities[i-acc_period]
                acceleration = abs(velocity_change)

                # Convertir aceleración a score 0-100
                if acceleration >= 1.0:       # Aceleración extrema
                    score = 100
                elif acceleration >= 0.5:     # Aceleración alta
                    score = 80
                elif acceleration >= 0.2:     # Aceleración moderada
                    score = 60
                elif acceleration >= 0.1:     # Aceleración normal
                    score = 40
                elif acceleration >= 0.05:    # Aceleración baja
                    score = 20
                else:                          # Sin aceleración
                    score = 10

                acceleration_scores[i] = score

            return acceleration_scores
        except:
            return np.zeros(len(rates))

    def calculate_ivi(self, symbol, timeframe=mt5.TIMEFRAME_M1, count=100):
        """
        Calcular IVI - Institutional Velocity Index
        Función principal del indicador
        """
        try:
            # Obtener datos
            rates = self.get_market_data(symbol, timeframe, count)
            if rates is None:
                return None, "Error obteniendo datos de mercado"

            # Calcular componentes
            candle_strength = self.calculate_candle_strength(rates)
            volume_factor = self.calculate_volume_factor(rates)
            velocity_factor = self.calculate_velocity_factor(rates)
            acceleration_factor = self.calculate_acceleration_factor(rates)

            # Calcular IVI usando pesos configurados
            ivi_values = (
                candle_strength * self.config['weight_candle'] +
                volume_factor * self.config['weight_volume'] +
                velocity_factor * self.config['weight_velocity'] +
                acceleration_factor * self.config['weight_acceleration']
            )

            # Preparar resultado detallado
            latest_idx = len(rates) - 1
            current_ivi = ivi_values[latest_idx]

            # Clasificar señal
            if current_ivi >= self.config['threshold_extreme']:
                signal_strength = "EXTREMO"
                signal_action = "ENTRADA INMEDIATA"
            elif current_ivi >= self.config['threshold_strong']:
                signal_strength = "FUERTE"
                signal_action = "PREPARAR ENTRADA"
            elif current_ivi >= self.config['threshold_moderate']:
                signal_strength = "MODERADO"
                signal_action = "VIGILAR"
            else:
                signal_strength = "NORMAL"
                signal_action = "SIN SEÑAL"

            # Determinar dirección
            current_candle = rates[latest_idx]
            direction = "ALCISTA" if current_candle['close'] > current_candle['open'] else "BAJISTA"

            result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now(),
                'ivi_value': current_ivi,
                'signal_strength': signal_strength,
                'signal_action': signal_action,
                'direction': direction,
                'components': {
                    'candle_strength': candle_strength[latest_idx],
                    'volume_factor': volume_factor[latest_idx],
                    'velocity_factor': velocity_factor[latest_idx],
                    'acceleration_factor': acceleration_factor[latest_idx]
                },
                'ivi_history': ivi_values,
                'recommendation': self.get_trading_recommendation(current_ivi, direction, signal_strength)
            }

            return result, None

        except Exception as e:
            return None, f"Error calculando IVI: {str(e)}"

    def get_trading_recommendation(self, ivi_value, direction, strength):
        """Generar recomendación de trading basada en IVI"""

        recommendations = {
            "EXTREMO": {
                "ALCISTA": "COMPRAR AHORA - Momentum institucional extremo detectado",
                "BAJISTA": "VENDER AHORA - Presión vendedora institucional extrema"
            },
            "FUERTE": {
                "ALCISTA": "PREPARAR COMPRA - Momentum alcista fuerte, esperar confirmación",
                "BAJISTA": "PREPARAR VENTA - Momentum bajista fuerte, esperar confirmación"
            },
            "MODERADO": {
                "ALCISTA": "VIGILAR - Momentum moderado alcista, sin prisa",
                "BAJISTA": "VIGILAR - Momentum moderado bajista, sin prisa"
            },
            "NORMAL": {
                "ALCISTA": "SIN ACCIÓN - Movimiento normal",
                "BAJISTA": "SIN ACCIÓN - Movimiento normal"
            }
        }

        return recommendations.get(strength, {}).get(direction, "SIN RECOMENDACIÓN")

    def print_ivi_analysis(self, result):
        """Mostrar análisis IVI de forma legible"""
        if not result:
            return

        print("=" * 80)
        print(f"    IVI - INSTITUTIONAL VELOCITY INDEX ANALYSIS")
        print("=" * 80)
        print(f"Símbolo: {result['symbol']}")
        print(f"Timestamp: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dirección: {result['direction']}")
        print()

        print(f"IVI VALOR: {result['ivi_value']:.2f}/100")
        print(f"FUERZA: {result['signal_strength']}")
        print(f"ACCIÓN: {result['signal_action']}")
        print()

        print("COMPONENTES DEL IVI:")
        print(f"  Fuerza Vela:    {result['components']['candle_strength']:.2f}/100")
        print(f"  Factor Volumen: {result['components']['volume_factor']:.2f}/100")
        print(f"  Factor Velocidad: {result['components']['velocity_factor']:.2f}/100")
        print(f"  Factor Aceleración: {result['components']['acceleration_factor']:.2f}/100")
        print()

        print(f"RECOMENDACIÓN: {result['recommendation']}")
        print("=" * 80)

def main():
    """Función principal de prueba"""
    print("=" * 80)
    print("    PROBANDO IVI - INSTITUTIONAL VELOCITY INDEX")
    print("=" * 80)

    # Crear indicador
    ivi = IVIIndicator()

    # Conectar MT5
    if not ivi.connect_mt5():
        print("Error: No se pudo conectar a MT5")
        return

    # Símbolos a analizar
    symbols = ['BTCUSDm', 'EURUSDm', 'XAUUSDm', 'GBPUSDm']

    print(f"\nAnalizando {len(symbols)} símbolos con IVI...")
    print()

    for symbol in symbols:
        print(f"Analizando {symbol}...")

        result, error = ivi.calculate_ivi(symbol)

        if error:
            print(f"Error en {symbol}: {error}")
            continue

        if result:
            ivi.print_ivi_analysis(result)

            # Guardar si es señal fuerte
            if result['ivi_value'] >= 50:
                print(f"[ALERTA] {symbol}: IVI = {result['ivi_value']:.2f} - {result['signal_action']}")

        print()

    mt5.shutdown()
    print("Análisis IVI completado.")

if __name__ == "__main__":
    main()