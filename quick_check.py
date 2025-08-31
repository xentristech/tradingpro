#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VERIFICACIÓN RÁPIDA DEL SISTEMA - ALGO TRADER V3
================================================
Verifica rápidamente que los componentes principales estén funcionando
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time

def check_component(name, check_func):
    """Ejecuta una verificación y muestra el resultado"""
    try:
        result = check_func()
        if result:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: FALLO")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)[:50]}")
        return False

def check_env():
    """Verifica el archivo .env"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        # Verificar TwelveData API key
        if 'TWELVEDATA_API_KEY=' in content:
            # Verificar que no sea la hardcodeada
            if '23d17ce5b7044ad5aef9766770a6252b' not in content:
                return True
    return False

def check_mt5():
    """Verifica MT5"""
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            mt5.shutdown()
            return True
    except:
        pass
    return False

def check_telegram():
    """Verifica Telegram"""
    try:
        from src.notifiers.telegram_notifier import TelegramNotifier
        notifier = TelegramNotifier()
        return notifier.is_active
    except:
        pass
    return False

def check_twelvedata():
    """Verifica TwelveData"""
    try:
        # Intentar cliente optimizado primero
        try:
            from src.data.twelvedata_client_optimized import TwelveDataClientOptimized
            client = TwelveDataClientOptimized()
        except:
            from src.data.twelvedata_client import TwelveDataClient
            client = TwelveDataClient()
        return hasattr(client, 'api_key') and client.api_key
    except:
        pass
    return False

def check_database():
    """Verifica la base de datos"""
    db_path = Path('storage/trading.db')
    return db_path.exists()

def check_signal_generator():
    """Verifica el generador de señales"""
    signal_gen = Path('src/signals/realtime_signal_generator.py')
    return signal_gen.exists()

def check_processes():
    """Verifica procesos activos"""
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline']):
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            if 'signal_generator' in cmdline or 'telegram_notifier' in cmdline:
                return True
    except:
        pass
    return False

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║          VERIFICACIÓN RÁPIDA - ALGO TRADER V3                 ║
╚════════════════════════════════════════════════════════════════╝
    """)
    print(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("VERIFICANDO COMPONENTES PRINCIPALES:\n")
    
    # Lista de verificaciones
    checks = [
        ("Archivo .env", check_env),
        ("MetaTrader 5", check_mt5),
        ("Bot Telegram", check_telegram),
        ("TwelveData API", check_twelvedata),
        ("Base de datos", check_database),
        ("Generador señales", check_signal_generator),
        ("Procesos activos", check_processes)
    ]
    
    results = []
    for name, func in checks:
        result = check_component(name, func)
        results.append(result)
        time.sleep(0.5)
    
    # Resumen
    print("\n" + "="*50)
    total = len(results)
    passed = sum(results)
    
    if passed == total:
        print("✅ SISTEMA COMPLETAMENTE FUNCIONAL")
        print(f"   Todos los componentes ({passed}/{total}) están OK")
    elif passed >= total * 0.7:
        print("⚠️ SISTEMA FUNCIONAL CON ADVERTENCIAS")
        print(f"   {passed}/{total} componentes funcionando")
    else:
        print("❌ SISTEMA CON PROBLEMAS CRÍTICOS")
        print(f"   Solo {passed}/{total} componentes funcionando")
    
    print("="*50)
    
    # Recomendaciones
    if passed < total:
        print("\n📋 RECOMENDACIONES:")
        
        if not results[0]:  # .env
            print("  1. Configura tu archivo .env")
            print("     Ejecuta: ACTUALIZAR_SEGURIDAD_URGENTE.bat")
            
        if not results[1]:  # MT5
            print("  2. Verifica que MetaTrader 5 esté instalado y abierto")
            
        if not results[2]:  # Telegram
            print("  3. Configura el bot de Telegram en .env")
            
        if not results[6]:  # Procesos
            print("  4. Inicia el sistema con EJECUTAR_TODO_PRO.bat")
    
    print("\nPara un diagnóstico completo, ejecuta: EJECUTAR_DIAGNOSTICO.bat")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nVerificación cancelada")
        sys.exit(1)
