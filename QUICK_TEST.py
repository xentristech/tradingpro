import MetaTrader5 as mt5
import time

# Configuración EXNESS
path = r'C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe'
login = 197678662
password = 'Badboy930218*'
server = 'Exness-MT5Trial11'

print('EXNESS QUICK LIVE TEST')
print('='*40)

# Conectar
if mt5.initialize(path):
    print('[OK] MT5 initialized')

    if mt5.login(login, password, server):
        print('[OK] Logged in to EXNESS')

        # Info cuenta
        account = mt5.account_info()
        if account:
            print(f'Balance: ${account.balance:,.2f}')
            print(f'Equity: ${account.equity:,.2f}')
            print(f'Free Margin: ${account.margin_free:,.2f}')

        # Test símbolo
        symbol = 'EURUSDm'
        if mt5.symbol_select(symbol, True):
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                print(f'{symbol}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}')
                print('System ready for live trading!')

        # Posiciones actuales
        positions = mt5.positions_get()
        print(f'Open positions: {len(positions) if positions else 0}')

        mt5.shutdown()
        print('[OK] Disconnected')
    else:
        print('[ERROR] Login failed')
else:
    print('[ERROR] MT5 initialization failed')