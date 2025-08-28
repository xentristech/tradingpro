#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Monitor de logs en tiempo real del bot de trading
"""
import os
import time
import subprocess
import sys
from datetime import datetime

def monitor_bot():
    print("="*60)
    print("   MONITOR DE LOGS - BOT DE TRADING")
    print(f"   Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    print()
    
    # Cambiar al directorio del bot
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(bot_dir)
    
    try:
        # Ejecutar el bot y capturar salida en tiempo real
        process = subprocess.Popen(
            [sys.executable, "quick_launcher.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("Bot iniciado... Mostrando logs en tiempo real:")
        print("-" * 60)
        
        # Leer salida línea por línea
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] {output.strip()}")
                
        # Obtener código de salida
        rc = process.poll()
        print(f"\n[EXIT] Bot terminado con código: {rc}")
        
    except KeyboardInterrupt:
        print("\n[STOP] Deteniendo monitor...")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print("\nPresione Enter para salir...")
    try:
        input()
    except:
        pass

if __name__ == "__main__":
    monitor_bot()