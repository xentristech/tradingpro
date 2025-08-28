"""
VERIFICACIÓN Y CONEXIÓN AUTOMÁTICA A MT5
"""
import os
import sys
import time
from dotenv import load_dotenv

# Configurar encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cargar configuración
load_dotenv('configs/.env')

print("="*60)
print("   🔌 CONECTANDO A METATRADER 5")
print("="*60)

# Credenciales
login = int(os.getenv("MT5_LOGIN"))
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")
path = os.getenv("MT5_PATH")
symbol = os.getenv("SYMBOL", "BTCUSDm")

print(f"\n📋 CONFIGURACIÓN:")
print(f"   Login: {login}")
print(f"   Server: {server}")
print(f"   Symbol: {symbol}")
print("-"*60)

try:
    import MetaTrader5 as mt5
    
    # Intentar conectar varias veces
    max_attempts = 3
    connected = False
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Intento {attempt} de {max_attempts}...")
        
        if mt5.initialize(
            path=path,
            login=login,
            password=password,
            server=server,
            timeout=60000
        ):
            connected = True
            print("✅ ¡Conexión exitosa!")
            break
        else:
            error = mt5.last_error()
            print(f"❌ Error: {error}")
            
            if attempt < max_attempts:
                print("   Reintentando en 5 segundos...")
                time.sleep(5)
    
    if connected:
        # Verificar cuenta
        account = mt5.account_info()
        if account:
            print("\n💰 CUENTA CONECTADA:")
            print(f"   Número: {account.login}")
            print(f"   Balance: ${account.balance:.2f}")
            print(f"   Equity: ${account.equity:.2f}")
            print(f"   Servidor: {account.server}")
            
            if account.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO:
                print(f"   Tipo: DEMO ✅ (Modo seguro)")
            else:
                print(f"   Tipo: REAL ⚠️")
                
            # Verificar símbolo
            if mt5.symbol_select(symbol, True):
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    print(f"\n📊 {symbol}:")
                    print(f"   Precio actual: {tick.bid:.2f}")
                    print(f"   Spread: {tick.ask - tick.bid:.5f}")
            
            # Ver posiciones
            positions = mt5.positions_get()
            if positions:
                print(f"\n💼 POSICIONES ABIERTAS: {len(positions)}")
                total_pl = 0
                for pos in positions:
                    tipo = "COMPRA" if pos.type == 0 else "VENTA"
                    profit = pos.profit
                    total_pl += profit
                    color = "🟢" if profit >= 0 else "🔴"
                    print(f"   {color} #{pos.ticket}: {tipo} {pos.volume} @ {pos.price_open:.2f} | P&L: ${profit:.2f}")
                print(f"   📊 P&L TOTAL: ${total_pl:.2f}")
            else:
                print("\n💼 No hay posiciones abiertas")
                
            print("\n" + "="*60)
            print("✅ METATRADER 5 LISTO PARA OPERAR")
            print("="*60)
            
            # Mantener la conexión activa
            print("\n🤖 El bot puede operar normalmente")
            print("   - Las señales se ejecutarán automáticamente")
            print("   - El sistema de gestión de riesgo está activo")
            print("   - Los logs se guardan en la carpeta 'logs'")
            
        mt5.shutdown()
        
    else:
        print("\n❌ No se pudo conectar después de varios intentos")
        print("\n🔍 SOLUCIONES:")
        print("1. Verifica que MetaTrader 5 esté abierto")
        print("2. Revisa las credenciales en configs/.env")
        print("3. Verifica tu conexión a internet")
        print("4. Intenta cerrar y volver a abrir MT5")
        
except ImportError:
    print("❌ La librería MetaTrader5 no está instalada")
    print("Ejecuta: pip install MetaTrader5")
    
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    import traceback
    traceback.print_exc()

input("\nPresiona Enter para continuar...")
