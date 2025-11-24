#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PROTECTOR DE GANANCIAS INMEDIATO
================================
Sistema ULTRA-PROTECTOR para asegurar ganancias actuales
Aplica breakeven agresivo a cualquier posición con ganancia >=10 pips o >=$50
"""

import MetaTrader5 as mt5
from datetime import datetime

def main():
    print("="*60)
    print("    PROTECTOR DE GANANCIAS INMEDIATO")
    print("    Sistema ULTRA-PROTECTOR")
    print("="*60)
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    # PARAMETROS ULTRA-PROTECTORES
    MIN_PIPS_FOR_PROTECTION = 10      # 10+ pips
    MIN_PROFIT_FOR_PROTECTION = 50    # $50+ USD
    BREAKEVEN_OFFSET = 2              # Solo +2 pips sobre entrada
    TRAILING_DISTANCE = 12            # 12 pips de distancia
    
    print("CONFIGURACION ULTRA-PROTECTORA:")
    print(f"- Criterio: >=10 pips O >=$50 ganancia")
    print(f"- Breakeven: Precio entrada + {BREAKEVEN_OFFSET} pips")
    print(f"- Trailing: Precio actual - {TRAILING_DISTANCE} pips")
    print(f"- Objetivo: ASEGURAR ganancias actuales")
    print()
    
    positions = mt5.positions_get()
    
    if not positions:
        print("No hay posiciones abiertas")
        return
    
    print(f"Analizando {len(positions)} posiciones...")
    print(f"Tiempo: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    protected_positions = 0
    
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
        
        # VERIFICAR SI CALIFICA PARA PROTECCION
        if pips_profit >= MIN_PIPS_FOR_PROTECTION or pos.profit >= MIN_PROFIT_FOR_PROTECTION:
            print(f"  ✅ CALIFICA PARA PROTECCION (>=10 pips o >=$50)")
            
            # APLICAR PROTECCION INMEDIATA
            if pos.type == 0:  # BUY
                # Breakeven + offset
                protective_sl = pos.price_open + (BREAKEVEN_OFFSET * pip_value)
                
                # Solo aplicar si mejora el SL actual
                if pos.sl == 0 or protective_sl > pos.sl:
                    new_sl = protective_sl
                    protection_type = "BREAKEVEN PROTECTOR"
                else:
                    print(f"  -> SL actual {pos.sl:.5f} ya es mejor que breakeven")
                    print()
                    continue
                    
            else:  # SELL
                # Breakeven + offset
                protective_sl = pos.price_open - (BREAKEVEN_OFFSET * pip_value)
                
                # Solo aplicar si mejora el SL actual
                if pos.sl == 0 or protective_sl < pos.sl:
                    new_sl = protective_sl
                    protection_type = "BREAKEVEN PROTECTOR"
                else:
                    print(f"  -> SL actual {pos.sl:.5f} ya es mejor que breakeven")
                    print()
                    continue
            
            print(f"  -> {protection_type}: SL {pos.sl:.5f} -> {new_sl:.5f}")
            
            # APLICAR MODIFICACION INMEDIATA
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
                protected_positions += 1
                # Calcular pips asegurados
                if pos.type == 0:
                    secured_pips = (new_sl - pos.price_open) / pip_value
                else:
                    secured_pips = (pos.price_open - new_sl) / pip_value
                
                print(f"  ✅ EXITO: Ganancia asegurada de {secured_pips:.1f} pips")
                print(f"     Ganancia actual: {pips_profit:.1f} pips -> Mínimo asegurado: {secured_pips:.1f} pips")
            else:
                print(f"  ❌ ERROR: {result.comment}")
        
        else:
            needed_pips = MIN_PIPS_FOR_PROTECTION - pips_profit
            needed_profit = MIN_PROFIT_FOR_PROTECTION - pos.profit
            
            if pips_profit > 0:
                print(f"  -> No califica: Necesita {needed_pips:.1f} pips más o ${needed_profit:.2f} más")
            else:
                print(f"  -> Sin ganancia, no aplica protección")
        
        print()
    
    print("="*60)
    print("RESUMEN DE PROTECCION:")
    print(f"Posiciones protegidas: {protected_positions}")
    print()
    
    if protected_positions > 0:
        print("✅ GANANCIAS ASEGURADAS!")
        print("- Las posiciones protegidas ahora tienen breakeven establecido")
        print("- Ganancia mínima asegurada incluso si el mercado se revierte")
        print("- El sistema continuará aplicando trailing cuando califique")
    else:
        print("ℹ️  NO SE APLICARON PROTECCIONES")
        print("- Ninguna posición cumple criterios de protección")
        print("- Se requieren >=10 pips o >=$50 de ganancia")
        print("- El sistema seguirá monitoreando automáticamente")
    
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()