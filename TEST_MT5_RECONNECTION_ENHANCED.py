#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test mejorado de reconexión automática de MT5
Detecta cuando MT5 se cierra y lo reconecta automáticamente
"""

import os
import sys
import time
from pathlib import Path

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_mt5_reconnection_enhanced():
    print("=" * 70)
    print("      TEST RECONEXION AUTOMATICA MT5 - ENHANCED")
    print("=" * 70)
    
    try:
        from src.broker.mt5_connection import MT5Connection
        
        print("\n1. Creando conexión MT5...")
        mt5_conn = MT5Connection()
        
        print(f"   Login: {mt5_conn.login}")
        print(f"   Servidor: {mt5_conn.server}")
        
        print("\n2. Conectando inicialmente...")
        initial_connection = mt5_conn.connect()
        print(f"   Conexión inicial: {initial_connection}")
        
        if not initial_connection:
            print("   [ERROR] No se pudo conectar inicialmente")
            return
        
        print("\n3. INICIANDO MONITORE CONTINUO...")
        print("   - Cada 3 segundos verificará la conexión")
        print("   - CIERRE MT5 MANUALMENTE para probar la reconexión")
        print("   - Presione Ctrl+C para salir")
        print("   " + "-" * 50)
        
        cycle = 0
        connection_lost_detected = False
        
        while True:
            cycle += 1
            current_time = time.strftime('%H:%M:%S')
            
            print(f"\n[{cycle:03d}] {current_time} - Verificando conexión MT5...")
            
            # Usar el método mejorado de verificación
            was_connected = mt5_conn.connected
            is_connected = mt5_conn.ensure_connected()
            
            if not was_connected and not is_connected:
                print("   [ESTADO] Sin conexión inicial")
            elif was_connected and not is_connected:
                print("   [ALERTA] CONEXION PERDIDA - MT5 cerrado detectado!")
                print("   [ACCION] Intentando reconectar...")
                connection_lost_detected = True
            elif not was_connected and is_connected:
                if connection_lost_detected:
                    print("   [EXITO] RECONEXION AUTOMATICA COMPLETADA!")
                    print("   [INFO] MT5 reconectado exitosamente")
                    connection_lost_detected = False
                else:
                    print("   [EXITO] Conexión establecida")
            else:
                print("   [OK] Conexión activa")
            
            # Mostrar información adicional si está conectado
            if is_connected and mt5_conn.account_info:
                print(f"        Balance: ${mt5_conn.account_info.balance:.2f}")
                print(f"        Estado MT5: Conectado a {mt5_conn.server}")
            
            # Esperar 3 segundos antes del próximo check
            print("   Esperando 3 segundos...")
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Test detenido por el usuario")
        if 'mt5_conn' in locals():
            mt5_conn.disconnect()
        
    except Exception as e:
        print(f"\n[ERROR] Error en test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mt5_reconnection_enhanced()