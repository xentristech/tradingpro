#!/usr/bin/env python3
"""
FULL CYCLE TEST - Cerrar todas las posiciones, crear una nueva y cerrarla
Validación completa del ciclo de operaciones
"""
import MetaTrader5 as mt5
import logging
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')

def connect_mt5():
    """Conectar a MT5"""
    if not mt5.initialize():
        logging.error("No se pudo inicializar MT5")
        return False
    
    account = mt5.account_info()
    if not account:
        logging.error("No se pudo obtener información de cuenta")
        return False
    
    logging.info(f"Conectado - Cuenta: {account.login} | Balance: ${account.balance:.2f}")
    return True

def get_all_positions():
    """Obtener todas las posiciones abiertas"""
    positions = mt5.positions_get()
    return positions if positions else []

def close_position(position):
    """Cerrar una posición específica"""
    try:
        # Determinar tipo de orden de cierre
        if position.type == mt5.ORDER_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
            close_price = mt5.symbol_info_tick(position.symbol).bid
        else:
            close_type = mt5.ORDER_TYPE_BUY
            close_price = mt5.symbol_info_tick(position.symbol).ask
        
        # Preparar orden de cierre
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": close_type,
            "position": position.ticket,
            "price": close_price,
            "deviation": 20,
            "magic": position.magic,
            "comment": "CIERRE COMPLETO",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        result = mt5.order_send(close_request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"✅ Posición {position.ticket} cerrada - {position.symbol} {position.volume}")
            return True
        else:
            error_msg = result.comment if result else "Sin respuesta"
            logging.error(f"❌ Error cerrando {position.ticket}: {error_msg}")
            return False
            
    except Exception as e:
        logging.error(f"Error cerrando posición {position.ticket}: {e}")
        return False

def close_all_positions():
    """Cerrar todas las posiciones abiertas"""
    positions = get_all_positions()
    
    if not positions:
        logging.info("No hay posiciones para cerrar")
        return True
    
    logging.info(f"🔄 Cerrando {len(positions)} posiciones...")
    
    success_count = 0
    for position in positions:
        pnl = position.profit
        logging.info(f"Cerrando: Ticket {position.ticket} | {position.symbol} | {'BUY' if position.type==0 else 'SELL'} | P&L: ${pnl:.2f}")
        
        if close_position(position):
            success_count += 1
            time.sleep(0.5)  # Pausa breve entre cierres
    
    logging.info(f"✅ {success_count}/{len(positions)} posiciones cerradas")
    
    # Verificar que todas se cerraron
    time.sleep(2)
    remaining = get_all_positions()
    if remaining:
        logging.warning(f"⚠️ Quedan {len(remaining)} posiciones sin cerrar")
        return False
    else:
        logging.info("✅ Todas las posiciones cerradas exitosamente")
        return True

def create_test_position():
    """Crear una posición de prueba"""
    symbol = "EURUSD"
    
    # Verificar símbolo disponible
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logging.error(f"No se pudo obtener tick para {symbol}")
        return None
    
    volume = 0.01
    price = tick.ask
    sl = price - (30 * 0.0001)  # 30 pips SL
    tp = price + (50 * 0.0001)  # 50 pips TP
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 77777777,
        "comment": "TEST COMPLETO - Validación sistema",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    logging.info(f"🚀 Creando posición: BUY {volume} {symbol} a {price:.5f}")
    logging.info(f"   SL: {sl:.5f} | TP: {tp:.5f}")
    
    result = mt5.order_send(request)
    
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(f"✅ POSICIÓN CREADA - Ticket: {result.order}")
        
        # Telegram notification
        try:
            from notifiers.telegram_notifier import send_telegram_message
            send_telegram_message(f"✅ POSICIÓN CREADA: BUY {volume} {symbol} - Ticket: {result.order}")
        except:
            pass
        
        return result.order
    else:
        error_msg = result.comment if result else "Sin respuesta"
        logging.error(f"❌ Error creando posición: {error_msg}")
        return None

def close_specific_position(ticket):
    """Cerrar posición específica por ticket"""
    positions = get_all_positions()
    
    target_position = None
    for pos in positions:
        if pos.ticket == ticket:
            target_position = pos
            break
    
    if not target_position:
        logging.error(f"Posición {ticket} no encontrada")
        return False
    
    logging.info(f"🔄 Cerrando posición específica: Ticket {ticket}")
    return close_position(target_position)

def full_cycle_validation():
    """Ejecutar validación completa del ciclo de operaciones"""
    
    if not connect_mt5():
        return False
    
    try:
        # Paso 1: Cerrar todas las posiciones existentes
        logging.info("=" * 60)
        logging.info("PASO 1: CERRAR TODAS LAS POSICIONES EXISTENTES")
        logging.info("=" * 60)
        
        if not close_all_positions():
            logging.error("No se pudieron cerrar todas las posiciones")
            return False
        
        # Paso 2: Crear nueva posición
        logging.info("=" * 60)
        logging.info("PASO 2: CREAR NUEVA POSICIÓN DE PRUEBA")
        logging.info("=" * 60)
        
        new_ticket = create_test_position()
        if not new_ticket:
            logging.error("No se pudo crear la nueva posición")
            return False
        
        # Esperar un momento
        time.sleep(3)
        
        # Verificar que la posición existe
        positions = get_all_positions()
        created_position = None
        for pos in positions:
            if pos.ticket == new_ticket:
                created_position = pos
                break
        
        if not created_position:
            logging.error("La posición creada no se encuentra")
            return False
        
        logging.info(f"✅ Posición verificada: Ticket {new_ticket} | P&L: ${created_position.profit:.2f}")
        
        # Paso 3: Cerrar la posición creada
        logging.info("=" * 60)
        logging.info("PASO 3: CERRAR LA POSICIÓN CREADA")
        logging.info("=" * 60)
        
        if not close_specific_position(new_ticket):
            logging.error("No se pudo cerrar la posición creada")
            return False
        
        # Paso 4: Validación final
        logging.info("=" * 60)
        logging.info("PASO 4: VALIDACIÓN FINAL")
        logging.info("=" * 60)
        
        final_positions = get_all_positions()
        if final_positions:
            logging.warning(f"⚠️ Quedan {len(final_positions)} posiciones abiertas")
        else:
            logging.info("✅ No hay posiciones abiertas - Validación completa")
        
        # Telegram notification final
        try:
            from notifiers.telegram_notifier import send_telegram_message
            send_telegram_message(f"✅ VALIDACIÓN COMPLETA: Ciclo de operaciones funciona correctamente. Posición creada (Ticket: {new_ticket}) y cerrada exitosamente.")
        except:
            pass
        
        return True
        
    except Exception as e:
        logging.error(f"Error en validación: {e}")
        return False

if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("VALIDACIÓN COMPLETA DEL CICLO DE OPERACIONES")
    logging.info("Cerrar existentes → Crear nueva → Cerrar nueva → Validar")
    logging.info("=" * 60)
    
    try:
        if full_cycle_validation():
            logging.info("🎉 SISTEMA COMPLETAMENTE VALIDADO")
            logging.info("   - Puede cerrar posiciones existentes")
            logging.info("   - Puede crear nuevas operaciones")
            logging.info("   - Puede cerrar operaciones específicas")
            logging.info("   - Ciclo completo funcionando correctamente")
        else:
            logging.error("❌ Problemas en la validación - Revisar logs")
    except Exception as e:
        logging.error(f"Error crítico: {e}")
    finally:
        mt5.shutdown()
        logging.info("=" * 60)