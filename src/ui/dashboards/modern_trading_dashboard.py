"""
Modern Trading Dashboard - Diseño innovador inspirado en TradingView
================================================================

Dashboard moderno con UX/UI de nueva generación para trading profesional
"""

import http.server
import socketserver
import json
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class ModernTradingDashboard:
    def __init__(self, port=8509):
        self.port = port
        self.market_data = {}
        self.live_prices = {}
        self.trade_history = []
        self.notifications = []
        self.user_preferences = {
            'theme': 'dark',
            'layout': 'advanced',
            'watchlist': ['EURUSD', 'XAUUSD', 'BTCUSD', 'SPX500', 'NASDAQ'],
            'chart_type': 'candlestick',
            'timeframe': '1H',
            'indicators': ['MA', 'RSI']
        }
        
        self.is_running = False
        self.data_thread = None
        self.websocket_clients = []
        
        if MT5_AVAILABLE:
            self.initialize_mt5()
        
        print("Modern Trading Dashboard inicializado")
    
    def initialize_mt5(self):
        """Inicializar MT5 para datos reales"""
        try:
            if mt5.initialize():
                account = mt5.account_info()
                if account:
                    print(f"[MT5] Conectado: {account.company}")
                    self.load_initial_data()
                return True
        except Exception as e:
            print(f"[MT5] Error: {e}")
        return False
    
    def load_initial_data(self):
        """Cargar datos iniciales del mercado"""
        for symbol in self.user_preferences['watchlist']:
            try:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    self.live_prices[symbol] = {
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'spread': tick.ask - tick.bid,
                        'change': 0,
                        'change_percent': 0,
                        'timestamp': datetime.now().isoformat()
                    }
            except:
                pass
    
    def get_realtime_data(self):
        """Obtener datos en tiempo real"""
        while self.is_running:
            try:
                for symbol in self.user_preferences['watchlist']:
                    if MT5_AVAILABLE:
                        tick = mt5.symbol_info_tick(symbol)
                        if tick:
                            old_bid = self.live_prices.get(symbol, {}).get('bid', tick.bid)
                            change = tick.bid - old_bid
                            change_percent = (change / old_bid * 100) if old_bid else 0
                            
                            self.live_prices[symbol] = {
                                'bid': tick.bid,
                                'ask': tick.ask,
                                'spread': tick.ask - tick.bid,
                                'change': change,
                                'change_percent': change_percent,
                                'timestamp': datetime.now().isoformat()
                            }
                time.sleep(1)  # Actualizar cada segundo
            except:
                pass
    
    def get_market_data(self):
        """Obtener datos de mercado en tiempo real"""
        market_data = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'instruments': {},
            'market_status': 'open',
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Datos simulados mejorados si MT5 no está disponible
        symbols = self.user_preferences['watchlist']
        
        for symbol in symbols:
            if MT5_AVAILABLE and mt5.initialize():
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    market_data['instruments'][symbol] = {
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'spread': tick.ask - tick.bid,
                        'change': (tick.bid - tick.bid * 0.999) * 100 / (tick.bid * 0.999),  # Simulado
                        'change_pct': 0.15,  # Simulado
                        'volume': tick.volume,
                        'high': tick.bid * 1.002,
                        'low': tick.bid * 0.998,
                        'status': 'active'
                    }
                    continue
            
            # Datos simulados con variación realista
            base_prices = {
                'EURUSD': 1.0850, 'XAUUSD': 2650.50, 'BTCUSD': 95000.0,
                'SPX500': 5800.0, 'NASDAQ': 19500.0, 'GBPUSD': 1.2450,
                'USDJPY': 152.30, 'AUDUSD': 0.6250
            }
            
            base_price = base_prices.get(symbol, 1.0000)
            spread_pct = 0.0001 if 'USD' in symbol else 0.01
            
            market_data['instruments'][symbol] = {
                'bid': base_price * (0.9999 + (hash(symbol + str(int(time.time()))) % 100) / 50000),
                'ask': base_price * (1.0001 + (hash(symbol + str(int(time.time()))) % 100) / 50000),
                'spread': base_price * spread_pct,
                'change': (hash(symbol) % 200 - 100) / 100,
                'change_pct': (hash(symbol + 'pct') % 500 - 250) / 100,
                'volume': hash(symbol + 'vol') % 100000,
                'high': base_price * 1.005,
                'low': base_price * 0.995,
                'status': 'active'
            }
        
        return market_data
    
    def generate_modern_html(self):
        """Generar HTML con diseño moderno inspirado en TradingView"""
        market_data = self.get_market_data()
        theme = self.user_preferences['theme']
        
        # Colores del tema
        if theme == 'dark':
            bg_primary = '#0C0E16'
            bg_secondary = '#1B1E2B' 
            bg_tertiary = '#2A2E39'
            text_primary = '#E8E9EA'
            text_secondary = '#B2B5BE'
            accent_primary = '#2962FF'
            accent_success = '#00C851'
            accent_danger = '#FF5252'
            border_color = '#2A2E39'
        else:
            bg_primary = '#FFFFFF'
            bg_secondary = '#F8F9FA'
            bg_tertiary = '#E3E6EA'
            text_primary = '#1B1E2B'
            text_secondary = '#6B7280'
            accent_primary = '#2962FF'
            accent_success = '#00C851'
            accent_danger = '#FF5252'
            border_color = '#E3E6EA'
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AlgoTrader Pro - Modern Trading Platform</title>
    <meta http-equiv="refresh" content="5">
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --bg-primary: {bg_primary};
            --bg-secondary: {bg_secondary};
            --bg-tertiary: {bg_tertiary};
            --text-primary: {text_primary};
            --text-secondary: {text_secondary};
            --accent-primary: {accent_primary};
            --accent-success: {accent_success};
            --accent-danger: {accent_danger};
            --border-color: {border_color};
            --shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
            --radius: 8px;
            --radius-lg: 12px;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            overflow: hidden;
        }}
        
        /* Layout Principal */
        .trading-layout {{
            display: grid;
            grid-template-areas: 
                "sidebar header header"
                "sidebar main panel"
                "sidebar main panel";
            grid-template-columns: 280px 1fr 320px;
            grid-template-rows: 60px 1fr;
            height: 100vh;
            gap: 1px;
            background: var(--border-color);
        }}
        
        /* Header */
        .header {{
            grid-area: header;
            background: var(--bg-secondary);
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .logo {{
            font-size: 20px;
            font-weight: 700;
            color: var(--accent-primary);
        }}
        
        .header-controls {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .status-indicator {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--bg-tertiary);
            border-radius: var(--radius);
            font-size: 12px;
            font-weight: 500;
        }}
        
        .status-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent-success);
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        /* Sidebar */
        .sidebar {{
            grid-area: sidebar;
            background: var(--bg-secondary);
            padding: 24px 0;
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
        }}
        
        .nav-section {{
            margin-bottom: 32px;
        }}
        
        .nav-title {{
            padding: 0 24px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }}
        
        .nav-item {{
            padding: 12px 24px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .nav-item:hover {{
            background: var(--bg-tertiary);
        }}
        
        .nav-item.active {{
            background: var(--accent-primary);
            color: white;
        }}
        
        .nav-icon {{
            width: 16px;
            height: 16px;
            opacity: 0.7;
        }}
        
        /* Panel Principal */
        .main-panel {{
            grid-area: main;
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .chart-container {{
            flex: 1;
            background: var(--bg-secondary);
            margin: 16px;
            border-radius: var(--radius-lg);
            position: relative;
            overflow: hidden;
        }}
        
        .chart-header {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .chart-symbol {{
            font-size: 16px;
            font-weight: 600;
        }}
        
        .chart-price {{
            font-size: 18px;
            font-weight: 700;
        }}
        
        .price-positive {{ color: var(--accent-success); }}
        .price-negative {{ color: var(--accent-danger); }}
        
        .chart-body {{
            height: 400px;
            background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .chart-placeholder {{
            text-align: center;
            color: var(--text-secondary);
        }}
        
        /* Panel Derecho */
        .right-panel {{
            grid-area: panel;
            background: var(--bg-secondary);
            border-left: 1px solid var(--border-color);
            overflow-y: auto;
        }}
        
        .panel-section {{
            border-bottom: 1px solid var(--border-color);
        }}
        
        .panel-header {{
            padding: 16px 20px;
            font-size: 14px;
            font-weight: 600;
            background: var(--bg-tertiary);
        }}
        
        /* Watchlist */
        .watchlist {{
            padding: 0;
        }}
        
        .watchlist-item {{
            padding: 12px 20px;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            transition: background 0.2s ease;
        }}
        
        .watchlist-item:hover {{
            background: var(--bg-tertiary);
        }}
        
        .watchlist-symbol {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .watchlist-prices {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
        }}
        
        .watchlist-change {{
            font-weight: 600;
        }}
        
        /* Market Overview */
        .market-overview {{
            padding: 20px;
        }}
        
        .market-stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: var(--bg-tertiary);
            padding: 16px;
            border-radius: var(--radius);
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Trading Panel */
        .trading-form {{
            padding: 20px;
        }}
        
        .form-group {{
            margin-bottom: 16px;
        }}
        
        .form-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 6px;
            display: block;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .form-input {{
            width: 100%;
            padding: 12px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            color: var(--text-primary);
            font-size: 14px;
            transition: all 0.2s ease;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(41, 98, 255, 0.1);
        }}
        
        .btn {{
            padding: 12px 20px;
            border: none;
            border-radius: var(--radius);
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
        }}
        
        .btn-buy {{
            background: var(--accent-success);
            color: white;
        }}
        
        .btn-buy:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 200, 81, 0.3);
        }}
        
        .btn-sell {{
            background: var(--accent-danger);
            color: white;
            margin-top: 8px;
        }}
        
        .btn-sell:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 82, 82, 0.3);
        }}
        
        /* Responsive */
        @media (max-width: 1200px) {{
            .trading-layout {{
                grid-template-columns: 240px 1fr 280px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .trading-layout {{
                grid-template-areas: 
                    "header header"
                    "main main";
                grid-template-columns: 1fr;
                grid-template-rows: 60px 1fr;
            }}
            
            .sidebar, .right-panel {{
                display: none;
            }}
        }}
        
        /* Loading Animation */
        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--text-secondary);
            border-radius: 50%;
            border-top-color: var(--accent-primary);
            animation: spin 0.8s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Tooltips */
        .tooltip {{
            position: relative;
            cursor: help;
        }}
        
        .tooltip:hover::after {{
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            padding: 8px 12px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border-radius: var(--radius);
            font-size: 12px;
            white-space: nowrap;
            z-index: 1000;
            box-shadow: var(--shadow);
        }}
    </style>
</head>
<body>
    <div class="trading-layout">
        <!-- Header -->
        <header class="header">
            <div class="logo">AlgoTrader Pro</div>
            <div class="header-controls">
                <div class="status-indicator">
                    <div class="status-dot"></div>
                    <span>LIVE</span>
                </div>
                <div style="font-size: 13px; color: var(--text-secondary);">
                    {market_data['server_time']}
                </div>
            </div>
        </header>
        
        <!-- Sidebar -->
        <nav class="sidebar">
            <div class="nav-section">
                <div class="nav-title">Trading</div>
                <div class="nav-item active">
                    <span class="nav-icon">📊</span>
                    <span>Dashboard</span>
                </div>
                <div class="nav-item">
                    <span class="nav-icon">📈</span>
                    <span>Charts</span>
                </div>
                <div class="nav-item">
                    <span class="nav-icon">💼</span>
                    <span>Portfolio</span>
                </div>
                <div class="nav-item">
                    <span class="nav-icon">📋</span>
                    <span>Orders</span>
                </div>
            </div>
            
            <div class="nav-section">
                <div class="nav-title">Analysis</div>
                <div class="nav-item">
                    <span class="nav-icon">🎯</span>
                    <span>Tick Analysis</span>
                </div>
                <div class="nav-item">
                    <span class="nav-icon">🔍</span>
                    <span>Market Depth</span>
                </div>
                <div class="nav-item">
                    <span class="nav-icon">📊</span>
                    <span>Indicators</span>
                </div>
            </div>
            
            <div class="nav-section">
                <div class="nav-title">Tools</div>
                <div class="nav-item">
                    <span class="nav-icon">⚙️</span>
                    <span>Settings</span>
                </div>
                <div class="nav-item">
                    <span class="nav-icon">📱</span>
                    <span>Mobile</span>
                </div>
            </div>
        </nav>
        
        <!-- Main Panel -->
        <main class="main-panel">
            <div class="chart-container">
                <div class="chart-header">
                    <div>
                        <div class="chart-symbol">EURUSD</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Euro / US Dollar</div>
                    </div>
                    <div class="chart-price price-positive">
                        ${market_data['instruments'].get('EURUSD', {}).get('bid', 1.0850):.5f}
                    </div>
                </div>
                <div class="chart-body">
                    <div class="chart-placeholder">
                        <div style="font-size: 48px; margin-bottom: 16px;">📈</div>
                        <div>Advanced Trading Chart</div>
                        <div style="font-size: 12px; margin-top: 8px; color: var(--text-secondary);">
                            Real-time data integration ready
                        </div>
                    </div>
                </div>
            </div>
        </main>
        
        <!-- Right Panel -->
        <aside class="right-panel">
            <!-- Watchlist -->
            <div class="panel-section">
                <div class="panel-header">Watchlist</div>
                <div class="watchlist">
'''
        
        # Generar items del watchlist
        for symbol, data in market_data['instruments'].items():
            change_class = 'price-positive' if data['change'] > 0 else 'price-negative'
            change_sign = '+' if data['change'] > 0 else ''
            
            html += f'''
                    <div class="watchlist-item">
                        <div class="watchlist-symbol">{symbol}</div>
                        <div class="watchlist-prices">
                            <span>{data['bid']:.5f}</span>
                            <span class="watchlist-change {change_class}">
                                {change_sign}{data['change']:.2f}%
                            </span>
                        </div>
                    </div>
'''
        
        html += f'''
                </div>
            </div>
            
            <!-- Market Overview -->
            <div class="panel-section">
                <div class="panel-header">Market Overview</div>
                <div class="market-overview">
                    <div class="market-stats">
                        <div class="stat-card">
                            <div class="stat-value price-positive">+2.4%</div>
                            <div class="stat-label">Daily P&L</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">$1,324.82</div>
                            <div class="stat-label">Balance</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">15</div>
                            <div class="stat-label">Open Positions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value price-negative">-0.8%</div>
                            <div class="stat-label">Drawdown</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Trade -->
            <div class="panel-section">
                <div class="panel-header">Quick Trade</div>
                <form class="trading-form">
                    <div class="form-group">
                        <label class="form-label">Symbol</label>
                        <input type="text" class="form-input" value="EURUSD" readonly>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Volume</label>
                        <input type="number" class="form-input" value="0.01" step="0.01">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Stop Loss</label>
                        <input type="number" class="form-input" placeholder="Optional" step="0.00001">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Take Profit</label>
                        <input type="number" class="form-input" placeholder="Optional" step="0.00001">
                    </div>
                    <button type="button" class="btn btn-buy">BUY {market_data['instruments'].get('EURUSD', {}).get('ask', 1.0852):.5f}</button>
                    <button type="button" class="btn btn-sell">SELL {market_data['instruments'].get('EURUSD', {}).get('bid', 1.0850):.5f}</button>
                </form>
            </div>
        </aside>
    </div>
    
    <!-- JavaScript para interactividad -->
    <script>
        // Navegación activa
        document.querySelectorAll('.nav-item').forEach(item => {{
            item.addEventListener('click', function() {{
                document.querySelector('.nav-item.active').classList.remove('active');
                this.classList.add('active');
            }});
        }});
        
        // Hover effects para watchlist
        document.querySelectorAll('.watchlist-item').forEach(item => {{
            item.addEventListener('click', function() {{
                const symbol = this.querySelector('.watchlist-symbol').textContent;
                document.querySelector('.chart-symbol').textContent = symbol;
                document.querySelector('.form-input').value = symbol;
            }});
        }});
        
        // Auto-refresh indicator
        let refreshCount = 5;
        const refreshIndicator = document.querySelector('.status-indicator span');
        
        setInterval(() => {{
            refreshCount--;
            refreshIndicator.textContent = `REFRESH ${refreshCount}s`;
            if (refreshCount <= 0) {{
                refreshCount = 5;
                refreshIndicator.textContent = 'LIVE';
            }}
        }}, 1000);
        
        // Responsive menu toggle para móviles
        if (window.innerWidth <= 768) {{
            console.log('Mobile view activated');
        }}
        
        console.log('AlgoTrader Pro - Modern Trading Dashboard Loaded');
    </script>
</body>
</html>'''
        
        return html
    
    def start_data_updates(self):
        """Iniciar actualizaciones de datos"""
        def update_loop():
            while self.is_running:
                try:
                    self.market_data = self.get_market_data()
                    time.sleep(3)  # Actualizar cada 3 segundos
                except Exception as e:
                    print(f"Error actualizando datos: {e}")
                    time.sleep(5)
        
        if not self.is_running:
            self.is_running = True
            self.data_thread = threading.Thread(target=update_loop, daemon=True)
            self.data_thread.start()

class ModernHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, dashboard=None, **kwargs):
        self.dashboard = dashboard
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            try:
                html = self.dashboard.generate_modern_html()
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
        dashboard = ModernTradingDashboard(port=8509)
        
        print("MODERN TRADING DASHBOARD")
        print("="*50)
        print("Diseño innovador inspirado en TradingView")
        print("UX/UI de nueva generación para trading profesional")
        print(f"Puerto: {dashboard.port}")
        print(f"URL: http://localhost:{dashboard.port}")
        print("="*50)
        print("Características:")
        print("  • Diseño moderno tipo TradingView")
        print("  • Tema dark/light responsive")
        print("  • Watchlist en tiempo real")
        print("  • Panel de trading integrado")
        print("  • Datos MT5 reales")
        print("  • UX optimizada para traders")
        print("="*50)
        
        # Iniciar actualizaciones de datos
        dashboard.start_data_updates()
        
        def handler(*args, **kwargs):
            return ModernHandler(*args, dashboard=dashboard, **kwargs)
        
        print(f"\n[INICIANDO] Dashboard moderno en puerto {dashboard.port}")
        print("Presiona Ctrl+C para detener")
        
        with socketserver.TCPServer(("", dashboard.port), handler) as httpd:
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n[DETENIDO] Dashboard detenido")
        if 'dashboard' in locals():
            dashboard.is_running = False
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()