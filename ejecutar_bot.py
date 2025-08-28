"""
EJECUTOR DIRECTO DEL BOT DE TRADING
Script simplificado para ejecutar el bot inmediatamente
"""
import os
import sys
import time
from pathlib import Path

# Configurar encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cambiar al directorio del proyecto
os.chdir(Path(__file__).parent)

print("="*70)
print(" "*15 + "🤖 ALGO TRADER BOT - INICIANDO")
print("="*70)
print()

# Cargar configuración
try:
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    
    print("✅ Configuración cargada")
    print(f"   Cuenta: {os.getenv('MT5_LOGIN')}")
    print(f"   Servidor: {os.getenv('MT5_SERVER')}")
    print(f"   Símbolo: {os.getenv('SYMBOL')}")
    print(f"   Modo: {'LIVE ⚠️' if os.getenv('LIVE_TRADING') == 'true' else 'DEMO ✅'}")
except Exception as e:
    print(f"❌ Error cargando configuración: {e}")
    input("\nPresiona Enter para salir...")
    sys.exit(1)

print()
print("🔌 Conectando a MetaTrader 5...")

# Verificar MT5
try:
    import MetaTrader5 as mt5
    
    if mt5.initialize():
        account = mt5.account_info()
        if account:
            print(f"✅ MT5 Conectado | Balance: ${account.balance:.2f}")
        mt5.shutdown()
    else:
        print("⚠️ No se pudo conectar a MT5 automáticamente")
        print("   Asegúrate de que MT5 esté abierto")
except ImportError:
    print("❌ Librería MT5 no instalada")
    print("   Instalando...")
    os.system(f"{sys.executable} -m pip install MetaTrader5")

print()
print("🚀 INICIANDO BOT PRINCIPAL...")
print("-"*70)
print()

# Ejecutar el bot principal
try:
    # Importar y ejecutar el bot
    import FINAL_BOT
    
except KeyboardInterrupt:
    print("\n\n⛔ Bot detenido por el usuario")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("\n📦 Instalando dependencias faltantes...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")
    print("\n✅ Intenta ejecutar nuevamente")
except Exception as e:
    print(f"❌ Error ejecutando el bot: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("Bot finalizado")
input("\nPresiona Enter para salir...")
