#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APLICAR BREAKEVEN Y TRAILING CONSERVADOR - ANTI-OSCILACIONES
============================================================
Aplica breakeven y trailing con parametros conservadores para mercados volatiles
"""

import MetaTrader5 as mt5
from datetime import datetime

def main():
    print("="*70)
    print("    BREAKEVEN Y TRAILING CONSERVADOR - ANTI-OSCILACIONES")
    print("="*70)
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    # CONFIGURACION CONSERVADORA
    BREAKEVEN_TRIGGER = 25   # Mayor trigger (era 12-15)
    BREAKEVEN_OFFSET = 5     # Mayor offset (era 2)
    TRAILING_TRIGGER = 40    # Mucho mayor (era 20-25) 
    TRAILING_DISTANCE = 20   # Mayor distancia (era 10-12)
    
    print("PARAMETROS CONSERVADORES:")
    print(f"- Breakeven: {BREAKEVEN_TRIGGER} pips -> +{BREAKEVEN_OFFSET} pips")
    print(f"- Trailing: {TRAILING_TRIGGER} pips -> {TRAILING_DISTANCE} pips distancia")
    print("- Diseñado para mercados con oscilaciones")
    print()
    
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
        
        # APLICAR BREAKEVEN CONSERVADOR
        if pips_profit >= BREAKEVEN_TRIGGER:
            if pos.type == 0:  # BUY
                breakeven_sl = pos.price_open + (BREAKEVEN_OFFSET * pip_value)
                if pos.sl == 0 or breakeven_sl > pos.sl:
                    new_sl = breakeven_sl
                    action_taken = True
                    print(f"  -> BREAKEVEN CONSERVADOR: SL -> {new_sl:.5f}")
            else:  # SELL
                breakeven_sl = pos.price_open - (BREAKEVEN_OFFSET * pip_value)
                if pos.sl == 0 or breakeven_sl < pos.sl:
                    new_sl = breakeven_sl
                    action_taken = True
                    print(f"  -> BREAKEVEN CONSERVADOR: SL -> {new_sl:.5f}")
        
        # APLICAR TRAILING CONSERVADOR
        if pips_profit >= TRAILING_TRIGGER:
            if pos.type == 0:  # BUY
                trailing_sl = current_price - (TRAILING_DISTANCE * pip_value)
                if new_sl == 0 or trailing_sl > new_sl:
                    new_sl = trailing_sl
                    action_taken = True
                    print(f"  -> TRAILING CONSERVADOR: SL -> {new_sl:.5f}")
            else:  # SELL
                trailing_sl = current_price + (TRAILING_DISTANCE * pip_value)
                if new_sl == 0 or trailing_sl < new_sl:
                    new_sl = trailing_sl
                    action_taken = True
                    print(f"  -> TRAILING CONSERVADOR: SL -> {new_sl:.5f}")
        
        # APLICAR MODIFICACION SI HAY CAMBIOS
        if action_taken and new_sl != pos.sl:
            # Verificar que el cambio es significativo (minimo 5 pips)
            min_change = 5 * pip_value
            if pos.sl != 0:
                if pos.type == 0 and (new_sl - pos.sl) < min_change:
                    print("  -> Cambio muy pequeño, omitiendo")
                    print()
                    continue
                elif pos.type == 1 and (pos.sl - new_sl) < min_change:
                    print("  -> Cambio muy pequeño, omitiendo")
                    print()
                    continue
            
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
                    print(f"  -> EXITO: Trailing conservador aplicado")
                else:
                    breakeven_applied += 1
                    print(f"  -> EXITO: Breakeven conservador aplicado")
            else:
                print(f"  -> ERROR: {result.comment}")
        
        if not action_taken:
            if pips_profit < BREAKEVEN_TRIGGER:
                needed = BREAKEVEN_TRIGGER - pips_profit
                print(f"  -> Necesita {needed:.1f} pips mas para breakeven conservador")
            elif pips_profit < TRAILING_TRIGGER:
                needed = TRAILING_TRIGGER - pips_profit
                print(f"  -> Necesita {needed:.1f} pips mas para trailing conservador")
            else:
                print(f"  -> Ya optimizada con parametros conservadores")
        
        print()
    
    print("="*70)
    print("RESUMEN:")
    print(f"Breakeven conservador aplicados: {breakeven_applied}")
    print(f"Trailing conservador aplicados: {trailing_applied}")
    print("NOTA: Parametros diseñados para resistir oscilaciones del mercado")
    print("="*70)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()