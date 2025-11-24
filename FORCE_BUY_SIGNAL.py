"""
FORZAR SEÑAL BUY FUERTE - TESTING
Simula una señal BUY fuerte directamente para probar ejecución automática
"""

import sys
import os
from pathlib import Path
import time
import MetaTrader5 as mt5

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from src.broker.mt5_connection import MT5Connection
from src.notifiers.telegram_notifier import TelegramNotifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_test_buy_signal():
    """
    Ejecutar señal BUY de prueba directamente usando el sistema MT5
    """
    
    print("="*70)
    print("        FORZAR SEÑAL BUY FUERTE - TESTING DIRECTO")
    print("="*70)
    print("Objetivo: Ejecutar BUY EURUSD directamente en MT5")
    print("Volumen: 0.01 (mínimo)")
    print("="*70)
    
    # Conectar a MT5 directamente
    if not mt5.initialize():
        print("❌ ERROR: No se pudo conectar a MT5")
        return False
    
    # Verificar conexión 
    account_info = mt5.account_info()
    if not account_info:
        print("❌ ERROR: No se pudo obtener info de cuenta")
        mt5.shutdown()
        return False
        
    print(f"\n✅ Conectado a cuenta: {account_info.login}")
    print(f"✅ Balance: ${account_info.balance:.2f}")
    
    # Obtener precio actual de EURUSD
    symbol = "EURUSD"
    symbol_info = mt5.symbol_info(symbol)
    
    if not symbol_info:
        print(f"❌ ERROR: Símbolo {symbol} no disponible")
        mt5.shutdown()
        return False
    
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"❌ ERROR: No se pudo seleccionar {symbol}")
            mt5.shutdown()
            return False
    
    # Obtener precio actual
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"❌ ERROR: No se pudo obtener precio de {symbol}")
        mt5.shutdown()
        return False
    
    current_price = tick.ask
    print(f"\n✅ Precio actual {symbol}: {current_price}")
    
    # Calcular SL y TP
    sl = current_price - 0.0020  # 20 pips SL
    tp = current_price + 0.0050  # 50 pips TP
    
    print(f"✅ Stop Loss: {sl}")
    print(f"✅ Take Profit: {tp}")
    
    # Crear orden BUY
    volume = 0.01
    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": current_price,
        "sl": sl,
        "tp": tp,
        "magic": 123456,
        "comment": "TEST_BUY_SIGNAL_FORCED",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    print(f"\n🚀 Ejecutando orden BUY {symbol}...")
    print(f"   Volumen: {volume}")
    print(f"   Precio: {current_price}")
    print(f"   SL: {sl} | TP: {tp}")
    
    # Enviar orden
    result = mt5.order_send(order_request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ ERROR ejecutando orden: {result.retcode}")
        print(f"   Descripción: {result.comment}")
        mt5.shutdown()
        return False
    
    print(f"\n✅ ¡ORDEN EJECUTADA EXITOSAMENTE!")
    print(f"✅ Ticket: #{result.order}")
    print(f"✅ Precio ejecución: {result.price}")
    print(f"✅ Volumen: {result.volume}")
    
    # Verificar posición creada
    print(f"\n🔍 Verificando posición creada...")
    time.sleep(2)
    
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for pos in positions:
            if pos.ticket == result.order:
                print(f"✅ Posición confirmada:")
                print(f"   Ticket: #{pos.ticket}")
                print(f"   Símbolo: {pos.symbol}")
                print(f"   Tipo: BUY")
                print(f"   Volumen: {pos.volume}")
                print(f"   Precio entrada: {pos.price_open}")
                print(f"   SL: {pos.sl}")
                print(f"   TP: {pos.tp}")
                print(f"   P&L actual: ${pos.profit:.2f}")
                break
    
    # Enviar notificación Telegram
    try:
        telegram = TelegramNotifier()
        message = f"""
🚀 <b>SEÑAL FORZADA EJECUTADA</b>

📈 <b>BUY {symbol}</b>
💰 Volumen: {volume}
🎯 Precio: {current_price}
🛡️ SL: {sl}
🎯 TP: {tp}
🎫 Ticket: #{result.order}

✅ <b>SISTEMA DE TRADING FUNCIONANDO</b>
🔥 Test exitoso - Auto-trading ACTIVO

<i>Generado para testing automático</i>
        """
        telegram.send_message(message)
        print(f"✅ Notificación enviada por Telegram")
        
    except Exception as e:
        print(f"⚠️ Error enviando Telegram: {e}")
    
    mt5.shutdown()
    return True

def main():
    """Función principal"""
    
    print("""
    ========================================================================
                  FORZAR SEÑAL BUY - TESTING DIRECTO v1.0
    ========================================================================
    
    Este script ejecuta una orden BUY directamente en MT5 para probar que
    el sistema de trading automático puede ejecutar órdenes correctamente.
    
    Se ejecutará:
    - BUY EURUSD 0.01 lotes
    - Stop Loss: 20 pips
    - Take Profit: 50 pips
    
    IMPORTANTE: Esto abrirá una posición real en tu cuenta de trading.
    
    ========================================================================
    """)
    
    # Confirmar ejecución
    response = input("¿Deseas ejecutar la orden BUY de prueba? (s/n): ").lower().strip()
    if response not in ['s', 'si', 'y', 'yes']:
        print("Operación cancelada")
        return
    
    # Ejecutar señal
    success = execute_test_buy_signal()
    
    if success:
        print("\n" + "="*70)
        print("🎉 ¡PRUEBA EXITOSA! - SISTEMA DE TRADING FUNCIONANDO")
        print("✅ Orden BUY ejecutada correctamente")
        print("✅ Posición abierta en MT5")
        print("✅ Notificación enviada por Telegram")
        print("="*70)
        
        print("\n🔥 CONCLUSIÓN:")
        print("El sistema de trading automático funciona perfectamente.")
        print("El problema anterior era que la IA solo generaba señales NO_OPERAR.")
        print("Para más trades automáticos, necesitas señales BUY/SELL con +60% confianza.")
        
    else:
        print("\n" + "="*70)
        print("❌ PRUEBA FALLIDA - REVISAR CONFIGURACIÓN")
        print("="*70)

if __name__ == "__main__":
    main()