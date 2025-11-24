#!/usr/bin/env python
"""
Check current MT5 status and recent operations
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta

# Initialize MT5
if not mt5.initialize():
    print('MT5 initialization failed')
    exit()

# Get account info
account = mt5.account_info()
if account:
    print(f'ESTADO ACTUAL DE CUENTA MT5')
    print(f'  Cuenta: {account.login}')
    print(f'  Balance: ${account.balance:.2f}')
    print(f'  Equity: ${account.equity:.2f}')
    print(f'  Margen libre: ${account.margin_free:.2f}')
    print(f'  Profit/Loss: ${account.profit:.2f}')

# Get open positions
positions = mt5.positions_get()
print(f'\nPOSICIONES ABIERTAS ({len(positions)}):')
if positions:
    for pos in positions:
        direction = 'BUY' if pos.type == 0 else 'SELL'
        print(f'  #{pos.ticket} {pos.symbol} {direction} Vol:{pos.volume}')
        print(f'    P&L: ${pos.profit:.2f} | SL: {pos.sl} | TP: {pos.tp}')
        print(f'    Precio entrada: {pos.price_open:.5f}')
        print(f'    Precio actual: {pos.price_current:.5f}')
else:
    print('  No hay posiciones abiertas')

# Get recent history (last 10 trades)
print(f'\nULTIMAS 10 OPERACIONES CERRADAS:')
from_date = datetime.now() - timedelta(days=3)
to_date = datetime.now()

history = mt5.history_deals_get(from_date, to_date)
if history:
    deals = sorted(history, key=lambda x: x.time, reverse=True)[:10]
    total_profit = 0
    
    for deal in deals:
        if deal.type in [0, 1]:  # Buy or Sell deals
            time_str = datetime.fromtimestamp(deal.time).strftime('%m-%d %H:%M')
            direction = 'BUY' if deal.type == 0 else 'SELL'
            print(f'  {time_str} #{deal.ticket} {deal.symbol} {direction}')
            print(f'    Vol: {deal.volume} | Precio: {deal.price:.5f} | P&L: ${deal.profit:.2f}')
            total_profit += deal.profit
    
    print(f'\nPROFIT TOTAL ULTIMAS OPERACIONES: ${total_profit:.2f}')

mt5.shutdown()