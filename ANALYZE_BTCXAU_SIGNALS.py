"""
ANÁLISIS ESPECÍFICO DE SEÑALES - BTCXAUm y XAUUSD
Análisis detallado usando las funciones existentes del proyecto
"""

import sys
import os
from pathlib import Path
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from src.signals.signal_generator import SignalGenerator

def get_current_price_info(symbol):
    """Obtener información de precio actual de MT5"""
    try:
        if not mt5.initialize():
            return None
            
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return None
            
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return None
            
        return {
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'spread': tick.ask - tick.bid,
            'spread_points': (tick.ask - tick.bid) / symbol_info.point,
            'digits': symbol_info.digits,
            'point': symbol_info.point,
            'contract_size': symbol_info.trade_contract_size,
            'volume_min': symbol_info.volume_min,
            'volume_max': symbol_info.volume_max,
            'timestamp': datetime.now()
        }
    except Exception as e:
        print(f"Error obteniendo precio de {symbol}: {e}")
        return None

def get_mt5_historical_data(symbol, timeframe=mt5.TIMEFRAME_H1, count=100):
    """Obtener datos históricos de MT5"""
    try:
        if not mt5.initialize():
            return None
            
        rates = mt5.copy_rates(symbol, timeframe, count)
        if rates is None:
            print(f"No hay datos para {symbol}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df
    except Exception as e:
        print(f"Error obteniendo datos históricos para {symbol}: {e}")
        return None

def calculate_simple_indicators(df):
    """Calcular indicadores técnicos básicos"""
    if df is None or len(df) < 20:
        return {}
    
    indicators = {}
    
    try:
        close_prices = df['close'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        
        # RSI simple
        def calculate_rsi(prices, period=14):
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        # Moving Averages
        sma_20 = np.mean(close_prices[-20:])
        sma_50 = np.mean(close_prices[-50:]) if len(close_prices) >= 50 else sma_20
        
        # Bollinger Bands simple
        sma_period = 20
        if len(close_prices) >= sma_period:
            bb_middle = np.mean(close_prices[-sma_period:])
            bb_std = np.std(close_prices[-sma_period:])
            bb_upper = bb_middle + (2 * bb_std)
            bb_lower = bb_middle - (2 * bb_std)
            
            current_price = close_prices[-1]
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
        else:
            bb_upper = bb_middle = bb_lower = close_prices[-1]
            bb_position = 0.5
        
        # RSI
        rsi = calculate_rsi(close_prices) if len(close_prices) > 14 else 50
        
        # MACD simple
        ema_12 = close_prices[-12:].mean() if len(close_prices) >= 12 else close_prices[-1]
        ema_26 = close_prices[-26:].mean() if len(close_prices) >= 26 else close_prices[-1]
        macd_line = ema_12 - ema_26
        
        # Momentum
        momentum = close_prices[-1] - close_prices[-10] if len(close_prices) >= 10 else 0
        
        # Volatilidad (ATR simple)
        if len(df) >= 14:
            high_low = high_prices[-14:] - low_prices[-14:]
            atr = np.mean(high_low)
        else:
            atr = high_prices[-1] - low_prices[-1] if len(high_prices) > 0 else 0
        
        indicators = {
            'price': {
                'current': close_prices[-1],
                'previous': close_prices[-2] if len(close_prices) > 1 else close_prices[-1],
                'change': close_prices[-1] - close_prices[-2] if len(close_prices) > 1 else 0,
                'change_pct': (close_prices[-1] / close_prices[-2] - 1) * 100 if len(close_prices) > 1 else 0
            },
            'rsi': {
                'value': rsi,
                'signal': 'BUY' if rsi < 30 else 'SELL' if rsi > 70 else 'NEUTRAL',
                'overbought': rsi > 70,
                'oversold': rsi < 30
            },
            'moving_averages': {
                'sma_20': sma_20,
                'sma_50': sma_50,
                'price_vs_sma20': (close_prices[-1] / sma_20 - 1) * 100,
                'sma_trend': 'BULLISH' if sma_20 > sma_50 else 'BEARISH'
            },
            'bollinger_bands': {
                'upper': bb_upper,
                'middle': bb_middle,
                'lower': bb_lower,
                'position': bb_position,
                'position_pct': bb_position * 100,
                'signal': 'BUY' if bb_position < 0.2 else 'SELL' if bb_position > 0.8 else 'NEUTRAL',
                'squeeze': (bb_upper - bb_lower) / bb_middle < 0.02
            },
            'macd': {
                'value': macd_line,
                'signal': 'BUY' if macd_line > 0 else 'SELL',
                'bullish': macd_line > 0
            },
            'momentum': {
                'value': momentum,
                'signal': 'BUY' if momentum > 0 else 'SELL',
                'positive': momentum > 0
            },
            'volatility': {
                'atr': atr,
                'atr_pct': (atr / close_prices[-1]) * 100,
                'high': atr > np.mean([atr]) * 1.5
            }
        }
        
    except Exception as e:
        print(f"Error calculando indicadores: {e}")
        
    return indicators

def analyze_symbol_signals(symbol):
    """Análizar señales detalladas para un símbolo específico"""
    
    print(f"\n{'='*70}")
    print(f"     ANÁLISIS DETALLADO DE SEÑALES - {symbol}")
    print(f"{'='*70}")
    
    # Obtener información de precio actual
    price_info = get_current_price_info(symbol)
    if not price_info:
        print(f"ERROR: No se pudo obtener informacion de precio para {symbol}")
        return None
    
    print(f"INFORMACION DE PRECIO:")
    print(f"   Precio actual: {price_info['last']:.5f}")
    print(f"   Bid: {price_info['bid']:.5f}")
    print(f"   Ask: {price_info['ask']:.5f}")
    print(f"   Spread: {price_info['spread']:.5f} ({price_info['spread_points']:.1f} puntos)")
    print(f"   Dígitos: {price_info['digits']}")
    
    # Obtener datos históricos
    historical_data = get_mt5_historical_data(symbol, mt5.TIMEFRAME_H1, 100)
    if historical_data is None:
        print(f"ERROR: No se pudieron obtener datos historicos para {symbol}")
        return price_info
    
    print(f"DATOS HISTORICOS:")
    print(f"   Período: {historical_data.index[0]} a {historical_data.index[-1]}")
    print(f"   Velas analizadas: {len(historical_data)}")
    
    # Calcular indicadores
    indicators = calculate_simple_indicators(historical_data)
    if not indicators:
        print(f"ERROR: Error calculando indicadores para {symbol}")
        return price_info
    
    print(f"\nANALISIS DE INDICADORES:")
    print(f"{'='*50}")
    
    # Análisis de precio
    price_data = indicators.get('price', {})
    print(f"PRECIO:")
    print(f"   Actual: {price_data.get('current', 0):.5f}")
    print(f"   Cambio: {price_data.get('change', 0):+.5f} ({price_data.get('change_pct', 0):+.2f}%)")
    
    # Análisis RSI
    rsi_data = indicators.get('rsi', {})
    print(f"\nRSI(14):")
    print(f"   Valor: {rsi_data.get('value', 0):.2f}")
    print(f"   Señal: {rsi_data.get('signal', 'N/A')}")
    print(f"   Sobrecompra: {'SÍ' if rsi_data.get('overbought', False) else 'NO'}")
    print(f"   Sobreventa: {'SÍ' if rsi_data.get('oversold', False) else 'NO'}")
    
    # Análisis Moving Averages
    ma_data = indicators.get('moving_averages', {})
    print(f"\nMEDIAS MOVILES:")
    print(f"   SMA 20: {ma_data.get('sma_20', 0):.5f}")
    print(f"   SMA 50: {ma_data.get('sma_50', 0):.5f}")
    print(f"   Precio vs SMA20: {ma_data.get('price_vs_sma20', 0):+.2f}%")
    print(f"   Tendencia: {ma_data.get('sma_trend', 'N/A')}")
    
    # Análisis Bollinger Bands
    bb_data = indicators.get('bollinger_bands', {})
    print(f"\nBOLLINGER BANDS:")
    print(f"   Superior: {bb_data.get('upper', 0):.5f}")
    print(f"   Media: {bb_data.get('middle', 0):.5f}")
    print(f"   Inferior: {bb_data.get('lower', 0):.5f}")
    print(f"   Posición: {bb_data.get('position_pct', 0):.1f}%")
    print(f"   Señal: {bb_data.get('signal', 'N/A')}")
    print(f"   Squeeze: {'SÍ' if bb_data.get('squeeze', False) else 'NO'}")
    
    # Análisis MACD
    macd_data = indicators.get('macd', {})
    print(f"\nMACD:")
    print(f"   Valor: {macd_data.get('value', 0):.6f}")
    print(f"   Señal: {macd_data.get('signal', 'N/A')}")
    print(f"   Alcista: {'SÍ' if macd_data.get('bullish', False) else 'NO'}")
    
    # Análisis Momentum
    mom_data = indicators.get('momentum', {})
    print(f"\nMOMENTUM:")
    print(f"   Valor: {mom_data.get('value', 0):.6f}")
    print(f"   Señal: {mom_data.get('signal', 'N/A')}")
    print(f"   Positivo: {'SÍ' if mom_data.get('positive', False) else 'NO'}")
    
    # Análisis Volatilidad
    vol_data = indicators.get('volatility', {})
    print(f"\nVOLATILIDAD:")
    print(f"   ATR: {vol_data.get('atr', 0):.6f}")
    print(f"   ATR %: {vol_data.get('atr_pct', 0):.2f}%")
    print(f"   Alta volatilidad: {'SÍ' if vol_data.get('high', False) else 'NO'}")
    
    # Calcular score total
    score = calculate_signal_score(indicators)
    confidence = abs(score)
    signal_type = 'BUY' if score > 0 else 'SELL' if score < 0 else 'NO_OPERAR'
    
    print(f"\nRESULTADO FINAL:")
    print(f"{'='*30}")
    print(f"Score: {score:+d}/100")
    print(f"Confianza: {confidence:.0f}%")
    print(f"Señal: {signal_type}")
    
    # Evaluar calidad de la señal
    if confidence >= 70:
        quality = "EXCELENTE"
    elif confidence >= 60:
        quality = "BUENA"
    elif confidence >= 40:
        quality = "REGULAR"
    else:
        quality = "DÉBIL"
    
    print(f"Calidad: {quality}")
    
    return {
        'symbol': symbol,
        'price_info': price_info,
        'indicators': indicators,
        'score': score,
        'confidence': confidence,
        'signal': signal_type,
        'quality': quality
    }

def calculate_signal_score(indicators):
    """Calcular score de señal basado en indicadores"""
    score = 0
    
    # RSI (peso: 20)
    rsi_data = indicators.get('rsi', {})
    rsi_val = rsi_data.get('value', 50)
    if rsi_val < 30:
        score += 20  # Sobreventa fuerte
    elif rsi_val < 40:
        score += 10  # Sobreventa leve
    elif rsi_val > 70:
        score -= 20  # Sobrecompra fuerte
    elif rsi_val > 60:
        score -= 10  # Sobrecompra leve
    
    # Bollinger Bands (peso: 25)
    bb_data = indicators.get('bollinger_bands', {})
    bb_pos = bb_data.get('position', 0.5)
    if bb_pos < 0.1:
        score += 25  # Muy cerca banda inferior
    elif bb_pos < 0.2:
        score += 20  # Cerca banda inferior
    elif bb_pos > 0.9:
        score -= 25  # Muy cerca banda superior
    elif bb_pos > 0.8:
        score -= 20  # Cerca banda superior
    
    if bb_data.get('squeeze', False):
        score += 10  # Squeeze = probable breakout
    
    # Moving Averages (peso: 20)
    ma_data = indicators.get('moving_averages', {})
    price_vs_sma = ma_data.get('price_vs_sma20', 0)
    if ma_data.get('sma_trend') == 'BULLISH':
        score += 15
    else:
        score -= 15
    
    if price_vs_sma > 2:  # 2% arriba SMA
        score -= 10  # Puede estar caro
    elif price_vs_sma < -2:  # 2% debajo SMA
        score += 10  # Puede estar barato
    
    # MACD (peso: 15)
    macd_data = indicators.get('macd', {})
    if macd_data.get('bullish', False):
        score += 15
    else:
        score -= 15
    
    # Momentum (peso: 15)
    mom_data = indicators.get('momentum', {})
    if mom_data.get('positive', False):
        score += 15
    else:
        score -= 15
    
    # Volatilidad (peso: 5)
    vol_data = indicators.get('volatility', {})
    if vol_data.get('high', False):
        score += 5  # Alta volatilidad = más oportunidades
    
    return max(-100, min(100, score))  # Limitar entre -100 y 100

def main():
    """Función principal"""
    
    print("ANALISIS DETALLADO - BTCXAUm y XAUUSD")
    print("=" * 70)
    
    # Conectar MT5
    if not mt5.initialize():
        print("ERROR: Error conectando MT5")
        return
    
    results = {}
    
    # Analizar BTCXAUm
    btc_result = analyze_symbol_signals('BTCXAUm')
    if btc_result:
        results['BTCXAUm'] = btc_result
    
    # Analizar XAUUSD
    xau_result = analyze_symbol_signals('XAUUSD')
    if xau_result:
        results['XAUUSD'] = xau_result
    
    # Comparar resultados
    if len(results) >= 2:
        print(f"\nCOMPARACION DE SIMBOLOS:")
        print(f"{'='*50}")
        
        for symbol, data in results.items():
            print(f"{symbol:>10}: {data['signal']:>8} | Confianza: {data['confidence']:>3.0f}% | Calidad: {data['quality']}")
        
        # Determinar mejor oportunidad
        best_symbol = max(results.keys(), key=lambda x: results[x]['confidence'])
        print(f"\nMejor oportunidad: {best_symbol}")
        print(f"   Señal: {results[best_symbol]['signal']}")
        print(f"   Confianza: {results[best_symbol]['confidence']:.0f}%")
        print(f"   Calidad: {results[best_symbol]['quality']}")
        
        if results[best_symbol]['confidence'] >= 60:
            print(f"\nRECOMENDACION: Considerar {results[best_symbol]['signal']} en {best_symbol}")
        else:
            print(f"\nRECOMENDACION: Esperar mejor oportunidad (confianza < 60%)")
    
    mt5.shutdown()
    print(f"\nAnalisis completado - {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()