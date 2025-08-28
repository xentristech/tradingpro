"""
TEST RÁPIDO DE METATRADER 5
Verifica la conexión con MT5 usando las credenciales del .env
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Configurar encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cargar configuración
load_dotenv('configs/.env')

print("="*60)
print("   PRUEBA DE CONEXIÓN METATRADER 5")
print("="*60)

# Obtener credenciales
mt5_login = os.getenv("MT5_LOGIN")
mt5_password = os.getenv("MT5_PASSWORD")
mt5_server = os.getenv("MT5_SERVER")
mt5_path = os.getenv("MT5_PATH")
symbol = os.getenv("SYMBOL", "BTCUSDm")

print(f"\n📋 CONFIGURACIÓN:")
print(f"   Login: {mt5_login}")
print(f"   Server: {mt5_server}")
print(f"   Path: {mt5_path}")
print(f"   Symbol: {symbol}")
print("-"*60)

try:
    import MetaTrader5 as mt5
    
    print("\n🔌 CONECTANDO A MT5...")
    
    # Inicializar MT5
    if mt5.initialize(
        path=mt5_path,
        login=int(mt5_login) if mt5_login else None,
        password=mt5_password,
        server=mt5_server,
        timeout=60000
    ):
        print("✅ Conexión exitosa!")
        
        # Información de cuenta
        account_info = mt5.account_info()
        if account_info:
            print("\n💰 INFORMACIÓN DE CUENTA:")
            print(f"   Número: {account_info.login}")
            print(f"   Servidor: {account_info.server}")
            print(f"   Balance: ${account_info.balance:.2f}")
            print(f"   Equity: ${account_info.equity:.2f}")
            print(f"   Margen libre: ${account_info.margin_free:.2f}")
            print(f"   Apalancamiento: 1:{account_info.leverage}")
            print(f"   Moneda: {account_info.currency}")
            
            # Verificar si es cuenta demo o real
            if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO:
                print(f"   Tipo: DEMO ✅")
            else:
                print(f"   Tipo: REAL ⚠️")
        
        # Verificar símbolo
        print(f"\n📊 VERIFICANDO SÍMBOLO {symbol}...")
        if mt5.symbol_select(symbol, True):
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                print(f"✅ Símbolo disponible")
                
                # Obtener precio actual
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    print(f"\n💹 PRECIO ACTUAL:")
                    print(f"   Bid: {tick.bid}")
                    print(f"   Ask: {tick.ask}")
                    print(f"   Spread: {tick.ask - tick.bid:.5f}")
                    print(f"   Tiempo: {datetime.fromtimestamp(tick.time)}")
                
                # Información del símbolo
                print(f"\n📈 INFORMACIÓN DEL SÍMBOLO:")
                print(f"   Descripción: {symbol_info.description}")
                print(f"   Volumen mínimo: {symbol_info.volume_min}")
                print(f"   Volumen máximo: {symbol_info.volume_max}")
                print(f"   Step de volumen: {symbol_info.volume_step}")
                print(f"   Spread actual: {symbol_info.spread}")
                print(f"   Digits: {symbol_info.digits}")
        else:
            print(f"❌ No se pudo seleccionar el símbolo {symbol}")
            print("\n📋 SÍMBOLOS DISPONIBLES:")
            symbols = mt5.symbols_get()
            if symbols:
                # Mostrar primeros 20 símbolos
                for i, s in enumerate(symbols[:20]):
                    print(f"   - {s.name}")
                if len(symbols) > 20:
                    print(f"   ... y {len(symbols)-20} más")
        
        # Verificar posiciones abiertas
        positions = mt5.positions_get()
        print(f"\n💼 POSICIONES ABIERTAS: {len(positions) if positions else 0}")
        if positions:
            for pos in positions:
                tipo = "COMPRA" if pos.type == 0 else "VENTA"
                profit = pos.profit
                color = "🟢" if profit >= 0 else "🔴"
                print(f"   {color} {tipo} {pos.volume} {pos.symbol} | P&L: ${profit:.2f}")
        
        # Verificar órdenes pendientes
        orders = mt5.orders_get()
        print(f"\n📝 ÓRDENES PENDIENTES: {len(orders) if orders else 0}")
        if orders:
            for order in orders:
                print(f"   - {order.symbol}: {order.type_description}")
        
        # Cerrar conexión
        mt5.shutdown()
        print("\n✅ Prueba completada exitosamente")
        
    else:
        error = mt5.last_error()
        print(f"❌ No se pudo conectar a MT5")
        print(f"   Error: {error}")
        print("\n🔍 POSIBLES SOLUCIONES:")
        print("   1. Verificar que MetaTrader 5 esté instalado")
        print("   2. Verificar credenciales en configs/.env")
        print("   3. Asegurarse de que MT5 esté abierto")
        print("   4. Verificar conexión a internet")
        print("   5. Probar con una cuenta demo")
        
except ImportError:
    print("❌ MetaTrader5 no está instalado")
    print("\n📦 Para instalar, ejecuta:")
    print("   .venv\\Scripts\\pip install MetaTrader5")
    
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
input("Presiona Enter para salir...")
