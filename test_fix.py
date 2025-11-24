#!/usr/bin/env python
"""
PRUEBA DEL FIX TWELVEDATA
"""
import os
import sys

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.data.twelvedata_client import TwelveDataClient

print("PROBANDO CLIENTE TWELVEDATA CORREGIDO...")
client = TwelveDataClient()

# Probar método corregido
symbols = ['EURUSD', 'XAUUSD']
for symbol in symbols:
    print(f'\nProbando {symbol}:')
    try:
        df = client.get_historical_data(symbol, '5min', 10)
        if df is not None and len(df) > 0:
            print(f'  OK - Datos obtenidos: {len(df)} registros')
            print(f'  Precio actual: {df["close"].iloc[-1]:.5f}')
        else:
            print(f'  ERROR - Sin datos para {symbol}')
    except Exception as e:
        print(f'  ERROR: {e}')

print('\nPrueba completada')