#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DETECTOR DE VELAS INSTITUCIONALES CADA MINUTO
=============================================
Detecta velas institucionales con volumen elevado cada minuto
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
    format='%(asctime)s - DETECTOR_VELAS - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('detector_velas_institucionales.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DetectorVelasInstitucionales:
    def __init__(self):
        self.client = TwelveDataClient()
        self.running = True
        self.detecciones = []

        # Símbolos a monitorear
        self.symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']

        # Configuración de detección
        self.config = {
            'volumen_multiplicador_minimo': 2.0,  # 2x volumen promedio
            'tamaño_vela_minimo': 0.002,  # 0.2% del precio
            'rsi_extremo_compra': 70,
            'rsi_extremo_venta': 30,
            'atr_multiplicador': 1.5
        }

    def analizar_vela_institucional(self, symbol, df):
        """Analiza si una vela es institucional"""
        try:
            if len(df) < 20:
                return None

            # Última vela (actual)
            current = df.iloc[-1]

            # Calcular volumen promedio de las últimas 20 velas
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]

            # Calcular tamaño de la vela
            vela_size = abs(current['close'] - current['open']) / current['open']

            # Calcular ATR para contexto de volatilidad
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = abs(df['high'] - df['close'].shift(1))
            df['low_close'] = abs(df['low'] - df['close'].shift(1))
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            atr = df['true_range'].rolling(14).mean().iloc[-1]

            # Detectar vela institucional
            deteccion = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'precio': current['close'],
                'volumen_actual': current['volume'],
                'volumen_promedio': avg_volume,
                'volumen_ratio': current['volume'] / avg_volume if avg_volume > 0 else 0,
                'tamaño_vela': vela_size,
                'atr': atr,
                'direccion': 'ALCISTA' if current['close'] > current['open'] else 'BAJISTA',
                'es_institucional': False,
                'razon': []
            }

            # Criterios para vela institucional
            razon = []

            # 1. Volumen elevado
            if deteccion['volumen_ratio'] >= self.config['volumen_multiplicador_minimo']:
                razon.append(f"Volumen {deteccion['volumen_ratio']:.1f}x promedio")

            # 2. Tamaño de vela significativo
            if vela_size >= self.config['tamaño_vela_minimo']:
                razon.append(f"Vela grande: {vela_size*100:.2f}%")

            # 3. Comparar con ATR
            vela_atr_ratio = abs(current['high'] - current['low']) / atr if atr > 0 else 0
            if vela_atr_ratio >= self.config['atr_multiplicador']:
                razon.append(f"Rango {vela_atr_ratio:.1f}x ATR")

            # 4. Patrones específicos
            shadow_superior = current['high'] - max(current['open'], current['close'])
            shadow_inferior = min(current['open'], current['close']) - current['low']
            cuerpo = abs(current['close'] - current['open'])

            # Hammer o Shooting Star con volumen
            if shadow_inferior > cuerpo * 2 and deteccion['volumen_ratio'] > 1.5:
                razon.append("Hammer institucional")
            elif shadow_superior > cuerpo * 2 and deteccion['volumen_ratio'] > 1.5:
                razon.append("Shooting Star institucional")

            # 5. Engulfing con volumen
            if len(df) >= 2:
                prev = df.iloc[-2]
                if (current['close'] > current['open'] and
                    current['open'] < prev['close'] and
                    current['close'] > prev['open'] and
                    deteccion['volumen_ratio'] > 1.5):
                    razon.append("Bullish Engulfing institucional")
                elif (current['close'] < current['open'] and
                      current['open'] > prev['close'] and
                      current['close'] < prev['open'] and
                      deteccion['volumen_ratio'] > 1.5):
                    razon.append("Bearish Engulfing institucional")

            deteccion['razon'] = razon
            deteccion['es_institucional'] = len(razon) >= 2  # Al menos 2 criterios

            return deteccion

        except Exception as e:
            logger.error(f"Error analizando vela institucional para {symbol}: {e}")
            return None

    def obtener_datos_1min(self, symbol):
        """Obtiene datos de 1 minuto para análisis"""
        try:
            # Obtener datos de 1 minuto (últimas 30 velas)
            df = self.client.get_time_series(symbol, interval='1min', outputsize=30)

            if df is not None and len(df) > 0:
                return df
            else:
                logger.warning(f"No se pudieron obtener datos para {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error obteniendo datos de {symbol}: {e}")
            return None

    def procesar_symbol(self, symbol):
        """Procesa un símbolo específico"""
        try:
            logger.info(f"🔍 Analizando {symbol}...")

            # Obtener datos
            df = self.obtener_datos_1min(symbol)
            if df is None:
                return None

            # Analizar vela institucional
            deteccion = self.analizar_vela_institucional(symbol, df)

            if deteccion and deteccion['es_institucional']:
                self.detecciones.append(deteccion)

                logger.info(f"🚨 VELA INSTITUCIONAL DETECTADA en {symbol}!")
                logger.info(f"   💰 Precio: {deteccion['precio']:.6f}")
                logger.info(f"   📊 Volumen: {deteccion['volumen_ratio']:.1f}x promedio")
                logger.info(f"   🎯 Dirección: {deteccion['direccion']}")
                logger.info(f"   ✅ Razones: {', '.join(deteccion['razon'])}")

                # Guardar detección importante
                self.guardar_deteccion_importante(deteccion)

                return deteccion
            else:
                logger.info(f"   📈 {symbol}: Actividad normal")
                return None

        except Exception as e:
            logger.error(f"Error procesando {symbol}: {e}")
            return None

    def guardar_deteccion_importante(self, deteccion):
        """Guarda detecciones importantes en archivo"""
        try:
            filename = f"detecciones_institucionales_{datetime.now().strftime('%Y%m%d')}.json"

            # Convertir timestamp a string para JSON
            deteccion_json = deteccion.copy()
            deteccion_json['timestamp'] = deteccion['timestamp'].isoformat()

            # Leer detecciones existentes
            detecciones_existentes = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    detecciones_existentes = json.load(f)

            # Agregar nueva detección
            detecciones_existentes.append(deteccion_json)

            # Guardar todas las detecciones
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(detecciones_existentes, f, indent=2, ensure_ascii=False)

            logger.info(f"📝 Detección guardada en {filename}")

        except Exception as e:
            logger.error(f"Error guardando detección: {e}")

    def mostrar_resumen(self):
        """Muestra resumen de detecciones"""
        if self.detecciones:
            logger.info(f"")
            logger.info(f"📊 RESUMEN DE DETECCIONES:")
            for det in self.detecciones[-5:]:  # Últimas 5
                logger.info(f"   🕐 {det['timestamp'].strftime('%H:%M:%S')} | "
                          f"{det['symbol']} | {det['direccion']} | "
                          f"Vol: {det['volumen_ratio']:.1f}x")
        else:
            logger.info("   📊 No hay detecciones institucionales recientes")

    def ciclo_deteccion(self):
        """Ejecuta un ciclo completo de detección"""
        logger.info(f"")
        logger.info(f"🔄 CICLO DE DETECCIÓN - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'='*50}")

        detecciones_ciclo = []

        for symbol in self.symbols:
            deteccion = self.procesar_symbol(symbol)
            if deteccion:
                detecciones_ciclo.append(deteccion)

        if detecciones_ciclo:
            logger.info(f"🚨 ¡{len(detecciones_ciclo)} VELAS INSTITUCIONALES DETECTADAS!")
        else:
            logger.info(f"✅ Mercado normal - No hay actividad institucional detectada")

        # Mostrar resumen cada 10 ciclos
        if len(self.detecciones) % 10 == 0:
            self.mostrar_resumen()

        return detecciones_ciclo

    def run(self):
        """Ejecuta el detector principal"""
        logger.info(f"")
        logger.info(f"🚀 INICIANDO DETECTOR DE VELAS INSTITUCIONALES")
        logger.info(f"⏰ Análisis cada minuto")
        logger.info(f"📊 Símbolos: {', '.join(self.symbols)}")
        logger.info(f"🎯 Configuración:")
        logger.info(f"   - Volumen mínimo: {self.config['volumen_multiplicador_minimo']}x")
        logger.info(f"   - Tamaño vela mínimo: {self.config['tamaño_vela_minimo']*100}%")
        logger.info(f"   - ATR multiplicador: {self.config['atr_multiplicador']}x")
        logger.info(f"")

        ciclo_count = 0

        try:
            while self.running:
                ciclo_count += 1

                # Ejecutar ciclo de detección
                detecciones = self.ciclo_deteccion()

                # Esperar hasta el próximo minuto
                now = datetime.now()
                next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
                sleep_seconds = (next_minute - now).total_seconds()

                logger.info(f"⏳ Próximo análisis en {sleep_seconds:.0f} segundos...")

                # Esperar con interrupciones cada 10 segundos
                slept = 0
                while slept < sleep_seconds and self.running:
                    sleep_time = min(10, sleep_seconds - slept)
                    time.sleep(sleep_time)
                    slept += sleep_time

        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo detector por interrupción del usuario...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}")
            self.running = False
        finally:
            logger.info(f"🏁 Detector detenido")
            logger.info(f"📊 Total detecciones: {len(self.detecciones)}")
            self.mostrar_resumen()

def main():
    """Función principal"""
    print("""
╔════════════════════════════════════════════════════════════╗
║         DETECTOR VELAS INSTITUCIONALES - 1 MINUTO        ║
║              ANÁLISIS DE VOLUMEN ELEVADO                  ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Crear y ejecutar detector
    detector = DetectorVelasInstitucionales()
    detector.run()

if __name__ == "__main__":
    main()