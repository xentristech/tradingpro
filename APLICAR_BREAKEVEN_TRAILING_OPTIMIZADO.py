#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APLICAR BREAKEVEN Y TRAILING - VERSIÓN OPTIMIZADA
================================================
Sistema mejorado con parámetros más agresivos y alertas Telegram
- BREAKEVEN: 15 pips (manual con alerta)
- TRAILING: 20 pips automático (era 40)
"""

import sys
from pathlib import Path

# Agregar src al path
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

from src.utils.smart_trailing_system import smart_trailing

def main():
    print("=" * 70)
    print("    BREAKEVEN Y TRAILING OPTIMIZADO CON TELEGRAM")
    print("=" * 70)
    print()
    
    print("CONFIGURACIÓN NUEVA (MÁS AGRESIVA):")
    print(f"• Breakeven MANUAL: {smart_trailing.BREAKEVEN_TRIGGER} pips → +{smart_trailing.BREAKEVEN_OFFSET} pips")
    print(f"• Trailing AUTOMÁTICO: {smart_trailing.TRAILING_TRIGGER} pips → {smart_trailing.TRAILING_DISTANCE} pips distancia")
    print()
    
    print("PARÁMETROS ESPECIALES POR SÍMBOLO:")
    for symbol, params in smart_trailing.SYMBOL_PARAMS.items():
        be = params['breakeven_trigger']
        tr = params['trailing_trigger']
        dist = params['trailing_distance']
        print(f"• {symbol}: Breakeven {be}p | Trailing {tr}p (distancia {dist}p)")
    print()
    
    # Obtener estado actual
    positions_status = smart_trailing.get_position_status()
    
    if not positions_status:
        print("❌ No hay posiciones abiertas")
        return
    
    print(f"📊 ESTADO ACTUAL: {len(positions_status)} posiciones")
    print("-" * 50)
    
    for pos in positions_status:
        be_status = "✅ LISTO" if pos['breakeven_ready'] else "⏳ NO LISTO"
        tr_status = "✅ LISTO" if pos['trailing_ready'] else "⏳ NO LISTO"
        be_applied_status = " [🛡️ YA APLICADO]" if pos['breakeven_applied'] else ""
        
        print(f"📈 {pos['symbol']} #{pos['ticket']} ({pos['type']})")
        print(f"   💰 Ganancia: {pos['pips_profit']} pips | ${pos['profit_usd']:.2f}")
        print(f"   🛡️ Breakeven: {be_status}{be_applied_status}")
        print(f"   🔄 Trailing: {tr_status}")
        print(f"   📍 SL actual: {pos['current_sl']} | TP: {pos['current_tp']}")
        print()
    
    # Aplicar sistema
    input("Presiona ENTER para aplicar BREAKEVEN MANUAL y TRAILING AUTOMÁTICO...")
    print()
    print("🚀 APLICANDO SISTEMA INTELIGENTE...")
    
    results = smart_trailing.process_all_positions()
    
    print("=" * 50)
    print("📋 RESULTADOS:")
    print(f"• Total posiciones: {results.get('total_positions', 0)}")
    print(f"• Breakeven aplicados: {results.get('breakeven_applied', 0)}")  
    print(f"• Trailing aplicados: {results.get('trailing_applied', 0)}")
    print(f"• Sin cambios: {results.get('skipped', 0)}")
    
    if results.get('breakeven_applied', 0) > 0:
        print()
        print("🛡️ BREAKEVEN aplicado - Notificación enviada a Telegram")
        
    if results.get('trailing_applied', 0) > 0:
        print()
        print("🔄 TRAILING STOP ajustado - Notificación enviada a Telegram")
    
    print()
    print("✅ Proceso completado - Revisa tu Telegram para confirmaciones")

if __name__ == "__main__":
    main()