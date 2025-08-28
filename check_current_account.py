#!/usr/bin/env python3
import MetaTrader5 as mt5

print("=== VERIFICACION CUENTA ACTUAL ===")

# Conectar con cuenta actual
if not mt5.initialize():
    print("ERROR: No se pudo inicializar MT5")
    exit()

# Info de cuenta
account = mt5.account_info()
if not account:
    print("ERROR: No se pudo obtener info de cuenta")
    exit()

print(f"Cuenta: {account.login}")
print(f"Servidor: {account.server}")
print(f"Balance: ${account.balance:.2f}")
print(f"Trading permitido: {account.trade_allowed}")
print(f"Expert Advisors: {account.trade_expert}")

# Info de terminal
terminal = mt5.terminal_info()
if terminal:
    print(f"Auto Trading terminal: {terminal.trade_allowed}")
    print(f"Conectado: {terminal.connected}")
else:
    print("No se pudo obtener info de terminal")

# Verificar simbolos disponibles
print("\n=== SIMBOLOS DISPONIBLES ===")
symbols = mt5.symbols_get()
if symbols:
    available_count = 0
    for s in symbols[:20]:  # Primeros 20
        if s.visible:
            tick = mt5.symbol_info_tick(s.name)
            if tick and tick.bid > 0:
                print(f"{s.name}: {tick.bid}")
                available_count += 1
                if available_count >= 5:  # Mostrar solo 5
                    break
    
    print(f"Total simbolos: {len(symbols)}")
    print(f"Visibles encontrados: {available_count}")
else:
    print("No se encontraron simbolos")

# Verificar posiciones actuales
positions = mt5.positions_get()
if positions:
    print(f"\n=== POSICIONES ACTUALES ({len(positions)}) ===")
    for p in positions:
        side = "BUY" if p.type == 0 else "SELL"
        print(f"Ticket {p.ticket}: {p.symbol} {side} {p.volume} P&L: ${p.profit:.2f}")
else:
    print("\nNo hay posiciones abiertas")

# Diagnostico final
print("\n=== DIAGNOSTICO ===")
if account.login == 197678662:
    print("✓ Conectado a cuenta Exness correcta")
else:
    print(f"! Conectado a cuenta {account.login} (esperaba 197678662)")

if account.trade_allowed and (terminal and terminal.trade_allowed):
    print("✓ Trading habilitado - LISTO PARA OPERAR")
    
    # Test rapido de orden (sin ejecutar)
    print("\n=== TEST DE ORDEN ===")
    if symbols and len([s for s in symbols if s.visible]) > 0:
        test_symbol = None
        for s in symbols:
            if s.visible:
                tick = mt5.symbol_info_tick(s.name)
                if tick:
                    test_symbol = s.name
                    break
        
        if test_symbol:
            print(f"Probando con simbolo: {test_symbol}")
            
            # Preparar orden de prueba (NO EJECUTAR)
            tick = mt5.symbol_info_tick(test_symbol)
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": test_symbol,
                "volume": 0.01,
                "type": mt5.ORDER_TYPE_BUY,
                "price": tick.ask,
                "deviation": 20,
                "magic": 12345,
                "comment": "TEST",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            # Solo verificar que se puede crear la estructura
            print(f"Orden de prueba preparada para {test_symbol}")
            print("✓ Sistema listo para ejecutar ordenes")
        
else:
    print("X Trading deshabilitado")
    if not account.trade_allowed:
        print("  - Cuenta no permite trading")
    if terminal and not terminal.trade_allowed:
        print("  - Terminal tiene auto trading deshabilitado")
        print("  - Habilitar en MT5: Tools -> Options -> Expert Advisors -> Allow automated trading")

mt5.shutdown()
print("\n=== FIN VERIFICACION ===")