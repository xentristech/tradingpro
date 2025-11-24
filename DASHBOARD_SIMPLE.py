#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DASHBOARD SIMPLE - MONITOREO EN TIEMPO REAL
===========================================
"""

import time
import os
import json
from datetime import datetime

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_mt5_data():
    if not MT5_AVAILABLE:
        return None

    try:
        if not mt5.initialize():
            return None

        account = mt5.account_info()
        positions = mt5.positions_get()

        return {
            'account': account,
            'positions': positions or []
        }
    except Exception:
        return None

def load_latest_report():
    try:
        files = [f for f in os.listdir('.') if f.startswith('reporte_detallado_')]
        if not files:
            return None

        latest = max(files, key=lambda x: os.path.getctime(x))
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def show_dashboard():
    clear_screen()

    print("=" * 70)
    print("           ALGO TRADER V3 - DASHBOARD TIEMPO REAL")
    print("=" * 70)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Datos MT5
    mt5_data = get_mt5_data()
    if mt5_data and mt5_data['account']:
        account = mt5_data['account']
        positions = mt5_data['positions']

        print("BALANCE Y POSICIONES:")
        print(f"  Balance: ${account.balance:,.2f}")
        print(f"  Equity:  ${account.equity:,.2f}")
        print(f"  P&L:     ${account.equity - account.balance:+,.2f}")
        print(f"  Posiciones abiertas: {len(positions)}")

        if positions:
            total_profit = sum(pos.profit for pos in positions)
            print(f"  P&L Posiciones: ${total_profit:+,.2f}")

            print("\n  POSICIONES DETALLADAS:")
            for pos in positions[:5]:  # Solo primeras 5
                type_str = "BUY" if pos.type == 0 else "SELL"
                print(f"    {pos.symbol} {type_str} | Vol: {pos.volume} | P&L: ${pos.profit:+.2f}")

        print()
    else:
        print("MT5: NO CONECTADO")
        print()

    # Estadísticas del día
    report = load_latest_report()
    if report:
        stats = report.get('estadisticas_generales', {})

        print("ESTADISTICAS DEL DIA:")
        print(f"  Trades ejecutados: {stats.get('trades_totales', 0)}")
        print(f"  Trades ganadores: {stats.get('trades_ganadores', 0)}")
        print(f"  Trades perdedores: {stats.get('trades_perdedores', 0)}")
        print(f"  Win Rate: {stats.get('win_rate', 0):.1f}%")
        print(f"  Profit total: ${stats.get('profit_total', 0):+.2f}")
        print()

        # Análisis por símbolos
        simbolos = report.get('analisis_simbolos', {})
        if simbolos:
            print("ANALISIS POR SIMBOLOS:")
            for symbol, data in simbolos.items():
                print(f"  {symbol}: {data.get('total_trades', 0)} trades | "
                      f"Win: {data.get('win_rate', 0):.1f}% | P&L: ${data.get('profit_total', 0):+.2f}")
            print()

    # Estado de sistemas
    print("SISTEMAS ACTIVOS:")
    log_files = [
        ('sistema_completo_integrado.log', 'Sistema Integrado'),
        ('diario_trades_monitoreo.log', 'Diario de Trades'),
        ('detector_oportunidades_mejorado.log', 'Detector Mejorado')
    ]

    for log_file, name in log_files:
        if os.path.exists(log_file):
            mod_time = os.path.getmtime(log_file)
            if time.time() - mod_time < 120:  # Último 2 minutos
                status = "ACTIVO"
            else:
                status = "INACTIVO"
        else:
            status = "NO ENCONTRADO"
        print(f"  {name}: {status}")

    print()
    print("=" * 70)
    print("Actualizacion cada 15 segundos | Presiona Ctrl+C para salir")
    print("=" * 70)

def main():
    print("INICIANDO DASHBOARD SIMPLE...")
    print("Presiona Ctrl+C para detener")
    time.sleep(2)

    try:
        while True:
            show_dashboard()
            time.sleep(15)

    except KeyboardInterrupt:
        print("\nDashboard detenido")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if MT5_AVAILABLE:
            mt5.shutdown()

if __name__ == "__main__":
    main()