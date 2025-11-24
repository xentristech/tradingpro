#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST DEL DIRECTOR DE OPERACIONES
===============================
Prueba el Director con posiciones reales
"""

import sys
from pathlib import Path
import MetaTrader5 as mt5

# Agregar src al path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_director():
    print("PRUEBA DEL DIRECTOR DE OPERACIONES")
    print("=" * 50)
    
    # Inicializar MT5
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    try:
        from src.director.operations_director import OperationsDirector
        
        # Crear Director
        print("Inicializando Director...")
        director = OperationsDirector()
        
        # Obtener posiciones actuales
        positions = mt5.positions_get()
        print(f"Posiciones encontradas: {len(positions) if positions else 0}")
        
        if positions:
            for pos in positions:
                profit_pips = 0
                if pos.type == 0:  # BUY
                    if 'EUR' in pos.symbol:
                        profit_pips = (pos.price_current - pos.price_open) * 10000
                    elif 'XAU' in pos.symbol:
                        profit_pips = (pos.price_current - pos.price_open) * 10
                else:  # SELL
                    if 'EUR' in pos.symbol:
                        profit_pips = (pos.price_open - pos.price_current) * 10000
                    elif 'XAU' in pos.symbol:
                        profit_pips = (pos.price_open - pos.price_current) * 10
                        
                print(f"  {pos.symbol} #{pos.ticket}: {profit_pips:.1f} pips | ${pos.profit:.2f}")
        
        print()
        print("Ejecutando analisis del Director...")
        
        # Test del Director
        result = director.analyze_single_cycle()
        
        print("RESULTADO DEL DIRECTOR:")
        if result:
            for key, value in result.items():
                if key == 'adjustments_details':
                    print(f"  {key}: {len(value)} ajustes")
                    for adj in value:
                        print(f"    - {adj}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("  No se obtuvo resultado del Director")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    test_director()