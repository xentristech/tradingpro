#!/usr/bin/env python
"""
EJECUTOR DEL SISTEMA COMPLETO - ALGO TRADER V3
Sistema de trading automatico con IA sin problemas de encoding
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    print("="*60)
    print("      ALGO TRADER V3 - SISTEMA COMPLETO ACTIVO")  
    print("="*60)
    print()
    print("CONFIGURACION:")
    print("  * Auto-ejecucion: ACTIVADA")
    print("  * Simbolos: XAUUSD, EURUSD, GBPUSD, BTCUSD") 
    print("  * Monitor SL/TP: ACTIVADO")
    print("  * Notificaciones: Telegram activas")
    print()
    print("ATENCION: Este modo ejecutara trades reales en MetaTrader 5")
    print()
    
    response = input("Estas seguro de activar el trading automatico? (yes/no): ")
    if response.lower() != 'yes':
        print("Operacion cancelada por seguridad")
        return
    
    print()
    print("Iniciando sistema completo...")
    print("="*60)
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Configurar encoding UTF-8 para Python
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # Importar las librerías necesarias
        sys.path.insert(0, str(project_dir))
        
        from src.signals.advanced_signal_generator import SignalGenerator
        
        # Crear y configurar el generador
        print("\nCreando generador de senales con IA...")
        generator = SignalGenerator(
            symbols=['XAUUSD', 'EURUSD', 'GBPUSD', 'BTCUSD'], 
            auto_execute=True
        )
        
        # Mostrar estado
        status = generator.get_status()
        print(f"\nESTADO DEL SISTEMA:")
        print(f"  * MT5 Datos: {'Conectado' if status['mt5_connected'] else 'Modo simulacion'}")
        print(f"  * MT5 Trading: {'Conectado' if status['mt5_connection_active'] else 'Desconectado'}")
        print(f"  * Telegram: {'Activo' if status['telegram_active'] else 'Inactivo'}")
        print(f"  * Simbolos: {', '.join(status['symbols'])}")
        print(f"  * Estrategias: 6 activas")
        print(f"  * Auto-ejecucion: {'ACTIVADA' if status['auto_execute'] else 'DESACTIVADA'}")
        print(f"  * Monitor SL/TP: {'ACTIVADO' if status['auto_execute'] and status['mt5_connection_active'] else 'DESACTIVADO'}")
        
        # Mostrar posiciones si están disponibles
        if status['mt5_connection_active'] and status['positions_summary'] != "MT5 no conectado":
            print(f"\nPOSICIONES ACTUALES:")
            print(f"  {status['positions_summary']}")
        
        print(f"\nIniciando analisis continuo...")
        print(f"Presiona Ctrl+C para detener")
        print("="*60)
        print()
        
        # Iniciar el sistema
        generator.start()
        
    except KeyboardInterrupt:
        print("\n\nDeteniendo sistema por usuario...")
        if 'generator' in locals():
            generator.stop()
        print("Sistema detenido correctamente")
        
    except ImportError as e:
        print(f"\nError importando modulos: {e}")
        print("Asegurate de que todas las dependencias esten instaladas")
        
    except Exception as e:
        print(f"\nError ejecutando sistema: {e}")
        print("Revisa los logs para mas detalles")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error critico: {e}")
        input("Presiona Enter para cerrar...")