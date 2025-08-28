import os
import sys

# Configurar encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("="*50)
print("TEST DE CONEXIÓN MT5 - EXNESS")
print("="*50)

# Cargar configuración
try:
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    print("✅ Configuración cargada")
except Exception as e:
    print(f"❌ Error cargando configuración: {e}")
    sys.exit(1)

# Mostrar configuración
print(f"Cuenta: {os.getenv('MT5_LOGIN')}")
print(f"Servidor: {os.getenv('MT5_SERVER')}")

# Intentar conectar a MT5
try:
    import MetaTrader5 as mt5
    print("\n✅ Librería MT5 importada")
    
    # Inicializar
    path = os.getenv('MT5_PATH')
    login = int(os.getenv('MT5_LOGIN'))
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    
    print(f"\nConectando a MT5...")
    print(f"Path: {path}")
    
    if mt5.initialize(path=path, login=login, password=password, server=server, timeout=60000):
        print("✅ MT5 inicializado")
        
        # Obtener información de cuenta
        account = mt5.account_info()
        if account:
            print(f"\n✅ CONECTADO EXITOSAMENTE")
            print(f"Cuenta: {account.login}")
            print(f"Balance: ${account.balance:.2f}")
            print(f"Equity: ${account.equity:.2f}")
            print(f"Servidor: {account.server}")
            print(f"Empresa: {account.company}")
            
            # Verificar símbolo
            symbol = os.getenv('SYMBOL', 'BTCUSDm')
            if mt5.symbol_select(symbol, True):
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    print(f"\n📊 {symbol}")
                    print(f"Bid: {tick.bid}")
                    print(f"Ask: {tick.ask}")
                    print(f"Spread: {tick.ask - tick.bid:.2f}")
        else:
            print("❌ No se pudo obtener información de cuenta")
            error = mt5.last_error()
            print(f"Error: {error}")
        
        mt5.shutdown()
    else:
        print("❌ No se pudo inicializar MT5")
        error = mt5.last_error()
        print(f"Error: {error}")
        
except ImportError as e:
    print(f"❌ MetaTrader5 no instalado: {e}")
    print("Instalando MetaTrader5...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "MetaTrader5"])
    print("Intenta ejecutar nuevamente")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50)
input("Presiona Enter para salir...")
