#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de reconexión automática de MT5
"""

import os
import sys
from pathlib import Path

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_mt5_reconnection():
    print("=" * 60)
    print("      TEST RECONEXION AUTOMATICA MT5")
    print("=" * 60)
    
    try:
        from src.broker.mt5_connection import MT5Connection
        
        print("\n1. Creando conexión MT5...")
        mt5_conn = MT5Connection()
        
        print(f"   Login: {mt5_conn.login}")
        print(f"   Servidor: {mt5_conn.server}")
        print(f"   Estado inicial: {mt5_conn.connected}")
        
        print("\n2. Probando ensure_connected()...")
        result = mt5_conn.ensure_connected()
        print(f"   Resultado: {result}")
        print(f"   Estado después: {mt5_conn.connected}")
        
        if result:
            print("\n3. Simulando desconexión...")
            mt5_conn.connected = False
            print(f"   Estado forzado: {mt5_conn.connected}")
            
            print("\n4. Probando reconexión automática...")
            reconnect_result = mt5_conn.ensure_connected()
            print(f"   Reconexión: {reconnect_result}")
            print(f"   Estado final: {mt5_conn.connected}")
            
            if reconnect_result:
                print("\n   [OK] Reconexión automática funcionando")
            else:
                print("\n   [ERROR] Reconexión falló")
        
        # Test con SignalGenerator
        print("\n5. Probando con SignalGenerator...")
        from src.signals.advanced_signal_generator import SignalGenerator
        
        generator = SignalGenerator(symbols=['BTCUSD'], auto_execute=False)
        
        # Intentar habilitar auto-trading para inicializar MT5
        print("   Habilitando auto-trading...")
        mt5_enabled = generator.enable_auto_trading()
        print(f"   MT5 habilitado: {mt5_enabled}")
        
        if generator.mt5_connection:
            print(f"   Estado MT5: {generator.mt5_connection.connected}")
            
            print("\n6. Probando check_and_reconnect_mt5()...")
            check_result = generator.check_and_reconnect_mt5()
            print(f"   Verificación: {check_result}")
            
        print("\n[OK] Test de reconexión completado")
        
    except Exception as e:
        print(f"\n[ERROR] Error en test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mt5_reconnection()