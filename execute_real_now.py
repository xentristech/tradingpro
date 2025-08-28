#!/usr/bin/env python3
import MetaTrader5 as mt5
import time

print("=== OPERACION REAL EN VIVO ===")

# Conectar
mt5.initialize()
account = mt5.account_info()
print(f"Cuenta: {account.login}")
print(f"Balance: ${account.balance:.2f}")

# EURUSD disponible
symbol = "EURUSD"
tick = mt5.symbol_info_tick(symbol)
print(f"EURUSD Precio: {tick.bid:.5f}")

# Crear orden REAL
volume = 0.01
price = tick.ask

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": price,
    "deviation": 20,
    "magic": 11111111,
    "comment": "OPERACION REAL AHORA",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_FOK,
}

print(f"\nEJECUTANDO: BUY {volume} {symbol} a {price:.5f}")

# Enviar orden
result = mt5.order_send(request)

if result and result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"EXITO - ORDEN EJECUTADA")
    print(f"Ticket: {result.order}")
    print(f"Precio: {result.price:.5f}")
    
    # Verificar posicion
    time.sleep(1)
    positions = mt5.positions_get()
    for pos in positions:
        if pos.ticket == result.order:
            print(f"\nPOSICION CONFIRMADA:")
            print(f"Ticket: {pos.ticket}")
            print(f"P&L: ${pos.profit:.2f}")
            
            # Telegram notification
            try:
                from notifiers.telegram_notifier import send_telegram_message
                send_telegram_message(f"OPERACION REAL EJECUTADA: BUY {volume} {symbol} - Ticket: {result.order} - P&L: ${pos.profit:.2f}")
            except:
                print("Error enviando Telegram")
            
            print(f"\nSISTEMA FUNCIONA - OPERACION REAL CREADA")
            break
    
else:
    error = result.comment if result else "Sin respuesta"
    print(f"ERROR: {error}")

# Estado final
positions = mt5.positions_get()
print(f"\nPosiciones totales: {len(positions) if positions else 0}")

mt5.shutdown()