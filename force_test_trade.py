#!/usr/bin/env python3
"""
FORCE TEST TRADE - Cerrar una posición y ejecutar una nueva para verificar
"""
import MetaTrader5 as mt5
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')

def close_position(ticket):
    """Cerrar posición específica"""
    try:
        position = None
        positions = mt5.positions_get()
        if positions:
            for pos in positions:
                if pos.ticket == ticket:
                    position = pos
                    break
        
        if not position:
            logging.error(f"Posición {ticket} no encontrada")
            return False
        
        # Preparar orden de cierre
        if position.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(position.symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).ask
        
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": position.magic,
            "comment": "CIERRE TEST",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(close_request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"✅ Posición {ticket} cerrada exitosamente")
            return True
        else:
            error_msg = result.comment if result else "Sin respuesta"
            logging.error(f"❌ Error cerrando posición: {error_msg}")
            return False
            
    except Exception as e:
        logging.error(f"Error cerrando posición {ticket}: {e}")
        return False

def force_trade():
    """Forzar trade después de cerrar una posición"""
    
    if not mt5.initialize():
        logging.error("No se pudo conectar a MT5")
        return False
    
    # Información de cuenta
    account = mt5.account_info()
    logging.info(f"Cuenta: {account.login} | Balance: ${account.balance:.2f}")
    
    # Ver posiciones actuales
    positions = mt5.positions_get()
    if positions:
        logging.info(f"=== {len(positions)} POSICIONES ACTUALES ===")
        for pos in positions:
            pnl = pos.profit
            logging.info(f"Ticket: {pos.ticket} | {pos.symbol} | {'BUY' if pos.type==0 else 'SELL'} | P&L: ${pnl:.2f}")
        
        # Cerrar la primera posición (más antigua)
        oldest_ticket = positions[0].ticket
        logging.info(f"🔄 Cerrando posición {oldest_ticket} para hacer espacio...")
        
        if not close_position(oldest_ticket):
            logging.error("No se pudo cerrar posición")
            return False
        
        # Esperar un momento
        import time
        time.sleep(2)
    
    # Ahora ejecutar trade nuevo
    symbol = "EURUSD"
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logging.error(f"No tick para {symbol}")
        return False
    
    volume = 0.01
    price = tick.ask
    sl = price - (20 * 0.0001)
    tp = price + (30 * 0.0001)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 99999999,
        "comment": "FORCE TEST - Verificación funcionamiento",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    logging.info(f"🚀 Enviando orden BUY {volume} {symbol} a {price:.5f}")
    
    result = mt5.order_send(request)
    
    if result:
        logging.info(f"Respuesta recibida - Código: {result.retcode}")
        if hasattr(result, 'comment'):
            logging.info(f"Comentario: {result.comment}")
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"✅ ORDEN EJECUTADA - Ticket: {result.order}")
            
            # Telegram notification
            try:
                from notifiers.telegram_notifier import send_telegram_message
                send_telegram_message(f"✅ TEST EXITOSO: BUY {volume} {symbol} - Ticket: {result.order}")
            except:
                pass
            
            return True
        else:
            logging.error(f"❌ Error en orden: {result.retcode}")
            return False
    else:
        logging.error("❌ Sin respuesta del servidor")
        return False

if __name__ == "__main__":
    logging.info("=" * 50)
    logging.info("FORCE TEST TRADE - VERIFICACIÓN SISTEMA")
    logging.info("=" * 50)
    
    if force_trade():
        logging.info("✅ SISTEMA FUNCIONAL - Orden ejecutada exitosamente")
    else:
        logging.error("❌ SISTEMA CON PROBLEMAS")
    
    mt5.shutdown()
    logging.info("=" * 50)