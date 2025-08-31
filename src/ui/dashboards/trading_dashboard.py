"""
Trading Dashboard - Dashboard de Operaciones en Vivo
Puerto: 8504
Especializado en mostrar trading en tiempo real
"""
import http.server
import socketserver
import threading
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5

class TradingDashboard:
    def __init__(self, port=8504):
        self.port = port
        self.symbols = ['BTCUSD', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
    
    def get_market_prices(self):
        """Obtener precios en tiempo real"""
        prices = {}
        
        try:
            if not mt5.initialize():
                return {}
            
            for symbol in self.symbols:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    symbol_info = mt5.symbol_info(symbol)
                    prices[symbol] = {
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'spread': tick.ask - tick.bid,
                        'time': datetime.fromtimestamp(tick.time).strftime('%H:%M:%S'),
                        'digits': symbol_info.digits if symbol_info else 5,
                        'point': symbol_info.point if symbol_info else 0.00001
                    }
        except Exception as e:
            pass
        finally:
            mt5.shutdown()
        
        return prices
    
    def get_trading_data(self):
        """Obtener datos de trading"""
        try:
            if not mt5.initialize():
                return None
            
            account = mt5.account_info()
            positions = mt5.positions_get()
            
            if not account:
                return None
            
            # Calcular estadísticas
            active_positions = len(positions) if positions else 0
            total_profit = sum(pos.profit for pos in positions) if positions else 0
            
            # Posiciones por símbolo
            positions_by_symbol = {}
            buy_positions = 0
            sell_positions = 0
            
            if positions:
                for pos in positions:
                    if pos.symbol not in positions_by_symbol:
                        positions_by_symbol[pos.symbol] = {'count': 0, 'profit': 0, 'volume': 0}
                    
                    positions_by_symbol[pos.symbol]['count'] += 1
                    positions_by_symbol[pos.symbol]['profit'] += pos.profit
                    positions_by_symbol[pos.symbol]['volume'] += pos.volume
                    
                    if pos.type == 0:
                        buy_positions += 1
                    else:
                        sell_positions += 1
            
            # Historial reciente (últimas 2 horas)
            recent_trades = []
            try:
                from_date = datetime.now() - timedelta(hours=2)
                deals = mt5.history_deals_get(from_date, datetime.now())
                
                if deals:
                    for deal in deals[-20:]:  # Últimas 20 operaciones
                        recent_trades.append({
                            'ticket': deal.ticket,
                            'symbol': deal.symbol,
                            'type': 'BUY' if deal.type == 0 else 'SELL',
                            'volume': deal.volume,
                            'price': deal.price,
                            'profit': deal.profit,
                            'time': datetime.fromtimestamp(deal.time).strftime('%H:%M:%S'),
                            'comment': deal.comment
                        })
            except:
                pass
            
            # Margen y exposición
            margin_level = (account.equity / account.margin * 100) if account.margin > 0 else 0
            used_margin_pct = (account.margin / account.equity * 100) if account.equity > 0 else 0
            
            return {
                'account': {
                    'login': account.login,
                    'balance': account.balance,
                    'equity': account.equity,
                    'margin': account.margin,
                    'margin_free': account.margin_free,
                    'profit': account.profit,
                    'margin_level': margin_level,
                    'used_margin_pct': used_margin_pct
                },
                'positions': {
                    'total': active_positions,
                    'buy': buy_positions,
                    'sell': sell_positions,
                    'total_profit': total_profit,
                    'by_symbol': positions_by_symbol
                },
                'recent_trades': recent_trades
            }
            
        except Exception as e:
            return {'error': str(e)}
        finally:
            mt5.shutdown()
    
    def get_system_data(self):
        """Obtener todos los datos del sistema"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_only': datetime.now().strftime('%H:%M:%S'),
            'prices': self.get_market_prices(),
            'trading': self.get_trading_data()
        }
    
    def generate_html(self, data):
        """Generar HTML del dashboard de trading"""
        
        # Determinar estado general
        trading_data = data.get('trading')
        has_error = trading_data is None or 'error' in trading_data
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <title>Trading Dashboard - Live Operations</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 15px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .section {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .section-title {{
            font-size: 1.3rem;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .live-indicator {{
            width: 10px;
            height: 10px;
            background: #4CAF50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .prices-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        
        .price-card {{
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .symbol {{
            font-weight: bold;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }}
        
        .price {{
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .spread {{
            font-size: 0.8rem;
            opacity: 0.8;
        }}
        
        .trading-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.8rem;
            opacity: 0.8;
        }}
        
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        .neutral {{ color: #FFC107; }}
        
        .trades-table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .trades-table th,
        .trades-table td {{
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .trades-table th {{
            background: rgba(255,255,255,0.1);
            font-weight: bold;
            font-size: 0.9rem;
        }}
        
        .trades-table td {{
            font-size: 0.85rem;
        }}
        
        .positions-breakdown {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .position-item {{
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .auto-refresh {{
            position: fixed;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.7);
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 11px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .error-message {{
            background: rgba(244, 67, 54, 0.2);
            border: 1px solid #f44336;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
        
        .full-width {{
            grid-column: 1 / -1;
        }}
    </style>
</head>
<body>
    <div class="auto-refresh">
        <div class="live-indicator"></div>
        Live - 5s refresh
    </div>
    
    <div class="header">
        <h1>TRADING DASHBOARD</h1>
        <p>Live Trading Operations - Puerto 8504</p>
        <p><strong>Tiempo:</strong> {data['time_only']}</p>
    </div>"""
        
        if has_error:
            error_msg = trading_data.get('error', 'Sin conexión MT5') if trading_data else 'Sin datos de trading'
            html += f"""
    <div class="error-message">
        <h3>Estado del Sistema</h3>
        <p>Error: {error_msg}</p>
    </div>"""
        
        # Sección de precios en vivo
        html += f"""
    <div class="main-grid">
        <div class="section">
            <div class="section-title">
                Precios en Vivo
                <div class="live-indicator"></div>
            </div>
            <div class="prices-grid">"""
        
        if data['prices']:
            for symbol, price_data in data['prices'].items():
                html += f"""
                <div class="price-card">
                    <div class="symbol">{symbol}</div>
                    <div class="price">{price_data['bid']:.{price_data['digits']}f}</div>
                    <div class="spread">Spread: {price_data['spread']:.{price_data['digits']}f}</div>
                    <div class="spread">{price_data['time']}</div>
                </div>"""
        else:
            html += "<p>Sin datos de precios</p>"
        
        html += """
            </div>
        </div>"""
        
        # Sección de estadísticas de trading
        if not has_error and trading_data:
            account = trading_data['account']
            positions = trading_data['positions']
            
            html += f"""
        <div class="section">
            <div class="section-title">Estadísticas de Trading</div>
            <div class="trading-stats">
                <div class="stat-card">
                    <div class="stat-number">${account['balance']:,.0f}</div>
                    <div class="stat-label">Balance</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${account['equity']:,.0f}</div>
                    <div class="stat-label">Equity</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number {'positive' if account['profit'] >= 0 else 'negative'}">${account['profit']:.2f}</div>
                    <div class="stat-label">P&L</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{positions['total']}</div>
                    <div class="stat-label">Posiciones</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number {('positive' if account['margin_level'] > 200 else 'neutral' if account['margin_level'] > 100 else 'negative') if account['margin_level'] > 0 else 'neutral'}">{account['margin_level']:.0f}%</div>
                    <div class="stat-label">Nivel Margen</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number {'positive' if positions['total_profit'] >= 0 else 'negative'}">${positions['total_profit']:.2f}</div>
                    <div class="stat-label">P&L Posiciones</div>
                </div>
            </div>
            
            <div class="positions-breakdown">
                <div class="position-item">
                    <span>Posiciones BUY:</span>
                    <span class="positive">{positions['buy']}</span>
                </div>
                <div class="position-item">
                    <span>Posiciones SELL:</span>
                    <span class="negative">{positions['sell']}</span>
                </div>
                <div class="position-item">
                    <span>Margen Usado:</span>
                    <span>${account['margin']:,.2f} ({account['used_margin_pct']:.1f}%)</span>
                </div>
                <div class="position-item">
                    <span>Margen Libre:</span>
                    <span>${account['margin_free']:,.2f}</span>
                </div>
            </div>"""
            
            # Breakdown por símbolo
            if positions['by_symbol']:
                html += """
            <h4 style="margin-top: 20px; margin-bottom: 10px;">Posiciones por Símbolo</h4>
            <div class="positions-breakdown">"""
                
                for symbol, data in positions['by_symbol'].items():
                    html += f"""
                <div class="position-item">
                    <span><strong>{symbol}</strong> ({data['count']} pos, {data['volume']} vol)</span>
                    <span class="{'positive' if data['profit'] >= 0 else 'negative'}">${data['profit']:.2f}</span>
                </div>"""
                
                html += "</div>"
        
        else:
            html += """
        <div class="section">
            <div class="section-title">Estadísticas de Trading</div>
            <p style="text-align: center; opacity: 0.7;">Sin datos de trading disponibles</p>
        </div>"""
        
        html += """
    </div>"""
        
        # Tabla de operaciones recientes
        html += f"""
    <div class="section full-width">
        <div class="section-title">Operaciones Recientes (Últimas 2 horas)</div>"""
        
        if not has_error and trading_data and trading_data['recent_trades']:
            html += f"""
        <table class="trades-table">
            <thead>
                <tr>
                    <th>Hora</th>
                    <th>Ticket</th>
                    <th>Símbolo</th>
                    <th>Tipo</th>
                    <th>Volumen</th>
                    <th>Precio</th>
                    <th>P&L</th>
                    <th>Comentario</th>
                </tr>
            </thead>
            <tbody>"""
            
            for trade in trading_data['recent_trades']:
                html += f"""
                <tr>
                    <td>{trade['time']}</td>
                    <td>#{trade['ticket']}</td>
                    <td>{trade['symbol']}</td>
                    <td class="{'positive' if trade['type'] == 'BUY' else 'negative'}">{trade['type']}</td>
                    <td>{trade['volume']}</td>
                    <td>{trade['price']}</td>
                    <td class="{'positive' if trade['profit'] >= 0 else 'negative'}">${trade['profit']:.2f}</td>
                    <td>{trade['comment'][:20]}{'...' if len(trade['comment']) > 20 else ''}</td>
                </tr>"""
            
            html += """
            </tbody>
        </table>"""
        else:
            html += "<p style='text-align: center; opacity: 0.7; margin: 20px 0;'>No hay operaciones recientes</p>"
        
        html += """
    </div>
    
    <div class="footer">
        <p><strong>TRADING DASHBOARD</strong> - Puerto 8504</p>
        <p>Especializado en operaciones en vivo y precios en tiempo real</p>
    </div>
</body>
</html>"""
        
        return html

class TradingHandler(http.server.SimpleHTTPRequestHandler):
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
    dashboard = TradingDashboard()
    port = 8504
    
    def handler(*args, **kwargs):
        return TradingHandler(*args, dashboard=dashboard, **kwargs)
    
    print(f"[TRADING DASHBOARD] Iniciando en puerto {port}")
    print(f"URL: http://localhost:{port}")
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()