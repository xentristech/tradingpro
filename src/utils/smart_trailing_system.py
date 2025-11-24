#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SMART TRAILING SYSTEM - BREAKEVEN MANUAL + TRAILING AUTOMÁTICO RÁPIDO
====================================================================
Sistema inteligente con breakeven manual y trailing automático optimizado
"""

import MetaTrader5 as mt5
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Agregar src al path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

try:
    from src.notifiers.telegram_notifier import TelegramNotifier
except ImportError:
    TelegramNotifier = None

logger = logging.getLogger(__name__)

class SmartTrailingSystem:
    """Sistema inteligente de trailing stop y breakeven"""
    
    def __init__(self):
        # CONFIGURACIÓN OPTIMIZADA - MÁS AGRESIVA
        self.BREAKEVEN_TRIGGER = 15        # 15 pips (era 25)
        self.BREAKEVEN_OFFSET = 3          # +3 pips sobre entrada
        
        self.TRAILING_TRIGGER = 20         # 20 pips (era 40) 
        self.TRAILING_DISTANCE = 12        # 12 pips de distancia (era 20)
        
        # Parámetros especiales por símbolo
        self.SYMBOL_PARAMS = {
            'XAUUSD': {'breakeven_trigger': 8, 'trailing_trigger': 12, 'trailing_distance': 8},
            'XAUUSDm': {'breakeven_trigger': 8, 'trailing_trigger': 12, 'trailing_distance': 8},
            'EURUSD': {'breakeven_trigger': 15, 'trailing_trigger': 20, 'trailing_distance': 12},
            'EURUSDm': {'breakeven_trigger': 15, 'trailing_trigger': 20, 'trailing_distance': 12},
            'BTCUSD': {'breakeven_trigger': 100, 'trailing_trigger': 150, 'trailing_distance': 80},
            'BTCUSDm': {'breakeven_trigger': 100, 'trailing_trigger': 150, 'trailing_distance': 80},
        }
        
        # Telegram notifier
        self.telegram = TelegramNotifier() if TelegramNotifier else None
        
        # Estado de breakeven aplicado (para evitar spam)
        self.breakeven_applied = set()
        
        logger.info("Smart Trailing System inicializado - PARÁMETROS OPTIMIZADOS")
        logger.info(f"Breakeven: {self.BREAKEVEN_TRIGGER} pips -> +{self.BREAKEVEN_OFFSET}")
        logger.info(f"Trailing: {self.TRAILING_TRIGGER} pips -> {self.TRAILING_DISTANCE} distancia")
    
    def get_symbol_params(self, symbol: str) -> Dict[str, int]:
        """Obtiene parámetros específicos por símbolo"""
        return self.SYMBOL_PARAMS.get(symbol, {
            'breakeven_trigger': self.BREAKEVEN_TRIGGER,
            'trailing_trigger': self.TRAILING_TRIGGER, 
            'trailing_distance': self.TRAILING_DISTANCE
        })
    
    def calculate_pips(self, symbol: str, price_diff: float) -> float:
        """Calcula pips basado en el símbolo"""
        if 'JPY' in symbol:
            return price_diff * 100  # Pares JPY
        elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
            return price_diff  # Criptos ya en "pips"
        elif 'XAU' in symbol or 'GOLD' in symbol:
            return price_diff * 10  # Oro
        else:
            return price_diff * 10000  # Pares mayores
    
    def apply_manual_breakeven(self, position) -> bool:
        """Aplica breakeven manual y envía alerta a Telegram"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            entry_price = position.price_open
            current_price = position.price_current
            position_type = position.type
            
            # Obtener parámetros del símbolo
            params = self.get_symbol_params(symbol)
            breakeven_trigger = params['breakeven_trigger']
            
            # Calcular ganancia en pips
            if position_type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, current_price - entry_price)
                new_sl = entry_price + (self.BREAKEVEN_OFFSET / 10000)
                if 'XAU' in symbol:
                    new_sl = entry_price + (self.BREAKEVEN_OFFSET / 10)
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    new_sl = entry_price + self.BREAKEVEN_OFFSET
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, entry_price - current_price)
                new_sl = entry_price - (self.BREAKEVEN_OFFSET / 10000)
                if 'XAU' in symbol:
                    new_sl = entry_price - (self.BREAKEVEN_OFFSET / 10)
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    new_sl = entry_price - self.BREAKEVEN_OFFSET
            
            # Verificar si cumple condiciones
            if pips_profit < breakeven_trigger:
                return False
                
            # Evitar aplicar múltiples veces
            if ticket in self.breakeven_applied:
                return False
            
            # Aplicar breakeven
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.breakeven_applied.add(ticket)
                
                # Enviar alerta a Telegram
                message = f"""
🛡️ *BREAKEVEN APLICADO*

📈 *{symbol}* #{ticket}
💰 Ganancia: {pips_profit:.1f} pips
🎯 SL Movido: {new_sl:.5f}
⚖️ Trade protegido sin pérdida

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
                if self.telegram:
                    self.telegram.send_message(message, parse_mode='Markdown')
                    
                logger.info(f"[BREAKEVEN] {symbol} #{ticket}: {pips_profit:.1f} pips -> SL {new_sl:.5f}")
                return True
            else:
                logger.error(f"Error aplicando breakeven a {ticket}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error en apply_manual_breakeven: {e}")
            return False
    
    def apply_automatic_trailing(self, position) -> bool:
        """Aplica trailing stop automático"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            entry_price = position.price_open
            current_price = position.price_current
            current_sl = position.sl
            position_type = position.type
            
            # Obtener parámetros del símbolo
            params = self.get_symbol_params(symbol)
            trailing_trigger = params['trailing_trigger']
            trailing_distance = params['trailing_distance']
            
            # Calcular ganancia en pips
            if position_type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, current_price - entry_price)
                distance_factor = trailing_distance / 10000
                if 'XAU' in symbol:
                    distance_factor = trailing_distance / 10
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    distance_factor = trailing_distance
                new_sl = current_price - distance_factor
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, entry_price - current_price)
                distance_factor = trailing_distance / 10000
                if 'XAU' in symbol:
                    distance_factor = trailing_distance / 10
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    distance_factor = trailing_distance
                new_sl = current_price + distance_factor
            
            # Verificar condiciones para trailing
            if pips_profit < trailing_trigger:
                return False
            
            # Solo mover SL si mejora la posición
            should_move = False
            if position_type == 0 and (current_sl == 0 or new_sl > current_sl):
                should_move = True
            elif position_type == 1 and (current_sl == 0 or new_sl < current_sl):
                should_move = True
                
            if not should_move:
                return False
            
            # Aplicar trailing stop
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                # Notificar trailing aplicado
                message = f"""
🔄 *TRAILING STOP AJUSTADO*

📈 *{symbol}* #{ticket}  
💰 Ganancia: {pips_profit:.1f} pips
🔄 SL: {current_sl:.5f} → {new_sl:.5f}
📏 Distancia: {trailing_distance} pips

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
                if self.telegram:
                    self.telegram.send_message(message, parse_mode='Markdown')
                    
                logger.info(f"[TRAILING] {symbol} #{ticket}: {pips_profit:.1f} pips -> SL {current_sl:.5f} → {new_sl:.5f}")
                return True
            else:
                logger.error(f"Error aplicando trailing a {ticket}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error en apply_automatic_trailing: {e}")
            return False
    
    def process_all_positions(self) -> Dict[str, int]:
        """Procesa todas las posiciones abiertas"""
        if not mt5.initialize():
            logger.error("No se pudo conectar a MT5")
            return {"error": 1}
        
        positions = mt5.positions_get()
        if not positions:
            return {"no_positions": 1}
        
        results = {
            "total_positions": len(positions),
            "breakeven_applied": 0,
            "trailing_applied": 0,
            "skipped": 0
        }
        
        for position in positions:
            try:
                # Intentar breakeven manual
                if self.apply_manual_breakeven(position):
                    results["breakeven_applied"] += 1
                
                # Intentar trailing automático
                elif self.apply_automatic_trailing(position):
                    results["trailing_applied"] += 1
                else:
                    results["skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Error procesando posición {position.ticket}: {e}")
                results["skipped"] += 1
        
        return results
    
    def get_position_status(self) -> List[Dict]:
        """Obtiene estado de todas las posiciones"""
        if not mt5.initialize():
            return []
        
        positions = mt5.positions_get()
        if not positions:
            return []
        
        status_list = []
        
        for position in positions:
            symbol = position.symbol
            params = self.get_symbol_params(symbol)
            
            # Calcular pips de ganancia
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, position.price_open - position.price_current)
            
            status = {
                "ticket": position.ticket,
                "symbol": symbol,
                "type": "BUY" if position.type == 0 else "SELL",
                "pips_profit": round(pips_profit, 1),
                "breakeven_ready": pips_profit >= params['breakeven_trigger'],
                "trailing_ready": pips_profit >= params['trailing_trigger'],
                "breakeven_applied": position.ticket in self.breakeven_applied,
                "current_sl": position.sl,
                "current_tp": position.tp,
                "profit_usd": position.profit
            }
            
            status_list.append(status)
        
        return status_list

# Instancia global
smart_trailing = SmartTrailingSystem()

# Funciones de utilidad
def apply_breakeven_to_all():
    """Aplica breakeven manual a todas las posiciones elegibles"""
    return smart_trailing.process_all_positions()

def get_positions_status():
    """Obtiene estado de posiciones"""
    return smart_trailing.get_position_status()

if __name__ == "__main__":
    # Test del sistema
    print("SMART TRAILING SYSTEM - TEST")
    print("=" * 50)
    
    results = apply_breakeven_to_all()
    print(f"Resultados: {results}")
    
    status = get_positions_status()
    for pos in status:
        print(f"{pos['symbol']} #{pos['ticket']}: {pos['pips_profit']} pips - "
              f"BE: {pos['breakeven_ready']}, TR: {pos['trailing_ready']}")