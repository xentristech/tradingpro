#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DASHBOARD DE SEÑALES IA - TIEMPO REAL
===================================== 
Monitorea las señales que genera la IA y su proceso de análisis
"""

import time
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import threading
from collections import deque

# Configurar path
sys.path.insert(0, str(Path(__file__).parent))

class SignalMonitor:
    def __init__(self):
        self.signals_history = deque(maxlen=50)  # Últimas 50 señales
        self.ai_analysis_history = deque(maxlen=100)  # Últimos 100 análisis
        self.confidence_stats = {'total': 0, 'above_45': 0, 'executed': 0}
        self.symbols_analyzed = {'BTCUSDm': 0, 'XAUUSDm': 0, 'EURUSDm': 0, 'GBPUSDm': 0}
        self.last_analysis_time = {}
        
    def parse_log_line(self, line):
        """Extrae información de las líneas de log"""
        if not line.strip():
            return None
            
        try:
            # Extraer timestamp
            timestamp_str = line.split(' - ')[0] if ' - ' in line else ''
            
            # Buscar análisis IA completado
            if "Análisis IA completado para" in line and ":" in line:
                parts = line.split("Análisis IA completado para ")
                if len(parts) > 1:
                    symbol_and_result = parts[1]
                    if ":" in symbol_and_result:
                        symbol = symbol_and_result.split(":")[0].strip()
                        decision = symbol_and_result.split(":")[1].strip()
                        
                        return {
                            'timestamp': timestamp_str,
                            'type': 'ai_analysis',
                            'symbol': symbol,
                            'decision': decision,
                            'confidence': None
                        }
            
            # Buscar líneas con confianza
            if "Confianza:" in line and "%" in line:
                try:
                    conf_part = line.split("Confianza:")[1].split("%")[0].strip()
                    confidence = float(conf_part)
                    
                    # Extraer símbolo
                    symbol = None
                    for sym in ['BTCUSDm', 'XAUUSDm', 'EURUSDm', 'GBPUSDm']:
                        if sym in line:
                            symbol = sym
                            break
                    
                    # Extraer decisión
                    decision = 'NO_OPERAR'
                    if 'BUY' in line:
                        decision = 'BUY'
                    elif 'SELL' in line:
                        decision = 'SELL'
                    
                    return {
                        'timestamp': timestamp_str,
                        'type': 'confidence_analysis',
                        'symbol': symbol,
                        'decision': decision,
                        'confidence': confidence
                    }
                except:
                    pass
            
            # Buscar señales generadas
            if "señal IA generada" in line or "Señal IA generada" in line:
                return {
                    'timestamp': timestamp_str,
                    'type': 'signal_generated',
                    'content': line
                }
                
        except Exception as e:
            pass
        
        return None
    
    def update_from_logs(self):
        """Lee los logs del sistema para obtener análisis de IA"""
        log_files = [
            Path("logs/advanced_signal_generator.log"),
            Path("logs/ai_hybrid_strategy.log"),
        ]
        
        current_time = datetime.now()
        
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            try:
                # Leer últimas líneas del archivo
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                # Procesar últimas 100 líneas
                for line in lines[-100:]:
                    parsed = self.parse_log_line(line)
                    if parsed:
                        parsed['source'] = log_file.name
                        
                        if parsed['type'] == 'confidence_analysis':
                            # Actualizar estadísticas
                            if parsed['symbol']:
                                self.symbols_analyzed[parsed['symbol']] = self.symbols_analyzed.get(parsed['symbol'], 0) + 1
                                self.last_analysis_time[parsed['symbol']] = current_time
                            
                            if parsed['confidence'] is not None:
                                self.confidence_stats['total'] += 1
                                if parsed['confidence'] >= 45:
                                    self.confidence_stats['above_45'] += 1
                                    if parsed['decision'] in ['BUY', 'SELL']:
                                        self.confidence_stats['executed'] += 1
                        
                        self.ai_analysis_history.append(parsed)
                        
            except Exception as e:
                continue
    
    def get_recent_analysis(self, minutes=10):
        """Obtiene análisis recientes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = []
        
        for analysis in list(self.ai_analysis_history)[-20:]:  # Últimos 20
            try:
                if analysis.get('timestamp'):
                    # Parsear timestamp simple
                    time_str = analysis['timestamp'].split(',')[0] if ',' in analysis['timestamp'] else analysis['timestamp']
                    recent.append(analysis)
            except:
                recent.append(analysis)
                
        return recent[-10:]  # Últimos 10
    
    def display_dashboard(self):
        """Muestra el dashboard en consola"""
        self.update_from_logs()
        
        print("\033[2J\033[H")  # Limpiar pantalla
        print("=" * 80)
        print("MONITOR DE SENALES IA - TIEMPO REAL")
        print("=" * 80)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Estadísticas generales
        print("ESTADISTICAS DE CONFIANZA:")
        print(f"  * Total analisis: {self.confidence_stats['total']}")
        print(f"  * Confianza >=45%: {self.confidence_stats['above_45']}")
        if self.confidence_stats['total'] > 0:
            pct_above = (self.confidence_stats['above_45'] / self.confidence_stats['total']) * 100
            print(f"  * Porcentaje >=45%: {pct_above:.1f}%")
        print(f"  * Senales ejecutadas: {self.confidence_stats['executed']}")
        print()
        
        # Análisis por símbolo
        print("ANALISIS POR SIMBOLO:")
        current_time = datetime.now()
        for symbol, count in self.symbols_analyzed.items():
            last_time = self.last_analysis_time.get(symbol)
            if last_time:
                mins_ago = int((current_time - last_time).total_seconds() / 60)
                status = "[ACTIVO]" if mins_ago < 5 else "[OK]" if mins_ago < 15 else "[INACTIVO]"
                print(f"  {status} {symbol}: {count} analisis (ultimo: hace {mins_ago}min)")
            else:
                print(f"  [SIN DATOS] {symbol}: {count} analisis (sin actividad reciente)")
        print()
        
        # Análisis recientes
        print("ANALISIS RECIENTES (Ultimos 10):")
        print("-" * 80)
        recent = self.get_recent_analysis()
        
        if not recent:
            print("  No hay analisis recientes disponibles")
        else:
            for i, analysis in enumerate(reversed(recent[-10:]), 1):
                timestamp = analysis.get('timestamp', 'N/A')[:19] if analysis.get('timestamp') else 'N/A'
                symbol = analysis.get('symbol', 'N/A')
                decision = analysis.get('decision', 'N/A')
                confidence = analysis.get('confidence')
                
                conf_str = f"{confidence:.1f}%" if confidence is not None else "N/A"
                
                # Colorear según confianza
                if confidence and confidence >= 45:
                    if decision in ['BUY', 'SELL']:
                        status = "[EJECUTABLE]"  # Ejecutable
                    else:
                        status = "[ALTA CONF]"   # Alta confianza pero NO_OPERAR
                else:
                    status = "[BAJA CONF]"  # Baja confianza
                
                print(f"  {status} {timestamp} | {symbol:8} | {decision:10} | Conf: {conf_str}")
        
        print("-" * 80)
        print()
        
        # Instrucciones
        print("LEYENDA:")
        print("  [EJECUTABLE] - Senal ejecutable (>=45% confianza + BUY/SELL)")
        print("  [ALTA CONF]  - Alta confianza pero NO_OPERAR")
        print("  [BAJA CONF]  - Confianza insuficiente (<45%)")
        print()
        print("Actualizando cada 5 segundos... Presiona Ctrl+C para salir")

def main():
    monitor = SignalMonitor()
    
    print("Iniciando Monitor de Señales IA...")
    print("Leyendo logs del sistema...")
    
    try:
        while True:
            monitor.display_dashboard()
            time.sleep(5)  # Actualizar cada 5 segundos
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor detenido por usuario")
        print("Monitor finalizado")

if __name__ == "__main__":
    main()