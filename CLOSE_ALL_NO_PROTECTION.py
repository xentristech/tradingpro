#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIERRE TODAS LAS POSICIONES SIN SL/TP
====================================
Cierra TODAS las posiciones que no tengan Stop Loss o Take Profit
"""

import MetaTrader5 as mt5
from datetime import datetime
import time

def close_all_unprotected():
    print("="*70)
    print("    CIERRE DE POSICIONES SIN PROTECCION")
    print("="*70)
    
    if not mt5.initialize():
        print("[ERROR] No se pudo conectar a MT5")
        return False
    
    account_info = mt5.account_info()
    print(f"Cuenta: {account_info.login}")
    print(f"Balance: ${account_info.balance:.2f}")
    print(f"P&L Total: ${account_info.profit:.2f}")
    
    positions = mt5.positions_get()
    if not positions:
        print("No hay posiciones abiertas")
        return True
    
    # Buscar posiciones sin protección
    unprotected = []
    for pos in positions:
        if pos.sl == 0 or pos.tp == 0:
            unprotected.append(pos)
    
    if not unprotected:
        print("Todas las posiciones tienen protección")
        return True
    
    print(f"\nPOSICIONES SIN PROTECCION: {len(unprotected)}")
    
    total_profit = sum(pos.profit for pos in unprotected)
    print(f"P&L acumulado: ${total_profit:.2f}")
    
    print("\nCerrando posiciones...")
    
    closed = 0
    failed = 0
    
    for pos in unprotected:
        try:
            tick = mt5.symbol_info_tick(pos.symbol)
            if not tick:
                failed += 1
                continue
            
            # Precio y tipo de cierre
            if pos.type == 0:  # BUY
                price = tick.bid
                close_type = mt5.ORDER_TYPE_SELL
            else:  # SELL
                price = tick.ask
                close_type = mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": price,
                "deviation": 100,
                "magic": pos.magic,
                "comment": "CLOSE_NO_PROTECTION"
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[OK] {pos.symbol} #{pos.ticket} - ${pos.profit:.2f}")
                closed += 1
            else:
                print(f"[FAIL] {pos.symbol} #{pos.ticket} - Error: {result.retcode if result else 'N/A'}")
                failed += 1
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"[ERROR] {pos.ticket}: {e}")
            failed += 1
    
    print(f"\nRESULTADO:")
    print(f"Cerradas: {closed}")
    print(f"Fallos: {failed}")
    
    # Estado final
    final_account = mt5.account_info()
    if final_account:
        print(f"Balance final: ${final_account.balance:.2f}")
        print(f"P&L final: ${final_account.profit:.2f}")
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    close_all_unprotected()