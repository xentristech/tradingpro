#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEJORADOR DE BREAKEVEN Y TRAILING STOP
=====================================
Aplica y mejora la gestión de breakeven y trailing stop en tiempo real
"""

import MetaTrader5 as mt5
import time
from datetime import datetime
import logging

class BreakevenTrailingManager:
    """Gestor mejorado de Breakeven y Trailing Stop"""
    
    def __init__(self):
        # PARAMETROS CONSERVADORES PARA MERCADOS CON OSCILACIONES
        self.BREAKEVEN_TRIGGER_PIPS = 25   # Aumentado para dar más espacio
        self.BREAKEVEN_OFFSET_PIPS = 5     # Mayor offset para protección
        self.TRAILING_TRIGGER_PIPS = 40    # Aumentado significativamente 
        self.TRAILING_DISTANCE_PIPS = 20   # Mayor distancia para oscilaciones
        self.TRAILING_STEP_PIPS = 8        # Pasos más grandes, menos actualizaciones
        
        self.position_states = {
            'breakeven_applied': set(),
            'trailing_active': set(),
            'last_trailing_price': {}
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('BreakevenTrailing')
        
    def get_pip_value(self, symbol):
        """Obtener valor de pip para símbolo"""
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
    
    def apply_breakeven(self, position):
        """Aplicar breakeven mejorado"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            position_key = f"{ticket}"
            
            # Verificar si ya se aplicó breakeven
            if position_key in self.position_states['breakeven_applied']:
                return False
            
            entry_price = position.price_open
            pip_value = self.get_pip_value(symbol)
            offset = self.BREAKEVEN_OFFSET_PIPS * pip_value
            
            # Calcular nuevo SL en breakeven
            if position.type == 0:  # BUY
                new_sl = entry_price + offset
                # Solo aplicar si es mejor que el SL actual
                if position.sl != 0 and new_sl <= position.sl:
                    return False
            else:  # SELL
                new_sl = entry_price - offset
                # Solo aplicar si es mejor que el SL actual
                if position.sl != 0 and new_sl >= position.sl:
                    return False
            
            # Aplicar modificación
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.position_states['breakeven_applied'].add(position_key)
                self.logger.info(f"✅ [BREAKEVEN] {symbol} #{ticket}: SL -> {new_sl:.5f}")
                return True
            else:
                self.logger.error(f"❌ [BREAKEVEN ERROR] {symbol} #{ticket}: {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error aplicando breakeven: {e}")
            return False
    
    def apply_trailing_stop(self, position):
        """Aplicar trailing stop mejorado"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            position_key = f"{ticket}"
            
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False
            
            current_price = tick.bid if position.type == 0 else tick.ask
            pip_value = self.get_pip_value(symbol)
            trailing_distance = self.TRAILING_DISTANCE_PIPS * pip_value
            step_size = self.TRAILING_STEP_PIPS * pip_value
            
            # Calcular nuevo trailing SL
            if position.type == 0:  # BUY
                new_sl = current_price - trailing_distance
                # Solo actualizar si mejora el SL actual por al menos step_size
                if position.sl != 0:
                    improvement = new_sl - position.sl
                    if improvement < step_size:
                        return False
            else:  # SELL
                new_sl = current_price + trailing_distance
                # Solo actualizar si mejora el SL actual por al menos step_size
                if position.sl != 0:
                    improvement = position.sl - new_sl
                    if improvement < step_size:
                        return False
            
            # Aplicar modificación
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.position_states['trailing_active'].add(position_key)
                self.position_states['last_trailing_price'][position_key] = current_price
                self.logger.info(f"🎯 [TRAILING] {symbol} #{ticket}: SL {position.sl:.5f} -> {new_sl:.5f}")
                return True
            else:
                self.logger.error(f"❌ [TRAILING ERROR] {symbol} #{ticket}: {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error aplicando trailing: {e}")
            return False
    
    def manage_all_positions(self):
        """Gestionar todas las posiciones"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        self.logger.info(f"📊 Gestionando {len(positions)} posiciones...")
        
        breakeven_applied = 0
        trailing_updated = 0
        
        for position in positions:
            pips_profit = self.calculate_pips_profit(position)
            
            if pips_profit <= 0:
                continue  # Solo gestionar posiciones ganadoras
            
            symbol = position.symbol
            ticket = position.ticket
            
            self.logger.info(f"📈 {symbol} #{ticket}: +{pips_profit:.1f} pips (${position.profit:.2f})")
            
            # Aplicar breakeven si califica
            if pips_profit >= self.BREAKEVEN_TRIGGER_PIPS:
                if self.apply_breakeven(position):
                    breakeven_applied += 1
                    self.logger.info(f"🟢 Breakeven aplicado con +{pips_profit:.1f} pips")
            
            # Aplicar trailing si califica
            if pips_profit >= self.TRAILING_TRIGGER_PIPS:
                if self.apply_trailing_stop(position):
                    trailing_updated += 1
                    self.logger.info(f"🔥 Trailing actualizado con +{pips_profit:.1f} pips")
        
        if breakeven_applied > 0 or trailing_updated > 0:
            self.logger.info(f"✨ Resumen: {breakeven_applied} breakeven, {trailing_updated} trailing")
    
    def run_continuous(self, duration_minutes=60):
        """Ejecutar continuamente por X minutos"""
        self.logger.info(f"🚀 Iniciando gestión continua por {duration_minutes} minutos...")
        
        if not mt5.initialize():
            self.logger.error("❌ No se pudo conectar a MT5")
            return
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        cycle = 0
        
        try:
            while time.time() < end_time:
                cycle += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                self.logger.info(f"\n[Ciclo {cycle:03d}] {current_time}")
                self.manage_all_positions()
                
                # Esperar 30 segundos (menos frecuente para evitar sobreajustes)
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Detenido por usuario")
        finally:
            mt5.shutdown()
            self.logger.info("✅ Gestor finalizado")

def main():
    """Función principal"""
    print("="*60)
    print("    MEJORADOR DE BREAKEVEN Y TRAILING STOP")
    print("="*60)
    print("Configuración CONSERVADORA para mercados oscilantes:")
    print("• Breakeven: 25 pips -> +5 pips (más espacio)")
    print("• Trailing: 40 pips -> 20 pips distancia (anti-oscilación)")  
    print("• Actualización: Cada 8 pips (menos frecuente)")
    print("• Frecuencia: Cada 30 segundos (más estable)")
    print("="*60)
    
    manager = BreakevenTrailingManager()
    
    # Hacer una pasada inmediata
    if mt5.initialize():
        print("\n🔍 REVISIÓN INICIAL:")
        manager.manage_all_positions()
        mt5.shutdown()
    
    # Preguntar si ejecutar continuamente
    print(f"\n¿Ejecutar continuamente? (y/n): ", end="")
    if input().lower().startswith('y'):
        manager.run_continuous(60)  # 60 minutos
    else:
        print("✅ Revisión completada")

if __name__ == "__main__":
    main()