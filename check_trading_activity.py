import MetaTrader5 as mt5
from datetime import datetime, timedelta

mt5.initialize()

# Check current positions
positions = mt5.positions_get()
print(f'=== POSICIONES ACTUALES ({len(positions) if positions else 0}) ===')
if positions:
    for p in positions:
        type_name = "BUY" if p.type == 0 else "SELL"
        print(f'- {p.symbol}: {type_name} | Vol: {p.volume} | Profit: ${p.profit:.2f} | Time: {datetime.fromtimestamp(p.time)}')
else:
    print('No hay posiciones abiertas')

# Check recent orders/deals
print('\n=== ORDENES RECIENTES (ultima hora) ===')
from_time = datetime.now() - timedelta(hours=1)
orders = mt5.history_orders_get(from_time, datetime.now())
if orders:
    for order in orders[-5:]:  # ultimas 5
        order_type = "BUY" if order.type == 0 else "SELL"
        print(f'- {order.symbol}: {order_type} | Vol: {order.volume_current} | State: {order.state} | Time: {datetime.fromtimestamp(order.time_setup)}')
else:
    print('No hay ordenes recientes')

print('\n=== DEALS RECIENTES (ultima hora) ===')
deals = mt5.history_deals_get(from_time, datetime.now())
if deals:
    for deal in deals[-5:]:  # ultimos 5
        deal_type = "BUY" if deal.type == 0 else "SELL"
        print(f'- {deal.symbol}: {deal_type} | Vol: {deal.volume} | Profit: ${deal.profit:.2f} | Time: {datetime.fromtimestamp(deal.time)}')
else:
    print('No hay deals recientes')

mt5.shutdown()