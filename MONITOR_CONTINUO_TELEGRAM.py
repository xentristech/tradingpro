#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MONITOR CONTINUO CON TELEGRAM
=============================
Monitor continuo que aplica breakeven/trailing y notifica por Telegram
"""

import MetaTrader5 as mt5
import sys
import time
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
    print("="*70)
    print("    MONITOR CONTINUO CON NOTIFICACIONES TELEGRAM")
    print("="*70)
    
    # Inicializar MT5
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    # Inicializar Telegram
    telegram = TelegramNotifier() if TelegramNotifier else None
    
    if telegram and telegram.is_active:
        print("OK: Telegram conectado - Notificaciones automáticas activas")
        # Notificar inicio del monitor
        telegram.send_alert(
            'success',
            'Monitor continuo iniciado\n\nSistema híbrido:\n• Breakeven protector: 15 pips\n• Breakeven conservador: 25 pips\n• Revisión cada 30 segundos\n\nNotificará cuando aplique protecciones'
        )
    else:
        print("AVISO: Telegram no disponible - Solo logs locales")
    
    # Configuración
    PROTECTIVE_BREAKEVEN = 15
    CONSERVATIVE_BREAKEVEN = 25
    PROTECTIVE_TRAILING = 20
    CONSERVATIVE_TRAILING = 40
    BREAKEVEN_OFFSET = 3
    TRAILING_DISTANCE = 15
    
    print()
    print("CONFIGURACION DEL MONITOR:")
    print(f"- Breakeven PROTECTOR: {PROTECTIVE_BREAKEVEN} pips (>=10 pips o >=$50)")
    print(f"- Breakeven CONSERVADOR: {CONSERVATIVE_BREAKEVEN} pips")
    print(f"- Trailing PROTECTOR: {PROTECTIVE_TRAILING} pips")
    print(f"- Trailing CONSERVADOR: {CONSERVATIVE_TRAILING} pips")
    print(f"- Revisión: Cada 30 segundos")
    print()
    print("POSICIONES OBJETIVO:")
    print("- XAUAUDm #226329954: 14.6 pips -> Solo 0.4 pips más para protección")
    print("- XAUGBPm #226330108: 5.8 pips -> Necesita 9.2 pips más")
    print()
    print("INICIANDO MONITOR... (Ctrl+C para detener)")
    print("="*70)
    
    # Estados para evitar aplicar múltiples veces
    processed_positions = {
        'breakeven': set(),
        'trailing': set()
    }
    
    cycle = 0
    total_actions = 0
    
    try:
        while True:
            cycle += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n[Ciclo {cycle:03d}] {current_time}")
            
            # Obtener posiciones
            positions = mt5.positions_get()
            
            if not positions:
                print("  Sin posiciones abiertas")
                time.sleep(30)
                continue
            
            print(f"  Revisando {len(positions)} posiciones...")
            
            cycle_actions = 0
            
            for pos in positions:
                symbol = pos.symbol
                ticket = pos.ticket
                
                # Calcular pips de ganancia
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    continue
                
                current_price = tick.bid if pos.type == 0 else tick.ask
                
                # Valor de pip
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
                
                if pips_profit <= 0:
                    continue
                
                # Mostrar estado
                print(f"    {symbol} #{ticket}: {pips_profit:.1f} pips (${pos.profit:.2f})")
                
                # Determinar modo
                if pips_profit >= 10 or pos.profit >= 50:
                    mode = "PROTECTOR"
                    breakeven_trigger = PROTECTIVE_BREAKEVEN
                    trailing_trigger = PROTECTIVE_TRAILING
                else:
                    mode = "CONSERVADOR"
                    breakeven_trigger = CONSERVATIVE_BREAKEVEN
                    trailing_trigger = CONSERVATIVE_TRAILING
                
                position_key = f"{ticket}"
                
                # APLICAR BREAKEVEN
                if (pips_profit >= breakeven_trigger and 
                    position_key not in processed_positions['breakeven']):
                    
                    old_sl = pos.sl
                    
                    # Calcular nuevo SL
                    if pos.type == 0:  # BUY
                        new_sl = pos.price_open + (BREAKEVEN_OFFSET * pip_value)
                        should_apply = (old_sl == 0 or new_sl > old_sl)
                    else:  # SELL
                        new_sl = pos.price_open - (BREAKEVEN_OFFSET * pip_value)
                        should_apply = (old_sl == 0 or new_sl < old_sl)
                    
                    if should_apply:
                        # Aplicar
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
                            processed_positions['breakeven'].add(position_key)
                            cycle_actions += 1
                            total_actions += 1
                            
                            print(f"      >> BREAKEVEN {mode} APLICADO!")
                            print(f"         SL: {old_sl:.5f} -> {new_sl:.5f}")
                            
                            # NOTIFICAR POR TELEGRAM
                            if telegram and telegram.is_active:
                                telegram.send_breakeven_notification(
                                    symbol=symbol,
                                    ticket=ticket,
                                    old_sl=old_sl,
                                    new_sl=new_sl,
                                    pips_profit=pips_profit
                                )
                                print(f"         Telegram: Notificado")
                        else:
                            print(f"      >> ERROR: {result.comment}")
                
                # APLICAR TRAILING
                elif (pips_profit >= trailing_trigger and 
                      position_key not in processed_positions['trailing']):
                    
                    old_sl = pos.sl
                    trailing_distance = TRAILING_DISTANCE * pip_value
                    
                    # Calcular nuevo trailing SL
                    if pos.type == 0:  # BUY
                        new_sl = current_price - trailing_distance
                        should_apply = (old_sl == 0 or new_sl > old_sl)
                    else:  # SELL
                        new_sl = current_price + trailing_distance
                        should_apply = (old_sl == 0 or new_sl < old_sl)
                    
                    if should_apply:
                        # Aplicar
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
                            processed_positions['trailing'].add(position_key)
                            cycle_actions += 1
                            total_actions += 1
                            
                            print(f"      >> TRAILING {mode} APLICADO!")
                            print(f"         SL: {old_sl:.5f} -> {new_sl:.5f}")
                            
                            # NOTIFICAR POR TELEGRAM
                            if telegram and telegram.is_active:
                                telegram.send_trailing_notification(
                                    symbol=symbol,
                                    ticket=ticket,
                                    old_sl=old_sl,
                                    new_sl=new_sl,
                                    pips_profit=pips_profit,
                                    distance_pips=TRAILING_DISTANCE
                                )
                                print(f"         Telegram: Notificado")
                        else:
                            print(f"      >> ERROR: {result.comment}")
                
                else:
                    # Mostrar cuanto falta
                    if pips_profit < breakeven_trigger:
                        needed = breakeven_trigger - pips_profit
                        print(f"      -> Falta {needed:.1f} pips para breakeven {mode}")
            
            if cycle_actions > 0:
                print(f"  ACCIONES EN ESTE CICLO: {cycle_actions}")
                print(f"  TOTAL ACCIONES: {total_actions}")
                
                # Enviar resumen por Telegram
                if telegram and telegram.is_active:
                    telegram.send_protection_summary(
                        breakeven_count=len(processed_positions['breakeven']),
                        trailing_count=len(processed_positions['trailing']),
                        total_positions=len(positions)
                    )
            
            # Esperar 30 segundos
            time.sleep(30)
    
    except KeyboardInterrupt:
        print(f"\n\nMONITOR DETENIDO")
        print(f"Total acciones aplicadas: {total_actions}")
        
        if telegram and telegram.is_active:
            telegram.send_alert(
                'warning',
                f'Monitor continuo detenido\n\nAcciones aplicadas:\n• Breakeven: {len(processed_positions["breakeven"])}\n• Trailing: {len(processed_positions["trailing"])}\n\nTotal: {total_actions} protecciones aplicadas'
            )
        
        print("="*70)
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()