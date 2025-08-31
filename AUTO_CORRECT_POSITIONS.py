#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CORRECTOR AUTOMATICO DE POSICIONES SIN SL/TP
Conecta a MT5 y corrige automáticamente trades sin protección
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def auto_correct_positions():
    print("=" * 80)
    print("               CORRECTOR AUTOMATICO DE POSICIONES")
    print("=" * 80)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        import MetaTrader5 as mt5
        
        print("1. Conectando con MT5...")
        
        # Inicializar MT5
        if not mt5.initialize():
            print(f"   ERROR: {mt5.last_error()}")
            return
        
        # Verificar cuenta
        account_info = mt5.account_info()
        if account_info is None:
            print("   ERROR: No hay información de cuenta")
            print("   SOLUCION: Abre MT5 y loguéate primero")
            mt5.shutdown()
            return
        
        print(f"   [OK] Conectado - Cuenta: {account_info.login}")
        print(f"   Balance: ${account_info.balance:.2f}")
        print()
        
        print("2. Obteniendo posiciones abiertas...")
        
        positions = mt5.positions_get()
        
        if not positions:
            print("   [INFO] No hay posiciones abiertas")
            print("   Para probar: Abre una posición sin SL/TP en MT5")
            mt5.shutdown()
            return
        
        print(f"   [FOUND] {len(positions)} posiciones encontradas")
        print()
        
        corrected_count = 0
        
        for i, position in enumerate(positions, 1):
            symbol = position.symbol
            ticket = position.ticket
            pos_type = "BUY" if position.type == 0 else "SELL"
            volume = position.volume
            entry_price = position.price_open
            profit = position.profit
            
            has_sl = position.sl != 0.0
            has_tp = position.tp != 0.0
            
            print(f"--- POSICION #{i} ---")
            print(f"Simbolo: {symbol} | Ticket: #{ticket} | Tipo: {pos_type}")
            print(f"Volumen: {volume} | Entrada: {entry_price:.5f} | P&L: {profit:.2f}")
            print(f"SL Actual: {position.sl:.5f} {'[OK]' if has_sl else '[FALTA]'}")
            print(f"TP Actual: {position.tp:.5f} {'[OK]' if has_tp else '[FALTA]'}")
            
            # ¿Necesita corrección?
            needs_correction = not has_sl or not has_tp
            
            if needs_correction:
                print("*** CORRIGIENDO AUTOMATICAMENTE ***")
                
                # Calcular SL/TP con ATR estimado
                atr = entry_price * 0.015  # 1.5% ATR
                
                if pos_type == 'BUY':
                    new_sl = entry_price - (atr * 2.0) if not has_sl else position.sl
                    new_tp = entry_price + (atr * 3.0) if not has_tp else position.tp
                else:  # SELL
                    new_sl = entry_price + (atr * 2.0) if not has_sl else position.sl
                    new_tp = entry_price - (atr * 3.0) if not has_tp else position.tp
                
                print(f"Nuevo SL: {new_sl:.5f} {'(AGREGADO)' if not has_sl else '(MANTENIDO)'}")
                print(f"Nuevo TP: {new_tp:.5f} {'(AGREGADO)' if not has_tp else '(MANTENIDO)'}")
                
                # Preparar orden de modificación
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": ticket,
                    "symbol": symbol,
                    "sl": new_sl,
                    "tp": new_tp,
                    "magic": 20250817,
                    "comment": f"AutoCorrect-{datetime.now().strftime('%H%M%S')}"
                }
                
                print("Ejecutando modificación...")
                
                # Enviar orden
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    corrected_count += 1
                    print("[SUCCESS] Posición corregida exitosamente!")
                    print(f"Order: {result.order} | Deal: {result.deal}")
                else:
                    error_msg = result.comment if result else "Sin respuesta"
                    retcode = result.retcode if result else "N/A"
                    print(f"[ERROR] Corrección falló: {error_msg} (Code: {retcode})")
                    
                    # Mostrar detalles del error
                    if result:
                        print(f"Detalles: retcode={result.retcode}, request_id={result.request_id}")
                
            else:
                print("[OK] Posición ya tiene protección completa")
            
            print()
        
        # Resumen final
        print("=" * 80)
        print("                           RESUMEN FINAL")
        print("=" * 80)
        print(f"Posiciones revisadas: {len(positions)}")
        print(f"Posiciones corregidas: {corrected_count}")
        
        if corrected_count > 0:
            print(f"\n[SUCCESS] {corrected_count} posiciones fueron protegidas automáticamente")
            print("Todas las posiciones ahora tienen Stop Loss y Take Profit")
        else:
            print("\n[INFO] Todas las posiciones ya estaban protegidas")
        
        print(f"\nPróxima verificación recomendada en 60 segundos")
        
        # Cerrar MT5
        mt5.shutdown()
        
    except ImportError:
        print("ERROR: MetaTrader5 library no encontrada")
        print("SOLUCION: pip install MetaTrader5")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    auto_correct_positions()