#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA TRADING CORREGIDO Y MEJORADO - VERSION DEFINITIVA
=========================================================
Sistema completo con generación de señales IA + gestión avanzada de riesgo
Incluye breakeven automático y trailing stop integrados
"""

import os
import sys
import threading
import time
import logging
from pathlib import Path
from datetime import datetime
import MetaTrader5 as mt5

# Configurar encoding para Windows
if sys.platform == 'win32':
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except:
        locale.setlocale(locale.LC_ALL, '')

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))
sys.path.insert(0, str(project_path / 'src'))

class TradingSystemManager:
    """Gestor principal del sistema de trading completo"""
    
    def __init__(self):
        self.running = True
        self.signal_generator = None
        self.statistics = {
            'signals_generated': 0,
            'trades_executed': 0,
            'breakeven_applied': 0,
            'trailing_updates': 0,
            'positions_protected': 0
        }
        
        # Configuración de Risk Management - PARAMETROS CONSERVADORES
        self.ENABLE_BREAKEVEN = True
        self.ENABLE_TRAILING_STOP = True
        self.BREAKEVEN_TRIGGER_PIPS = 25   # Mayor trigger para dar espacio
        self.BREAKEVEN_OFFSET_PIPS = 5     # Mayor offset para protección
        self.TRAILING_TRIGGER_PIPS = 40    # Activar trailing con más ganancias
        self.TRAILING_DISTANCE_PIPS = 20   # Mayor distancia para oscilaciones
        self.position_states = {}  # Para tracking de posiciones
        
        self.setup_logging()
    
    def setup_logging(self):
        """Configurar logging del sistema"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/trading_system.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TradingSystem')
    
    def initialize_mt5(self):
        """Inicializar MT5 con manejo robusto de errores"""
        try:
            # Cerrar cualquier conexión existente
            mt5.shutdown()
            time.sleep(2)
            
            # Inicializar MT5
            if not mt5.initialize():
                self.logger.error("No se pudo inicializar MT5")
                return False
            
            # Verificar información de cuenta
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("No se pudo obtener información de cuenta")
                return False
            
            self.logger.info(f"MT5 conectado - Cuenta: {account_info.login}")
            self.logger.info(f"Balance: ${account_info.balance:.2f}")
            self.logger.info(f"Servidor: {account_info.server}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando MT5: {e}")
            return False
    
    def get_symbol_pip_value(self, symbol):
        """Obtener valor de pip para un símbolo"""
        if symbol.startswith(('EUR', 'GBP', 'AUD', 'NZD')):
            return 0.0001  # 4 decimales
        elif 'JPY' in symbol:
            return 0.01    # 2 decimales
        else:
            return 1.0     # Oro, crypto, indices
    
    def calculate_pips_profit(self, position):
        """Calcular profit en pips para una posición"""
        try:
            symbol = position.symbol
            entry_price = position.price_open
            position_type = position.type
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return 0
            
            current_price = tick.bid if position_type == 0 else tick.ask
            pip_value = self.get_symbol_pip_value(symbol)
            
            if position_type == 0:  # BUY
                profit_pips = (current_price - entry_price) / pip_value
            else:  # SELL
                profit_pips = (entry_price - current_price) / pip_value
            
            return profit_pips
            
        except Exception as e:
            self.logger.error(f"Error calculando pips: {e}")
            return 0
    
    def apply_breakeven(self, position):
        """Aplicar breakeven a una posición"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            entry_price = position.price_open
            position_type = position.type
            current_sl = position.sl
            current_tp = position.tp
            
            pip_value = self.get_symbol_pip_value(symbol)
            offset = self.BREAKEVEN_OFFSET_PIPS * pip_value
            
            # Calcular nuevo SL en breakeven + offset
            if position_type == 0:  # BUY
                new_sl = entry_price + offset
                # Solo aplicar si es mejor que el SL actual
                if current_sl == 0 or new_sl > current_sl:
                    pass
                else:
                    return False
            else:  # SELL
                new_sl = entry_price - offset
                # Solo aplicar si es mejor que el SL actual
                if current_sl == 0 or new_sl < current_sl:
                    pass
                else:
                    return False
            
            # Modificar posición
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": current_tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.statistics['breakeven_applied'] += 1
                self.logger.info(f"[BREAKEVEN] {symbol} #{ticket}: SL -> {new_sl:.5f}")
                return True
            else:
                self.logger.error(f"[BREAKEVEN ERROR] {symbol} #{ticket}: {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error aplicando breakeven: {e}")
            return False
    
    def apply_trailing_stop(self, position):
        """Aplicar trailing stop a una posición"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            position_type = position.type
            current_sl = position.sl
            current_tp = position.tp
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False
            
            current_price = tick.bid if position_type == 0 else tick.ask
            pip_value = self.get_symbol_pip_value(symbol)
            trailing_distance = self.TRAILING_DISTANCE_PIPS * pip_value
            
            # Calcular nuevo trailing SL
            if position_type == 0:  # BUY
                new_sl = current_price - trailing_distance
                # Solo actualizar si es mejor que el SL actual
                if current_sl == 0 or new_sl > current_sl:
                    pass
                else:
                    return False
            else:  # SELL
                new_sl = current_price + trailing_distance
                # Solo actualizar si es mejor que el SL actual
                if current_sl == 0 or new_sl < current_sl:
                    pass
                else:
                    return False
            
            # Verificar que el movimiento justifica la actualización (mín 8 pips para evitar sobreajustes)
            min_movement = 8 * pip_value
            if current_sl != 0:
                if position_type == 0 and (new_sl - current_sl) < min_movement:
                    return False
                elif position_type == 1 and (current_sl - new_sl) < min_movement:
                    return False
            
            # Modificar posición
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": current_tp,
                "magic": 20250817
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.statistics['trailing_updates'] += 1
                self.logger.info(f"[TRAILING] {symbol} #{ticket}: SL {current_sl:.5f} -> {new_sl:.5f}")
                return True
            else:
                self.logger.error(f"[TRAILING ERROR] {symbol} #{ticket}: {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error aplicando trailing stop: {e}")
            return False
    
    def manage_positions(self):
        """Gestionar todas las posiciones abiertas"""
        try:
            positions = mt5.positions_get()
            
            if not positions:
                return
            
            self.logger.info(f"[RISK MANAGER] Gestionando {len(positions)} posiciones...")
            
            for position in positions:
                symbol = position.symbol
                ticket = position.ticket
                
                # Calcular profit en pips
                profit_pips = self.calculate_pips_profit(position)
                
                if profit_pips <= 0:
                    continue  # Solo gestionar posiciones ganadoras
                
                position_key = f"{ticket}"
                
                # Aplicar breakeven si califica y no se ha aplicado
                if (self.ENABLE_BREAKEVEN and 
                    profit_pips >= self.BREAKEVEN_TRIGGER_PIPS and
                    position_key not in self.position_states.get('breakeven_applied', set())):
                    
                    if self.apply_breakeven(position):
                        if 'breakeven_applied' not in self.position_states:
                            self.position_states['breakeven_applied'] = set()
                        self.position_states['breakeven_applied'].add(position_key)
                        
                        self.logger.info(f"[SUCCESS] Breakeven aplicado a {symbol} #{ticket} (+{profit_pips:.1f} pips)")
                
                # Aplicar trailing stop si califica
                if (self.ENABLE_TRAILING_STOP and 
                    profit_pips >= self.TRAILING_TRIGGER_PIPS):
                    
                    if self.apply_trailing_stop(position):
                        self.logger.info(f"[SUCCESS] Trailing actualizado para {symbol} #{ticket} (+{profit_pips:.1f} pips)")
                
                self.statistics['positions_protected'] += 1
                
        except Exception as e:
            self.logger.error(f"Error gestionando posiciones: {e}")
    
    def risk_manager_thread(self):
        """Hilo del gestor de riesgo"""
        self.logger.info("[RISK MANAGER] Hilo iniciado")
        
        while self.running:
            try:
                # Verificar conexión MT5
                if not mt5.terminal_info():
                    if not self.initialize_mt5():
                        self.logger.warning("[RISK MANAGER] MT5 no disponible")
                        time.sleep(30)
                        continue
                
                # Gestionar posiciones
                self.manage_positions()
                
                # Esperar 45 segundos (mayor intervalo para estabilidad)
                time.sleep(45)
                
            except Exception as e:
                self.logger.error(f"[RISK MANAGER] Error: {e}")
                time.sleep(30)
        
        self.logger.info("[RISK MANAGER] Hilo terminado")
    
    def signal_generator_thread(self):
        """Hilo del generador de señales"""
        self.logger.info("[SIGNAL GENERATOR] Hilo iniciado")
        
        try:
            # Importar y configurar signal generator
            from src.signals.advanced_signal_generator import SignalGenerator
            
            symbols = ['XAUUSDm', 'EURUSDm', 'GBPUSDm', 'BTCUSDm']
            self.signal_generator = SignalGenerator(symbols=symbols, auto_execute=False)
            self.signal_generator.enable_auto_trading()
            
            cycle_count = 0
            
            while self.running:
                try:
                    cycle_count += 1
                    current_time = datetime.now().strftime('%H:%M:%S')
                    
                    self.logger.info(f"[SG Ciclo {cycle_count:04d}] {current_time} - Analizando mercados...")
                    
                    # Ejecutar análisis
                    signals = self.signal_generator.run_analysis_cycle()
                    
                    if signals:
                        self.statistics['signals_generated'] += len(signals)
                        self.statistics['trades_executed'] += self.signal_generator.trades_executed
                        self.logger.info(f"[SIGNALS] {len(signals)} señales generadas")
                    
                    # Esperar 60 segundos
                    time.sleep(60)
                    
                except Exception as e:
                    self.logger.error(f"[SIGNAL GENERATOR] Error en ciclo: {e}")
                    time.sleep(30)
            
        except Exception as e:
            self.logger.error(f"[SIGNAL GENERATOR] Error crítico: {e}")
        
        self.logger.info("[SIGNAL GENERATOR] Hilo terminado")
    
    def start(self):
        """Iniciar el sistema completo"""
        print("="*70)
        print("    SISTEMA TRADING CORREGIDO Y MEJORADO")
        print("    Generador IA + Breakeven + Trailing Stop")
        print("="*70)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Inicializar MT5
        if not self.initialize_mt5():
            print("ERROR: No se pudo inicializar MT5")
            return
        
        print("CONFIGURACION:")
        print(f"- Breakeven: {'ACTIVADO' if self.ENABLE_BREAKEVEN else 'DESACTIVADO'} ({self.BREAKEVEN_TRIGGER_PIPS} pips -> +{self.BREAKEVEN_OFFSET_PIPS}) [CONSERVADOR]")
        print(f"- Trailing Stop: {'ACTIVADO' if self.ENABLE_TRAILING_STOP else 'DESACTIVADO'} ({self.TRAILING_TRIGGER_PIPS} pips -> {self.TRAILING_DISTANCE_PIPS} dist) [ANTI-OSCILACION]")
        print(f"- Verificacion: Cada 30 segundos")
        print(f"- Señales IA: Cada 60 segundos")
        print()
        
        # Crear hilos
        threads = []
        
        # Hilo 1: Risk Manager
        risk_thread = threading.Thread(target=self.risk_manager_thread, daemon=True)
        risk_thread.start()
        threads.append(risk_thread)
        print("[OK] Risk Manager iniciado")
        
        # Hilo 2: Signal Generator
        signal_thread = threading.Thread(target=self.signal_generator_thread, daemon=True)
        signal_thread.start()
        threads.append(signal_thread)
        print("[OK] Signal Generator iniciado")
        
        print()
        print("="*70)
        print("SISTEMA EJECUTANDOSE - Presiona Ctrl+C para detener")
        print("="*70)
        
        # Loop principal con estadísticas
        try:
            while True:
                time.sleep(300)  # 5 minutos
                
                print(f"\n--- ESTADISTICAS [{datetime.now().strftime('%H:%M:%S')}] ---")
                print(f"Señales generadas: {self.statistics['signals_generated']}")
                print(f"Trades ejecutados: {self.statistics['trades_executed']}")
                print(f"Breakeven aplicados: {self.statistics['breakeven_applied']}")
                print(f"Trailing updates: {self.statistics['trailing_updates']}")
                print(f"Posiciones protegidas: {self.statistics['positions_protected']}")
                
        except KeyboardInterrupt:
            print("\n\nDeteniendo sistema...")
            self.running = False
            
            # Esperar hilos
            time.sleep(3)
            
            # Cerrar MT5
            mt5.shutdown()
            
            print("\n" + "="*70)
            print("SISTEMA DETENIDO CORRECTAMENTE")
            print("="*70)

def main():
    """Función principal"""
    try:
        system = TradingSystemManager()
        system.start()
    except Exception as e:
        print(f"Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()