#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DASHBOARD EN TIEMPO REAL - ALGO TRADER V3
=========================================
Visualización completa del sistema en tiempo real
"""

import time
import sys
import os
import json
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar MT5 si está disponible
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class DashboardTiempoReal:
    def __init__(self):
        self.running = True
        self.mt5_connected = self.initialize_mt5()

    def initialize_mt5(self):
        """Inicializa MT5"""
        if not MT5_AVAILABLE:
            return False
        try:
            if not mt5.initialize():
                return False
            return True
        except Exception:
            return False

    def limpiar_pantalla(self):
        """Limpia la pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def obtener_datos_mt5(self):
        """Obtiene datos de MT5"""
        if not self.mt5_connected:
            return None

        try:
            account_info = mt5.account_info()
            positions = mt5.positions_get()

            # Obtener historial del día
            from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            deals = mt5.history_deals_get(from_date, datetime.now())

            return {
                'account': account_info,
                'positions': positions,
                'deals': deals
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos MT5: {e}")
            return None

    def cargar_reportes_json(self):
        """Carga reportes JSON más recientes"""
        try:
            # Buscar archivos más recientes
            reporte_files = [f for f in os.listdir('.') if f.startswith('reporte_detallado_')]
            if reporte_files:
                latest_reporte = max(reporte_files, key=lambda x: os.path.getctime(x))
                with open(latest_reporte, 'r', encoding='utf-8') as f:
                    reporte_data = json.load(f)
            else:
                reporte_data = None

            # Cargar diario
            diario_file = f"diario_trades_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(diario_file):
                with open(diario_file, 'r', encoding='utf-8') as f:
                    diario_data = json.load(f)
            else:
                diario_data = None

            return reporte_data, diario_data

        except Exception as e:
            logger.error(f"Error cargando reportes: {e}")
            return None, None

    def mostrar_header(self):
        """Muestra header del dashboard"""
        print("=" * 80)
        print(" " * 20 + "ALGO TRADER V3 - DASHBOARD EN TIEMPO REAL")
        print("=" * 80)
        print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"MT5: {'CONECTADO' if self.mt5_connected else 'DESCONECTADO'}")
        print("=" * 80)

    def mostrar_balance_posiciones(self, mt5_data):
        """Muestra balance y posiciones"""
        if not mt5_data or not mt5_data['account']:
            print("❌ No se pudieron obtener datos de cuenta")
            return

        account = mt5_data['account']
        positions = mt5_data['positions'] or []

        print("💰 BALANCE Y EQUITY:")
        print(f"   Balance: ${account.balance:,.2f}")
        print(f"   Equity:  ${account.equity:,.2f}")
        print(f"   Margin:  ${account.margin:,.2f}")
        print(f"   Free Margin: ${account.margin_free:,.2f}")

        profit_loss = account.equity - account.balance
        color = "🟢" if profit_loss >= 0 else "🔴"
        print(f"   P&L: {color} ${profit_loss:+,.2f}")
        print()

        print(f"📊 POSICIONES ABIERTAS ({len(positions)}):")
        if positions:
            total_profit = 0
            for pos in positions:
                symbol = pos.symbol
                type_str = "BUY" if pos.type == 0 else "SELL"
                profit_color = "🟢" if pos.profit >= 0 else "🔴"

                print(f"   {profit_color} {symbol} | {type_str} | Vol: {pos.volume} | "
                      f"Price: {pos.price_open:.5f} | P&L: ${pos.profit:+.2f}")
                total_profit += pos.profit

            print(f"   Total P&L Posiciones: ${total_profit:+.2f}")
        else:
            print("   ✅ Sin posiciones abiertas")
        print()

    def mostrar_estadisticas_dia(self, reporte_data):
        """Muestra estadísticas del día"""
        if not reporte_data:
            print("❌ No hay datos de estadísticas")
            return

        stats = reporte_data.get('estadisticas_generales', {})

        print("📈 ESTADÍSTICAS DEL DÍA:")
        print(f"   Trades ejecutados: {stats.get('trades_totales', 0)}")
        print(f"   Trades ganadores: {stats.get('trades_ganadores', 0)}")
        print(f"   Trades perdedores: {stats.get('trades_perdedores', 0)}")
        print(f"   Win Rate: {stats.get('win_rate', 0):.1f}%")
        print(f"   Mejor trade: ${stats.get('mejor_trade', 0):+.2f}")
        print(f"   Peor trade: ${stats.get('peor_trade', 0):+.2f}")
        print(f"   Profit total: ${stats.get('profit_total', 0):+.2f}")
        print()

    def mostrar_analisis_simbolos(self, reporte_data):
        """Muestra análisis por símbolos"""
        if not reporte_data:
            return

        simbolos = reporte_data.get('analisis_simbolos', {})
        if not simbolos:
            return

        print("🎯 ANÁLISIS POR SÍMBOLOS:")
        for symbol, data in simbolos.items():
            win_rate = data.get('win_rate', 0)
            color = "🟢" if win_rate >= 50 else "🟡" if win_rate >= 30 else "🔴"

            print(f"   {color} {symbol}: {data.get('total_trades', 0)} trades | "
                  f"Win: {win_rate:.1f}% | P&L: ${data.get('profit_total', 0):+.2f}")
        print()

    def mostrar_recomendaciones(self, reporte_data):
        """Muestra recomendaciones del sistema"""
        if not reporte_data:
            return

        recomendaciones = reporte_data.get('recomendaciones', [])
        if not recomendaciones:
            return

        print("💡 RECOMENDACIONES DEL SISTEMA:")
        for i, rec in enumerate(recomendaciones[:5], 1):
            print(f"   {i}. {rec}")
        print()

    def mostrar_sistemas_activos(self):
        """Muestra estado de sistemas activos"""
        print("🚀 SISTEMAS ACTIVOS:")

        # Verificar archivos de log para ver sistemas activos
        log_files = [
            ('sistema_completo_integrado.log', 'Sistema Integrado'),
            ('diario_trades_monitoreo.log', 'Diario de Trades'),
            ('detector_oportunidades_mejorado.log', 'Detector Mejorado')
        ]

        for log_file, name in log_files:
            if os.path.exists(log_file):
                # Verificar si el archivo se modificó en los últimos 2 minutos
                mod_time = os.path.getmtime(log_file)
                if time.time() - mod_time < 120:  # 2 minutos
                    print(f"   ✅ {name}: ACTIVO")
                else:
                    print(f"   🟡 {name}: INACTIVO")
            else:
                print(f"   ❌ {name}: NO ENCONTRADO")
        print()

    def mostrar_rendimiento_tiempo_real(self, mt5_data):
        """Muestra rendimiento en tiempo real"""
        if not mt5_data or not mt5_data['deals']:
            return

        deals = mt5_data['deals']
        if not deals:
            return

        # Filtrar deals del día actual
        today_deals = []
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for deal in deals:
            deal_time = datetime.fromtimestamp(deal.time)
            if deal_time >= today_start and deal.entry == 1:  # Solo trades de entrada
                today_deals.append(deal)

        if not today_deals:
            return

        print("⚡ RENDIMIENTO TIEMPO REAL:")
        total_profit = sum(deal.profit for deal in today_deals)

        # Últimos 5 trades
        recent_deals = sorted(today_deals, key=lambda x: x.time)[-5:]

        print(f"   Profit acumulado hoy: ${total_profit:+.2f}")
        print("   Últimos 5 trades:")

        for deal in recent_deals:
            symbol = deal.symbol
            type_str = "BUY" if deal.type == 0 else "SELL"
            profit_color = "🟢" if deal.profit >= 0 else "🔴"
            time_str = datetime.fromtimestamp(deal.time).strftime('%H:%M')

            print(f"     {profit_color} {time_str} | {symbol} {type_str} | ${deal.profit:+.2f}")
        print()

    def mostrar_footer(self):
        """Muestra footer con información de actualización"""
        print("=" * 80)
        print("🔄 Actualización automática cada 10 segundos | Presiona Ctrl+C para salir")
        print("=" * 80)

    def run_dashboard(self):
        """Ejecuta el dashboard en tiempo real"""
        print("Iniciando Dashboard en Tiempo Real...")
        print("Presiona Ctrl+C para detener")
        time.sleep(2)

        try:
            while self.running:
                # Limpiar pantalla
                self.limpiar_pantalla()

                # Obtener datos
                mt5_data = self.obtener_datos_mt5()
                reporte_data, diario_data = self.cargar_reportes_json()

                # Mostrar dashboard
                self.mostrar_header()
                self.mostrar_balance_posiciones(mt5_data)
                self.mostrar_estadisticas_dia(reporte_data)
                self.mostrar_analisis_simbolos(reporte_data)
                self.mostrar_rendimiento_tiempo_real(mt5_data)
                self.mostrar_sistemas_activos()
                self.mostrar_recomendaciones(reporte_data)
                self.mostrar_footer()

                # Esperar 10 segundos
                time.sleep(10)

        except KeyboardInterrupt:
            print("\nDashboard detenido por el usuario")
        except Exception as e:
            print(f"Error en dashboard: {e}")
        finally:
            if self.mt5_connected:
                mt5.shutdown()

def main():
    print("=" * 60)
    print("         DASHBOARD TIEMPO REAL - ALGO TRADER V3")
    print("=" * 60)

    dashboard = DashboardTiempoReal()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()