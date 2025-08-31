import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

load_dotenv("configs/.env")
print("=== Testing MT5 Connection ===")

# Conectar a MT5 existente (sin parmetros para usar el que ya est abierto)
if mt5.initialize():
    print(" Connected to existing MT5!")
    
    # Info de la cuenta
    account_info = mt5.account_info()
    if account_info:
        print(f" Account: [account_info.login]")
        print(f" Balance: $[account_info.balance]")
        print(f" Server: [account_info.server]")
    
    # Probar smbolo BTCUSDm
    symbol = "BTCUSDm"
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        print(f" Symbol [symbol] found!")
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f" Current price: [tick.bid]")
    else:
        print(f" Symbol [symbol] not found, trying BTCUSD...")
        symbol = "BTCUSD"
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            print(f" Symbol [symbol] found!")
    
    print(" MT5 is ready for trading!")
else:
    print(" Could not connect to MT5")
    print("Error:", mt5.last_error())

mt5.shutdown()
