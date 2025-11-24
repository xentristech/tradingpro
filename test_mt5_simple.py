import os
import sys
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

print("=" * 70)
print("TEST DE CONEXION MT5")
print("=" * 70)

login = int(os.getenv('MT5_LOGIN'))
password = os.getenv('MT5_PASSWORD')
server = os.getenv('MT5_SERVER')

print(f"Login: {login}")
print(f"Server: {server}")
print()

if not mt5.initialize(login=login, password=password, server=server):
    print(f"ERROR: {mt5.last_error()}")
    sys.exit(1)

print("CONEXION EXITOSA!")

account = mt5.account_info()
if account:
    print(f"\nBalance: ${account.balance:.2f}")
    print(f"Equity: ${account.equity:.2f}")
    print(f"Profit: ${account.profit:.2f}")
    print(f"Leverage: 1:{account.leverage}")

mt5.shutdown()
print("\nTest completado")
