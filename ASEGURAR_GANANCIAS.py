#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ASEGURAR GANANCIAS
==================
Sistema para asegurar ganancias inmediatamente
"""

import MetaTrader5 as mt5
from datetime import datetime

def main():
    print("="*60)
    print("    ASEGURADOR DE GANANCIAS INMEDIATO")
    print("="*60)
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    # PARAMETROS PROTECTORES
    MIN_PIPS_FOR_PROTECTION = 10
    MIN_PROFIT_FOR_PROTECTION = 50
    BREAKEVEN_OFFSET = 2
    
    print("CONFIGURACION:")
    print(f"- Proteger si: >=10 pips O >=$50")
    print(f"- Breakeven: Entrada + {BREAKEVEN_OFFSET} pips")
    print()
    
    positions = mt5.positions_get()
    
    if not positions:
        print("No hay posiciones abiertas")
        return
    
    print(f"Analizando {len(positions)} posiciones...")
    print()
    
    protected = 0
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        
        # Obtener precio actual
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
        
        current_price = tick.bid if pos.type == 0 else tick.ask
        
        # Valor de pip
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
        print(f"Ganancia: {pips_profit:.1f} pips (${pos.profit:.2f})")
        
        # Verificar si califica
        if pips_profit >= MIN_PIPS_FOR_PROTECTION or pos.profit >= MIN_PROFIT_FOR_PROTECTION:
            print(f"  >> CALIFICA PARA PROTECCION")
            
            # Calcular nuevo SL protector
            if pos.type == 0:  # BUY
                new_sl = pos.price_open + (BREAKEVEN_OFFSET * pip_value)
                if pos.sl != 0 and new_sl <= pos.sl:
                    print(f"  -> SL actual ya es mejor")
                    print()
                    continue
            else:  # SELL
                new_sl = pos.price_open - (BREAKEVEN_OFFSET * pip_value)
                if pos.sl != 0 and new_sl >= pos.sl:
                    print(f"  -> SL actual ya es mejor")
                    print()
                    continue
            
            print(f"  -> SL: {pos.sl:.5f} -> {new_sl:.5f}")
            
            # Aplicar
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
                protected += 1
                if pos.type == 0:
                    secured = (new_sl - pos.price_open) / pip_value
                else:
                    secured = (pos.price_open - new_sl) / pip_value
                
                print(f"  >> EXITO: {secured:.1f} pips asegurados")
            else:
                print(f"  >> ERROR: {result.comment}")
        else:
            print(f"  -> No califica (necesita mas ganancia)")
        
        print()
    
    print("="*60)
    print(f"POSICIONES PROTEGIDAS: {protected}")
    
    if protected > 0:
        print("GANANCIAS ASEGURADAS!")
    else:
        print("NO SE APLICARON PROTECCIONES")
    
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()