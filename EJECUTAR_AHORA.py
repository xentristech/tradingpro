"""
LAUNCHER DIRECTO DEL BOT
"""
import sys
import os
import subprocess
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Cambiar al directorio del proyecto
os.chdir(project_dir)

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv('configs/.env')

print("="*60)
print("   EJECUTANDO ALGO TRADER BOT")
print("="*60)

# Mostrar configuración
print("\nCONFIGURACION ACTUAL:")
print(f"   MT5 Login: {os.getenv('MT5_LOGIN')}")
print(f"   MT5 Server: {os.getenv('MT5_SERVER')}")
print(f"   Symbol: {os.getenv('SYMBOL')}")
print(f"   Live Trading: {os.getenv('LIVE_TRADING')} {'REAL' if os.getenv('LIVE_TRADING') == 'true' else 'DEMO'}")
print(f"   TwelveData API: {'Configurada' if os.getenv('TWELVEDATA_API_KEY') else 'No configurada'}")
print(f"   Telegram: {'Configurado' if os.getenv('TELEGRAM_TOKEN') else 'No configurado'}")

print("\n" + "="*60)
print("INICIANDO BOT PRINCIPAL...")
print("="*60)

try:
    # Importar y ejecutar el bot principal
    import FINAL_BOT
except KeyboardInterrupt:
    print("\n\n⛔ Bot detenido por el usuario")
except ImportError as e:
    print(f"\n❌ Error importando módulos: {e}")
    print("\n📦 Instalando dependencias faltantes...")
    
    # Lista de paquetes esenciales
    packages = [
        'MetaTrader5',
        'pandas',
        'numpy',
        'requests',
        'python-dotenv',
        'pytz'
    ]
    
    for package in packages:
        print(f"   Instalando {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    print("\n✅ Dependencias instaladas. Intenta ejecutar nuevamente.")
    
except Exception as e:
    print(f"\n❌ Error ejecutando el bot: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "="*60)
input("Presiona Enter para salir...")
