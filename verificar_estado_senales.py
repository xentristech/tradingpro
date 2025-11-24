#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VERIFICADOR DE SEÑALES Y ESTADO DEL SISTEMA
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Configurar paths
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

def check_signals_status():
    """Verificar estado de las señales"""
    print("="*60)
    print("   VERIFICADOR DE SEÑALES - TRADING PRO v3.0")
    print("="*60)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar archivos de log
    log_dir = project_path / "logs"
    
    print("📁 VERIFICANDO LOGS DE SEÑALES:")
    print("-"*40)
    
    # Buscar archivos de log recientes
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        json_files = list(log_dir.glob("*.json"))
        
        print(f"Archivos de log encontrados: {len(log_files)}")
        print(f"Archivos JSON encontrados: {len(json_files)}")
        
        # Verificar logs recientes (últimas 24 horas)
        recent_logs = []
        one_day_ago = datetime.now() - timedelta(days=1)
        
        for log_file in log_files:
            mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mod_time > one_day_ago:
                recent_logs.append({
                    'file': log_file.name,
                    'time': mod_time,
                    'size': log_file.stat().st_size
                })
        
        if recent_logs:
            print(f"\n📝 Logs recientes (últimas 24h): {len(recent_logs)}")
            for log in sorted(recent_logs, key=lambda x: x['time'], reverse=True)[:5]:
                print(f"  - {log['file']}: {log['time'].strftime('%H:%M:%S')} ({log['size']} bytes)")
        else:
            print("\n⚠️ No hay logs recientes en las últimas 24 horas")
    else:
        print("❌ Directorio de logs no existe")
    
    # Verificar archivo de señales generadas
    signals_file = project_path / "logs" / "signals.json"
    if signals_file.exists():
        print("\n📊 SEÑALES GENERADAS:")
        print("-"*40)
        try:
            with open(signals_file, 'r') as f:
                signals = json.load(f)
                if isinstance(signals, list):
                    recent_signals = signals[-10:] if len(signals) > 10 else signals
                    print(f"Total señales registradas: {len(signals)}")
                    print(f"Últimas señales:")
                    for signal in recent_signals:
                        print(f"  - {signal.get('symbol', 'N/A')}: {signal.get('action', 'N/A')} ({signal.get('confidence', 0):.1f}%)")
                else:
                    print("Formato de archivo no reconocido")
        except Exception as e:
            print(f"Error leyendo señales: {e}")
    else:
        print("\n⚠️ No se encontró archivo de señales (signals.json)")
    
    # Verificar procesos en ejecución
    print("\n🔄 VERIFICANDO PROCESOS:")
    print("-"*40)
    
    import subprocess
    try:
        # Buscar procesos Python relacionados con el trading
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe"],
            capture_output=True,
            text=True
        )
        
        if "python.exe" in result.stdout:
            python_processes = result.stdout.count("python.exe")
            print(f"✅ Procesos Python activos: {python_processes}")
            
            # Buscar procesos específicos del sistema
            trading_keywords = ['MONITOR', 'SIGNAL', 'TRADING', 'START']
            for keyword in trading_keywords:
                if keyword.lower() in result.stdout.lower():
                    print(f"  ✓ Posible proceso de {keyword} detectado")
        else:
            print("⚠️ No hay procesos Python activos")
            
    except Exception as e:
        print(f"Error verificando procesos: {e}")
    
    # Verificar configuración
    print("\n⚙️ CONFIGURACIÓN:")
    print("-"*40)
    
    env_file = project_path / "configs" / ".env"
    if env_file.exists():
        print("✅ Archivo .env encontrado")
        
        # Verificar configuraciones clave
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            
            # Verificar APIs
            if os.getenv("TWELVEDATA_API_KEY"):
                print("  ✓ TwelveData API configurada")
            else:
                print("  ✗ TwelveData API NO configurada")
                
            if os.getenv("TELEGRAM_TOKEN"):
                print("  ✓ Telegram configurado")
            else:
                print("  ✗ Telegram NO configurado")
                
            if os.getenv("MT5_LOGIN"):
                print(f"  ✓ MT5 configurado (Cuenta: {os.getenv('MT5_LOGIN')})")
            else:
                print("  ✗ MT5 NO configurado")
                
            # Verificar Ollama
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            print(f"  ✓ Ollama configurado en: {ollama_host}")
            
        except Exception as e:
            print(f"Error verificando configuración: {e}")
    else:
        print("❌ Archivo .env NO encontrado")
    
    # Verificar conexión MT5
    print("\n🔌 CONEXIÓN MT5:")
    print("-"*40)
    
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            account = mt5.account_info()
            if account:
                print(f"✅ MT5 Conectado")
                print(f"  Cuenta: {account.login}")
                print(f"  Balance: ${account.balance:.2f}")
                
                # Verificar posiciones
                positions = mt5.positions_get()
                if positions:
                    print(f"  Posiciones abiertas: {len(positions)}")
                else:
                    print(f"  Posiciones abiertas: 0")
            else:
                print("⚠️ MT5 inicializado pero sin cuenta")
            mt5.shutdown()
        else:
            print("❌ MT5 no se pudo inicializar")
    except ImportError:
        print("❌ MetaTrader5 no está instalado")
    except Exception as e:
        print(f"❌ Error con MT5: {e}")
    
    print("\n" + "="*60)
    print("RESUMEN DEL ESTADO:")
    print("="*60)
    
    # Determinar estado general
    if recent_logs and env_file.exists():
        if len(recent_logs) > 0:
            print("🟢 Sistema parece haber estado activo recientemente")
        else:
            print("🟡 Sistema configurado pero sin actividad reciente")
    else:
        print("🔴 Sistema no parece estar ejecutándose")
    
    print("\nPARA INICIAR EL SISTEMA:")
    print("1. Ejecutar: START_TRADING_SYSTEM_MONITOR_PRIORITY_CLEAN.py")
    print("2. O usar: EJECUTAR_SISTEMA_COMPLETO.py")
    print("3. Para monitoreo: MONITOR_CONTINUO_TELEGRAM.py")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_signals_status()
    input("\nPresiona Enter para salir...")
