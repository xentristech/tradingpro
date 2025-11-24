#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA DE TRADING CON LOGGING COMPLETO
=======================================
Sistema de trading que registra TODA la actividad en logs detallados
"""

import MetaTrader5 as mt5
import sys
import time
from datetime import datetime
from pathlib import Path
import threading

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.notifiers.telegram_notifier import TelegramNotifier
    from src.utils.comprehensive_logger import comprehensive_logger
except ImportError as e:
    print(f"Error importando módulos: {e}")
    TelegramNotifier = None
    comprehensive_logger = None

class TradingSystemWithLogs:
    """Sistema de trading con logging completo integrado"""
    
    def __init__(self):
        # Inicializar componentes
        self.telegram = TelegramNotifier() if TelegramNotifier else None
        self.logger = comprehensive_logger if comprehensive_logger else None
        
        # Parámetros del sistema
        self.PROTECTIVE_BREAKEVEN = 15
        self.CONSERVATIVE_BREAKEVEN = 25
        self.PROTECTIVE_TRAILING = 20
        self.CONSERVATIVE_TRAILING = 40
        self.BREAKEVEN_OFFSET = 3
        self.TRAILING_DISTANCE = 15
        
        # Estados
        self.position_states = {
            'breakeven_applied': set(),
            'trailing_active': set()
        }
        
        self.running = True
        
        # Log de inicialización
        if self.logger:
            self.logger.log_system_event('TRADING_SYSTEM_INIT', 'Sistema de trading con logs inicializado', {
                'protective_breakeven': self.PROTECTIVE_BREAKEVEN,
                'conservative_breakeven': self.CONSERVATIVE_BREAKEVEN,
                'protective_trailing': self.PROTECTIVE_TRAILING,
                'conservative_trailing': self.CONSERVATIVE_TRAILING,
                'telegram_available': self.telegram is not None and (self.telegram.is_active if self.telegram else False)
            })
        
        print("Sistema de trading con logging completo inicializado")
        if self.telegram and self.telegram.is_active:
            print("OK Telegram: Conectado")
        if self.logger:
            print("OK Logger: Activo")
    
    def get_pip_value(self, symbol):
        """Obtener valor de pip"""
        if symbol.startswith(('EUR', 'GBP', 'AUD', 'NZD')):
            return 0.0001
        elif 'JPY' in symbol:
            return 0.01
        else:
            return 1.0
    
    def calculate_pips_profit(self, position):
        """Calcular profit en pips"""
        try:
            tick = mt5.symbol_info_tick(position.symbol)
            if not tick:
                if self.logger:
                    self.logger.log_error('TICK_DATA_ERROR', Exception(f"No tick data for {position.symbol}"), {
                        'symbol': position.symbol,
                        'ticket': position.ticket
                    })
                return 0
            
            current_price = tick.bid if position.type == 0 else tick.ask
            pip_value = self.get_pip_value(position.symbol)
            
            if position.type == 0:  # BUY
                profit_pips = (current_price - position.price_open) / pip_value
            else:  # SELL
                profit_pips = (position.price_open - current_price) / pip_value
            
            # Log datos de mercado
            if self.logger:
                self.logger.log_market_data(position.symbol, {
                    'current_price': current_price,
                    'entry_price': position.price_open,
                    'profit_pips': profit_pips,
                    'profit_usd': position.profit,
                    'position_type': 'BUY' if position.type == 0 else 'SELL'
                })
            
            return profit_pips
        except Exception as e:
            if self.logger:
                self.logger.log_error('PIPS_CALCULATION_ERROR', e, {
                    'symbol': position.symbol,
                    'ticket': position.ticket
                })
            return 0
    
    def apply_breakeven_with_logging(self, position, pips_profit, strategy_mode):
        """Aplicar breakeven con logging completo"""
        try:
            position_key = f"{position.ticket}"
            
            if position_key in self.position_states['breakeven_applied']:
                return False
            
            trigger = self.PROTECTIVE_BREAKEVEN if strategy_mode == 'PROTECTIVE' else self.CONSERVATIVE_BREAKEVEN
            
            if pips_profit < trigger:
                return False
            
            old_sl = position.sl
            pip_value = self.get_pip_value(position.symbol)
            offset = self.BREAKEVEN_OFFSET * pip_value
            
            if position.type == 0:  # BUY
                new_sl = position.price_open + offset
                if old_sl != 0 and new_sl <= old_sl:
                    if self.logger:
                        self.logger.log_risk_action('BREAKEVEN_SKIPPED', {
                            'symbol': position.symbol,
                            'ticket': position.ticket,
                            'reason': 'Current SL is already better',
                            'old_sl': old_sl,
                            'calculated_sl': new_sl,
                            'mode': strategy_mode
                        }, success=True, reason="SL already better")
                    return False
            else:  # SELL
                new_sl = position.price_open - offset
                if old_sl != 0 and new_sl >= old_sl:
                    if self.logger:
                        self.logger.log_risk_action('BREAKEVEN_SKIPPED', {
                            'symbol': position.symbol,
                            'ticket': position.ticket,
                            'reason': 'Current SL is already better',
                            'old_sl': old_sl,
                            'calculated_sl': new_sl,
                            'mode': strategy_mode
                        }, success=True, reason="SL already better")
                    return False
            
            # Log intento de aplicar breakeven
            if self.logger:
                self.logger.log_risk_action('BREAKEVEN_ATTEMPT', {
                    'symbol': position.symbol,
                    'ticket': position.ticket,
                    'old_sl': old_sl,
                    'new_sl': new_sl,
                    'profit_pips': pips_profit,
                    'mode': strategy_mode,
                    'trigger_used': trigger
                }, success=True)
            
            # Aplicar modificación
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": position.ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.position_states['breakeven_applied'].add(position_key)
                
                # Log éxito
                position_data = {
                    'symbol': position.symbol,
                    'ticket': position.ticket,
                    'old_sl': old_sl,
                    'new_sl': new_sl,
                    'profit_pips': pips_profit,
                    'profit_usd': position.profit,
                    'mode': strategy_mode,
                    'secured_pips': self.BREAKEVEN_OFFSET
                }
                
                if self.logger:
                    self.logger.log_risk_action('BREAKEVEN_APPLIED', position_data, success=True)
                
                # Notificar Telegram
                if self.telegram and self.telegram.is_active:
                    telegram_success = self.telegram.send_breakeven_notification(
                        position.symbol, position.ticket, old_sl, new_sl, pips_profit
                    )
                    
                    if self.logger:
                        self.logger.log_telegram_notification('BREAKEVEN_NOTIFICATION', {
                            'symbol': position.symbol,
                            'ticket': position.ticket,
                            'old_sl': old_sl,
                            'new_sl': new_sl
                        }, success=telegram_success)
                
                print(f"[BREAKEVEN {strategy_mode}] {position.symbol} #{position.ticket}: SL {old_sl:.5f} -> {new_sl:.5f}")
                return True
            
            else:
                # Log fallo
                error_msg = f"MT5 Error: {result.comment}"
                if self.logger:
                    self.logger.log_risk_action('BREAKEVEN_FAILED', {
                        'symbol': position.symbol,
                        'ticket': position.ticket,
                        'old_sl': old_sl,
                        'new_sl': new_sl,
                        'mt5_error': result.comment,
                        'mode': strategy_mode
                    }, success=False, reason=error_msg)
                
                print(f"[BREAKEVEN ERROR] {position.symbol} #{position.ticket}: {result.comment}")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.log_error('BREAKEVEN_EXCEPTION', e, {
                    'symbol': position.symbol,
                    'ticket': position.ticket,
                    'strategy_mode': strategy_mode
                })
            print(f"[BREAKEVEN EXCEPTION] {e}")
            return False
    
    def apply_trailing_with_logging(self, position, pips_profit, strategy_mode):
        """Aplicar trailing stop con logging completo"""
        try:
            trigger = self.PROTECTIVE_TRAILING if strategy_mode == 'PROTECTIVE' else self.CONSERVATIVE_TRAILING
            
            if pips_profit < trigger:
                return False
            
            tick = mt5.symbol_info_tick(position.symbol)
            if not tick:
                return False
            
            current_price = tick.bid if position.type == 0 else tick.ask
            pip_value = self.get_pip_value(position.symbol)
            trailing_distance = self.TRAILING_DISTANCE * pip_value
            
            old_sl = position.sl
            
            if position.type == 0:  # BUY
                new_sl = current_price - trailing_distance
                if old_sl != 0 and new_sl <= old_sl:
                    return False
            else:  # SELL
                new_sl = current_price + trailing_distance
                if old_sl != 0 and new_sl >= old_sl:
                    return False
            
            # Log intento
            if self.logger:
                self.logger.log_risk_action('TRAILING_ATTEMPT', {
                    'symbol': position.symbol,
                    'ticket': position.ticket,
                    'old_sl': old_sl,
                    'new_sl': new_sl,
                    'current_price': current_price,
                    'trailing_distance_pips': self.TRAILING_DISTANCE,
                    'profit_pips': pips_profit,
                    'mode': strategy_mode
                }, success=True)
            
            # Aplicar
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": position.ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                position_data = {
                    'symbol': position.symbol,
                    'ticket': position.ticket,
                    'old_sl': old_sl,
                    'new_sl': new_sl,
                    'profit_pips': pips_profit,
                    'mode': strategy_mode,
                    'trailing_distance': self.TRAILING_DISTANCE
                }
                
                if self.logger:
                    self.logger.log_risk_action('TRAILING_APPLIED', position_data, success=True)
                
                # Notificar Telegram
                if self.telegram and self.telegram.is_active:
                    telegram_success = self.telegram.send_trailing_notification(
                        position.symbol, position.ticket, old_sl, new_sl, pips_profit, self.TRAILING_DISTANCE
                    )
                    
                    if self.logger:
                        self.logger.log_telegram_notification('TRAILING_NOTIFICATION', {
                            'symbol': position.symbol,
                            'ticket': position.ticket,
                            'old_sl': old_sl,
                            'new_sl': new_sl
                        }, success=telegram_success)
                
                print(f"[TRAILING {strategy_mode}] {position.symbol} #{position.ticket}: SL {old_sl:.5f} -> {new_sl:.5f}")
                return True
            
            else:
                if self.logger:
                    self.logger.log_risk_action('TRAILING_FAILED', {
                        'symbol': position.symbol,
                        'ticket': position.ticket,
                        'mt5_error': result.comment,
                        'mode': strategy_mode
                    }, success=False, reason=f"MT5 Error: {result.comment}")
                
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.log_error('TRAILING_EXCEPTION', e, {
                    'symbol': position.symbol,
                    'ticket': position.ticket,
                    'strategy_mode': strategy_mode
                })
            return False
    
    def manage_positions_with_logging(self):
        """Gestionar posiciones con logging completo"""
        try:
            positions = mt5.positions_get()
            
            if not positions:
                if self.logger:
                    self.logger.log_system_event('NO_POSITIONS', 'No hay posiciones abiertas')
                return
            
            if self.logger:
                self.logger.log_system_event('POSITION_SCAN_START', f'Iniciando escaneo de {len(positions)} posiciones', {
                    'position_count': len(positions),
                    'tickets': [pos.ticket for pos in positions]
                })
            
            actions_taken = {'breakeven': 0, 'trailing': 0}
            
            for position in positions:
                pips_profit = self.calculate_pips_profit(position)
                
                if pips_profit <= 0:
                    continue
                
                # Determinar modo
                if pips_profit >= 10 or position.profit >= 50:
                    strategy_mode = 'PROTECTIVE'
                else:
                    strategy_mode = 'CONSERVATIVE'
                
                # Aplicar breakeven
                if self.apply_breakeven_with_logging(position, pips_profit, strategy_mode):
                    actions_taken['breakeven'] += 1
                
                # Aplicar trailing
                if self.apply_trailing_with_logging(position, pips_profit, strategy_mode):
                    actions_taken['trailing'] += 1
            
            # Log resumen del ciclo
            if self.logger:
                self.logger.log_system_event('POSITION_SCAN_COMPLETE', 'Escaneo de posiciones completado', {
                    'positions_scanned': len(positions),
                    'breakeven_applied': actions_taken['breakeven'],
                    'trailing_applied': actions_taken['trailing'],
                    'total_actions': sum(actions_taken.values())
                })
            
            # Enviar resumen por Telegram si hubo acciones
            if sum(actions_taken.values()) > 0:
                if self.telegram and self.telegram.is_active:
                    telegram_success = self.telegram.send_protection_summary(
                        actions_taken['breakeven'],
                        actions_taken['trailing'],
                        len(positions)
                    )
                    
                    if self.logger:
                        self.logger.log_telegram_notification('PROTECTION_SUMMARY', actions_taken, success=telegram_success)
            
        except Exception as e:
            if self.logger:
                self.logger.log_error('POSITION_MANAGEMENT_ERROR', e)
            print(f"Error gestionando posiciones: {e}")
    
    def run_system(self, duration_minutes=60):
        """Ejecutar sistema completo con logging"""
        print("="*70)
        print("    SISTEMA DE TRADING CON LOGGING COMPLETO")
        print("="*70)
        
        if not mt5.initialize():
            error_msg = "No se pudo conectar a MT5"
            if self.logger:
                self.logger.log_error('MT5_CONNECTION_ERROR', Exception(error_msg))
            print(f"ERROR: {error_msg}")
            return
        
        # Log inicio del sistema
        if self.logger:
            self.logger.log_system_event('SYSTEM_START', 'Sistema de trading iniciado', {
                'duration_minutes': duration_minutes,
                'parameters': {
                    'protective_breakeven': self.PROTECTIVE_BREAKEVEN,
                    'conservative_breakeven': self.CONSERVATIVE_BREAKEVEN,
                    'protective_trailing': self.PROTECTIVE_TRAILING,
                    'conservative_trailing': self.CONSERVATIVE_TRAILING
                }
            })
        
        # Notificar inicio por Telegram
        if self.telegram and self.telegram.is_active:
            telegram_success = self.telegram.send_alert('success', 
                f'Sistema de trading con logging iniciado\nDuración: {duration_minutes} minutos\n\nTodos los eventos serán registrados en logs detallados'
            )
            
            if self.logger:
                self.logger.log_telegram_notification('SYSTEM_START_ALERT', {
                    'duration_minutes': duration_minutes
                }, success=telegram_success)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        cycle = 0
        
        try:
            while time.time() < end_time and self.running:
                cycle += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Ciclo {cycle:03d}] {current_time}")
                
                if self.logger:
                    self.logger.log_system_event('CYCLE_START', f'Iniciando ciclo {cycle}', {
                        'cycle_number': cycle,
                        'current_time': current_time
                    })
                
                self.manage_positions_with_logging()
                
                # Log métricas de rendimiento cada 10 ciclos
                if cycle % 10 == 0 and self.logger:
                    stats = self.logger.get_current_stats()
                    self.logger.log_performance_metrics({
                        'cycle_number': cycle,
                        'system_stats': stats
                    })
                
                time.sleep(45)
                
        except KeyboardInterrupt:
            print("\n\nSistema detenido por usuario")
            
            if self.logger:
                self.logger.log_system_event('SYSTEM_STOP_USER', 'Sistema detenido por usuario', {
                    'cycles_completed': cycle,
                    'uptime_minutes': (time.time() - start_time) / 60
                })
            
        finally:
            self.running = False
            mt5.shutdown()
            
            # Generar reporte final
            if self.logger:
                self.logger.log_system_event('SYSTEM_SHUTDOWN', 'Sistema finalizando', {
                    'total_cycles': cycle,
                    'final_stats': self.logger.get_current_stats()
                })
                
                # Crear reporte diario
                report = self.logger.create_daily_report()
                print("\n" + "="*70)
                print("REPORTE FINAL:")
                print("="*70)
                print(report)
                
                # Shutdown del logger
                self.logger.shutdown()
            
            print("\nSistema finalizado - Todos los logs guardados")

def main():
    """Función principal"""
    system = TradingSystemWithLogs()
    
    print("\nOPCIONES:")
    print("1. Ejecutar sistema (60 minutos)")
    print("2. Ejecutar sistema (tiempo personalizado)")
    print("3. Solo una revisión")
    
    try:
        opcion = input("Selecciona (1-3): ").strip()
        
        if opcion == '1':
            system.run_system(60)
        elif opcion == '2':
            minutes = input("Minutos a ejecutar: ").strip()
            minutes = int(minutes) if minutes.isdigit() else 60
            system.run_system(minutes)
        elif opcion == '3':
            if mt5.initialize():
                system.manage_positions_with_logging()
                mt5.shutdown()
            else:
                print("Error conectando a MT5")
        else:
            print("Opción no válida")
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()