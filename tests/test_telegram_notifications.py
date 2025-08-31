"""
Test de Sistema de Notificaciones Telegram
Prueba todas las funcionalidades de notificación implementadas
"""
import asyncio
import logging
from datetime import datetime
from notifiers.telegram_notifier import (
    TelegramNotifier, 
    send_signal_notification,
    send_execution_notification,
    send_error_notification,
    send_telegram_message
)

# Configurar logging
logging.basicConfig(level=logging.INFO)

async def test_all_notifications():
    """Prueba todas las notificaciones implementadas"""
    
    notifier = TelegramNotifier()
    
    if not notifier.enabled:
        print("❌ Telegram no está configurado correctamente")
        print("   Configura TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en .env")
        return
    
    print("🚀 Iniciando prueba de notificaciones Telegram...")
    
    # 1. Test señal de trading
    print("\n📊 Enviando señal de COMPRA...")
    signal_data = {
        'symbol': 'BTCUSDm',
        'direction': 'BUY',
        'strength': 0.85,
        'confidence': 0.78,
        'price': 113245.67,
        'reasons': [
            'Golden Cross en 15min',
            'RSI sobreventa (28.5)',
            'Ruptura de resistencia',
            'Volumen alto confirmando breakout',
            'MACD cruzando al alza'
        ],
        'entry_price': 113250.00,
        'stop_loss': 112800.00,
        'take_profit': 114200.00
    }
    await notifier.send_signal_alert(signal_data)
    await asyncio.sleep(2)
    
    # 2. Test señal de VENTA
    print("📊 Enviando señal de VENTA...")
    signal_data['direction'] = 'SELL'
    signal_data['reasons'] = [
        'Death Cross en 1H',
        'RSI sobrecompra (72.8)',
        'Divergencia bajista',
        'Rechazo en resistencia clave'
    ]
    await notifier.send_signal_alert(signal_data)
    await asyncio.sleep(2)
    
    # 3. Test ejecución exitosa
    print("\n✅ Enviando notificación de ejecución exitosa...")
    execution_data = {
        'success': True,
        'symbol': 'BTCUSDm',
        'order_type': 'BUY',
        'volume': 0.1,
        'price': 113250.45,
        'ticket': 123456789,
        'magic': 20250817,
        'retcode': 10009
    }
    await notifier.send_execution_result(execution_data)
    await asyncio.sleep(2)
    
    # 4. Test error de ejecución
    print("❌ Enviando notificación de error de ejecución...")
    execution_data = {
        'success': False,
        'symbol': 'BTCUSDm',
        'order_type': 'SELL',
        'volume': 0.1,
        'price': 113100.22,
        'retcode': 10006,
        'error_message': 'Fondos insuficientes para la operación'
    }
    await notifier.send_execution_result(execution_data)
    await asyncio.sleep(2)
    
    # 5. Test ejecución DEMO
    print("🧪 Enviando notificación de ejecución DEMO...")
    execution_data = {
        'success': True,
        'symbol': 'BTCUSDm',
        'order_type': 'BUY (DEMO)',
        'volume': 0.05,
        'price': 113350.78,
        'ticket': 'DEMO',
        'magic': 20250817,
        'retcode': 'DEMO_SUCCESS'
    }
    await notifier.send_execution_result(execution_data)
    await asyncio.sleep(2)
    
    # 6. Test alerta de error del sistema
    print("\n⚠️ Enviando alerta de error del sistema...")
    error_data = {
        'type': 'CONNECTION_ERROR',
        'message': 'No se pudo conectar con MT5',
        'location': 'pro_trading_bot.py:initialize_mt5()',
        'action': 'Reintentando conexión en 30 segundos'
    }
    await notifier.send_error_alert(error_data)
    await asyncio.sleep(2)
    
    print("\n🎉 ¡Prueba completa! Verifica tu chat de Telegram.")
    print(f"📱 Chat ID: {notifier.chat_id}")

def test_sync_functions():
    """Prueba funciones síncronas"""
    print("\n🔄 Probando funciones síncronas...")
    
    # Test mensaje simple
    send_telegram_message("🧪 Mensaje de prueba sincrónico")
    
    # Test señal
    signal_data = {
        'symbol': 'BTCUSDm',
        'direction': 'NEUTRAL',
        'strength': 0.2,
        'confidence': 0.45,
        'price': 113500.00,
        'reasons': ['Sin confluencia clara de indicadores'],
        'entry_price': 0,
        'stop_loss': 0,
        'take_profit': 0
    }
    send_signal_notification(signal_data)

if __name__ == "__main__":
    print("="*60)
    print("🤖 TEST DE NOTIFICACIONES TELEGRAM")
    print("   AlgoTrader v3.0")
    print("="*60)
    
    # Test asíncrono
    asyncio.run(test_all_notifications())
    
    # Test síncrono
    test_sync_functions()
    
    print("\n✅ Pruebas completadas!")
    print("   Si no recibes mensajes, verifica:")
    print("   - TELEGRAM_TOKEN en .env")
    print("   - TELEGRAM_CHAT_ID en .env")
    print("   - Bot agregado al chat")
    print("   - Bot con permisos para enviar mensajes")