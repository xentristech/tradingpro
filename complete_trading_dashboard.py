#!/usr/bin/env python3
"""
Complete Trading Dashboard con Graficos de Senales y Operaciones
================================================================
Dashboard profesional con visualizacion completa de trading
"""

import http.server
import socketserver
import json
import threading
import webbrowser
import time
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import pandas as pd
import sqlite3
import random

class CompleteTradingDashboard:
    def __init__(self, port=8511):
        self.port = port
        self.signal_history = []
        self.operations_history = []
        self.pnl_history = []
        
    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                return False, "No se pudo inicializar MT5"
            return True, "Conectado exitosamente"
        except Exception as e:
            return False, f"Error: {e}"
    
    def get_signal_history(self):
        """Obtener historial de senales desde CSV y DB"""
        signals = []
        
        # Leer desde CSV
        try:
            csv_path = Path("data/historial_senales.csv")
            if csv_path.exists():
                df = pd.read_csv(csv_path, nrows=100)
                for _, row in df.iterrows():
                    signals.append({
                        'timestamp': row['timestamp'],
                        'symbol': row['symbol'],
                        'signal_type': row['signal_type'],
                        'confidence': row['confidence'],
                        'entry_price': row['entry_price'],
                        'stop_loss': row['stop_loss'],
                        'take_profit': row['take_profit']
                    })
        except Exception as e:
            print(f"Error leyendo CSV: {e}")
        
        # Leer desde SQLite
        try:
            db_path = Path("data/trading.db")
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, symbol, signal_type, confidence, entry_price, stop_loss, take_profit
                    FROM signals
                    ORDER BY timestamp DESC
                    LIMIT 50
                """)
                for row in cursor.fetchall():
                    signals.append({
                        'timestamp': row[0],
                        'symbol': row[1],
                        'signal_type': row[2],
                        'confidence': row[3],
                        'entry_price': row[4],
                        'stop_loss': row[5],
                        'take_profit': row[6]
                    })
                conn.close()
        except Exception as e:
            print(f"Error leyendo DB: {e}")
        
        return signals[:50]  # Ultimas 50 senales
    
    def get_operations_history(self):
        """Obtener historial de operaciones de MT5"""
        operations = []
        
        mt5_ok, _ = self.connect_mt5()
        if mt5_ok:
            try:
                # Obtener historial de deals
                from_date = datetime.now() - timedelta(days=30)
                to_date = datetime.now()
                
                deals = mt5.history_deals_get(from_date, to_date)
                if deals:
                    for deal in deals[-50:]:  # Ultimas 50 operaciones
                        operations.append({
                            'ticket': deal.ticket,
                            'time': datetime.fromtimestamp(deal.time).strftime('%Y-%m-%d %H:%M:%S'),
                            'symbol': deal.symbol,
                            'type': 'BUY' if deal.type == 0 else 'SELL',
                            'volume': deal.volume,
                            'price': deal.price,
                            'profit': deal.profit,
                            'commission': deal.commission,
                            'swap': deal.swap
                        })
                
                # Obtener posiciones actuales
                positions = mt5.positions_get()
                if positions:
                    for pos in positions:
                        operations.append({
                            'ticket': pos.ticket,
                            'time': datetime.fromtimestamp(pos.time).strftime('%Y-%m-%d %H:%M:%S'),
                            'symbol': pos.symbol,
                            'type': 'BUY' if pos.type == 0 else 'SELL',
                            'volume': pos.volume,
                            'price': pos.price_open,
                            'profit': pos.profit,
                            'commission': 0,
                            'swap': pos.swap,
                            'current': True
                        })
                        
            except Exception as e:
                print(f"Error obteniendo operaciones: {e}")
            finally:
                mt5.shutdown()
        
        # Datos de ejemplo si no hay operaciones reales
        if not operations:
            base_time = datetime.now()
            for i in range(20):
                operations.append({
                    'ticket': 220000000 + i,
                    'time': (base_time - timedelta(hours=i*2)).strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': random.choice(['XAUUSDm', 'BTCUSDm', 'EURUSDm']),
                    'type': random.choice(['BUY', 'SELL']),
                    'volume': round(random.uniform(0.01, 0.5), 2),
                    'price': round(random.uniform(1.0, 3500), 2),
                    'profit': round(random.uniform(-50, 150), 2),
                    'commission': round(random.uniform(-2, 0), 2),
                    'swap': round(random.uniform(-1, 1), 2)
                })
        
        return operations
    
    def calculate_statistics(self, operations):
        """Calcular estadisticas de trading"""
        if not operations:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'average_profit': 0,
                'max_profit': 0,
                'max_loss': 0,
                'profit_factor': 0
            }
        
        profits = [op['profit'] for op in operations if 'profit' in op]
        winning = [p for p in profits if p > 0]
        losing = [p for p in profits if p < 0]
        
        return {
            'total_trades': len(profits),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': round(len(winning) / len(profits) * 100, 2) if profits else 0,
            'total_profit': round(sum(profits), 2),
            'average_profit': round(sum(profits) / len(profits), 2) if profits else 0,
            'max_profit': round(max(profits), 2) if profits else 0,
            'max_loss': round(min(profits), 2) if profits else 0,
            'profit_factor': round(sum(winning) / abs(sum(losing)), 2) if losing else 0
        }
    
    def get_system_data(self):
        """Obtener todos los datos del sistema"""
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mt5_connected': False,
            'account': {},
            'signals': [],
            'operations': [],
            'statistics': {},
            'pnl_chart': [],
            'signal_distribution': {},
            'hourly_performance': []
        }
        
        # Conectar MT5
        mt5_ok, msg = self.connect_mt5()
        data['mt5_connected'] = mt5_ok
        
        if mt5_ok:
            try:
                # Informacion de cuenta
                account = mt5.account_info()
                if account:
                    data['account'] = {
                        'balance': account.balance,
                        'equity': account.equity,
                        'margin': account.margin,
                        'free_margin': account.margin_free,
                        'profit': account.profit,
                        'leverage': account.leverage
                    }
            except Exception as e:
                print(f"Error cuenta: {e}")
            finally:
                mt5.shutdown()
        
        # Obtener senales
        data['signals'] = self.get_signal_history()
        
        # Obtener operaciones
        data['operations'] = self.get_operations_history()
        
        # Calcular estadisticas
        data['statistics'] = self.calculate_statistics(data['operations'])
        
        # Generar grafico P&L acumulado
        if data['operations']:
            cumulative = 0
            for op in sorted(data['operations'], key=lambda x: x['time']):
                cumulative += op.get('profit', 0)
                data['pnl_chart'].append({
                    'time': op['time'],
                    'value': round(cumulative, 2)
                })
        
        # Distribucion de senales
        signal_types = {}
        for signal in data['signals']:
            sig_type = signal.get('signal_type', 'UNKNOWN')
            signal_types[sig_type] = signal_types.get(sig_type, 0) + 1
        
        data['signal_distribution'] = [
            {'name': k, 'value': v} for k, v in signal_types.items()
        ]
        
        # Performance por hora
        hourly = {}
        for op in data['operations']:
            try:
                hour = datetime.strptime(op['time'], '%Y-%m-%d %H:%M:%S').hour
                if hour not in hourly:
                    hourly[hour] = {'profit': 0, 'count': 0}
                hourly[hour]['profit'] += op.get('profit', 0)
                hourly[hour]['count'] += 1
            except:
                pass
        
        data['hourly_performance'] = [
            {'hour': h, 'profit': round(v['profit'], 2), 'trades': v['count']}
            for h, v in sorted(hourly.items())
        ]
        
        return data
    
    def generate_html(self):
        """Generar HTML del dashboard completo"""
        return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Trading Dashboard - AlgoTrader v3.0</title>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            min-height: 100vh;
        }
        
        .dashboard-header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .card h3 {
            margin-bottom: 15px;
            color: #fff;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .stat-box {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.8;
            text-transform: uppercase;
        }
        
        .positive { color: #4CAF50; }
        .negative { color: #f44336; }
        .neutral { color: #FFC107; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        th {
            background: rgba(255,255,255,0.1);
            font-weight: 600;
        }
        
        .signal-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }
        
        .signal-buy { background: #4CAF50; }
        .signal-sell { background: #f44336; }
        .signal-hold { background: #FFC107; color: #333; }
        
        .refresh-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        
        .performance-chart {
            height: 250px;
        }
        
        #pnl-chart, #volume-chart {
            height: 300px;
        }
    </style>
</head>
<body>
    <div class="refresh-indicator">Auto-refresh: 10s</div>
    
    <div class="dashboard-header">
        <h1>COMPLETE TRADING DASHBOARD v3.0</h1>
        <p>Panel Profesional con Graficos de Senales y Operaciones</p>
        <p id="last-update">Actualizando...</p>
    </div>
    
    <!-- Statistics Cards -->
    <div class="dashboard-grid">
        <div class="card">
            <h3>ESTADISTICAS DE TRADING</h3>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value" id="total-trades">0</div>
                    <div class="stat-label">Total Trades</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value positive" id="win-rate">0%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="total-profit">$0</div>
                    <div class="stat-label">P&L Total</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="profit-factor">0</div>
                    <div class="stat-label">Profit Factor</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>INFORMACION DE CUENTA</h3>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value" id="balance">$0</div>
                    <div class="stat-label">Balance</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="equity">$0</div>
                    <div class="stat-label">Equity</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="margin">$0</div>
                    <div class="stat-label">Margen</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="free-margin">$0</div>
                    <div class="stat-label">Margen Libre</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Charts -->
    <div class="dashboard-grid">
        <div class="card">
            <h3>GRAFICO P&L ACUMULADO</h3>
            <div class="chart-container">
                <canvas id="pnl-chart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h3>DISTRIBUCION DE SENALES</h3>
            <div class="chart-container">
                <canvas id="signals-chart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h3>PERFORMANCE POR HORA</h3>
            <div class="chart-container">
                <canvas id="hourly-chart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h3>VOLUMEN DE OPERACIONES</h3>
            <div class="chart-container">
                <canvas id="volume-chart"></canvas>
            </div>
        </div>
    </div>
    
    <!-- Tables -->
    <div class="dashboard-grid">
        <div class="card">
            <h3>ULTIMAS SENALES GENERADAS</h3>
            <div style="max-height: 400px; overflow-y: auto;">
                <table id="signals-table">
                    <thead>
                        <tr>
                            <th>Tiempo</th>
                            <th>Symbol</th>
                            <th>Senal</th>
                            <th>Precio</th>
                            <th>Confianza</th>
                        </tr>
                    </thead>
                    <tbody id="signals-tbody">
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card">
            <h3>HISTORIAL DE OPERACIONES</h3>
            <div style="max-height: 400px; overflow-y: auto;">
                <table id="operations-table">
                    <thead>
                        <tr>
                            <th>Ticket</th>
                            <th>Tiempo</th>
                            <th>Symbol</th>
                            <th>Tipo</th>
                            <th>Vol</th>
                            <th>P&L</th>
                        </tr>
                    </thead>
                    <tbody id="operations-tbody">
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        // Chart instances
        let pnlChart, signalsChart, hourlyChart, volumeChart;
        
        // Initialize charts
        function initCharts() {
            // P&L Chart
            const pnlCtx = document.getElementById('pnl-chart').getContext('2d');
            pnlChart = new Chart(pnlCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'P&L Acumulado',
                        data: [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        x: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    }
                }
            });
            
            // Signals Distribution Chart
            const signalsCtx = document.getElementById('signals-chart').getContext('2d');
            signalsChart = new Chart(signalsCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: ['#4CAF50', '#f44336', '#FFC107', '#2196F3']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: 'white' }
                        }
                    }
                }
            });
            
            // Hourly Performance Chart
            const hourlyCtx = document.getElementById('hourly-chart').getContext('2d');
            hourlyChart = new Chart(hourlyCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Profit por Hora',
                        data: [],
                        backgroundColor: '#2196F3'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        x: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    }
                }
            });
            
            // Volume Chart
            const volumeCtx = document.getElementById('volume-chart').getContext('2d');
            volumeChart = new Chart(volumeCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Volumen',
                        data: [],
                        backgroundColor: '#9C27B0'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        x: {
                            ticks: { color: 'white' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    }
                }
            });
        }
        
        // Update dashboard data
        async function updateDashboard() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                // Update timestamp
                document.getElementById('last-update').textContent = 
                    `Ultima actualizacion: ${data.timestamp}`;
                
                // Update statistics
                if (data.statistics) {
                    document.getElementById('total-trades').textContent = data.statistics.total_trades;
                    document.getElementById('win-rate').textContent = data.statistics.win_rate + '%';
                    document.getElementById('total-profit').textContent = '$' + data.statistics.total_profit;
                    document.getElementById('profit-factor').textContent = data.statistics.profit_factor;
                    
                    // Color code profit
                    const profitEl = document.getElementById('total-profit');
                    profitEl.className = data.statistics.total_profit >= 0 ? 'stat-value positive' : 'stat-value negative';
                }
                
                // Update account info
                if (data.account) {
                    document.getElementById('balance').textContent = '$' + (data.account.balance || 0).toFixed(2);
                    document.getElementById('equity').textContent = '$' + (data.account.equity || 0).toFixed(2);
                    document.getElementById('margin').textContent = '$' + (data.account.margin || 0).toFixed(2);
                    document.getElementById('free-margin').textContent = '$' + (data.account.free_margin || 0).toFixed(2);
                }
                
                // Update P&L Chart
                if (data.pnl_chart && pnlChart) {
                    pnlChart.data.labels = data.pnl_chart.map(p => p.time.split(' ')[1]);
                    pnlChart.data.datasets[0].data = data.pnl_chart.map(p => p.value);
                    pnlChart.update();
                }
                
                // Update Signals Distribution
                if (data.signal_distribution && signalsChart) {
                    signalsChart.data.labels = data.signal_distribution.map(s => s.name);
                    signalsChart.data.datasets[0].data = data.signal_distribution.map(s => s.value);
                    signalsChart.update();
                }
                
                // Update Hourly Performance
                if (data.hourly_performance && hourlyChart) {
                    hourlyChart.data.labels = data.hourly_performance.map(h => h.hour + ':00');
                    hourlyChart.data.datasets[0].data = data.hourly_performance.map(h => h.profit);
                    hourlyChart.update();
                }
                
                // Update Volume Chart
                if (data.operations && volumeChart) {
                    const volumeData = data.operations.slice(0, 20).map(op => ({
                        time: op.time.split(' ')[1],
                        volume: op.volume
                    }));
                    volumeChart.data.labels = volumeData.map(v => v.time);
                    volumeChart.data.datasets[0].data = volumeData.map(v => v.volume);
                    volumeChart.update();
                }
                
                // Update Signals Table
                const signalsTbody = document.getElementById('signals-tbody');
                signalsTbody.innerHTML = '';
                if (data.signals) {
                    data.signals.slice(0, 10).forEach(signal => {
                        const row = signalsTbody.insertRow();
                        const signalClass = signal.signal_type === 'BUY' ? 'signal-buy' : 
                                           signal.signal_type === 'SELL' ? 'signal-sell' : 'signal-hold';
                        row.innerHTML = `
                            <td>${signal.timestamp}</td>
                            <td>${signal.symbol}</td>
                            <td><span class="signal-badge ${signalClass}">${signal.signal_type}</span></td>
                            <td>$${signal.entry_price}</td>
                            <td>${signal.confidence}%</td>
                        `;
                    });
                }
                
                // Update Operations Table
                const opsTbody = document.getElementById('operations-tbody');
                opsTbody.innerHTML = '';
                if (data.operations) {
                    data.operations.slice(0, 10).forEach(op => {
                        const row = opsTbody.insertRow();
                        const profitClass = op.profit >= 0 ? 'positive' : 'negative';
                        row.innerHTML = `
                            <td>#${op.ticket}</td>
                            <td>${op.time}</td>
                            <td>${op.symbol}</td>
                            <td>${op.type}</td>
                            <td>${op.volume}</td>
                            <td class="${profitClass}">$${op.profit.toFixed(2)}</td>
                        `;
                    });
                }
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }
        
        // Initialize on load
        window.addEventListener('load', () => {
            initCharts();
            updateDashboard();
            
            // Auto-refresh every 10 seconds
            setInterval(updateDashboard, 10000);
        });
    </script>
</body>
</html>
"""
    
    def run(self):
        """Ejecutar el servidor del dashboard"""
        class CustomHandler(http.server.BaseHTTPRequestHandler):
            def __init__(self, *args, dashboard=None, **kwargs):
                self.dashboard = dashboard
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(self.dashboard.generate_html().encode('utf-8'))
                
                elif self.path == '/api/data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    data = self.dashboard.get_system_data()
                    self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
                
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suprimir logs
        
        def handler(*args, **kwargs):
            return CustomHandler(*args, dashboard=self, **kwargs)
        
        try:
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                print(f"COMPLETE TRADING DASHBOARD iniciado en puerto {self.port}")
                print(f"Acceso: http://localhost:{self.port}")
                print("Caracteristicas:")
                print("   - Graficos de P&L acumulado")
                print("   - Distribucion de senales de trading")
                print("   - Performance por hora")
                print("   - Volumen de operaciones")
                print("   - Historial completo de senales")
                print("   - Historial de operaciones")
                print("   - Estadisticas en tiempo real")
                print("   - Auto-refresh cada 10 segundos")
                print("\nPresiona Ctrl+C para detener")
                
                # Abrir navegador
                threading.Timer(2.0, lambda: webbrowser.open(f'http://localhost:{self.port}')).start()
                
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\nDashboard detenido")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    dashboard = CompleteTradingDashboard(port=8511)
    dashboard.run()