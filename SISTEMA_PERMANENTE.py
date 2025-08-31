#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de Trading Permanente con Reinicio Automático
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

def log_message(message):
    """Función para logging con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    """Ejecutor principal permanente"""
    script_dir = Path(__file__).parent
    trading_script = script_dir / "START_TRADING_SYSTEM.py"
    
    print("=" * 60)
    print("    ALGO TRADER V3 - SISTEMA PERMANENTE")
    print("=" * 60)
    print()
    print("🤖 Sistema de reinicio automático activado")
    print("🔄 El sistema se reiniciará automáticamente si se detiene")
    print("⏹️  Presiona Ctrl+C para detener completamente")
    print("📝 Los logs se guardan automáticamente")
    print()
    
    restart_count = 0
    
    while True:
        try:
            restart_count += 1
            log_message(f"🚀 Iniciando sistema (Intento #{restart_count})")
            
            # Ejecutar el sistema de trading
            result = subprocess.run([
                sys.executable, str(trading_script)
            ], 
            cwd=str(script_dir),
            capture_output=False,  # Mostrar output en tiempo real
            text=True
            )
            
            # Si llegamos aquí, el proceso terminó
            if result.returncode == 0:
                log_message("✅ Sistema terminado normalmente")
            else:
                log_message(f"⚠️ Sistema terminó con código: {result.returncode}")
            
            log_message("⏳ Esperando 15 segundos antes de reiniciar...")
            time.sleep(15)
            
        except KeyboardInterrupt:
            log_message("🛑 Detenido por usuario (Ctrl+C)")
            print()
            print("Sistema detenido completamente.")
            break
            
        except Exception as e:
            log_message(f"❌ Error inesperado: {e}")
            log_message("⏳ Esperando 30 segundos antes de reiniciar...")
            time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error crítico: {e}")
        input("Presiona Enter para salir...")