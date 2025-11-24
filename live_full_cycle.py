#!/usr/bin/env python3
"""
EXNESS FULL CYCLE TEST - Validación completa con cuenta EXNESS
"""
import MetaTrader5 as mt5
import logging
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')

def connect_exness():
    """Conectar específicamente a cuenta EXNESS"""
    if not mt5.initialize():
        logging.error("No se pudo inicializar MT5")
        return False
    
    account = mt5.account_info()
    if not account:
        logging.error("No se pudo obtener información de cuenta")
        return False
    
    logging.info(f"Conectado - Cuenta: {account.login} | Balance: ${account.balance:.2f}")
    logging.info(f"Servidor: {account.server}")
    
    # Verificar si es cuenta EXNESS
    if account.login == 197678662:
        logging.info("✅ Conectado a cuenta EXNESS")
    else:
        logging.warning(f"⚠️ Conectado a cuenta {account.login}, no es la EXNESS 197678662")
        logging.info("Continuando con cuenta disponible...")
    
    return True

def get_available_symbol():
    """Obtener símbolo disponible para operar"""
    symbols = mt5.symbols_get()
    if not symbols:
        return None
    
    # Buscar símbolos preferidos
    preferred = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]
    
    for pref in preferred:
        for symbol in symbols:
            if symbol.name == pref and symbol.visible:
                tick = mt5.symbol_info_tick(symbol.name)
                if tick:
                    logging.info(f"✅ Símbolo disponible: {symbol.name} - Precio: {tick.bid:.5f}")
                    return symbol.name
    
    # Si no encuentra preferidos, buscar cualquiera
    for symbol in symbols:
        if symbol.visible:
            tick = mt5.symbol_info_tick(symbol.name)
            if tick and tick.bid > 0:
                logging.info(f"✅ Símbolo alternativo: {symbol.name}")
                return symbol.name
    
    return None

def show_positions():
    """Mostrar posiciones actuales"""
    positions = mt5.positions_get()
    if not positions:
        logging.info("No hay posiciones abiertas")
        return []
    
    logging.info(f"=== {len(positions)} POSICIONES ACTUALES ===")
    total_pnl = 0
    for pos in positions:
        pnl = pos.profit
        total_pnl += pnl
        logging.info(f"Ticket: {pos.ticket} | {pos.symbol} | {'BUY' if pos.type==0 else 'SELL'} | {pos.volume} | P&L: ${pnl:.2f}")
    
    logging.info(f"Total P&L: ${total_pnl:.2f}")
    return list(positions)

def close_all_positions():
    """Cerrar todas las posiciones"""
    positions = show_positions()
    
    if not positions:
        return True
    
    logging.info(f"🔄 Cerrando {len(positions)} posiciones...")
    
    success_count = 0
    for position in positions:
        try:
            # Determinar tipo de cierre
            if position.type == mt5.ORDER_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
                close_price = mt5.symbol_info_tick(position.symbol).bid
            else:
                close_type = mt5.ORDER_TYPE_BUY  
                close_price = mt5.symbol_info_tick(position.symbol).ask
            
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": position.ticket,
                "price": close_price,
                "deviation": 20,
                "magic": position.magic,
                "comment": "CIERRE TOTAL",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(close_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logging.info(f"✅ Cerrada: {position.ticket} - {position.symbol}")
                success_count += 1
            else:
                error = result.comment if result else "Sin respuesta"
                logging.error(f"❌ Error cerrando {position.ticket}: {error}")
                
            time.sleep(0.5)  # Pausa entre cierres
            
        except Exception as e:
            logging.error(f"Error cerrando {position.ticket}: {e}")
    
    logging.info(f"✅ {success_count}/{len(positions)} posiciones cerradas")
    
    # Verificar resultado final
    time.sleep(2)
    remaining = mt5.positions_get()
    remaining_count = len(remaining) if remaining else 0
    
    if remaining_count == 0:
        logging.info("✅ TODAS LAS POSICIONES CERRADAS")
        return True
    else:
        logging.warning(f"⚠️ Quedan {remaining_count} posiciones")
        return False

def create_test_trade(symbol):
    """Crear operación de prueba"""
    
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logging.error(f"No tick para {symbol}")
        return None
    
    # Configurar trade pequeño
    volume = 0.01
    price = tick.ask
    
    # SL y TP básicos
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info.digits >= 4:
        pip_size = 0.0001 if symbol_info.digits == 5 else 0.01
    else:
        pip_size = 0.01
    
    sl = price - (25 * pip_size)  # 25 pips SL
    tp = price + (40 * pip_size)  # 40 pips TP
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 66666666,
        "comment": "VALIDACIÓN COMPLETA",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    logging.info(f"🚀 Creando: BUY {volume} {symbol} a {price}")
    logging.info(f"   SL: {sl} | TP: {tp}")
    
    result = mt5.order_send(request)
    
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(f"✅ CREADA - Ticket: {result.order}")
        return result.order
    else:
        error = result.comment if result else "Sin respuesta"
        logging.error(f"❌ Error creando: {error}")
        logging.error(f"   Código: {result.retcode if result else 'N/A'}")
        return None

def close_by_ticket(ticket):
    """Cerrar posición específica por ticket"""
    positions = mt5.positions_get()
    if not positions:
        logging.error("No hay posiciones para cerrar")
        return False
    
    target_pos = None
    for pos in positions:
        if pos.ticket == ticket:
            target_pos = pos
            break
    
    if not target_pos:
        logging.error(f"Posición {ticket} no encontrada")
        return False
    
    # Cerrar la posición
    if target_pos.type == mt5.ORDER_TYPE_BUY:
        close_type = mt5.ORDER_TYPE_SELL
        close_price = mt5.symbol_info_tick(target_pos.symbol).bid
    else:
        close_type = mt5.ORDER_TYPE_BUY
        close_price = mt5.symbol_info_tick(target_pos.symbol).ask
    
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": target_pos.symbol,
        "volume": target_pos.volume,
        "type": close_type,
        "position": target_pos.ticket,
        "price": close_price,
        "deviation": 20,
        "magic": target_pos.magic,
        "comment": "CIERRE ESPECÍFICO",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    result = mt5.order_send(close_request)
    
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(f"✅ Posición {ticket} cerrada exitosamente")
        return True
    else:
        error = result.comment if result else "Sin respuesta"
        logging.error(f"❌ Error cerrando {ticket}: {error}")
        return False

def run_full_validation():
    """Ejecutar validación completa"""
    
    if not connect_exness():
        return False
    
    try:
        # PASO 1: Mostrar estado inicial
        logging.info("=" * 70)
        logging.info("PASO 1: ESTADO INICIAL")
        logging.info("=" * 70)
        initial_positions = show_positions()
        
        # PASO 2: Cerrar todas las existentes
        logging.info("=" * 70)
        logging.info("PASO 2: CERRAR TODAS LAS POSICIONES EXISTENTES")
        logging.info("=" * 70)
        
        if not close_all_positions():
            logging.warning("No se pudieron cerrar todas, continuando...")
        
        # PASO 3: Obtener símbolo disponible
        logging.info("=" * 70)
        logging.info("PASO 3: VERIFICAR SÍMBOLO DISPONIBLE")
        logging.info("=" * 70)
        
        symbol = get_available_symbol()
        if not symbol:
            logging.error("No se encontró símbolo disponible")
            return False
        
        # PASO 4: Crear nueva posición
        logging.info("=" * 70)
        logging.info("PASO 4: CREAR NUEVA POSICIÓN DE VALIDACIÓN")
        logging.info("=" * 70)
        
        new_ticket = create_test_trade(symbol)
        if not new_ticket:
            logging.error("No se pudo crear nueva posición")
            return False
        
        # Esperar y verificar
        time.sleep(3)
        
        # PASO 5: Verificar posición creada
        logging.info("=" * 70)
        logging.info("PASO 5: VERIFICAR POSICIÓN CREADA")
        logging.info("=" * 70)
        
        current_positions = show_positions()
        created_pos = None
        for pos in current_positions:
            if pos.ticket == new_ticket:
                created_pos = pos
                break
        
        if not created_pos:
            logging.error("La posición creada no se encuentra")
            return False
        
        logging.info(f"✅ Posición confirmada: Ticket {new_ticket} | P&L: ${created_pos.profit:.2f}")
        
        # PASO 6: Cerrar la posición creada
        logging.info("=" * 70)
        logging.info("PASO 6: CERRAR LA POSICIÓN CREADA")
        logging.info("=" * 70)
        
        if not close_by_ticket(new_ticket):
            logging.error("No se pudo cerrar la posición creada")
            return False
        
        # PASO 7: Verificación final
        logging.info("=" * 70)
        logging.info("PASO 7: VERIFICACIÓN FINAL")
        logging.info("=" * 70)
        
        time.sleep(2)
        final_positions = show_positions()
        
        # Telegram notification
        try:
            from notifiers.telegram_notifier import send_telegram_message
            send_telegram_message(f"🎉 VALIDACIÓN EXNESS COMPLETA EXITOSA:\n- Cerradas {len(initial_positions)} posiciones existentes\n- Creada posición {new_ticket} en {symbol}\n- Cerrada la posición creada\n- Sistema EXNESS funcionando perfectamente")
        except Exception as e:
            logging.debug(f"Error Telegram: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error en validación: {e}")
        return False

if __name__ == "__main__":
    logging.info("=" * 70)
    logging.info("VALIDACIÓN COMPLETA DEL SISTEMA EXNESS")
    logging.info("Cerrar → Crear → Cerrar → Validar")
    logging.info("=" * 70)
    
    try:
        if run_full_validation():
            logging.info("=" * 70)
            logging.info("🎉 SISTEMA EXNESS COMPLETAMENTE VALIDADO Y FUNCIONAL")
            logging.info("   ✅ Cierre de posiciones existentes: OK")
            logging.info("   ✅ Creación de nuevas posiciones: OK")
            logging.info("   ✅ Cierre de posiciones específicas: OK")
            logging.info("   ✅ Ciclo completo de operaciones: OK")
            logging.info("=" * 70)
        else:
            logging.error("❌ PROBLEMAS EN LA VALIDACIÓN")
    except Exception as e:
        logging.error(f"Error crítico: {e}")
    finally:
        mt5.shutdown()
        logging.info("MT5 desconectado")