#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TRAILING STOP CON NOTIFICACIONES TELEGRAM
=========================================
Sistema de trailing stop que notifica por Telegram cada acción
"""

import MetaTrader5 as mt5
import sys
from datetime import datetime
from pathlib import Path
import time

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.notifiers.telegram_notifier import TelegramNotifier
except ImportError as e:
    print(f"Error importando TelegramNotifier: {e}")
    TelegramNotifier = None

class TrailingWithTelegram:
    """Sistema de trailing stop con notificaciones Telegram"""
    
    def __init__(self):
        # Inicializar Telegram
        self.telegram = TelegramNotifier() if TelegramNotifier else None
        
        # PARAMETROS HIBRIDOS
        self.CONSERVATIVE_BREAKEVEN = 25  # Para nuevas activaciones
        self.PROTECTIVE_BREAKEVEN = 15    # Para posiciones ya ganadoras
        
        self.CONSERVATIVE_TRAILING = 40   # Para nuevas activaciones
        self.PROTECTIVE_TRAILING = 20     # Para posiciones ya ganadoras
        
        self.BREAKEVEN_OFFSET = 3
        self.TRAILING_DISTANCE = 15
        self.MIN_STEP = 5
        
        # Estados
        self.position_states = {
            'breakeven_applied': set(),
            'trailing_active': set(),
            'protection_mode': set()
        }
        
        if self.telegram and self.telegram.is_active:
            print("✅ Telegram conectado - Las acciones serán notificadas")
        else:
            print("⚠️ Telegram no disponible - Solo logs locales")
    
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
                profit_pips = (current_price - position.price_open) / pip_value
            else:  # SELL
                profit_pips = (position.price_open - current_price) / pip_value
            
            return profit_pips
        except:
            return 0
    
    def determine_strategy_mode(self, position, pips_profit):
        """Determinar modo conservador o protector"""
        position_key = f"{position.ticket}"
        
        if (pips_profit >= 10 or 
            position.profit >= 50 or 
            position_key in self.position_states['protection_mode']):
            
            self.position_states['protection_mode'].add(position_key)
            return 'PROTECTIVE'
        else:
            return 'CONSERVATIVE'
    
    def apply_breakeven_with_telegram(self, position, pips_profit, strategy_mode):
        """Aplicar breakeven y notificar por Telegram"""
        try:
            position_key = f"{position.ticket}"
            
            if position_key in self.position_states['breakeven_applied']:
                return False
            
            # Determinar trigger
            trigger = self.PROTECTIVE_BREAKEVEN if strategy_mode == 'PROTECTIVE' else self.CONSERVATIVE_BREAKEVEN
            
            if pips_profit < trigger:
                return False
            
            # Calcular nuevo SL
            pip_value = self.get_pip_value(position.symbol)
            offset = self.BREAKEVEN_OFFSET * pip_value
            old_sl = position.sl
            
            if position.type == 0:  # BUY
                new_sl = position.price_open + offset
                if old_sl != 0 and new_sl <= old_sl:
                    return False
            else:  # SELL
                new_sl = position.price_open - offset
                if old_sl != 0 and new_sl >= old_sl:
                    return False
            
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
                
                print(f"🛡️ [BREAKEVEN {strategy_mode}] {position.symbol} #{position.ticket}")
                print(f"   SL: {old_sl:.5f} -> {new_sl:.5f} (+{pips_profit:.1f} pips)")
                
                # NOTIFICAR POR TELEGRAM
                if self.telegram and self.telegram.is_active:
                    self.telegram.send_breakeven_notification(
                        position.symbol,
                        position.ticket,
                        old_sl,
                        new_sl,
                        pips_profit
                    )
                
                return True
            else:
                print(f"❌ Error breakeven: {result.comment}")
                return False
                
        except Exception as e:
            print(f"Error en breakeven: {e}")
            return False
    
    def apply_trailing_with_telegram(self, position, pips_profit, strategy_mode):
        """Aplicar trailing stop y notificar por Telegram"""
        try:
            position_key = f"{position.ticket}"
            
            # Determinar trigger
            trigger = self.PROTECTIVE_TRAILING if strategy_mode == 'PROTECTIVE' else self.CONSERVATIVE_TRAILING
            
            if pips_profit < trigger:
                return False
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(position.symbol)
            if not tick:
                return False
            
            current_price = tick.bid if position.type == 0 else tick.ask
            pip_value = self.get_pip_value(position.symbol)
            trailing_distance = self.TRAILING_DISTANCE * pip_value
            min_step = self.MIN_STEP * pip_value
            
            old_sl = position.sl
            
            # Calcular nuevo trailing SL
            if position.type == 0:  # BUY
                new_sl = current_price - trailing_distance
                if old_sl != 0:
                    improvement = new_sl - old_sl
                    if improvement < min_step:
                        return False
            else:  # SELL
                new_sl = current_price + trailing_distance
                if old_sl != 0:
                    improvement = old_sl - new_sl
                    if improvement < min_step:
                        return False
            
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
                self.position_states['trailing_active'].add(position_key)
                
                print(f"🎯 [TRAILING {strategy_mode}] {position.symbol} #{position.ticket}")
                print(f"   SL: {old_sl:.5f} -> {new_sl:.5f} ({self.TRAILING_DISTANCE} pips dist)")
                
                # NOTIFICAR POR TELEGRAM
                if self.telegram and self.telegram.is_active:
                    self.telegram.send_trailing_notification(
                        position.symbol,
                        position.ticket,
                        old_sl,
                        new_sl,
                        pips_profit,
                        self.TRAILING_DISTANCE
                    )
                
                return True
            else:
                print(f"❌ Error trailing: {result.comment}")
                return False
                
        except Exception as e:
            print(f"Error en trailing: {e}")
            return False
    
    def manage_positions_with_telegram(self):
        """Gestionar posiciones y notificar por Telegram"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        print(f"📊 Gestionando {len(positions)} posiciones...")
        
        breakeven_applied = 0
        trailing_updated = 0
        
        for position in positions:
            pips_profit = self.calculate_pips_profit(position)
            
            if pips_profit <= 0:
                continue
            
            strategy_mode = self.determine_strategy_mode(position, pips_profit)
            
            print(f"\n📈 {position.symbol} #{position.ticket}: +{pips_profit:.1f} pips (${position.profit:.2f})")
            print(f"   Modo: {strategy_mode}")
            
            # Aplicar breakeven
            if self.apply_breakeven_with_telegram(position, pips_profit, strategy_mode):
                breakeven_applied += 1
            
            # Aplicar trailing
            if self.apply_trailing_with_telegram(position, pips_profit, strategy_mode):
                trailing_updated += 1
        
        # ENVIAR RESUMEN POR TELEGRAM
        if (breakeven_applied > 0 or trailing_updated > 0) and self.telegram and self.telegram.is_active:
            self.telegram.send_protection_summary(
                breakeven_applied,
                trailing_updated,
                len(positions)
            )
        
        if breakeven_applied > 0 or trailing_updated > 0:
            print(f"\n✨ RESUMEN: {breakeven_applied} breakeven, {trailing_updated} trailing aplicados")
    
    def run_single_check(self):
        """Ejecutar una revisión única"""
        print("="*70)
        print("    TRAILING STOP CON NOTIFICACIONES TELEGRAM")
        print("="*70)
        
        if not mt5.initialize():
            print("❌ No se pudo conectar a MT5")
            return
        
        try:
            print(f"🔍 REVISIÓN: {datetime.now().strftime('%H:%M:%S')}")
            self.manage_positions_with_telegram()
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            mt5.shutdown()
            print("✅ Revisión completada")
    
    def run_continuous(self, duration_minutes=60):
        """Ejecutar continuamente con notificaciones"""
        print("="*70)
        print("    TRAILING STOP CONTINUO CON TELEGRAM")
        print("="*70)
        
        if not mt5.initialize():
            print("❌ No se pudo conectar a MT5")
            return
        
        # Notificar inicio del sistema
        if self.telegram and self.telegram.is_active:
            self.telegram.send_alert(
                'success',
                f'🚀 Risk Manager iniciado\nDuración: {duration_minutes} minutos\n\nSistema híbrido activo:\n• Breakeven conservador: {self.CONSERVATIVE_BREAKEVEN} pips\n• Breakeven protector: {self.PROTECTIVE_BREAKEVEN} pips\n• Trailing conservador: {self.CONSERVATIVE_TRAILING} pips\n• Trailing protector: {self.PROTECTIVE_TRAILING} pips'
            )
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        cycle = 0
        
        try:
            while time.time() < end_time:
                cycle += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Ciclo {cycle:03d}] {current_time}")
                self.manage_positions_with_telegram()
                
                time.sleep(45)  # Cada 45 segundos
                
        except KeyboardInterrupt:
            print("\n⏹️ Sistema detenido por usuario")
            
            if self.telegram and self.telegram.is_active:
                self.telegram.send_alert('warning', '⏹️ Risk Manager detenido manualmente')
                
        finally:
            mt5.shutdown()
            print("✅ Sistema finalizado")

def main():
    """Función principal"""
    manager = TrailingWithTelegram()
    
    print("OPCIONES:")
    print("1. Revisión única")
    print("2. Sistema continuo (60 minutos)")
    
    opcion = input("Selecciona (1-2): ").strip()
    
    if opcion == '1':
        manager.run_single_check()
    elif opcion == '2':
        duration = input("¿Por cuántos minutos? (default 60): ").strip()
        duration = int(duration) if duration.isdigit() else 60
        manager.run_continuous(duration)
    else:
        print("Opción inválida")

if __name__ == "__main__":
    main()