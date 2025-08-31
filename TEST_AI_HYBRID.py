#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prueba de la estrategia híbrida IA (Ollama + TwelveData)
"""

import os
import sys
from pathlib import Path

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_ai_hybrid_strategy():
    print("="*60)
    print("      PRUEBA ESTRATEGIA HIBRIDA IA")
    print("      Ollama + TwelveData + Indicadores")
    print("="*60)
    
    try:
        # 1. Probar importación
        print("\n1. Probando importación de módulos...")
        
        try:
            from src.signals.ai_hybrid_strategy import AIHybridStrategy
            print("[OK] AIHybridStrategy importada correctamente")
        except ImportError as e:
            print(f"[ERROR] Error importando AIHybridStrategy: {e}")
            return
        
        # 2. Crear instancia
        print("\n2. Creando instancia de estrategia IA...")
        
        try:
            strategy = AIHybridStrategy()
            print("[OK] Estrategia IA creada correctamente")
        except Exception as e:
            print(f"[ERROR] Error creando estrategia: {e}")
            return
        
        # 3. Verificar clientes
        print("\n3. Verificando clientes disponibles...")
        
        status = strategy.get_status()
        print(f"  - Ollama disponible: {'SI' if status['ollama_available'] else 'NO'}")
        print(f"  - TwelveData disponible: {'SI' if status['twelvedata_available'] else 'NO'}")
        print(f"  - Telegram disponible: {'SI' if status['telegram_available'] else 'NO'}")
        
        # 4. Probar análisis
        print("\n4. Probando análisis con IA...")
        
        test_symbols = ['BTCUSD', 'XAUUSD']
        
        for symbol in test_symbols:
            print(f"\n  [INFO] Analizando {symbol}...")
            
            try:
                # Generar señal (simular DataFrame vacío)
                signals = strategy.generate_signal(None, symbol)
                
                if signals:
                    for signal in signals:
                        print(f"    [OK] Señal generada: {signal['type']} (Fuerza: {signal['strength']*100:.0f}%)")
                        print(f"    [PRECIO] Precio: {signal['price']}")
                        print(f"    [SL] SL: {signal.get('sl', 'N/A')}")
                        print(f"    [TP] TP: {signal.get('tp', 'N/A')}")
                        print(f"    [STRATEGY] Estrategia: {signal['strategy']}")
                        print(f"    [REASON] Razón: {signal.get('reason', 'N/A')}")
                else:
                    print(f"    [INFO] No se generaron señales para {symbol}")
                    
            except Exception as e:
                print(f"    [ERROR] Error analizando {symbol}: {e}")
        
        # 5. Mostrar estadísticas
        print(f"\n5. Estadísticas de la estrategia:")
        final_status = strategy.get_status()
        print(f"  - Análisis realizados: {final_status['analysis_count']}")
        print(f"  - Señales generadas: {final_status['signals_generated']}")
        print(f"  - Timeframes utilizados: {', '.join(final_status['timeframes'])}")
        print(f"  - Umbral de confianza: {final_status['confidence_threshold']*100:.0f}%")
        
        print("\n[OK] Prueba de estrategia IA completada")
        
    except Exception as e:
        print(f"\n[ERROR] Error general en prueba: {e}")
        import traceback
        traceback.print_exc()

def test_integration_with_signal_generator():
    print("\n" + "="*60)
    print("      PRUEBA INTEGRACIÓN CON SIGNAL GENERATOR")
    print("="*60)
    
    try:
        # Importar SignalGenerator
        from src.signals.advanced_signal_generator import SignalGenerator
        
        # Crear generador con símbolos de prueba
        print("\nCreando SignalGenerator con estrategia IA...")
        generator = SignalGenerator(symbols=['BTCUSD'], auto_execute=False)
        
        # Verificar si IA está disponible
        if hasattr(generator, 'ai_hybrid_available') and generator.ai_hybrid_available:
            print("[OK] Estrategia IA integrada correctamente")
            print(f"  - Total estrategias: {len(generator.strategies)}")
            print(f"  - Estrategias disponibles: {', '.join(generator.strategies.keys())}")
        else:
            print("[ERROR] Estrategia IA no está disponible en SignalGenerator")
            return
        
        # Probar análisis de un símbolo
        print(f"\nProbando análisis con todas las estrategias...")
        
        symbol = 'BTCUSD'
        all_signals = generator.analyze_symbol(symbol)
        
        print(f"  [INFO] Señales generadas para {symbol}: {len(all_signals)}")
        
        for signal in all_signals:
            strategy_name = signal.get('strategy', 'Unknown')
            signal_type = signal.get('type', 'Unknown')
            strength = signal.get('strength', 0) * 100
            
            print(f"    - {strategy_name}: {signal_type} (Fuerza: {strength:.0f}%)")
        
        print("\n[OK] Integración con SignalGenerator verificada")
        
    except Exception as e:
        print(f"\n[ERROR] Error en integración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Configurar encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Ejecutar pruebas
    test_ai_hybrid_strategy()
    test_integration_with_signal_generator()
    
    print(f"\n{'='*60}")
    print("PRUEBAS COMPLETADAS")
    print(f"{'='*60}")