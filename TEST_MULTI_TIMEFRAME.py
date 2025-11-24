#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST DE ESTRATEGIA MULTI-TIMEFRAME
Prueba la nueva estrategia con datos reales
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.signals.multi_timeframe_strategy import MultiTimeframeStrategy

def main():
    print("="*60)
    print("     TEST ESTRATEGIA MULTI-TIMEFRAME")
    print("="*60)
    
    # Crear instancia de la estrategia
    strategy = MultiTimeframeStrategy()
    
    # Símbolos a probar
    symbols_to_test = ['BTCUSDm', 'EURUSD', 'XAUUSD']
    
    for symbol in symbols_to_test:
        print(f"\n[TEST] Analizando {symbol}...")
        print("-"*40)
        
        try:
            # Generar señal
            signals = strategy.generate_signal(None, symbol)
            
            if signals:
                for signal in signals:
                    print(f"\n[SEÑAL DETECTADA]")
                    print(f"  Símbolo: {signal['symbol']}")
                    print(f"  Tipo: {signal['type']}")
                    print(f"  Precio entrada: {signal['price']:.5f}")
                    print(f"  Stop Loss: {signal['sl']:.5f}")
                    print(f"  Take Profit: {signal['tp']:.5f}")
                    print(f"  Confianza: {signal['strength']*100:.1f}%")
                    print(f"  Estrategia: {signal['strategy']}")
                    print(f"  Razón: {signal['reason']}")
                    
                    # Mostrar análisis adicional si está disponible
                    if 'analysis' in signal:
                        print(f"\n  [Análisis técnico]")
                        analysis = signal['analysis']
                        if analysis.get('rsi_5min'):
                            print(f"    RSI 5min: {analysis['rsi_5min']}")
                        if analysis.get('rsi_15min'):
                            print(f"    RSI 15min: {analysis['rsi_15min']}")
                        if analysis.get('rsi_1h'):
                            print(f"    RSI 1h: {analysis['rsi_1h']}")
                        if analysis.get('atr'):
                            print(f"    ATR: {analysis['atr']}")
                        if analysis.get('adx'):
                            print(f"    ADX: {analysis['adx']}")
            else:
                print(f"  -> No hay señales fuertes para {symbol}")
                
        except Exception as e:
            print(f"  -> Error analizando {symbol}: {e}")
    
    print("\n" + "="*60)
    print("Test completado")
    print("="*60)

if __name__ == "__main__":
    main()