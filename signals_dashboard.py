"""
Signals Dashboard - Dashboard de Señales y Análisis Técnico
Puerto: 8506
Especializado en mostrar señales técnicas y análisis de mercado
"""
import http.server
import socketserver
import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Cargar variables de entorno
load_dotenv()

class SignalsDashboard:
    def __init__(self, port=8506):
        self.port = port
        self.symbols = {
            'crypto': ['BTC/USD', 'ETH/USD'],
            'forex': ['EUR/USD', 'GBP/USD', 'USD/JPY'],
            'commodities': ['XAU/USD']
        }
        self.twelvedata_api_key = os.getenv('TWELVEDATA_API_KEY')
    
    def get_mt5_data(self, symbol):
        """Obtener datos básicos de MT5"""
        try:
            if not mt5.initialize():
                return None
            
            # Mapear símbolos de TwelveData a MT5
            mt5_symbol = symbol.replace('/', '').replace('BTC', 'BTCUSD').replace('XAU', 'XAUUSD')
            
            tick = mt5.symbol_info_tick(mt5_symbol)
            symbol_info = mt5.symbol_info(mt5_symbol)
            
            if tick and symbol_info:
                return {
                    'symbol': mt5_symbol,
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': tick.ask - tick.bid,
                    'time': datetime.fromtimestamp(tick.time).strftime('%H:%M:%S'),
                    'digits': symbol_info.digits,
                    'available': True
                }
        except Exception:
            pass
        finally:
            mt5.shutdown()
        
        return {'available': False}
    
    def get_twelvedata_signal(self, symbol):
        """Obtener señal de TwelveData API"""
        if not self.twelvedata_api_key:
            return {'status': 'NO_API_KEY'}
        
        try:
            # Obtener RSI
            rsi_response = requests.get(
                f"https://api.twelvedata.com/rsi",
                params={
                    'symbol': symbol,
                    'interval': '15min',
                    'apikey': self.twelvedata_api_key,
                    'outputsize': 1
                },
                timeout=5
            )
            
            # Obtener MACD
            macd_response = requests.get(
                f"https://api.twelvedata.com/macd",
                params={
                    'symbol': symbol,
                    'interval': '15min',
                    'apikey': self.twelvedata_api_key,
                    'outputsize': 1
                },
                timeout=5
            )
            
            # Obtener precio actual
            price_response = requests.get(
                f"https://api.twelvedata.com/time_series",
                params={
                    'symbol': symbol,
                    'interval': '1min',
                    'apikey': self.twelvedata_api_key,
                    'outputsize': 1
                },
                timeout=5
            )
            
            signals = []
            current_price = 0
            
            # Procesar RSI
            if rsi_response.status_code == 200:
                rsi_data = rsi_response.json()
                if 'values' in rsi_data and rsi_data['values']:
                    rsi_value = float(rsi_data['values'][0]['rsi'])
                    
                    if rsi_value < 30:
                        signals.append({
                            'indicator': 'RSI',
                            'signal': 'BUY',
                            'strength': (30 - rsi_value) / 30,
                            'value': rsi_value,
                            'reason': f'RSI sobreventa ({rsi_value:.1f})'
                        })
                    elif rsi_value > 70:
                        signals.append({
                            'indicator': 'RSI',
                            'signal': 'SELL',
                            'strength': (rsi_value - 70) / 30,
                            'value': rsi_value,
                            'reason': f'RSI sobrecompra ({rsi_value:.1f})'
                        })
                    else:
                        signals.append({
                            'indicator': 'RSI',
                            'signal': 'NEUTRAL',
                            'strength': 0,
                            'value': rsi_value,
                            'reason': f'RSI neutral ({rsi_value:.1f})'
                        })
            
            # Procesar MACD
            if macd_response.status_code == 200:
                macd_data = macd_response.json()
                if 'values' in macd_data and macd_data['values']:
                    macd_value = float(macd_data['values'][0]['macd'])
                    macd_signal = float(macd_data['values'][0]['macd_signal'])
                    
                    if macd_value > macd_signal and macd_value > 0:
                        signals.append({
                            'indicator': 'MACD',
                            'signal': 'BUY',
                            'strength': min(abs(macd_value - macd_signal) * 1000, 1.0),
                            'value': macd_value,
                            'reason': 'MACD bullish crossover'
                        })
                    elif macd_value < macd_signal and macd_value < 0:
                        signals.append({
                            'indicator': 'MACD',
                            'signal': 'SELL',
                            'strength': min(abs(macd_value - macd_signal) * 1000, 1.0),
                            'value': macd_value,
                            'reason': 'MACD bearish crossover'
                        })
                    else:
                        signals.append({
                            'indicator': 'MACD',
                            'signal': 'NEUTRAL',
                            'strength': 0,
                            'value': macd_value,
                            'reason': 'MACD neutral'
                        })
            
            # Obtener precio actual
            if price_response.status_code == 200:
                price_data = price_response.json()
                if 'values' in price_data and price_data['values']:
                    current_price = float(price_data['values'][0]['close'])
            
            # Calcular señal consolidada
            consolidated_signal = self.consolidate_signals(signals)
            
            return {
                'status': 'SUCCESS',
                'current_price': current_price,
                'signals': signals,
                'consolidated': consolidated_signal,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def consolidate_signals(self, signals):
        """Consolidar múltiples señales en una recomendación"""
        if not signals:
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reasons': []}
        
        buy_strength = sum(s['strength'] for s in signals if s['signal'] == 'BUY')
        sell_strength = sum(s['strength'] for s in signals if s['signal'] == 'SELL')
        
        total_signals = len(signals)
        max_possible_strength = total_signals
        
        if buy_strength > sell_strength and buy_strength > 0.3:
            confidence = min((buy_strength / max_possible_strength) * 100, 100)
            return {
                'signal': 'BUY',
                'confidence': confidence,
                'reasons': [s['reason'] for s in signals if s['signal'] == 'BUY']
            }
        elif sell_strength > buy_strength and sell_strength > 0.3:
            confidence = min((sell_strength / max_possible_strength) * 100, 100)
            return {
                'signal': 'SELL',
                'confidence': confidence,
                'reasons': [s['reason'] for s in signals if s['signal'] == 'SELL']
            }
        else:
            return {
                'signal': 'NEUTRAL',
                'confidence': 50,
                'reasons': ['Señales mixtas o débiles']
            }
    
    def get_market_analysis(self):
        """Obtener análisis completo del mercado"""
        analysis = {}
        
        for category, symbols in self.symbols.items():
            analysis[category] = {}
            
            for symbol in symbols:
                # Obtener datos de MT5
                mt5_data = self.get_mt5_data(symbol)
                
                # Obtener señales de TwelveData
                signal_data = self.get_twelvedata_signal(symbol)
                
                analysis[category][symbol] = {
                    'mt5': mt5_data,
                    'signals': signal_data
                }
        
        return analysis
    
    def get_system_data(self):
        """Obtener todos los datos del sistema"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_only': datetime.now().strftime('%H:%M:%S'),
            'market_analysis': self.get_market_analysis(),
            'api_status': 'ENABLED' if self.twelvedata_api_key else 'DISABLED'
        }
    
    def generate_html(self, data):
        """Generar HTML del dashboard de señales"""
        
        market_analysis = data['market_analysis']
        api_status = data['api_status']
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="20">
    <title>Signals Dashboard - Análisis Técnico</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
            color: white;
            min-height: 100vh;
            padding: 15px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 25px;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        .api-status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
            margin-left: 10px;
        }}
        
        .api-enabled {{ background: #4CAF50; }}
        .api-disabled {{ background: #f44336; }}
        
        .categories {{
            display: grid;
            gap: 25px;
        }}
        
        .category {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .category-title {{
            font-size: 1.4rem;
            font-weight: bold;
            margin-bottom: 20px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .category-crypto {{ border-left: 4px solid #FF9800; }}
        .category-forex {{ border-left: 4px solid #4CAF50; }}
        .category-commodities {{ border-left: 4px solid #FFD700; }}
        
        .symbols-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .symbol-card {{
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 18px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .symbol-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .symbol-name {{
            font-size: 1.2rem;
            font-weight: bold;
        }}
        
        .symbol-price {{
            font-size: 1.1rem;
            font-weight: bold;
        }}
        
        .mt5-status {{
            font-size: 0.8rem;
            opacity: 0.8;
            margin-bottom: 10px;
        }}
        
        .signal-summary {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
        }}
        
        .signal-buy {{ 
            background: linear-gradient(45deg, #4CAF50, #66BB6A);
            color: white;
        }}
        
        .signal-sell {{ 
            background: linear-gradient(45deg, #f44336, #EF5350);
            color: white;
        }}
        
        .signal-neutral {{ 
            background: linear-gradient(45deg, #FFC107, #FFCA28);
            color: black;
        }}
        
        .confidence {{
            font-size: 0.9rem;
        }}
        
        .indicators-list {{
            display: grid;
            gap: 8px;
        }}
        
        .indicator-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: rgba(255,255,255,0.05);
            border-radius: 6px;
            font-size: 0.9rem;
        }}
        
        .indicator-name {{
            font-weight: bold;
        }}
        
        .indicator-signal {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        
        .ind-buy {{ background: #4CAF50; color: white; }}
        .ind-sell {{ background: #f44336; color: white; }}
        .ind-neutral {{ background: #9E9E9E; color: white; }}
        
        .error-message {{
            background: rgba(244, 67, 54, 0.2);
            border: 1px solid #f44336;
            padding: 12px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 0.9rem;
        }}
        
        .no-api-message {{
            background: rgba(255, 193, 7, 0.2);
            border: 1px solid #FFC107;
            padding: 12px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 0.9rem;
            color: #FFC107;
        }}
        
        .signal-reasons {{
            margin-top: 10px;
            font-size: 0.8rem;
            opacity: 0.9;
        }}
        
        .signal-reasons ul {{
            margin-left: 15px;
        }}
        
        .auto-refresh {{
            position: fixed;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.7);
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 11px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 25px;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
        
        .live-dot {{
            width: 8px;
            height: 8px;
            background: #4CAF50;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
            animation: blink 2s infinite;
        }}
        
        @keyframes blink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0.3; }}
        }}
    </style>
</head>
<body>
    <div class="auto-refresh">
        Signals Live - 20s refresh
    </div>
    
    <div class="header">
        <h1>SIGNALS DASHBOARD</h1>
        <p>Análisis Técnico y Señales de Trading - Puerto 8506</p>
        <p>
            <strong>Tiempo:</strong> {data['time_only']}
            <span class="api-status api-{'enabled' if api_status == 'ENABLED' else 'disabled'}">
                TwelveData API: {api_status}
            </span>
        </p>
    </div>
    
    <div class="categories">"""
        
        # Generar cada categoría
        for category, symbols_data in market_analysis.items():
            category_class = f"category-{category}"
            
            html += f"""
        <div class="category {category_class}">
            <div class="category-title">
                <span>{category.upper()}</span>
                <span class="live-dot"></span>
            </div>
            <div class="symbols-grid">"""
            
            for symbol, data in symbols_data.items():
                mt5_data = data['mt5']
                signals_data = data['signals']
                
                html += f"""
                <div class="symbol-card">
                    <div class="symbol-header">
                        <span class="symbol-name">{symbol}</span>
                        <span class="symbol-price">"""
                
                # Mostrar precio de MT5 o TwelveData
                if mt5_data.get('available'):
                    html += f"{mt5_data['bid']:.{mt5_data['digits']}f} ({mt5_data['time']})"
                elif signals_data.get('status') == 'SUCCESS' and signals_data.get('current_price'):
                    html += f"{signals_data['current_price']:.5f}"
                else:
                    html += "N/A"
                
                html += "</span></div>"
                
                # Estado MT5
                if mt5_data.get('available'):
                    html += f"""
                    <div class="mt5-status">
                        MT5: Disponible | Spread: {mt5_data['spread']:.{mt5_data['digits']}f}
                    </div>"""
                else:
                    html += '<div class="mt5-status">MT5: No disponible</div>'
                
                # Señales
                if signals_data.get('status') == 'SUCCESS':
                    consolidated = signals_data.get('consolidated', {})
                    signal_type = consolidated.get('signal', 'NEUTRAL').lower()
                    confidence = consolidated.get('confidence', 0)
                    
                    html += f"""
                    <div class="signal-summary signal-{signal_type}">
                        <span>SEÑAL: {consolidated.get('signal', 'NEUTRAL')}</span>
                        <span class="confidence">{confidence:.0f}%</span>
                    </div>"""
                    
                    # Indicadores individuales
                    if signals_data.get('signals'):
                        html += '<div class="indicators-list">'
                        
                        for indicator in signals_data['signals']:
                            ind_signal = indicator['signal'].lower()
                            html += f"""
                            <div class="indicator-item">
                                <span class="indicator-name">{indicator['indicator']}</span>
                                <span class="indicator-signal ind-{ind_signal}">{indicator['signal']}</span>
                            </div>"""
                        
                        html += '</div>'
                    
                    # Razones
                    if consolidated.get('reasons'):
                        html += f"""
                        <div class="signal-reasons">
                            <strong>Razones:</strong>
                            <ul>
                                {''.join(f'<li>{reason}</li>' for reason in consolidated['reasons'])}
                            </ul>
                        </div>"""
                
                elif signals_data.get('status') == 'NO_API_KEY':
                    html += '<div class="no-api-message">TwelveData API key no configurada</div>'
                
                elif signals_data.get('status') == 'ERROR':
                    html += f'<div class="error-message">Error: {signals_data.get("error", "Desconocido")}</div>'
                
                else:
                    html += '<div class="error-message">Sin datos de señales</div>'
                
                html += "</div>"
            
            html += "</div></div>"
        
        html += """
    </div>
    
    <div class="footer">
        <p><strong>SIGNALS DASHBOARD</strong> - Puerto 8506</p>
        <p>Análisis técnico con RSI, MACD y señales consolidadas</p>
    </div>
</body>
</html>"""
        
        return html

class SignalsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, dashboard=None, **kwargs):
        self.dashboard = dashboard
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            data = self.dashboard.get_system_data()
            html = self.dashboard.generate_html(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        return

def main():
    dashboard = SignalsDashboard()
    port = 8506
    
    def handler(*args, **kwargs):
        return SignalsHandler(*args, dashboard=dashboard, **kwargs)
    
    print(f"[SIGNALS DASHBOARD] Iniciando en puerto {port}")
    print(f"URL: http://localhost:{port}")
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()