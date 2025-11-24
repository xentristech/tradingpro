#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DIARIO DE TRADES Y MONITOREO DE RENDIMIENTO
==========================================
Sistema de aprendizaje y mejora continua
"""

import time
import sys
import os
import json
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from src.notifiers.telegram_notifier import TelegramNotifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DIARIO_TRADES - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('diario_trades_monitoreo.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Importar MT5 si está disponible
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class DiarioTradesMonitoreo:
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.running = True

        # Archivos de datos
        self.diario_file = f"diario_trades_{datetime.now().strftime('%Y%m%d')}.json"
        self.estadisticas_file = "estadisticas_historicas.json"
        self.aprendizaje_file = "patrones_aprendizaje.json"

        # Datos en memoria
        self.trades_actuales = []
        self.estadisticas_dia = {
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'trades_totales': 0,
            'trades_ganadores': 0,
            'trades_perdedores': 0,
            'trades_abiertos': 0,
            'profit_total': 0.0,
            'mejor_trade': 0.0,
            'peor_trade': 0.0,
            'balance_inicial': 0.0,
            'balance_actual': 0.0,
            'drawdown_maximo': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'señales_detectadas': 0,
            'señales_ejecutadas': 0,
            'eficiencia_ejecucion': 0.0
        }

        # Patrones de aprendizaje
        self.patrones_exitosos = []
        self.patrones_fallidos = []

        # Inicializar MT5
        self.mt5_connected = self.initialize_mt5()

        # Cargar datos existentes
        self.cargar_datos_existentes()

    def initialize_mt5(self):
        """Inicializa conexión con MetaTrader5"""
        if not MT5_AVAILABLE:
            logger.warning("MT5 no disponible - modo simulación")
            return False

        try:
            if not mt5.initialize():
                return False
            return True
        except Exception as e:
            logger.error(f"Error conectando con MT5: {e}")
            return False

    def cargar_datos_existentes(self):
        """Carga datos existentes de archivos"""
        try:
            # Cargar diario del día
            if os.path.exists(self.diario_file):
                with open(self.diario_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.trades_actuales = data.get('trades', [])
                    self.estadisticas_dia = data.get('estadisticas', self.estadisticas_dia)

            # Cargar patrones de aprendizaje
            if os.path.exists(self.aprendizaje_file):
                with open(self.aprendizaje_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patrones_exitosos = data.get('exitosos', [])
                    self.patrones_fallidos = data.get('fallidos', [])

            logger.info(f"Datos cargados: {len(self.trades_actuales)} trades, {len(self.patrones_exitosos)} patrones exitosos")

        except Exception as e:
            logger.error(f"Error cargando datos: {e}")

    def obtener_posiciones_mt5(self):
        """Obtiene posiciones actuales de MT5"""
        if not self.mt5_connected:
            return []

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            positions_data = []
            for pos in positions:
                positions_data.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'time_open': datetime.fromtimestamp(pos.time).isoformat(),
                    'comment': pos.comment
                })

            return positions_data

        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {e}")
            return []

    def obtener_historial_trades(self):
        """Obtiene historial de trades del día"""
        if not self.mt5_connected:
            return []

        try:
            # Obtener trades del día actual
            from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            to_date = datetime.now()

            deals = mt5.history_deals_get(from_date, to_date)
            if deals is None:
                return []

            trades_data = []
            for deal in deals:
                if deal.entry == 1:  # Solo trades de entrada
                    trades_data.append({
                        'ticket': deal.ticket,
                        'order': deal.order,
                        'symbol': deal.symbol,
                        'type': 'BUY' if deal.type == 0 else 'SELL',
                        'volume': deal.volume,
                        'price': deal.price,
                        'profit': deal.profit,
                        'time': datetime.fromtimestamp(deal.time).isoformat(),
                        'comment': deal.comment
                    })

            return trades_data

        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []

    def analizar_rendimiento_tiempo_real(self):
        """Analiza el rendimiento en tiempo real"""
        try:
            # Obtener datos actuales
            posiciones = self.obtener_posiciones_mt5()
            historial = self.obtener_historial_trades()

            if self.mt5_connected:
                account_info = mt5.account_info()
                if account_info:
                    self.estadisticas_dia['balance_actual'] = account_info.balance
                    self.estadisticas_dia['equity_actual'] = account_info.equity
                    if self.estadisticas_dia['balance_inicial'] == 0:
                        self.estadisticas_dia['balance_inicial'] = account_info.balance

            # Actualizar estadísticas
            self.estadisticas_dia['trades_abiertos'] = len(posiciones)
            self.estadisticas_dia['trades_totales'] = len(historial)

            # Calcular profits
            profits = [trade['profit'] for trade in historial if 'profit' in trade]
            if profits:
                self.estadisticas_dia['profit_total'] = sum(profits)
                self.estadisticas_dia['mejor_trade'] = max(profits)
                self.estadisticas_dia['peor_trade'] = min(profits)

                ganadores = [p for p in profits if p > 0]
                self.estadisticas_dia['trades_ganadores'] = len(ganadores)
                self.estadisticas_dia['trades_perdedores'] = len(profits) - len(ganadores)

                if len(profits) > 0:
                    self.estadisticas_dia['win_rate'] = (len(ganadores) / len(profits)) * 100

            # Calcular drawdown
            if self.estadisticas_dia['balance_actual'] > 0 and self.estadisticas_dia['balance_inicial'] > 0:
                current_drawdown = ((self.estadisticas_dia['balance_inicial'] - self.estadisticas_dia['balance_actual']) / self.estadisticas_dia['balance_inicial']) * 100
                if current_drawdown > self.estadisticas_dia['drawdown_maximo']:
                    self.estadisticas_dia['drawdown_maximo'] = current_drawdown

            return {
                'posiciones': posiciones,
                'historial': historial,
                'estadisticas': self.estadisticas_dia
            }

        except Exception as e:
            logger.error(f"Error analizando rendimiento: {e}")
            return None

    def detectar_patrones_exitosos(self, trades_data):
        """Detecta patrones exitosos para aprendizaje"""
        try:
            patrones_nuevos = []

            for trade in trades_data.get('historial', []):
                if trade.get('profit', 0) > 0:  # Trade exitoso
                    patron = {
                        'symbol': trade['symbol'],
                        'type': trade['type'],
                        'profit': trade['profit'],
                        'profit_pct': (trade['profit'] / self.estadisticas_dia['balance_inicial']) * 100 if self.estadisticas_dia['balance_inicial'] > 0 else 0,
                        'hora': trade['time'],
                        'timestamp': datetime.now().isoformat()
                    }

                    # Clasificar por rentabilidad
                    if patron['profit_pct'] > 1.0:  # Más del 1% de ganancia
                        patron['clasificacion'] = 'EXCELENTE'
                    elif patron['profit_pct'] > 0.5:  # Más del 0.5% de ganancia
                        patron['clasificacion'] = 'BUENO'
                    else:
                        patron['clasificacion'] = 'REGULAR'

                    patrones_nuevos.append(patron)

            self.patrones_exitosos.extend(patrones_nuevos)

            # Mantener solo los últimos 100 patrones
            if len(self.patrones_exitosos) > 100:
                self.patrones_exitosos = self.patrones_exitosos[-100:]

            return patrones_nuevos

        except Exception as e:
            logger.error(f"Error detectando patrones: {e}")
            return []

    def generar_reporte_detallado(self):
        """Genera reporte detallado del día"""
        try:
            datos = self.analizar_rendimiento_tiempo_real()
            if not datos:
                return None

            # Detectar nuevos patrones
            patrones_nuevos = self.detectar_patrones_exitosos(datos)

            reporte = {
                'timestamp': datetime.now().isoformat(),
                'estadisticas_generales': self.estadisticas_dia,
                'posiciones_abiertas': datos['posiciones'],
                'total_trades_dia': len(datos['historial']),
                'patrones_detectados': len(patrones_nuevos),
                'analisis_simbolos': self.analizar_por_simbolos(datos['historial']),
                'recomendaciones': self.generar_recomendaciones()
            }

            # Guardar reporte
            reporte_file = f"reporte_detallado_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(reporte_file, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)

            return reporte

        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return None

    def analizar_por_simbolos(self, historial):
        """Analiza rendimiento por símbolos"""
        try:
            simbolos = {}

            for trade in historial:
                symbol = trade['symbol']
                if symbol not in simbolos:
                    simbolos[symbol] = {
                        'total_trades': 0,
                        'ganadores': 0,
                        'perdedores': 0,
                        'profit_total': 0.0,
                        'win_rate': 0.0
                    }

                simbolos[symbol]['total_trades'] += 1
                simbolos[symbol]['profit_total'] += trade.get('profit', 0)

                if trade.get('profit', 0) > 0:
                    simbolos[symbol]['ganadores'] += 1
                else:
                    simbolos[symbol]['perdedores'] += 1

                if simbolos[symbol]['total_trades'] > 0:
                    simbolos[symbol]['win_rate'] = (simbolos[symbol]['ganadores'] / simbolos[symbol]['total_trades']) * 100

            return simbolos

        except Exception as e:
            logger.error(f"Error analizando por símbolos: {e}")
            return {}

    def generar_recomendaciones(self):
        """Genera recomendaciones basadas en el análisis"""
        recomendaciones = []

        try:
            # Análisis de win rate
            if self.estadisticas_dia['win_rate'] < 50:
                recomendaciones.append("Win rate bajo (<50%). Considerar ajustar criterios de entrada.")
            elif self.estadisticas_dia['win_rate'] > 70:
                recomendaciones.append("Excelente win rate (>70%). Mantener estrategia actual.")

            # Análisis de drawdown
            if self.estadisticas_dia['drawdown_maximo'] > 5:
                recomendaciones.append("Drawdown alto (>5%). Revisar gestión de riesgo.")

            # Análisis de patrones
            if len(self.patrones_exitosos) >= 5:
                mejores_simbolos = {}
                for patron in self.patrones_exitosos[-10:]:  # Últimos 10 patrones
                    symbol = patron['symbol']
                    mejores_simbolos[symbol] = mejores_simbolos.get(symbol, 0) + 1

                mejor_symbol = max(mejores_simbolos, key=mejores_simbolos.get) if mejores_simbolos else None
                if mejor_symbol:
                    recomendaciones.append(f"Símbolo más exitoso reciente: {mejor_symbol}")

            # Recomendaciones de horario
            hora_actual = datetime.now().hour
            if 22 <= hora_actual or hora_actual <= 6:
                recomendaciones.append("Horario de baja volatilidad. Considerar reducir tamaño de posición.")

            return recomendaciones

        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            return ["Error generando recomendaciones"]

    def enviar_reporte_telegram(self, reporte):
        """Envía reporte resumido por Telegram"""
        try:
            stats = reporte['estadisticas_generales']

            mensaje = f"""
📊 REPORTE DIARIO DE TRADING 📊

📅 Fecha: {stats['fecha']}
⏰ Hora: {datetime.now().strftime('%H:%M:%S')}

💰 RESULTADOS FINANCIEROS:
• Balance: ${stats['balance_actual']:,.2f}
• Profit del día: ${stats['profit_total']:,.2f}
• Mejor trade: ${stats['mejor_trade']:,.2f}
• Peor trade: ${stats['peor_trade']:,.2f}

📈 ESTADÍSTICAS DE TRADING:
• Trades totales: {stats['trades_totales']}
• Trades ganadores: {stats['trades_ganadores']}
• Trades perdedores: {stats['trades_perdedores']}
• Posiciones abiertas: {stats['trades_abiertos']}
• Win Rate: {stats['win_rate']:.1f}%
• Drawdown máximo: {stats['drawdown_maximo']:.2f}%

🎯 EFICIENCIA:
• Señales detectadas: {stats['señales_detectadas']}
• Señales ejecutadas: {stats['señales_ejecutadas']}
• Eficiencia: {stats['eficiencia_ejecucion']:.1f}%

🔍 ANÁLISIS:
• Patrones detectados: {reporte['patrones_detectados']}
• Símbolos analizados: {len(reporte['analisis_simbolos'])}

💡 RECOMENDACIONES:
{chr(10).join(['• ' + rec for rec in reporte['recomendaciones'][:3]])}

🤖 Sistema de Aprendizaje Activo
"""

            return self.telegram.send_message(mensaje.strip(), parse_mode='HTML')

        except Exception as e:
            logger.error(f"Error enviando reporte Telegram: {e}")
            return False

    def guardar_datos(self):
        """Guarda todos los datos en archivos"""
        try:
            # Guardar diario del día
            diario_data = {
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'trades': self.trades_actuales,
                'estadisticas': self.estadisticas_dia,
                'ultima_actualizacion': datetime.now().isoformat()
            }

            with open(self.diario_file, 'w', encoding='utf-8') as f:
                json.dump(diario_data, f, indent=2, ensure_ascii=False)

            # Guardar patrones de aprendizaje
            patrones_data = {
                'exitosos': self.patrones_exitosos,
                'fallidos': self.patrones_fallidos,
                'ultima_actualizacion': datetime.now().isoformat()
            }

            with open(self.aprendizaje_file, 'w', encoding='utf-8') as f:
                json.dump(patrones_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Datos guardados: {self.diario_file}, {self.aprendizaje_file}")

        except Exception as e:
            logger.error(f"Error guardando datos: {e}")

    def run_monitoreo_continuo(self):
        """Ejecuta monitoreo continuo cada 2 minutos"""
        logger.info("INICIANDO DIARIO DE TRADES Y MONITOREO")
        logger.info("Análisis y aprendizaje continuo activado")
        logger.info("Frecuencia: cada 2 minutos")
        logger.info("")

        ciclo = 0

        try:
            while self.running:
                ciclo += 1
                logger.info(f"MONITOREO #{ciclo} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 50)

                # Generar reporte completo
                reporte = self.generar_reporte_detallado()

                if reporte:
                    logger.info(f"Balance actual: ${reporte['estadisticas_generales']['balance_actual']:,.2f}")
                    logger.info(f"Profit del día: ${reporte['estadisticas_generales']['profit_total']:,.2f}")
                    logger.info(f"Win Rate: {reporte['estadisticas_generales']['win_rate']:.1f}%")
                    logger.info(f"Posiciones abiertas: {reporte['estadisticas_generales']['trades_abiertos']}")
                    logger.info(f"Trades totales: {reporte['total_trades_dia']}")

                    if reporte['patrones_detectados'] > 0:
                        logger.info(f"Nuevos patrones detectados: {reporte['patrones_detectados']}")

                    # Enviar reporte cada 30 minutos (15 ciclos)
                    if ciclo % 15 == 0:
                        self.enviar_reporte_telegram(reporte)
                        logger.info("Reporte enviado por Telegram")

                # Guardar datos
                self.guardar_datos()

                logger.info("")
                logger.info("Próximo monitoreo en 2 minutos...")
                logger.info("")

                time.sleep(120)  # 2 minutos

        except KeyboardInterrupt:
            logger.info("Deteniendo monitoreo...")
        except Exception as e:
            logger.error(f"Error en monitoreo: {e}")
        finally:
            self.guardar_datos()
            logger.info("Diario de trades finalizado")

def main():
    print("DIARIO DE TRADES Y SISTEMA DE APRENDIZAJE")
    print("Monitoreo continuo y mejora del sistema")
    print("=" * 50)

    # Crear y ejecutar monitor
    monitor = DiarioTradesMonitoreo()

    # Generar reporte inicial
    print("Generando reporte inicial...")
    reporte = monitor.generar_reporte_detallado()
    if reporte:
        print(f"Balance actual: ${reporte['estadisticas_generales']['balance_actual']:,.2f}")
        print(f"Trades del día: {reporte['total_trades_dia']}")
        print(f"Posiciones abiertas: {len(reporte['posiciones_abiertas'])}")

    print("\nIniciando monitoreo continuo...")
    monitor.run_monitoreo_continuo()

if __name__ == "__main__":
    main()