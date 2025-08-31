#!/usr/bin/env python
"""
INICIADOR DIRECTO DEL SISTEMA DE TRADING AUTOMATICO - ALGO TRADER V3
Sistema que inicia directamente sin confirmaciones para testing
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

def main():
    print("="*70)
    print("           ALGO TRADER V3 - INICIANDO SISTEMA COMPLETO")  
    print("="*70)
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Configurar encoding UTF-8 para Python
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # Importar las librerías necesarias
        sys.path.insert(0, str(project_dir))
        
        print("Importando modulos del sistema...")
        from src.signals.advanced_signal_generator import SignalGenerator
        print("Modulos importados correctamente")
        
        # Crear y configurar el generador CON AUTO-EJECUCION
        print("\nConfigurando generador de senales con IA...")
        print("MODO: TRADING AUTOMATICO ACTIVADO")
        print("SIMBOLOS: XAUUSD, EURUSD, GBPUSD, BTCUSD")
        print("MONITOR SL/TP: ACTIVADO")
        
        generator = SignalGenerator(
            symbols=['XAUUSD', 'EURUSD', 'GBPUSD', 'BTCUSD'], 
            auto_execute=True  # TRADING AUTOMATICO ACTIVADO
        )
        
        print("Generador creado correctamente")
        
        # Mostrar estado detallado
        print("\n" + "="*50)
        print("ESTADO DEL SISTEMA:")
        print("="*50)
        
        status = generator.get_status()
        print(f"Running: {status['running']}")
        print(f"Auto-execute: {status['auto_execute']}")
        print(f"MT5 Data Connected: {status['mt5_connected']}")
        print(f"MT5 Trading Connected: {status['mt5_connection_active']}")
        print(f"Telegram Active: {status['telegram_active']}")
        print(f"Symbols: {', '.join(status['symbols'])}")
        print(f"Signals Generated: {status['signals_generated']}")
        print(f"Trades Executed: {status['trades_executed']}")
        print(f"Positions Corrected: {status['positions_corrected']}")
        
        # Mostrar posiciones si están disponibles
        if status['mt5_connection_active']:
            print(f"\nPOSITIONS SUMMARY:")
            print(f"{status['positions_summary']}")
        
        print("\n" + "="*50)
        print("INICIANDO CICLO DE TRADING AUTOMATICO...")
        print("="*50)
        print("El sistema:")
        print("1. Analizara mercados cada 60 segundos")
        print("2. Generara senales con 6 estrategias de IA")
        print("3. EJECUTARA TRADES AUTOMATICAMENTE en MT5")
        print("4. Monitoreara y corregira posiciones sin SL/TP")
        print("5. Enviara notificaciones por Telegram")
        print()
        print("Presiona Ctrl+C para detener el sistema")
        print("="*70)
        print()
        
        # INICIAR EL SISTEMA COMPLETO
        generator.start()
        
    except KeyboardInterrupt:
        print("\n" + "="*50)
        print("DETENIENDO SISTEMA POR SOLICITUD DEL USUARIO")
        print("="*50)
        if 'generator' in locals():
            generator.stop()
        print("Sistema detenido correctamente")
        
    except ImportError as e:
        print(f"\nERROR IMPORTANDO MODULOS: {e}")
        print("Solucion: Instala las dependencias faltantes")
        
    except Exception as e:
        print(f"\nERROR EJECUTANDO SISTEMA: {e}")
        print("Revisa los logs en la carpeta 'logs/' para mas detalles")
        
        # Mostrar stack trace completo para debugging
        import traceback
        print("\nSTACK TRACE COMPLETO:")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR CRITICO: {e}")
        print("El sistema no pudo iniciarse correctamente")