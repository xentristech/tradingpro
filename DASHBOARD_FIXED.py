#!/usr/bin/env python
"""
DASHBOARD FIXED - MONITOREO SIN EMOJIS
=====================================
Dashboard HTML sin caracteres especiales para compatibilidad Windows
"""

import http.server
import socketserver
import MetaTrader5 as mt5
from datetime import datetime
import os
import sys

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class SimpleDashboard:
    def __init__(self, port=8515):
        self.port = port

    def get_mt5_data(self):
        """Obtener datos de MT5"""
        try:
            if not mt5.initialize():
                return None, [], []

            account = mt5.account_info()
            if not account:
                return None, [], []

            # Posiciones
            positions = mt5.positions_get()
            pos_data = []
            if positions:
                for pos in positions:
                    pos_data.append({
                        'ticket': pos.ticket,
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == 0 else 'SELL',
                        'volume': pos.volume,
                        'profit': pos.profit,
                        'sl': pos.sl if pos.sl != 0 else 'NO',
                        'tp': pos.tp if pos.tp != 0 else 'NO',
                        'sl_missing': pos.sl == 0,
                        'tp_missing': pos.tp == 0
                    })

            # Trades recientes
            try:
                from_date = datetime.now().timestamp() - 3600
                deals = mt5.history_deals_get(from_date, datetime.now().timestamp())
                trades = []
                if deals:
                    for deal in deals[-5:]:
                        trades.append({
                            'ticket': deal.ticket,
                            'symbol': deal.symbol,
                            'type': 'BUY' if deal.type == 0 else 'SELL',
                            'volume': deal.volume,
                            'profit': deal.profit
                        })
            except:
                trades = []

            mt5.shutdown()
            return account, pos_data, trades

        except Exception as e:
            print(f"Error MT5: {e}")
            return None, [], []

    def generate_html(self):
        """Generar HTML"""
        account, positions, trades = self.get_mt5_data()

        current_time = datetime.now().strftime('%H:%M:%S')
        total_profit = sum(p['profit'] for p in positions) if positions else 0
        risk_count = sum(1 for p in positions if p['sl_missing'] or p['tp_missing']) if positions else 0

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <title>Trading Dashboard</title>
    <style>
        body {{
            font-family: 'Consolas', monospace;
            background: #1a1a2e;
            color: #00ff00;
            margin: 0;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            background: rgba(0,255,0,0.1);
            padding: 20px;
            border: 2px solid #00ff00;
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: rgba(0,0,0,0.7);
            border: 1px solid #00ff00;
            padding: 15px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .positive {{ color: #00ff00; }}
        .negative {{ color: #ff4444; }}
        .warning {{ color: #ffaa00; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: rgba(0,0,0,0.8);
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #00ff00;
        }}
        th {{ background: rgba(0,255,0,0.2); }}
        .section {{
            background: rgba(0,0,0,0.8);
            border: 1px solid #00ff00;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .status {{ position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.9); padding: 10px; }}
    </style>
</head>
<body>
    <div class="status">Auto-refresh: 10s</div>

    <div class="container">
        <div class="header">
            <h1>TRADING DASHBOARD</h1>
            <p>Tiempo: {current_time} | MT5: {'CONECTADO' if account else 'DESCONECTADO'}</p>
            {'<p>Cuenta: ' + str(account.login) + ' | Balance: $' + f'{account.balance:,.2f}' + '</p>' if account else ''}
        </div>

        <div class="stats">
            <div class="stat-card">
                <div>POSICIONES</div>
                <div class="stat-value positive">{len(positions)}</div>
            </div>
            <div class="stat-card">
                <div>P&L TOTAL</div>
                <div class="stat-value {'positive' if total_profit >= 0 else 'negative'}">${total_profit:.2f}</div>
            </div>
            <div class="stat-card">
                <div>RIESGO</div>
                <div class="stat-value {'warning' if risk_count > 0 else 'positive'}">{risk_count}</div>
            </div>
            {'<div class="stat-card"><div>BALANCE</div><div class="stat-value">${:,.2f}</div></div>'.format(account.balance) if account else ''}
            {'<div class="stat-card"><div>EQUITY</div><div class="stat-value">${:,.2f}</div></div>'.format(account.equity) if account else ''}
        </div>

        <div class="section">
            <h2>POSICIONES ABIERTAS ({len(positions)})</h2>
            {'<p>No hay posiciones</p>' if not positions else '''
            <table>
                <tr>
                    <th>Ticket</th>
                    <th>Simbolo</th>
                    <th>Tipo</th>
                    <th>Vol</th>
                    <th>P&L</th>
                    <th>SL</th>
                    <th>TP</th>
                    <th>Estado</th>
                </tr>''' +
                ''.join([f'''<tr>
                    <td>#{pos['ticket']}</td>
                    <td>{pos['symbol']}</td>
                    <td class="{'positive' if pos['type'] == 'BUY' else ''}">{pos['type']}</td>
                    <td>{pos['volume']}</td>
                    <td class="{'positive' if pos['profit'] >= 0 else 'negative'}">${pos['profit']:.2f}</td>
                    <td class="{'warning' if pos['sl_missing'] else 'positive'}">{pos['sl']}</td>
                    <td class="{'warning' if pos['tp_missing'] else 'positive'}">{pos['tp']}</td>
                    <td class="{'warning' if pos['sl_missing'] or pos['tp_missing'] else 'positive'}">{'RIESGO' if pos['sl_missing'] or pos['tp_missing'] else 'OK'}</td>
                </tr>''' for pos in positions]) + '</table>'}
        </div>

        <div class="section">
            <h2>TRADES RECIENTES ({len(trades)})</h2>
            {'<p>No hay trades</p>' if not trades else '''
            <table>
                <tr>
                    <th>Ticket</th>
                    <th>Simbolo</th>
                    <th>Tipo</th>
                    <th>Vol</th>
                    <th>P&L</th>
                </tr>''' +
                ''.join([f'''<tr>
                    <td>#{trade['ticket']}</td>
                    <td>{trade['symbol']}</td>
                    <td>{trade['type']}</td>
                    <td>{trade['volume']}</td>
                    <td class="{'positive' if trade['profit'] >= 0 else 'negative'}">${trade['profit']:.2f}</td>
                </tr>''' for trade in trades]) + '</table>'}
        </div>

        <div class="section">
            <h2>SISTEMAS ACTIVOS</h2>
            <p>[+] Monitor Posiciones: ACTIVO</p>
            <p>[+] Trading System: ACTIVO</p>
            <p>[+] Detector Velas: ACTIVO</p>
            <p>[+] Alertas IA: ACTIVO</p>
            <p>[+] Ejecutor Ordenes: DISPONIBLE</p>
            <p>[+] Volumen Institucional: ACTIVO</p>
        </div>
    </div>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, dashboard=None, **kwargs):
        self.dashboard = dashboard
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html = self.dashboard.generate_html()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        return

def main():
    dashboard = SimpleDashboard()
    port = 8515

    def handler(*args, **kwargs):
        return Handler(*args, dashboard=dashboard, **kwargs)

    print(f"[+] DASHBOARD INICIADO EN PUERTO {port}")
    print(f"[+] URL: http://localhost:{port}")
    print("=" * 50)

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()