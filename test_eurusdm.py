#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prueba rápida EURUSDm
"""
import MetaTrader5 as mt5

def test_eurusdm():
    """Prueba EURUSDm"""
    
    if not mt5.initialize():
        print("Error MT5")
        return
    
    # Probar EURUSDm
    symbol_info = mt5.symbol_info("EURUSDm")
    if symbol_info:
        print(f"[OK] EURUSDm: Spread {symbol_info.spread}")
        
        tick = mt5.symbol_info_tick("EURUSDm")
        if tick:
            print(f"[OK] Bid: {tick.bid}, Ask: {tick.ask}")
        else:
            print("[ERROR] No tick")
    else:
        print("[ERROR] EURUSDm no disponible")

if __name__ == "__main__":
    test_eurusdm()