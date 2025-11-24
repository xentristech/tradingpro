#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VISOR DE LOGS DEL DIRECTOR EN TIEMPO REAL
========================================
Muestra la actividad del Director de Operaciones en vivo
"""

import time
import os
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 70)
    print("    VISOR DE LOGS DEL DIRECTOR - TIEMPO REAL")
    print("=" * 70)
    print()
    
    log_file = Path("logs/director_operations.log")
    
    if not log_file.exists():
        print("❌ Archivo de log no encontrado:")
        print(f"   {log_file}")
        print()
        print("Para generar logs del Director, ejecuta:")
        print("   python START_TRADING_SYSTEM_CON_DIRECTOR.py")
        return
    
    print(f"📊 Monitoreando: {log_file}")
    print(f"🕐 Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print()
    print("Presiona Ctrl+C para detener")
    print("-" * 50)
    
    # Ir al final del archivo
    last_position = log_file.stat().st_size
    
    try:
        while True:
            # Verificar si el archivo creció
            current_size = log_file.stat().st_size
            
            if current_size > last_position:
                # Leer las nuevas líneas
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                
                # Mostrar nuevas líneas
                for line in new_lines:
                    line = line.strip()
                    if line:
                        # Formatear salida
                        if "DIRECTOR - INFO" in line:
                            timestamp = line.split(' - ')[0]
                            message = ' - '.join(line.split(' - ')[3:])
                            print(f"🎯 [{timestamp.split()[1]}] {message}")
                        elif "DIRECTOR - ERROR" in line:
                            timestamp = line.split(' - ')[0]
                            message = ' - '.join(line.split(' - ')[3:])
                            print(f"❌ [{timestamp.split()[1]}] {message}")
                        elif "AJUSTE:" in line:
                            timestamp = line.split(' - ')[0]
                            message = ' - '.join(line.split(' - ')[3:])
                            print(f"  💰 [{timestamp.split()[1]}] {message}")
                        else:
                            print(f"   {line}")
                
                last_position = current_size
            
            time.sleep(1)  # Verificar cada segundo
            
    except KeyboardInterrupt:
        print()
        print("🛑 Visor detenido por usuario")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_recent_logs():
    """Muestra los logs recientes del Director"""
    print("=" * 50)
    print("  ACTIVIDAD RECIENTE DEL DIRECTOR")
    print("=" * 50)
    
    log_file = Path("logs/director_operations.log")
    
    if not log_file.exists():
        print("No hay logs del Director disponibles")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Mostrar últimas 20 líneas
        recent_lines = lines[-20:] if len(lines) > 20 else lines
        
        for line in recent_lines:
            line = line.strip()
            if line:
                if "AJUSTE:" in line:
                    print(f"💰 {line}")
                elif "TP ajustados:" in line:
                    print(f"🎯 {line}")
                elif "ERROR" in line:
                    print(f"❌ {line}")
                else:
                    print(f"   {line}")
                    
        print()
        print(f"Total líneas en log: {len(lines)}")
        
    except Exception as e:
        print(f"Error leyendo logs: {e}")

if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--recent":
        show_recent_logs()
    else:
        main()