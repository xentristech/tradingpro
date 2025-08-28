#!/usr/bin/env python3
"""
ACTIVAR SIMBOLOS - Agregar simbolos al Market Watch y verificar trading
"""
import MetaTrader5 as mt5
import time

print("=== ACTIVANDO SIMBOLOS Y TRADING ===")

if not mt5.initialize():
    print("ERROR: No se pudo inicializar MT5")
    exit()

# Intentar agregar simbolos principales al Market Watch
symbols_to_add = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD',
    'BTCUSD', 'ETHUSD', 'LTCUSD', 'XAUUSD', 'XAGUSD',
    'BTCUSDm', 'ETHUSDm'  # Variantes mini
]

print("Agregando simbolos al Market Watch...")
added_count = 0

for symbol_name in symbols_to_add:
    try:
        # Intentar agregar al Market Watch
        if mt5.symbol_select(symbol_name, True):
            # Verificar que ahora es visible
            symbol_info = mt5.symbol_info(symbol_name)
            if symbol_info and symbol_info.visible:
                tick = mt5.symbol_info_tick(symbol_name)
                if tick:
                    print(f"+ {symbol_name}: {tick.bid}")
                    added_count += 1
        time.sleep(0.1)  # Pequeña pausa
    except:
        continue

print(f"Simbolos agregados: {added_count}")

# Verificar estado del terminal
terminal = mt5.terminal_info()
account = mt5.account_info()

print(f"\n=== ESTADO ACTUAL ===")
print(f"Cuenta: {account.login}")
print(f"Balance: ${account.balance:.2f}")
print(f"Trading cuenta: {account.trade_allowed}")
print(f"Expert Advisors: {account.trade_expert}")
if terminal:
    print(f"Auto Trading: {terminal.trade_allowed}")

# Si auto trading está deshabilitado, dar instrucciones claras
if terminal and not terminal.trade_allowed:
    print(f"\n!!! AUTO TRADING DESHABILITADO !!!")
    print(f"Para habilitar:")
    print(f"1. En MT5, presionar Ctrl+E (o Tools -> Options)")
    print(f"2. Ir a la pestana 'Expert Advisors'")
    print(f"3. Marcar 'Allow automated trading'")
    print(f"4. Marcar 'Allow DLL imports'")
    print(f"5. Hacer clic en 'OK'")
    print(f"6. Volver a ejecutar este script")
else:
    print(f"\n=== PROBANDO OPERACION REAL ===")
    
    # Buscar simbolo disponible
    test_symbol = None
    symbols = mt5.symbols_get()
    
    if symbols:
        for s in symbols:
            if s.visible:
                tick = mt5.symbol_info_tick(s.name)
                if tick and tick.bid > 0:
                    test_symbol = s.name
                    print(f"Usando simbolo: {test_symbol}")
                    print(f"Precio: {tick.bid}")
                    break
    
    if test_symbol:
        # EJECUTAR OPERACION REAL
        tick = mt5.symbol_info_tick(test_symbol)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": test_symbol,
            "volume": 0.01,
            "type": mt5.ORDER_TYPE_BUY,
            "price": tick.ask,
            "deviation": 20,
            "magic": 88888888,
            "comment": "EXNESS VALIDATION",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        print(f"\nEJECUTANDO: BUY 0.01 {test_symbol}")
        result = mt5.order_send(request)
        
        if result:
            print(f"Codigo respuesta: {result.retcode}")
            if hasattr(result, 'comment'):
                print(f"Comentario: {result.comment}")
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"EXITO! Ticket: {result.order}")
                
                # Verificar posicion
                time.sleep(1)
                positions = mt5.positions_get()
                if positions:
                    for p in positions:
                        if p.ticket == result.order:
                            print(f"Posicion confirmada:")
                            print(f"  Ticket: {p.ticket}")
                            print(f"  P&L: ${p.profit:.2f}")
                            
                            # Telegram
                            try:
                                from notifiers.telegram_notifier import send_telegram_message
                                send_telegram_message(f"EXNESS VALIDADO: Operacion real ejecutada en cuenta 197678662 - Ticket: {result.order} - {test_symbol}")
                            except:
                                pass
                            
                            print(f"\nSISTEMA FUNCIONAL - OPERACION REAL EJECUTADA")
                            break
            else:
                print(f"Error: {result.retcode}")
                if result.retcode == 10027:
                    print("Auto trading aun deshabilitado - seguir instrucciones arriba")
        else:
            print("Sin respuesta del servidor")
    else:
        print("No se encontro simbolo disponible")

# Estado final
positions = mt5.positions_get()
if positions:
    print(f"\nPosiciones finales: {len(positions)}")
    for p in positions:
        side = "BUY" if p.type == 0 else "SELL" 
        print(f"  {p.ticket}: {p.symbol} {side} P&L: ${p.profit:.2f}")

mt5.shutdown()
print("\n=== FIN ===")