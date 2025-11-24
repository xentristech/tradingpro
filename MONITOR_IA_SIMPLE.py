#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MONITOR SIMPLE DE SEÑALES IA
============================
Muestra las señales y análisis de IA del sistema en tiempo real
"""

import time
import re
from datetime import datetime
from pathlib import Path

def display_recent_ai_analysis():
    """Muestra análisis recientes de IA desde los logs del sistema"""
    print("\033[2J\033[H")  # Limpiar pantalla
    print("=" * 80)
    print("MONITOR DE SENALES IA - TIEMPO REAL")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Buscar análisis recientes
    ai_analysis = []
    confidence_stats = {'total': 0, 'above_45': 0, 'executed': 0}
    
    # Verificar logs de IA
    log_files = [
        'logs/ai_signal_generator.log',
        'logs/enhanced_signals.log',
        'logs/sistema_completo.log',
        'logs/sistema_optimizado.log',
        'logs/trading_system.log'
    ]
    
    for log_file in log_files:
        try:
            if Path(log_file).exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                # Buscar líneas con análisis IA
                for line in lines[-100:]:  # Últimas 100 líneas
                    if any(keyword in line for keyword in [
                        'Análisis IA completado',
                        'IA Analysis:',
                        'Confianza:',
                        'AI_Hybrid_Analysis',
                        'señal IA generada'
                    ]):
                        ai_analysis.append(line.strip())
                        
                        # Extraer estadísticas de confianza
                        if 'Confianza:' in line:
                            try:
                                conf_match = re.search(r'Confianza:\s*([\d.]+)', line)
                                if conf_match:
                                    conf = float(conf_match.group(1))
                                    confidence_stats['total'] += 1
                                    if conf >= 0.45:  # 45%
                                        confidence_stats['above_45'] += 1
                                        if any(word in line for word in ['BUY', 'SELL']):
                                            confidence_stats['executed'] += 1
                            except:
                                pass
        except:
            continue
    
    # Mostrar estadísticas
    print("ESTADISTICAS DE CONFIANZA:")
    print(f"  * Total analisis encontrados: {confidence_stats['total']}")
    print(f"  * Con confianza >=45%: {confidence_stats['above_45']}")
    if confidence_stats['total'] > 0:
        pct = (confidence_stats['above_45'] / confidence_stats['total']) * 100
        print(f"  * Porcentaje >=45%: {pct:.1f}%")
    print(f"  * Senales ejecutadas: {confidence_stats['executed']}")
    print()
    
    # Mostrar análisis recientes
    print("ANALISIS RECIENTES DE IA:")
    print("-" * 80)
    
    if not ai_analysis:
        print("  No hay analisis de IA en los logs disponibles")
        print("  Verificar que el sistema principal este ejecutandose")
    else:
        # Mostrar últimos 15 análisis
        recent_analysis = ai_analysis[-15:] if len(ai_analysis) > 15 else ai_analysis
        
        for i, analysis in enumerate(reversed(recent_analysis), 1):
            # Limpiar la línea para mostrar solo lo importante
            clean_line = analysis.replace('src.signals.ai_hybrid_strategy - INFO - ', '')
            clean_line = clean_line.replace('src.signals.advanced_signal_generator - INFO - ', '')
            clean_line = clean_line.replace('src.ai.ollama_client - INFO - ', '')
            
            # Extraer timestamp si existe
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', clean_line)
            if timestamp_match:
                timestamp = timestamp_match.group(1)[-8:]  # Solo HH:MM:SS
                clean_line = clean_line[len(timestamp_match.group(1)) + 3:]  # Remover timestamp
            else:
                timestamp = "N/A"
            
            # Categorizar el análisis
            if 'Análisis IA completado' in clean_line:
                status = "[IA COMPLETE]"
            elif 'Confianza:' in clean_line:
                status = "[CONFIANZA]"
            elif 'señal IA generada' in clean_line:
                status = "[EJECUTADA]"
            elif 'AI_Hybrid_Analysis' in clean_line:
                status = "[HYBRID]"
            else:
                status = "[INFO]"
            
            print(f"  {status} {timestamp} | {clean_line[:70]}...")
    
    print("-" * 80)
    print()
    
    # Instrucciones
    print("DESCRIPCION:")
    print("  [IA COMPLETE] - Analisis de IA terminado")
    print("  [CONFIANZA]   - Nivel de confianza reportado")
    print("  [EJECUTADA]   - Senal ejecutada por el sistema")
    print("  [HYBRID]      - Analisis hibrido con multiple timeframes")
    print()
    print("Actualizando cada 10 segundos... Presiona Ctrl+C para salir")

def main():
    """Bucle principal del monitor"""
    print("Iniciando Monitor Simple de IA...")
    print("Buscando analisis en logs del sistema...")
    time.sleep(2)
    
    try:
        while True:
            display_recent_ai_analysis()
            time.sleep(10)  # Actualizar cada 10 segundos
            
    except KeyboardInterrupt:
        print("\n\nMonitor detenido por usuario")
        print("Finalizado")

if __name__ == "__main__":
    main()