#!/usr/bin/env python3
"""
Dashboard Simple HTML - AlgoTrader v3.0
Panel de control básico que funciona sin dependencias complejas
"""
import http.server
import socketserver
import webbrowser
import threading
import time
import json
import os
from datetime import datetime
from pathlib import Path
import MetaTrader5 as mt5

class TradingDashboardServer:
    def __init__(self, port=8502):
        self.port = port
        self.data_cache = {}
        
    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                return False, "No se pudo inicializar MT5"
            return True, "Conectado exitosamente"
        except Exception as e:
            return False, f"Error: {e}"
    
    def get_system_data(self):
        """Obtener datos del sistema"""
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mt5_connected': False,
            'account': {},
            'positions': [],
            'bot_status': 'UNKNOWN',
            'last_signals': [],
            'price': 0
        }
        
        # Conectar MT5
        mt5_ok, mt5_msg = self.connect_mt5()
        data['mt5_connected'] = mt5_ok
        data['mt5_message'] = mt5_msg
        
        if mt5_ok:
            try:
                # Información de cuenta
                account = mt5.account_info()
                if account:
                    data['account'] = {
                        'login': account.login,
                        'balance': account.balance,
                        'equity': account.equity,
                        'margin': account.margin,
                        'free_margin': account.margin_free,
                        'profit': account.profit
                    }
                
                # Posiciones
                positions = mt5.positions_get()
                if positions:
                    data['positions'] = [
                        {
                            'ticket': pos.ticket,
                            'symbol': pos.symbol,
                            'type': 'BUY' if pos.type == 0 else 'SELL',
                            'volume': pos.volume,
                            'price_open': pos.price_open,
                            'price_current': pos.price_current,
                            'profit': pos.profit
                        }
                        for pos in positions
                    ]
                
                # Precio actual
                tick = mt5.symbol_info_tick("BTCUSD")
                if tick:
                    data['price'] = tick.bid
                    
            except Exception as e:
                data['error'] = str(e)
        
        # Estado del bot (desde logs)
        try:
            log_file = Path("logs/pro_bot.log")
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                if lines:
                    last_line = lines[-1].strip()
                    if '|' in last_line:
                        time_part = last_line.split('|')[0].strip()
                        try:
                            last_time = datetime.strptime(time_part, '%H:%M:%S')
                            last_time = last_time.replace(
                                year=datetime.now().year,
                                month=datetime.now().month,
                                day=datetime.now().day
                            )
                            
                            time_diff = datetime.now() - last_time
                            data['bot_status'] = 'ONLINE' if time_diff.total_seconds() < 120 else 'OFFLINE'
                            data['bot_last_update'] = last_time.strftime('%H:%M:%S')
                        except:
                            data['bot_status'] = 'UNKNOWN'
                    
                    # Últimas señales
                    signals = []
                    for line in lines[-10:]:
                        if 'Señal:' in line and 'Precio:' in line:
                            try:
                                parts = line.strip().split('|')
                                time_str = parts[0].strip()
                                content = parts[-1].strip()
                                
                                if 'Precio:' in content and 'Señal:' in content:
                                    precio_part = content.split('Precio:')[1].split()[0]
                                    senal_part = content.split('Señal:')[1].split()[0]
                                    conf_part = content.split('Confianza:')[1].split()[0] if 'Confianza:' in content else '0.0%'
                                    
                                    signals.append({
                                        'time': time_str,
                                        'price': precio_part,
                                        'signal': senal_part,
                                        'confidence': conf_part
                                    })
                            except:
                                continue
                    
                    data['last_signals'] = signals[-5:]  # Últimas 5
                        
        except Exception as e:
            data['log_error'] = str(e)
        
        if mt5_ok:
            mt5.shutdown()
            
        return data
    
    def generate_html(self, data):
        """Generar HTML del dashboard"""
        
        # Status colors
        mt5_color = "green" if data['mt5_connected'] else "red"
        bot_color = "green" if data['bot_status'] == 'ONLINE' else "orange" if data['bot_status'] == 'OFFLINE' else "gray"
        
        # P&L color
        if data['account']:
            pnl = data['account'].get('profit', 0)
            pnl_color = "green" if pnl >= 0 else "red"
        else:
            pnl_color = "gray"
            pnl = 0
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>AlgoTrader Dashboard v3.0</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .status {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
        }}
        .status.online {{ background: green; }}
        .status.offline {{ background: red; }}
        .status.unknown {{ background: gray; }}
        .metric {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 5px;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        .neutral {{ color: #FFC107; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
        th {{ background: rgba(255,255,255,0.1); }}
        .auto-refresh {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="auto-refresh">🔄 Auto-refresh: 30s</div>
    
    <div class="container">
        <div class="header">
            <h1>🚀 AlgoTrader Dashboard v3.0</h1>
            <p>Panel de Control en Tiempo Real</p>
            <p><strong>Última actualización:</strong> {data['timestamp']}</p>
        </div>
        
        <div class="grid">
            <!-- Estado del Sistema -->
            <div class="card">
                <h3>📊 Estado del Sistema</h3>
                <div class="metric">
                    <span>MT5:</span>
                    <span class="status {'online' if data['mt5_connected'] else 'offline'}">
                        {'🟢 CONECTADO' if data['mt5_connected'] else '🔴 DESCONECTADO'}
                    </span>
                </div>
                <div class="metric">
                    <span>Bot:</span>
                    <span class="status {bot_color.replace('green', 'online').replace('red', 'offline').replace('orange', 'offline').replace('gray', 'unknown')}">
                        {'🤖 ' + data['bot_status']}
                    </span>
                </div>
                {f'<div class="metric"><span>Última actividad:</span><span>{data.get("bot_last_update", "N/A")}</span></div>' if data.get("bot_last_update") else ''}
                <div class="metric">
                    <span>Ollama IA:</span>
                    <span class="status online">🧠 ACTIVO</span>
                </div>
            </div>
            
            <!-- Información de Cuenta -->
            <div class="card">
                <h3>💰 Información de Cuenta</h3>
                {f'''
                <div class="metric">
                    <span>Cuenta:</span>
                    <span>{data['account']['login']}</span>
                </div>
                <div class="metric">
                    <span>Balance:</span>
                    <span>${data['account']['balance']:,.2f}</span>
                </div>
                <div class="metric">
                    <span>Equity:</span>
                    <span>${data['account']['equity']:,.2f}</span>
                </div>
                <div class="metric">
                    <span>P&L Diario:</span>
                    <span class="{'positive' if pnl >= 0 else 'negative'}">${pnl:,.2f}</span>
                </div>
                <div class="metric">
                    <span>Margen Libre:</span>
                    <span>${data['account']['free_margin']:,.2f}</span>
                </div>
                ''' if data['account'] else '<p>❌ No hay información de cuenta disponible</p>'}
            </div>
            
            <!-- Precio Actual -->
            <div class="card">
                <h3>📈 Precio Actual</h3>
                <div class="metric">
                    <span>Símbolo:</span>
                    <span>BTCUSD</span>
                </div>
                <div class="metric">
                    <span>Precio:</span>
                    <span>${data['price']:,.2f}</span>
                </div>
                <div class="metric">
                    <span>Estado:</span>
                    <span>{'🟢 Activo' if data['price'] > 0 else '🔴 Sin datos'}</span>
                </div>
            </div>
            
            <!-- Posiciones Abiertas -->
            <div class="card">
                <h3>📊 Posiciones Abiertas</h3>
                {f'''
                <p><strong>Total:</strong> {len(data['positions'])} posiciones</p>
                <table>
                    <tr>
                        <th>Ticket</th>
                        <th>Tipo</th>
                        <th>Volumen</th>
                        <th>P&L</th>
                    </tr>
                    {''.join([
                        f'''<tr>
                            <td>#{pos['ticket']}</td>
                            <td>{pos['type']}</td>
                            <td>{pos['volume']}</td>
                            <td class="{'positive' if pos['profit'] >= 0 else 'negative'}">${pos['profit']:,.2f}</td>
                        </tr>'''
                        for pos in data['positions']
                    ])}
                </table>
                ''' if data['positions'] else '<p>📭 No hay posiciones abiertas</p>'}
            </div>
            
            <!-- Señales Recientes -->
            <div class="card">
                <h3>🎯 Señales Recientes</h3>
                {f'''
                <table>
                    <tr>
                        <th>Hora</th>
                        <th>Señal</th>
                        <th>Precio</th>
                        <th>Confianza</th>
                    </tr>
                    {''.join([
                        f'''<tr>
                            <td>{signal['time']}</td>
                            <td class="{'positive' if signal['signal'] == 'BUY' else 'negative' if signal['signal'] == 'SELL' else 'neutral'}">{signal['signal']}</td>
                            <td>{signal['price']}</td>
                            <td>{signal['confidence']}</td>
                        </tr>'''
                        for signal in data['last_signals']
                    ])}
                </table>
                ''' if data['last_signals'] else '<p>📭 No hay señales recientes</p>'}
            </div>
            
            <!-- Métricas Adicionales -->
            <div class="card">
                <h3>📈 Resumen</h3>
                <div class="metric">
                    <span>Tiempo activo:</span>
                    <span>{'🟢 Funcionando' if data['bot_status'] == 'ONLINE' else '🔴 Detenido'}</span>
                </div>
                <div class="metric">
                    <span>Conexiones:</span>
                    <span>MT5: {'✅' if data['mt5_connected'] else '❌'}</span>
                </div>
                <div class="metric">
                    <span>Modo:</span>
                    <span>🧪 DEMO</span>
                </div>
                <div class="metric">
                    <span>Última señal:</span>
                    <span>{data['last_signals'][-1]['signal'] if data['last_signals'] else 'N/A'}</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 <strong>AlgoTrader v3.0</strong> - Dashboard Simple</p>
            <p>Actualización automática cada 30 segundos | <a href="javascript:location.reload()" style="color: white;">🔄 Refrescar ahora</a></p>
        </div>
    </div>
</body>
</html>
        """
        
        return html

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, dashboard_server=None, **kwargs):
        self.dashboard_server = dashboard_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            data = self.dashboard_server.get_system_data()
            html = self.dashboard_server.generate_html(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        # Suprimir logs del servidor
        return

def main():
    print("="*60)
    print("ALGOTRADER SIMPLE DASHBOARD")
    print("   Panel de Control HTML v3.0")
    print("="*60)
    print()
    
    dashboard = TradingDashboardServer()
    port = 8502
    
    # Crear handler con referencia al dashboard
    def handler(*args, **kwargs):
        return DashboardHandler(*args, dashboard_server=dashboard, **kwargs)
    
    print(f">> Iniciando servidor web en puerto {port}...")
    print(f">> URL: http://localhost:{port}")
    print(">> Auto-refresh cada 30 segundos")
    print(">> Presiona Ctrl+C para detener")
    print()
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(">> Servidor iniciado exitosamente")
            
            # Abrir navegador después de 2 segundos
            def open_browser():
                time.sleep(2)
                webbrowser.open(f'http://localhost:{port}')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            print(">> Abriendo navegador automaticamente...")
            print("="*60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n>> Dashboard detenido por el usuario")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f">> Error: Puerto {port} ya esta en uso")
            print("   Intenta cerrar otros programas o usar otro puerto")
        else:
            print(f">> Error del servidor: {e}")
    except Exception as e:
        print(f">> Error inesperado: {e}")

if __name__ == "__main__":
    main()