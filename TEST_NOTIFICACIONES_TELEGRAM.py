#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST NOTIFICACIONES TELEGRAM
============================
Probar notificaciones de breakeven y trailing stop
"""

import MetaTrader5 as mt5
import sys
from pathlib import Path

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.notifiers.telegram_notifier import TelegramNotifier
except ImportError as e:
    print(f"Error importando TelegramNotifier: {e}")
    TelegramNotifier = None

def test_telegram_notifications():
    """Probar notificaciones de Telegram"""
    print("="*60)
    print("    TEST DE NOTIFICACIONES TELEGRAM")
    print("="*60)
    
    # Inicializar Telegram
    telegram = TelegramNotifier() if TelegramNotifier else None
    
    if not telegram:
        print("ERROR: No se pudo inicializar TelegramNotifier")
        return
    
    if not telegram.is_active:
        print("ERROR: Telegram no está activo")
        return
    
    print("OK: Telegram conectado")
    print()
    
    # TEST 1: Notificación de breakeven
    print("TEST 1: Enviando notificación de breakeven...")
    result1 = telegram.send_breakeven_notification(
        symbol="XAUUSDm",
        ticket=123456,
        old_sl=3630.00000,
        new_sl=3635.00000,
        pips_profit=15.5
    )
    
    if result1:
        print("OK: Notificación de breakeven enviada")
    else:
        print("ERROR: No se pudo enviar notificación de breakeven")
    
    print()
    
    # TEST 2: Notificación de trailing stop
    print("TEST 2: Enviando notificación de trailing stop...")
    result2 = telegram.send_trailing_notification(
        symbol="BTCUSDm",
        ticket=654321,
        old_sl=110000.00000,
        new_sl=110500.00000,
        pips_profit=25.3,
        distance_pips=15
    )
    
    if result2:
        print("OK: Notificación de trailing enviada")
    else:
        print("ERROR: No se pudo enviar notificación de trailing")
    
    print()
    
    # TEST 3: Resumen de protecciones
    print("TEST 3: Enviando resumen de protecciones...")
    result3 = telegram.send_protection_summary(
        breakeven_count=2,
        trailing_count=1,
        total_positions=5
    )
    
    if result3:
        print("OK: Resumen de protecciones enviado")
    else:
        print("ERROR: No se pudo enviar resumen")
    
    print()
    print("="*60)
    
    if all([result1, result2, result3]):
        print("EXITO: Todas las notificaciones funcionan correctamente")
        print("El sistema enviará alertas por Telegram cuando aplique breakeven o trailing")
    else:
        print("PROBLEMA: Algunas notificaciones fallaron")
        print("Revisar configuración de Telegram")
    
    print("="*60)

def test_real_positions():
    """Probar con posiciones reales y enviar notificación si hay alguna acción"""
    print("="*60)
    print("    TEST CON POSICIONES REALES")
    print("="*60)
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    telegram = TelegramNotifier() if TelegramNotifier else None
    
    if not telegram or not telegram.is_active:
        print("ERROR: Telegram no disponible")
        mt5.shutdown()
        return
    
    positions = mt5.positions_get()
    
    if not positions:
        print("No hay posiciones abiertas para probar")
        mt5.shutdown()
        return
    
    print(f"Encontradas {len(positions)} posiciones")
    
    # Buscar una posición con ganancia para simular notificación
    for pos in positions:
        if pos.profit > 0:
            print(f"Enviando notificación de prueba para {pos.symbol} #{pos.ticket}")
            
            # Simular notificación de breakeven
            telegram.send_breakeven_notification(
                symbol=pos.symbol,
                ticket=pos.ticket,
                old_sl=pos.sl,
                new_sl=pos.sl + 0.0001,  # Simular cambio
                pips_profit=pos.profit / 10  # Estimado
            )
            break
    
    mt5.shutdown()
    print("Test completado")

if __name__ == "__main__":
    print("OPCIONES DE TEST:")
    print("1. Test básico de notificaciones")
    print("2. Test con posiciones reales") 
    
    opcion = input("Selecciona (1-2): ").strip()
    
    if opcion == '1':
        test_telegram_notifications()
    elif opcion == '2':
        test_real_positions()
    else:
        test_telegram_notifications()