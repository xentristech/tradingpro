#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificar estado actual de posiciones
"""
import MetaTrader5 as mt5
from datetime import datetime

def main():
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    print("="*60)
    print("    ESTADO ACTUAL DE POSICIONES")
    print("="*60)
    print(f"Tiempo: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    positions = mt5.positions_get()
    
    if not positions:
        print("No hay posiciones abiertas")
        return
    
    print(f"Total posiciones: {len(positions)}")
    print()
    
    for i, pos in enumerate(positions, 1):
        symbol = pos.symbol
        ticket = pos.ticket
        
        # Calcular pips de ganancia
        tick = mt5.symbol_info_tick(symbol)
        if tick:
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
        else:
            pips_profit = 0
            current_price = 0
        
        print(f"[{i}] {symbol} #{ticket}")
        print(f"    Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"    Entry: {pos.price_open:.5f}")
        print(f"    Actual: {current_price:.5f}")
        print(f"    SL: {pos.sl:.5f}" if pos.sl > 0 else "    SL: No establecido")
        print(f"    TP: {pos.tp:.5f}" if pos.tp > 0 else "    TP: No establecido")
        print(f"    Profit: ${pos.profit:.2f} ({pips_profit:.1f} pips)")
        print()
    
    # Verificar estado para breakeven/trailing
    print("ANALISIS PARA BREAKEVEN/TRAILING CONSERVADOR:")
    print("- Breakeven: 25 pips -> +5 pips")
    print("- Trailing: 40 pips -> 20 pips distancia")
    print()
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
            
        current_price = tick.bid if pos.type == 0 else tick.ask
        
        if symbol.startswith(('EUR', 'GBP', 'AUD', 'NZD')):
            pip_value = 0.0001
        elif 'JPY' in symbol:
            pip_value = 0.01
        else:
            pip_value = 1.0
        
        if pos.type == 0:  # BUY
            pips_profit = (current_price - pos.price_open) / pip_value
        else:  # SELL
            pips_profit = (pos.price_open - current_price) / pip_value
        
        print(f"{symbol} #{ticket}: {pips_profit:.1f} pips", end="")
        
        if pips_profit >= 40:
            print(" -> CALIFICA TRAILING")
        elif pips_profit >= 25:
            print(" -> CALIFICA BREAKEVEN")
        elif pips_profit > 0:
            needed_be = 25 - pips_profit
            needed_tr = 40 - pips_profit
            print(f" -> Necesita {needed_be:.1f} para breakeven, {needed_tr:.1f} para trailing")
        else:
            print(" -> En perdida")
    
    print()
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()