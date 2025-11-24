#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA TRADING CORREGIDO - BREAKEVEN MANUAL, TRAILING AUTOMÁTICO
================================================================
Breakeven: Se sugiere por Telegram, pero aplicación MANUAL
Trailing Stop: Automático siguiendo el precio
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

class CorrectedTradingSystem:
    """Sistema de trading corregido - Breakeven manual, Trailing automático"""
    
    def __init__(self):
        # Inicializar componentes
        self.telegram = TelegramNotifier() if TelegramNotifier else None
        self.logger = comprehensive_logger if comprehensive_logger else None
        
        # Parámetros del sistema
        self.BREAKEVEN_SUGGESTION_PIPS = 15  # Cuando sugerir breakeven
        self.TRAILING_TRIGGER_PIPS = 25      # Cuando activar trailing automático
        self.TRAILING_DISTANCE_PIPS = 15     # Distancia del trailing
        
        # Estados
        self.position_states = {
            'breakeven_suggested': set(),      # Solo sugerencias enviadas
            'trailing_active': set(),          # Trailing automático activo
            'manual_breakeven_applied': set()  # Breakeven aplicados manualmente
        }
        
        self.running = True
        
        # Log de inicialización
        if self.logger:
            self.logger.log_system_event('CORRECTED_SYSTEM_INIT', 'Sistema corregido inicializado', {
                'breakeven_mode': 'MANUAL_SUGGESTION',
                'trailing_mode': 'AUTOMATIC',
                'breakeven_suggestion_pips': self.BREAKEVEN_SUGGESTION_PIPS,
                'trailing_trigger_pips': self.TRAILING_TRIGGER_PIPS,
                'trailing_distance_pips': self.TRAILING_DISTANCE_PIPS
            })
        
        print("Sistema de trading corregido inicializado")
        print("BREAKEVEN: Manual (solo sugerencias por Telegram)")
        print("TRAILING STOP: Automático")
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
                return 0
            
            current_price = tick.bid if position.type == 0 else tick.ask
            pip_value = self.get_pip_value(position.symbol)
            
            if position.type == 0:  # BUY
                pips_profit = (current_price - position.price_open) / pip_value
            else:  # SELL
                pips_profit = (position.price_open - current_price) / pip_value
            
            # Log datos de mercado
            if self.logger:
                self.logger.log_market_data(position.symbol, {
                    'current_price': current_price,
                    'entry_price': position.price_open,
                    'profit_pips': pips_profit,
                    'profit_usd': position.profit,
                    'position_type': 'BUY' if position.type == 0 else 'SELL'
                })
            
            return pips_profit
        except Exception as e:
            if self.logger:
                self.logger.log_error('PIPS_CALCULATION_ERROR', f'Error calculando pips: {e}', {
                    'symbol': position.symbol,
                    'ticket': position.ticket
                })
            return 0
    
    def suggest_breakeven(self, position, pips_profit):
        """Sugerir breakeven por Telegram (NO aplicar automáticamente)"""
        try:
            position_key = f"{position.ticket}"
            
            if position_key in self.position_states['breakeven_suggested']:
                return False
            
            if pips_profit < self.BREAKEVEN_SUGGESTION_PIPS:
                return False
            
            # Calcular donde debería ir el breakeven
            pip_value = self.get_pip_value(position.symbol)
            offset = 3 * pip_value  # 3 pips de offset
            
            if position.type == 0:  # BUY
                suggested_sl = position.price_open + offset
            else:  # SELL
                suggested_sl = position.price_open - offset
            
            # Verificar si ya tiene SL en breakeven
            current_sl = position.sl
            if current_sl != 0:
                if position.type == 0 and current_sl >= position.price_open:
                    # Ya tiene breakeven en BUY
                    self.position_states['manual_breakeven_applied'].add(position_key)
                    self.position_states['breakeven_suggested'].add(position_key)
                    return False
                elif position.type == 1 and current_sl <= position.price_open:
                    # Ya tiene breakeven en SELL
                    self.position_states['manual_breakeven_applied'].add(position_key)
                    self.position_states['breakeven_suggested'].add(position_key)
                    return False
            
            # Enviar sugerencia por Telegram
            if self.telegram and self.telegram.is_active:
                message = f"🎯 **SUGERENCIA BREAKEVEN**\\n\\n"
                message += f"Símbolo: {position.symbol}\\n"
                message += f"Ticket: #{position.ticket}\\n"
                message += f"Ganancia: {pips_profit:.1f} pips (${position.profit:.2f})\\n"
                message += f"Precio entrada: {position.price_open:.5f}\\n"
                message += f"SL sugerido: {suggested_sl:.5f}\\n"
                message += f"\\n⚠️ **APLICAR MANUALMENTE**\\n"
                message += f"El sistema NO aplicará breakeven automáticamente"
                
                success = self.telegram.send_message(message)
                
                if success:
                    self.position_states['breakeven_suggested'].add(position_key)
                    
                    # Log sugerencia
                    if self.logger:
                        self.logger.log_risk_action('BREAKEVEN_SUGGESTED', {
                            'symbol': position.symbol,
                            'ticket': position.ticket,
                            'current_sl': current_sl,
                            'suggested_sl': suggested_sl,
                            'profit_pips': pips_profit,
                            'profit_usd': position.profit,
                            'requires_manual_action': True
                        }, success=True)
                    
                    print(f"    >> BREAKEVEN SUGERIDO para {position.symbol} #{position.ticket}")
                    print(f"       Ganancia: {pips_profit:.1f} pips -> SL sugerido: {suggested_sl:.5f}")
                    print(f"       ⚠️  APLICAR MANUALMENTE")
                    
                    return True
            
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.log_error('BREAKEVEN_SUGGESTION_ERROR', f'Error sugiriendo breakeven: {e}', {
                    'symbol': position.symbol,
                    'ticket': position.ticket
                })
            return False
    
    def apply_trailing_stop(self, position, pips_profit):
        """Aplicar trailing stop automáticamente"""
        try:
            position_key = f"{position.ticket}"
            
            if pips_profit < self.TRAILING_TRIGGER_PIPS:
                return False
            
            pip_value = self.get_pip_value(position.symbol)
            trailing_distance = self.TRAILING_DISTANCE_PIPS * pip_value
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(position.symbol)
            if not tick:
                return False
            
            current_price = tick.bid if position.type == 0 else tick.ask
            old_sl = position.sl
            
            # Calcular nuevo trailing SL
            if position.type == 0:  # BUY
                new_sl = current_price - trailing_distance
                should_apply = (old_sl == 0 or new_sl > old_sl)
            else:  # SELL
                new_sl = current_price + trailing_distance
                should_apply = (old_sl == 0 or new_sl < old_sl)
            
            if not should_apply:
                return False
            
            # Aplicar trailing stop
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
                self.position_states['trailing_active'].add(position_key)
                
                # Log éxito
                if self.logger:
                    self.logger.log_risk_action('TRAILING_APPLIED', {
                        'symbol': position.symbol,
                        'ticket': position.ticket,
                        'old_sl': old_sl,
                        'new_sl': new_sl,
                        'current_price': current_price,
                        'trailing_distance_pips': self.TRAILING_DISTANCE_PIPS,
                        'profit_pips': pips_profit,
                        'profit_usd': position.profit
                    }, success=True)
                
                print(f"    >> TRAILING STOP APLICADO para {position.symbol} #{position.ticket}")
                print(f"       SL: {old_sl:.5f} -> {new_sl:.5f} (Distancia: {self.TRAILING_DISTANCE_PIPS} pips)")
                
                # Notificar por Telegram
                if self.telegram and self.telegram.is_active:
                    message = f"📈 **TRAILING STOP APLICADO**\\n\\n"
                    message += f"Símbolo: {position.symbol}\\n"
                    message += f"Ticket: #{position.ticket}\\n"
                    message += f"SL anterior: {old_sl:.5f}\\n"
                    message += f"SL nuevo: {new_sl:.5f}\\n"
                    message += f"Ganancia: {pips_profit:.1f} pips\\n"
                    message += f"Distancia trailing: {self.TRAILING_DISTANCE_PIPS} pips"
                    
                    self.telegram.send_message(message)
                
                return True
            else:
                # Log error
                if self.logger:
                    self.logger.log_risk_action('TRAILING_FAILED', {
                        'symbol': position.symbol,
                        'ticket': position.ticket,
                        'error_code': result.retcode,
                        'error_comment': result.comment,
                        'attempted_sl': new_sl
                    }, success=False, reason=result.comment)
                
                print(f"    >> ERROR aplicando trailing: {result.comment}")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.log_error('TRAILING_STOP_ERROR', f'Error aplicando trailing stop: {e}', {
                    'symbol': position.symbol,
                    'ticket': position.ticket
                })
            return False
    
    def monitor_positions_cycle(self):
        """Un ciclo de monitoreo de posiciones"""
        try:
            if not mt5.initialize():
                print("ERROR: No se pudo conectar a MT5")
                return {'suggestions': 0, 'trailing': 0}
            
            positions = mt5.positions_get()
            
            if not positions:
                return {'suggestions': 0, 'trailing': 0}
            
            if self.logger:
                self.logger.log_system_event('POSITION_SCAN_START', f'Iniciando escaneo de {len(positions)} posiciones', {
                    'position_count': len(positions),
                    'tickets': [pos.ticket for pos in positions]
                })
            
            actions_taken = {'suggestions': 0, 'trailing': 0}
            
            for position in positions:
                pips_profit = self.calculate_pips_profit(position)
                
                if pips_profit <= 0:
                    continue  # Solo procesar posiciones en ganancia
                
                print(f"  {position.symbol} #{position.ticket}: {pips_profit:.1f} pips (${position.profit:.2f})")
                
                # 1. SUGERIR BREAKEVEN (no aplicar)
                if self.suggest_breakeven(position, pips_profit):
                    actions_taken['suggestions'] += 1
                
                # 2. APLICAR TRAILING STOP (automático)
                if self.apply_trailing_stop(position, pips_profit):
                    actions_taken['trailing'] += 1
            
            if self.logger:
                self.logger.log_system_event('POSITION_SCAN_COMPLETE', 'Escaneo de posiciones completado', {
                    'positions_scanned': len(positions),
                    'breakeven_suggested': actions_taken['suggestions'],
                    'trailing_applied': actions_taken['trailing'],
                    'total_actions': sum(actions_taken.values())
                })
            
            return actions_taken
            
        except Exception as e:
            if self.logger:
                self.logger.log_error('MONITOR_CYCLE_ERROR', f'Error en ciclo de monitoreo: {e}')
            return {'suggestions': 0, 'trailing': 0}
    
    def run_system(self, duration_minutes=60):
        """Ejecutar sistema por tiempo determinado"""
        try:
            if self.logger:
                self.logger.log_system_event('SYSTEM_START', 'Sistema corregido iniciado', {
                    'duration_minutes': duration_minutes,
                    'breakeven_mode': 'SUGGESTION_ONLY',
                    'trailing_mode': 'AUTOMATIC'
                })
            
            # Notificar inicio por Telegram
            if self.telegram and self.telegram.is_active:
                message = f"🚀 **SISTEMA CORREGIDO INICIADO**\\n\\n"
                message += f"Duración: {duration_minutes} minutos\\n\\n"
                message += f"**BREAKEVEN**: Solo sugerencias\\n"
                message += f"- Trigger: {self.BREAKEVEN_SUGGESTION_PIPS} pips\\n"
                message += f"- Acción: Manual (tú decides)\\n\\n"
                message += f"**TRAILING STOP**: Automático\\n"
                message += f"- Trigger: {self.TRAILING_TRIGGER_PIPS} pips\\n"
                message += f"- Distancia: {self.TRAILING_DISTANCE_PIPS} pips\\n"
                message += f"- Acción: Automática"
                
                self.telegram.send_message(message)
            
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)
            cycle = 0
            total_suggestions = 0
            total_trailing = 0
            
            print("INICIANDO SISTEMA CORREGIDO...")
            print(f"- Duración: {duration_minutes} minutos")
            print(f"- Breakeven: SOLO SUGERENCIAS ({self.BREAKEVEN_SUGGESTION_PIPS} pips)")
            print(f"- Trailing: AUTOMÁTICO ({self.TRAILING_TRIGGER_PIPS} pips)")
            print("="*70)
            
            while time.time() < end_time and self.running:
                cycle += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Ciclo {cycle:03d}] {current_time}")
                
                if self.logger:
                    self.logger.log_system_event('CYCLE_START', f'Iniciando ciclo {cycle}', {
                        'cycle_number': cycle,
                        'current_time': current_time
                    })
                
                actions = self.monitor_positions_cycle()
                
                total_suggestions += actions['suggestions']
                total_trailing += actions['trailing']
                
                if actions['suggestions'] > 0 or actions['trailing'] > 0:
                    print(f"  ACCIONES: {actions['suggestions']} sugerencias, {actions['trailing']} trailing aplicados")
                
                # Esperar 45 segundos
                time.sleep(45)
            
            # Resumen final
            print(f"\n{'='*70}")
            print("SISTEMA DETENIDO")
            print(f"Total sugerencias breakeven enviadas: {total_suggestions}")
            print(f"Total trailing stops aplicados: {total_trailing}")
            
            if self.telegram and self.telegram.is_active:
                message = f"🛑 **SISTEMA DETENIDO**\\n\\n"
                message += f"**Resumen de {duration_minutes} minutos:**\\n"
                message += f"- Sugerencias breakeven: {total_suggestions}\\n"
                message += f"- Trailing aplicados: {total_trailing}\\n\\n"
                message += f"**Recuerda**: Los breakeven sugeridos requieren aplicación manual"
                
                self.telegram.send_message(message)
            
            if self.logger:
                self.logger.log_system_event('SYSTEM_COMPLETE', 'Sistema completado exitosamente', {
                    'duration_minutes': duration_minutes,
                    'total_cycles': cycle,
                    'total_suggestions': total_suggestions,
                    'total_trailing_applied': total_trailing
                })
            
        except KeyboardInterrupt:
            print(f"\n\nSISTEMA INTERRUMPIDO")
            print(f"Sugerencias enviadas: {total_suggestions}")
            print(f"Trailing aplicados: {total_trailing}")
            
        finally:
            mt5.shutdown()

def main():
    """Función principal"""
    system = CorrectedTradingSystem()
    
    print("\nOPCIONES:")
    print("1. Ejecutar sistema (60 minutos)")
    print("2. Ejecutar sistema (tiempo personalizado)")
    print("3. Solo una revisión")
    
    try:
        opcion = input("Selecciona (1-3): ").strip()
        
        if opcion == '1':
            system.run_system(60)
        elif opcion == '2':
            minutos = int(input("Minutos de ejecución: "))
            system.run_system(minutos)
        elif opcion == '3':
            actions = system.monitor_positions_cycle()
            print(f"Revisión completada: {actions['suggestions']} sugerencias, {actions['trailing']} trailing aplicados")
        else:
            print("Opción no válida")
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()