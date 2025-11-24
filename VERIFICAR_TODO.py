"""
SCRIPT DE VERIFICACIÓN Y CONEXIÓN REAL A MT5
No simulación - Verificación completa paso a paso
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Configurar encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("="*80)
print(" "*20 + "VERIFICACIÓN COMPLETA DEL SISTEMA")
print("="*80)
print()

# ========== PASO 1: VERIFICAR ARCHIVOS ==========
print("[PASO 1] VERIFICANDO ARCHIVOS Y RUTAS")
print("-"*40)

# Verificar archivo .env
env_file = Path("configs/.env")
if env_file.exists():
    print("✅ Archivo .env encontrado")
    
    # Cargar variables
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = os.getenv("MT5_LOGIN")
    mt5_password = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    print(f"   Path configurado: {mt5_path}")
    print(f"   Login: {mt5_login}")
    print(f"   Server: {mt5_server}")
else:
    print("❌ ERROR: No se encuentra configs/.env")
    sys.exit(1)

# Verificar que MT5 existe en el path configurado
mt5_exe = Path(mt5_path)
if mt5_exe.exists():
    print(f"✅ MetaTrader 5 encontrado en: {mt5_exe}")
    file_size_mb = mt5_exe.stat().st_size / (1024*1024)
    print(f"   Tamaño del archivo: {file_size_mb:.2f} MB")
else:
    print(f"❌ ERROR: No se encuentra MT5 en {mt5_path}")
    print("\n🔍 Buscando MT5 en ubicaciones alternativas...")
    
    possible_paths = [
        r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files\Exness MT5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
    ]
    
    mt5_found = False
    for path in possible_paths:
        if Path(path).exists():
            print(f"   ✅ Encontrado en: {path}")
            print(f"   Actualiza MT5_PATH en configs/.env a: {path}")
            mt5_found = True
            mt5_path = path
            break
    
    if not mt5_found:
        print("   ❌ No se encontró MT5 en ninguna ubicación conocida")
        sys.exit(1)

print()

# ========== PASO 2: VERIFICAR PROCESOS ==========
print("[PASO 2] VERIFICANDO PROCESOS ACTUALES")
print("-"*40)

# Verificar si MT5 ya está ejecutándose
try:
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
        capture_output=True,
        text=True,
        check=True
    )
    
    if "terminal64.exe" in result.stdout:
        print("✅ MetaTrader 5 ya está ejecutándose")
        
        # Obtener PID
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if "terminal64.exe" in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    print(f"   PID del proceso: {pid}")
    else:
        print("⚠️ MetaTrader 5 NO está ejecutándose")
        print("   Será necesario iniciarlo")
except Exception as e:
    print(f"❌ Error verificando procesos: {e}")

print()

# ========== PASO 3: ABRIR MT5 SI NO ESTÁ ABIERTO ==========
print("[PASO 3] INICIANDO METATRADER 5")
print("-"*40)

# Verificar de nuevo si está ejecutándose
mt5_running = False
try:
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
        capture_output=True,
        text=True
    )
    mt5_running = "terminal64.exe" in result.stdout
except:
    pass

if not mt5_running:
    print(f"🚀 Iniciando MT5 desde: {mt5_path}")
    try:
        # Iniciar MT5
        process = subprocess.Popen([mt5_path])
        print(f"   Proceso iniciado con PID: {process.pid}")
        
        # Esperar a que MT5 se inicie completamente
        print("   Esperando 15 segundos para que MT5 se inicie...")
        for i in range(15, 0, -1):
            print(f"   {i}...", end='', flush=True)
            time.sleep(1)
        print()
        
        # Verificar que se inició
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
            capture_output=True,
            text=True
        )
        
        if "terminal64.exe" in result.stdout:
            print("✅ MetaTrader 5 iniciado correctamente")
        else:
            print("❌ Error: MT5 no se inició correctamente")
            
    except Exception as e:
        print(f"❌ Error al iniciar MT5: {e}")
        print("   Intenta abrirlo manualmente")
else:
    print("✅ MetaTrader 5 ya estaba ejecutándose")

print()

# ========== PASO 4: VERIFICAR LIBRERÍA PYTHON MT5 ==========
print("[PASO 4] VERIFICANDO LIBRERÍA MetaTrader5 DE PYTHON")
print("-"*40)

try:
    import MetaTrader5 as mt5
    print("✅ Librería MetaTrader5 instalada")
    print(f"   Versión: {mt5.__version__ if hasattr(mt5, '__version__') else 'Desconocida'}")
except ImportError:
    print("❌ Librería MetaTrader5 NO instalada")
    print("\n📦 Instalando MetaTrader5...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "MetaTrader5"])
        import MetaTrader5 as mt5
        print("✅ Librería instalada correctamente")
    except:
        print("❌ No se pudo instalar la librería")
        sys.exit(1)

print()

# ========== PASO 5: INTENTAR CONEXIÓN ==========
print("[PASO 5] CONECTANDO A LA CUENTA MT5")
print("-"*40)

try:
    # Intentar inicializar MT5
    print(f"🔌 Conectando...")
    print(f"   Login: {mt5_login}")
    print(f"   Server: {mt5_server}")
    
    # Inicializar con timeout más largo
    initialized = mt5.initialize(
        path=mt5_path,
        login=int(mt5_login) if mt5_login else None,
        password=mt5_password,
        server=mt5_server,
        timeout=60000,
        portable=False
    )
    
    if initialized:
        print("✅ CONEXIÓN EXITOSA!")
        
        # Obtener información de cuenta
        account_info = mt5.account_info()
        if account_info:
            print("\n📊 INFORMACIÓN DE LA CUENTA:")
            print("-"*40)
            print(f"   Número de cuenta: {account_info.login}")
            print(f"   Servidor: {account_info.server}")
            print(f"   Nombre: {account_info.name}")
            print(f"   Compañía: {account_info.company}")
            print(f"   Balance: ${account_info.balance:.2f}")
            print(f"   Equity: ${account_info.equity:.2f}")
            print(f"   Margen libre: ${account_info.margin_free:.2f}")
            print(f"   Moneda: {account_info.currency}")
            print(f"   Apalancamiento: 1:{account_info.leverage}")
            
            # Verificar si es demo o real
            if account_info.trade_mode == 0:
                print(f"   Tipo de cuenta: DEMO ✅")
            else:
                print(f"   Tipo de cuenta: REAL ⚠️")
                
            # Verificar símbolo
            symbol = os.getenv("SYMBOL", "BTCUSDm")
            print(f"\n📈 VERIFICANDO SÍMBOLO: {symbol}")
            print("-"*40)
            
            # Seleccionar símbolo
            if mt5.symbol_select(symbol, True):
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    print(f"✅ Símbolo {symbol} disponible")
                    
                    # Obtener precio actual
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        print(f"   Precio Bid: {tick.bid}")
                        print(f"   Precio Ask: {tick.ask}")
                        print(f"   Spread: {tick.ask - tick.bid:.5f}")
                        print(f"   Volumen: {tick.volume}")
                else:
                    print(f"❌ No se pudo obtener info del símbolo")
            else:
                print(f"❌ Símbolo {symbol} no disponible")
                print("\n📋 Símbolos disponibles (primeros 10):")
                symbols = mt5.symbols_get()
                if symbols:
                    for i, s in enumerate(symbols[:10]):
                        print(f"   - {s.name}")
                        
            # Verificar posiciones abiertas
            positions = mt5.positions_get()
            print(f"\n💼 POSICIONES ABIERTAS: {len(positions) if positions else 0}")
            if positions:
                for pos in positions:
                    tipo = "COMPRA" if pos.type == 0 else "VENTA"
                    print(f"   #{pos.ticket}: {tipo} {pos.volume} {pos.symbol} | P&L: ${pos.profit:.2f}")
                    
        else:
            print("❌ No se pudo obtener información de la cuenta")
            print("   Posibles causas:")
            print("   - Credenciales incorrectas")
            print("   - Servidor incorrecto")
            print("   - Cuenta no activa")
            
        # Cerrar conexión
        mt5.shutdown()
        
    else:
        error = mt5.last_error()
        print(f"❌ NO SE PUDO CONECTAR A MT5")
        print(f"   Código de error: {error[0] if error else 'Desconocido'}")
        print(f"   Descripción: {error[1] if error else 'Sin descripción'}")
        
        print("\n🔍 POSIBLES SOLUCIONES:")
        print("   1. Verifica que MT5 esté abierto")
        print("   2. Revisa las credenciales en configs/.env")
        print("   3. Verifica el nombre del servidor")
        print("   4. Asegúrate de tener conexión a internet")
        print("   5. Intenta con una cuenta demo nueva")
        
        # Intentar obtener más información
        print("\n📝 INFORMACIÓN ADICIONAL:")
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"   Terminal conectado: {terminal_info.connected}")
            print(f"   Path del terminal: {terminal_info.path}")
            print(f"   Path de datos: {terminal_info.data_path}")
            
except Exception as e:
    print(f"❌ Error durante la conexión: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print(" "*20 + "VERIFICACIÓN COMPLETADA")
print("="*80)

# ========== RESUMEN FINAL ==========
print("\n📋 RESUMEN:")
print("-"*40)

checks = {
    "Archivo .env": env_file.exists(),
    "MT5 instalado": mt5_exe.exists() if 'mt5_exe' in locals() else False,
    "MT5 ejecutándose": mt5_running if 'mt5_running' in locals() else False,
    "Librería Python MT5": 'mt5' in sys.modules,
    "Conexión exitosa": initialized if 'initialized' in locals() else False
}

all_ok = True
for item, status in checks.items():
    icon = "✅" if status else "❌"
    print(f"   {icon} {item}")
    if not status:
        all_ok = False

print()
if all_ok:
    print("🎉 ¡TODO ESTÁ LISTO PARA EJECUTAR EL BOT!")
else:
    print("⚠️ Hay problemas que resolver antes de ejecutar el bot")

print()
input("Presiona Enter para salir...")
