#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
REVISAR ESTADO DE TRADING
========================
Script para verificar si se están ejecutando operaciones
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import os
import sys

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 60)
print("    ESTADO ACTUAL DEL TRADING")
print("=" * 60)

if mt5.initialize():
    print("✅ Conectado a MT5")
    
    # Info de cuenta
    account = mt5.account_info()
    if account:
        print(f"Cuenta: {account.login}")
        print(f"Balance: ${account.balance:.2f}")
        print(f"Equity: ${account.equity:.2f}")
        print(f"Margin: ${account.margin:.2f}")
        print(f"Free Margin: ${account.margin_free:.2f}")
        print(f"Profit: ${account.profit:.2f}")
    
    # Posiciones activas
    positions = mt5.positions_get()
    if positions:
        print(f"\n📊 POSICIONES ACTIVAS: {len(positions)}")
        total_profit = 0
        for pos in positions:
            type_desc = "BUY" if pos.type == 0 else "SELL"
            print(f"  {pos.symbol} #{pos.ticket}: ${pos.profit:.2f} | {type_desc}")
            total_profit += pos.profit
        print(f"  TOTAL P&L: ${total_profit:.2f}")
    else:
        print("\n❌ Sin posiciones activas")
    
    # Órdenes pendientes
    orders = mt5.orders_get()
    if orders:
        print(f"\n📋 ÓRDENES PENDIENTES: {len(orders)}")
        for order in orders:
            order_type = "BUY LIMIT" if order.type == 2 else "SELL LIMIT" if order.type == 3 else f"TYPE_{order.type}"
            print(f"  {order.symbol} #{order.ticket}: {order_type} @ {order.price_open}")
    else:
        print("\n📋 Sin órdenes pendientes")
    
    # Historial de órdenes recientes (últimas 4 horas)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=4)
    
    history_orders = mt5.history_orders_get(start_time, end_time)
    if history_orders:
        print(f"\n📈 ÓRDENES RECIENTES (últimas 4h): {len(history_orders)}")
        for order in history_orders[-10:]:  # Mostrar las últimas 10
            time_str = datetime.fromtimestamp(order.time_setup).strftime("%H:%M:%S")
            print(f"  [{time_str}] {order.symbol} {order.type_str}: {order.state_description}")
    else:
        print("\n📈 Sin órdenes en las últimas 4 horas")
    
    # Deals recientes
    history_deals = mt5.history_deals_get(start_time, end_time)
    if history_deals:
        print(f"\n💰 DEALS RECIENTES (últimas 4h): {len(history_deals)}")
        for deal in history_deals[-10:]:
            time_str = datetime.fromtimestamp(deal.time).strftime("%H:%M:%S")
            print(f"  [{time_str}] {deal.symbol} {deal.type_str}: ${deal.profit:.2f}")
    else:
        print("\n💰 Sin deals en las últimas 4 horas")
    
    mt5.shutdown()
else:
    print("❌ Error conectando a MT5")

print("\n" + "=" * 60)