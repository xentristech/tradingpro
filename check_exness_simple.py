import MetaTrader5 as mt5
import sys

print("="*60)
print("VERIFICANDO CUENTA EXNESS")
print("="*60)

# Inicializar MT5
if not mt5.initialize():
    print("ERROR: MetaTrader 5 no está abierto o no se puede conectar")
    print("Por favor abre MetaTrader 5 primero")
    input("\nPresiona Enter para salir...")
    sys.exit(1)

# Obtener info de cuenta
account = mt5.account_info()
if account:
    print(f"\nCUENTA CONECTADA:")
    print(f"Login: {account.login}")
    print(f"Servidor: {account.server}")
    print(f"Empresa: {account.company}")
    print(f"Balance: ${account.balance:.2f}")
    print(f"Equity: ${account.equity:.2f}")
    print(f"Apalancamiento: 1:{account.leverage}")
    
    # Verificar si es Exness
    if 'exness' in account.company.lower():
        print("\n✓ ES UNA CUENTA EXNESS")
        
        # Datos conocidos de Exness
        if account.login == 197678662:
            print("Cuenta Demo identificada: 197678662")
            print("Servidor: Exness-MT5Trial11")
    else:
        print(f"\n✗ NO ES EXNESS (es {account.company})")
else:
    print("ERROR: No se pudo obtener información de la cuenta")

# Verificar símbolos principales
print("\nSÍMBOLOS DISPONIBLES:")
symbols = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD', 'US30']
for symbol in symbols:
    info = mt5.symbol_info(symbol)
    if info and info.visible:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"  {symbol}: Bid={tick.bid:.5f} Ask={tick.ask:.5f}")

mt5.shutdown()
input("\nPresiona Enter para salir...")
