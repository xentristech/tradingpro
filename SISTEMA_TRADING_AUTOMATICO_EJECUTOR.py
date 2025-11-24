#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA TRADING AUTOMATICO EJECUTOR
===================================
¡EJECUTA TRADES REALES EN MT5 CUANDO DETECTA SEÑALES!
"""

import time
import sys
import os
from datetime import datetime, timedelta
import logging
import json
import pandas as pd
import numpy as np
from src.data.twelvedata_client import TwelveDataClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TRADING_EJECUTOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_automatico_ejecutor.log', encoding='utf-8'),
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

class TradingAutomaticoEjecutor:
    def __init__(self):
        self.client = TwelveDataClient()
        self.running = True
        self.symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']

        # Configuración de trading
        self.config = {
            'lot_size': 0.01,  # Tamaño de lote pequeño para seguridad
            'max_trades_per_symbol': 1,  # Máximo 1 trade por símbolo
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'rsi_oversold_medium': 35,
            'rsi_overbought_medium': 65,
            'atr_multiplier_sl': 2.0,  # Stop Loss = 2 * ATR
            'atr_multiplier_tp': 3.0,  # Take Profit = 3 * ATR
            'min_interval_between_trades': 300,  # 5 minutos entre trades del mismo símbolo
        }

        # Control de trades
        self.trades_ejecutados = {}
        self.ultimo_trade_timestamp = {}

        # Inicializar MT5
        self.mt5_connected = self.initialize_mt5()

    def initialize_mt5(self):
        """Inicializa conexión con MetaTrader5"""
        if not MT5_AVAILABLE:
            logger.warning("MT5 no disponible - ejecutando en modo simulación")
            return False

        try:
            # Inicializar MT5
            if not mt5.initialize():
                logger.error("Error inicializando MT5")
                return False

            # Verificar conexión
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("No se pudo obtener información de la cuenta")
                return False

            logger.info(f"MT5 conectado - Cuenta: {account_info.login}")
            logger.info(f"Balance: {account_info.balance}")
            logger.info(f"Equity: {account_info.equity}")

            return True

        except Exception as e:
            logger.error(f"Error conectando con MT5: {e}")
            return False

    def can_trade_symbol(self, symbol):
        """Verifica si se puede hacer trade del símbolo"""
        try:
            # Verificar intervalo mínimo entre trades
            if symbol in self.ultimo_trade_timestamp:
                time_since_last = (datetime.now() - self.ultimo_trade_timestamp[symbol]).total_seconds()
                if time_since_last < self.config['min_interval_between_trades']:
                    logger.info(f"  {symbol}: Esperando {self.config['min_interval_between_trades'] - time_since_last:.0f}s para próximo trade")
                    return False

            # Verificar máximo trades por símbolo
            if symbol in self.trades_ejecutados:
                if self.trades_ejecutados[symbol] >= self.config['max_trades_per_symbol']:
                    logger.info(f"  {symbol}: Máximo trades alcanzado ({self.config['max_trades_per_symbol']})")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error verificando si puede hacer trade {symbol}: {e}")
            return False

    def execute_trade_mt5(self, symbol, trade_type, price, sl, tp):
        """Ejecuta trade real en MT5"""
        if not self.mt5_connected:
            logger.warning(f"  SIMULACIÓN: {trade_type} {symbol} a {price:.6f} SL:{sl:.6f} TP:{tp:.6f}")
            return True

        try:
            # Preparar request de trade
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
                "comment": "Trading Automatico v3",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Enviar orden
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"  Error ejecutando trade {symbol}: {result.retcode} - {result.comment}")
                return False

            logger.info(f"  ✅ TRADE EJECUTADO: {trade_type} {symbol} Ticket: {result.order}")
            logger.info(f"     Precio: {price:.6f} | SL: {sl:.6f} | TP: {tp:.6f}")

            return True

        except Exception as e:
            logger.error(f"Error ejecutando trade MT5 {symbol}: {e}")
            return False

    def analyze_and_execute(self, symbol):
        """Analiza símbolo y ejecuta trade si detecta señal"""
        try:
            logger.info(f"🔍 Analizando {symbol}...")

            # Verificar si se puede hacer trade
            if not self.can_trade_symbol(symbol):
                return None

            # Obtener análisis completo
            analysis = self.client.get_complete_analysis(symbol)

            if not analysis or not analysis['price']:
                logger.warning(f"  No se pudo obtener análisis de {symbol}")
                return None

            price = analysis['price']
            indicators = analysis.get('indicators', {})

            # Extraer indicadores
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            atr = indicators.get('atr', 0)
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)

            logger.info(f"  💰 Precio: {price:.6f}")
            logger.info(f"  📊 RSI: {rsi:.1f} | MACD: {macd:.4f} | ATR: {atr:.6f}")

            # LÓGICA DE TRADING MEJORADA
            trade_signal = None
            trade_reason = []

            # ========== SEÑALES DE COMPRA ==========
            buy_signals = 0

            # RSI oversold
            if rsi <= self.config['rsi_oversold']:
                buy_signals += 3  # Señal muy fuerte
                trade_reason.append(f"RSI {rsi:.1f} EXTREMO OVERSOLD")
            elif rsi <= self.config['rsi_oversold_medium']:
                buy_signals += 2  # Señal fuerte
                trade_reason.append(f"RSI {rsi:.1f} OVERSOLD")

            # MACD alcista
            if macd > macd_signal and macd > 0:
                buy_signals += 2
                trade_reason.append("MACD ALCISTA")
            elif macd > macd_signal:
                buy_signals += 1
                trade_reason.append("MACD CRUCE ALCISTA")

            # Bollinger Bands - precio cerca del límite inferior
            if bb_lower and price <= bb_lower * 1.002:  # 0.2% tolerancia
                buy_signals += 2
                trade_reason.append("PRECIO EN BB LOWER")

            # ========== SEÑALES DE VENTA ==========
            sell_signals = 0

            # RSI overbought
            if rsi >= self.config['rsi_overbought']:
                sell_signals += 3  # Señal muy fuerte
                trade_reason.append(f"RSI {rsi:.1f} EXTREMO OVERBOUGHT")
            elif rsi >= self.config['rsi_overbought_medium']:
                sell_signals += 2  # Señal fuerte
                trade_reason.append(f"RSI {rsi:.1f} OVERBOUGHT")

            # MACD bajista
            if macd < macd_signal and macd < 0:
                sell_signals += 2
                trade_reason.append("MACD BAJISTA")
            elif macd < macd_signal:
                sell_signals += 1
                trade_reason.append("MACD CRUCE BAJISTA")

            # Bollinger Bands - precio cerca del límite superior
            if bb_upper and price >= bb_upper * 0.998:  # 0.2% tolerancia
                sell_signals += 2
                trade_reason.append("PRECIO EN BB UPPER")

            # ========== DECISIÓN DE TRADE ==========
            min_signal_strength = 3  # Mínimo 3 puntos para ejecutar trade

            if buy_signals >= min_signal_strength and buy_signals > sell_signals:
                trade_signal = "BUY"
                logger.info(f"  🟢 SEÑAL DE COMPRA DETECTADA (Fuerza: {buy_signals})")

            elif sell_signals >= min_signal_strength and sell_signals > buy_signals:
                trade_signal = "SELL"
                logger.info(f"  🔴 SEÑAL DE VENTA DETECTADA (Fuerza: {sell_signals})")

            else:
                logger.info(f"  ⚪ SIN SEÑAL (Compra: {buy_signals}, Venta: {sell_signals})")
                return None

            # ========== CALCULAR SL y TP ==========
            if not atr or atr == 0:
                logger.warning(f"  ATR no disponible para {symbol}, usando 0.1% del precio")
                atr = price * 0.001  # 0.1% del precio como fallback

            if trade_signal == "BUY":
                sl = price - (atr * self.config['atr_multiplier_sl'])
                tp = price + (atr * self.config['atr_multiplier_tp'])
            else:  # SELL
                sl = price + (atr * self.config['atr_multiplier_sl'])
                tp = price - (atr * self.config['atr_multiplier_tp'])

            # ========== EJECUTAR TRADE ==========
            logger.info(f"  🎯 Razones: {', '.join(trade_reason)}")
            logger.info(f"  💼 Ejecutando {trade_signal} - SL: {sl:.6f} TP: {tp:.6f}")

            # Ejecutar trade
            if self.execute_trade_mt5(symbol, trade_signal, price, sl, tp):
                # Actualizar contadores
                if symbol not in self.trades_ejecutados:
                    self.trades_ejecutados[symbol] = 0
                self.trades_ejecutados[symbol] += 1
                self.ultimo_trade_timestamp[symbol] = datetime.now()

                # Log del trade
                trade_info = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'type': trade_signal,
                    'price': price,
                    'sl': sl,
                    'tp': tp,
                    'reasons': trade_reason,
                    'rsi': rsi,
                    'macd': macd,
                    'atr': atr
                }

                self.save_trade_log(trade_info)

                return trade_info

            return None

        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return None

    def save_trade_log(self, trade_info):
        """Guarda log de trades ejecutados"""
        try:
            log_file = f"trades_ejecutados_{datetime.now().strftime('%Y%m%d')}.json"

            # Leer trades existentes
            trades = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    trades = json.load(f)

            # Agregar nuevo trade
            trades.append(trade_info)

            # Guardar
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(trades, f, indent=2, ensure_ascii=False)

            logger.info(f"📝 Trade guardado en {log_file}")

        except Exception as e:
            logger.error(f"Error guardando trade log: {e}")

    def run_cycle(self):
        """Ejecuta un ciclo completo de análisis y trading"""
        cycle_start = datetime.now()
        logger.info(f"")
        logger.info(f"🚀 CICLO TRADING AUTOMÁTICO - {cycle_start.strftime('%H:%M:%S')}")
        logger.info(f"{'='*60}")

        trades_ejecutados_ciclo = []

        for symbol in self.symbols:
            trade_info = self.analyze_and_execute(symbol)
            if trade_info:
                trades_ejecutados_ciclo.append(trade_info)

        # Resumen del ciclo
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()

        logger.info(f"")
        logger.info(f"📊 RESUMEN DEL CICLO:")
        logger.info(f"   ⏱️ Duración: {duration:.1f} segundos")
        logger.info(f"   💼 Trades ejecutados: {len(trades_ejecutados_ciclo)}")

        if trades_ejecutados_ciclo:
            logger.info(f"   🎯 Detalles:")
            for trade in trades_ejecutados_ciclo:
                logger.info(f"      {trade['type']} {trade['symbol']} @ {trade['price']:.6f}")

        logger.info(f"")
        return trades_ejecutados_ciclo

    def run(self):
        """Ejecuta el sistema de trading automático"""
        logger.info(f"")
        logger.info(f"🚀 INICIANDO SISTEMA TRADING AUTOMÁTICO EJECUTOR")
        logger.info(f"💼 MT5 Conectado: {'SÍ' if self.mt5_connected else 'NO (Simulación)'}")
        logger.info(f"📊 Símbolos: {', '.join(self.symbols)}")
        logger.info(f"💰 Tamaño lote: {self.config['lot_size']}")
        logger.info(f"⏰ Intervalo entre trades: {self.config['min_interval_between_trades']}s")
        logger.info(f"")

        cycle_count = 0

        try:
            while self.running:
                cycle_count += 1
                logger.info(f"CICLO #{cycle_count}")

                # Ejecutar ciclo de trading
                trades = self.run_cycle()

                # Pausa 30 segundos
                logger.info(f"⏳ Próximo ciclo en 30 segundos...")
                time.sleep(30)

        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo sistema por interrupción del usuario...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}")
            self.running = False
        finally:
            if self.mt5_connected:
                mt5.shutdown()
            logger.info("🏁 Sistema de trading automático detenido")

def main():
    """Función principal"""
    print("SISTEMA TRADING AUTOMATICO EJECUTOR")
    print("EJECUTA TRADES REALES CUANDO DETECTA SEÑALES")
    print("=" * 50)

    # Crear y ejecutar sistema
    ejecutor = TradingAutomaticoEjecutor()
    ejecutor.run()

if __name__ == "__main__":
    main()