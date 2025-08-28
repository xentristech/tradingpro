#!/usr/bin/env python3
"""
OPERACIÓN REAL AHORA - Sin trucos, operación real inmediata
"""
import MetaTrader5 as mt5
import time

print("=== OPERACIÓN REAL EN VIVO ===")

# Conectar
if not mt5.initialize():
    print("ERROR: No se pudo conectar a MT5")
    exit()

account = mt5.account_info()
print(f"Cuenta: {account.login}")
print(f"Balance: ${account.balance:.2f}")

# Buscar símbolo disponible
symbols = mt5.symbols_get()
available_symbol = None

for symbol in symbols:
    if symbol.visible:
        tick = mt5.symbol_info_tick(symbol.name)
        if tick and tick.bid > 0:
            available_symbol = symbol.name
            print(f"Símbolo encontrado: {available_symbol}")
            print(f"Precio actual: {tick.bid:.5f}")
            break

if not available_symbol:
    print("ERROR: No se encontró símbolo disponible")
    mt5.shutdown()
    exit()

# Crear orden REAL
volume = 0.01
tick = mt5.symbol_info_tick(available_symbol)
price = tick.ask

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": available_symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": price,
    "deviation": 20,
    "magic": 12345678,
    "comment": "OPERACION REAL",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_FOK,
}

print(f"\n🚀 EJECUTANDO ORDEN REAL:")
print(f"   BUY {volume} {available_symbol} a {price}")

# Enviar orden
result = mt5.order_send(request)

if result:
    print(f"\nRESPUESTA MT5:")
    print(f"   Código: {result.retcode}")
    if hasattr(result, 'comment'):
        print(f"   Comentario: {result.comment}")
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"\n✅ ORDEN EJECUTADA EXITOSAMENTE")
        print(f"   Ticket: {result.order}")
        print(f"   Precio: {result.price}")
        
        # Verificar que la posición existe
        time.sleep(2)
        positions = mt5.positions_get()
        if positions:
            for pos in positions:
                if pos.ticket == result.order:
                    print(f"\n📊 POSICIÓN CONFIRMADA:")
                    print(f"   Ticket: {pos.ticket}")
                    print(f"   Símbolo: {pos.symbol}")
                    print(f"   Volumen: {pos.volume}")
                    print(f"   P&L: ${pos.profit:.2f}")
                    
                    # Ahora cerrarla para completar el ciclo
                    print(f"\n🔄 CERRANDO LA POSICIÓN...")
                    
                    close_price = mt5.symbol_info_tick(available_symbol).bid
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": available_symbol,
                        "volume": volume,
                        "type": mt5.ORDER_TYPE_SELL,
                        "position": pos.ticket,
                        "price": close_price,
                        "deviation": 20,
                        "magic": 12345678,
                        "comment": "CIERRE REAL",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_FOK,
                    }
                    
                    close_result = mt5.order_send(close_request)
                    
                    if close_result and close_result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"✅ POSICIÓN CERRADA - Ticket: {close_result.order}")
                        print(f"   P&L Final: ${pos.profit:.2f}")
                        
                        # Telegram
                        try:
                            from notifiers.telegram_notifier import send_telegram_message
                            send_telegram_message(f"✅ OPERACIÓN REAL COMPLETADA:\n- Abierta: BUY {volume} {available_symbol} (Ticket: {result.order})\n- Cerrada con P&L: ${pos.profit:.2f}\n- Sistema funcionando correctamente")
                        except:
                            pass
                        
                        print(f"\n🎉 CICLO COMPLETO EXITOSO - SISTEMA FUNCIONAL")
                    else:
                        error = close_result.comment if close_result else "Sin respuesta"
                        print(f"❌ Error cerrando: {error}")
                    break
    else:
        print(f"❌ ERROR EN ORDEN: {result.retcode}")
        if hasattr(result, 'comment'):
            print(f"   {result.comment}")
else:
    print("❌ Sin respuesta del servidor")

mt5.shutdown()
print("\n=== FIN ===")