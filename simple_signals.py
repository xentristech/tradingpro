#!/usr/bin/env python3
"""
GENERADOR DE SEÑALES SIMPLE Y EFECTIVO
"""
import requests
import time
from datetime import datetime

# Configuración
API_KEY = '915b2ea02f7d49b986c1ae27d2711c73'
BASE_URL = 'https://api.twelvedata.com'

# Símbolos principales
SYMBOLS = {
    'NAS100': 'NAS100',
    'BTCUSD': 'BTC/USD', 
    'XAUUSD': 'XAU/USD',
    'EURUSD': 'EUR/USD',
    'GBPUSD': 'GBP/USD'
}

def get_quote(symbol):
    """Obtiene precio actual"""
    try:
        url = f"{BASE_URL}/quote"
        params = {'symbol': symbol, 'apikey': API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_rsi(symbol, interval='5min'):
    """Obtiene RSI"""
    try:
        url = f"{BASE_URL}/rsi"
        params = {
            'symbol': symbol,
            'interval': interval,
            'time_period': 14,
            'apikey': API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'values' in data and data['values']:
                return float(data['values'][0]['rsi'])
    except:
        pass
    return None

def get_signal(rsi, price_change):
    """Genera señal basada en RSI y cambio de precio"""
    if rsi is None:
        return "NO DATA", "❓"
    
    score = 50  # Neutral
    
    # RSI Analysis
    if rsi < 30:
        score += 30  # Oversold
    elif rsi > 70:
        score -= 30  # Overbought
    elif 40 <= rsi <= 60:
        score += 0  # Neutral
    
    # Price momentum
    if price_change:
        if price_change > 1:
            score += 10
        elif price_change < -1:
            score -= 10
    
    # Determine signal
    if score >= 70:
        return "STRONG BUY 🚀", "✅"
    elif score >= 60:
        return "BUY 📈", "✅"
    elif score <= 30:
        return "STRONG SELL 📉", "🔴"
    elif score <= 40:
        return "SELL ⬇️", "🔴"
    else:
        return "NEUTRAL ➖", "⚠️"

def analyze_all():
    """Analiza todos los símbolos"""
    print("\n" + "="*60)
    print(f"🚀 SEÑALES DE TRADING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    signals_summary = []
    
    for symbol_key, symbol_value in SYMBOLS.items():
        print(f"\n📊 Analizando {symbol_key}...")
        
        # Get quote
        quote = get_quote(symbol_value)
        if not quote:
            print(f"   ❌ No se pudo obtener datos")
            continue
        
        # Get price info
        price = float(quote.get('close', 0))
        change = float(quote.get('percent_change', 0))
        
        # Get RSI
        rsi = get_rsi(symbol_value)
        
        # Generate signal
        signal, icon = get_signal(rsi, change)
        
        # Print results
        print(f"   💰 Precio: ${price:,.2f}")
        print(f"   📊 Cambio: {change:+.2f}%")
        if rsi:
            print(f"   📈 RSI: {rsi:.1f}")
        print(f"   {icon} SEÑAL: {signal}")
        
        signals_summary.append({
            'symbol': symbol_key,
            'price': price,
            'change': change,
            'rsi': rsi,
            'signal': signal
        })
        
        time.sleep(0.5)  # Rate limiting
    
    # Print summary
    print("\n" + "="*60)
    print("📋 RESUMEN DE SEÑALES")
    print("="*60)
    
    # Classify signals
    strong_buys = [s for s in signals_summary if 'STRONG BUY' in s['signal']]
    buys = [s for s in signals_summary if 'BUY' in s['signal'] and 'STRONG' not in s['signal']]
    sells = [s for s in signals_summary if 'SELL' in s['signal'] and 'STRONG' not in s['signal']]
    strong_sells = [s for s in signals_summary if 'STRONG SELL' in s['signal']]
    
    if strong_buys:
        print("\n🚀 COMPRA FUERTE:")
        for s in strong_buys:
            print(f"   • {s['symbol']}: ${s['price']:,.2f} (RSI: {s['rsi']:.1f if s['rsi'] else 'N/A'})")
    
    if buys:
        print("\n✅ COMPRA:")
        for s in buys:
            print(f"   • {s['symbol']}: ${s['price']:,.2f} (RSI: {s['rsi']:.1f if s['rsi'] else 'N/A'})")
    
    if sells:
        print("\n📉 VENTA:")
        for s in sells:
            print(f"   • {s['symbol']}: ${s['price']:,.2f} (RSI: {s['rsi']:.1f if s['rsi'] else 'N/A'})")
    
    if strong_sells:
        print("\n🔴 VENTA FUERTE:")
        for s in strong_sells:
            print(f"   • {s['symbol']}: ${s['price']:,.2f} (RSI: {s['rsi']:.1f if s['rsi'] else 'N/A'})")
    
    print("\n" + "="*60)
    print("✅ Análisis completado")
    print("="*60)

if __name__ == "__main__":
    try:
        analyze_all()
    except KeyboardInterrupt:
        print("\n\n⛔ Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
