#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DETECTOR ANTICIPATORIO DE VELAS INSTITUCIONALES
===============================================
Detecta patrones institucionales antes de que terminen las velas,
basado en momentum, tamaño parcial y análisis de ticks.
"""

import time
import sys
import os
from datetime import datetime, timedelta
import logging
import json
import pandas as pd
import numpy as np
import MetaTrader5 as mt5

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ANTICIPATORY_DETECTOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('detector_anticipatorio.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DetectorAnticipatorioInstitucional:
    def __init__(self):
        """Detector que anticipa velas institucionales usando datos de MT5"""
        self.running = True
        self.detecciones = []

        # Símbolos a monitorear
        self.symbols = ['XAUUSD', 'BTCUSD', 'EURUSD', 'GBPUSD']

        # Configuración de detección anticipatoria
        self.config = {
            'momentum_threshold': 0.6,  # 60% del tamaño promedio en 10 segundos
            'tick_ratio_bullish': 0.7,  # 70% de ticks al alza
            'tick_ratio_bearish': 0.7,  # 70% de ticks a la baja
            'min_ticks_sample': 10,     # Mínimo 10 ticks para análisis
            'price_movement_threshold': 0.0005,  # 0.05% movimiento mínimo
            'tiempo_anticipacion': 45   # Segundos antes del cierre para detectar
        }

        # Conectar MT5
        if not mt5.initialize():
            logger.error("Error inicializando MT5")
            raise Exception("No se pudo conectar a MT5")
        else:
            logger.info("MT5 conectado para detector anticipatorio")

    def obtener_datos_tick_recientes(self, symbol, count=50):
        """Obtiene los últimos ticks de un símbolo"""
        try:
            # Obtener ticks recientes
            ticks = mt5.copy_ticks_from(symbol, datetime.now() - timedelta(minutes=2), count, mt5.COPY_TICKS_ALL)

            if ticks is None or len(ticks) == 0:
                return None

            # Convertir a DataFrame
            df_ticks = pd.DataFrame(ticks)
            df_ticks['time'] = pd.to_datetime(df_ticks['time'], unit='s')

            return df_ticks

        except Exception as e:
            logger.error(f"Error obteniendo ticks para {symbol}: {e}")
            return None

    def obtener_velas_recientes(self, symbol, timeframe=mt5.TIMEFRAME_M1, count=20):
        """Obtiene las últimas velas del símbolo"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            return df

        except Exception as e:
            logger.error(f"Error obteniendo velas para {symbol}: {e}")
            return None

    def calcular_tamaño_promedio_velas(self, df_velas, periods=5):
        """Calcula el tamaño promedio de las últimas velas"""
        if len(df_velas) < periods:
            return 0

        # Calcular tamaño de cada vela (high - low)
        df_velas['size'] = df_velas['high'] - df_velas['low']

        # Promedio de las últimas N velas (excluyendo la actual)
        return df_velas['size'].iloc[-(periods+1):-1].mean()

    def analizar_momentum_actual(self, symbol):
        """Analiza el momentum de la vela actual en formación"""
        try:
            # Obtener velas recientes
            df_velas = self.obtener_velas_recientes(symbol)
            if df_velas is None or len(df_velas) < 10:
                return None

            # Vela actual (la que se está formando)
            vela_actual = df_velas.iloc[-1]
            tiempo_vela = vela_actual['time']

            # Calcular cuánto tiempo ha pasado en la vela actual
            ahora = datetime.now()
            tiempo_transcurrido = (ahora - tiempo_vela).total_seconds()

            # Solo analizar si quedan menos de 45 segundos para cerrar la vela
            if tiempo_transcurrido < (60 - self.config['tiempo_anticipacion']):
                return None

            # Obtener precio actual
            tick_info = mt5.symbol_info_tick(symbol)
            if tick_info is None:
                return None

            precio_actual = (tick_info.bid + tick_info.ask) / 2

            # Calcular tamaño actual de la vela
            tamaño_actual = precio_actual - vela_actual['open']
            tamaño_absoluto = abs(tamaño_actual)

            # Calcular tamaño promedio de velas anteriores
            tamaño_promedio = self.calcular_tamaño_promedio_velas(df_velas)

            if tamaño_promedio == 0:
                return None

            # Ratio del tamaño actual vs promedio
            ratio_tamaño = tamaño_absoluto / tamaño_promedio

            # Obtener ticks recientes para análisis de momentum
            df_ticks = self.obtener_datos_tick_recientes(symbol)
            if df_ticks is None or len(df_ticks) < self.config['min_ticks_sample']:
                return None

            # Analizar dirección de los ticks recientes
            ticks_recientes = df_ticks.tail(self.config['min_ticks_sample'])

            # Calcular momentum de ticks
            ticks_alcistas = 0
            ticks_bajistas = 0

            for i in range(1, len(ticks_recientes)):
                if ticks_recientes.iloc[i]['bid'] > ticks_recientes.iloc[i-1]['bid']:
                    ticks_alcistas += 1
                elif ticks_recientes.iloc[i]['bid'] < ticks_recientes.iloc[i-1]['bid']:
                    ticks_bajistas += 1

            total_ticks = ticks_alcistas + ticks_bajistas
            if total_ticks == 0:
                return None

            ratio_alcista = ticks_alcistas / total_ticks
            ratio_bajista = ticks_bajistas / total_ticks

            # Determinar señal anticipatoria
            señal = None
            confianza = 0

            # Criterios para señal ALCISTA anticipatoria
            if (ratio_tamaño >= self.config['momentum_threshold'] and
                ratio_alcista >= self.config['tick_ratio_bullish'] and
                tamaño_actual > 0):

                señal = 'BUY'
                confianza = min(0.95, 0.6 + (ratio_tamaño * 0.2) + (ratio_alcista * 0.15))

            # Criterios para señal BAJISTA anticipatoria
            elif (ratio_tamaño >= self.config['momentum_threshold'] and
                  ratio_bajista >= self.config['tick_ratio_bearish'] and
                  tamaño_actual < 0):

                señal = 'SELL'
                confianza = min(0.95, 0.6 + (ratio_tamaño * 0.2) + (ratio_bajista * 0.15))

            if señal:
                deteccion = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'tipo': señal,
                    'precio_actual': precio_actual,
                    'precio_open_vela': vela_actual['open'],
                    'tamaño_actual': tamaño_absoluto,
                    'tamaño_promedio': tamaño_promedio,
                    'ratio_tamaño': ratio_tamaño,
                    'ratio_alcista': ratio_alcista,
                    'ratio_bajista': ratio_bajista,
                    'confianza': confianza,
                    'tiempo_restante_vela': 60 - tiempo_transcurrido,
                    'razon': f"Momentum {ratio_tamaño:.1f}x promedio, ticks {max(ratio_alcista, ratio_bajista)*100:.0f}% direccionales"
                }

                logger.info(f"SEÑAL ANTICIPATORIA: {symbol} {señal} - Confianza: {confianza:.1%}")
                logger.info(f"   Tamaño: {ratio_tamaño:.1f}x promedio | Ticks: {max(ratio_alcista, ratio_bajista)*100:.0f}% direccionales")

                return deteccion

        except Exception as e:
            logger.error(f"Error analizando momentum para {symbol}: {e}")

        return None

    def escanear_oportunidades(self):
        """Escanea todos los símbolos buscando oportunidades anticipatorias"""
        oportunidades = []

        for symbol in self.symbols:
            try:
                deteccion = self.analizar_momentum_actual(symbol)
                if deteccion:
                    oportunidades.append(deteccion)

            except Exception as e:
                logger.error(f"Error escaneando {symbol}: {e}")

        return oportunidades

    def ejecutar_monitoreo_continuo(self, intervalo=10):
        """Ejecuta monitoreo continuo cada X segundos"""
        logger.info(f"Iniciando detector anticipatorio - Intervalo: {intervalo}s")

        try:
            while self.running:
                start_time = time.time()

                # Escanear oportunidades
                oportunidades = self.escanear_oportunidades()

                if oportunidades:
                    logger.info(f"{len(oportunidades)} oportunidades detectadas")

                    for op in oportunidades:
                        # Guardar detección
                        self.detecciones.append(op)

                        # Log detallado
                        logger.info(f"{op['symbol']}: {op['tipo']} | "
                                  f"Confianza: {op['confianza']:.1%} | "
                                  f"Restante: {op['tiempo_restante_vela']:.0f}s")

                # Esperar intervalo
                elapsed = time.time() - start_time
                sleep_time = max(0, intervalo - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Detector detenido por usuario")
        except Exception as e:
            logger.error(f"Error en monitoreo continuo: {e}")
        finally:
            mt5.shutdown()
            logger.info("Detector anticipatorio finalizado")

if __name__ == "__main__":
    detector = DetectorAnticipatorioInstitucional()
    detector.ejecutar_monitoreo_continuo(intervalo=5)  # Cada 5 segundos