#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA DE MONITOREO MULTI-TIMEFRAME
====================================
Monitoreo específico para cada minuto y cada 5 minutos
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
import threading

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR_MULTI - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoreo_multi_timeframe.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MonitoreoMultiTimeframe:
    def __init__(self):
        self.client = TwelveDataClient()
        self.running = True
        self.symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']

        # Contadores
        self.ciclo_1min = 0
        self.ciclo_5min = 0

        # Historiales
        self.historial_1min = []
        self.historial_5min = []
        self.alertas_activas = []

    def monitoreo_1_minuto(self):
        """
        🔥 MONITOREO CADA MINUTO - SCALPING Y MICRO SEÑALES
        =================================================
        """
        self.ciclo_1min += 1
        timestamp = datetime.now()

        logger.info(f"")
        logger.info(f"⚡ MONITOREO 1 MINUTO - Ciclo #{self.ciclo_1min}")
        logger.info(f"🕐 {timestamp.strftime('%H:%M:%S')}")
        logger.info(f"{'='*50}")

        datos_1min = {
            'timestamp': timestamp,
            'ciclo': self.ciclo_1min,
            'alertas': [],
            'señales_scalping': [],
            'velas_institucionales': [],
            'cambios_momentum': []
        }

        for symbol in self.symbols:
            logger.info(f"📊 Analizando {symbol}...")

            try:
                # 1. PRECIO Y CAMBIO INMEDIATO
                price = self.client.get_realtime_price(symbol)
                if price:
                    logger.info(f"   💰 Precio actual: {price:.6f}")

                # 2. INDICADORES RÁPIDOS (RSI, MACD para scalping)
                indicators = self.client.get_technical_indicators(symbol, '1min')

                if indicators:
                    rsi = indicators.get('rsi', 50)
                    macd = indicators.get('macd', 0)
                    macd_signal = indicators.get('macd_signal', 0)

                    logger.info(f"   📈 RSI: {rsi:.1f} | MACD: {macd:.4f}")

                    # 3. DETECTAR MICRO SEÑALES
                    if rsi >= 75:
                        alerta = f"🚨 {symbol} RSI EXTREMO: {rsi:.1f} - POSIBLE VENTA"
                        logger.warning(alerta)
                        datos_1min['alertas'].append(alerta)

                    elif rsi <= 25:
                        alerta = f"🚨 {symbol} RSI EXTREMO: {rsi:.1f} - POSIBLE COMPRA"
                        logger.warning(alerta)
                        datos_1min['alertas'].append(alerta)

                    # 4. CRUCE DE MACD RÁPIDO
                    if macd > macd_signal and macd > 0:
                        señal = f"⚡ {symbol} MACD CRUCE ALCISTA - SCALPING COMPRA"
                        logger.info(señal)
                        datos_1min['señales_scalping'].append(señal)

                    elif macd < macd_signal and macd < 0:
                        señal = f"⚡ {symbol} MACD CRUCE BAJISTA - SCALPING VENTA"
                        logger.info(señal)
                        datos_1min['señales_scalping'].append(señal)

                # 5. DETECTAR VELAS INSTITUCIONALES (VOLUMEN ALTO)
                df = self.client.get_time_series(symbol, '1min', 5)
                if df is not None and len(df) >= 2:
                    current = df.iloc[-1]
                    prev = df.iloc[-2]

                    # Volumen inusual
                    if len(df) >= 5:
                        avg_volume = df['volume'].head(4).mean()
                        if current['volume'] > avg_volume * 2:
                            vela_inst = f"🏛️ {symbol} VELA INSTITUCIONAL - Volumen {current['volume']/avg_volume:.1f}x"
                            logger.warning(vela_inst)
                            datos_1min['velas_institucionales'].append(vela_inst)

                    # Cambio de momentum
                    cambio_precio = ((current['close'] - prev['close']) / prev['close']) * 100
                    if abs(cambio_precio) > 0.1:  # 0.1% cambio significativo en 1min
                        momentum = f"🚀 {symbol} MOMENTUM: {cambio_precio:+.2f}% en 1min"
                        logger.info(momentum)
                        datos_1min['cambios_momentum'].append(momentum)

            except Exception as e:
                logger.error(f"   ❌ Error en {symbol}: {e}")

        # Guardar datos
        self.historial_1min.append(datos_1min)

        # Resumen del ciclo
        total_alertas = len(datos_1min['alertas'])
        total_señales = len(datos_1min['señales_scalping'])

        logger.info(f"")
        logger.info(f"📋 RESUMEN 1MIN: {total_alertas} alertas, {total_señales} señales scalping")
        logger.info(f"⏰ Próximo análisis en 1 minuto...")
        logger.info(f"")

        return datos_1min

    def monitoreo_5_minutos(self):
        """
        📊 MONITOREO CADA 5 MINUTOS - TENDENCIAS Y ESTRATEGIAS
        ====================================================
        """
        self.ciclo_5min += 1
        timestamp = datetime.now()

        logger.info(f"")
        logger.info(f"📊 MONITOREO 5 MINUTOS - Ciclo #{self.ciclo_5min}")
        logger.info(f"🕐 {timestamp.strftime('%H:%M:%S')}")
        logger.info(f"{'='*60}")

        datos_5min = {
            'timestamp': timestamp,
            'ciclo': self.ciclo_5min,
            'tendencias': [],
            'señales_swing': [],
            'soportes_resistencias': [],
            'confluencias': [],
            'recomendaciones': []
        }

        for symbol in self.symbols:
            logger.info(f"📈 Análisis profundo {symbol}...")

            try:
                # 1. ANÁLISIS COMPLETO
                analysis = self.client.get_complete_analysis(symbol)

                if analysis and analysis['price']:
                    price = analysis['price']
                    indicators = analysis.get('indicators', {})

                    logger.info(f"   💰 Precio: {price:.6f}")

                    # 2. INDICADORES DE TENDENCIA
                    rsi = indicators.get('rsi', 50)
                    macd = indicators.get('macd', 0)
                    ema_12 = indicators.get('ema_12', 0)
                    sma_20 = indicators.get('sma_20', 0)
                    bb_upper = indicators.get('bb_upper', 0)
                    bb_lower = indicators.get('bb_lower', 0)
                    atr = indicators.get('atr', 0)
                    adx = indicators.get('adx', 0)

                    logger.info(f"   📊 RSI: {rsi:.1f} | MACD: {macd:.4f} | ADX: {adx:.1f}")

                    # 3. DETERMINAR TENDENCIA
                    if ema_12 > sma_20 and adx > 25:
                        tendencia = f"📈 {symbol} TENDENCIA ALCISTA FUERTE (ADX: {adx:.1f})"
                        datos_5min['tendencias'].append(tendencia)
                        logger.info(f"   {tendencia}")

                    elif ema_12 < sma_20 and adx > 25:
                        tendencia = f"📉 {symbol} TENDENCIA BAJISTA FUERTE (ADX: {adx:.1f})"
                        datos_5min['tendencias'].append(tendencia)
                        logger.info(f"   {tendencia}")

                    elif adx < 25:
                        tendencia = f"↔️ {symbol} MERCADO LATERAL (ADX: {adx:.1f})"
                        datos_5min['tendencias'].append(tendencia)
                        logger.info(f"   {tendencia}")

                    # 4. SEÑALES DE SWING TRADING
                    if 30 <= rsi <= 40 and macd > 0 and price < bb_lower:
                        swing = f"🎯 {symbol} SEÑAL SWING COMPRA - RSI oversold + MACD+"
                        datos_5min['señales_swing'].append(swing)
                        logger.warning(swing)

                    elif 60 <= rsi <= 70 and macd < 0 and price > bb_upper:
                        swing = f"🎯 {symbol} SEÑAL SWING VENTA - RSI overbought + MACD-"
                        datos_5min['señales_swing'].append(swing)
                        logger.warning(swing)

                    # 5. SOPORTES Y RESISTENCIAS
                    if bb_upper and bb_lower:
                        if price >= bb_upper * 0.995:  # Cerca del BB superior
                            resistencia = f"🔴 {symbol} CERCA RESISTENCIA BB: {bb_upper:.6f}"
                            datos_5min['soportes_resistencias'].append(resistencia)
                            logger.info(f"   {resistencia}")

                        elif price <= bb_lower * 1.005:  # Cerca del BB inferior
                            soporte = f"🟢 {symbol} CERCA SOPORTE BB: {bb_lower:.6f}"
                            datos_5min['soportes_resistencias'].append(soporte)
                            logger.info(f"   {soporte}")

                    # 6. CONFLUENCIAS (múltiples confirmaciones)
                    confluencia_count = 0
                    confluencia_desc = []

                    if rsi < 30:
                        confluencia_count += 1
                        confluencia_desc.append("RSI oversold")
                    if macd > 0:
                        confluencia_count += 1
                        confluencia_desc.append("MACD+")
                    if price < sma_20 and ema_12 > sma_20:
                        confluencia_count += 1
                        confluencia_desc.append("Price pullback")

                    if confluencia_count >= 2:
                        confluencia = f"⭐ {symbol} CONFLUENCIA COMPRA: {', '.join(confluencia_desc)}"
                        datos_5min['confluencias'].append(confluencia)
                        logger.warning(confluencia)

                    # 7. RECOMENDACIONES ESPECÍFICAS
                    if atr > 0:
                        if symbol == 'XAUUSDm':
                            if rsi < 35 and price < sma_20:
                                rec = f"💡 {symbol} RECOMENDACIÓN: Compra en pullback, SL: {price - atr*2:.2f}, TP: {price + atr*3:.2f}"
                                datos_5min['recomendaciones'].append(rec)
                                logger.info(f"   {rec}")

                        elif symbol == 'BTCUSDm':
                            if rsi > 75:
                                rec = f"💡 {symbol} RECOMENDACIÓN: Tomar ganancias, RSI extremo"
                                datos_5min['recomendaciones'].append(rec)
                                logger.info(f"   {rec}")

            except Exception as e:
                logger.error(f"   ❌ Error en análisis de {symbol}: {e}")

        # Guardar datos
        self.historial_5min.append(datos_5min)

        # Resumen del ciclo
        total_tendencias = len(datos_5min['tendencias'])
        total_swing = len(datos_5min['señales_swing'])
        total_confluencias = len(datos_5min['confluencias'])

        logger.info(f"")
        logger.info(f"📋 RESUMEN 5MIN: {total_tendencias} tendencias, {total_swing} swing, {total_confluencias} confluencias")
        logger.info(f"⏰ Próximo análisis en 5 minutos...")
        logger.info(f"")

        return datos_5min

    def guardar_historial(self):
        """Guarda el historial en archivos JSON"""
        try:
            fecha = datetime.now().strftime('%Y%m%d')

            # Guardar historial 1min
            with open(f'historial_1min_{fecha}.json', 'w', encoding='utf-8') as f:
                historial_serializable = []
                for item in self.historial_1min:
                    item_copy = item.copy()
                    item_copy['timestamp'] = item_copy['timestamp'].isoformat()
                    historial_serializable.append(item_copy)
                json.dump(historial_serializable, f, indent=2, ensure_ascii=False)

            # Guardar historial 5min
            with open(f'historial_5min_{fecha}.json', 'w', encoding='utf-8') as f:
                historial_serializable = []
                for item in self.historial_5min:
                    item_copy = item.copy()
                    item_copy['timestamp'] = item_copy['timestamp'].isoformat()
                    historial_serializable.append(item_copy)
                json.dump(historial_serializable, f, indent=2, ensure_ascii=False)

            logger.info("💾 Historial guardado exitosamente")

        except Exception as e:
            logger.error(f"Error guardando historial: {e}")

    def run_1_minuto(self):
        """Hilo para monitoreo de 1 minuto"""
        while self.running:
            try:
                self.monitoreo_1_minuto()

                # Esperar hasta el próximo minuto
                now = datetime.now()
                next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
                sleep_seconds = (next_minute - now).total_seconds()

                time.sleep(sleep_seconds)

            except Exception as e:
                logger.error(f"Error en hilo 1min: {e}")
                time.sleep(60)

    def run_5_minutos(self):
        """Hilo para monitoreo de 5 minutos"""
        while self.running:
            try:
                self.monitoreo_5_minutos()

                # Esperar 5 minutos
                time.sleep(300)

            except Exception as e:
                logger.error(f"Error en hilo 5min: {e}")
                time.sleep(300)

    def run(self):
        """Ejecuta el sistema completo con hilos separados"""
        logger.info(f"")
        logger.info(f"🚀 INICIANDO MONITOREO MULTI-TIMEFRAME")
        logger.info(f"⚡ 1 MINUTO: Scalping, micro señales, velas institucionales")
        logger.info(f"📊 5 MINUTOS: Tendencias, swing trading, confluencias")
        logger.info(f"📈 Símbolos: {', '.join(self.symbols)}")
        logger.info(f"")

        try:
            # Crear hilos separados
            hilo_1min = threading.Thread(target=self.run_1_minuto, daemon=True)
            hilo_5min = threading.Thread(target=self.run_5_minutos, daemon=True)

            # Iniciar hilos
            hilo_1min.start()
            hilo_5min.start()

            # Mantener el programa corriendo
            while self.running:
                time.sleep(10)

                # Guardar historial cada 30 minutos
                if self.ciclo_1min % 30 == 0:
                    self.guardar_historial()

        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo monitoreo multi-timeframe...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}")
            self.running = False
        finally:
            self.guardar_historial()
            logger.info("🏁 Monitoreo multi-timeframe detenido")

def main():
    """Función principal"""
    print("""
╔════════════════════════════════════════════════════════════╗
║            MONITOREO MULTI-TIMEFRAME - V3                ║
║         1 MINUTO: Scalping | 5 MINUTOS: Swing            ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Crear y ejecutar monitor
    monitor = MonitoreoMultiTimeframe()
    monitor.run()

if __name__ == "__main__":
    main()