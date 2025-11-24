#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TRAILING STOP HIBRIDO INTELIGENTE
=================================
Sistema híbrido que ajusta parámetros según las ganancias actuales
Protector para ganancias existentes, conservador para nuevas señales
"""

import MetaTrader5 as mt5
from datetime import datetime
import time

class HybridTrailingManager:
    """Gestor híbrido de trailing stop inteligente"""
    
    def __init__(self):
        # PARAMETROS HIBRIDOS - Se ajustan según ganancias
        self.CONSERVATIVE_BREAKEVEN_TRIGGER = 25  # Para nuevas activaciones
        self.CONSERVATIVE_TRAILING_TRIGGER = 40   # Para nuevas activaciones
        
        # PARAMETROS PROTECTORES - Para posiciones ya ganadoras
        self.PROTECTIVE_BREAKEVEN_TRIGGER = 15    # Más agresivo para proteger
        self.PROTECTIVE_TRAILING_TRIGGER = 20     # Más agresivo para proteger
        
        # OFFSETS Y DISTANCIAS
        self.BREAKEVEN_OFFSET_PIPS = 3
        self.TRAILING_DISTANCE_PIPS = 15
        self.MIN_STEP_PIPS = 5
        
        # ESTADO DE POSICIONES
        self.position_states = {
            'breakeven_applied': set(),
            'trailing_active': set(),
            'protection_mode': set()  # Posiciones en modo protector
        }
    
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
        """Determinar si usar modo conservador o protector"""
        position_key = f"{position.ticket}"
        
        # Criterios para modo protector
        if (pips_profit >= 10 or  # 10+ pips de ganancia
            position.profit >= 50 or  # $50+ de ganancia
            position_key in self.position_states['protection_mode']):
            
            self.position_states['protection_mode'].add(position_key)
            return 'PROTECTIVE'
        else:
            return 'CONSERVATIVE'
    
    def apply_hybrid_breakeven(self, position, pips_profit, strategy_mode):
        """Aplicar breakeven híbrido"""
        try:
            position_key = f"{position.ticket}"
            
            # Ya aplicado
            if position_key in self.position_states['breakeven_applied']:
                return False
            
            # Determinar trigger según modo
            if strategy_mode == 'PROTECTIVE':
                trigger = self.PROTECTIVE_BREAKEVEN_TRIGGER
                mode_desc = "PROTECTOR"
            else:
                trigger = self.CONSERVATIVE_BREAKEVEN_TRIGGER
                mode_desc = "CONSERVADOR"
            
            # Verificar si califica
            if pips_profit < trigger:
                return False
            
            # Calcular nuevo SL
            pip_value = self.get_pip_value(position.symbol)
            offset = self.BREAKEVEN_OFFSET_PIPS * pip_value
            
            if position.type == 0:  # BUY
                new_sl = position.price_open + offset
                if position.sl != 0 and new_sl <= position.sl:
                    return False
            else:  # SELL
                new_sl = position.price_open - offset
                if position.sl != 0 and new_sl >= position.sl:
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
                print(f"✅ [BREAKEVEN {mode_desc}] {position.symbol} #{position.ticket}")
                print(f"   SL: {position.sl:.5f} -> {new_sl:.5f} (+{pips_profit:.1f} pips)")
                return True
            else:
                print(f"❌ Error breakeven: {result.comment}")
                return False
                
        except Exception as e:
            print(f"Error en breakeven híbrido: {e}")
            return False
    
    def apply_hybrid_trailing(self, position, pips_profit, strategy_mode):
        """Aplicar trailing híbrido"""
        try:
            position_key = f"{position.ticket}"
            
            # Determinar trigger según modo
            if strategy_mode == 'PROTECTIVE':
                trigger = self.PROTECTIVE_TRAILING_TRIGGER
                mode_desc = "PROTECTOR"
            else:
                trigger = self.CONSERVATIVE_TRAILING_TRIGGER
                mode_desc = "CONSERVADOR"
            
            # Verificar si califica
            if pips_profit < trigger:
                return False
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(position.symbol)
            if not tick:
                return False
            
            current_price = tick.bid if position.type == 0 else tick.ask
            pip_value = self.get_pip_value(position.symbol)
            trailing_distance = self.TRAILING_DISTANCE_PIPS * pip_value
            min_step = self.MIN_STEP_PIPS * pip_value
            
            # Calcular nuevo trailing SL
            if position.type == 0:  # BUY
                new_sl = current_price - trailing_distance
                if position.sl != 0:
                    improvement = new_sl - position.sl
                    if improvement < min_step:
                        return False
            else:  # SELL
                new_sl = current_price + trailing_distance
                if position.sl != 0:
                    improvement = position.sl - new_sl
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
                print(f"🎯 [TRAILING {mode_desc}] {position.symbol} #{position.ticket}")
                print(f"   SL: {position.sl:.5f} -> {new_sl:.5f} ({trailing_distance/pip_value:.0f} pips dist)")
                return True
            else:
                print(f"❌ Error trailing: {result.comment}")
                return False
                
        except Exception as e:
            print(f"Error en trailing híbrido: {e}")
            return False
    
    def manage_all_positions(self):
        """Gestionar todas las posiciones con lógica híbrida"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        print(f"📊 Gestionando {len(positions)} posiciones con sistema HÍBRIDO...")
        
        breakeven_applied = 0
        trailing_updated = 0
        
        for position in positions:
            pips_profit = self.calculate_pips_profit(position)
            
            if pips_profit <= 0:
                continue  # Solo gestionar posiciones ganadoras
            
            # Determinar estrategia
            strategy_mode = self.determine_strategy_mode(position, pips_profit)
            
            print(f"\n📈 {position.symbol} #{position.ticket}: +{pips_profit:.1f} pips (${position.profit:.2f})")
            print(f"   Modo: {strategy_mode}")
            
            # Aplicar breakeven
            if self.apply_hybrid_breakeven(position, pips_profit, strategy_mode):
                breakeven_applied += 1
            
            # Aplicar trailing
            if self.apply_hybrid_trailing(position, pips_profit, strategy_mode):
                trailing_updated += 1
        
        if breakeven_applied > 0 or trailing_updated > 0:
            print(f"\n✨ RESUMEN: {breakeven_applied} breakeven, {trailing_updated} trailing aplicados")
    
    def run_continuous_hybrid(self, duration_minutes=30):
        """Ejecutar sistema híbrido continuamente"""
        print("="*70)
        print("    TRAILING STOP HÍBRIDO INTELIGENTE")
        print("="*70)
        print("CONFIGURACIÓN HÍBRIDA:")
        print(f"• MODO CONSERVADOR: Breakeven {self.CONSERVATIVE_BREAKEVEN_TRIGGER} pips, Trailing {self.CONSERVATIVE_TRAILING_TRIGGER} pips")
        print(f"• MODO PROTECTOR: Breakeven {self.PROTECTIVE_BREAKEVEN_TRIGGER} pips, Trailing {self.PROTECTIVE_TRAILING_TRIGGER} pips")
        print(f"• Distancia trailing: {self.TRAILING_DISTANCE_PIPS} pips")
        print(f"• Frecuencia: Cada 30 segundos")
        print("="*70)
        
        if not mt5.initialize():
            print("❌ No se pudo conectar a MT5")
            return
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        cycle = 0
        
        try:
            while time.time() < end_time:
                cycle += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Ciclo Híbrido {cycle:03d}] {current_time}")
                self.manage_all_positions()
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n⏹️ Sistema híbrido detenido")
        finally:
            mt5.shutdown()
            print("✅ Sistema híbrido finalizado")

def main():
    """Función principal"""
    manager = HybridTrailingManager()
    
    print("SISTEMA HÍBRIDO DE TRAILING STOP")
    print("================================")
    print("¿Ejecutar análisis inmediato? (s/n): ", end="")
    
    if input().lower().startswith('s'):
        if mt5.initialize():
            print("\n🔍 ANÁLISIS INMEDIATO:")
            manager.manage_all_positions()
            mt5.shutdown()
            print()
    
    print("¿Ejecutar sistema híbrido continuo? (s/n): ", end="")
    if input().lower().startswith('s'):
        duration = input("¿Por cuántos minutos? (default 30): ").strip()
        duration = int(duration) if duration.isdigit() else 30
        manager.run_continuous_hybrid(duration)
    else:
        print("✅ Análisis completado")

if __name__ == "__main__":
    main()