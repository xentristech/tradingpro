#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador completo de posiciones e historial
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta

def check_all():
    print("="*70)
    print("     VERIFICADOR COMPLETO MT5 - POSICIONES E HISTORIAL")
    print("="*70)
    print(f"Hora: {datetime.now()}\n")
    
    # Conectar a MT5
    if not mt5.initialize():
        print("[ERROR] No se pudo conectar a MT5")
        return
    
    # Info de cuenta
    account_info = mt5.account_info()
    if account_info:
        print("INFORMACION DE CUENTA:")
        print(f"  Cuenta: {account_info.login}")
        print(f"  Balance: ${account_info.balance:.2f}")
        print(f"  Equity: ${account_info.equity:.2f}")
        print(f"  Margin: ${account_info.margin:.2f}")
        print(f"  Margin libre: ${account_info.margin_free:.2f}")
        print(f"  Profit actual: ${account_info.profit:.2f}")
        print(f"  Servidor: {account_info.server}")
        print(f"  Apalancamiento: 1:{account_info.leverage}")
    
    print("\n" + "-"*70)
    print("POSICIONES ABIERTAS:")
    print("-"*70)
    
    # Obtener posiciones abiertas
    positions = mt5.positions_get()
    
    if positions:
        print(f"Total: {len(positions)} posiciones\n")
        for i, pos in enumerate(positions, 1):
            print(f"Posicion #{i}:")
            print(f"  Ticket: {pos.ticket}")
            print(f"  Simbolo: {pos.symbol}")
            print(f"  Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
            print(f"  Volumen: {pos.volume} lotes")
            print(f"  Precio entrada: {pos.price_open:.5f}")
            print(f"  Precio actual: {pos.price_current:.5f}")
            print(f"  Swap: ${pos.swap:.2f}")
            print(f"  Profit: ${pos.profit:.2f}")
            print(f"  Stop Loss: {pos.sl if pos.sl > 0 else 'NO CONFIGURADO'}")
            print(f"  Take Profit: {pos.tp if pos.tp > 0 else 'NO CONFIGURADO'}")
            
            if pos.sl == 0 or pos.tp == 0:
                print("  [ALERTA] Posicion sin proteccion completa!")
            
            print(f"  Hora apertura: {datetime.fromtimestamp(pos.time)}")
            print(f"  Comentario: {pos.comment}")
            print()
    else:
        print("No hay posiciones abiertas\n")
    
    print("-"*70)
    print("ORDENES PENDIENTES:")
    print("-"*70)
    
    # Obtener ordenes pendientes
    orders = mt5.orders_get()
    
    if orders:
        print(f"Total: {len(orders)} ordenes\n")
        for order in orders:
            print(f"Orden #{order.ticket}:")
            print(f"  Simbolo: {order.symbol}")
            print(f"  Tipo: {order.type_filling}")
            print(f"  Volumen: {order.volume_current} lotes")
            print(f"  Precio: {order.price_open:.5f}")
            print()
    else:
        print("No hay ordenes pendientes\n")
    
    print("-"*70)
    print("HISTORIAL (ultimas 24 horas):")
    print("-"*70)
    
    # Obtener historial de las ultimas 24 horas
    desde = datetime.now() - timedelta(days=1)
    hasta = datetime.now()
    
    # Obtener deals del historial
    history_deals = mt5.history_deals_get(desde, hasta)
    
    if history_deals:
        print(f"Total: {len(history_deals)} operaciones\n")
        
        total_profit = 0
        wins = 0
        losses = 0
        
        for deal in history_deals[-10:]:  # Mostrar ultimas 10
            if deal.profit != 0:
                print(f"Deal #{deal.ticket}:")
                print(f"  Simbolo: {deal.symbol}")
                print(f"  Tipo: {'BUY' if deal.type == 0 else 'SELL'}")
                print(f"  Volumen: {deal.volume}")
                print(f"  Profit: ${deal.profit:.2f}")
                print(f"  Hora: {datetime.fromtimestamp(deal.time)}")
                
                total_profit += deal.profit
                if deal.profit > 0:
                    wins += 1
                else:
                    losses += 1
                print()
        
        print(f"\nRESUMEN ULTIMAS 24H:")
        print(f"  Ganadas: {wins}")
        print(f"  Perdidas: {losses}")
        print(f"  Total P&L: ${total_profit:.2f}")
    else:
        print("No hay operaciones en las ultimas 24 horas\n")
    
    print("="*70)
    print("VERIFICACION COMPLETADA")
    print("="*70)
    
    mt5.shutdown()

if __name__ == "__main__":
    check_all()