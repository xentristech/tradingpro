#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA COMPLETO FUNCIONAL - TRADING + MONITOR SL/TP
===================================================
Sistema que combina:
1. Trading automático con señales
2. Monitor automático de SL/TP
3. Corrección automática con ATR
"""

import os
import sys
import time
import logging
import requests
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import threading

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/sistema_completo.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SistemaCompletoFuncional:
    """Sistema completo que combina trading automático y monitor SL/TP"""
    
    def __init__(self):
        logger.info("="*70)
        logger.info("    SISTEMA COMPLETO FUNCIONAL - TRADING + MONITOR")
        logger.info("="*70)
        
        # Configuración
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'
        self.base_url = 'https://api.twelvedata.com'
        
        # Símbolos
        self.symbols = {
            'XAUUSDm': 'XAU/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD'
        }
        
        # Configuración de trading
        self.min_confidence = 40.0  
        self.risk_per_trade = 0.02  
        self.max_positions = 2      
        
        # Estados
        self.mt5_connected = False
        self.monitor_running = False
        self.trading_running = False
        
        logger.info(f"Configuracion:")
        logger.info(f"  Confianza minima: {self.min_confidence}%")
        logger.info(f"  Riesgo por trade: {self.risk_per_trade*100}%")
        logger.info(f"  Max posiciones: {self.max_positions}")
    
    def initialize(self) -> bool:
        """Inicializa MT5"""
        try:
            if not mt5.initialize():
                logger.error("No se pudo inicializar MT5")
                return False
            
            account_info = mt5.account_info()
            if not account_info:
                logger.error("No se pudo obtener info de cuenta")
                return False
            
            self.mt5_connected = True
            
            logger.info(f"MT5 conectado - Cuenta: {account_info.login}")
            logger.info(f"Balance: ${account_info.balance:.2f}")
            logger.info(f"Servidor: {account_info.server}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en inicializacion: {e}")
            return False
    
    def calculate_atr_mt5(self, symbol: str, periods: int = 14) -> Optional[float]:
        """Calcula ATR usando datos de MT5"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, periods + 10)
            
            if rates is None or len(rates) < periods + 1:
                return None
            
            # Calcular True Range
            true_ranges = []
            for i in range(1, len(rates)):
                high = rates[i]['high']
                low = rates[i]['low']
                prev_close = rates[i-1]['close']
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                tr = max(tr1, tr2, tr3)
                true_ranges.append(tr)
            
            if len(true_ranges) >= periods:
                atr = sum(true_ranges[-periods:]) / periods
                return atr
            
            return None
            
        except Exception as e:
            logger.warning(f"Error calculando ATR para {symbol}: {e}")
            return None
    
    def monitor_and_fix_positions(self):
        """Monitorea y corrige posiciones sin SL/TP"""
        try:
            positions = mt5.positions_get()
            if not positions:
                return 0
            
            fixed_count = 0
            logger.info(f"[MONITOR] {len(positions)} posiciones encontradas")
            
            for pos in positions:
                needs_sl = pos.sl == 0
                needs_tp = pos.tp == 0
                
                if needs_sl or needs_tp:
                    logger.info(f"[FIX] Posicion {pos.ticket} necesita proteccion")
                    
                    # Calcular ATR
                    atr = self.calculate_atr_mt5(pos.symbol)
                    if atr is None:
                        # ATR por defecto según símbolo
                        if "XAU" in pos.symbol.upper() or "GOLD" in pos.symbol.upper():
                            atr = 20.0
                        else:
                            atr = 0.001
                    
                    # Calcular niveles
                    price = pos.price_current
                    
                    if pos.type == 0:  # BUY
                        new_sl = price - (atr * 2.0) if needs_sl else pos.sl
                        new_tp = price + (atr * 3.0) if needs_tp else pos.tp
                    else:  # SELL
                        new_sl = price + (atr * 2.0) if needs_sl else pos.sl
                        new_tp = price - (atr * 3.0) if needs_tp else pos.tp
                    
                    # Redondear
                    symbol_info = mt5.symbol_info(pos.symbol)
                    if symbol_info:
                        new_sl = round(new_sl, symbol_info.digits)
                        new_tp = round(new_tp, symbol_info.digits)
                    
                    # Modificar posición
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "symbol": pos.symbol,
                        "position": pos.ticket,
                        "sl": new_sl,
                        "tp": new_tp,
                        "magic": 234569
                    }
                    
                    result = mt5.order_send(request)
                    
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"[FIX OK] Pos {pos.ticket}: SL={new_sl:.5f}, TP={new_tp:.5f}, ATR={atr:.5f}")
                        fixed_count += 1
                    else:
                        logger.warning(f"[FIX FAIL] Pos {pos.ticket}: {result.retcode if result else 'No result'}")
            
            return fixed_count
            
        except Exception as e:
            logger.error(f"Error en monitor: {e}")
            return 0
    
    def get_quick_signal(self, symbol: str) -> Tuple[str, float, List]:
        """Análisis rápido de señal"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            
            # RSI rápido
            url = f"{self.base_url}/rsi"
            params = {
                'symbol': mapped_symbol,
                'interval': '15min',
                'time_period': 14,
                'outputsize': 5,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            signal_score = 0
            reasons = []
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and data['values']:
                    rsi = float(data['values'][0]['rsi'])
                    
                    if rsi < 35:
                        signal_score += 30
                        reasons.append(f"RSI sobreventa: {rsi:.1f}")
                    elif rsi > 65:
                        signal_score -= 30
                        reasons.append(f"RSI sobrecompra: {rsi:.1f}")
                    elif 45 <= rsi <= 55:
                        signal_score += 5
                        reasons.append("RSI neutral")
            
            # Precio de TwelveData
            url2 = f"{self.base_url}/time_series"
            params2 = {
                'symbol': mapped_symbol,
                'interval': '15min',
                'outputsize': 3,
                'apikey': self.api_key
            }
            
            response2 = requests.get(url2, params=params2, timeout=5)
            
            if response2.status_code == 200:
                data2 = response2.json()
                if 'values' in data2 and len(data2['values']) >= 2:
                    current = float(data2['values'][0]['close'])
                    previous = float(data2['values'][1]['close'])
                    
                    change_pct = (current - previous) / previous * 100
                    
                    if abs(change_pct) > 0.05:  # Movimiento significativo
                        if change_pct > 0:
                            signal_score += 10
                            reasons.append(f"Momentum alcista +{change_pct:.2f}%")
                        else:
                            signal_score -= 10
                            reasons.append(f"Momentum bajista {change_pct:.2f}%")
            
            # Determinar señal
            if signal_score >= 20:
                return 'BUY', min(signal_score * 2, 100), reasons
            elif signal_score <= -20:
                return 'SELL', min(abs(signal_score) * 2, 100), reasons
            else:
                return 'NEUTRAL', 0, reasons
                
        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return 'NEUTRAL', 0, [f'Error: {str(e)}']
    
    def execute_trade(self, symbol: str, direction: str, confidence: float) -> bool:
        """Ejecuta un trade"""
        try:
            if confidence < self.min_confidence:
                return False
            
            # Verificar posiciones
            positions = mt5.positions_get()
            if positions and len(positions) >= self.max_positions:
                return False
            
            # Verificar posición existente
            existing_pos = mt5.positions_get(symbol=symbol)
            if existing_pos:
                return False
            
            # Info del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False
            
            # Precio actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False
            
            current_price = tick.bid if direction == 'SELL' else tick.ask
            
            # ATR para SL/TP
            atr = self.calculate_atr_mt5(symbol)
            if atr is None:
                if "XAU" in symbol.upper():
                    atr = 20.0
                else:
                    atr = 0.001
            
            # Calcular SL/TP
            if direction == 'BUY':
                sl = current_price - (atr * 2.0)
                tp = current_price + (atr * 3.0)
                order_type = mt5.ORDER_TYPE_BUY
            else:
                sl = current_price + (atr * 2.0)
                tp = current_price - (atr * 3.0)
                order_type = mt5.ORDER_TYPE_SELL
            
            # Tamaño de posición
            account_info = mt5.account_info()
            if not account_info:
                return False
            
            volume = 0.01  # Volumen fijo pequeño para pruebas
            
            # Preparar orden
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": current_price,
                "sl": round(sl, symbol_info.digits),
                "tp": round(tp, symbol_info.digits),
                "deviation": 20,
                "magic": 234569,
                "comment": f"Auto_{direction}_{confidence:.0f}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"[TRADE OK] {symbol} {direction} #{result.order}")
                logger.info(f"  Precio: {current_price:.5f} | SL: {sl:.5f} | TP: {tp:.5f}")
                logger.info(f"  Confianza: {confidence:.1f}% | ATR: {atr:.5f}")
                return True
            else:
                if result:
                    logger.warning(f"[TRADE FAIL] {symbol}: {result.retcode}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade {symbol}: {e}")
            return False
    
    def trading_cycle(self):
        """Ciclo de trading"""
        cycle = 0
        while self.trading_running:
            try:
                cycle += 1
                logger.info(f"\n[TRADING CYCLE {cycle:03d}] {datetime.now().strftime('%H:%M:%S')}")
                
                trades_executed = 0
                
                for symbol in self.symbols.keys():
                    try:
                        direction, confidence, reasons = self.get_quick_signal(symbol)
                        
                        logger.info(f"[{symbol}] {direction} ({confidence:.1f}%)")
                        
                        if confidence >= self.min_confidence:
                            logger.info(f"[{symbol}] Ejecutando trade...")
                            if self.execute_trade(symbol, direction, confidence):
                                trades_executed += 1
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error con {symbol}: {e}")
                
                logger.info(f"Trades ejecutados: {trades_executed}")
                
                # Esperar antes del próximo ciclo
                time.sleep(45)
                
            except Exception as e:
                logger.error(f"Error en ciclo trading: {e}")
                time.sleep(30)
    
    def monitor_cycle(self):
        """Ciclo de monitoreo SL/TP"""
        cycle = 0
        while self.monitor_running:
            try:
                cycle += 1
                logger.info(f"\n[MONITOR CYCLE {cycle:03d}] {datetime.now().strftime('%H:%M:%S')}")
                
                fixed_positions = self.monitor_and_fix_positions()
                
                if fixed_positions > 0:
                    logger.info(f"[MONITOR] {fixed_positions} posiciones corregidas")
                else:
                    logger.info(f"[MONITOR] Todas las posiciones protegidas")
                
                # Esperar antes del próximo check
                time.sleep(15)
                
            except Exception as e:
                logger.error(f"Error en ciclo monitor: {e}")
                time.sleep(30)
    
    def run(self):
        """Ejecuta el sistema completo"""
        if not self.initialize():
            logger.error("No se pudo inicializar")
            return
        
        logger.info("\n" + "="*70)
        logger.info("    SISTEMA COMPLETO FUNCIONAL - ACTIVO")
        logger.info("="*70)
        logger.info("Trading cada 45s + Monitor SL/TP cada 15s")
        
        # Activar ambos sistemas
        self.trading_running = True
        self.monitor_running = True
        
        # Crear threads separados
        trading_thread = threading.Thread(target=self.trading_cycle, name="TradingThread")
        monitor_thread = threading.Thread(target=self.monitor_cycle, name="MonitorThread")
        
        try:
            # Iniciar threads
            trading_thread.start()
            monitor_thread.start()
            
            logger.info("[SISTEMA] Ambos threads iniciados correctamente")
            logger.info("Presiona Ctrl+C para detener")
            
            # Mantener el programa corriendo
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n[SISTEMA] Deteniendo...")
            
            # Detener threads
            self.trading_running = False
            self.monitor_running = False
            
            # Esperar a que terminen
            trading_thread.join(timeout=5)
            monitor_thread.join(timeout=5)
            
        finally:
            if self.mt5_connected:
                mt5.shutdown()
            logger.info("[SISTEMA] Finalizado")

def main():
    system = SistemaCompletoFuncional()
    system.run()

if __name__ == "__main__":
    main()