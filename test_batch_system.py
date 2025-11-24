#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prueba del sistema batch de TwelveData
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.twelvedata_client import TwelveDataClient

def test_batch_system():
    """Prueba el sistema de batch requests"""
    
    print("=== PRUEBA SISTEMA BATCH REQUESTS ===")
    
    # Crear cliente
    client = TwelveDataClient()
    
    # Símbolos para probar
    symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD']
    
    print(f"Probando batch con símbolos: {symbols}")
    
    # Ejecutar batch request
    batch_data = client.get_symbol_batch_data(symbols, intervals=['5min', '15min'])
    
    if batch_data:
        print(f"\n[OK] BATCH EXITOSO - Datos obtenidos para {len(batch_data)} simbolos")
        
        for symbol, data in batch_data.items():
            print(f"\n--- {symbol} ---")
            
            # Time series
            if data['time_series']:
                for interval, ts_data in data['time_series'].items():
                    if ts_data and 'values' in ts_data:
                        print(f"  Time series {interval}: {len(ts_data['values'])} velas")
                    else:
                        print(f"  Time series {interval}: SIN DATOS")
            
            # Indicadores
            if data['indicators']:
                indicators_ok = [ind for ind, ind_data in data['indicators'].items() if ind_data and 'values' in ind_data]
                print(f"  Indicadores exitosos: {len(indicators_ok)} - {', '.join(indicators_ok)}")
            
            # Quote
            if data['quote']:
                price = data['quote'].get('close', 'N/A')
                print(f"  Precio actual: {price}")
            else:
                print(f"  Precio actual: NO DISPONIBLE")
        
        # Calcular ahorro de consultas
        individual_requests = len(symbols) * (2 + 5 + 1)  # 2 time series + 5 indicadores + 1 quote = 8 por símbolo
        batch_requests = 1  # Solo 1 batch request
        
        print(f"\n[AHORRO] API OPTIMIZADA:")
        print(f"  Consultas individuales: {individual_requests}")
        print(f"  Consultas batch: {batch_requests}")
        print(f"  Ahorro: {individual_requests - batch_requests} consultas ({((individual_requests - batch_requests) / individual_requests * 100):.1f}%)")
        
    else:
        print("[ERROR] No se pudieron obtener datos batch")

if __name__ == "__main__":
    test_batch_system()