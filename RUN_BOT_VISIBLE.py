"""
EJECUTOR PRINCIPAL DEL BOT - VISIBLE
Muestra todo el output en tiempo real
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Configurar encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cambiar al directorio del proyecto
os.chdir(Path(__file__).parent)

# Cargar configuración
load_dotenv('configs/.env')

print("="*80)
print(" "*20 + "🤖 ALGO TRADER BOT - EJECUTANDO")
print("="*80)
print()

# Mostrar configuración
print("📋 CONFIGURACIÓN:")
print("-"*40)
print(f"  Cuenta MT5: {os.getenv('MT5_LOGIN')}")
print(f"  Servidor: {os.getenv('MT5_SERVER')}")
print(f"  Símbolo: {os.getenv('SYMBOL')}")
print(f"  Modo: {'🔴 LIVE' if os.getenv('LIVE_TRADING') == 'true' else '🟢 DEMO'}")
print(f"  SL Default: ${os.getenv('DEF_SL_USD')}")
print(f"  TP Default: ${os.getenv('DEF_TP_USD')}")
print()

print("🚀 INICIANDO BOT PRINCIPAL...")
print("-"*80)
print()

try:
    # Ejecutar el bot principal y mostrar output en tiempo real
    proc = subprocess.Popen(
        [sys.executable, "FINAL_BOT.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Mostrar output línea por línea
    for line in proc.stdout:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {line}", end='')
    
    proc.wait()
    
except KeyboardInterrupt:
    print("\n\n⛔ Bot detenido por el usuario")
    proc.terminate()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    
print("\n" + "="*80)
print("Bot finalizado")
input("Presiona Enter para salir...")
