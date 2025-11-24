#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APLICAR BREAKEVEN Y TRAILING STOP - VERSION RAPIDA
==================================================
Aplica breakeven y trailing stop a posiciones que califican
"""

import MetaTrader5 as mt5
from datetime import datetime

def main():
    print("="*60)
    print("    BREAKEVEN Y TRAILING STOP - APLICACION RAPIDA")
    print("="*60)
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    # Configuración mejorada
    BREAKEVEN_TRIGGER = 12  # Reducido para ser más agresivo
    BREAKEVEN_OFFSET = 2
    TRAILING_TRIGGER = 20   # Reducido para ser más agresivo
    TRAILING_DISTANCE = 10  # Reducido para seguir más cerca
    
    positions = mt5.positions_get()
    
    if not positions:
        print("No hay posiciones abiertas")
        return
    
    print(f"Analizando {len(positions)} posiciones...")
    print(f"Tiempo: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    breakeven_applied = 0
    trailing_applied = 0
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        
        # Calcular pips de ganancia
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
        
        current_price = tick.bid if pos.type == 0 else tick.ask
        
        # Determinar valor de pip
        if symbol.startswith(('EUR', 'GBP', 'AUD', 'NZD')):
            pip_value = 0.0001
        elif 'JPY' in symbol:
            pip_value = 0.01
        else:
            pip_value = 1.0
        
        # Calcular pips de ganancia
        if pos.type == 0:  # BUY
            pips_profit = (current_price - pos.price_open) / pip_value
        else:  # SELL
            pips_profit = (pos.price_open - current_price) / pip_value
        
        print(f"--- {symbol} #{ticket} ---")
        print(f"Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"Ganancia: {pips_profit:.1f} pips (${pos.profit:.2f})")
        
        if pips_profit <= 0:
            print("  -> Sin ganancia, saltando")
            print()
            continue
        
        new_sl = pos.sl
        action_taken = False
        
        # APLICAR BREAKEVEN
        if pips_profit >= BREAKEVEN_TRIGGER:
            if pos.type == 0:  # BUY
                breakeven_sl = pos.price_open + (BREAKEVEN_OFFSET * pip_value)
                if pos.sl == 0 or breakeven_sl > pos.sl:
                    new_sl = breakeven_sl
                    action_taken = True
                    print(f"  -> BREAKEVEN: SL -> {new_sl:.5f}")
            else:  # SELL
                breakeven_sl = pos.price_open - (BREAKEVEN_OFFSET * pip_value)
                if pos.sl == 0 or breakeven_sl < pos.sl:
                    new_sl = breakeven_sl
                    action_taken = True
                    print(f"  -> BREAKEVEN: SL -> {new_sl:.5f}")
        
        # APLICAR TRAILING STOP
        if pips_profit >= TRAILING_TRIGGER:
            if pos.type == 0:  # BUY
                trailing_sl = current_price - (TRAILING_DISTANCE * pip_value)
                if new_sl == 0 or trailing_sl > new_sl:
                    new_sl = trailing_sl
                    action_taken = True
                    print(f"  -> TRAILING: SL -> {new_sl:.5f}")
            else:  # SELL
                trailing_sl = current_price + (TRAILING_DISTANCE * pip_value)
                if new_sl == 0 or trailing_sl < new_sl:
                    new_sl = trailing_sl
                    action_taken = True
                    print(f"  -> TRAILING: SL -> {new_sl:.5f}")
        
        # APLICAR MODIFICACION SI HAY CAMBIOS
        if action_taken and new_sl != pos.sl:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": pos.tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                if pips_profit >= TRAILING_TRIGGER:
                    trailing_applied += 1
                    print(f"  -> EXITO: Trailing aplicado")
                else:
                    breakeven_applied += 1
                    print(f"  -> EXITO: Breakeven aplicado")
            else:
                print(f"  -> ERROR: {result.comment}")
        
        if not action_taken:
            if pips_profit < BREAKEVEN_TRIGGER:
                needed = BREAKEVEN_TRIGGER - pips_profit
                print(f"  -> Necesita {needed:.1f} pips mas para breakeven")
            else:
                print(f"  -> Ya optimizada")
        
        print()
    
    print("="*60)
    print("RESUMEN:")
    print(f"Breakeven aplicados: {breakeven_applied}")
    print(f"Trailing aplicados: {trailing_applied}")
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()