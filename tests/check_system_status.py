#!/usr/bin/env python
"""
VERIFICADOR DE ESTADO - ALGO TRADER V3
=======================================
Verifica el estado de todos los componentes del sistema
"""

import os
import sys
import socket
import json
from pathlib import Path
from datetime import datetime
import subprocess

def check_port(port):
    """Verifica si un puerto está en uso"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def check_python_packages():
    """Verifica los paquetes Python instalados"""
    packages = {
        'MetaTrader5': '✓',
        'pandas': '✓',
        'numpy': '✓',
        'requests': '✓',
        'beautifulsoup4': '✓',
        'plotly': '✓',
        'streamlit': '✓',
        'ta': '✓',
        'scikit-learn': '✓',
        'xgboost': '○',
        'python-dotenv': '✓'
    }
    
    installed = []
    missing = []
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            installed.append(package)
        except ImportError:
            missing.append(package)
            
    return installed, missing

def check_file_structure():
    """Verifica la estructura de archivos"""
    base_path = Path(__file__).parent
    
    critical_files = {
        'src/core/bot_manager.py': False,
        'src/trading/main_trader.py': False,
        'src/ui/dashboards/revolutionary_dashboard_final.py': False,
        'src/ui/charts/chart_simulation_reviewed.py': False,
        'src/data/TICK_SYSTEM_FINAL.py': False,
        'src/ai/ollama_validator.py': False,
        'src/signals/signal_generator.py': False,
        '.env': False,
        'requirements.txt': False
    }
    
    for file_path in critical_files:
        full_path = base_path / file_path
        critical_files[file_path] = full_path.exists()
        
    return critical_files

def check_services():
    """Verifica los servicios activos"""
    services = {
        'Sistema de Ticks (8508)': check_port(8508),
        'Revolutionary Dashboard (8512)': check_port(8512),
        'Chart Simulation (8516)': check_port(8516),
        'TradingView Pro (8517)': check_port(8517),
        'Modern Dashboard (8508)': check_port(8508),
        'Signal Dashboard (8510)': check_port(8510)
    }
    return services

def check_mt5_connection():
    """Verifica la conexión con MT5"""
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            info = mt5.terminal_info()
            account = mt5.account_info()
            mt5.shutdown()
            
            if info and account:
                return {
                    'connected': True,
                    'terminal': info.name,
                    'account': account.login,
                    'broker': account.company,
                    'balance': account.balance
                }
        return {'connected': False}
    except:
        return {'connected': False}

def generate_report():
    """Genera un reporte completo del estado"""
    print("""
╔════════════════════════════════════════════════════════════╗
║         VERIFICADOR DE ESTADO - ALGO TRADER V3            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Información del sistema
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Directorio: {Path(__file__).parent}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print()
    
    # 1. Verificar paquetes
    print("="*60)
    print("1. DEPENDENCIAS PYTHON")
    print("="*60)
    
    installed, missing = check_python_packages()
    
    print(f"✓ Instalados: {len(installed)}")
    print(f"✗ Faltantes: {len(missing)}")
    
    if missing:
        print(f"\nPaquetes faltantes: {', '.join(missing)}")
        print("Instálalos con: pip install", ' '.join(missing))
    else:
        print("\n✓ Todas las dependencias críticas instaladas")
    
    # 2. Verificar estructura de archivos
    print("\n" + "="*60)
    print("2. ESTRUCTURA DE ARCHIVOS")
    print("="*60)
    
    files = check_file_structure()
    files_ok = sum(files.values())
    files_total = len(files)
    
    print(f"Archivos encontrados: {files_ok}/{files_total}")
    
    for file_path, exists in files.items():
        if not exists:
            print(f"  ✗ Falta: {file_path}")
    
    if files_ok == files_total:
        print("\n✓ Estructura de archivos completa")
    else:
        print(f"\n⚠️ Faltan {files_total - files_ok} archivos críticos")
    
    # 3. Verificar servicios
    print("\n" + "="*60)
    print("3. SERVICIOS WEB")
    print("="*60)
    
    services = check_services()
    services_running = sum(services.values())
    
    for service, running in services.items():
        status = "✓ ACTIVO" if running else "✗ INACTIVO"
        print(f"{status:12} {service}")
    
    print(f"\nServicios activos: {services_running}/{len(services)}")
    
    # 4. Verificar MT5
    print("\n" + "="*60)
    print("4. CONEXIÓN METATRADER 5")
    print("="*60)
    
    mt5_info = check_mt5_connection()
    
    if mt5_info['connected']:
        print("✓ MT5 Conectado")
        print(f"  Terminal: {mt5_info['terminal']}")
        print(f"  Cuenta: {mt5_info['account']}")
        print(f"  Broker: {mt5_info['broker']}")
        print(f"  Balance: ${mt5_info['balance']:.2f}")
    else:
        print("✗ MT5 No conectado")
        print("  Asegúrate de tener MetaTrader 5 instalado y abierto")
    
    # 5. URLs de acceso
    print("\n" + "="*60)
    print("5. URLS DE ACCESO")
    print("="*60)
    
    urls = {
        'Revolutionary Dashboard': 'http://localhost:8512',
        'Chart Simulation': 'http://localhost:8516',
        'TradingView Professional': 'http://localhost:8517',
        'Modern Dashboard': 'http://localhost:8508',
        'Signal Dashboard': 'http://localhost:8510'
    }
    
    for name, url in urls.items():
        print(f"  • {name}: {url}")
    
    # 6. Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    
    status_points = 0
    max_points = 4
    
    if not missing:
        status_points += 1
        print("✓ Dependencias completas")
    else:
        print("✗ Faltan dependencias")
    
    if files_ok == files_total:
        status_points += 1
        print("✓ Archivos completos")
    else:
        print("✗ Faltan archivos")
    
    if services_running > 0:
        status_points += 1
        print(f"✓ {services_running} servicios activos")
    else:
        print("✗ No hay servicios activos")
    
    if mt5_info['connected']:
        status_points += 1
        print("✓ MT5 conectado")
    else:
        print("✗ MT5 no conectado")
    
    # Estado general
    print("\n" + "="*60)
    percentage = (status_points / max_points) * 100
    
    if percentage == 100:
        print("🎉 SISTEMA 100% OPERATIVO")
    elif percentage >= 75:
        print(f"✓ Sistema {percentage:.0f}% operativo")
    elif percentage >= 50:
        print(f"⚠️ Sistema {percentage:.0f}% operativo - Requiere atención")
    else:
        print(f"✗ Sistema {percentage:.0f}% operativo - Configuración necesaria")
    
    print("="*60)
    
    # Guardar reporte
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'dependencies': {
            'installed': installed,
            'missing': missing
        },
        'files': files,
        'services': services,
        'mt5': mt5_info,
        'status_percentage': percentage
    }
    
    report_path = Path(__file__).parent / 'system_status_report.json'
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Reporte guardado en: system_status_report.json")

if __name__ == "__main__":
    try:
        generate_report()
        
        print("\n" + "="*60)
        print("ACCIONES RECOMENDADAS")
        print("="*60)
        
        print("""
1. Para iniciar el sistema completo:
   → Ejecuta: EJECUTAR_TODO.bat
   
2. Para instalar dependencias faltantes:
   → Ejecuta: INSTALAR.bat
   
3. Para reorganizar archivos:
   → Ejecuta: MASTER_ORGANIZER.bat
   
4. Para ver este estado nuevamente:
   → Ejecuta: python check_system_status.py
        """)
        
        input("\nPresiona Enter para salir...")
        
    except Exception as e:
        print(f"\n✗ Error al generar reporte: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
