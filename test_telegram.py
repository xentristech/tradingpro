#!/usr/bin/env python
"""
TEST DE TELEGRAM - ALGO TRADER V3
==================================
Prueba las notificaciones de Telegram
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def test_telegram():
    print("""
╔════════════════════════════════════════════════════════════╗
║            TEST DE NOTIFICACIONES TELEGRAM                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar configuración
    print("\n1️⃣ Verificando configuración...")
    
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
            
        if 'TELEGRAM_TOKEN=7872232379' in content:
            print("  ✅ Token encontrado")
        else:
            print("  ❌ Token no configurado")
            
        if 'TELEGRAM_CHAT_ID=-1002766499765' in content:
            print("  ✅ Chat ID encontrado")
        else:
            print("  ❌ Chat ID no configurado")
    else:
        print("  ❌ Archivo .env no encontrado")
        return
        
    # Intentar importar el notificador
    print("\n2️⃣ Importando notificador...")
    
    try:
        from src.notifiers.telegram_notifier import TelegramNotifier
        print("  ✅ Módulo importado")
    except ImportError as e:
        print(f"  ❌ Error importando: {e}")
        return
        
    # Crear instancia
    print("\n3️⃣ Conectando con Telegram...")
    
    notifier = TelegramNotifier()
    
    if not notifier.is_active:
        print("  ❌ No se pudo conectar con Telegram")
        return
        
    print("  ✅ Conectado exitosamente")
    
    # Enviar mensajes de prueba
    print("\n4️⃣ Enviando mensajes de prueba...")
    
    # Mensaje de bienvenida
    print("\n  📤 Enviando mensaje de bienvenida...")
    notifier.send_message(
        "🎉 *TEST EXITOSO DE TELEGRAM*\n\n"
        "El sistema de notificaciones está funcionando correctamente.\n"
        f"Hora: {datetime.now().strftime('%H:%M:%S')}",
        parse_mode='Markdown'
    )
    
    # Señal de prueba
    print("  📤 Enviando señal de trading...")
    test_signal = {
        'symbol': 'XAUUSD',
        'type': 'BUY',
        'price': 2650.50,
        'strength': 0.92,
        'tp': 2655.00,
        'sl': 2648.00,
        'strategy': 'Multi-Strategy AI',
        'timeframe': 'M5',
        'reason': 'Confluencia de 4 indicadores + patrón bullish'
    }
    notifier.send_signal(test_signal)
    
    # Trade update
    print("  📤 Enviando actualización de trade...")
    test_trade = {
        'symbol': 'EURUSD',
        'ticket': 123456,
        'type': 'SELL',
        'status': 'opened',
        'open_price': 1.0850,
        'current_price': 1.0845,
        'volume': 0.10,
        'profit': 5.00,
        'profit_percent': 0.46
    }
    notifier.send_trade_update(test_trade)
    
    # Alerta
    print("  📤 Enviando alerta...")
    notifier.send_alert(
        'warning',
        'Drawdown alcanzó -15%\nSe recomienda revisar posiciones abiertas',
        critical=True
    )
    
    # Reporte diario
    print("  📤 Enviando reporte de ejemplo...")
    test_report = {
        'total_trades': 15,
        'winning_trades': 11,
        'losing_trades': 4,
        'win_rate': 73.33,
        'total_profit': 450.50,
        'best_trade': 120.00,
        'worst_trade': -45.00,
        'avg_profit': 30.03,
        'balance': 10450.50,
        'equity': 10445.00,
        'margin': 150.00,
        'drawdown': 5.2,
        'signals_generated': 45,
        'signals_executed': 15,
        'signal_accuracy': 73.33
    }
    notifier.send_daily_report(test_report)
    
    print("\n✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("\n📱 Revisa tu Telegram, deberías ver 5 mensajes:")
    print("  1. Mensaje de bienvenida")
    print("  2. Señal de trading")
    print("  3. Actualización de trade")
    print("  4. Alerta de sistema")
    print("  5. Reporte diario")
    
    print("\n" + "="*60)
    print("CONFIGURACIÓN ACTUAL:")
    print(f"  • Bot: @{notifier.token.split(':')[0]}")
    print(f"  • Chat ID: {notifier.chat_id}")
    print("  • Estado: ✅ ACTIVO")
    print("="*60)

if __name__ == "__main__":
    try:
        test_telegram()
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPresiona Enter para salir...")
