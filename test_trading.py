import MetaTrader5 as mt5
import time

print('=== PRUEBA DIRECTA DE TRADING AUTOMATICO ===')
print('Conectando a MT5...')

if not mt5.initialize():
    print('ERROR: No se pudo conectar a MT5')
    exit()

account_info = mt5.account_info()
print(f'Cuenta: {account_info.login}')
print(f'Balance: ${account_info.balance:.2f}')

symbol = 'BTCXAUm'
if not mt5.symbol_select(symbol, True):
    print(f'ERROR: No se pudo seleccionar {symbol}')
    exit()

tick = mt5.symbol_info_tick(symbol)
price = tick.ask
sl = price - 1.0  # 1.0 SL para BTCXAUm
tp = price + 3.0  # 3.0 TP para BTCXAUm

print(f'Precio {symbol}: {price}')
print(f'SL: {sl} | TP: {tp}')

order = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': 0.01,
    'type': mt5.ORDER_TYPE_BUY,
    'price': price,
    'sl': sl,
    'tp': tp,
    'magic': 999999,
    'comment': 'TEST_AUTO_TRADING',
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_IOC,
}

print('Ejecutando orden BUY...')
result = mt5.order_send(order)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f'EXITO! Ticket: #{result.order}')
    print(f'Precio ejecutado: {result.price}')
    print('SISTEMA DE TRADING AUTOMATICO FUNCIONANDO!')
    
    time.sleep(2)
    positions = mt5.positions_get(symbol=symbol)
    for pos in positions:
        if pos.ticket == result.order:
            print(f'Posicion confirmada: #{pos.ticket}')
            print(f'P&L actual: ${pos.profit:.2f}')
            break
else:
    print(f'ERROR: {result.retcode} - {result.comment}')

mt5.shutdown()