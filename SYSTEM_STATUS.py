#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ESTADO DEL SISTEMA - ALGO TRADER V3
===================================
Monitor del estado completo del sistema
"""

import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.journal.trading_journal import get_journal
    from src.risk.risk_monitor import RiskMonitor
    from src.broker.mt5_connection import MT5Connection
    from src.notifiers.telegram_notifier import TelegramNotifier
except ImportError as e:
    print(f"Error importando módulos: {e}")

def check_system_status():
    """Verifica el estado completo del sistema"""
    print("=" * 70)
    print("         ALGO TRADER V3 - ESTADO DEL SISTEMA")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    status = {
        'journal': False,
        'risk_monitor': False,
        'mt5': False,
        'telegram': False,
        'dashboard_8501': False,
        'dashboard_8502': False,
        'trading_system': False
    }
    
    # 1. Journal de Trading
    print("1. JOURNAL DE TRADING:")
    try:
        journal = get_journal()
        metrics = journal.calculate_metrics(period_days=30)
        status['journal'] = True
        print(f"   [OK] {len(journal.trades)} trades en historial")
        print(f"   [OK] Win Rate: {metrics['win_rate']*100:.1f}%")
        print(f"   [OK] Net Profit: ${metrics['net_profit']:.2f}")
        print(f"   [OK] Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 2. Monitor de Riesgo
    print("\n2. MONITOR DE RIESGO:")
    try:
        risk_monitor = RiskMonitor()
        report = risk_monitor.generate_risk_report()
        status['risk_monitor'] = True
        print(f"   [OK] Risk Score: {report.get('risk_score', 0):.1f}/100")
        print(f"   [OK] Status: {report.get('status', 'unknown')}")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 3. MT5 Connection
    print("\n3. CONEXION MT5:")
    try:
        mt5 = MT5Connection()
        if mt5.connect():
            status['mt5'] = True
            print(f"   [OK] Conectado a cuenta {mt5.login}")
            if mt5.account_info:
                print(f"   [OK] Balance: ${mt5.account_info.balance:.2f}")
                print(f"   [OK] Equity: ${mt5.account_info.equity:.2f}")
                positions = mt5.get_positions()
                print(f"   [OK] Posiciones abiertas: {len(positions) if positions else 0}")
        else:
            print("   [WARNING] MT5 no conectado")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 4. Telegram
    print("\n4. NOTIFICACIONES TELEGRAM:")
    try:
        telegram = TelegramNotifier()
        if telegram.is_active:
            status['telegram'] = True
            print("   [OK] Telegram activo")
            print(f"   [OK] Bot: @XentrisAIForex_bot")
        else:
            print("   [WARNING] Telegram inactivo")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 5. Dashboards Streamlit
    print("\n5. DASHBOARDS WEB:")
    
    # Dashboard puerto 8501
    try:
        response = requests.get("http://localhost:8501", timeout=2)
        if response.status_code == 200:
            status['dashboard_8501'] = True
            print("   [OK] Dashboard 8501: http://localhost:8501")
        else:
            print("   [WARNING] Dashboard 8501 no responde")
    except:
        print("   [WARNING] Dashboard 8501 no disponible")
    
    # Dashboard puerto 8502
    try:
        response = requests.get("http://localhost:8502", timeout=2)
        if response.status_code == 200:
            status['dashboard_8502'] = True
            print("   [OK] Dashboard 8502: http://localhost:8502")
        else:
            print("   [WARNING] Dashboard 8502 no responde")
    except:
        print("   [WARNING] Dashboard 8502 no disponible")
    
    # 6. Archivos del Sistema
    print("\n6. ARCHIVOS DEL SISTEMA:")
    
    files_to_check = [
        ("Journal Principal", "data/trading_journal.json"),
        ("Configuración", "configs/.env"),
        ("Log de Alertas", "logs/risk_alerts.csv"),
        ("Credenciales Google", "configs/google_credentials.json")
    ]
    
    for name, path in files_to_check:
        if Path(path).exists():
            size = Path(path).stat().st_size
            print(f"   [OK] {name}: {path} ({size} bytes)")
        else:
            print(f"   [INFO] {name}: {path} (no existe)")
    
    # 7. Resumen Final
    print("\n" + "=" * 70)
    print("RESUMEN DEL ESTADO:")
    print("=" * 70)
    
    total_components = len(status)
    active_components = sum(status.values())
    health_percentage = (active_components / total_components) * 100
    
    print(f"Componentes activos: {active_components}/{total_components} ({health_percentage:.1f}%)")
    print()
    
    for component, is_active in status.items():
        symbol = "[OK]" if is_active else "[--]"
        name = component.replace('_', ' ').title()
        print(f"{symbol} {name}")
    
    print()
    
    if health_percentage >= 80:
        print("[STATUS] SISTEMA OPERACIONAL - Todo funcionando correctamente")
    elif health_percentage >= 60:
        print("[STATUS] SISTEMA PARCIAL - Algunos componentes inactivos")
    else:
        print("[STATUS] SISTEMA DEGRADADO - Múltiples fallos detectados")
    
    print()
    print("ACCIONES DISPONIBLES:")
    if not status['dashboard_8501'] and not status['dashboard_8502']:
        print("- Ejecutar: START_RISK_DASHBOARD.bat")
    if not status['mt5']:
        print("- Abrir MetaTrader 5")
    if not status['telegram']:
        print("- Verificar configuración de Telegram")
    
    print("\nPara monitoreo continuo:")
    print("- Dashboard: http://localhost:8502")
    print("- Logs: logs/trading.log")
    print("- Journal: python SIMPLE_RISK_SYSTEM_TEST.py")
    
    return status

if __name__ == "__main__":
    while True:
        try:
            check_system_status()
            print(f"\nPróxima verificación en 60 segundos...")
            print("Presiona Ctrl+C para salir")
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nMonitor detenido por usuario")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)