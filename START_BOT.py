"""
SCRIPT DE INICIO RÁPIDO - ALGO TRADER BOT
Verifica el sistema y ejecuta el bot de manera segura
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Configurar encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("="*60)
print("    🤖 ALGO TRADER BOT - INICIO RÁPIDO")
print("="*60)

# 1. VERIFICAR ENTORNO VIRTUAL
venv_python = Path(".venv/Scripts/python.exe")
if not venv_python.exists():
    print("❌ ERROR: Entorno virtual no encontrado")
    print("   Ejecuta: python -m venv .venv")
    sys.exit(1)
print("✅ Entorno virtual encontrado")

# 2. CARGAR CONFIGURACIÓN
env_file = Path("configs/.env")
if not env_file.exists():
    print("❌ ERROR: Archivo .env no encontrado")
    print("   Copia configs/.env.example a configs/.env")
    sys.exit(1)

load_dotenv('configs/.env')
print("✅ Configuración cargada")

# 3. VERIFICAR VARIABLES CRÍTICAS
critical_vars = {
    "MT5_LOGIN": os.getenv("MT5_LOGIN"),
    "MT5_PASSWORD": os.getenv("MT5_PASSWORD"),
    "MT5_SERVER": os.getenv("MT5_SERVER"),
    "TWELVEDATA_API_KEY": os.getenv("TWELVEDATA_API_KEY"),
    "LIVE_TRADING": os.getenv("LIVE_TRADING")
}

print("\n📋 CONFIGURACIÓN ACTUAL:")
print("-" * 40)
for var, value in critical_vars.items():
    if var == "MT5_PASSWORD":
        display = "***" if value else "NO CONFIGURADO"
    elif var == "TWELVEDATA_API_KEY":
        display = value[:10] + "..." if value else "NO CONFIGURADO"
    else:
        display = value if value else "NO CONFIGURADO"
    
    if var == "LIVE_TRADING":
        if value == "true":
            print(f"   {var}: {display} ⚠️ MODO REAL")
        else:
            print(f"   {var}: {display} ✅ MODO DEMO")
    else:
        print(f"   {var}: {display}")

# 4. VERIFICAR CONEXIONES
print("\n🔌 VERIFICANDO CONEXIONES:")
print("-" * 40)

# Verificar TwelveData
print("   TwelveData API: ", end="")
try:
    import requests
    api_key = os.getenv("TWELVEDATA_API_KEY")
    if api_key:
        response = requests.get(
            f"https://api.twelvedata.com/api_usage?apikey={api_key}",
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Conectado")
        else:
            print("⚠️ Error de API")
    else:
        print("❌ API Key no configurada")
except Exception as e:
    print(f"❌ Error: {e}")

# Verificar Ollama
print("   Ollama Local: ", end="")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        print("✅ Ejecutándose")
    else:
        print("⚠️ No responde")
except:
    print("⚠️ No disponible (opcional)")

# Verificar MT5
print("   MetaTrader 5: ", end="")
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        account = mt5.account_info()
        if account:
            print(f"✅ Conectado (Balance: ${account.balance:.2f})")
        else:
            print("⚠️ Sin cuenta activa")
        mt5.shutdown()
    else:
        print("❌ No se pudo conectar")
except ImportError:
    print("❌ Librería no instalada")
except Exception as e:
    print(f"❌ Error: {e}")

# 5. MENÚ DE OPCIONES
print("\n" + "="*60)
print("🎯 ¿QUÉ DESEAS HACER?")
print("="*60)
print("1. Ejecutar prueba de conexión completa")
print("2. Iniciar bot en modo DEMO")
print("3. Ver logs en tiempo real")
print("4. Ejecutar backtesting")
print("5. Abrir dashboard (Streamlit)")
print("6. Verificar posiciones abiertas")
print("0. Salir")
print("-"*60)

try:
    opcion = input("Selecciona una opción (0-6): ").strip()
    
    if opcion == "1":
        print("\n🔧 Ejecutando prueba de sistema...")
        subprocess.run([str(venv_python), "test_system.py"])
        
    elif opcion == "2":
        live_mode = os.getenv("LIVE_TRADING", "false").lower() == "true"
        if live_mode:
            confirm = input("\n⚠️ ADVERTENCIA: Modo LIVE activado. ¿Continuar? (si/no): ")
            if confirm.lower() != "si":
                print("Operación cancelada")
                sys.exit(0)
        
        print("\n🚀 Iniciando bot...")
        print("   Presiona Ctrl+C para detener")
        print("-"*40)
        subprocess.run([str(venv_python), "FINAL_BOT.py"])
        
    elif opcion == "3":
        print("\n📊 Mostrando logs...")
        logs_dir = Path("logs")
        if logs_dir.exists():
            # Buscar el log más reciente
            log_files = list(logs_dir.glob("*.out.log"))
            if log_files:
                latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
                print(f"   Archivo: {latest_log.name}")
                print("-"*40)
                subprocess.run(["powershell", "Get-Content", str(latest_log), "-Wait", "-Tail", "50"])
            else:
                print("No hay logs disponibles")
        
    elif opcion == "4":
        print("\n📈 Ejecutando backtesting...")
        subprocess.run([str(venv_python), "backtester.py"])
        
    elif opcion == "5":
        print("\n🌐 Abriendo dashboard...")
        subprocess.run([str(venv_python), "-m", "streamlit", "run", "streamlit_app.py"])
        
    elif opcion == "6":
        print("\n💼 Verificando posiciones...")
        subprocess.run([str(venv_python), "list_positions.py"])
        
    elif opcion == "0":
        print("\n👋 Hasta luego!")
        sys.exit(0)
        
    else:
        print("❌ Opción no válida")
        
except KeyboardInterrupt:
    print("\n\n⛔ Bot detenido por el usuario")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n✅ Proceso completado")
input("Presiona Enter para salir...")
