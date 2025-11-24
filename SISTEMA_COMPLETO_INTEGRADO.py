#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA COMPLETO INTEGRADO - DETECTOR + EJECUTOR
===============================================
Detecta oportunidades y ejecuta trades reales automáticamente
"""

import time
import sys
import os
from datetime import datetime, timedelta
import logging
import json
import threading
from src.data.twelvedata_client import TwelveDataClient
from src.notifiers.telegram_notifier import TelegramNotifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SISTEMA_INTEGRADO - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sistema_completo_integrado.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Importar MT5 si está disponible
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    logger.info("MetaTrader5 importado correctamente")
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 no disponible - modo simulación")

class SistemaCompletoIntegrado:
    def __init__(self):
        self.client = TwelveDataClient()
        self.telegram = TelegramNotifier()
        self.running = True
        self.symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']

        # Control de trades
        self.trades_ejecutados = {}
        self.ultimo_trade_timestamp = {}
        self.oportunidades_historial = []

        # Configuración mejorada
        self.config = {
            'lot_size': 0.01,
            'max_trades_per_symbol': 2,
            'min_interval_between_trades': 180,  # 3 minutos

            # Criterios de detección más sensibles
            'rsi_oversold_extremo': 30,
            'rsi_oversold_fuerte': 35,
            'rsi_overbought_fuerte': 65,
            'rsi_overbought_extremo': 70,

            # MACD
            'macd_momentum_minimo': 0.0001,

            # Bollinger Bands
            'bb_distancia_extrema': 0.08,  # 0.08% de distancia
            'bb_distancia_cerca': 0.20,     # 0.20% de distancia

            # ATR para SL/TP
            'atr_multiplier_sl': 2.0,
            'atr_multiplier_tp': 3.0,

            # Fuerza mínima para ejecutar
            'fuerza_minima_ejecucion': 6,  # De 10
        }

        # Inicializar MT5
        self.mt5_connected = self.initialize_mt5()

    def initialize_mt5(self):
        """Inicializa conexión con MetaTrader5"""
        if not MT5_AVAILABLE:
            logger.warning("MT5 no disponible - ejecutando en modo simulación")
            return False

        try:
            if not mt5.initialize():
                logger.error("Error inicializando MT5")
                return False

            account_info = mt5.account_info()
            if account_info is None:
                logger.error("No se pudo obtener información de la cuenta")
                return False

            logger.info(f"MT5 conectado - Cuenta: {account_info.login}")
            logger.info(f"Balance: {account_info.balance}")

            # Notificar por Telegram
            self.telegram.send_alert(
                'success',
                f"MT5 Conectado!\nCuenta: {account_info.login}\nBalance: ${account_info.balance:,.2f}",
                critical=True
            )

            return True

        except Exception as e:
            logger.error(f"Error conectando con MT5: {e}")
            return False

    def analizar_oportunidad_completa(self, symbol):
        """Análisis completo y puntuación de oportunidad"""
        try:
            # Obtener análisis completo
            analysis = self.client.get_complete_analysis(symbol)

            if not analysis or not analysis['price']:
                return None

            price = analysis['price']
            indicators = analysis.get('indicators', {})

            # Extraer indicadores
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)
            atr = indicators.get('atr', 0)

            # Sistema de puntuación
            puntuacion_compra = 0
            puntuacion_venta = 0
            razones = []

            # ====== ANÁLISIS RSI ======
            if rsi <= self.config['rsi_oversold_extremo']:
                puntuacion_compra += 4
                razones.append(f"RSI EXTREMO {rsi:.1f}")
            elif rsi <= self.config['rsi_oversold_fuerte']:
                puntuacion_compra += 3
                razones.append(f"RSI OVERSOLD {rsi:.1f}")

            if rsi >= self.config['rsi_overbought_extremo']:
                puntuacion_venta += 4
                razones.append(f"RSI EXTREMO {rsi:.1f}")
            elif rsi >= self.config['rsi_overbought_fuerte']:
                puntuacion_venta += 3
                razones.append(f"RSI OVERBOUGHT {rsi:.1f}")

            # ====== ANÁLISIS MACD ======
            macd_diff = macd - macd_signal
            if macd > macd_signal and abs(macd_diff) > self.config['macd_momentum_minimo']:
                if macd > 0:
                    puntuacion_compra += 3
                    razones.append("MACD ALCISTA+")
                else:
                    puntuacion_compra += 2
                    razones.append("MACD ALCISTA")

            elif macd < macd_signal and abs(macd_diff) > self.config['macd_momentum_minimo']:
                if macd < 0:
                    puntuacion_venta += 3
                    razones.append("MACD BAJISTA-")
                else:
                    puntuacion_venta += 2
                    razones.append("MACD BAJISTA")

            # ====== ANÁLISIS BOLLINGER BANDS ======
            if bb_upper and bb_lower and price:
                distancia_upper = ((bb_upper - price) / price) * 100
                distancia_lower = ((price - bb_lower) / price) * 100

                if distancia_upper <= self.config['bb_distancia_extrema']:
                    puntuacion_venta += 3
                    razones.append(f"BB UPPER {distancia_upper:.3f}%")
                elif distancia_upper <= self.config['bb_distancia_cerca']:
                    puntuacion_venta += 2
                    razones.append(f"BB UPPER CERCA")

                if distancia_lower <= self.config['bb_distancia_extrema']:
                    puntuacion_compra += 3
                    razones.append(f"BB LOWER {distancia_lower:.3f}%")
                elif distancia_lower <= self.config['bb_distancia_cerca']:
                    puntuacion_compra += 2
                    razones.append(f"BB LOWER CERCA")

            # Determinar señal
            if puntuacion_compra >= self.config['fuerza_minima_ejecucion'] and puntuacion_compra > puntuacion_venta:
                return {
                    'symbol': symbol,
                    'tipo': 'BUY',
                    'price': price,
                    'fuerza': puntuacion_compra,
                    'razones': razones,
                    'rsi': rsi,
                    'macd': macd,
                    'atr': atr,
                    'timestamp': datetime.now()
                }
            elif puntuacion_venta >= self.config['fuerza_minima_ejecucion'] and puntuacion_venta > puntuacion_compra:
                return {
                    'symbol': symbol,
                    'tipo': 'SELL',
                    'price': price,
                    'fuerza': puntuacion_venta,
                    'razones': razones,
                    'rsi': rsi,
                    'macd': macd,
                    'atr': atr,
                    'timestamp': datetime.now()
                }

            return None

        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return None

    def puede_ejecutar_trade(self, symbol):
        """Verifica si se puede ejecutar trade"""
        try:
            # Verificar intervalo mínimo
            if symbol in self.ultimo_trade_timestamp:
                tiempo_transcurrido = (datetime.now() - self.ultimo_trade_timestamp[symbol]).total_seconds()
                if tiempo_transcurrido < self.config['min_interval_between_trades']:
                    return False, f"Esperando {self.config['min_interval_between_trades'] - tiempo_transcurrido:.0f}s"

            # Verificar máximo trades
            if symbol in self.trades_ejecutados:
                if self.trades_ejecutados[symbol] >= self.config['max_trades_per_symbol']:
                    return False, f"Máximo trades alcanzado ({self.config['max_trades_per_symbol']})"

            return True, "OK"

        except Exception as e:
            return False, f"Error: {e}"

    def ejecutar_trade_mt5(self, oportunidad):
        """Ejecuta trade real en MT5"""
        symbol = oportunidad['symbol']
        trade_type = oportunidad['tipo']
        price = oportunidad['price']
        atr = oportunidad.get('atr', 0)

        if not self.mt5_connected:
            logger.info(f"SIMULACIÓN: {trade_type} {symbol} @ {price:.6f} Fuerza:{oportunidad['fuerza']}")
            return True

        try:
            # Calcular SL y TP
            if not atr or atr == 0:
                atr = price * 0.001  # 0.1% como fallback

            if trade_type == "BUY":
                sl = price - (atr * self.config['atr_multiplier_sl'])
                tp = price + (atr * self.config['atr_multiplier_tp'])
            else:  # SELL
                sl = price + (atr * self.config['atr_multiplier_sl'])
                tp = price - (atr * self.config['atr_multiplier_tp'])

            # Preparar request
            action = mt5.TRADE_ACTION_DEAL
            type_trade = mt5.ORDER_TYPE_BUY if trade_type == "BUY" else mt5.ORDER_TYPE_SELL

            request = {
                "action": action,
                "symbol": symbol,
                "volume": self.config['lot_size'],
                "type": type_trade,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": "Sistema Integrado v3",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Enviar orden
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Error ejecutando trade {symbol}: {result.retcode}")
                return False

            logger.info(f"TRADE EJECUTADO: {trade_type} {symbol} Ticket: {result.order}")

            # Notificar por Telegram
            signal_data = {
                'symbol': symbol,
                'type': trade_type,
                'price': price,
                'sl': sl,
                'tp': tp,
                'strength': oportunidad['fuerza'] / 10.0,
                'strategy': 'Sistema Integrado v3',
                'timeframe': '5M',
                'reason': ', '.join(oportunidad['razones'][:3])
            }
            self.telegram.send_signal(signal_data)

            # Actualizar contadores
            if symbol not in self.trades_ejecutados:
                self.trades_ejecutados[symbol] = 0
            self.trades_ejecutados[symbol] += 1
            self.ultimo_trade_timestamp[symbol] = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Error ejecutando trade MT5: {e}")
            return False

    def ciclo_completo(self):
        """Ejecuta un ciclo completo de detección y ejecución"""
        inicio = datetime.now()
        logger.info(f"")
        logger.info(f"CICLO SISTEMA INTEGRADO - {inicio.strftime('%H:%M:%S')}")
        logger.info(f"=" * 60)

        oportunidades_detectadas = []
        trades_ejecutados = []

        for symbol in self.symbols:
            logger.info(f"Analizando {symbol}...")

            # Detectar oportunidad
            oportunidad = self.analizar_oportunidad_completa(symbol)

            if oportunidad:
                oportunidades_detectadas.append(oportunidad)
                logger.info(f"  OPORTUNIDAD: {oportunidad['tipo']} Fuerza:{oportunidad['fuerza']}/10")
                logger.info(f"  Razones: {', '.join(oportunidad['razones'])}")

                # Verificar si se puede ejecutar
                puede_ejecutar, motivo = self.puede_ejecutar_trade(symbol)

                if puede_ejecutar:
                    logger.info(f"  Ejecutando trade...")
                    if self.ejecutar_trade_mt5(oportunidad):
                        trades_ejecutados.append(oportunidad)
                        logger.info(f"  TRADE EJECUTADO EXITOSAMENTE")
                    else:
                        logger.error(f"  Error ejecutando trade")
                else:
                    logger.info(f"  No se puede ejecutar: {motivo}")
            else:
                logger.info(f"  Sin oportunidades detectadas")

        # Resumen del ciclo
        fin = datetime.now()
        duracion = (fin - inicio).total_seconds()

        logger.info(f"")
        logger.info(f"RESUMEN DEL CICLO:")
        logger.info(f"  Duración: {duracion:.1f}s")
        logger.info(f"  Oportunidades detectadas: {len(oportunidades_detectadas)}")
        logger.info(f"  Trades ejecutados: {len(trades_ejecutados)}")

        if trades_ejecutados:
            logger.info(f"  Detalles de trades:")
            for trade in trades_ejecutados:
                logger.info(f"    {trade['tipo']} {trade['symbol']} @ {trade['price']:.6f}")

        return len(oportunidades_detectadas), len(trades_ejecutados)

    def run(self):
        """Ejecuta el sistema completo integrado"""
        logger.info(f"")
        logger.info(f"INICIANDO SISTEMA COMPLETO INTEGRADO")
        logger.info(f"MT5 Conectado: {'SÍ' if self.mt5_connected else 'NO (Simulación)'}")
        logger.info(f"Símbolos: {', '.join(self.symbols)}")
        logger.info(f"Tamaño lote: {self.config['lot_size']}")
        logger.info(f"Fuerza mínima: {self.config['fuerza_minima_ejecucion']}/10")
        logger.info(f"Intervalo: 30 segundos")
        logger.info(f"")

        ciclo_count = 0
        total_oportunidades = 0
        total_trades = 0

        try:
            while self.running:
                ciclo_count += 1
                logger.info(f"CICLO #{ciclo_count}")

                # Ejecutar ciclo completo
                oportunidades, trades = self.ciclo_completo()
                total_oportunidades += oportunidades
                total_trades += trades

                # Estadísticas cada 10 ciclos
                if ciclo_count % 10 == 0:
                    logger.info(f"")
                    logger.info(f"ESTADÍSTICAS (últimos 10 ciclos):")
                    logger.info(f"  Total oportunidades: {total_oportunidades}")
                    logger.info(f"  Total trades: {total_trades}")
                    if total_oportunidades > 0:
                        eficiencia = (total_trades / total_oportunidades) * 100
                        logger.info(f"  Eficiencia ejecución: {eficiencia:.1f}%")

                    # Reset contadores
                    total_oportunidades = 0
                    total_trades = 0

                # Pausa 30 segundos
                logger.info(f"Próximo ciclo en 30 segundos...")
                time.sleep(30)

        except KeyboardInterrupt:
            logger.info("Deteniendo sistema por interrupción del usuario...")
        except Exception as e:
            logger.error(f"Error crítico: {e}")
        finally:
            if self.mt5_connected:
                mt5.shutdown()
            logger.info("Sistema completo integrado detenido")

def main():
    """Función principal"""
    print("SISTEMA COMPLETO INTEGRADO")
    print("DETECTOR + EJECUTOR AUTOMÁTICO")
    print("=" * 50)

    # Crear y ejecutar sistema
    sistema = SistemaCompletoIntegrado()
    sistema.run()

if __name__ == "__main__":
    main()