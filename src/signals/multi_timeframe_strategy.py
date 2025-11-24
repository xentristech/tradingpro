#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ESTRATEGIA MULTI-TIMEFRAME CON TWELVEDATA + IA
Analiza múltiples timeframes y genera señales precisas
"""
import os
import time
import requests
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Cargar configuración
load_dotenv('configs/.env')

logger = logging.getLogger(__name__)

class MultiTimeframeStrategy:
    """Estrategia avanzada multi-timeframe con TwelveData"""
    
    def __init__(self):
        """Inicializa la estrategia"""
        # API Keys
        self.api_key = os.getenv('TWELVEDATA_API_KEY', 'demo')
        self.ollama_base = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/v1')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'deepseek-r1:8b')
        
        # Timeframes a analizar
        self.timeframes = ['5min', '15min', '30min', '1h']
        
        # Cache de datos
        self.datos_guardados = {tf: {} for tf in self.timeframes}
        self.cierres_guardados = {tf: [] for tf in self.timeframes}
        self.datetime_guardados = {tf: None for tf in self.timeframes}
        
        # Contador de análisis
        self.analysis_count = 0
        
        logger.info("MultiTimeframe Strategy inicializada")
    
    def consulta_twelvedata(self, indicador: str, symbol: str, tf: str, params: Dict = None) -> Dict:
        """
        Consulta indicador específico en TwelveData
        
        Args:
            indicador: Nombre del indicador (rsi, macd, etc)
            symbol: Símbolo a consultar (BTC/USD, EUR/USD, etc)
            tf: Timeframe (5min, 15min, 30min, 1h)
            params: Parámetros adicionales
            
        Returns:
            Dict con valores del indicador
        """
        if params is None:
            params = {}
            
        # Mapear símbolo para TwelveData
        symbol_map = {
            'BTCUSD': 'BTC/USD',
            'BTCUSDm': 'BTC/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'XAUUSD': 'XAU/USD',
            'XAUUSDm': 'XAU/USD',  # Mapeo para símbolo MT5 oro
            'ETHUSD': 'ETH/USD',
            'ETHUSDm': 'ETH/USD'
        }
        
        api_symbol = symbol_map.get(symbol, symbol)
        
        url = f"https://api.twelvedata.com/{indicador}"
        default_params = {
            "symbol": api_symbol,
            "interval": tf,
            "apikey": self.api_key
        }
        default_params.update(params)
        
        try:
            r = requests.get(url, params=default_params, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            if "values" in data and data["values"]:
                return data["values"][0]
            else:
                logger.debug(f"Sin datos para {indicador} {tf}: {data}")
                return {}
                
        except Exception as e:
            logger.error(f"Error consultando {indicador} {tf}: {e}")
            return {}
    
    def get_indicadores_tf(self, symbol: str, tf: str) -> Dict:
        """
        Obtiene todos los indicadores para un timeframe
        
        Args:
            symbol: Símbolo a analizar
            tf: Timeframe
            
        Returns:
            Dict con todos los indicadores
        """
        indicadores = {
            "precio": self.consulta_twelvedata("price", symbol, tf),
            "vwap": self.consulta_twelvedata("vwap", symbol, tf),
            "rsi": self.consulta_twelvedata("rsi", symbol, tf, {"time_period": 14}),
            "macd": self.consulta_twelvedata("macd", symbol, tf),
            "bollinger": self.consulta_twelvedata("bbands", symbol, tf),
            "adx": self.consulta_twelvedata("adx", symbol, tf, {"time_period": 14}),
            "percent_b": self.consulta_twelvedata("percent_b", symbol, tf),
            "obv": self.consulta_twelvedata("obv", symbol, tf),
            "atr": self.consulta_twelvedata("atr", symbol, tf, {"time_period": 14}),
            "cci": self.consulta_twelvedata("cci", symbol, tf, {"time_period": 14}),
            "stochastic": self.consulta_twelvedata("stoch", symbol, tf),
            "sma_20": self.consulta_twelvedata("sma", symbol, tf, {"time_period": 20}),
            "ema_12": self.consulta_twelvedata("ema", symbol, tf, {"time_period": 12}),
            "momentum": self.consulta_twelvedata("mom", symbol, tf, {"time_period": 10})
        }
        
        # Filtrar indicadores vacíos
        indicadores_validos = {k: v for k, v in indicadores.items() if v}
        
        return indicadores_validos
    
    def obtener_cierres(self, symbol: str, tf: str, cantidad: int = 30) -> List[float]:
        """
        Obtiene histórico de cierres
        
        Args:
            symbol: Símbolo
            tf: Timeframe
            cantidad: Número de velas a obtener
            
        Returns:
            Lista de precios de cierre
        """
        # Mapear símbolo
        symbol_map = {
            'BTCUSD': 'BTC/USD',
            'BTCUSDm': 'BTC/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'XAUUSD': 'XAU/USD',
            'XAUUSDm': 'XAU/USD',  # Mapeo para símbolo MT5 oro
            'ETHUSD': 'ETH/USD',
            'ETHUSDm': 'ETH/USD'
        }
        api_symbol = symbol_map.get(symbol, symbol)
        
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": api_symbol,
            "interval": tf,
            "outputsize": cantidad,
            "apikey": self.api_key
        }
        
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            datos = r.json().get("values", [])
            cierres = [float(d.get("close", 0)) for d in datos if "close" in d]
            return cierres[:10]  # Solo últimos 10 para el prompt
            
        except Exception as e:
            logger.error(f"Error obteniendo cierres: {e}")
            return []
    
    def limpiar_datos(self, datos: Dict) -> Dict:
        """
        Limpia y aplana los datos de indicadores
        
        Args:
            datos: Dict con indicadores anidados
            
        Returns:
            Dict aplanado
        """
        out = {}
        for k, v in datos.items():
            if isinstance(v, dict):
                # Aplanar diccionarios anidados
                for sk, sv in v.items():
                    out[f"{k}_{sk}"] = sv
            else:
                out[k] = v
                
        # Conservar datetime si existe
        if "datetime" in datos:
            out["datetime"] = datos["datetime"]
            
        return out
    
    def generar_prompt(self, symbol: str, indicadores_multi: Dict, cierres_multi: Dict) -> str:
        """
        Genera prompt para la IA
        
        Args:
            symbol: Símbolo analizado
            indicadores_multi: Dict con indicadores por timeframe
            cierres_multi: Dict con cierres por timeframe
            
        Returns:
            Prompt formateado
        """
        PROMPT = f"""
Analiza {symbol} técnicamente. Formato:
"""
        
        # Agregar datos por timeframe
        for tf in self.timeframes:
            if tf in indicadores_multi and indicadores_multi[tf]:
                PROMPT += f"\n--- {tf} ---\n"
                inds = self.limpiar_datos(indicadores_multi[tf])
                
                for k, v in inds.items():
                    PROMPT += f"{k}: {v}\n"
                    
                if tf in cierres_multi and cierres_multi[tf]:
                    PROMPT += f"Últimos cierres: {cierres_multi[tf][:5]}\n"
        
        PROMPT += """

DECISION: COMPRA/VENTA/NO_OPERAR
CONFIANZA: [0-100]%
ENTRADA: [precio]
STOP_LOSS: [precio]
TAKE_PROFIT: [precio]
RAZON: [breve]
"""
        
        return PROMPT
    
    def analizar_con_ia(self, prompt: str) -> Dict:
        """
        Analiza con Ollama/OpenAI
        
        Args:
            prompt: Prompt a enviar
            
        Returns:
            Dict con la decisión parseada
        """
        try:
            # Usar requests directamente para Ollama
            import requests
            
            url = f"{self.ollama_base}/chat/completions"
            
            payload = {
                "model": self.ollama_model,
                "messages": [
                    {"role": "system", "content": "Eres un analista técnico experto. Responde SOLO con el formato solicitado."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 200
            }
            
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            
            data = response.json()
            respuesta = data['choices'][0]['message']['content']
            
            # Parsear respuesta
            decision = re.search(r"DECISION:\s*(\w+)", respuesta)
            confianza = re.search(r"CONFIANZA:\s*(\d+)", respuesta)
            entrada = re.search(r"ENTRADA:\s*([\d.]+)", respuesta)
            sl = re.search(r"STOP_LOSS:\s*([\d.]+)", respuesta)
            tp = re.search(r"TAKE_PROFIT:\s*([\d.]+)", respuesta)
            razon = re.search(r"RAZON:\s*(.+)", respuesta)
            
            return {
                'decision': decision.group(1) if decision else 'NO_OPERAR',
                'confianza': float(confianza.group(1)) if confianza else 0,
                'entrada': float(entrada.group(1)) if entrada else 0,
                'stop_loss': float(sl.group(1)) if sl else 0,
                'take_profit': float(tp.group(1)) if tp else 0,
                'razon': razon.group(1) if razon else 'Sin razón especificada',
                'respuesta_completa': respuesta
            }
            
        except Exception as e:
            logger.error(f"Error analizando con IA: {e}")
            return {
                'decision': 'NO_OPERAR',
                'confianza': 0,
                'razon': f'Error en análisis: {str(e)}'
            }
    
    def debe_actualizar(self, tf: str, dt: datetime) -> bool:
        """
        Determina si debe actualizar datos para un timeframe
        
        Args:
            tf: Timeframe
            dt: Datetime actual
            
        Returns:
            True si debe actualizar
        """
        minute = dt.minute
        
        if tf == "5min":
            return minute % 5 == 0
        elif tf == "15min":
            return minute % 15 == 0
        elif tf == "30min":
            return minute % 30 == 0
        elif tf == "1h":
            return minute == 0  # Solo al inicio de cada hora
            
        return False
    
    def generate_signal(self, df, symbol: str) -> List[Dict]:
        """
        Genera señal usando análisis multi-timeframe
        
        Args:
            df: DataFrame con datos (no usado aquí, para compatibilidad)
            symbol: Símbolo a analizar
            
        Returns:
            Lista de señales generadas
        """
        signals = []
        
        try:
            self.analysis_count += 1
            logger.info(f"[MULTI-TF] Análisis #{self.analysis_count} para {symbol}")
            
            # Actualizar datos por timeframe
            now = datetime.now()
            indicadores_actuales = {}
            cierres_actuales = {}
            
            for tf in self.timeframes:
                # Verificar si debe actualizar o usar cache
                if not self.datos_guardados[tf] or self.debe_actualizar(tf, now):
                    logger.info(f"Actualizando datos {tf} para {symbol}")
                    
                    # Obtener nuevos indicadores
                    nuevos_indicadores = self.get_indicadores_tf(symbol, tf)
                    
                    if nuevos_indicadores:
                        self.datos_guardados[tf] = nuevos_indicadores
                        self.cierres_guardados[tf] = self.obtener_cierres(symbol, tf, 30)
                        self.datetime_guardados[tf] = now
                        
                        indicadores_actuales[tf] = nuevos_indicadores
                        cierres_actuales[tf] = self.cierres_guardados[tf]
                    else:
                        # Usar cache si no hay nuevos datos
                        indicadores_actuales[tf] = self.datos_guardados[tf]
                        cierres_actuales[tf] = self.cierres_guardados[tf]
                else:
                    # Usar datos cacheados
                    indicadores_actuales[tf] = self.datos_guardados[tf]
                    cierres_actuales[tf] = self.cierres_guardados[tf]
            
            # Verificar que tenemos datos suficientes
            if not all(indicadores_actuales.values()):
                logger.warning(f"Datos insuficientes para análisis multi-timeframe de {symbol}")
                return signals
            
            # Generar prompt y analizar con IA
            prompt = self.generar_prompt(symbol, indicadores_actuales, cierres_actuales)
            
            logger.info("Consultando IA para análisis multi-timeframe...")
            resultado = self.analizar_con_ia(prompt)
            
            logger.info(f"Decisión IA: {resultado['decision']} (Confianza: {resultado['confianza']}%)")
            
            # Generar señal si hay decisión de trading
            if resultado['decision'] in ['COMPRA', 'VENTA'] and resultado['confianza'] >= 70:
                
                # Obtener precio actual
                precio_actual = 0
                if 'precio_price' in indicadores_actuales['5min']:
                    precio_actual = float(indicadores_actuales['5min']['precio_price'])
                elif cierres_actuales['5min']:
                    precio_actual = float(cierres_actuales['5min'][0])
                else:
                    precio_actual = resultado['entrada']
                
                signal = {
                    'symbol': symbol,
                    'type': 'BUY' if resultado['decision'] == 'COMPRA' else 'SELL',
                    'price': precio_actual,
                    'sl': resultado['stop_loss'],
                    'tp': resultado['take_profit'],
                    'strength': resultado['confianza'] / 100.0,
                    'strategy': 'Multi-Timeframe AI',
                    'timeframe': 'MULTI',
                    'reason': resultado['razon'],
                    'timestamp': datetime.now(),
                    'analysis': {
                        'rsi_5min': indicadores_actuales.get('5min', {}).get('rsi_value'),
                        'rsi_15min': indicadores_actuales.get('15min', {}).get('rsi_value'),
                        'rsi_1h': indicadores_actuales.get('1h', {}).get('rsi_value'),
                        'atr': indicadores_actuales.get('15min', {}).get('atr_value'),
                        'adx': indicadores_actuales.get('15min', {}).get('adx_value')
                    }
                }
                
                signals.append(signal)
                
                logger.info(f"[SIGNAL] {signal['type']} {symbol} @ {signal['price']:.2f}")
                logger.info(f"         SL: {signal['sl']:.2f} | TP: {signal['tp']:.2f}")
                logger.info(f"         Razón: {signal['reason']}")
            
            else:
                logger.info(f"No hay señal fuerte para {symbol} (Decisión: {resultado['decision']}, Confianza: {resultado['confianza']}%)")
        
        except Exception as e:
            logger.error(f"Error en análisis multi-timeframe: {e}")
            import traceback
            traceback.print_exc()
        
        return signals

# Función wrapper para compatibilidad con el sistema
def multi_timeframe_strategy_function(df, symbol):
    """
    Wrapper para integración con el sistema actual
    
    Args:
        df: DataFrame con datos
        symbol: Símbolo a analizar
        
    Returns:
        Lista de señales
    """
    # Crear instancia singleton
    if not hasattr(multi_timeframe_strategy_function, 'strategy'):
        multi_timeframe_strategy_function.strategy = MultiTimeframeStrategy()
    
    return multi_timeframe_strategy_function.strategy.generate_signal(df, symbol)

# Para testing directo
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Test de la estrategia
    strategy = MultiTimeframeStrategy()
    
    # Probar con BTCUSDm
    print("Probando estrategia multi-timeframe con BTCUSDm...")
    signals = strategy.generate_signal(None, 'BTCUSDm')
    
    if signals:
        print(f"\n[OK] Señal generada:")
        for signal in signals:
            print(f"  Tipo: {signal['type']}")
            print(f"  Precio: {signal['price']}")
            print(f"  SL: {signal['sl']}")
            print(f"  TP: {signal['tp']}")
            print(f"  Confianza: {signal['strength']*100:.1f}%")
            print(f"  Razón: {signal['reason']}")
    else:
        print("\n[INFO] No hay señales en este momento")