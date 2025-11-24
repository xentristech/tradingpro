#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APLICAR TRAILING HIBRIDO INMEDIATAMENTE
=======================================
Aplica sistema híbrido para proteger ganancias actuales
"""

import MetaTrader5 as mt5
from datetime import datetime

def main():
    print("="*60)
    print("    APLICANDO TRAILING HÍBRIDO INMEDIATAMENTE")
    print("="*60)
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    # PARAMETROS HIBRIDOS
    CONSERVATIVE_BREAKEVEN = 25  # Para nuevas activaciones
    PROTECTIVE_BREAKEVEN = 15    # Para posiciones ya ganadoras
    
    CONSERVATIVE_TRAILING = 40   # Para nuevas activaciones  
    PROTECTIVE_TRAILING = 20     # Para posiciones ya ganadoras
    
    BREAKEVEN_OFFSET = 3
    TRAILING_DISTANCE = 15
    
    print("CONFIGURACION HIBRIDA:")
    print(f"- Modo CONSERVADOR: Breakeven {CONSERVATIVE_BREAKEVEN} pips, Trailing {CONSERVATIVE_TRAILING} pips")
    print(f"- Modo PROTECTOR: Breakeven {PROTECTIVE_BREAKEVEN} pips, Trailing {PROTECTIVE_TRAILING} pips")
    print(f"- Criterio protector: >=10 pips o >=$50 ganancia")
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
        
        # DETERMINAR MODO (PROTECTOR vs CONSERVADOR)
        if pips_profit >= 10 or pos.profit >= 50:
            mode = "PROTECTOR"
            breakeven_trigger = PROTECTIVE_BREAKEVEN
            trailing_trigger = PROTECTIVE_TRAILING
            print(f"  -> MODO: {mode} (>=10 pips o >=$50)")
        else:
            mode = "CONSERVADOR"
            breakeven_trigger = CONSERVATIVE_BREAKEVEN
            trailing_trigger = CONSERVATIVE_TRAILING
            print(f"  -> MODO: {mode} (nueva posición)")
        
        new_sl = pos.sl
        action_taken = False
        
        # APLICAR BREAKEVEN SEGÚN MODO
        if pips_profit >= breakeven_trigger:
            if pos.type == 0:  # BUY
                breakeven_sl = pos.price_open + (BREAKEVEN_OFFSET * pip_value)
                if pos.sl == 0 or breakeven_sl > pos.sl:
                    new_sl = breakeven_sl
                    action_taken = True
                    print(f"  -> BREAKEVEN {mode}: SL -> {new_sl:.5f}")
            else:  # SELL
                breakeven_sl = pos.price_open - (BREAKEVEN_OFFSET * pip_value)
                if pos.sl == 0 or breakeven_sl < pos.sl:
                    new_sl = breakeven_sl
                    action_taken = True
                    print(f"  -> BREAKEVEN {mode}: SL -> {new_sl:.5f}")
        
        # APLICAR TRAILING SEGÚN MODO
        if pips_profit >= trailing_trigger:
            if pos.type == 0:  # BUY
                trailing_sl = current_price - (TRAILING_DISTANCE * pip_value)
                if new_sl == 0 or trailing_sl > new_sl:
                    new_sl = trailing_sl
                    action_taken = True
                    print(f"  -> TRAILING {mode}: SL -> {new_sl:.5f}")
            else:  # SELL
                trailing_sl = current_price + (TRAILING_DISTANCE * pip_value)
                if new_sl == 0 or trailing_sl < new_sl:
                    new_sl = trailing_sl
                    action_taken = True
                    print(f"  -> TRAILING {mode}: SL -> {new_sl:.5f}")
        
        # APLICAR MODIFICACION SI HAY CAMBIOS
        if action_taken and new_sl != pos.sl:
            # Verificar cambio mínimo de 3 pips
            min_change = 3 * pip_value
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
                if pips_profit >= trailing_trigger:
                    trailing_applied += 1
                    print(f"  -> EXITO: Trailing {mode} aplicado")
                else:
                    breakeven_applied += 1
                    print(f"  -> EXITO: Breakeven {mode} aplicado")
            else:
                print(f"  -> ERROR: {result.comment}")
        
        if not action_taken:
            if pips_profit < breakeven_trigger:
                needed = breakeven_trigger - pips_profit
                print(f"  -> Necesita {needed:.1f} pips mas para breakeven {mode}")
            else:
                print(f"  -> Ya optimizada con parametros {mode}")
        
        print()
    
    print("="*60)
    print("RESUMEN DEL SISTEMA HÍBRIDO:")
    print(f"Breakeven aplicados: {breakeven_applied}")
    print(f"Trailing aplicados: {trailing_applied}")
    print()
    print("VENTAJAS DEL SISTEMA HÍBRIDO:")
    print("- Protege ganancias existentes con parámetros más agresivos")
    print("- Mantiene conservadurismo para nuevas activaciones")
    print("- Adapta automáticamente según el rendimiento de cada posición")
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()