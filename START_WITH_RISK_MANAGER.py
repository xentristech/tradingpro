#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA INTEGRADO CON RISK MANAGER
===================================
Ejecuta el bot de trading con gestión avanzada de riesgo
"""

import os
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))
sys.path.insert(0, str(project_path / 'src'))

def setup_environment():
    """Configurar el entorno"""
    # Verificar que existe el archivo .env
    env_path = project_path / 'configs' / '.env'
    if not env_path.exists():
        print("ERROR: No se encontró archivo de configuración")
        print("   Ejecuta primero: python configurar_sistema.py")
        sys.exit(1)
        
    # Cargar configuración
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    # Verificar configuración de Risk Manager
    enable_breakeven = os.getenv('ENABLE_BREAKEVEN', 'false').lower() == 'true'
    enable_trailing = os.getenv('ENABLE_TRAILING_STOP', 'false').lower() == 'true'
    
    if not enable_breakeven and not enable_trailing:
        print("WARNING: Risk Manager desactivado en configuración")
        print("   Para activarlo, edita configs/.env:")
        print("   ENABLE_BREAKEVEN=true")
        print("   ENABLE_TRAILING_STOP=true")
        
    return enable_breakeven or enable_trailing

def run_risk_manager():
    """Ejecutar el Risk Manager en thread separado"""
    try:
        from src.risk.advanced_risk_manager import AdvancedRiskManager
        print("[OK] Iniciando Advanced Risk Manager...")
        manager = AdvancedRiskManager()
        manager.start()
    except Exception as e:
        print(f"[ERROR] Error en Risk Manager: {e}")

def run_trading_bot():
    """Ejecutar el bot de trading principal"""
    try:
        # Importar el bot principal
        from src.signals.advanced_signal_generator import AdvancedSignalGenerator
        from src.broker.mt5_connection import MT5Connection
        
        print("[OK] Iniciando Bot de Trading...")
        
        # Configurar componentes
        mt5_conn = MT5Connection()
        if not mt5_conn.connect():
            print("[ERROR] No se pudo conectar a MT5")
            return
            
        signal_gen = AdvancedSignalGenerator()
        
        # Loop principal
        cycle = 0
        while True:
            cycle += 1
            print(f"\n[Ciclo {cycle:04d}] {datetime.now().strftime('%H:%M:%S')} - Analizando mercados...")
            
            # Generar señales
            signals = signal_gen.generate_signals()
            
            if signals:
                print(f"  -> {len(signals)} señales generadas")
                # Aquí ejecutarías las señales
            else:
                print("  -> Sin señales en este ciclo")
                
            # Esperar antes del próximo ciclo
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nBot de trading detenido")
    except Exception as e:
        print(f"[ERROR] Error en bot de trading: {e}")

def main():
    """Función principal"""
    print("="*60)
    print("  ALGO TRADER V3 - SISTEMA INTEGRADO")
    print("  Bot + Risk Manager (Breakeven & Trailing)")
    print("="*60)
    print()
    
    # Configurar entorno
    risk_manager_enabled = setup_environment()
    
    threads = []
    
    # Thread para Risk Manager (si está activado)
    if risk_manager_enabled:
        risk_thread = threading.Thread(target=run_risk_manager, daemon=True)
        risk_thread.start()
        threads.append(risk_thread)
        print("[OK] Risk Manager iniciado en background")
    
    # Thread para Bot de Trading
    bot_thread = threading.Thread(target=run_trading_bot, daemon=True)
    bot_thread.start()
    threads.append(bot_thread)
    print("[OK] Bot de Trading iniciado")
    
    print("\n" + "="*60)
    print("Sistema ejecutándose. Presiona Ctrl+C para detener")
    print("="*60)
    
    try:
        # Mantener el programa principal vivo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nDeteniendo sistema...")
        time.sleep(2)
        print("[OK] Sistema detenido correctamente")
        sys.exit(0)

if __name__ == "__main__":
    main()
