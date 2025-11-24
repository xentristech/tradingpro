#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA DE TRADING ACTIVO - CONFIGURACIÓN AGRESIVA
==================================================
Sistema configurado para ejecutar trades con señales más débiles
- Confianza mínima: 30%
- Trading más activo
- Monitor SL/TP integrado
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

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_activo.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingActivoSystem:
    """Sistema de trading activo con configuración agresiva"""
    
    def __init__(self):
        logger.info("="*60)
        logger.info("    SISTEMA DE TRADING ACTIVO - CONFIGURACION AGRESIVA")
        logger.info("="*60)
        
        # Configuración agresiva
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'
        self.base_url = 'https://api.twelvedata.com'
        
        # Símbolos
        self.symbols = {
            'XAUUSDm': 'XAU/USD',
            'BTCUSDm': 'BTC/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD'
        }
        
        # Configuración más agresiva
        self.min_confidence = 30.0  # Reducido de 70% a 30%
        self.risk_per_trade = 0.01  # Reducido a 1% por trade
        self.max_positions = 2      # Máximo 2 posiciones
        
        # Estados
        self.mt5_connected = False
        self.api_usage = {'used': 0, 'limit': 800}
        
        logger.info(f"CONFIGURACION AGRESIVA:")
        logger.info(f"  Confianza minima: {self.min_confidence}%")
        logger.info(f"  Riesgo por trade: {self.risk_per_trade*100}%")
        logger.info(f"  Max posiciones: {self.max_positions}")
    
    def initialize(self) -> bool:
        """Inicializa conexiones"""
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
            
            return True
            
        except Exception as e:
            logger.error(f"Error en inicializacion: {e}")
            return False
    
    def get_simple_indicators(self, symbol: str) -> Dict:
        """Obtiene indicadores básicos rápidamente"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            indicators = {}
            
            # Solo indicadores esenciales para velocidad
            essential_indicators = [
                ('rsi', {'time_period': 14}),
                ('macd', {}),
                ('sma', {'time_period': 20}),
                ('ema', {'time_period': 12}),
                ('bbands', {'time_period': 20}),
                ('atr', {'time_period': 14})
            ]
            
            for indicator_name, params in essential_indicators:
                try:
                    url = f"{self.base_url}/{indicator_name}"
                    request_params = {
                        'symbol': mapped_symbol,
                        'interval': '15min',
                        'outputsize': 20,
                        'apikey': self.api_key,
                        **params
                    }
                    
                    response = requests.get(url, params=request_params, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'values' in data and data['values']:
                            indicators[indicator_name] = data['values']
                    
                    time.sleep(0.1)
                    
                except:
                    continue
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error obteniendo indicadores para {symbol}: {e}")
            return {}
    
    def get_price_data(self, symbol: str) -> Optional[List]:
        """Obtiene datos de precios"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': mapped_symbol,
                'interval': '15min',
                'outputsize': 20,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    return data['values']
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo precios de {symbol}: {e}")
            return None
    
    def analyze_quick_signal(self, symbol: str) -> Tuple[str, float, List]:
        """Análisis rápido de señales - más agresivo"""
        try:
            # Obtener datos
            indicators = self.get_simple_indicators(symbol)
            price_data = self.get_price_data(symbol)
            
            if not indicators or not price_data:
                return 'NEUTRAL', 0.0, ['Sin datos']
            
            signal_score = 0.0
            reasons = []
            current_price = float(price_data[0]['close'])
            
            # Análisis simplificado pero efectivo
            
            # 1. RSI - Más sensible
            if 'rsi' in indicators and indicators['rsi']:
                rsi = float(indicators['rsi'][0]['rsi'])
                if rsi < 40:  # Menos estricto que 30
                    signal_score += 20
                    reasons.append(f"RSI {rsi:.1f} - Posible compra")
                elif rsi > 60:  # Menos estricto que 70
                    signal_score -= 20
                    reasons.append(f"RSI {rsi:.1f} - Posible venta")
            
            # 2. MACD simplificado
            if 'macd' in indicators and indicators['macd']:
                try:
                    macd = float(indicators['macd'][0]['macd'])
                    signal_line = float(indicators['macd'][0]['macd_signal'])
                    
                    if macd > signal_line:
                        signal_score += 15
                        reasons.append("MACD por encima de señal")
                    else:
                        signal_score -= 15
                        reasons.append("MACD por debajo de señal")
                except:
                    pass
            
            # 3. Bollinger Bands - Más agresivo
            if 'bbands' in indicators and indicators['bbands']:
                try:
                    upper = float(indicators['bbands'][0]['upper_band'])
                    lower = float(indicators['bbands'][0]['lower_band'])
                    middle = float(indicators['bbands'][0]['middle_band'])
                    
                    # Más agresivo en las bandas
                    if current_price < lower * 1.002:  # Cerca de banda inferior
                        signal_score += 15
                        reasons.append("Cerca de banda inferior BB")
                    elif current_price > upper * 0.998:  # Cerca de banda superior
                        signal_score -= 15
                        reasons.append("Cerca de banda superior BB")
                    elif current_price < middle:
                        signal_score += 5
                    else:
                        signal_score -= 5
                except:
                    pass
            
            # 4. Tendencia con SMA
            if 'sma' in indicators and indicators['sma']:
                try:
                    sma = float(indicators['sma'][0]['sma'])
                    if len(indicators['sma']) > 1:
                        prev_sma = float(indicators['sma'][1]['sma'])
                        
                        # Tendencia
                        if sma > prev_sma and current_price > sma:
                            signal_score += 10
                            reasons.append("Tendencia alcista")
                        elif sma < prev_sma and current_price < sma:
                            signal_score -= 10
                            reasons.append("Tendencia bajista")
                except:
                    pass
            
            # 5. Volatilidad (momentum adicional)
            if len(price_data) > 1:
                prev_price = float(price_data[1]['close'])
                price_change = (current_price - prev_price) / prev_price * 100
                
                if abs(price_change) > 0.1:  # Movimiento significativo
                    if price_change > 0:
                        signal_score += 5
                        reasons.append(f"Momentum alcista {price_change:.2f}%")
                    else:
                        signal_score -= 5
                        reasons.append(f"Momentum bajista {price_change:.2f}%")
            
            # Determinar dirección con umbral más bajo
            if signal_score >= 15:  # Reducido de 20
                direction = 'BUY'
                confidence = min(signal_score * 2, 100)
            elif signal_score <= -15:  # Reducido de -20
                direction = 'SELL'
                confidence = min(abs(signal_score) * 2, 100)
            else:
                direction = 'NEUTRAL'
                confidence = 0
            
            return direction, confidence, reasons
            
        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return 'NEUTRAL', 0.0, [f'Error: {str(e)}']
    
    def execute_aggressive_trade(self, symbol: str, direction: str, confidence: float, current_price: float, indicators: Dict) -> bool:
        """Ejecuta trade con configuración agresiva"""
        try:
            if not self.mt5_connected or confidence < self.min_confidence:
                return False
            
            # Verificar posiciones
            positions = mt5.positions_get()
            if positions and len(positions) >= self.max_positions:
                logger.info(f"Maximo de posiciones alcanzado: {len(positions)}")
                return False
            
            # Verificar posición existente en símbolo
            existing_pos = mt5.positions_get(symbol=symbol)
            if existing_pos:
                return False
            
            # Info del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False
            
            # ATR para SL/TP
            atr_value = None
            if 'atr' in indicators and indicators['atr']:
                atr_value = float(indicators['atr'][0]['atr'])
            else:
                atr_value = symbol_info.spread * symbol_info.point * 20
            
            # SL/TP más cercanos (menos riesgo)
            if direction == 'BUY':
                sl = current_price - (atr_value * 1.5)  # Reducido de 2.0
                tp = current_price + (atr_value * 2.5)  # Reducido de 3.0
                order_type = mt5.ORDER_TYPE_BUY
            else:
                sl = current_price + (atr_value * 1.5)
                tp = current_price - (atr_value * 2.5)
                order_type = mt5.ORDER_TYPE_SELL
            
            # Balance
            account_info = mt5.account_info()
            if not account_info:
                return False
            
            # Tamaño de posición pequeño
            sl_distance = abs(current_price - sl)
            risk_amount = account_info.balance * self.risk_per_trade
            
            if sl_distance > 0:
                volume = max(0.01, min(risk_amount / sl_distance / current_price, 0.1))
            else:
                volume = 0.01
            
            # Ajustar a límites del símbolo
            volume = max(symbol_info.volume_min, min(volume, symbol_info.volume_max))
            volume = round(volume, 2)
            
            # Preparar orden
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": current_price,
                "sl": round(sl, symbol_info.digits),
                "tp": round(tp, symbol_info.digits),
                "deviation": 30,  # Más tolerante
                "magic": 234568,
                "comment": f"Activo_{direction}_{confidence:.0f}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"[TRADE EJECUTADO] {symbol}")
                logger.info(f"  Ticket: #{result.order}")
                logger.info(f"  Direccion: {direction}")
                logger.info(f"  Volumen: {volume}")
                logger.info(f"  Precio: {current_price:.5f}")
                logger.info(f"  SL: {sl:.5f} | TP: {tp:.5f}")
                logger.info(f"  Confianza: {confidence:.1f}%")
                return True
            else:
                if result:
                    logger.warning(f"Trade rechazado {symbol}: {result.retcode}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade {symbol}: {e}")
            return False
    
    def run_active_cycle(self):
        """Ejecuta ciclo de trading activo"""
        cycle_start = time.time()
        
        logger.info("\n" + "-"*50)
        logger.info("CICLO DE TRADING ACTIVO")
        logger.info("-"*50)
        
        trades_executed = 0
        
        for symbol in self.symbols.keys():
            try:
                logger.info(f"\n[{symbol}] Analisis rapido...")
                
                direction, confidence, reasons = self.analyze_quick_signal(symbol)
                
                logger.info(f"[{symbol}] SEÑAL: {direction} (Confianza: {confidence:.1f}%)")
                
                if confidence >= self.min_confidence:
                    logger.info(f"[{symbol}] SEÑAL VALIDA - Ejecutando...")
                    
                    for reason in reasons[:2]:
                        logger.info(f"[{symbol}]   - {reason}")
                    
                    # Obtener precio actual
                    price_data = self.get_price_data(symbol)
                    if price_data:
                        current_price = float(price_data[0]['close'])
                        indicators = self.get_simple_indicators(symbol)
                        
                        if self.execute_aggressive_trade(symbol, direction, confidence, current_price, indicators):
                            trades_executed += 1
                            logger.info(f"[{symbol}] TRADE EJECUTADO!")
                        else:
                            logger.info(f"[{symbol}] Trade no ejecutado")
                else:
                    logger.info(f"[{symbol}] Señal debil (umbral: {self.min_confidence}%)")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error con {symbol}: {e}")
        
        cycle_time = time.time() - cycle_start
        
        logger.info("\n" + "-"*50)
        logger.info(f"Ciclo completado en {cycle_time:.1f}s")
        logger.info(f"Trades ejecutados: {trades_executed}")
        logger.info("-"*50)
    
    def run(self):
        """Ejecuta el sistema activo"""
        if not self.initialize():
            logger.error("No se pudo inicializar")
            return
        
        logger.info("\n" + "="*60)
        logger.info("    SISTEMA DE TRADING ACTIVO - FUNCIONANDO")
        logger.info("="*60)
        logger.info("Ciclos cada 30 segundos - Configuracion agresiva")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n[CICLO {cycle_count:04d}] {datetime.now().strftime('%H:%M:%S')}")
                
                self.run_active_cycle()
                
                # Ciclos más frecuentes
                logger.info(f"Esperando 30 segundos...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("\nSistema detenido")
        finally:
            if self.mt5_connected:
                mt5.shutdown()

def main():
    system = TradingActivoSystem()
    system.run()

if __name__ == "__main__":
    main()