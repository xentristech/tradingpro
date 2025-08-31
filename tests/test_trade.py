#!/usr/bin/env python3
"""
TEST TRADER - Forzar una operación para verificar el sistema
"""
import MetaTrader5 as mt5
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')

def test_trade():
    """Forzar una operación de prueba"""
    
    # Conectar MT5
    if not mt5.initialize():
        logging.error("No se pudo conectar a MT5")
        return False
    
    # Información de cuenta
    account = mt5.account_info()
    if not account:
        logging.error("No se pudo obtener cuenta")
        return False
    
    logging.info(f"Cuenta: {account.login} | Balance: ${account.balance:.2f}")
    
    # Verificar posiciones actuales
    positions = mt5.positions_get()
    logging.info(f"Posiciones actuales: {len(positions) if positions else 0}")
    
    # Verificar símbolos disponibles
    symbols = mt5.symbols_get()
    available_symbols = [s.name for s in symbols if s.visible and 'EUR' in s.name or 'BTC' in s.name]
    logging.info(f"Símbolos disponibles: {available_symbols[:5]}")  # Mostrar primeros 5
    
    # Seleccionar símbolo disponible
    symbol = "EURUSD"
    if available_symbols and "EURUSD" not in available_symbols:
        symbol = available_symbols[0]  # Usar el primer símbolo disponible
        logging.info(f"EURUSD no disponible, usando: {symbol}")
    
    # Verificar símbolo
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logging.error(f"No se pudo obtener tick para {symbol}")
        return False
    
    logging.info(f"{symbol} - Bid: {tick.bid:.5f} | Ask: {tick.ask:.5f}")
    
    # Preparar orden de COMPRA pequeña
    volume = 0.01  # Volumen mínimo
    price = tick.ask
    sl = price - (20 * 0.0001)  # SL 20 pips
    tp = price + (30 * 0.0001)  # TP 30 pips
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 99999999,  # Magic number especial para prueba
        "comment": "TEST TRADE - Verificacion sistema",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    logging.info(f"Enviando orden: BUY {volume} {symbol} a {price:.5f}")
    logging.info(f"SL: {sl:.5f} | TP: {tp:.5f}")
    
    # Enviar notificación Telegram
    try:
        from notifiers.telegram_notifier import send_telegram_message
        send_telegram_message(f"PRUEBA: Ejecutando orden BUY {volume} {symbol} a {price:.5f} - Verificando funcionamiento del sistema")
    except:
        pass
    
    # Ejecutar orden
    result = mt5.order_send(request)
    
    if result:
        logging.info(f"Respuesta recibida - Código: {result.retcode}")
        logging.info(f"Comentario: {result.comment}")
        logging.info(f"Request ID: {result.request_id}")
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"✅ ORDEN EJECUTADA EXITOSAMENTE!")
            logging.info(f"   Ticket: {result.order}")
            logging.info(f"   Precio: {result.price:.5f}")
            logging.info(f"   Volumen: {result.volume}")
            
            # Notificación de éxito
            try:
                send_telegram_message(f"✅ ORDEN EJECUTADA: BUY {result.volume} {symbol} - Ticket: {result.order} - Precio: {result.price:.5f}")
            except:
                pass
            
            return True
        else:
            logging.error(f"❌ ERROR EN ORDEN: {result.retcode}")
            logging.error(f"   Comentario: {result.comment}")
            
            # Notificación de error
            try:
                send_telegram_message(f"❌ ERROR: No se pudo ejecutar orden - Código: {result.retcode} - {result.comment}")
            except:
                pass
            
            return False
    else:
        logging.error("❌ No se recibió respuesta del servidor")
        return False

def show_current_positions():
    """Mostrar posiciones actuales"""
    if not mt5.initialize():
        return
    
    positions = mt5.positions_get()
    
    if positions:
        logging.info(f"\n=== POSICIONES ACTUALES ({len(positions)}) ===")
        for pos in positions:
            logging.info(f"Ticket: {pos.ticket} | {pos.symbol} | {'BUY' if pos.type==0 else 'SELL'} | {pos.volume} | P&L: ${pos.profit:.2f}")
    else:
        logging.info("No hay posiciones abiertas")
    
    mt5.shutdown()

if __name__ == "__main__":
    logging.info("=" * 50)
    logging.info("TEST TRADER - VERIFICACIÓN DEL SISTEMA")
    logging.info("=" * 50)
    
    # Mostrar posiciones actuales
    show_current_positions()
    
    # Ejecutar trade de prueba
    logging.info("\n🚀 EJECUTANDO TRADE DE PRUEBA...")
    
    if test_trade():
        logging.info("✅ SISTEMA VERIFICADO - El código está funcionando correctamente")
    else:
        logging.error("❌ SISTEMA CON PROBLEMAS - Revisar configuración")
    
    # Mostrar posiciones después
    logging.info("\n📊 ESTADO FINAL:")
    show_current_positions()
    
    logging.info("=" * 50)