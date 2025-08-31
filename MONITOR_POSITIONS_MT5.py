#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MONITOR Y CORRECTOR DE POSICIONES MT5 - STANDALONE
Detecta y corrige automáticamente trades sin SL/TP
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def setup_logging():
    """Configurar logging sin emojis"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
        encoding='utf-8',
        errors='replace'
    )
    return logging.getLogger(__name__)

def calculate_sl_tp_from_market_data(symbol, entry_price, position_type):
    """
    Calcula SL/TP usando datos reales de TwelveData
    """
    try:
        from src.data.twelvedata_client import TwelveDataClient
        
        client = TwelveDataClient()
        
        # Obtener datos para calcular ATR
        if symbol == 'BTCUSD':
            df = client.get_crypto_data(symbol, interval='5min')
        elif symbol in ['EURUSD', 'GBPUSD', 'XAUUSD']:
            df = client.get_forex_data(symbol, interval='5min')
        else:
            df = client.get_time_series(symbol, interval='5min', outputsize=20)
        
        if df is not None and len(df) > 1:
            # Calcular ATR simple
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = abs(df['high'] - df['close'].shift(1))
            df['low_close'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            atr = df['tr'].rolling(window=14).mean().iloc[-1]
            
            print(f"   ATR calculado para {symbol}: {atr:.5f}")
        else:
            # Fallback: usar porcentaje del precio
            atr = entry_price * 0.015  # 1.5% del precio
            print(f"   ATR fallback para {symbol}: {atr:.5f} (1.5% del precio)")
        
        # Calcular SL y TP
        if position_type == 'BUY':
            sl = entry_price - (atr * 2.0)  # Riesgo: 2x ATR
            tp = entry_price + (atr * 3.0)  # Beneficio: 3x ATR
        else:  # SELL
            sl = entry_price + (atr * 2.0)
            tp = entry_price - (atr * 3.0)
        
        return sl, tp, atr
        
    except Exception as e:
        print(f"   Error calculando SL/TP: {e}")
        # Fallback manual
        atr_fallback = entry_price * 0.01
        if position_type == 'BUY':
            return entry_price - atr_fallback, entry_price + (atr_fallback * 1.5), atr_fallback
        else:
            return entry_price + atr_fallback, entry_price - (atr_fallback * 1.5), atr_fallback

def monitor_and_correct_positions():
    """
    Función principal de monitoreo independiente
    """
    logger = setup_logging()
    
    print("=" * 80)
    print("           MONITOR MT5 - DETECCION Y CORRECCION AUTOMATICA")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Intentar conectar directamente con MT5
        import MetaTrader5 as mt5
        
        print("1. Conectando directamente con MT5...")
        
        # Inicializar MT5
        if not mt5.initialize():
            print(f"   ERROR: No se pudo inicializar MT5: {mt5.last_error()}")
            return
        
        # Verificar conexión
        account_info = mt5.account_info()
        if account_info is None:
            print("   ERROR: No se pudo obtener información de cuenta")
            print("   SOLUCION: Verifica que MT5 esté abierto y logueado")
            mt5.shutdown()
            return
        
        print(f"   [OK] Conectado a MT5")
        print(f"   Cuenta: {account_info.login}")
        print(f"   Balance: ${account_info.balance:.2f}")
        print(f"   Servidor: {account_info.server}")
        
        # Variables de seguimiento
        cycle_count = 0
        total_corrected = 0
        
        print("\n2. INICIANDO MONITOR CONTINUO...")
        print("   - Cada 10 segundos verificará posiciones abiertas")
        print("   - Detectará trades sin SL/TP automáticamente")
        print("   - Corregirá usando ATR de datos reales")
        print("   - Presiona Ctrl+C para salir")
        print("   " + "-" * 60)
        
        while True:
            cycle_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n[Monitor {cycle_count:03d}] {current_time} - Verificando posiciones...")
            
            # Obtener todas las posiciones abiertas
            positions = mt5.positions_get()
            
            if not positions:
                print("   [INFO] No hay posiciones abiertas")
            else:
                print(f"   [FOUND] {len(positions)} posiciones encontradas")
                
                for i, position in enumerate(positions, 1):
                    symbol = position.symbol
                    ticket = position.ticket
                    pos_type = "BUY" if position.type == 0 else "SELL"
                    
                    # Verificar SL/TP
                    has_sl = position.sl != 0.0
                    has_tp = position.tp != 0.0
                    
                    sl_status = f"SL: {position.sl:.5f}" if has_sl else "SIN SL"
                    tp_status = f"TP: {position.tp:.5f}" if has_tp else "SIN TP"
                    
                    print(f"   Pos #{i}: {symbol} {pos_type} Vol:{position.volume} | {sl_status} | {tp_status}")
                    print(f"           Ticket: #{ticket} | P&L: {position.profit:.2f} USD")
                    
                    # ¿Necesita corrección?
                    needs_correction = not has_sl or not has_tp
                    
                    if needs_correction:
                        print(f"   🚨 [DETECTADO] Trade sin protección completa!")
                        
                        try:
                            # Calcular SL/TP usando datos reales
                            print(f"   [CORRIGIENDO] Calculando SL/TP con datos reales...")
                            
                            new_sl, new_tp, atr_used = calculate_sl_tp_from_market_data(
                                symbol, position.price_open, pos_type
                            )
                            
                            # Solo modificar lo que falta
                            final_sl = new_sl if not has_sl else position.sl
                            final_tp = new_tp if not has_tp else position.tp
                            
                            print(f"   [CALCULADO] SL: {final_sl:.5f} | TP: {final_tp:.5f} | ATR: {atr_used:.5f}")
                            
                            # Preparar request de modificación
                            request = {
                                "action": mt5.TRADE_ACTION_SLTP,
                                "position": ticket,
                                "symbol": symbol,
                                "sl": final_sl,
                                "tp": final_tp,
                                "magic": 20250817,
                                "comment": f"Auto-Correct #{ticket}"
                            }
                            
                            # Ejecutar modificación
                            result = mt5.order_send(request)
                            
                            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                total_corrected += 1
                                print(f"   ✅ [CORREGIDO] Posición #{ticket} modificada exitosamente!")
                                print(f"      Nuevo SL: {final_sl:.5f}")
                                print(f"      Nuevo TP: {final_tp:.5f}")
                                
                                # Log para Telegram (si estuviera configurado)
                                logger.info(f"POSICION CORREGIDA: {symbol} #{ticket} - SL:{final_sl:.5f} TP:{final_tp:.5f}")
                                
                            else:
                                error_msg = result.comment if result else "Sin respuesta"
                                print(f"   ❌ [ERROR] No se pudo corregir: {error_msg}")
                                logger.error(f"Error corrigiendo posición {ticket}: {error_msg}")
                                
                        except Exception as e:
                            print(f"   ❌ [ERROR] Error en corrección: {e}")
                            logger.error(f"Error calculando SL/TP para {symbol}: {e}")
                    else:
                        print(f"   ✅ [OK] Posición ya tiene protección completa")
            
            # Mostrar estadísticas cada 6 ciclos (1 minuto)
            if cycle_count % 6 == 0:
                print(f"\n--- ESTADISTICAS (Ciclo {cycle_count}) ---")
                print(f"Posiciones corregidas total: {total_corrected}")
                print(f"Tiempo transcurrido: {cycle_count * 10} segundos")
            
            print("   Esperando 10 segundos...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\n\n[INFO] Monitor detenido por el usuario")
        print(f"Resumen final:")
        print(f"- Ciclos ejecutados: {cycle_count}")
        print(f"- Posiciones corregidas: {total_corrected}")
        
    except Exception as e:
        print(f"\n[ERROR] Error en monitor: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cerrar MT5
        try:
            mt5.shutdown()
            print("- Conexión MT5 cerrada")
        except:
            pass

if __name__ == "__main__":
    monitor_and_correct_positions()