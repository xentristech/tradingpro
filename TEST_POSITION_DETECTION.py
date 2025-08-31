#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de detección y corrección de posiciones sin SL/TP
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

class MockPosition:
    """Simula una posición de MT5"""
    def __init__(self, ticket, symbol, type_pos, volume, price_open, sl=0.0, tp=0.0, profit=0.0):
        self.ticket = ticket
        self.symbol = symbol
        self.type = type_pos  # 0 = BUY, 1 = SELL
        self.volume = volume
        self.price_open = price_open
        self.sl = sl
        self.tp = tp
        self.profit = profit

def test_position_detection():
    print("=" * 70)
    print("      TEST DETECCION Y CORRECCION DE POSICIONES")
    print("=" * 70)
    
    try:
        from src.signals.advanced_signal_generator import SignalGenerator
        
        print("\n1. Creando generador de señales con Mock MT5...")
        
        # Crear generador sin auto_execute para evitar problemas MT5
        generator = SignalGenerator(symbols=['BTCUSD'], auto_execute=False)
        
        # Crear mock de conexión MT5
        mock_mt5 = Mock()
        mock_mt5.connected = True
        mock_mt5.ensure_connected.return_value = True
        
        # Crear posiciones de prueba
        positions_test = [
            # Posición SIN SL ni TP (debe detectar y corregir)
            MockPosition(
                ticket=12345,
                symbol="BTCUSD", 
                type_pos=0,  # BUY
                volume=0.1,
                price_open=67500.0,
                sl=0.0,      # SIN STOP LOSS
                tp=0.0,      # SIN TAKE PROFIT
                profit=-25.50
            ),
            # Posición CON SL pero sin TP (debe detectar y corregir)
            MockPosition(
                ticket=12346,
                symbol="EURUSD",
                type_pos=1,  # SELL
                volume=0.05,
                price_open=1.0850,
                sl=1.0900,   # CON STOP LOSS
                tp=0.0,      # SIN TAKE PROFIT
                profit=15.20
            ),
            # Posición CON SL y TP (NO debe corregir)
            MockPosition(
                ticket=12347,
                symbol="XAUUSD",
                type_pos=0,  # BUY
                volume=0.02,
                price_open=2650.0,
                sl=2630.0,   # CON STOP LOSS
                tp=2680.0,   # CON TAKE PROFIT
                profit=8.75
            )
        ]
        
        # Configurar mock para retornar posiciones
        mock_mt5.get_positions.return_value = positions_test
        mock_mt5.modify_position.return_value = True
        
        # Asignar mock al generador
        generator.mt5_connection = mock_mt5
        
        # Mock Telegram para capturar notificaciones
        mock_telegram = Mock()
        mock_telegram.is_active = True
        generator.telegram = mock_telegram
        
        print(f"   [OK] Generador configurado con {len(positions_test)} posiciones de prueba")
        
        print("\n2. Ejecutando monitoreo de posiciones...")
        
        # Ejecutar monitoreo
        corrected_count = generator.monitor_and_correct_positions()
        
        print(f"\n3. RESULTADOS:")
        print(f"   Posiciones corregidas: {corrected_count}")
        print(f"   Total correcciones acumuladas: {generator.positions_corrected}")
        
        print(f"\n4. VERIFICANDO DETECCIÓN:")
        
        # Verificar llamadas al mock
        positions_calls = mock_mt5.get_positions.call_count
        modify_calls = mock_mt5.modify_position.call_count
        telegram_calls = mock_telegram.send_message.call_count
        
        print(f"   get_positions() llamado: {positions_calls} veces")
        print(f"   modify_position() llamado: {modify_calls} veces")
        print(f"   Telegram enviado: {telegram_calls} mensajes")
        
        print(f"\n5. DETALLE DE POSICIONES ANALIZADAS:")
        
        for i, pos in enumerate(positions_test, 1):
            pos_type = "BUY" if pos.type == 0 else "SELL"
            sl_status = "CON SL" if pos.sl != 0.0 else "SIN SL"
            tp_status = "CON TP" if pos.tp != 0.0 else "SIN TP"
            needs_correction = (pos.sl == 0.0) or (pos.tp == 0.0)
            
            print(f"   Pos #{i}: {pos.symbol} {pos_type} - {sl_status}, {tp_status}")
            print(f"            Ticket: #{pos.ticket} | Corrección: {'SÍ' if needs_correction else 'NO'}")
        
        print(f"\n6. VERIFICACIÓN DE MENSAJES TELEGRAM:")
        
        if telegram_calls > 0:
            print(f"   [OK] {telegram_calls} notificaciones enviadas correctamente")
            
            # Mostrar contenido de los mensajes
            for i, call in enumerate(mock_telegram.send_message.call_args_list, 1):
                message = call[0][0]  # Primer argumento del call
                print(f"\n   Mensaje #{i}:")
                print("   " + "-" * 40)
                for line in message.split('\n')[:5]:  # Primeras 5 líneas
                    print(f"   {line}")
                print("   ...")
        else:
            print("   [WARNING] No se enviaron notificaciones")
        
        print(f"\n7. RESUMEN FINAL:")
        
        expected_corrections = sum(1 for pos in positions_test if pos.sl == 0.0 or pos.tp == 0.0)
        
        print(f"   Posiciones esperadas a corregir: {expected_corrections}")
        print(f"   Posiciones realmente corregidas: {corrected_count}")
        
        if corrected_count == expected_corrections:
            print("   [SUCCESS] PRUEBA EXITOSA - Sistema detecta y corrige correctamente")
        else:
            print("   [FAILED] PRUEBA FALLIDA - Discrepancia en detección")
        
        print("\n" + "=" * 70)
        print("                    PRUEBA COMPLETADA")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] Error en prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_position_detection()