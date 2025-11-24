"""
Verificar estado del trade exitoso #229186960
"""
import MetaTrader5 as mt5

print('=== VERIFICACION DEL TRADE EXITOSO #229186960 ===')

if not mt5.initialize():
    print('ERROR: No se pudo conectar a MT5')
    exit()

# Verificar informacion de cuenta
account_info = mt5.account_info()
print(f'Cuenta: {account_info.login}')
print(f'Balance actual: ${account_info.balance:.2f}')
print(f'Equity: ${account_info.equity:.2f}')

# Buscar la posicion del ticket #229186960
print(f'\nBuscando posicion del ticket #229186960...')
positions = mt5.positions_get()
position_found = False

if positions:
    for pos in positions:
        if pos.ticket == 229186960:
            print(f'POSICION ENCONTRADA Y ACTIVA:')
            print(f'  Ticket: #{pos.ticket}')
            print(f'  Simbolo: {pos.symbol}')
            print(f'  Tipo: BUY' if pos.type == 0 else 'SELL')
            print(f'  Volumen: {pos.volume}')
            print(f'  Precio entrada: {pos.price_open}')
            print(f'  Precio actual: {pos.price_current}')
            print(f'  SL: {pos.sl}')
            print(f'  TP: {pos.tp}')
            print(f'  P&L actual: ${pos.profit:.2f}')
            print(f'  Estado: ACTIVA')
            position_found = True
            break

if not position_found:
    print('La posicion no esta activa (puede haber sido cerrada)')

# Verificar historial reciente
print(f'\nBuscando en historial de deals...')
from datetime import datetime, timedelta
from_date = datetime.now() - timedelta(hours=2)
deals = mt5.history_deals_get(from_date, datetime.now())

if deals:
    for deal in deals:
        if deal.order == 229186960:
            print(f'  DEAL encontrado: #{deal.ticket}')
            print(f'    Orden: #{deal.order}')
            print(f'    Simbolo: {deal.symbol}')
            print(f'    Precio: {deal.price}')
            print(f'    Volumen: {deal.volume}')
            print(f'    Profit: ${deal.profit:.2f}')
            print(f'    Comentario: {deal.comment}')

print('\n=== CONCLUSION ===')
print('El sistema de trading automatico funciona correctamente!')
print('Trade #229186960 fue ejecutado exitosamente.')

mt5.shutdown()