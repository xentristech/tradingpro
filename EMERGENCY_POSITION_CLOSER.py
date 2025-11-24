#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLUCION DE EMERGENCIA - CIERRE DE POSICIONES PROBLEMATICAS
===========================================================
Cierra posiciones sin SL/TP que están causando pérdidas
Sistema alternativo al error MT5 10027
"""

import MetaTrader5 as mt5
from datetime import datetime
import time

def emergency_close_positions():
    print("="*70)
    print("    SOLUCION DE EMERGENCIA - CIERRE MASIVO")
    print("="*70)
    
    # Conectar MT5
    if not mt5.initialize():
        print("[ERROR] No se pudo conectar a MT5")
        return False
    
    # Info cuenta
    account_info = mt5.account_info()
    print(f"Cuenta: {account_info.login}")
    print(f"Balance: ${account_info.balance:.2f}")
    print(f"Equity: ${account_info.equity:.2f}")
    print(f"P&L Actual: ${account_info.profit:.2f}")
    
    # Obtener posiciones
    positions = mt5.positions_get()
    if not positions:
        print("No hay posiciones abiertas")
        return True
    
    print(f"\nPosiciones encontradas: {len(positions)}")
    
    # Analizar posiciones problemáticas
    problematic_positions = []
    total_loss = 0
    
    for pos in positions:
        # Posiciones sin protección Y con pérdidas
        if (pos.sl == 0 or pos.tp == 0) and pos.profit < -50:
            problematic_positions.append(pos)
            total_loss += pos.profit
    
    if not problematic_positions:
        print("No hay posiciones problemáticas para cerrar")
        return True
    
    print(f"\nPOSICIONES PROBLEMATICAS: {len(problematic_positions)}")
    print(f"Pérdida total acumulada: ${total_loss:.2f}")
    
    print("\nLista de posiciones a cerrar:")
    for i, pos in enumerate(problematic_positions, 1):
        print(f"{i:2d}. Ticket: {pos.ticket} | {pos.symbol} | "
              f"{pos.volume} lotes | Profit: ${pos.profit:.2f}")
    
    # Confirmación automática para emergencia
    print(f"\nCERRANDO {len(problematic_positions)} posiciones problemáticas...")
    
    closed_count = 0
    failed_count = 0
    
    for pos in problematic_positions:
        try:
            # Precio actual para cierre
            symbol_info = mt5.symbol_info(pos.symbol)
            if not symbol_info:
                failed_count += 1
                continue
            
            tick = mt5.symbol_info_tick(pos.symbol)
            if not tick:
                failed_count += 1
                continue
            
            # Precio de cierre según tipo
            if pos.type == 0:  # BUY - cerrar con bid
                close_price = tick.bid
                close_type = mt5.ORDER_TYPE_SELL
            else:  # SELL - cerrar con ask
                close_price = tick.ask
                close_type = mt5.ORDER_TYPE_BUY
            
            # Solicitud de cierre
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": close_price,
                "deviation": 50,
                "magic": pos.magic,
                "comment": "EMERGENCY_CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar cierre
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[OK] Posicion {pos.ticket} cerrada - Profit: ${pos.profit:.2f}")
                closed_count += 1
            else:
                print(f"[FAIL] Posicion {pos.ticket} - Error: {result.retcode if result else 'No result'}")
                failed_count += 1
            
            time.sleep(0.5)  # Pausa entre cierres
            
        except Exception as e:
            print(f"[ERROR] Cerrando posicion {pos.ticket}: {e}")
            failed_count += 1
    
    print("\n" + "="*70)
    print("RESUMEN DE CIERRE DE EMERGENCIA")
    print("="*70)
    print(f"Posiciones cerradas: {closed_count}")
    print(f"Fallos: {failed_count}")
    
    # Estado final
    final_account = mt5.account_info()
    if final_account:
        print(f"Balance final: ${final_account.balance:.2f}")
        print(f"P&L final: ${final_account.profit:.2f}")
    
    mt5.shutdown()
    return closed_count > 0

if __name__ == "__main__":
    emergency_close_positions()