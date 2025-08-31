#!/usr/bin/env python
"""
DEBUG - Analizar por que no se generan senales
"""

import os
import sys
from pathlib import Path

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from src.signals.advanced_signal_generator import SignalGenerator

def debug_signal_generation():
    print("=== DEBUG GENERACION DE SENALES ===")
    
    # Crear generador
    generator = SignalGenerator(symbols=['XAUUSD'], auto_execute=False)
    
    # Obtener datos de un simbolo
    symbol = 'XAUUSD'
    print(f"\nAnalizando {symbol}...")
    
    # Obtener datos de mercado
    df = generator.get_market_data(symbol, 'M5', 100)
    
    if df is not None:
        print(f"Datos obtenidos: {len(df)} filas")
        print(f"Columnas: {list(df.columns)}")
        
        # Mostrar ultimas filas
        print(f"\nUltimos 5 datos:")
        print(df[['close', 'volume_ratio', 'rsi', 'momentum', 'macd', 'signal']].tail())
        
        # Calcular indicadores
        df = generator.calculate_indicators(df)
        
        print(f"\nIndicadores calculados:")
        print(f"RSI ultimo: {df['rsi'].iloc[-1]}")
        print(f"Volume ratio ultimo: {df['volume_ratio'].iloc[-1]}")
        print(f"Momentum ultimo: {df['momentum'].iloc[-1] if 'momentum' in df else 'No calculado'}")
        print(f"MACD ultimo: {df['macd'].iloc[-1]}")
        
        # Probar cada estrategia individualmente
        print(f"\n=== PROBANDO ESTRATEGIAS ===")
        
        for strategy_name, strategy_func in generator.strategies.items():
            print(f"\nEstrategia: {strategy_name}")
            signals = strategy_func(df, symbol)
            print(f"Senales generadas: {len(signals)}")
            
            if signals:
                for signal in signals:
                    print(f"  -> {signal['type']} {signal['strength']:.2f} - {signal['reason']}")
            else:
                print("  -> No hay senales")
                
                # Debug especifico para momentum
                if strategy_name == 'momentum':
                    last_row = df.iloc[-1]
                    prev_row = df.iloc[-2]
                    
                    print(f"    Debug momentum:")
                    print(f"    - Momentum actual: {last_row.get('momentum', 'N/A')}")
                    print(f"    - Momentum previo: {prev_row.get('momentum', 'N/A')}")
                    print(f"    - RSI: {last_row['rsi']}")
                    print(f"    - Volume ratio: {last_row['volume_ratio']}")
                    
                    # Condiciones
                    momentum_actual = last_row.get('momentum', 0)
                    momentum_previo = prev_row.get('momentum', 0)
                    
                    print(f"    Condiciones BUY:")
                    print(f"    - momentum > 0: {momentum_actual > 0} ({momentum_actual})")
                    print(f"    - prev_momentum <= 0: {momentum_previo <= 0} ({momentum_previo})")
                    print(f"    - RSI < 70: {last_row['rsi'] < 70} ({last_row['rsi']})")
                    print(f"    - volume_ratio > 1.2: {last_row['volume_ratio'] > 1.2} ({last_row['volume_ratio']})")
        
    else:
        print("No se pudieron obtener datos")

if __name__ == "__main__":
    debug_signal_generation()