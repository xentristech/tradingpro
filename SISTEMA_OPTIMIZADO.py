#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA DE TRADING OPTIMIZADO
=============================
Combina:
- Generador de señales mejorado con 15+ indicadores
- Monitor automático de SL/TP con ATR
- Integración completa MT5 + TwelveData
- Sistema de trading automático
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

# Configurar logging sin caracteres especiales
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/sistema_optimizado.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedTradingSystem:
    """Sistema de trading optimizado completo"""
    
    def __init__(self):
        """Inicializa el sistema optimizado"""
        logger.info("="*60)
        logger.info("    SISTEMA DE TRADING OPTIMIZADO - INICIANDO")
        logger.info("="*60)
        
        # Configuración
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'
        self.base_url = 'https://api.twelvedata.com'
        
        # Símbolos MT5 -> TwelveData
        self.symbols = {
            'XAUUSDm': 'XAU/USD',
            'BTCUSDm': 'BTC/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD'
        }
        
        # Estados
        self.mt5_connected = False
        self.api_usage = {'used': 0, 'limit': 800}
        self.active_positions = {}
        
        # Configuración de trading
        self.min_confidence = 70.0  # Confianza mínima para ejecutar
        self.risk_per_trade = 0.02  # 2% del balance por trade
        self.max_positions = 3     # Máximo posiciones simultáneas
        
        logger.info(f"Simbolos configurados: {list(self.symbols.keys())}")
        logger.info(f"Confianza minima: {self.min_confidence}%")
        logger.info(f"Riesgo por trade: {self.risk_per_trade*100}%")
    
    def initialize(self) -> bool:
        """Inicializa conexiones"""
        try:
            # Conectar MT5
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
            
            # Verificar API TwelveData
            usage = self.check_api_usage()
            if usage:
                logger.info(f"TwelveData API: {usage['used']}/{usage['limit']} llamadas")
                self.api_usage = usage
            
            return True
            
        except Exception as e:
            logger.error(f"Error en inicializacion: {e}")
            return False
    
    def check_api_usage(self) -> Optional[Dict]:
        """Verifica uso de API TwelveData"""
        try:
            url = f"{self.base_url}/api_usage"
            params = {'apikey': self.api_key}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'used': data.get('current_usage', 0),
                    'limit': data.get('plan_limit', 800)
                }
        except:
            pass
        return None
    
    def get_comprehensive_indicators(self, symbol: str, timeframe: str = '15min') -> Dict:
        """Obtiene indicadores completos de TwelveData"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            indicators = {}
            
            # Lista de indicadores a obtener
            indicator_configs = [
                ('rsi', {'time_period': 14}),
                ('rsi', {'time_period': 21}),
                ('macd', {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}),
                ('stoch', {'fastkperiod': 14, 'slowkperiod': 3, 'slowdperiod': 3}),
                ('bbands', {'time_period': 20, 'nbdevup': 2, 'nbdevdn': 2}),
                ('sma', {'time_period': 20}),
                ('sma', {'time_period': 50}),
                ('ema', {'time_period': 12}),
                ('ema', {'time_period': 26}),
                ('atr', {'time_period': 14}),
                ('cci', {'time_period': 20}),
                ('williams', {'time_period': 14}),
                ('obv', {}),
                ('adx', {'time_period': 14})
            ]
            
            for indicator_name, params in indicator_configs:
                try:
                    # Verificar límite de API
                    if self.api_usage['used'] >= self.api_usage['limit'] - 10:
                        logger.warning("Cerca del limite de API, saltando indicadores")
                        break
                    
                    url = f"{self.base_url}/{indicator_name}"
                    
                    request_params = {
                        'symbol': mapped_symbol,
                        'interval': timeframe,
                        'outputsize': 30,
                        'apikey': self.api_key,
                        **params
                    }
                    
                    response = requests.get(url, params=request_params, timeout=8)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'values' in data and data['values']:
                            key = f"{indicator_name}_{params.get('time_period', '')}" if params else indicator_name
                            indicators[key] = data['values']
                            self.api_usage['used'] += 1
                    
                    time.sleep(0.2)  # Pausa para evitar rate limiting
                    
                except Exception as e:
                    logger.warning(f"Error obteniendo {indicator_name}: {e}")
                    continue
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error obteniendo indicadores para {symbol}: {e}")
            return {}
    
    def get_price_data(self, symbol: str, timeframe: str = '15min') -> Optional[List]:
        """Obtiene datos de precios OHLCV"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': mapped_symbol,
                'interval': timeframe,
                'outputsize': 50,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    self.api_usage['used'] += 1
                    return data['values']
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo precios de {symbol}: {e}")
            return None
    
    def analyze_signal_strength(self, symbol: str, indicators: Dict, price_data: List) -> Tuple[str, float, List]:
        """Analiza fuerza de señal con múltiples indicadores"""
        try:
            if not indicators or not price_data:
                return 'NEUTRAL', 0.0, ['Sin datos suficientes']
            
            signal_score = 0.0
            reasons = []
            current_price = float(price_data[0]['close'])
            
            # 1. RSI Analysis
            if 'rsi_14' in indicators and indicators['rsi_14']:
                rsi = float(indicators['rsi_14'][0]['rsi'])
                if rsi < 30:
                    signal_score += 15
                    reasons.append(f"RSI sobreventa: {rsi:.1f}")
                elif rsi > 70:
                    signal_score -= 15
                    reasons.append(f"RSI sobrecompra: {rsi:.1f}")
                elif 45 <= rsi <= 55:
                    signal_score += 3  # RSI neutral
            
            # 2. MACD Analysis
            if 'macd' in indicators and indicators['macd']:
                try:
                    macd = float(indicators['macd'][0]['macd'])
                    signal_line = float(indicators['macd'][0]['macd_signal'])
                    histogram = float(indicators['macd'][0]['macd_histogram'])
                    
                    if len(indicators['macd']) > 1:
                        prev_histogram = float(indicators['macd'][1]['macd_histogram'])
                        
                        # Cruce alcista
                        if prev_histogram <= 0 and histogram > 0:
                            signal_score += 12
                            reasons.append("MACD cruce alcista")
                        # Cruce bajista  
                        elif prev_histogram >= 0 and histogram < 0:
                            signal_score -= 12
                            reasons.append("MACD cruce bajista")
                        # Momentum creciente
                        elif histogram > prev_histogram and histogram > 0:
                            signal_score += 5
                            reasons.append("MACD momentum alcista")
                        elif histogram < prev_histogram and histogram < 0:
                            signal_score -= 5
                            reasons.append("MACD momentum bajista")
                except:
                    pass
            
            # 3. Bollinger Bands
            if 'bbands_20' in indicators and indicators['bbands_20']:
                try:
                    upper = float(indicators['bbands_20'][0]['upper_band'])
                    lower = float(indicators['bbands_20'][0]['lower_band'])
                    middle = float(indicators['bbands_20'][0]['middle_band'])
                    
                    if current_price <= lower:
                        signal_score += 10
                        reasons.append("Precio en banda inferior BB")
                    elif current_price >= upper:
                        signal_score -= 10  
                        reasons.append("Precio en banda superior BB")
                    elif current_price < middle:
                        signal_score += 2
                except:
                    pass
            
            # 4. Moving Average Trend
            if 'sma_20' in indicators and 'sma_50' in indicators:
                if (indicators['sma_20'] and indicators['sma_50'] and 
                    len(indicators['sma_20']) > 1 and len(indicators['sma_50']) > 1):
                    try:
                        sma20_curr = float(indicators['sma_20'][0]['sma'])
                        sma20_prev = float(indicators['sma_20'][1]['sma'])
                        sma50_curr = float(indicators['sma_50'][0]['sma'])
                        
                        # Golden Cross
                        if sma20_prev <= sma50_curr and sma20_curr > sma50_curr:
                            signal_score += 8
                            reasons.append("Golden Cross SMA 20/50")
                        # Death Cross
                        elif sma20_prev >= sma50_curr and sma20_curr < sma50_curr:
                            signal_score -= 8
                            reasons.append("Death Cross SMA 20/50")
                        # Tendencia alcista
                        elif sma20_curr > sma50_curr and current_price > sma20_curr:
                            signal_score += 4
                            reasons.append("Tendencia alcista confirmada")
                        # Tendencia bajista
                        elif sma20_curr < sma50_curr and current_price < sma20_curr:
                            signal_score -= 4
                            reasons.append("Tendencia bajista confirmada")
                    except:
                        pass
            
            # 5. Stochastic
            if 'stoch' in indicators and indicators['stoch']:
                try:
                    slow_k = float(indicators['stoch'][0]['slow_k'])
                    slow_d = float(indicators['stoch'][0]['slow_d'])
                    
                    if slow_k < 20 and slow_d < 20:
                        signal_score += 6
                        reasons.append(f"Stochastic sobreventa: {slow_k:.1f}")
                    elif slow_k > 80 and slow_d > 80:
                        signal_score -= 6
                        reasons.append(f"Stochastic sobrecompra: {slow_k:.1f}")
                except:
                    pass
            
            # 6. Williams %R
            if 'williams_14' in indicators and indicators['williams_14']:
                try:
                    williams = float(indicators['williams_14'][0]['williams'])
                    
                    if williams < -80:
                        signal_score += 4
                        reasons.append(f"Williams %R sobreventa: {williams:.1f}")
                    elif williams > -20:
                        signal_score -= 4
                        reasons.append(f"Williams %R sobrecompra: {williams:.1f}")
                except:
                    pass
            
            # 7. CCI (Commodity Channel Index)
            if 'cci_20' in indicators and indicators['cci_20']:
                try:
                    cci = float(indicators['cci_20'][0]['cci'])
                    
                    if cci < -100:
                        signal_score += 5
                        reasons.append(f"CCI sobreventa: {cci:.1f}")
                    elif cci > 100:
                        signal_score -= 5
                        reasons.append(f"CCI sobrecompra: {cci:.1f}")
                except:
                    pass
            
            # Determinar dirección y confianza
            if signal_score >= 20:
                direction = 'BUY'
                confidence = min(signal_score * 2.5, 100)
            elif signal_score <= -20:
                direction = 'SELL'
                confidence = min(abs(signal_score) * 2.5, 100)
            else:
                direction = 'NEUTRAL'
                confidence = 0
            
            return direction, confidence, reasons
            
        except Exception as e:
            logger.error(f"Error analizando señal para {symbol}: {e}")
            return 'NEUTRAL', 0.0, [f'Error: {str(e)}']
    
    def calculate_position_size(self, account_balance: float, stop_loss_distance: float, current_price: float) -> float:
        """Calcula tamaño de posición basado en riesgo"""
        try:
            risk_amount = account_balance * self.risk_per_trade
            
            if stop_loss_distance > 0:
                # Calcular tamaño basado en distancia de SL
                position_size = risk_amount / stop_loss_distance
                
                # Convertir a lotes (mínimo 0.01, máximo 10)
                lot_size = max(0.01, min(position_size / current_price, 10.0))
                
                # Redondear a 2 decimales
                return round(lot_size, 2)
            else:
                return 0.01  # Tamaño mínimo por defecto
                
        except:
            return 0.01
    
    def execute_trade(self, symbol: str, direction: str, confidence: float, current_price: float, indicators: Dict) -> bool:
        """Ejecuta un trade si cumple criterios"""
        try:
            if not self.mt5_connected or confidence < self.min_confidence:
                return False
            
            # Verificar máximo de posiciones
            positions = mt5.positions_get()
            if positions and len(positions) >= self.max_positions:
                logger.info(f"Maximo de posiciones alcanzado: {len(positions)}")
                return False
            
            # Verificar si ya hay posición en este símbolo
            existing_pos = mt5.positions_get(symbol=symbol)
            if existing_pos:
                logger.info(f"Ya existe posicion en {symbol}")
                return False
            
            # Obtener info del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger.error(f"No se pudo obtener info de {symbol}")
                return False
            
            # Calcular ATR para SL/TP
            atr_value = None
            if 'atr_14' in indicators and indicators['atr_14']:
                atr_value = float(indicators['atr_14'][0]['atr'])
            else:
                # ATR estimado como 1.5 veces el spread típico
                atr_value = symbol_info.spread * symbol_info.point * 50
            
            # Calcular SL y TP
            if direction == 'BUY':
                sl = current_price - (atr_value * 2.0)
                tp = current_price + (atr_value * 3.0)
                order_type = mt5.ORDER_TYPE_BUY
            else:  # SELL
                sl = current_price + (atr_value * 2.0)
                tp = current_price - (atr_value * 3.0)
                order_type = mt5.ORDER_TYPE_SELL
            
            # Obtener balance de cuenta
            account_info = mt5.account_info()
            if not account_info:
                return False
            
            # Calcular tamaño de posición
            sl_distance = abs(current_price - sl)
            volume = self.calculate_position_size(account_info.balance, sl_distance, current_price)
            
            # Ajustar volumen a los límites del símbolo
            volume = max(symbol_info.volume_min, min(volume, symbol_info.volume_max))
            
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
                "magic": 234567,
                "comment": f"Auto_{direction}_{confidence:.0f}%",
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
                logger.info(f"  ATR usado: {atr_value:.5f}")
                return True
            else:
                error_msg = result.comment if result else "Sin respuesta"
                logger.warning(f"Trade rechazado para {symbol}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade {symbol}: {e}")
            return False
    
    def monitor_and_fix_positions(self):
        """Monitorea y corrige posiciones sin SL/TP"""
        try:
            positions = mt5.positions_get()
            if not positions:
                return
            
            for pos in positions:
                needs_fix = pos.sl == 0 or pos.tp == 0
                
                if needs_fix:
                    logger.info(f"[FIX] Posicion {pos.ticket} necesita SL/TP")
                    
                    # Obtener ATR actual del símbolo
                    indicators = self.get_comprehensive_indicators(pos.symbol)
                    atr_value = None
                    
                    if 'atr_14' in indicators and indicators['atr_14']:
                        atr_value = float(indicators['atr_14'][0]['atr'])
                    else:
                        # ATR estimado
                        symbol_info = mt5.symbol_info(pos.symbol)
                        if symbol_info:
                            atr_value = symbol_info.spread * symbol_info.point * 30
                        else:
                            continue
                    
                    # Calcular nuevos niveles
                    price = pos.price_current
                    
                    if pos.type == 0:  # BUY
                        new_sl = price - (atr_value * 2.0) if pos.sl == 0 else pos.sl
                        new_tp = price + (atr_value * 3.0) if pos.tp == 0 else pos.tp
                    else:  # SELL
                        new_sl = price + (atr_value * 2.0) if pos.sl == 0 else pos.sl
                        new_tp = price - (atr_value * 3.0) if pos.tp == 0 else pos.tp
                    
                    # Obtener info del símbolo para redondeo
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
                        "magic": 234567
                    }
                    
                    result = mt5.order_send(request)
                    
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"[FIX OK] Posicion {pos.ticket}: SL={new_sl:.5f}, TP={new_tp:.5f}")
                    else:
                        logger.warning(f"[FIX FAIL] Posicion {pos.ticket}")
                        
        except Exception as e:
            logger.error(f"Error monitoreando posiciones: {e}")
    
    def run_analysis_cycle(self):
        """Ejecuta un ciclo completo de análisis"""
        cycle_start = time.time()
        
        logger.info("\n" + "-"*50)
        logger.info("INICIANDO CICLO DE ANALISIS")
        logger.info("-"*50)
        
        signals_generated = 0
        trades_executed = 0
        
        for symbol in self.symbols.keys():
            try:
                logger.info(f"\n[{symbol}] Obteniendo datos...")
                
                # Obtener datos de precios
                price_data = self.get_price_data(symbol)
                if not price_data:
                    logger.warning(f"[{symbol}] Sin datos de precios")
                    continue
                
                # Obtener indicadores
                indicators = self.get_comprehensive_indicators(symbol)
                if not indicators:
                    logger.warning(f"[{symbol}] Sin indicadores")
                    continue
                
                current_price = float(price_data[0]['close'])
                logger.info(f"[{symbol}] Precio actual: {current_price:.4f}")
                logger.info(f"[{symbol}] Indicadores obtenidos: {len(indicators)}")
                
                # Analizar señal
                direction, confidence, reasons = self.analyze_signal_strength(
                    symbol, indicators, price_data
                )
                
                signals_generated += 1
                
                logger.info(f"[{symbol}] SEÑAL: {direction}")
                logger.info(f"[{symbol}] Confianza: {confidence:.1f}%")
                
                if confidence >= self.min_confidence:
                    logger.info(f"[{symbol}] SEÑAL FUERTE - Intentando ejecutar trade")
                    
                    # Mostrar razones principales
                    for reason in reasons[:3]:
                        logger.info(f"[{symbol}]   - {reason}")
                    
                    # Ejecutar trade
                    if self.execute_trade(symbol, direction, confidence, current_price, indicators):
                        trades_executed += 1
                        logger.info(f"[{symbol}] TRADE EJECUTADO EXITOSAMENTE")
                    else:
                        logger.info(f"[{symbol}] Trade no ejecutado")
                else:
                    logger.info(f"[{symbol}] Señal debil - No ejecutar")
                
                time.sleep(1)  # Pausa entre símbolos
                
            except Exception as e:
                logger.error(f"Error analizando {symbol}: {e}")
        
        # Monitorear posiciones existentes
        self.monitor_and_fix_positions()
        
        cycle_time = time.time() - cycle_start
        
        logger.info("\n" + "-"*50)
        logger.info("RESUMEN DEL CICLO")
        logger.info("-"*50)
        logger.info(f"Duracion: {cycle_time:.1f} segundos")
        logger.info(f"Señales generadas: {signals_generated}")
        logger.info(f"Trades ejecutados: {trades_executed}")
        logger.info(f"API calls usadas: {self.api_usage['used']}/{self.api_usage['limit']}")
        
        # Actualizar uso de API
        usage = self.check_api_usage()
        if usage:
            self.api_usage = usage
    
    def run(self):
        """Ejecuta el sistema completo"""
        if not self.initialize():
            logger.error("No se pudo inicializar el sistema")
            return
        
        logger.info("\n" + "="*60)
        logger.info("    SISTEMA OPTIMIZADO ACTIVO")
        logger.info("="*60)
        logger.info("Presiona Ctrl+C para detener")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n[CICLO {cycle_count:04d}] {datetime.now().strftime('%H:%M:%S')}")
                
                self.run_analysis_cycle()
                
                # Pausa entre ciclos
                logger.info(f"Esperando 60 segundos hasta el proximo ciclo...")
                time.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("\nSistema detenido por el usuario")
        except Exception as e:
            logger.error(f"Error en sistema: {e}")
        finally:
            if self.mt5_connected:
                mt5.shutdown()
            logger.info("Sistema finalizado")

def main():
    """Función principal"""
    system = OptimizedTradingSystem()
    system.run()

if __name__ == "__main__":
    main()