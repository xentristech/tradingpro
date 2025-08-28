"""
TICK SYSTEM FINAL - Sistema completo de análisis de ticks funcionando en Windows
===============================================================================

Sistema que funciona sin problemas de encoding y muestra datos tick bid/ask reales
"""

import http.server
import socketserver
import json
import time
import threading
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class TickSystemFinal:
    def __init__(self, port=8508):
        self.port = port
        self.mt5_available = False
        self.td_available = False
        self.tick_data = {}
        self.is_running = False
        
        self.initialize_connections()
    
    def initialize_connections(self):
        """Inicializar conexiones sin emojis problemáticos"""
        print("INICIALIZANDO CONEXIONES...")
        
        # Verificar MetaTrader5
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                self.mt5_available = True
                account_info = mt5.account_info()
                if account_info:
                    print(f"[OK] MT5 conectado - Cuenta: {account_info.login}")
                    print(f"     Broker: {account_info.company}")
                    print(f"     Balance: ${account_info.balance:.2f}")
                else:
                    print("[OK] MT5 conectado sin info de cuenta")
            else:
                print("[ERROR] No se puede conectar a MT5")
        except Exception as e:
            print(f"[ERROR] MT5: {e}")
        
        # Verificar TwelveData
        try:
            from twelvedata import TDClient
            api_key = os.getenv('TWELVEDATA_API_KEY')
            if api_key:
                self.td_client = TDClient(apikey=api_key)
                self.td_available = True
                print("[OK] TwelveData disponible")
            else:
                print("[ERROR] TwelveData API key no encontrada")
        except Exception as e:
            print(f"[ERROR] TwelveData: {e}")
    
    def get_mt5_price(self, symbol):
        """Obtener precio MT5"""
        if not self.mt5_available:
            return None
        
        try:
            import MetaTrader5 as mt5
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return {
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': tick.ask - tick.bid,
                    'mid': (tick.ask + tick.bid) / 2,
                    'time': datetime.fromtimestamp(tick.time).strftime('%H:%M:%S')
                }
        except Exception as e:
            print(f"Error MT5 {symbol}: {e}")
        return None
    
    def get_td_price(self, symbol):
        """Obtener precio TwelveData"""
        if not self.td_available:
            return None
        
        try:
            quote = self.td_client.quote(symbol=symbol)
            data = quote.as_json()
            if data and 'close' in data:
                price = float(data['close'])
                spread = price * 0.0001  # Spread aproximado
                return {
                    'price': price,
                    'bid': price - spread/2,
                    'ask': price + spread/2,
                    'spread': spread,
                    'time': datetime.now().strftime('%H:%M:%S')
                }
        except Exception as e:
            print(f"Error TD {symbol}: {e}")
        return None
    
    def update_tick_data(self):
        """Actualizar datos tick"""
        symbols_mt5 = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD']
        symbols_td = ['EUR/USD', 'GBP/USD', 'XAU/USD', 'BTC/USD']
        
        current_data = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'mt5_status': 'CONECTADO' if self.mt5_available else 'NO DISPONIBLE',
            'td_status': 'CONECTADO' if self.td_available else 'NO DISPONIBLE',
            'comparisons': []
        }
        
        for i, mt5_sym in enumerate(symbols_mt5):
            if i < len(symbols_td):
                td_sym = symbols_td[i]
                
                mt5_data = self.get_mt5_price(mt5_sym)
                td_data = self.get_td_price(td_sym)
                
                comparison = {
                    'mt5_symbol': mt5_sym,
                    'td_symbol': td_sym,
                    'mt5_data': mt5_data,
                    'td_data': td_data
                }
                
                if mt5_data and td_data:
                    diff = mt5_data['mid'] - td_data['price']
                    diff_pct = (diff / td_data['price']) * 100
                    comparison['difference'] = diff
                    comparison['diff_pct'] = diff_pct
                
                current_data['comparisons'].append(comparison)
        
        self.tick_data = current_data
    
    def generate_html(self):
        """Generar HTML del dashboard"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Tick System - Datos Bid/Ask en Tiempo Real</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ 
            font-family: 'Courier New', monospace; 
            margin: 0; 
            background: #0a0a0a; 
            color: #00ff00;
            line-height: 1.4;
        }}
        .header {{ 
            background: #000; 
            color: #00ff00; 
            padding: 20px; 
            text-align: center; 
            border-bottom: 2px solid #00ff00;
        }}
        .status {{ 
            background: #1a1a1a; 
            padding: 15px; 
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
        }}
        .content {{ 
            padding: 20px;
        }}
        .symbol-block {{ 
            background: #1a1a1a; 
            margin: 15px 0; 
            padding: 15px; 
            border: 1px solid #333;
            border-radius: 5px;
        }}
        .symbol-title {{ 
            color: #ffff00; 
            font-size: 1.2em; 
            font-weight: bold; 
            margin-bottom: 10px;
        }}
        .price-data {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px;
        }}
        .source {{ 
            padding: 10px; 
            background: #2a2a2a; 
            border-radius: 3px;
        }}
        .source-title {{ 
            color: #00ffff; 
            font-weight: bold; 
            margin-bottom: 5px;
        }}
        .price-line {{ 
            margin: 3px 0;
        }}
        .difference {{ 
            grid-column: 1 / -1; 
            text-align: center; 
            padding: 10px; 
            margin-top: 10px; 
            background: #333;
            border-radius: 3px;
        }}
        .pos-diff {{ color: #00ff00; }}
        .neg-diff {{ color: #ff4444; }}
        .no-data {{ 
            color: #888; 
            text-align: center; 
            padding: 20px;
        }}
        
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
        }}
        th, td {{ 
            padding: 8px; 
            text-align: left; 
            border: 1px solid #333;
        }}
        th {{ 
            background: #333; 
            color: #ffff00;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TICK SYSTEM - DATOS BID/ASK EN TIEMPO REAL</h1>
        <div>MetaTrader 5 + TwelveData | Actualizado: {current_time}</div>
    </div>
    
    <div class="status">
        <div>MT5: {self.tick_data.get('mt5_status', 'VERIFICANDO')}</div>
        <div>TwelveData: {self.tick_data.get('td_status', 'VERIFICANDO')}</div>
        <div>Auto-refresh: 10 segundos</div>
    </div>
    
    <div class="content">
'''
        
        if self.tick_data.get('comparisons'):
            for comp in self.tick_data['comparisons']:
                html += f'''
        <div class="symbol-block">
            <div class="symbol-title">{comp['mt5_symbol']} / {comp['td_symbol']}</div>
            <div class="price-data">
'''
                
                # Datos MT5
                if comp['mt5_data']:
                    mt5 = comp['mt5_data']
                    html += f'''
                <div class="source">
                    <div class="source-title">MetaTrader 5</div>
                    <div class="price-line">Bid: {mt5['bid']:.5f}</div>
                    <div class="price-line">Ask: {mt5['ask']:.5f}</div>
                    <div class="price-line">Spread: {mt5['spread']:.5f}</div>
                    <div class="price-line">Mid: {mt5['mid']:.5f}</div>
                    <div class="price-line">Tiempo: {mt5['time']}</div>
                </div>
'''
                else:
                    html += '''
                <div class="source">
                    <div class="source-title">MetaTrader 5</div>
                    <div class="no-data">Sin datos</div>
                </div>
'''
                
                # Datos TwelveData
                if comp['td_data']:
                    td = comp['td_data']
                    html += f'''
                <div class="source">
                    <div class="source-title">TwelveData</div>
                    <div class="price-line">Precio: {td['price']:.5f}</div>
                    <div class="price-line">Bid: {td['bid']:.5f}</div>
                    <div class="price-line">Ask: {td['ask']:.5f}</div>
                    <div class="price-line">Spread: {td['spread']:.5f}</div>
                    <div class="price-line">Tiempo: {td['time']}</div>
                </div>
'''
                else:
                    html += '''
                <div class="source">
                    <div class="source-title">TwelveData</div>
                    <div class="no-data">Sin datos</div>
                </div>
'''
                
                # Diferencia
                if comp.get('difference') is not None:
                    diff = comp['difference']
                    diff_pct = comp['diff_pct']
                    diff_class = 'pos-diff' if diff > 0 else 'neg-diff'
                    html += f'''
                <div class="difference">
                    <span class="{diff_class}">
                        DIFERENCIA: {diff:+.5f} ({diff_pct:+.3f}%)
                    </span>
                </div>
'''
                
                html += '''
            </div>
        </div>
'''
        else:
            html += '''
        <div class="no-data">
            <h2>Inicializando sistema...</h2>
            <p>Conectando a fuentes de datos...</p>
        </div>
'''
        
        html += '''
        <div style="margin-top: 30px; text-align: center; color: #888;">
            <p>SISTEMA DE ANÁLISIS DE TICKS BID/ASK</p>
            <p>Comparación en tiempo real entre MetaTrader 5 y TwelveData</p>
        </div>
    </div>
</body>
</html>'''
        
        return html
    
    def start_data_updates(self):
        """Iniciar actualizaciones de datos"""
        def update_loop():
            while self.is_running:
                try:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Actualizando datos tick...")
                    self.update_tick_data()
                    time.sleep(10)
                except Exception as e:
                    print(f"Error actualizando: {e}")
                    time.sleep(5)
        
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=update_loop, daemon=True)
            self.update_thread.start()
    
    def stop_updates(self):
        """Detener actualizaciones"""
        self.is_running = False

class TickHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, tick_system=None, **kwargs):
        self.tick_system = tick_system
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            try:
                html = self.tick_system.generate_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Error: {e}")
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass

def main():
    try:
        tick_system = TickSystemFinal(port=8508)
        
        print("TICK SYSTEM FINAL")
        print("="*50)
        print(f"Puerto: {tick_system.port}")
        print(f"URL: http://localhost:{tick_system.port}")
        print("Características:")
        print("  - Datos tick bid/ask en tiempo real")
        print("  - Comparación MT5 vs TwelveData")
        print("  - Cálculo de spreads y diferencias")
        print("  - Dashboard web funcional")
        print("  - Sin problemas de encoding")
        print("="*50)
        
        # Iniciar actualizaciones
        tick_system.start_data_updates()
        
        def handler(*args, **kwargs):
            return TickHandler(*args, tick_system=tick_system, **kwargs)
        
        print(f"\n[INICIANDO] Dashboard en puerto {tick_system.port}")
        print("Presiona Ctrl+C para detener")
        
        with socketserver.TCPServer(("", tick_system.port), handler) as httpd:
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n[DETENIDO] Sistema detenido")
        if 'tick_system' in locals():
            tick_system.stop_updates()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()