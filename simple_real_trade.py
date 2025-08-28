import MetaTrader5 as mt5

mt5.initialize()
account = mt5.account_info()
print(f"Cuenta: {account.login}")
print(f"Balance: ${account.balance:.2f}")

# Buscar primer simbolo disponible
symbols = mt5.symbols_get()
symbol_name = None
for s in symbols:
    if s.visible:
        tick = mt5.symbol_info_tick(s.name)
        if tick and tick.bid > 0:
            symbol_name = s.name
            print(f"Simbolo: {symbol_name}")
            print(f"Precio: {tick.bid}")
            break

if symbol_name:
    # Crear orden
    tick = mt5.symbol_info_tick(symbol_name)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol_name,
        "volume": 0.01,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "deviation": 20,
        "magic": 99999,
        "comment": "REAL TRADE NOW",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    print("Ejecutando orden...")
    result = mt5.order_send(request)
    
    if result:
        print(f"Codigo: {result.retcode}")
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"EXITO - Ticket: {result.order}")
            
            # Verificar
            import time
            time.sleep(1)
            positions = mt5.positions_get()
            if positions:
                for p in positions:
                    if p.ticket == result.order:
                        print(f"Posicion confirmada: {p.ticket}")
                        print(f"P&L: ${p.profit:.2f}")
                        break
        else:
            print(f"Error: {result.comment if hasattr(result, 'comment') else 'Unknown'}")
    else:
        print("Sin respuesta")

# Estado final
positions = mt5.positions_get()
if positions:
    print(f"Total posiciones: {len(positions)}")
    for p in positions:
        side = "BUY" if p.type == 0 else "SELL"
        print(f"  {p.ticket}: {p.symbol} {side} P&L: ${p.profit:.2f}")
else:
    print("No hay posiciones")

mt5.shutdown()