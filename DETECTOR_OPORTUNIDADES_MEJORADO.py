#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DETECTOR DE OPORTUNIDADES MEJORADO - SENSIBILIDAD MAXIMA
========================================================
Detecta TODAS las oportunidades que el sistema anterior perdía
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

# Configurar logging sin emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DETECTOR_MEJORADO - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('detector_oportunidades_mejorado.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DetectorOportunidadesMejorado:
    def __init__(self):
        self.client = TwelveDataClient()
        self.running = True
        self.symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']
        self.oportunidades_detectadas = []

        # CRITERIOS MEJORADOS - MAS SENSIBLES
        self.config = {
            # RSI - Rangos más amplios
            'rsi_oversold_extremo': 25,      # Era 25
            'rsi_oversold_fuerte': 35,       # NUEVO - detecta antes
            'rsi_oversold_medio': 40,        # NUEVO - zona de interés
            'rsi_overbought_medio': 60,      # NUEVO - zona de interés
            'rsi_overbought_fuerte': 65,     # NUEVO - detecta antes
            'rsi_overbought_extremo': 75,    # Era 75

            # Bollinger Bands - Más sensible
            'bb_distancia_extrema': 0.05,   # 0.05% de distancia
            'bb_distancia_cerca': 0.15,     # 0.15% de distancia

            # MACD - Más sensible a cruces
            'macd_momentum_minimo': 0.001,  # Momentum mínimo

            # Velas - Detectar micro-movimientos
            'vela_tamaño_minimo': 0.01,     # 0.01% = micro-velas
            'vela_cambio_minimo': 0.005,    # 0.005% = micro-cambios

            # Volumen - Más sensible
            'volumen_multiplicador': 1.5,   # 1.5x volumen promedio
        }

    def analizar_oportunidades_avanzadas(self, symbol):
        """Análisis super sensible de oportunidades"""
        try:
            logger.info(f"ANALIZANDO {symbol} con criterios mejorados...")

            # Obtener análisis completo
            analysis = self.client.get_complete_analysis(symbol)

            if not analysis or not analysis['price']:
                logger.warning(f"No se pudo obtener análisis de {symbol}")
                return []

            price = analysis['price']
            indicators = analysis.get('indicators', {})

            # Extraer indicadores
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)
            bb_middle = indicators.get('bb_middle', 0)
            atr = indicators.get('atr', 0)
            ema_12 = indicators.get('ema_12', 0)
            sma_20 = indicators.get('sma_20', 0)

            oportunidades = []

            # ====== ANALISIS RSI MEJORADO ======
            if rsi <= self.config['rsi_oversold_extremo']:
                oportunidades.append({
                    'tipo': 'RSI_OVERSOLD_EXTREMO',
                    'señal': 'COMPRA_FUERTE',
                    'valor': rsi,
                    'descripcion': f'RSI {rsi:.1f} <= {self.config["rsi_oversold_extremo"]} - OVERSOLD EXTREMO',
                    'fuerza': 9
                })
            elif rsi <= self.config['rsi_oversold_fuerte']:
                oportunidades.append({
                    'tipo': 'RSI_OVERSOLD_FUERTE',
                    'señal': 'COMPRA',
                    'valor': rsi,
                    'descripcion': f'RSI {rsi:.1f} <= {self.config["rsi_oversold_fuerte"]} - ZONA OVERSOLD',
                    'fuerza': 7
                })
            elif rsi <= self.config['rsi_oversold_medio']:
                oportunidades.append({
                    'tipo': 'RSI_OVERSOLD_MEDIO',
                    'señal': 'COMPRA_SUAVE',
                    'valor': rsi,
                    'descripcion': f'RSI {rsi:.1f} <= {self.config["rsi_oversold_medio"]} - APPROACHING OVERSOLD',
                    'fuerza': 5
                })

            if rsi >= self.config['rsi_overbought_extremo']:
                oportunidades.append({
                    'tipo': 'RSI_OVERBOUGHT_EXTREMO',
                    'señal': 'VENTA_FUERTE',
                    'valor': rsi,
                    'descripcion': f'RSI {rsi:.1f} >= {self.config["rsi_overbought_extremo"]} - OVERBOUGHT EXTREMO',
                    'fuerza': 9
                })
            elif rsi >= self.config['rsi_overbought_fuerte']:
                oportunidades.append({
                    'tipo': 'RSI_OVERBOUGHT_FUERTE',
                    'señal': 'VENTA',
                    'valor': rsi,
                    'descripcion': f'RSI {rsi:.1f} >= {self.config["rsi_overbought_fuerte"]} - ZONA OVERBOUGHT',
                    'fuerza': 7
                })
            elif rsi >= self.config['rsi_overbought_medio']:
                oportunidades.append({
                    'tipo': 'RSI_OVERBOUGHT_MEDIO',
                    'señal': 'VENTA_SUAVE',
                    'valor': rsi,
                    'descripcion': f'RSI {rsi:.1f} >= {self.config["rsi_overbought_medio"]} - APPROACHING OVERBOUGHT',
                    'fuerza': 5
                })

            # ====== ANALISIS BOLLINGER BANDS MEJORADO ======
            if bb_upper and bb_lower and price:
                distancia_upper = ((bb_upper - price) / price) * 100
                distancia_lower = ((price - bb_lower) / price) * 100

                if distancia_upper <= self.config['bb_distancia_extrema']:
                    oportunidades.append({
                        'tipo': 'BB_UPPER_EXTREMO',
                        'señal': 'VENTA_FUERTE',
                        'valor': distancia_upper,
                        'descripcion': f'Precio {distancia_upper:.3f}% del BB Upper - REBOTE VENTA',
                        'fuerza': 8
                    })
                elif distancia_upper <= self.config['bb_distancia_cerca']:
                    oportunidades.append({
                        'tipo': 'BB_UPPER_CERCA',
                        'señal': 'VENTA',
                        'valor': distancia_upper,
                        'descripcion': f'Precio {distancia_upper:.3f}% del BB Upper - VIGILAR VENTA',
                        'fuerza': 6
                    })

                if distancia_lower <= self.config['bb_distancia_extrema']:
                    oportunidades.append({
                        'tipo': 'BB_LOWER_EXTREMO',
                        'señal': 'COMPRA_FUERTE',
                        'valor': distancia_lower,
                        'descripcion': f'Precio {distancia_lower:.3f}% del BB Lower - REBOTE COMPRA',
                        'fuerza': 8
                    })
                elif distancia_lower <= self.config['bb_distancia_cerca']:
                    oportunidades.append({
                        'tipo': 'BB_LOWER_CERCA',
                        'señal': 'COMPRA',
                        'valor': distancia_lower,
                        'descripcion': f'Precio {distancia_lower:.3f}% del BB Lower - VIGILAR COMPRA',
                        'fuerza': 6
                    })

            # ====== ANALISIS MACD MEJORADO ======
            macd_diff = macd - macd_signal

            if macd > macd_signal and abs(macd_diff) > self.config['macd_momentum_minimo']:
                if macd > 0:
                    oportunidades.append({
                        'tipo': 'MACD_CRUCE_ALCISTA_POSITIVO',
                        'señal': 'COMPRA',
                        'valor': macd_diff,
                        'descripcion': f'MACD cruce alcista en territorio positivo',
                        'fuerza': 7
                    })
                else:
                    oportunidades.append({
                        'tipo': 'MACD_CRUCE_ALCISTA',
                        'señal': 'COMPRA_SUAVE',
                        'valor': macd_diff,
                        'descripcion': f'MACD cruce alcista',
                        'fuerza': 5
                    })

            elif macd < macd_signal and abs(macd_diff) > self.config['macd_momentum_minimo']:
                if macd < 0:
                    oportunidades.append({
                        'tipo': 'MACD_CRUCE_BAJISTA_NEGATIVO',
                        'señal': 'VENTA',
                        'valor': macd_diff,
                        'descripcion': f'MACD cruce bajista en territorio negativo',
                        'fuerza': 7
                    })
                else:
                    oportunidades.append({
                        'tipo': 'MACD_CRUCE_BAJISTA',
                        'señal': 'VENTA_SUAVE',
                        'valor': macd_diff,
                        'descripcion': f'MACD cruce bajista',
                        'fuerza': 5
                    })

            # ====== ANALISIS DE CONFLUENCIAS ======
            # Buscar múltiples confirmaciones
            señales_compra = [op for op in oportunidades if 'COMPRA' in op['señal']]
            señales_venta = [op for op in oportunidades if 'VENTA' in op['señal']]

            if len(señales_compra) >= 2:
                fuerza_total = sum([op['fuerza'] for op in señales_compra])
                oportunidades.append({
                    'tipo': 'CONFLUENCIA_COMPRA',
                    'señal': 'COMPRA_FUERTE',
                    'valor': len(señales_compra),
                    'descripcion': f'CONFLUENCIA: {len(señales_compra)} señales de compra',
                    'fuerza': min(10, fuerza_total)
                })

            if len(señales_venta) >= 2:
                fuerza_total = sum([op['fuerza'] for op in señales_venta])
                oportunidades.append({
                    'tipo': 'CONFLUENCIA_VENTA',
                    'señal': 'VENTA_FUERTE',
                    'valor': len(señales_venta),
                    'descripcion': f'CONFLUENCIA: {len(señales_venta)} señales de venta',
                    'fuerza': min(10, fuerza_total)
                })

            # Agregar información del símbolo y timestamp
            for op in oportunidades:
                op['symbol'] = symbol
                op['price'] = price
                op['timestamp'] = datetime.now()
                op['rsi'] = rsi
                op['macd'] = macd

            return oportunidades

        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return []

    def ejecutar_analisis_completo(self):
        """Ejecuta análisis completo de todos los símbolos"""
        timestamp = datetime.now()
        logger.info(f"")
        logger.info(f"ANALISIS COMPLETO MEJORADO - {timestamp.strftime('%H:%M:%S')}")
        logger.info(f"=" * 60)

        todas_oportunidades = []

        for symbol in self.symbols:
            oportunidades = self.analizar_oportunidades_avanzadas(symbol)
            todas_oportunidades.extend(oportunidades)

            if oportunidades:
                logger.info(f"")
                logger.info(f"OPORTUNIDADES DETECTADAS en {symbol}:")
                for op in oportunidades:
                    fuerza_str = "🔥" * min(3, op['fuerza'] // 3)
                    logger.info(f"  {op['señal']} | Fuerza: {op['fuerza']}/10 | {op['descripcion']}")
            else:
                logger.info(f"  {symbol}: Sin oportunidades detectadas")

        # Resumen general
        if todas_oportunidades:
            # Ordenar por fuerza
            todas_oportunidades.sort(key=lambda x: x['fuerza'], reverse=True)

            logger.info(f"")
            logger.info(f"RESUMEN GENERAL:")
            logger.info(f"Total oportunidades: {len(todas_oportunidades)}")

            # Top 3 oportunidades
            logger.info(f"TOP 3 OPORTUNIDADES:")
            for i, op in enumerate(todas_oportunidades[:3], 1):
                logger.info(f"  {i}. {op['symbol']} - {op['señal']} (Fuerza: {op['fuerza']}/10)")
                logger.info(f"     {op['descripcion']}")
        else:
            logger.info(f"")
            logger.info(f"Sin oportunidades detectadas en este momento")

        # Guardar oportunidades
        self.oportunidades_detectadas.extend(todas_oportunidades)

        return todas_oportunidades

    def run_continuo(self):
        """Ejecuta detección continua cada 30 segundos"""
        logger.info(f"INICIANDO DETECTOR MEJORADO DE OPORTUNIDADES")
        logger.info(f"Sensibilidad MAXIMA activada")
        logger.info(f"Frecuencia: cada 30 segundos")
        logger.info(f"Simbolos: {', '.join(self.symbols)}")
        logger.info(f"")

        ciclo = 0

        try:
            while self.running:
                ciclo += 1
                logger.info(f"CICLO #{ciclo}")

                # Ejecutar análisis
                oportunidades = self.ejecutar_analisis_completo()

                # Pausa 30 segundos
                logger.info(f"")
                logger.info(f"Proximo analisis en 30 segundos...")
                logger.info(f"")

                time.sleep(30)

        except KeyboardInterrupt:
            logger.info("Deteniendo detector mejorado...")
            self.running = False
        except Exception as e:
            logger.error(f"Error critico: {e}")
        finally:
            logger.info(f"Detector detenido. Total oportunidades detectadas: {len(self.oportunidades_detectadas)}")

def main():
    print("DETECTOR DE OPORTUNIDADES MEJORADO")
    print("Sensibilidad MAXIMA para detectar TODAS las oportunidades")
    print("=" * 50)

    detector = DetectorOportunidadesMejorado()

    # Ejecutar una vez para testing
    print("Ejecutando analisis de prueba...")
    oportunidades = detector.ejecutar_analisis_completo()

    print(f"\\nAnalisis completado. Se detectaron {len(oportunidades)} oportunidades.")
    print("\\nPara ejecucion continua: detector.run_continuo()")

if __name__ == "__main__":
    main()