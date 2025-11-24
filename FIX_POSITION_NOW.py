#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir posiciones sin SL/TP
"""

import MetaTrader5 as mt5
import time
from datetime import datetime

def fix_positions():
    """Corrige todas las posiciones sin SL/TP"""
    
    print("=" * 60)
    print("     CORRECTOR DE POSICIONES SIN SL/TP")
    print("=" * 60)
    print(f"Hora: {datetime.now()}\n")
    
    # Conectar a MT5
    if not mt5.initialize():
        print("[ERROR] No se pudo conectar a MT5")
        return False
    
    # Obtener info de cuenta
    account_info = mt5.account_info()
    if account_info is None:
        print("[ERROR] No se pudo obtener info de cuenta")
        mt5.shutdown()
        return False
    
    print(f"Cuenta: {account_info.login}")
    print(f"Balance: ${account_info.balance:.2f}")
    print(f"Servidor: {account_info.server}\n")
    
    # Obtener posiciones abiertas
    positions = mt5.positions_get()
    
    if not positions:
        print("[INFO] No hay posiciones abiertas")
        mt5.shutdown()
        return True
    
    print(f"[FOUND] {len(positions)} posiciones encontradas\n")
    
    fixed_count = 0
    
    for pos in positions:
        print(f"Posicion #{pos.ticket}:")
        print(f"  Simbolo: {pos.symbol}")
        print(f"  Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"  Volumen: {pos.volume}")
        print(f"  P&L: ${pos.profit:.2f}")
        
        # Verificar si necesita SL/TP
        needs_fix = False
        if pos.sl == 0:
            print("  [!] Sin Stop Loss")
            needs_fix = True
        if pos.tp == 0:
            print("  [!] Sin Take Profit")
            needs_fix = True
            
        if needs_fix:
            # Obtener info del simbolo
            symbol_info = mt5.symbol_info(pos.symbol)
            if symbol_info is None:
                print(f"  [ERROR] No se pudo obtener info del simbolo")
                continue
                
            # Calcular SL y TP basado en ATR estimado
            price = pos.price_current
            point = symbol_info.point
            
            # Usar 100 puntos como distancia base para GOLD
            if "GOLD" in pos.symbol.upper() or "XAU" in pos.symbol.upper():
                sl_distance = 100  # 100 puntos para GOLD
                tp_distance = 150  # 150 puntos para GOLD
            else:
                sl_distance = 50   # 50 puntos para otros
                tp_distance = 100  # 100 puntos para otros
            
            # Calcular niveles
            if pos.type == 0:  # BUY
                sl_price = price - (sl_distance * point)
                tp_price = price + (tp_distance * point)
            else:  # SELL
                sl_price = price + (sl_distance * point)
                tp_price = price - (tp_distance * point)
            
            # Redondear a los decimales del simbolo
            sl_price = round(sl_price, symbol_info.digits)
            tp_price = round(tp_price, symbol_info.digits)
            
            print(f"  Configurando SL: {sl_price:.5f}")
            print(f"  Configurando TP: {tp_price:.5f}")
            
            # Crear request de modificacion
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": pos.ticket,
                "sl": sl_price,
                "tp": tp_price,
                "magic": 234000,
                "comment": "Fixed by script"
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result is None:
                print(f"  [ERROR] order_send() fallo, no hay resultado")
            elif result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"  [ERROR] Codigo: {result.retcode}")
                if result.comment:
                    print(f"  Comentario: {result.comment}")
            else:
                print(f"  [OK] SL/TP configurados exitosamente!")
                fixed_count += 1
        else:
            print("  [OK] Ya tiene SL y TP configurados")
        
        print()
    
    print("=" * 60)
    print(f"RESUMEN: {fixed_count} posiciones corregidas")
    print("=" * 60)
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    try:
        fix_positions()
        print("\nPresiona Enter para salir...")
        input()
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        print("\nPresiona Enter para salir...")
        input()