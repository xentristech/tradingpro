#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de debug para el sistema de monitoreo de posiciones
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.signals.advanced_signal_generator import SignalGenerator

def test_monitor_debug():
    """Prueba la función de monitoreo con debug detallado"""
    
    # Crear generador con auto_execute para que tenga conexión MT5
    generator = SignalGenerator(auto_execute=True)
    
    print("=== TEST MONITOR DEBUG ===")
    print(f"MT5 Connection: {generator.mt5_connection is not None}")
    print(f"Auto Execute: {generator.auto_execute}")
    
    if generator.mt5_connection:
        print(f"MT5 Connected: {generator.mt5_connection.connected}")
        
        # Llamar directamente a la función monitor
        print("\\nEjecutando monitor_and_correct_positions()...")
        corrected = generator.monitor_and_correct_positions()
        print(f"Posiciones corregidas: {corrected}")
        
        # Ver posiciones directamente
        print("\\n=== POSICIONES DIRECTAS ===")
        positions = generator.mt5_connection.get_positions()
        print(f"Total posiciones: {len(positions)}")
        
        for i, pos in enumerate(positions, 1):
            print(f"Posición {i}:")
            print(f"  Ticket: {pos.ticket}")
            print(f"  Symbol: {pos.symbol}")
            print(f"  Type: {pos.type} ({'BUY' if pos.type == 0 else 'SELL'})")
            print(f"  Volume: {pos.volume}")
            print(f"  Price Open: {pos.price_open}")
            print(f"  SL: {pos.sl} {'(FALTA)' if pos.sl == 0.0 else '(OK)'}")
            print(f"  TP: {pos.tp} {'(FALTA)' if pos.tp == 0.0 else '(OK)'}")
            print(f"  Needs correction: {pos.sl == 0.0 or pos.tp == 0.0}")
            print()
    else:
        print("ERROR: No hay conexión MT5")

if __name__ == "__main__":
    test_monitor_debug()