#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APLICAR TRAILING REAL CON TELEGRAM
==================================
Sistema que aplica trailing/breakeven a posiciones reales y notifica por Telegram
"""

import MetaTrader5 as mt5
import sys
from datetime import datetime
from pathlib import Path

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.notifiers.telegram_notifier import TelegramNotifier
except ImportError as e:
    print(f"Error importando TelegramNotifier: {e}")
    TelegramNotifier = None

def main():
    print("="*60)
    print("    APLICAR TRAILING REAL CON TELEGRAM")
    print("="*60)
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    # Inicializar Telegram
    telegram = TelegramNotifier() if TelegramNotifier else None
    
    if telegram and telegram.is_active:
        print("OK: Telegram conectado - Notificaciones activadas")
    else:
        print("AVISO: Telegram no disponible - Solo logs locales")
    
    # PARAMETROS HIBRIDOS REALES
    CONSERVATIVE_BREAKEVEN = 25  # Para nuevas activaciones
    PROTECTIVE_BREAKEVEN = 15    # Para posiciones ya ganadoras
    PROTECTIVE_PROFIT_USD = 50   # $50+ para modo protector
    
    BREAKEVEN_OFFSET = 3
    
    print()
    print("CONFIGURACION HIBRIDA REAL:")
    print(f"- Breakeven CONSERVADOR: {CONSERVATIVE_BREAKEVEN} pips")
    print(f"- Breakeven PROTECTOR: {PROTECTIVE_BREAKEVEN} pips (si >=10 pips o >=$50)")
    print(f"- Offset: +{BREAKEVEN_OFFSET} pips sobre entrada")
    print()
    
    positions = mt5.positions_get()
    
    if not positions:
        print("No hay posiciones abiertas")
        mt5.shutdown()
        return
    
    print(f"Analizando {len(positions)} posiciones REALES...")
    print(f"Tickets reales: {[pos.ticket for pos in positions]}")
    print()
    
    actions_taken = 0
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        
        # Calcular pips de ganancia
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
        
        current_price = tick.bid if pos.type == 0 else tick.ask
        
        # Determinar valor de pip
        if symbol.startswith(('EUR', 'GBP', 'AUD', 'NZD')):
            pip_value = 0.0001
        elif 'JPY' in symbol:
            pip_value = 0.01
        else:
            pip_value = 1.0
        
        # Calcular pips de ganancia
        if pos.type == 0:  # BUY
            pips_profit = (current_price - pos.price_open) / pip_value
        else:  # SELL
            pips_profit = (pos.price_open - current_price) / pip_value
        
        print(f"--- {symbol} #{ticket} (REAL) ---")
        print(f"Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"Ganancia: {pips_profit:.1f} pips (${pos.profit:.2f})")
        
        if pips_profit <= 0:
            print("  -> Sin ganancia, saltando")
            print()
            continue
        
        # DETERMINAR MODO (PROTECTOR vs CONSERVADOR)
        if pips_profit >= 10 or pos.profit >= PROTECTIVE_PROFIT_USD:
            mode = "PROTECTOR"
            breakeven_trigger = PROTECTIVE_BREAKEVEN
            print(f"  -> MODO: {mode} (>=10 pips o >=$50)")
        else:
            mode = "CONSERVADOR"
            breakeven_trigger = CONSERVATIVE_BREAKEVEN
            print(f"  -> MODO: {mode} (nueva posicion)")
        
        # VERIFICAR SI CALIFICA PARA BREAKEVEN
        if pips_profit >= breakeven_trigger:
            old_sl = pos.sl
            
            # Calcular nuevo SL
            if pos.type == 0:  # BUY
                new_sl = pos.price_open + (BREAKEVEN_OFFSET * pip_value)
                if old_sl != 0 and new_sl <= old_sl:
                    print(f"  -> SL actual {old_sl:.5f} ya es mejor")
                    print()
                    continue
            else:  # SELL
                new_sl = pos.price_open - (BREAKEVEN_OFFSET * pip_value)
                if old_sl != 0 and new_sl >= old_sl:
                    print(f"  -> SL actual {old_sl:.5f} ya es mejor")
                    print()
                    continue
            
            print(f"  -> APLICANDO BREAKEVEN {mode}")
            print(f"     SL: {old_sl:.5f} -> {new_sl:.5f}")
            
            # APLICAR MODIFICACION REAL
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": pos.tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                actions_taken += 1
                secured_pips = BREAKEVEN_OFFSET
                
                print(f"  -> EXITO: Breakeven aplicado")
                print(f"     Ganancia asegurada: {secured_pips} pips")
                
                # NOTIFICAR POR TELEGRAM CON TICKET REAL
                if telegram and telegram.is_active:
                    success = telegram.send_breakeven_notification(
                        symbol=symbol,
                        ticket=ticket,  # TICKET REAL
                        old_sl=old_sl,
                        new_sl=new_sl,
                        pips_profit=pips_profit
                    )
                    
                    if success:
                        print(f"     Telegram: Notificacion enviada")
                    else:
                        print(f"     Telegram: Error enviando notificacion")
                
            else:
                print(f"  -> ERROR: {result.comment}")
        
        else:
            needed = breakeven_trigger - pips_profit
            print(f"  -> Necesita {needed:.1f} pips mas para breakeven {mode}")
        
        print()
    
    print("="*60)
    print(f"ACCIONES APLICADAS: {actions_taken}")
    
    if actions_taken > 0:
        print("GANANCIAS ASEGURADAS CON TICKETS REALES!")
        
        # ENVIAR RESUMEN POR TELEGRAM
        if telegram and telegram.is_active:
            telegram.send_protection_summary(
                breakeven_count=actions_taken,
                trailing_count=0,
                total_positions=len(positions)
            )
            print("Resumen enviado por Telegram")
    else:
        print("NO SE APLICARON PROTECCIONES")
        print("Las posiciones aun no califican para breakeven")
    
    print("="*60)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()