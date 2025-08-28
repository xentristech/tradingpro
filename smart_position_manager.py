"""
SISTEMA DE GESTIÓN AVANZADA DE POSICIONES
Breakeven automático, Trailing Stop dinámico, TP parciales
Sistema autónomo de clase mundial
"""
import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import MetaTrader5 as mt5
from dotenv import load_dotenv

load_dotenv('.env')

@dataclass
class PositionManager:
    """Gestión profesional de posiciones"""
    ticket: int
    symbol: str
    type: int  # 0=Buy, 1=Sell
    volume: float
    price_open: float
    sl: float
    tp: float
    profit: float
    points: float
    magic: int
    
    # Estados de gestión
    breakeven_activated: bool = False
    trailing_activated: bool = False
    partial_closed: bool = False
    last_trailing_price: float = 0
    max_profit_reached: float = 0
    
class SmartPositionManager:
    """
    Sistema de gestión autónomo de posiciones de clase mundial
    """
    
    def __init__(self):
        self.symbol = os.getenv("TRADING_SYMBOL", "BTCUSD")
        self.magic = int(os.getenv("MT5_MAGIC", "20250817"))
        
        # === CONFIGURACIÓN DE GESTIÓN AVANZADA ===
        
        # BREAKEVEN AUTOMÁTICO
        self.breakeven_trigger_points = 20  # Activar BE cuando gane 20 puntos
        self.breakeven_buffer_points = 2    # Dejar 2 puntos de ganancia en BE
        
        # TRAILING STOP DINÁMICO
        self.trailing_start_points = 30     # Iniciar trailing después de 30 puntos
        self.trailing_distance_points = 15  # Mantener SL a 15 puntos del precio
        self.trailing_step_points = 5       # Mover SL cada 5 puntos de avance
        
        # TAKE PROFIT PARCIAL
        self.partial_tp1_points = 25        # Primer TP parcial a 25 puntos
        self.partial_tp1_percent = 0.5      # Cerrar 50% en TP1
        self.partial_tp2_points = 50        # Segundo TP parcial a 50 puntos
        self.partial_tp2_percent = 0.25     # Cerrar 25% adicional en TP2
        
        # PROTECCIÓN DE GANANCIAS
        self.profit_protection_trigger = 40 # Si llega a 40 puntos de ganancia
        self.profit_protection_level = 20   # Proteger al menos 20 puntos
        
        # GESTIÓN BASADA EN VOLATILIDAD
        self.use_atr_adjustment = True      # Ajustar niveles según ATR
        self.atr_multiplier = 1.5           # Multiplicador para ATR
        
        # GESTIÓN DE TIEMPO
        self.max_position_hours = 24        # Cerrar después de 24 horas
        self.reduce_risk_after_hours = 12   # Reducir riesgo después de 12 horas
        
        # Tracking de posiciones
        self.positions_data: Dict[int, PositionManager] = {}
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configurar logging"""
        logger = logging.getLogger('SmartPositions')
        logger.setLevel(logging.INFO)
        
        # Handler para archivo
        fh = logging.FileHandler('logs/smart_positions.log')
        fh.setLevel(logging.INFO)
        
        # Handler para consola
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter('%(asctime)s | %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def calculate_atr(self, symbol: str, timeframe=mt5.TIMEFRAME_M15, period=14):
        """Calcular ATR para ajustes dinámicos"""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 1)
        if rates is None or len(rates) < period:
            return None
            
        atr_sum = 0
        for i in range(1, period + 1):
            high = rates[i]['high']
            low = rates[i]['low']
            prev_close = rates[i-1]['close']
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            atr_sum += tr
            
        return atr_sum / period
    
    def analyze_market_conditions(self, symbol: str) -> Dict:
        """Analizar condiciones del mercado para ajustes dinámicos"""
        conditions = {
            'volatility': 'normal',
            'trend_strength': 0,
            'momentum': 0,
            'volume_ratio': 1.0
        }
        
        try:
            # Obtener datos recientes
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
            if rates is None:
                return conditions
                
            # Calcular volatilidad (ATR)
            atr = self.calculate_atr(symbol)
            if atr:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    price = symbol_info.bid
                    atr_percent = (atr / price) * 100
                    
                    if atr_percent < 0.5:
                        conditions['volatility'] = 'low'
                    elif atr_percent > 1.5:
                        conditions['volatility'] = 'high'
                    else:
                        conditions['volatility'] = 'normal'
            
            # Calcular momentum (cambio de precio)
            if len(rates) >= 20:
                price_change = rates[-1]['close'] - rates[-20]['close']
                conditions['momentum'] = price_change
                
            # Calcular fuerza de tendencia
            if len(rates) >= 20:
                ma_short = sum([r['close'] for r in rates[-10:]]) / 10
                ma_long = sum([r['close'] for r in rates[-20:]]) / 20
                conditions['trend_strength'] = (ma_short - ma_long) / ma_long * 100
                
            # Calcular ratio de volumen
            if len(rates) >= 20:
                recent_vol = sum([r['real_volume'] for r in rates[-5:]]) / 5
                avg_vol = sum([r['real_volume'] for r in rates[-20:]]) / 20
                conditions['volume_ratio'] = recent_vol / avg_vol if avg_vol > 0 else 1
                
        except Exception as e:
            self.logger.error(f"Error analizando mercado: {e}")
            
        return conditions
    
    def calculate_dynamic_levels(self, position: PositionManager) -> Dict:
        """Calcular niveles dinámicos basados en condiciones del mercado"""
        market = self.analyze_market_conditions(position.symbol)
        
        # Ajustar niveles según volatilidad
        volatility_factor = 1.0
        if market['volatility'] == 'high':
            volatility_factor = 1.3  # Dar más espacio en mercados volátiles
        elif market['volatility'] == 'low':
            volatility_factor = 0.8  # Ajustar más cerca en mercados tranquilos
            
        # Ajustar según fuerza de tendencia
        trend_factor = 1.0
        if abs(market['trend_strength']) > 0.5:
            trend_factor = 1.2  # Dar más espacio en tendencias fuertes
            
        levels = {
            'breakeven_trigger': self.breakeven_trigger_points * volatility_factor,
            'breakeven_buffer': self.breakeven_buffer_points,
            'trailing_start': self.trailing_start_points * volatility_factor * trend_factor,
            'trailing_distance': self.trailing_distance_points * volatility_factor,
            'trailing_step': self.trailing_step_points,
            'partial_tp1': self.partial_tp1_points * volatility_factor,
            'partial_tp2': self.partial_tp2_points * volatility_factor * trend_factor,
            'profit_protection': self.profit_protection_trigger * volatility_factor
        }
        
        # Si el volumen es alto, ser más agresivo con las tomas de ganancia
        if market['volume_ratio'] > 1.5:
            levels['partial_tp1'] *= 0.8
            levels['partial_tp2'] *= 0.9
            
        return levels
    
    def manage_breakeven(self, position: PositionManager, levels: Dict) -> bool:
        """Gestión inteligente de breakeven"""
        if position.breakeven_activated:
            return False
            
        current_profit_points = position.points
        
        if current_profit_points >= levels['breakeven_trigger']:
            # Calcular nuevo SL (precio de entrada + buffer)
            if position.type == mt5.ORDER_TYPE_BUY:
                new_sl = position.price_open + (levels['breakeven_buffer'] * mt5.symbol_info(position.symbol).point)
            else:  # SELL
                new_sl = position.price_open - (levels['breakeven_buffer'] * mt5.symbol_info(position.symbol).point)
            
            # Modificar posición
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": position.ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": self.magic,
                "comment": "BE_AUTO"
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                position.breakeven_activated = True
                position.sl = new_sl
                self.logger.info(f"✅ BREAKEVEN activado #{position.ticket} | "
                               f"Ganancia: {current_profit_points:.1f} pts | "
                               f"Nuevo SL: {new_sl:.5f}")
                return True
                
        return False
    
    def manage_trailing_stop(self, position: PositionManager, levels: Dict) -> bool:
        """Trailing stop dinámico inteligente"""
        current_profit_points = position.points
        
        # Solo activar después del breakeven y si hay suficiente ganancia
        if not position.breakeven_activated or current_profit_points < levels['trailing_start']:
            return False
        
        symbol_info = mt5.symbol_info(position.symbol)
        current_price = symbol_info.bid if position.type == mt5.ORDER_TYPE_BUY else symbol_info.ask
        
        # Calcular nuevo nivel de SL
        if position.type == mt5.ORDER_TYPE_BUY:
            new_sl = current_price - (levels['trailing_distance'] * symbol_info.point)
            
            # Solo mover si mejora el SL actual y el precio avanzó lo suficiente
            if new_sl > position.sl and (
                not position.trailing_activated or 
                current_price >= position.last_trailing_price + (levels['trailing_step'] * symbol_info.point)
            ):
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": position.ticket,
                    "sl": new_sl,
                    "tp": position.tp,
                    "magic": self.magic,
                    "comment": "TRAIL_AUTO"
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    position.trailing_activated = True
                    position.last_trailing_price = current_price
                    position.sl = new_sl
                    self.logger.info(f"📈 TRAILING actualizado #{position.ticket} | "
                                   f"Ganancia: {current_profit_points:.1f} pts | "
                                   f"Nuevo SL: {new_sl:.5f}")
                    return True
                    
        else:  # SELL
            new_sl = current_price + (levels['trailing_distance'] * symbol_info.point)
            
            if new_sl < position.sl and (
                not position.trailing_activated or 
                current_price <= position.last_trailing_price - (levels['trailing_step'] * symbol_info.point)
            ):
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": position.ticket,
                    "sl": new_sl,
                    "tp": position.tp,
                    "magic": self.magic,
                    "comment": "TRAIL_AUTO"
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    position.trailing_activated = True
                    position.last_trailing_price = current_price
                    position.sl = new_sl
                    self.logger.info(f"📉 TRAILING actualizado #{position.ticket} | "
                                   f"Ganancia: {current_profit_points:.1f} pts | "
                                   f"Nuevo SL: {new_sl:.5f}")
                    return True
                    
        return False
    
    def manage_partial_profits(self, position: PositionManager, levels: Dict) -> bool:
        """Gestión de tomas de ganancias parciales"""
        if position.partial_closed:
            return False
            
        current_profit_points = position.points
        
        # TP Parcial 1
        if current_profit_points >= levels['partial_tp1'] and not position.partial_closed:
            close_volume = position.volume * self.partial_tp1_percent
            
            symbol_info = mt5.symbol_info(position.symbol)
            
            # Preparar orden de cierre parcial
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = symbol_info.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = symbol_info.ask
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": position.ticket,
                "price": price,
                "deviation": 20,
                "magic": self.magic,
                "comment": "TP1_PARTIAL"
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                position.partial_closed = True
                position.volume -= close_volume
                profit_secured = current_profit_points * close_volume
                self.logger.info(f"💰 TP PARCIAL 1 #{position.ticket} | "
                               f"Cerrado: {close_volume:.3f} lotes | "
                               f"Ganancia asegurada: {profit_secured:.1f} pts")
                return True
                
        # TP Parcial 2
        if current_profit_points >= levels['partial_tp2'] and position.partial_closed:
            close_volume = position.volume * self.partial_tp2_percent
            
            symbol_info = mt5.symbol_info(position.symbol)
            
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = symbol_info.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = symbol_info.ask
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": position.ticket,
                "price": price,
                "deviation": 20,
                "magic": self.magic,
                "comment": "TP2_PARTIAL"
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                position.volume -= close_volume
                profit_secured = current_profit_points * close_volume
                self.logger.info(f"💰💰 TP PARCIAL 2 #{position.ticket} | "
                               f"Cerrado: {close_volume:.3f} lotes | "
                               f"Ganancia adicional: {profit_secured:.1f} pts")
                return True
                
        return False
    
    def protect_profits(self, position: PositionManager, levels: Dict) -> bool:
        """Sistema de protección de ganancias"""
        current_profit_points = position.points
        
        # Actualizar máximo de ganancia alcanzado
        if current_profit_points > position.max_profit_reached:
            position.max_profit_reached = current_profit_points
            
        # Si alcanzamos el trigger de protección
        if position.max_profit_reached >= levels['profit_protection']:
            # Calcular el nivel mínimo de protección
            min_protection_points = self.profit_protection_level
            
            # Si la ganancia cae demasiado desde el máximo, proteger
            if current_profit_points < position.max_profit_reached - 10:
                symbol_info = mt5.symbol_info(position.symbol)
                
                # Mover SL para proteger ganancias
                if position.type == mt5.ORDER_TYPE_BUY:
                    protected_sl = position.price_open + (min_protection_points * symbol_info.point)
                else:
                    protected_sl = position.price_open - (min_protection_points * symbol_info.point)
                    
                # Solo mover si mejora el SL actual
                if (position.type == mt5.ORDER_TYPE_BUY and protected_sl > position.sl) or \
                   (position.type == mt5.ORDER_TYPE_SELL and protected_sl < position.sl):
                    
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": position.ticket,
                        "sl": protected_sl,
                        "tp": position.tp,
                        "magic": self.magic,
                        "comment": "PROFIT_PROTECT"
                    }
                    
                    result = mt5.order_send(request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        self.logger.info(f"🛡️ PROTECCIÓN activada #{position.ticket} | "
                                       f"Máx ganancia: {position.max_profit_reached:.1f} pts | "
                                       f"Protegiendo: {min_protection_points} pts")
                        position.sl = protected_sl
                        return True
                        
        return False
    
    def manage_time_based_exit(self, position: PositionManager) -> bool:
        """Gestión basada en tiempo"""
        # Calcular tiempo en posición
        position_time = datetime.now() - datetime.fromtimestamp(mt5.positions_get(ticket=position.ticket)[0].time)
        hours_in_position = position_time.total_seconds() / 3600
        
        # Cerrar posiciones muy antiguas
        if hours_in_position >= self.max_position_hours:
            self.close_position_complete(position, "TIME_EXIT")
            self.logger.info(f"⏰ CIERRE por tiempo #{position.ticket} | "
                           f"Tiempo: {hours_in_position:.1f} horas")
            return True
            
        # Reducir riesgo en posiciones largas
        if hours_in_position >= self.reduce_risk_after_hours and not position.breakeven_activated:
            # Forzar breakeven si hay alguna ganancia
            if position.points > 0:
                self.force_breakeven(position)
                self.logger.info(f"⚠️ Reduciendo riesgo por tiempo #{position.ticket}")
                return True
                
        return False
    
    def force_breakeven(self, position: PositionManager) -> bool:
        """Forzar breakeven inmediato"""
        symbol_info = mt5.symbol_info(position.symbol)
        
        # Mover SL a precio de entrada
        new_sl = position.price_open
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "sl": new_sl,
            "tp": position.tp,
            "magic": self.magic,
            "comment": "BE_FORCED"
        }
        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            position.breakeven_activated = True
            position.sl = new_sl
            return True
            
        return False
    
    def close_position_complete(self, position: PositionManager, reason: str = "") -> bool:
        """Cerrar posición completa"""
        symbol_info = mt5.symbol_info(position.symbol)
        
        if position.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = symbol_info.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = symbol_info.ask
            
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": self.magic,
            "comment": reason
        }
        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return True
            
        return False
    
    def update_positions(self):
        """Actualizar información de posiciones"""
        positions = mt5.positions_get(symbol=self.symbol)
        
        if not positions:
            self.positions_data.clear()
            return
            
        # Actualizar datos de posiciones existentes
        current_tickets = []
        for pos in positions:
            current_tickets.append(pos.ticket)
            
            if pos.ticket not in self.positions_data:
                # Nueva posición
                self.positions_data[pos.ticket] = PositionManager(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    type=pos.type,
                    volume=pos.volume,
                    price_open=pos.price_open,
                    sl=pos.sl,
                    tp=pos.tp,
                    profit=pos.profit,
                    points=(pos.price_current - pos.price_open) / mt5.symbol_info(pos.symbol).point,
                    magic=pos.magic
                )
                self.logger.info(f"📌 Nueva posición detectada #{pos.ticket}")
            else:
                # Actualizar posición existente
                pm = self.positions_data[pos.ticket]
                pm.profit = pos.profit
                pm.sl = pos.sl
                pm.tp = pos.tp
                pm.volume = pos.volume
                
                # Calcular puntos de ganancia/pérdida
                symbol_info = mt5.symbol_info(pos.symbol)
                if pos.type == mt5.ORDER_TYPE_BUY:
                    pm.points = (pos.price_current - pos.price_open) / symbol_info.point
                else:
                    pm.points = (pos.price_open - pos.price_current) / symbol_info.point
                    
        # Eliminar posiciones cerradas
        for ticket in list(self.positions_data.keys()):
            if ticket not in current_tickets:
                self.logger.info(f"❌ Posición cerrada #{ticket}")
                del self.positions_data[ticket]
    
    def process_all_positions(self):
        """Procesar todas las posiciones con gestión inteligente"""
        self.update_positions()
        
        for ticket, position in self.positions_data.items():
            try:
                # Obtener niveles dinámicos para esta posición
                levels = self.calculate_dynamic_levels(position)
                
                # Mostrar estado actual
                self.logger.info(f"📊 Analizando #{ticket} | "
                               f"P&L: {position.profit:.2f} | "
                               f"Puntos: {position.points:.1f} | "
                               f"BE: {position.breakeven_activated} | "
                               f"Trail: {position.trailing_activated}")
                
                # 1. Gestión por tiempo
                if self.manage_time_based_exit(position):
                    continue
                    
                # 2. Protección de ganancias
                if self.protect_profits(position, levels):
                    continue
                    
                # 3. Take Profit parcial
                if self.manage_partial_profits(position, levels):
                    continue
                    
                # 4. Breakeven automático
                if self.manage_breakeven(position, levels):
                    continue
                    
                # 5. Trailing Stop dinámico
                if self.manage_trailing_stop(position, levels):
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error procesando #{ticket}: {e}")
    
    def run_forever(self, interval: int = 5):
        """Loop principal de gestión"""
        self.logger.info("="*60)
        self.logger.info("🚀 SMART POSITION MANAGER - INICIADO")
        self.logger.info("="*60)
        self.logger.info(f"Configuración:")
        self.logger.info(f"  BE Trigger: {self.breakeven_trigger_points} pts")
        self.logger.info(f"  Trail Start: {self.trailing_start_points} pts")
        self.logger.info(f"  Trail Distance: {self.trailing_distance_points} pts")
        self.logger.info(f"  TP1: {self.partial_tp1_points} pts ({self.partial_tp1_percent*100}%)")
        self.logger.info(f"  TP2: {self.partial_tp2_points} pts ({self.partial_tp2_percent*100}%)")
        self.logger.info("="*60)
        
        while True:
            try:
                if not mt5.initialize():
                    self.logger.error("No se pudo conectar a MT5")
                    time.sleep(30)
                    continue
                    
                self.process_all_positions()
                
                # Resumen cada minuto
                if int(time.time()) % 60 < interval:
                    active_positions = len(self.positions_data)
                    total_profit = sum([p.profit for p in self.positions_data.values()])
                    self.logger.info(f"📈 Resumen | Posiciones: {active_positions} | "
                                   f"P&L Total: ${total_profit:.2f}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Sistema detenido por el usuario")
                break
            except Exception as e:
                self.logger.error(f"Error en loop principal: {e}")
                time.sleep(10)
                
        mt5.shutdown()

if __name__ == "__main__":
    manager = SmartPositionManager()
    manager.run_forever()
