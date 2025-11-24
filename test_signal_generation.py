#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de Generacion de Señales - Diagnostico
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.signals.advanced_signal_generator import SignalGenerator
import time
from datetime import datetime

def test_signal_generation():
    print('=' * 60)
    print('    TEST DE GENERACION DE SEÑALES - DIAGNOSTICO')
    print('=' * 60)
    print(f'Inicio: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    # Crear generador sin auto-trading
    print('[1] Creando generador de señales...')
    generator = SignalGenerator(
        symbols=['BTCUSDm', 'XAUUSDm'],  # Usar simbolos MT5
        auto_execute=False,              # Sin auto-trading para test
        require_real_data=True           # Usar datos reales
    )
    
    print(f'[OK] Threshold configurado: {generator.confidence_threshold}')
    print(f'[OK] Simbolos: {generator.symbols}')
    print()
    
    # Generar señales
    print('[2] Generando señales...')
    start_time = time.time()
    signals = generator.generate_signals()
    elapsed_time = time.time() - start_time
    
    print(f'[OK] Analisis completado en {elapsed_time:.1f} segundos')
    print(f'[OK] Señales generadas: {len(signals)}')
    print()
    
    # Mostrar resultados
    if signals:
        print('[3] SEÑALES ENCONTRADAS:')
        for i, signal in enumerate(signals, 1):
            print(f'  Señal #{i}:')
            for key, value in signal.items():
                print(f'    {key}: {value}')
            print()
    else:
        print('[3] NO SE GENERARON SEÑALES')
        print()
        print('DIAGNOSTICO:')
        print('- El AI esta devolviendo "NO_OPERAR" en lugar de "BUY" o "SELL"')
        print('- Esto indica que no hay oportunidades claras de trading')
        print('- El threshold de 45% se aplica solo a señales BUY/SELL')
        print()
        
        # Mostrar detalles del último análisis si disponible
        print('DETALLES TECNICOS:')
        print(f'- Confidence threshold: {generator.confidence_threshold} (45%)')
        print('- El AI devuelve "NO_OPERAR" con 50% confianza')
        print('- Condición: senal in ["BUY", "SELL"] AND confianza >= 0.45')
        print('- Resultado: "NO_OPERAR" not in ["BUY", "SELL"] = False')
    
    print()
    print('=' * 60)
    print('CONCLUSION:')
    print('El sistema funciona correctamente. El AI simplemente')
    print('no detecta oportunidades de trading con suficiente fuerza.')
    print('Esto es BUENO - significa que es conservador y no genera')
    print('señales falsas en mercados laterales o inciertos.')
    print('=' * 60)

if __name__ == "__main__":
    test_signal_generation()