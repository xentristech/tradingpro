"""
ABRIR Y CONECTAR MT5 - SCRIPT MEJORADO
"""
import os
import sys
import time
import subprocess
import ctypes
from pathlib import Path

# Para mostrar ventanas de mensaje
MessageBox = ctypes.windll.user32.MessageBoxW

def show_message(title, message):
    """Mostrar mensaje en ventana emergente"""
    MessageBox(None, message, title, 0)

def check_mt5_running():
    """Verificar si MT5 está ejecutándose"""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
            capture_output=True,
            text=True
        )
        return "terminal64.exe" in result.stdout
    except:
        return False

def open_mt5():
    """Abrir MetaTrader 5"""
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    
    mt5_path = os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe")
    
    print("="*60)
    print("   ABRIENDO METATRADER 5")
    print("="*60)
    print()
    
    # Verificar si el archivo existe
    if not Path(mt5_path).exists():
        print(f"❌ ERROR: No se encuentra MT5 en: {mt5_path}")
        
        # Buscar en ubicaciones alternativas
        alt_paths = [
            r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files\Ava Trade MT5 Terminal\terminal64.exe"
        ]
        
        for path in alt_paths:
            if Path(path).exists():
                print(f"✅ Encontrado en: {path}")
                mt5_path = path
                break
        else:
            print("❌ No se encontró MT5 en ninguna ubicación")
            return False
    
    # Verificar si ya está ejecutándose
    if check_mt5_running():
        print("✅ MetaTrader 5 ya está ejecutándose")
        return True
    
    # Abrir MT5
    print(f"🚀 Abriendo MT5 desde: {mt5_path}")
    try:
        # Usar START para abrir MT5 sin bloquear
        subprocess.Popen([mt5_path])
        
        # Esperar a que se abra
        print("⏳ Esperando a que MT5 se inicie...")
        for i in range(20):
            time.sleep(1)
            print(f"   Esperando... {i+1}/20 segundos", end='\r')
            if check_mt5_running():
                print("\n✅ MetaTrader 5 iniciado correctamente!")
                return True
                
        print("\n⚠️ MT5 tardó más de lo esperado en iniciar")
        
    except Exception as e:
        print(f"❌ Error al abrir MT5: {e}")
        return False
        
    return check_mt5_running()

def connect_mt5():
    """Conectar a la cuenta de MT5"""
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("❌ Instalando librería MetaTrader5...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "MetaTrader5"])
        import MetaTrader5 as mt5
    
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    
    print("\n📊 CONECTANDO A LA CUENTA...")
    print("-"*40)
    
    # Credenciales
    login = int(os.getenv("MT5_LOGIN", "0"))
    password = os.getenv("MT5_PASSWORD", "")
    server = os.getenv("MT5_SERVER", "")
    
    print(f"Login: {login}")
    print(f"Server: {server}")
    
    # Intentar conectar múltiples veces
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔌 Intento {attempt}/{max_attempts}...")
        
        if mt5.initialize(login=login, password=password, server=server, timeout=60000):
            print("✅ ¡CONEXIÓN EXITOSA!")
            
            # Mostrar información
            account = mt5.account_info()
            if account:
                print(f"\n💰 CUENTA CONECTADA:")
                print(f"   Balance: ${account.balance:.2f}")
                print(f"   Equity: ${account.equity:.2f}")
                print(f"   Servidor: {account.server}")
                
                # Verificar símbolo
                symbol = os.getenv("SYMBOL", "BTCUSDm")
                if mt5.symbol_select(symbol, True):
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        print(f"\n📈 {symbol}: ${tick.bid:.2f}")
                        
            mt5.shutdown()
            return True
        else:
            error = mt5.last_error()
            print(f"❌ Error: {error}")
            
            if attempt < max_attempts:
                print("   Reintentando en 5 segundos...")
                time.sleep(5)
                
    return False

def main():
    """Función principal"""
    print("╔" + "═"*58 + "╗")
    print("║" + "SISTEMA DE APERTURA Y CONEXIÓN MT5".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    print()
    
    # Paso 1: Abrir MT5
    if not open_mt5():
        print("\n❌ No se pudo abrir MT5")
        print("Por favor, ábrelo manualmente")
        input("\nPresiona Enter cuando MT5 esté abierto...")
        
    # Paso 2: Conectar
    if connect_mt5():
        print("\n" + "="*60)
        print("✅ SISTEMA LISTO PARA OPERAR")
        print("="*60)
        
        # Mensaje de éxito
        show_message("MT5 Conectado", "MetaTrader 5 está conectado y listo para operar")
        
        return True
    else:
        print("\n❌ No se pudo conectar a la cuenta")
        print("\n🔍 Verifica:")
        print("   1. Que MT5 esté abierto")
        print("   2. Las credenciales en configs/.env")
        print("   3. El nombre del servidor")
        print("   4. Tu conexión a internet")
        
        return False

if __name__ == "__main__":
    success = main()
    print()
    if success:
        print("✅ Puedes ejecutar el bot ahora")
    else:
        print("❌ Resuelve los problemas antes de ejecutar el bot")
    
    input("\nPresiona Enter para salir...")
