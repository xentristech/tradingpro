#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SMART BREAKEVEN Y TRAILING - OPTIMIZADO CON TELEGRAM
===================================================
Sistema inteligente con parametros agresivos y notificaciones
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

from src.utils.smart_trailing_system import smart_trailing

def main():
    print("=" * 60)
    print("  SMART BREAKEVEN Y TRAILING - OPTIMIZADO")
    print("=" * 60)
    print()
    
    print("CONFIGURACION NUEVA (MAS AGRESIVA):")
    print(f"- Breakeven MANUAL: {smart_trailing.BREAKEVEN_TRIGGER} pips -> +{smart_trailing.BREAKEVEN_OFFSET} pips")
    print(f"- Trailing AUTOMATICO: {smart_trailing.TRAILING_TRIGGER} pips -> {smart_trailing.TRAILING_DISTANCE} pips distancia")
    print()
    
    print("PARAMETROS POR SIMBOLO:")
    for symbol, params in smart_trailing.SYMBOL_PARAMS.items():
        be = params['breakeven_trigger']
        tr = params['trailing_trigger']
        dist = params['trailing_distance']
        print(f"- {symbol}: BE={be}p | TR={tr}p | DIST={dist}p")
    print()
    
    # Estado actual
    positions = smart_trailing.get_position_status()
    
    if not positions:
        print("No hay posiciones abiertas")
        return
    
    print(f"ESTADO ACTUAL: {len(positions)} posiciones")
    print("-" * 40)
    
    for pos in positions:
        be_ready = "LISTO" if pos['breakeven_ready'] else "NO LISTO"
        tr_ready = "LISTO" if pos['trailing_ready'] else "NO LISTO"
        be_applied = " [APLICADO]" if pos['breakeven_applied'] else ""
        
        print(f"{pos['symbol']} #{pos['ticket']} ({pos['type']})")
        print(f"  Ganancia: {pos['pips_profit']} pips | ${pos['profit_usd']:.2f}")
        print(f"  Breakeven: {be_ready}{be_applied}")
        print(f"  Trailing: {tr_ready}")
        print(f"  SL: {pos['current_sl']} | TP: {pos['current_tp']}")
        print()
    
    # Aplicar
    input("Presiona ENTER para APLICAR BREAKEVEN Y TRAILING...")
    print()
    print("Aplicando sistema inteligente...")
    
    results = smart_trailing.process_all_positions()
    
    print("=" * 40)
    print("RESULTADOS:")
    print(f"Total posiciones: {results.get('total_positions', 0)}")
    print(f"Breakeven aplicados: {results.get('breakeven_applied', 0)}")  
    print(f"Trailing aplicados: {results.get('trailing_applied', 0)}")
    print(f"Sin cambios: {results.get('skipped', 0)}")
    
    if results.get('breakeven_applied', 0) > 0:
        print()
        print("BREAKEVEN aplicado - Alerta enviada a Telegram")
        
    if results.get('trailing_applied', 0) > 0:
        print()
        print("TRAILING ajustado - Alerta enviada a Telegram")
    
    print()
    print("Proceso completado - Revisa Telegram para confirmaciones")

if __name__ == "__main__":
    main()