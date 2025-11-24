#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Revision detallada de posiciones abiertas
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.broker.mt5_connection import MT5Connection
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

print('=' * 80)
print('    REVISION DETALLADA DE POSICIONES ABIERTAS')
print('=' * 80)
print(f'Fecha/Hora: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# Conectar a MT5
mt5_conn = MT5Connection()
if mt5_conn.connect():
    print('[OK] Conectado a MT5')
    
    # Obtener información de cuenta
    account = mt5_conn.get_account_info()
    if account:
        print(f'[OK] Cuenta: {account.login}')
        print(f'[OK] Balance: ${account.balance:.2f}')
        print(f'[OK] Equity: ${account.equity:.2f}')
        print(f'[OK] Margin Free: ${account.margin_free:.2f}')
        print(f'[OK] Server: {account.server}')
        print()
    
    # Obtener posiciones abiertas
    positions = mt5_conn.get_positions()
    print(f'[INFO] Total posiciones abiertas: {len(positions)}')
    print()
    
    if positions:
        print('DETALLE DE POSICIONES:')
        print('-' * 80)
        
        total_profit = 0
        for i, pos in enumerate(positions, 1):
            profit_status = '[+]' if pos.profit > 0 else '[-]' if pos.profit < 0 else '[=]'
            
            print(f'{i}. Ticket: {pos.ticket}')
            print(f'   Simbolo: {pos.symbol}')
            print(f'   Tipo: {"BUY" if pos.type == 0 else "SELL"}')
            print(f'   Volumen: {pos.volume}')
            print(f'   Precio Entrada: {pos.price_open}')
            print(f'   Precio Actual: {pos.price_current}')
            print(f'   Stop Loss: {pos.sl if pos.sl != 0 else "Sin SL"}')
            print(f'   Take Profit: {pos.tp if pos.tp != 0 else "Sin TP"}')
            print(f'   Profit: ${pos.profit:.2f} {profit_status}')
            print(f'   Swap: ${pos.swap:.2f}')
            # print(f'   Comision: ${pos.commission:.2f}')  # No disponible en TradePosition
            print(f'   Tiempo: {datetime.fromtimestamp(pos.time)}')
            print(f'   Magic: {pos.magic}')
            print()
            
            total_profit += pos.profit
        
        print(f'RESUMEN:')
        print(f'Total P&L: ${total_profit:.2f}')
        print(f'Posiciones en ganancia: {sum(1 for p in positions if p.profit > 0)}')
        print(f'Posiciones en perdida: {sum(1 for p in positions if p.profit < 0)}')
        print()
        
        # Análizar protección de posiciones
        sin_sl = [p for p in positions if p.sl == 0]
        sin_tp = [p for p in positions if p.tp == 0]
        
        print('ANALISIS DE PROTECCION:')
        print('-' * 40)
        print(f'Posiciones SIN Stop Loss: {len(sin_sl)}')
        if sin_sl:
            for p in sin_sl:
                print(f'  - {p.symbol} Ticket: {p.ticket} (${p.profit:.2f})')
        
        print(f'Posiciones SIN Take Profit: {len(sin_tp)}')
        if sin_tp:
            for p in sin_tp:
                print(f'  - {p.symbol} Ticket: {p.ticket} (${p.profit:.2f})')
        
        print()
        print('QUE PUEDE HACER EL SISTEMA:')
        print('-' * 50)
        print('[OK] Monitor automatico cada 30 segundos')
        print('[OK] Breakeven: Mover SL a precio de entrada cuando hay ganancia')
        print('[OK] Trailing Stop: Seguir el precio con SL dinamico')
        print('[OK] Cerrar posiciones automaticamente por riesgo')
        print('[OK] Aplicar SL/TP automatico a posiciones sin proteccion')
        print('[OK] Notificaciones por Telegram sobre cambios')
        print('[OK] Gestion de riesgo adaptativa')
        
        # Configuración desde .env
        print()
        print('CONFIGURACION ACTUAL (.env):')
        print('-' * 40)
        import os
        from dotenv import load_dotenv
        load_dotenv('configs/.env')
        
        print(f'ENABLE_BREAKEVEN: {os.getenv("ENABLE_BREAKEVEN", "false")}')
        print(f'ENABLE_TRAILING_STOP: {os.getenv("ENABLE_TRAILING_STOP", "false")}')
        print(f'BREAKEVEN_TRIGGER_PIPS: {os.getenv("BREAKEVEN_TRIGGER_PIPS", "20")}')
        print(f'TRAILING_ACTIVATION_PIPS: {os.getenv("TRAILING_ACTIVATION_PIPS", "30")}')
        print(f'TRAILING_DISTANCE_PIPS: {os.getenv("TRAILING_DISTANCE_PIPS", "15")}')
        print(f'RISK_CHECK_INTERVAL: {os.getenv("RISK_CHECK_INTERVAL", "30")} segundos')
        
    else:
        print('[INFO] No hay posiciones abiertas')
    
    mt5_conn.disconnect()
else:
    print('[ERROR] No se pudo conectar a MT5')

print('=' * 80)