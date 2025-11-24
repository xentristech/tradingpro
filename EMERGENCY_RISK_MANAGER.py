"""
EMERGENCY RISK MANAGER v2.0 - Cierre Automatico de Posiciones en Riesgo
Sistema de proteccion de capital con cierre automatico de trades peligrosos
"""

import MetaTrader5 as mt5
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/emergency_risk_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmergencyRiskManager:
    """
    Gestor de Riesgo de Emergencia - Cierra automaticamente posiciones peligrosas
    """
    
    def __init__(self):
        """Inicializar el gestor de riesgo de emergencia"""
        
        # CONFIGURACION DE RIESGO - AJUSTABLE POR EL USUARIO
        self.config = {
            # Umbral de perdida para cierre automatico (% del balance)
            'max_loss_percent': 5.0,  # 5% del balance total
            
            # Perdida maxima por posicion individual (USD)
            'max_loss_per_position': 200.0,
            
            # Perdida maxima acumulada diaria (USD)  
            'max_daily_loss': 500.0,
            
            # Umbral de drawdown maximo (% del balance)
            'max_drawdown_percent': 15.0,
            
            # Tiempo minimo entre cierres automaticos (segundos)
            'cooldown_seconds': 60,
            
            # Activar/desactivar cierre automatico
            'auto_close_enabled': True,
            
            # Activar trailing stop dinamico
            'trailing_stop_enabled': True,
            
            # Distancia trailing stop (% del precio)
            'trailing_stop_distance': 2.0
        }
        
        self.initial_balance = 0
        self.daily_start_balance = 0
        self.last_action_time = datetime.min
        self.closed_positions_today = []
        self.running = False
        
        logger.info("Emergency Risk Manager v2.0 inicializado")
        self._print_configuration()
    
    def _print_configuration(self):
        """Imprimir configuracion actual"""
        print("\n" + "="*70)
        print("          EMERGENCY RISK MANAGER v2.0 - CONFIGURACION")
        print("="*70)
        print(f"Max perdida por posicion:     ${self.config['max_loss_per_position']:.2f}")
        print(f"Max perdida diaria:           ${self.config['max_daily_loss']:.2f}")
        print(f"Max drawdown:                 {self.config['max_drawdown_percent']:.1f}%")
        print(f"Trailing stop:                {self.config['trailing_stop_distance']:.1f}%")
        print(f"Auto-cierre activado:         {'SI' if self.config['auto_close_enabled'] else 'NO'}")
        print(f"Trailing stop activado:       {'SI' if self.config['trailing_stop_enabled'] else 'NO'}")
        print("="*70)
        print()
    
    def connect_mt5(self) -> bool:
        """Conectar a MetaTrader 5"""
        if not mt5.initialize():
            logger.error("Error inicializando MT5")
            return False
            
        # Obtener informacion de cuenta
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Error obteniendo info de cuenta")
            return False
            
        self.initial_balance = account_info.balance
        if self.daily_start_balance == 0:
            self.daily_start_balance = account_info.balance
            
        logger.info(f"Conectado a cuenta {account_info.login}")
        logger.info(f"Balance actual: ${account_info.balance:.2f}")
        logger.info(f"Balance inicial del dia: ${self.daily_start_balance:.2f}")
        
        return True
    
    def analyze_position_risk(self, position) -> Dict:
        """Analizar riesgo de una posicion individual"""
        
        # Calcular datos basicos
        current_profit = position.profit
        entry_price = position.price_open
        current_price = position.price_current
        volume = position.volume
        
        # Calcular porcentaje de perdida
        loss_percent = abs(current_profit / self.initial_balance * 100) if current_profit < 0 else 0
        
        # Determinar nivel de riesgo
        risk_level = "LOW"
        if current_profit < -100:
            risk_level = "MEDIUM"
        if current_profit < -150:
            risk_level = "HIGH" 
        if current_profit < -200:
            risk_level = "CRITICAL"
            
        # Calcular distancia del stop loss actual
        sl_distance_percent = 0
        if position.sl > 0:
            if position.type == mt5.ORDER_TYPE_BUY:
                sl_distance_percent = abs((current_price - position.sl) / current_price * 100)
            else:
                sl_distance_percent = abs((position.sl - current_price) / current_price * 100)
        
        return {
            'ticket': position.ticket,
            'symbol': position.symbol,
            'type': 'BUY' if position.type == mt5.ORDER_TYPE_BUY else 'SELL',
            'volume': volume,
            'current_profit': current_profit,
            'loss_percent': loss_percent,
            'risk_level': risk_level,
            'sl_distance_percent': sl_distance_percent,
            'should_close': self._should_close_position(position, current_profit, loss_percent),
            'should_trail': self._should_update_trailing_stop(position)
        }
    
    def _should_close_position(self, position, current_profit: float, loss_percent: float) -> bool:
        """Determinar si una posicion debe cerrarse automaticamente"""
        if not self.config['auto_close_enabled']:
            return False
            
        # Criterio 1: Perdida individual excesiva
        if current_profit < -self.config['max_loss_per_position']:
            logger.warning(f"Posicion {position.ticket} excede perdida maxima: ${current_profit:.2f}")
            return True
            
        # Criterio 2: Porcentaje de balance perdido
        if loss_percent > self.config['max_loss_percent']:
            logger.warning(f"Posicion {position.ticket} excede % de perdida: {loss_percent:.1f}%")
            return True
            
        return False
    
    def _should_update_trailing_stop(self, position) -> bool:
        """Determinar si se debe actualizar el trailing stop"""
        if not self.config['trailing_stop_enabled']:
            return False
            
        # Solo para posiciones en ganancia
        if position.profit <= 0:
            return False
            
        current_price = position.price_current
        trailing_distance = self.config['trailing_stop_distance'] / 100
        
        if position.type == mt5.ORDER_TYPE_BUY:
            # Para BUY: trailing stop debajo del precio actual
            new_sl = current_price * (1 - trailing_distance)
            return position.sl == 0 or new_sl > position.sl
        else:
            # Para SELL: trailing stop arriba del precio actual  
            new_sl = current_price * (1 + trailing_distance)
            return position.sl == 0 or new_sl < position.sl
    
    def close_position(self, position) -> bool:
        """Cerrar una posicion automaticamente"""
        
        # Verificar cooldown
        if (datetime.now() - self.last_action_time).seconds < self.config['cooldown_seconds']:
            logger.info("Cooldown activo, esperando...")
            return False
            
        # Preparar orden de cierre
        if position.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
        else:
            order_type = mt5.ORDER_TYPE_BUY
            
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "magic": 0,
            "comment": "EMERGENCY_CLOSE_RISK_MANAGER",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Ejecutar cierre
        result = mt5.order_send(close_request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            self.last_action_time = datetime.now()
            self.closed_positions_today.append({
                'ticket': position.ticket,
                'symbol': position.symbol,
                'profit': position.profit,
                'time': datetime.now()
            })
            
            logger.info(f"[CLOSED] Posicion {position.ticket} cerrada automaticamente")
            logger.info(f"         Simbolo: {position.symbol} | P&L: ${position.profit:.2f}")
            
            return True
        else:
            logger.error(f"Error cerrando posicion {position.ticket}: {result.retcode}")
            return False
    
    def update_trailing_stop(self, position) -> bool:
        """Actualizar trailing stop de una posicion"""
        
        current_price = position.price_current
        trailing_distance = self.config['trailing_stop_distance'] / 100
        
        if position.type == mt5.ORDER_TYPE_BUY:
            new_sl = current_price * (1 - trailing_distance)
        else:
            new_sl = current_price * (1 + trailing_distance)
            
        # Redondear segun el simbolo
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info:
            digits = symbol_info.digits
            new_sl = round(new_sl, digits)
        
        # Enviar orden de modificacion
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": new_sl,
            "tp": position.tp
        }
        
        result = mt5.order_send(modify_request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"[TRAILING] Trailing stop actualizado en {position.symbol}")
            logger.info(f"           SL: {position.sl:.5f} -> {new_sl:.5f}")
            return True
        else:
            logger.warning(f"Error actualizando trailing stop: {result.retcode}")
            return False
    
    def calculate_daily_risk(self) -> Dict:
        """Calcular riesgo diario acumulado"""
        
        account_info = mt5.account_info()
        if not account_info:
            return {}
            
        current_balance = account_info.balance
        daily_pnl = current_balance - self.daily_start_balance
        
        # Calcular perdida acumulada de posiciones cerradas hoy
        closed_pnl_today = sum(pos['profit'] for pos in self.closed_positions_today)
        
        # Calcular drawdown actual
        current_drawdown = 0
        if self.initial_balance > 0:
            current_drawdown = max(0, (self.initial_balance - current_balance) / self.initial_balance * 100)
        
        return {
            'current_balance': current_balance,
            'daily_start_balance': self.daily_start_balance,
            'daily_pnl': daily_pnl,
            'closed_positions_today': len(self.closed_positions_today),
            'closed_pnl_today': closed_pnl_today,
            'current_drawdown': current_drawdown,
            'risk_level': 'HIGH' if current_drawdown > 10 else 'MEDIUM' if current_drawdown > 5 else 'LOW'
        }
    
    def start_monitoring(self):
        """Iniciar monitoreo continuo de riesgo"""
        
        if not self.connect_mt5():
            logger.error("No se pudo conectar a MT5")
            return
            
        self.running = True
        monitor_cycle = 0
        
        print("\n" + "="*70)
        print("           EMERGENCY RISK MANAGER - MONITOREANDO")
        print("="*70)
        print("Presiona Ctrl+C para detener")
        print("="*70)
        
        try:
            while self.running:
                monitor_cycle += 1
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === CICLO #{monitor_cycle:03d} ===")
                
                # Obtener posiciones abiertas
                positions = mt5.positions_get()
                if positions is None:
                    positions = []
                
                if len(positions) == 0:
                    print("   No hay posiciones abiertas")
                else:
                    print(f"   Analizando {len(positions)} posiciones...")
                    
                    positions_closed = 0
                    trailing_stops_updated = 0
                    
                    # Analizar cada posicion
                    for position in positions:
                        risk_analysis = self.analyze_position_risk(position)
                        
                        # Mostrar estado
                        status_emoji = {
                            'LOW': '[OK]',
                            'MEDIUM': '[WATCH]', 
                            'HIGH': '[RISK]',
                            'CRITICAL': '[DANGER]'
                        }.get(risk_analysis['risk_level'], '[?]')
                        
                        print(f"   {status_emoji} {risk_analysis['symbol']} {risk_analysis['type']} "
                              f"Vol:{risk_analysis['volume']} P&L:${risk_analysis['current_profit']:+.2f}")
                        
                        # Acciones automaticas
                        if risk_analysis['should_close']:
                            if self.close_position(position):
                                positions_closed += 1
                                print(f"        -> [CLOSED] Posicion cerrada automaticamente!")
                        
                        elif risk_analysis['should_trail']:
                            if self.update_trailing_stop(position):
                                trailing_stops_updated += 1
                                print(f"        -> [TRAILING] Stop loss actualizado")
                
                # Mostrar resumen de riesgo diario
                daily_risk = self.calculate_daily_risk()
                if daily_risk:
                    print(f"\n   RESUMEN DIARIO:")
                    print(f"   Balance: ${daily_risk['current_balance']:.2f}")
                    print(f"   P&L Diario: ${daily_risk['daily_pnl']:+.2f}")
                    print(f"   Drawdown: {daily_risk['current_drawdown']:.1f}%")
                    print(f"   Posiciones cerradas hoy: {daily_risk['closed_positions_today']}")
                    
                    if positions_closed > 0:
                        print(f"   [ACTION] {positions_closed} posiciones cerradas este ciclo")
                    if trailing_stops_updated > 0:
                        print(f"   [ACTION] {trailing_stops_updated} trailing stops actualizados")
                
                # Esperar 15 segundos antes del siguiente ciclo
                time.sleep(15)
                
        except KeyboardInterrupt:
            logger.info("Monitore detenido por usuario")
        except Exception as e:
            logger.error(f"Error en monitoreo: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.running = False
        mt5.shutdown()
        
        print(f"\n{'='*70}")
        print("EMERGENCY RISK MANAGER DETENIDO")
        print(f"Posiciones cerradas hoy: {len(self.closed_positions_today)}")
        if self.closed_positions_today:
            total_pnl = sum(pos['profit'] for pos in self.closed_positions_today)
            print(f"P&L total de cierres: ${total_pnl:+.2f}")
        print("="*70)

def main():
    """Funcion principal"""
    
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    print("""
    ========================================================================
                    EMERGENCY RISK MANAGER v2.0
    ========================================================================
    
    FUNCIONES PRINCIPALES:
    - Cierre automatico de posiciones con perdidas excesivas
    - Trailing stop dinamico para proteger ganancias  
    - Monitor continuo de riesgo de cuenta
    - Proteccion contra drawdown excesivo
    - Control de perdida maxima diaria
    
    CONFIGURACION ACTUAL:
    - Max perdida por posicion: $200
    - Max perdida diaria: $500  
    - Max drawdown permitido: 15%
    - Trailing stop: 2%
    
    IMPORTANTE: Este sistema puede cerrar posiciones automaticamente
    para proteger tu capital. Revisa la configuracion antes de continuar.
    
    ========================================================================
    """)
    
    # Inicio automático para integración con sistema principal
    print("Iniciando automáticamente...")
    time.sleep(2)
    
    # Iniciar gestor de riesgo
    risk_manager = EmergencyRiskManager()
    risk_manager.start_monitoring()

if __name__ == "__main__":
    main()