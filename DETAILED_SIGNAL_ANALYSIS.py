"""
ANÁLISIS DETALLADO DE SEÑALES - BTCXAUm y XAUUSD
Análisis profundo de cómo se forman las señales para estos símbolos específicos
"""

import sys
import os
from pathlib import Path
import MetaTrader5 as mt5
import pandas as pd
import talib
from datetime import datetime, timedelta

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.twelve_data_client import TwelveDataClient

def get_mt5_data(symbol: str, timeframe=mt5.TIMEFRAME_H1, count=100):
    """Obtener datos de MT5 si está disponible"""
    try:
        if not mt5.initialize():
            return None
            
        rates = mt5.copy_rates(symbol, timeframe, count)
        if rates is None:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Renombrar columnas para compatibilidad
        df = df.rename(columns={
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        })
        
        return df
    except Exception as e:
        print(f"Error obteniendo datos MT5 para {symbol}: {e}")
        return None

def calculate_detailed_indicators(df):
    """Calcular indicadores técnicos detallados"""
    if df is None or len(df) < 50:
        return {}
    
    indicators = {}
    
    try:
        # RSI
        rsi = talib.RSI(df['close'].values, timeperiod=14)
        indicators['rsi'] = {
            'current': rsi[-1] if len(rsi) > 0 else 0,
            'previous': rsi[-2] if len(rsi) > 1 else 0,
            'signal': 'BUY' if rsi[-1] < 30 else 'SELL' if rsi[-1] > 70 else 'NEUTRAL'
        }
        
        # MACD
        macd, signal, hist = talib.MACD(df['close'].values)
        indicators['macd'] = {
            'macd': macd[-1] if len(macd) > 0 else 0,
            'signal': signal[-1] if len(signal) > 0 else 0,
            'histogram': hist[-1] if len(hist) > 0 else 0,
            'trend': 'BULLISH' if macd[-1] > signal[-1] else 'BEARISH'
        }
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'].values)
        current_price = df['close'].iloc[-1]
        bb_position = (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
        
        indicators['bollinger'] = {
            'upper': bb_upper[-1],
            'middle': bb_middle[-1],
            'lower': bb_lower[-1],
            'position': bb_position,
            'signal': 'BUY' if bb_position < 0.2 else 'SELL' if bb_position > 0.8 else 'NEUTRAL',
            'squeeze': (bb_upper[-1] - bb_lower[-1]) / bb_middle[-1] < 0.02
        }
        
        # Moving Averages
        ema20 = talib.EMA(df['close'].values, timeperiod=20)
        ema50 = talib.EMA(df['close'].values, timeperiod=50)
        sma200 = talib.SMA(df['close'].values, timeperiod=200) if len(df) >= 200 else None
        
        indicators['moving_averages'] = {
            'ema20': ema20[-1] if len(ema20) > 0 else 0,
            'ema50': ema50[-1] if len(ema50) > 0 else 0,
            'sma200': sma200[-1] if sma200 is not None and len(sma200) > 0 else 0,
            'price_vs_ema20': current_price / ema20[-1] - 1 if len(ema20) > 0 else 0,
            'ema_cross': 'GOLDEN' if ema20[-1] > ema50[-1] else 'DEATH'
        }
        
        # Momentum
        momentum = talib.MOM(df['close'].values, timeperiod=10)
        indicators['momentum'] = {
            'current': momentum[-1] if len(momentum) > 0 else 0,
            'signal': 'BUY' if momentum[-1] > 0 else 'SELL'
        }
        
        # Stochastic
        slowk, slowd = talib.STOCH(df['high'].values, df['low'].values, df['close'].values)
        indicators['stochastic'] = {
            'k': slowk[-1] if len(slowk) > 0 else 0,
            'd': slowd[-1] if len(slowd) > 0 else 0,
            'signal': 'BUY' if slowk[-1] < 20 else 'SELL' if slowk[-1] > 80 else 'NEUTRAL'
        }
        
        # ADX (Trend Strength)
        adx = talib.ADX(df['high'].values, df['low'].values, df['close'].values)
        indicators['adx'] = {
            'current': adx[-1] if len(adx) > 0 else 0,
            'strength': 'STRONG' if adx[-1] > 25 else 'WEAK'
        }
        
    except Exception as e:
        print(f"Error calculando indicadores: {e}")
    
    return indicators

def analyze_signal_formation(symbol: str):
    """Analizar en detalle cómo se forma la señal para un símbolo"""
    
    print(f"\n{'='*80}")
    print(f"         ANÁLISIS DETALLADO DE SEÑALES - {symbol}")
    print(f"{'='*80}")
    
    # Obtener datos de MT5
    df = get_mt5_data(symbol)
    if df is None:
        print(f"❌ No se pudieron obtener datos para {symbol}")
        return
    
    print(f"📊 Datos obtenidos: {len(df)} velas (H1)")
    print(f"📅 Período: {df.index[0]} hasta {df.index[-1]}")
    print(f"💰 Precio actual: {df['close'].iloc[-1]:.5f}")
    
    # Calcular indicadores detallados
    indicators = calculate_detailed_indicators(df)
    
    if not indicators:
        print("❌ Error calculando indicadores")
        return
    
    print(f"\n🎯 COMPONENTES DE LA SEÑAL:")
    print(f"{'='*50}")
    
    # Análisis RSI
    rsi_data = indicators.get('rsi', {})
    print(f"📈 RSI(14): {rsi_data.get('current', 0):.2f}")
    print(f"   Señal: {rsi_data.get('signal', 'N/A')}")
    print(f"   Cambio: {rsi_data.get('current', 0) - rsi_data.get('previous', 0):+.2f}")
    
    # Análisis MACD
    macd_data = indicators.get('macd', {})
    print(f"\n📊 MACD:")
    print(f"   MACD: {macd_data.get('macd', 0):.6f}")
    print(f"   Signal: {macd_data.get('signal', 0):.6f}")
    print(f"   Histograma: {macd_data.get('histogram', 0):.6f}")
    print(f"   Tendencia: {macd_data.get('trend', 'N/A')}")
    
    # Análisis Bollinger Bands
    bb_data = indicators.get('bollinger', {})
    print(f"\n🎈 Bollinger Bands:")
    print(f"   Superior: {bb_data.get('upper', 0):.5f}")
    print(f"   Media: {bb_data.get('middle', 0):.5f}")
    print(f"   Inferior: {bb_data.get('lower', 0):.5f}")
    print(f"   Posición: {bb_data.get('position', 0)*100:.1f}%")
    print(f"   Señal: {bb_data.get('signal', 'N/A')}")
    print(f"   Squeeze: {'SÍ' if bb_data.get('squeeze', False) else 'NO'}")
    
    # Análisis Moving Averages
    ma_data = indicators.get('moving_averages', {})
    print(f"\n📈 Medias Móviles:")
    print(f"   EMA20: {ma_data.get('ema20', 0):.5f}")
    print(f"   EMA50: {ma_data.get('ema50', 0):.5f}")
    print(f"   Precio vs EMA20: {ma_data.get('price_vs_ema20', 0)*100:+.2f}%")
    print(f"   Cruce: {ma_data.get('ema_cross', 'N/A')}")
    
    # Análisis Momentum
    mom_data = indicators.get('momentum', {})
    print(f"\n⚡ Momentum:")
    print(f"   Valor: {mom_data.get('current', 0):.6f}")
    print(f"   Señal: {mom_data.get('signal', 'N/A')}")
    
    # Análisis Stochastic
    stoch_data = indicators.get('stochastic', {})
    print(f"\n🔄 Stochastic:")
    print(f"   %K: {stoch_data.get('k', 0):.2f}")
    print(f"   %D: {stoch_data.get('d', 0):.2f}")
    print(f"   Señal: {stoch_data.get('signal', 'N/A')}")
    
    # Análisis ADX
    adx_data = indicators.get('adx', {})
    print(f"\n💪 ADX (Fuerza Tendencia):")
    print(f"   Valor: {adx_data.get('current', 0):.2f}")
    print(f"   Fuerza: {adx_data.get('strength', 'N/A')}")
    
    # Calcular score total
    score = calculate_signal_score(indicators)
    confidence = score / 100 * 100  # Convertir a porcentaje
    
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"{'='*30}")
    print(f"Score total: {score}/100")
    print(f"Confianza: {confidence:.1f}%")
    print(f"Señal: {'BUY' if score > 50 else 'SELL' if score < -50 else 'NO_OPERAR'}")
    
    return indicators, score

def calculate_signal_score(indicators):
    """Calcular score de señal basado en indicadores"""
    score = 0
    
    # RSI (peso: 15)
    rsi_data = indicators.get('rsi', {})
    rsi_val = rsi_data.get('current', 50)
    if rsi_val < 30:
        score += 15  # Sobreventa = BUY
    elif rsi_val > 70:
        score -= 15  # Sobrecompra = SELL
    elif 40 <= rsi_val <= 60:
        score += 5   # Neutral = pequeño positivo
    
    # MACD (peso: 20)
    macd_data = indicators.get('macd', {})
    if macd_data.get('trend') == 'BULLISH':
        score += 20
    else:
        score -= 20
    
    # Bollinger Bands (peso: 25)
    bb_data = indicators.get('bollinger', {})
    bb_pos = bb_data.get('position', 0.5)
    if bb_pos < 0.2:
        score += 25  # Cerca banda inferior = BUY
    elif bb_pos > 0.8:
        score -= 25  # Cerca banda superior = SELL
    
    if bb_data.get('squeeze', False):
        score += 10  # Squeeze añade probabilidad de breakout
    
    # Moving Averages (peso: 20)
    ma_data = indicators.get('moving_averages', {})
    price_vs_ema = ma_data.get('price_vs_ema20', 0)
    if ma_data.get('ema_cross') == 'GOLDEN':
        score += 15
    elif ma_data.get('ema_cross') == 'DEATH':
        score -= 15
    
    if price_vs_ema > 0.01:  # 1% arriba EMA20
        score += 5
    elif price_vs_ema < -0.01:  # 1% debajo EMA20
        score -= 5
    
    # Momentum (peso: 10)
    mom_data = indicators.get('momentum', {})
    if mom_data.get('current', 0) > 0:
        score += 10
    else:
        score -= 10
    
    # Stochastic (peso: 10)
    stoch_data = indicators.get('stochastic', {})
    stoch_k = stoch_data.get('k', 50)
    if stoch_k < 20:
        score += 10
    elif stoch_k > 80:
        score -= 10
    
    return max(-100, min(100, score))  # Limitar entre -100 y 100

def main():
    """Función principal"""
    
    print("🔍 ANÁLISIS DETALLADO DE SEÑALES - BTCXAUm y XAUUSD")
    print("=" * 80)
    
    # Conectar MT5
    if not mt5.initialize():
        print("❌ Error conectando MT5")
        return
    
    # Analizar BTCXAUm
    btc_indicators, btc_score = analyze_signal_formation('BTCXAUm')
    
    # Analizar XAUUSD (si está disponible)
    print("\n" + "="*80)
    xau_indicators, xau_score = analyze_signal_formation('XAUUSD')
    
    # Comparar ambos símbolos
    print(f"\n🔄 COMPARACIÓN DE SÍMBOLOS:")
    print(f"{'='*50}")
    print(f"BTCXAUm - Score: {btc_score}/100 ({btc_score}% confianza)")
    print(f"XAUUSD  - Score: {xau_score}/100 ({xau_score}% confianza)")
    
    mejor = "BTCXAUm" if btc_score > xau_score else "XAUUSD"
    print(f"\n🏆 Mejor oportunidad: {mejor}")
    
    mt5.shutdown()
    
    print(f"\n✅ Análisis completado")

if __name__ == "__main__":
    main()