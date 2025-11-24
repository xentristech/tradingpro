#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificar símbolos EURUSD disponibles en MT5
"""
import MetaTrader5 as mt5

def check_eurusd_symbols():
    """Busca símbolos EUR/USD disponibles"""
    
    print("=== VERIFICANDO SIMBOLOS EURUSD EN MT5 ===")
    
    # Inicializar MT5
    if not mt5.initialize():
        print("Error inicializando MT5")
        return
    
    try:
        # Buscar todos los símbolos que contienen EUR
        print("\n1. Símbolos que contienen 'EUR':")
        eur_symbols = mt5.symbols_get("*EUR*")
        if eur_symbols:
            for symbol in eur_symbols[:10]:  # Primeros 10
                print(f"   {symbol.name}: {symbol.description}")
        else:
            print("   No se encontraron símbolos con EUR")
        
        # Buscar variantes específicas de EURUSD
        print("\n2. Probando variantes específicas:")
        variants = ['EURUSD', 'EURUSDm', 'EURUSD.m', 'EURUSD-m', 'EURUSDmic', 'EURUSD_m']
        
        for variant in variants:
            symbol_info = mt5.symbol_info(variant)
            if symbol_info:
                print(f"   ✅ {variant}: DISPONIBLE - Spread: {symbol_info.spread}")
                
                # Probar obtener tick
                tick = mt5.symbol_info_tick(variant)
                if tick:
                    print(f"      Bid: {tick.bid}, Ask: {tick.ask}")
                else:
                    print(f"      No se pudo obtener tick")
            else:
                print(f"   ❌ {variant}: NO DISPONIBLE")
        
        # Buscar símbolos que contienen USD
        print("\n3. Símbolos principales con USD:")
        usd_symbols = mt5.symbols_get("*USD*")
        if usd_symbols:
            for symbol in usd_symbols[:15]:  # Primeros 15
                if 'EUR' in symbol.name.upper():
                    print(f"   🎯 {symbol.name}: {symbol.description}")
    
    finally:
        # No cerramos MT5
        pass

if __name__ == "__main__":
    check_eurusd_symbols()