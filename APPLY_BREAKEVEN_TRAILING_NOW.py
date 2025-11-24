#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APLICAR BREAKEVEN Y TRAILING STOP INMEDIATAMENTE
===============================================
Aplica breakeven y trailing stop a posiciones que califican
"""

import MetaTrader5 as mt5
import time
from datetime import datetime

def main():
    print("="*60)
    print("    APLICANDO BREAKEVEN Y TRAILING STOP")
    print("="*60)
    print(f"Tiempo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Conectar MT5
    if not mt5.initialize():
        print("Error: No se pudo conectar a MT5")
        return
    
    print("MT5 conectado exitosamente")
    
    # Obtener posiciones
    positions = mt5.positions_get()
    
    if not positions:
        print("No hay posiciones abiertas")
        return
    
    print(f"Analizando {len(positions)} posiciones...")
    print()
    
    # Configuración
    BREAKEVEN_TRIGGER_PIPS = 20
    BREAKEVEN_OFFSET_PIPS = 2
    TRAILING_TRIGGER_PIPS = 30
    TRAILING_DISTANCE_PIPS = 15
    
    for position in positions:
        symbol = position.symbol
        ticket = position.ticket
        entry_price = position.price_open
        position_type = position.type  # 0 = BUY, 1 = SELL
        current_sl = position.sl
        current_tp = position.tp
        
        print(f"--- {symbol} #{ticket} ---")
        print(f"Tipo: {'BUY' if position_type == 0 else 'SELL'}")
        print(f"Entrada: {entry_price:.5f}")
        print(f"SL Actual: {current_sl:.5f}")
        print(f"TP Actual: {current_tp:.5f}")
        
        # Obtener precio actual
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"Error: No se pudo obtener precio actual para {symbol}")
            continue
        
        current_price = tick.bid if position_type == 0 else tick.ask
        print(f"Precio Actual: {current_price:.5f}")
        
        # Calcular pips de ganancia/pérdida
        if symbol.startswith(('EUR', 'GBP', 'AUD', 'NZD')):
            # Pares forex con 4 decimales
            pip_multiplier = 10000
        else:
            # Oro, crypto, índices
            pip_multiplier = 1
        
        if position_type == 0:  # BUY
            pips_diff = (current_price - entry_price) * pip_multiplier
        else:  # SELL  
            pips_diff = (entry_price - current_price) * pip_multiplier
        
        print(f"Pips de ganancia: {pips_diff:.1f}")
        
        new_sl = current_sl
        new_tp = current_tp
        action_taken = False
        
        # APLICAR BREAKEVEN
        if pips_diff >= BREAKEVEN_TRIGGER_PIPS:
            if position_type == 0:  # BUY
                breakeven_sl = entry_price + (BREAKEVEN_OFFSET_PIPS / pip_multiplier)
            else:  # SELL
                breakeven_sl = entry_price - (BREAKEVEN_OFFSET_PIPS / pip_multiplier)
            
            # Solo aplicar si el nuevo SL es mejor que el actual
            if position_type == 0:  # BUY
                if current_sl == 0 or breakeven_sl > current_sl:
                    new_sl = breakeven_sl
                    print(f"✅ BREAKEVEN aplicado: SL -> {new_sl:.5f}")
                    action_taken = True
            else:  # SELL
                if current_sl == 0 or breakeven_sl < current_sl:
                    new_sl = breakeven_sl  
                    print(f"✅ BREAKEVEN aplicado: SL -> {new_sl:.5f}")
                    action_taken = True
        
        # APLICAR TRAILING STOP
        if pips_diff >= TRAILING_TRIGGER_PIPS:
            if position_type == 0:  # BUY
                trailing_sl = current_price - (TRAILING_DISTANCE_PIPS / pip_multiplier)
            else:  # SELL
                trailing_sl = current_price + (TRAILING_DISTANCE_PIPS / pip_multiplier)
            
            # Solo aplicar si el trailing SL es mejor que el actual
            if position_type == 0:  # BUY
                if new_sl == 0 or trailing_sl > new_sl:
                    new_sl = trailing_sl
                    print(f"✅ TRAILING STOP aplicado: SL -> {new_sl:.5f}")
                    action_taken = True
            else:  # SELL
                if new_sl == 0 or trailing_sl < new_sl:
                    new_sl = trailing_sl
                    print(f"✅ TRAILING STOP aplicado: SL -> {new_sl:.5f}")
                    action_taken = True
        
        if not action_taken:
            if pips_diff < BREAKEVEN_TRIGGER_PIPS:
                print(f"⏳ Necesita {BREAKEVEN_TRIGGER_PIPS - pips_diff:.1f} pips más para breakeven")
            else:
                print(f"✅ Posición ya optimizada")
        
        # Modificar posición si hay cambios
        if action_taken and new_sl != current_sl:
            print(f"Modificando posición...")
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": current_tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ ÉXITO: Posición modificada")
                print(f"   SL: {current_sl:.5f} -> {new_sl:.5f}")
            else:
                print(f"❌ ERROR: {result.retcode} - {result.comment}")
        
        print()
    
    print("="*60)
    print("PROCESO COMPLETADO")
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()