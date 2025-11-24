#!/usr/bin/env python
"""
AI SIGNAL ALERT SYSTEM - SISTEMA DE ALERTAS INTELIGENTE
========================================================
Analiza señales en tiempo real y genera alertas fuertes con predicciones
"""

import os
import sys
import time
import requests
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import json

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

class AISignalAlertSystem:
    """Sistema de Alertas IA con análisis predictivo"""

    def __init__(self):
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'
        self.base_url = 'https://api.twelvedata.com'

        # Símbolos a monitorear
        self.symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD', 'GBPUSD', 'USDJPY', 'ETHUSDm']

        # Configuración de alertas
        self.alert_config = {
            'min_signal_strength': 70,      # Fuerza mínima para alerta
            'confluence_threshold': 3,      # Mínimo de confluencias
            'prediction_confidence': 75,    # Confianza para predicción
            'urgent_alert_level': 85,      # Nivel para alerta URGENTE
            'telegram_alerts': True
        }

        # Cache de análisis
        self.signal_history = {}
        self.predictions = {}
        self.alerts_generated = []

        # Conectar MT5
        self.mt5_connected = self.connect_mt5()

        print("=" * 80)
        print("    AI SIGNAL ALERT SYSTEM - SISTEMA DE ALERTAS INTELIGENTE")
        print("=" * 80)
        print("- Análisis en tiempo real de 6 pares principales")
        print("- Predicciones de próximas señales con IA")
        print("- Alertas fuertes para oportunidades inmediatas")
        print("- Insights predictivos basados en patrones")
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
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Conectando MT5: {e}")
            return False

    def get_market_data(self, symbol):
        """Obtener datos de mercado actualizados"""
        try:
            # Mapear símbolos para API
            symbol_map = {
                'BTCUSDm': 'BTC/USD',
                'XAUUSDm': 'XAU/USD',
                'EURUSD': 'EUR/USD',
                'GBPUSD': 'GBP/USD',
                'USDJPY': 'USD/JPY',
                'ETHUSDm': 'ETH/USD'
            }

            api_symbol = symbol_map.get(symbol, symbol)

            # Obtener datos de precio
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': api_symbol,
                'interval': '5min',
                'outputsize': 50,
                'apikey': self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    return data['values']

            return None

        except Exception as e:
            print(f"[ERROR] Obteniendo datos {symbol}: {e}")
            return None

    def calculate_technical_indicators(self, data):
        """Calcular indicadores técnicos"""
        try:
            if not data or len(data) < 20:
                return {}

            closes = [float(d['close']) for d in data]
            highs = [float(d['high']) for d in data]
            lows = [float(d['low']) for d in data]

            # RSI
            rsi = self.calculate_rsi(closes, 14)

            # MACD
            macd, signal, histogram = self.calculate_macd(closes)

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger(closes, 20)

            # ATR
            atr = self.calculate_atr(highs, lows, closes, 14)

            # Momentum
            momentum = (closes[0] - closes[9]) / closes[9] * 100 if len(closes) > 9 else 0

            return {
                'rsi': rsi,
                'macd': macd,
                'macd_signal': signal,
                'macd_histogram': histogram,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'atr': atr,
                'momentum': momentum,
                'current_price': closes[0],
                'price_change_5m': (closes[0] - closes[1]) / closes[1] * 100 if len(closes) > 1 else 0,
                'price_change_1h': (closes[0] - closes[12]) / closes[12] * 100 if len(closes) > 12 else 0
            }

        except Exception as e:
            print(f"[ERROR] Calculando indicadores: {e}")
            return {}

    def calculate_rsi(self, prices, period=14):
        """Calcular RSI"""
        if len(prices) < period + 1:
            return 50

        gains = []
        losses = []

        for i in range(1, period + 1):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcular MACD"""
        if len(prices) < slow:
            return 0, 0, 0

        # EMA rápida
        ema_fast = self.calculate_ema(prices, fast)
        # EMA lenta
        ema_slow = self.calculate_ema(prices, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema([macd_line], signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_ema(self, prices, period):
        """Calcular EMA"""
        if len(prices) < period:
            return prices[0] if prices else 0

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def calculate_bollinger(self, prices, period=20):
        """Calcular Bandas de Bollinger"""
        if len(prices) < period:
            return prices[0], prices[0], prices[0]

        sma = sum(prices[:period]) / period
        std = np.std(prices[:period])

        upper = sma + (std * 2)
        lower = sma - (std * 2)

        return upper, sma, lower

    def calculate_atr(self, highs, lows, closes, period=14):
        """Calcular ATR"""
        if len(highs) < period + 1:
            return 0

        trs = []
        for i in range(1, period + 1):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            trs.append(tr)

        return sum(trs) / len(trs)

    def analyze_signal_strength(self, symbol, indicators):
        """Analizar fuerza de señal con IA"""
        try:
            strength_score = 0
            confluences = []
            direction = "NEUTRAL"

            # Análisis RSI
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                strength_score += 20
                confluences.append("RSI_SOBREVENTA")
                direction = "BUY"
            elif rsi > 70:
                strength_score += 20
                confluences.append("RSI_SOBRECOMPRA")
                direction = "SELL"

            # Análisis MACD
            macd_hist = indicators.get('macd_histogram', 0)
            if macd_hist > 0:
                strength_score += 15
                confluences.append("MACD_ALCISTA")
                if direction == "NEUTRAL":
                    direction = "BUY"
            elif macd_hist < 0:
                strength_score += 15
                confluences.append("MACD_BAJISTA")
                if direction == "NEUTRAL":
                    direction = "SELL"

            # Análisis Bollinger
            price = indicators.get('current_price', 0)
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)

            if price <= bb_lower:
                strength_score += 20
                confluences.append("PRECIO_BANDA_INFERIOR")
                if direction != "SELL":
                    direction = "BUY"
            elif price >= bb_upper:
                strength_score += 20
                confluences.append("PRECIO_BANDA_SUPERIOR")
                if direction != "BUY":
                    direction = "SELL"

            # Análisis Momentum
            momentum = indicators.get('momentum', 0)
            if abs(momentum) > 2:
                strength_score += 15
                if momentum > 0:
                    confluences.append("MOMENTUM_ALCISTA_FUERTE")
                else:
                    confluences.append("MOMENTUM_BAJISTA_FUERTE")

            # Análisis de cambio de precio
            price_change_1h = indicators.get('price_change_1h', 0)
            if abs(price_change_1h) > 1:
                strength_score += 10
                if price_change_1h > 0:
                    confluences.append("TENDENCIA_1H_ALCISTA")
                else:
                    confluences.append("TENDENCIA_1H_BAJISTA")

            # Bonus por múltiples confluencias
            if len(confluences) >= self.alert_config['confluence_threshold']:
                strength_score += 20

            return {
                'symbol': symbol,
                'direction': direction,
                'strength': min(strength_score, 100),
                'confluences': confluences,
                'indicators': indicators,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"[ERROR] Analizando señal {symbol}: {e}")
            return None

    def predict_next_signal(self, symbol, signal_analysis):
        """Predecir próxima señal con IA"""
        try:
            prediction = {
                'symbol': symbol,
                'current_signal': signal_analysis['direction'],
                'next_signal_time': "PRÓXIMOS 15-30 MIN",
                'predicted_direction': "NEUTRAL",
                'confidence': 0,
                'key_levels': {},
                'insights': []
            }

            indicators = signal_analysis['indicators']

            # Análisis predictivo basado en patrones
            rsi = indicators.get('rsi', 50)
            momentum = indicators.get('momentum', 0)
            macd_hist = indicators.get('macd_histogram', 0)

            # Predicción basada en RSI
            if rsi < 25:
                prediction['predicted_direction'] = "STRONG_BUY"
                prediction['confidence'] += 30
                prediction['insights'].append("RSI extremadamente sobreventa - Rebote inminente")
            elif rsi > 75:
                prediction['predicted_direction'] = "STRONG_SELL"
                prediction['confidence'] += 30
                prediction['insights'].append("RSI extremadamente sobrecomprada - Corrección esperada")

            # Predicción basada en divergencias
            if momentum > 0 and macd_hist < 0:
                prediction['insights'].append("DIVERGENCIA detectada - Posible cambio de tendencia")
                prediction['confidence'] += 20

            # Niveles clave
            price = indicators.get('current_price', 0)
            atr = indicators.get('atr', 0)

            prediction['key_levels'] = {
                'resistance_1': price + atr,
                'resistance_2': price + (atr * 2),
                'support_1': price - atr,
                'support_2': price - (atr * 2),
                'breakout_level': price + (atr * 1.5),
                'stop_loss_suggested': price - (atr * 1.5) if signal_analysis['direction'] == "BUY" else price + (atr * 1.5)
            }

            # Timing prediction
            if len(signal_analysis['confluences']) >= 4:
                prediction['next_signal_time'] = "PRÓXIMOS 5-15 MIN"
                prediction['confidence'] += 25
                prediction['insights'].append("Alta confluencia - Señal inminente")

            # Ajustar confianza final
            prediction['confidence'] = min(prediction['confidence'] + len(signal_analysis['confluences']) * 10, 100)

            return prediction

        except Exception as e:
            print(f"[ERROR] Prediciendo señal {symbol}: {e}")
            return None

    def generate_alert(self, signal_analysis, prediction):
        """Generar alerta fuerte"""
        try:
            symbol = signal_analysis['symbol']
            strength = signal_analysis['strength']
            direction = signal_analysis['direction']

            # Determinar nivel de alerta
            if strength >= self.alert_config['urgent_alert_level']:
                alert_level = "URGENTE"
                alert_icon = "🚨🚨🚨"
            elif strength >= self.alert_config['min_signal_strength']:
                alert_level = "FUERTE"
                alert_icon = "⚠️⚠️"
            else:
                return None  # No generar alerta si no es fuerte

            # Crear mensaje de alerta
            alert_message = f"""
{alert_icon} ALERTA {alert_level} - {symbol} {alert_icon}
{'=' * 60}
📊 SEÑAL: {direction} ({strength}%)
💎 CONFLUENCIAS: {len(signal_analysis['confluences'])}
   {' | '.join(signal_analysis['confluences'][:3])}

📈 NIVELES CLAVE:
   Precio actual: ${signal_analysis['indicators']['current_price']:.4f}
   Stop Loss: ${prediction['key_levels']['stop_loss_suggested']:.4f}
   Target 1: ${prediction['key_levels']['resistance_1' if direction == 'BUY' else 'support_1']:.4f}
   Target 2: ${prediction['key_levels']['resistance_2' if direction == 'BUY' else 'support_2']:.4f}

🔮 PREDICCIÓN PRÓXIMA:
   Tiempo: {prediction['next_signal_time']}
   Dirección esperada: {prediction['predicted_direction']}
   Confianza: {prediction['confidence']}%

💡 INSIGHTS:
   {chr(10).join(['• ' + i for i in prediction['insights'][:3]])}

⏰ Generada: {datetime.now().strftime('%H:%M:%S')}
{'=' * 60}
"""

            # Guardar alerta
            alert_data = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'level': alert_level,
                'strength': strength,
                'direction': direction,
                'message': alert_message,
                'prediction': prediction
            }

            self.alerts_generated.append(alert_data)

            # Enviar a Telegram si está configurado
            if self.alert_config['telegram_alerts']:
                self.send_telegram_alert(alert_message)

            return alert_data

        except Exception as e:
            print(f"[ERROR] Generando alerta: {e}")
            return None

    def send_telegram_alert(self, message):
        """Enviar alerta por Telegram"""
        try:
            from src.notifiers.telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier()
            notifier.send_message(message)
            print("[OK] Alerta enviada por Telegram")
        except:
            print("[INFO] Telegram no disponible")

    def run_analysis_cycle(self):
        """Ejecutar ciclo completo de análisis"""
        print(f"\n{'=' * 80}")
        print(f"🔍 ANALIZANDO SEÑALES - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'=' * 80}")

        strong_signals = []
        all_predictions = {}

        for symbol in self.symbols:
            print(f"\n📊 Analizando {symbol}...", end=" ")

            # Obtener datos de mercado
            market_data = self.get_market_data(symbol)
            if not market_data:
                print("❌ Sin datos")
                continue

            # Calcular indicadores
            indicators = self.calculate_technical_indicators(market_data)
            if not indicators:
                print("❌ Error indicadores")
                continue

            # Analizar señal
            signal_analysis = self.analyze_signal_strength(symbol, indicators)
            if not signal_analysis:
                print("❌ Error análisis")
                continue

            # Predecir próxima señal
            prediction = self.predict_next_signal(symbol, signal_analysis)
            all_predictions[symbol] = prediction

            # Mostrar resultado
            strength = signal_analysis['strength']
            if strength >= self.alert_config['min_signal_strength']:
                strong_signals.append(signal_analysis)
                print(f"🔥 SEÑAL FUERTE ({strength}%)")

                # Generar alerta si es necesario
                alert = self.generate_alert(signal_analysis, prediction)
                if alert:
                    print(alert['message'])
            else:
                print(f"✅ Normal ({strength}%)")

            time.sleep(0.5)  # Pequeña pausa entre símbolos

        # Resumen de señales fuertes
        if strong_signals:
            print(f"\n{'=' * 80}")
            print(f"⚡ RESUMEN DE SEÑALES FUERTES")
            print(f"{'=' * 80}")

            # Ordenar por fuerza
            strong_signals.sort(key=lambda x: x['strength'], reverse=True)

            for i, signal in enumerate(strong_signals[:3], 1):
                print(f"\n{i}. {signal['symbol']} - {signal['direction']} ({signal['strength']}%)")
                print(f"   Confluencias: {', '.join(signal['confluences'][:3])}")

                pred = all_predictions.get(signal['symbol'])
                if pred:
                    print(f"   Predicción: {pred['predicted_direction']} en {pred['next_signal_time']}")
                    print(f"   Confianza: {pred['confidence']}%")
        else:
            print(f"\n📊 No hay señales fuertes en este momento")

        # Estadísticas
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   Símbolos analizados: {len(self.symbols)}")
        print(f"   Señales fuertes: {len(strong_signals)}")
        print(f"   Alertas generadas: {len([a for a in self.alerts_generated if (datetime.now() - a['timestamp']).seconds < 300])}")

        return strong_signals, all_predictions

    def run_continuous_monitoring(self, interval=30):
        """Monitoreo continuo con alertas"""
        try:
            print(f"\n🚀 INICIANDO MONITOREO CONTINUO")
            print(f"⏰ Análisis cada {interval} segundos")
            print(f"Presiona Ctrl+C para detener")
            print("=" * 80)

            cycle = 0

            while True:
                cycle += 1
                print(f"\n🔄 CICLO #{cycle:03d}")

                # Ejecutar análisis
                strong_signals, predictions = self.run_analysis_cycle()

                # Mostrar próxima actualización
                print(f"\n⏰ Próximo análisis en {interval} segundos...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Monitoreo detenido por usuario")

            # Mostrar resumen final
            if self.alerts_generated:
                print(f"\n📊 RESUMEN DE ALERTAS GENERADAS:")
                print(f"Total: {len(self.alerts_generated)}")

                # Últimas 3 alertas
                for alert in self.alerts_generated[-3:]:
                    print(f"- {alert['symbol']} {alert['direction']} ({alert['strength']}%) - {alert['timestamp'].strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"❌ Error en monitoreo: {e}")

        finally:
            if self.mt5_connected:
                mt5.shutdown()
            print("Sistema de alertas finalizado")

def main():
    """Función principal"""
    system = AISignalAlertSystem()

    # Ejecutar análisis inicial
    print("\n📊 ANÁLISIS INICIAL...")
    strong_signals, predictions = system.run_analysis_cycle()

    if strong_signals:
        print(f"\n✅ {len(strong_signals)} señales fuertes detectadas")
        print("¿Desea iniciar monitoreo continuo? (Enter para continuar, Ctrl+C para salir)")
    else:
        print("\n📊 No hay señales fuertes en este momento")
        print("¿Desea iniciar monitoreo continuo? (Enter para continuar, Ctrl+C para salir)")

    try:
        input()
        # Iniciar monitoreo continuo
        system.run_continuous_monitoring(interval=30)
    except KeyboardInterrupt:
        print("\n🛑 Sistema cancelado")

if __name__ == "__main__":
    main()