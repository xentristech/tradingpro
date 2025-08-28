"""
Monitoring Dashboard - Dashboard de Monitoreo de Cuentas
Puerto: 8503
Especializado en monitorear múltiples cuentas MT5
"""
import http.server
import socketserver
import threading
import time
import json
import os
from datetime import datetime
from pathlib import Path
import MetaTrader5 as mt5

class MonitoringDashboard:
    def __init__(self, port=8503):
        self.port = port
        self.accounts_config = {
            'ava_real': {
                'login': 89390972,
                'server': 'Ava-Real 1-MT5',
                'name': 'AVA TRADE',
                'type': 'REAL',
                'monitor_only': True
            },
            'exness_trial': {
                'login': 197678662,
                'server': 'Exness-MT5Trial11',
                'name': 'EXNESS',
                'type': 'TRIAL',
                'monitor_only': False
            }
        }
    
    def get_account_data(self, account_config):
        """Obtener datos de una cuenta específica"""
        try:
            # Intentar conectar específicamente a la cuenta solicitada
            try:
                # Obtener credenciales según la cuenta
                if account_config['login'] == 89390972:
                    # AVA Trade
                    path = os.getenv('MT5_PATH_AVA', r"C:\Program Files\AVA TRADE LTD\MetaTrader 5\terminal64.exe")
                    password = os.getenv('MT5_PASSWORD_AVA', '')
                else:
                    # Exness
                    path = os.getenv('MT5_PATH_EXNESS', r"C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\terminal64.exe")  
                    password = os.getenv('MT5_PASSWORD_EXNESS', '')
                
                # Inicializar con la cuenta específica
                if not mt5.initialize(path):
                    # Si falla, intentar inicializar sin path específico
                    if not mt5.initialize():
                        return {'status': 'MT5_ERROR', 'error': 'No se pudo inicializar MT5'}
                
                # Intentar login a la cuenta específica
                if password:
                    login_result = mt5.login(account_config['login'], password, account_config['server'])
                    if not login_result:
                        return {'status': 'LOGIN_ERROR', 'error': f'No se pudo hacer login a {account_config["login"]}'}
                
            except Exception as login_error:
                # Si hay error de login, continuar para obtener info de la cuenta actual
                pass
            
            # Obtener información actual
            account = mt5.account_info()
            if not account:
                return {'status': 'NO_ACCOUNT', 'error': 'Sin información de cuenta'}
            
            # Si la cuenta no coincide, reportar pero obtener datos disponibles
            if account.login != account_config['login']:
                return {
                    'status': 'DIFFERENT_ACCOUNT',
                    'expected': account_config['login'],
                    'actual': account.login,
                    'name': account_config['name'],
                    'current_account_data': {
                        'login': account.login,
                        'server': account.server,
                        'company': account.company,
                        'balance': account.balance,
                        'equity': account.equity,
                        'currency': account.currency
                    }
                }
            
            # Obtener posiciones
            positions = mt5.positions_get()
            positions_data = []
            total_profit = 0
            risk_positions = 0
            
            if positions:
                for pos in positions:
                    sl_missing = pos.sl == 0
                    tp_missing = pos.tp == 0
                    
                    if sl_missing or tp_missing:
                        risk_positions += 1
                    
                    positions_data.append({
                        'ticket': pos.ticket,
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == 0 else 'SELL',
                        'volume': pos.volume,
                        'open_price': pos.price_open,
                        'current_price': pos.price_current,
                        'sl': pos.sl if pos.sl != 0 else None,
                        'tp': pos.tp if pos.tp != 0 else None,
                        'profit': pos.profit,
                        'sl_missing': sl_missing,
                        'tp_missing': tp_missing,
                        'time': datetime.fromtimestamp(pos.time).strftime('%Y-%m-%d %H:%M:%S')
                    })
                    total_profit += pos.profit
            
            # Obtener historial reciente
            history_data = []
            try:
                from_date = datetime.now().timestamp() - 86400  # Últimas 24 horas
                deals = mt5.history_deals_get(from_date, datetime.now().timestamp())
                
                if deals:
                    for deal in deals[-10:]:  # Últimas 10 operaciones
                        history_data.append({
                            'ticket': deal.ticket,
                            'symbol': deal.symbol,
                            'type': 'BUY' if deal.type == 0 else 'SELL',
                            'volume': deal.volume,
                            'price': deal.price,
                            'profit': deal.profit,
                            'time': datetime.fromtimestamp(deal.time).strftime('%Y-%m-%d %H:%M:%S')
                        })
            except:
                pass
            
            return {
                'status': 'CONNECTED',
                'account': {
                    'login': account.login,
                    'name': account_config['name'],
                    'server': account.server,
                    'company': account.company,
                    'balance': account.balance,
                    'equity': account.equity,
                    'margin': account.margin,
                    'margin_free': account.margin_free,
                    'profit': account.profit,
                    'leverage': account.leverage,
                    'currency': account.currency
                },
                'positions': positions_data,
                'total_positions': len(positions_data),
                'total_profit': total_profit,
                'risk_positions': risk_positions,
                'history': history_data,
                'type': account_config['type'],
                'monitor_only': account_config['monitor_only']
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
        finally:
            mt5.shutdown()
    
    def get_system_data(self):
        """Obtener datos de todas las cuentas"""
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'accounts': {},
            'summary': {
                'total_accounts': len(self.accounts_config),
                'connected_accounts': 0,
                'total_positions': 0,
                'total_profit': 0,
                'total_risk_positions': 0
            }
        }
        
        for account_key, account_config in self.accounts_config.items():
            account_data = self.get_account_data(account_config)
            data['accounts'][account_key] = account_data
            
            if account_data['status'] == 'CONNECTED':
                data['summary']['connected_accounts'] += 1
                data['summary']['total_positions'] += account_data['total_positions']
                data['summary']['total_profit'] += account_data['total_profit']
                data['summary']['total_risk_positions'] += account_data['risk_positions']
        
        return data
    
    def generate_html(self, data):
        """Generar HTML del dashboard de monitoreo"""
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="15">
    <title>Monitoring Dashboard - Multi Account</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: rgba(255,255,255,0.15);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .summary-number {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .accounts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
        }}
        
        .account-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .account-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
        
        .account-title {{
            font-size: 1.5rem;
            font-weight: bold;
        }}
        
        .status-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        
        .status-connected {{ background: #4CAF50; }}
        .status-error {{ background: #f44336; }}
        .status-wrong {{ background: #FF9800; }}
        .status-different {{ background: #9C27B0; }}
        .status-login {{ background: #FF5722; }}
        
        .account-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .info-item {{
            background: rgba(255,255,255,0.05);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .info-label {{
            font-size: 0.8rem;
            opacity: 0.8;
            margin-bottom: 5px;
        }}
        
        .info-value {{
            font-weight: bold;
        }}
        
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        .warning {{ color: #FF9800; }}
        
        .positions-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .positions-table th,
        .positions-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .positions-table th {{
            background: rgba(255,255,255,0.1);
            font-weight: bold;
        }}
        
        .risk-indicator {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }}
        
        .risk-high {{ background: #f44336; }}
        .risk-medium {{ background: #FF9800; }}
        .risk-low {{ background: #4CAF50; }}
        
        .auto-refresh {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            opacity: 0.7;
            font-size: 0.9rem;
        }}
        
        .monitor-badge {{
            background: #2196F3;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="auto-refresh">Auto-refresh: 15s</div>
    
    <div class="header">
        <h1>MONITORING DASHBOARD</h1>
        <p>Multi-Account MT5 Monitor - Puerto 8503</p>
        <p><strong>Última actualización:</strong> {data['timestamp']}</p>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <div class="summary-number">{data['summary']['total_accounts']}</div>
            <div>Cuentas Configuradas</div>
        </div>
        <div class="summary-card">
            <div class="summary-number {'positive' if data['summary']['connected_accounts'] > 0 else 'warning'}">{data['summary']['connected_accounts']}</div>
            <div>Cuentas Conectadas</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{data['summary']['total_positions']}</div>
            <div>Posiciones Totales</div>
        </div>
        <div class="summary-card">
            <div class="summary-number {'positive' if data['summary']['total_profit'] >= 0 else 'negative'}">${data['summary']['total_profit']:.2f}</div>
            <div>P&L Total</div>
        </div>
        <div class="summary-card">
            <div class="summary-number {'warning' if data['summary']['total_risk_positions'] > 0 else 'positive'}">{data['summary']['total_risk_positions']}</div>
            <div>Posiciones de Riesgo</div>
        </div>
    </div>
    
    <div class="accounts-grid">"""
        
        # Generar cada cuenta
        for account_key, account_data in data['accounts'].items():
            account_config = self.accounts_config[account_key]
            
            if account_data['status'] == 'CONNECTED':
                html += f"""
        <div class="account-card">
            <div class="account-header">
                <div class="account-title">
                    {account_data['account']['name']}
                    {'<span class="monitor-badge">MONITOR ONLY</span>' if account_data['monitor_only'] else '<span class="monitor-badge" style="background: #4CAF50;">TRADING</span>'}
                </div>
                <span class="status-badge status-connected">CONECTADO</span>
            </div>
            
            <div class="account-info">
                <div class="info-item">
                    <div class="info-label">Cuenta</div>
                    <div class="info-value">{account_data['account']['login']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Balance</div>
                    <div class="info-value">${account_data['account']['balance']:,.2f}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Equity</div>
                    <div class="info-value">${account_data['account']['equity']:,.2f}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">P&L</div>
                    <div class="info-value {'positive' if account_data['account']['profit'] >= 0 else 'negative'}">${account_data['account']['profit']:.2f}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Margen Libre</div>
                    <div class="info-value">${account_data['account']['margin_free']:,.2f}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Leverage</div>
                    <div class="info-value">1:{account_data['account']['leverage']}</div>
                </div>
            </div>
            
            <h4>Posiciones Abiertas ({account_data['total_positions']})</h4>
            {'<p style="opacity: 0.7; margin: 10px 0;">No hay posiciones abiertas</p>' if not account_data['positions'] else ''}
            
            {f'''<table class="positions-table">
                <thead>
                    <tr>
                        <th>Ticket</th>
                        <th>Símbolo</th>
                        <th>Tipo</th>
                        <th>Vol</th>
                        <th>P&L</th>
                        <th>Protección</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"""<tr>
                        <td>#{pos['ticket']}</td>
                        <td>{pos['symbol']}</td>
                        <td>{pos['type']}</td>
                        <td>{pos['volume']}</td>
                        <td class="{'positive' if pos['profit'] >= 0 else 'negative'}">${pos['profit']:.2f}</td>
                        <td>
                            <span class="risk-indicator {'risk-high' if pos['sl_missing'] and pos['tp_missing'] else 'risk-medium' if pos['sl_missing'] or pos['tp_missing'] else 'risk-low'}"></span>
                            {'SL: NO' if pos['sl_missing'] else 'SL: OK'} | 
                            {'TP: NO' if pos['tp_missing'] else 'TP: OK'}
                        </td>
                    </tr>""" for pos in account_data['positions']])}
                </tbody>
            </table>''' if account_data['positions'] else ''}
        </div>"""
            
            elif account_data['status'] == 'DIFFERENT_ACCOUNT':
                # Cuenta diferente pero con datos
                html += f"""
        <div class="account-card">
            <div class="account-header">
                <div class="account-title">
                    {account_config['name']}
                    {'<span class="monitor-badge">MONITOR ONLY</span>' if account_config['monitor_only'] else '<span class="monitor-badge" style="background: #4CAF50;">TRADING</span>'}
                </div>
                <span class="status-badge status-different">CUENTA DIFERENTE</span>
            </div>
            
            <div class="account-info">
                <div class="info-item">
                    <div class="info-label">Esperada</div>
                    <div class="info-value">{account_data['expected']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Actual</div>
                    <div class="info-value">{account_data['actual']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Servidor</div>
                    <div class="info-value">{account_data['current_account_data']['server']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Compañía</div>
                    <div class="info-value">{account_data['current_account_data']['company']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Balance</div>
                    <div class="info-value">${account_data['current_account_data']['balance']:,.2f}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Equity</div>
                    <div class="info-value">${account_data['current_account_data']['equity']:,.2f}</div>
                </div>
            </div>
            
            <p style="opacity: 0.8; margin-top: 15px; padding: 10px; background: rgba(156,39,176,0.2); border-radius: 5px;">
                ℹ️ MT5 está conectado a una cuenta diferente. Para ver datos de {account_config['name']} ({account_data['expected']}), 
                asegúrate de que MT5 esté conectado a esa cuenta específicamente.
            </p>
        </div>"""
            
            else:
                # Cuenta con error real
                error_msg = account_data.get('error', 'Error desconocido')
                status_class = 'status-error' if account_data['status'] == 'ERROR' else 'status-login' if account_data['status'] == 'LOGIN_ERROR' else 'status-wrong'
                
                html += f"""
        <div class="account-card">
            <div class="account-header">
                <div class="account-title">{account_config['name']}</div>
                <span class="status-badge {status_class}">{account_data['status']}</span>
            </div>
            <div class="info-item">
                <div class="info-label">Error</div>
                <div class="info-value">{error_msg}</div>
            </div>
            {'<p><strong>Cuenta esperada:</strong> ' + str(account_data.get('expected', '')) + '<br><strong>Cuenta actual:</strong> ' + str(account_data.get('actual', '')) + '</p>' if 'expected' in account_data else ''}
        </div>"""
        
        html += """
    </div>
    
    <div class="footer">
        <p><strong>MONITORING DASHBOARD</strong> - Puerto 8503</p>
        <p>Especializado en monitoreo multi-cuenta MT5</p>
    </div>
</body>
</html>"""
        
        return html

class MonitoringHandler(http.server.SimpleHTTPRequestHandler):
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
    dashboard = MonitoringDashboard()
    port = 8503
    
    def handler(*args, **kwargs):
        return MonitoringHandler(*args, dashboard=dashboard, **kwargs)
    
    print(f"[MONITORING DASHBOARD] Iniciando en puerto {port}")
    print(f"URL: http://localhost:{port}")
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()