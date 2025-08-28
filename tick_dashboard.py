"""
Tick Dashboard - Dashboard para visualizar datos tick en tiempo real
================================================================

Dashboard web que muestra datos tick de MT5 y TwelveData en tiempo real
"""

import http.server
import socketserver
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from mt5_tick_analyzer import MT5TickAnalyzer

class TickDashboard:
    def __init__(self, port=8508):
        self.port = port
        self.analyzer = MT5TickAnalyzer()
        self.tick_data = {}
        self.is_running = False
        self.update_thread = None
        
    def update_tick_data(self):
        """Actualizar datos tick en background"""
        while self.is_running:
            try:
                # Obtener comparación entre fuentes
                comparison = self.analyzer.compare_sources()
                
                # Obtener análisis de ticks MT5
                mt5_analysis = {}
                if self.analyzer.mt5_connected:
                    for symbol in self.analyzer.symbols_mt5[:5]:
                        analysis = self.analyzer.analyze_mt5_tick_patterns(symbol, 5)
                        if analysis:
                            mt5_analysis[symbol] = analysis
                
                # Guardar datos actualizados
                self.tick_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'comparison': comparison,
                    'mt5_analysis': mt5_analysis,
                    'connections': {
                        'mt5_connected': self.analyzer.mt5_connected,
                        'twelvedata_available': self.analyzer.twelvedata_client is not None
                    }
                }
                
                time.sleep(10)  # Actualizar cada 10 segundos
                
            except Exception as e:
                print(f"Error actualizando tick data: {e}")
                time.sleep(5)
    
    def start_data_updates(self):
        """Iniciar actualizaciones de datos en background"""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=self.update_tick_data, daemon=True)
            self.update_thread.start()
    
    def stop_data_updates(self):
        """Detener actualizaciones"""
        self.is_running = False
    
    def generate_html(self):
        """Generar HTML del dashboard"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Verificar conexiones
        mt5_status = "🟢 CONECTADO" if self.tick_data.get('connections', {}).get('mt5_connected') else "🔴 DESCONECTADO"
        td_status = "🟢 DISPONIBLE" if self.tick_data.get('connections', {}).get('twelvedata_available') else "🔴 NO DISPONIBLE"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Tick Dashboard - Analisis en Tiempo Real</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ 
            font-family: 'Courier New', monospace; 
            margin: 0; 
            background: #1a1a1a; 
            color: #00ff00;
        }}
        .header {{ 
            background: #000; 
            color: #00ff00; 
            padding: 20px; 
            text-align: center; 
            border-bottom: 2px solid #00ff00;
        }}
        .status-bar {{
            background: #333;
            padding: 10px;
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #555;
        }}
        .grid {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            padding: 20px;
        }}
        .panel {{ 
            background: #262626; 
            border: 2px solid #00ff00; 
            border-radius: 5px; 
            padding: 15px;
        }}
        .panel-title {{ 
            color: #ffff00; 
            font-weight: bold; 
            font-size: 1.2em; 
            margin-bottom: 15px;
            text-align: center;
        }}
        .symbol-row {{ 
            display: grid; 
            grid-template-columns: 80px 1fr; 
            gap: 10px; 
            margin-bottom: 15px; 
            padding: 10px; 
            background: #333;
            border-radius: 3px;
        }}
        .symbol {{ 
            color: #ffff00; 
            font-weight: bold;
        }}
        .data {{ 
            font-family: monospace; 
            font-size: 0.9em;
        }}
        .up {{ color: #00ff00; }}
        .down {{ color: #ff0000; }}
        .neutral {{ color: #ffff00; }}
        .warning {{ color: #ff6600; }}
        .error {{ color: #ff0000; }}
        .good {{ color: #00ff00; }}
        
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            font-size: 0.8em;
        }}
        th, td {{ 
            padding: 5px; 
            text-align: right; 
            border: 1px solid #555;
        }}
        th {{ 
            background: #444; 
            color: #ffff00;
        }}
        .full-width {{ 
            grid-column: 1 / -1;
        }}
        
        .tick-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }}
        .stat-box {{
            background: #444;
            padding: 10px;
            border-radius: 3px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 0.8em;
            color: #ccc;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TICK DASHBOARD - ANALISIS EN TIEMPO REAL</h1>
        <div>MT5 + TwelveData | Actualizado: {current_time}</div>
    </div>
    
    <div class="status-bar">
        <div>MetaTrader 5: {mt5_status}</div>
        <div>TwelveData: {td_status}</div>
        <div>Auto-refresh: 10s</div>
    </div>
    
    <div class="grid">
'''
        
        # Panel de comparación de precios
        if self.tick_data.get('comparison'):
            html += '''
        <div class="panel">
            <div class="panel-title">COMPARACION MT5 vs TWELVEDATA</div>
'''
            for symbol, data in self.tick_data['comparison'].items():
                diff_pct = data['price_diff_pct']
                diff_class = "error" if abs(diff_pct) > 0.1 else "warning" if abs(diff_pct) > 0.05 else "good"
                
                html += f'''
            <div class="symbol-row">
                <div class="symbol">{symbol}</div>
                <div class="data">
                    MT5: {data['mt5_bid']:.5f} | {data['mt5_ask']:.5f} (Spr: {data['mt5_spread']:.5f})<br>
                    TD:  {data['td_bid']:.5f} | {data['td_ask']:.5f} (Spr: {data['td_spread']:.5f})<br>
                    <span class="{diff_class}">DIFF: {data['price_difference']:+.5f} ({diff_pct:+.3f}%)</span>
                </div>
            </div>
'''
            html += '</div>'
        
        # Panel de análisis MT5
        if self.tick_data.get('mt5_analysis'):
            html += '''
        <div class="panel">
            <div class="panel-title">ANALISIS TICKS MT5 (5 min)</div>
'''
            for symbol, analysis in self.tick_data['mt5_analysis'].items():
                momentum_class = "up" if analysis['tick_momentum'] > 0 else "down" if analysis['tick_momentum'] < 0 else "neutral"
                bias_class = "up" if analysis['tick_bias'] > 0.1 else "down" if analysis['tick_bias'] < -0.1 else "neutral"
                
                html += f'''
            <div class="symbol-row">
                <div class="symbol">{symbol}</div>
                <div class="data">
                    Precio: {analysis['current_bid']:.5f} - {analysis['current_ask']:.5f}<br>
                    Spread: {analysis['current_spread']:.5f} (Avg: {analysis['avg_spread']:.5f})<br>
                    Ticks: <span class="up">↑{analysis['up_ticks']}</span> 
                           <span class="down">↓{analysis['down_ticks']}</span> 
                           <span class="neutral">→{analysis['flat_ticks']}</span><br>
                    <span class="{momentum_class}">Momentum: {analysis['tick_momentum']:+d}</span> | 
                    <span class="{bias_class}">Bias: {analysis['tick_bias']:+.3f}</span>
                </div>
            </div>
'''
            html += '</div>'
        
        # Panel de estadísticas detalladas
        if self.tick_data.get('mt5_analysis'):
            html += '''
        <div class="panel full-width">
            <div class="panel-title">ESTADISTICAS DETALLADAS TICKS</div>
            <table>
                <tr>
                    <th>Símbolo</th>
                    <th>Total Ticks</th>
                    <th>Rango Precio</th>
                    <th>Volatilidad</th>
                    <th>Spread Min/Max</th>
                    <th>Tick Avg Size</th>
                </tr>
'''
            for symbol, analysis in self.tick_data['mt5_analysis'].items():
                html += f'''
                <tr>
                    <td style="color: #ffff00;">{symbol}</td>
                    <td>{analysis['total_ticks']}</td>
                    <td>{analysis['price_range']:.5f}</td>
                    <td>{analysis['volatility']:.5f}</td>
                    <td>{analysis['min_spread']:.5f} / {analysis['max_spread']:.5f}</td>
                    <td>{analysis['avg_tick_size']:.5f}</td>
                </tr>
'''
            html += '''
            </table>
        </div>
'''
        
        # Si no hay datos
        if not self.tick_data.get('comparison') and not self.tick_data.get('mt5_analysis'):
            html += '''
        <div class="panel full-width">
            <div class="panel-title">INICIALIZANDO...</div>
            <div style="text-align: center; padding: 40px;">
                <div>Conectando a fuentes de datos...</div>
                <div style="margin-top: 10px;">
                    Para usar MT5: Asegúrate de tener MetaTrader 5 instalado y conectado<br>
                    Para usar TwelveData: Verifica tu API key en el archivo .env
                </div>
            </div>
        </div>
'''
        
        html += '''
    </div>
</body>
</html>'''
        
        return html

class TickHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, dashboard=None, **kwargs):
        self.dashboard = dashboard
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            try:
                html = self.dashboard.generate_html()
                
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
        pass  # Suprimir logs

def main():
    try:
        dashboard = TickDashboard(port=8508)
        
        print("TICK DASHBOARD")
        print("="*40)
        print(f"Puerto: {dashboard.port}")
        print(f"URL: http://localhost:{dashboard.port}")
        print("\nCaracterísticas:")
        print("  • Comparación MT5 vs TwelveData")
        print("  • Análisis tick en tiempo real")
        print("  • Spreads y movimientos")
        print("  • Estadísticas de momentum")
        print("  • Auto-refresh cada 10s")
        print("="*40)
        
        # Iniciar actualizaciones de datos
        dashboard.start_data_updates()
        
        def handler(*args, **kwargs):
            return TickHandler(*args, dashboard=dashboard, **kwargs)
        
        print(f"\n[INICIANDO] Tick Dashboard en puerto {dashboard.port}")
        print("Presiona Ctrl+C para detener")
        
        with socketserver.TCPServer(("", dashboard.port), handler) as httpd:
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n[DETENIDO] Dashboard detenido")
        if 'dashboard' in locals():
            dashboard.stop_data_updates()
            dashboard.analyzer.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()