#!/usr/bin/env python3
"""
🎯 TradingView-Style Dashboard - AlgoTrader v3.0
Dashboard profesional con TradingView Lightweight Charts
"""
import http.server
import socketserver
import webbrowser
import threading
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import requests
from typing import Dict, List

class TradingViewDashboardServer:
    def __init__(self, port=8510):
        self.port = port
        self.data_cache = {}
        self.running = True
        
    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                return False, "No se pudo inicializar MT5"
            return True, "Conectado exitosamente"
        except Exception as e:
            return False, f"Error: {e}"

    def get_candle_data(self, symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, count=100):
        """Obtener datos de velas para TradingView"""
        try:
            mt5_connected, _ = self.connect_mt5()
            if not mt5_connected:
                return []
            
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return []
            
            candles = []
            current_time = time.time()
            
            for i, rate in enumerate(rates):
                # Corregir timestamps: usar tiempo actual y restar intervalos de 5 minutos
                corrected_time = int(current_time - ((len(rates) - i - 1) * 300))  # 300 segundos = 5 min
                
                candles.append({
                    'time': corrected_time,
                    'open': float(rate['open']),
                    'high': float(rate['high']),
                    'low': float(rate['low']),
                    'close': float(rate['close']),
                    'volume': int(rate['tick_volume'])
                })
            
            return candles[-50:]  # Últimas 50 velas
            
        except Exception as e:
            print(f"Error obteniendo velas: {e}")
            return self.generate_sample_data(symbol, 50)
    
    def generate_sample_data(self, symbol, count=50):
        """Generar datos de muestra cuando MT5 no está disponible"""
        import random
        
        base_price = 109000 if 'BTC' in symbol else 3475
        candles = []
        current_time = int(time.time())
        price = base_price
        
        for i in range(count):
            timestamp = current_time - ((count - i - 1) * 300)  # 5 minutos entre velas
            
            # Simular variación de precio
            change = random.uniform(-0.005, 0.005) * price
            price += change
            
            open_price = price
            high_price = price + random.uniform(0, 0.003) * price
            low_price = price - random.uniform(0, 0.003) * price
            close_price = price + random.uniform(-0.002, 0.002) * price
            
            price = close_price
            
            candles.append({
                'time': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': random.randint(1000, 5000)
            })
        
        return candles

    def get_system_data(self):
        """Obtener datos del sistema"""
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mt5_connected': False,
            'account': {},
            'positions': [],
            'candles_btc': [],
            'candles_xau': [],
            'indicators': {}
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
                        'balance': account.balance,
                        'equity': account.equity,
                        'profit': account.profit,
                        'margin': account.margin,
                        'free_margin': account.margin_free,
                        'leverage': account.leverage,
                        'server': account.server
                    }
                
                # Posiciones abiertas
                positions = mt5.positions_get()
                if positions:
                    data['positions'] = []
                    for pos in positions:
                        data['positions'].append({
                            'ticket': pos.ticket,
                            'symbol': pos.symbol,
                            'type': 'BUY' if pos.type == 0 else 'SELL',
                            'volume': pos.volume,
                            'price_open': pos.price_open,
                            'price_current': pos.price_current,
                            'profit': pos.profit,
                            'swap': pos.swap
                        })
                
                # Datos de velas para gráficos
                data['candles_btc'] = self.get_candle_data('BTCUSDm', mt5.TIMEFRAME_M5, 100)
                data['candles_xau'] = self.get_candle_data('XAUUSDm', mt5.TIMEFRAME_M5, 100)
                
                # Indicadores básicos (usando datos de velas)
                if data['candles_btc']:
                    closes = [c['close'] for c in data['candles_btc'][-20:]]
                    if len(closes) >= 20:
                        sma20 = sum(closes) / len(closes)
                        data['indicators']['btc_sma20'] = sma20
                        data['indicators']['btc_current'] = closes[-1]
                        data['indicators']['btc_change'] = closes[-1] - closes[-2] if len(closes) > 1 else 0
                        data['indicators']['btc_change_pct'] = (data['indicators']['btc_change'] / closes[-2] * 100) if len(closes) > 1 and closes[-2] != 0 else 0

                if data['candles_xau']:
                    closes = [c['close'] for c in data['candles_xau'][-20:]]
                    if len(closes) >= 20:
                        sma20 = sum(closes) / len(closes)
                        data['indicators']['xau_sma20'] = sma20
                        data['indicators']['xau_current'] = closes[-1]
                        data['indicators']['xau_change'] = closes[-1] - closes[-2] if len(closes) > 1 else 0
                        data['indicators']['xau_change_pct'] = (data['indicators']['xau_change'] / closes[-2] * 100) if len(closes) > 1 and closes[-2] != 0 else 0
                
            except Exception as e:
                data['error'] = str(e)
                print(f"Error obteniendo datos MT5: {e}")
        
        return data

    def generate_html(self):
        """Generar HTML del dashboard"""
        return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 TradingView-Style Dashboard - AlgoTrader v3.0</title>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        :root {
            --bg-primary: #0f1115;
            --bg-secondary: #161b22;
            --fg-primary: #e5e7eb;
            --fg-secondary: #9ca3af;
            --border-color: #30363d;
            --accent-green: #26a69a;
            --accent-red: #ef5350;
            --accent-blue: #2196f3;
            --grid-color: #252932;
        }

        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --fg-primary: #111827;
            --fg-secondary: #6b7280;
            --border-color: #e5e7eb;
            --accent-green: #10b981;
            --accent-red: #f43f5e;
            --accent-blue: #3b82f6;
            --grid-color: #e5e7eb;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--fg-primary);
            overflow-x: hidden;
        }

        .dashboard {
            display: grid;
            grid-template-columns: 300px 1fr;
            grid-template-rows: 60px 1fr;
            height: 100vh;
            gap: 1px;
            background: var(--border-color);
        }

        .header {
            grid-column: 1 / -1;
            background: var(--bg-secondary);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .header h1 {
            font-size: 18px;
            font-weight: 600;
        }

        .theme-toggle {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--fg-primary);
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }

        .theme-toggle:hover {
            background: var(--bg-primary);
        }

        .sidebar {
            background: var(--bg-secondary);
            padding: 20px;
            overflow-y: auto;
        }

        .main-content {
            background: var(--bg-primary);
            display: grid;
            grid-template-rows: 1fr 200px;
            gap: 1px;
        }

        .charts-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1px;
            background: var(--border-color);
        }

        .chart-panel {
            background: var(--bg-primary);
            position: relative;
            min-height: 300px;
        }

        .chart-header {
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 10;
            background: rgba(15, 17, 21, 0.8);
            padding: 8px 12px;
            border-radius: 4px;
            backdrop-filter: blur(10px);
        }

        .chart-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .chart-price {
            font-size: 12px;
            color: var(--fg-secondary);
        }

        .volume-panel {
            background: var(--bg-primary);
            border-top: 1px solid var(--border-color);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
        }

        .stat-label {
            font-size: 12px;
            color: var(--fg-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .stat-value {
            font-size: 18px;
            font-weight: 600;
        }

        .stat-change {
            font-size: 12px;
            margin-top: 4px;
        }

        .positive { color: var(--accent-green); }
        .negative { color: var(--accent-red); }

        .positions-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .positions-table th,
        .positions-table td {
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid var(--border-color);
            font-size: 12px;
        }

        .positions-table th {
            background: var(--bg-primary);
            font-weight: 600;
            color: var(--fg-secondary);
        }

        .tv-tooltip {
            position: absolute;
            display: none;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            backdrop-filter: blur(10px);
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-online { background: var(--accent-green); }
        .status-offline { background: var(--accent-red); }

        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
                grid-template-rows: 60px auto 1fr;
            }
            
            .charts-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body data-theme="dark">
    <div class="dashboard">
        <header class="header">
            <h1>🚀 TradingView-Style Dashboard v3.0</h1>
            <button class="theme-toggle" id="theme-toggle" aria-pressed="true">🌙 Tema Oscuro</button>
        </header>

        <aside class="sidebar">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Estado MT5</div>
                    <div class="stat-value">
                        <span class="status-indicator" id="mt5-status"></span>
                        <span id="mt5-text">Conectando...</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-label">Balance</div>
                    <div class="stat-value" id="balance">$0.00</div>
                    <div class="stat-change" id="equity"></div>
                </div>

                <div class="stat-card">
                    <div class="stat-label">Posiciones</div>
                    <div class="stat-value" id="positions-count">0</div>
                    <div class="stat-change" id="total-profit"></div>
                </div>
            </div>

            <table class="positions-table" id="positions-table">
                <thead>
                    <tr>
                        <th>Símbolo</th>
                        <th>Tipo</th>
                        <th>Volumen</th>
                        <th>P&L</th>
                    </tr>
                </thead>
                <tbody id="positions-tbody">
                </tbody>
            </table>
        </aside>

        <main class="main-content">
            <div class="charts-container">
                <div class="chart-panel">
                    <div class="chart-header">
                        <div class="chart-title">BTC/USD</div>
                        <div class="chart-price" id="btc-price">Loading...</div>
                    </div>
                    <div id="btc-chart" style="height: 100%;"></div>
                </div>

                <div class="chart-panel">
                    <div class="chart-header">
                        <div class="chart-title">XAU/USD</div>
                        <div class="chart-price" id="xau-price">Loading...</div>
                    </div>
                    <div id="xau-chart" style="height: 100%;"></div>
                </div>
            </div>

            <div class="volume-panel">
                <div id="volume-chart" style="height: 100%;"></div>
            </div>
        </main>
    </div>

    <div class="tv-tooltip" id="tooltip" role="tooltip" aria-hidden="true"></div>

    <script>
        // Variables globales
        let btcChart, xauChart, volumeChart;
        let btcCandleSeries, btcSmaSeries;
        let xauCandleSeries, xauSmaSeries;
        let volumeSeries;
        let currentData = {};

        // Configuración de tema
        const darkTheme = {
            layout: {
                background: { type: 'solid', color: '#0f1115' },
                textColor: '#e5e7eb',
            },
            grid: {
                vertLines: { color: '#252932' },
                horzLines: { color: '#252932' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#30363d',
            },
            timeScale: {
                borderColor: '#30363d',
            },
        };

        const lightTheme = {
            layout: {
                background: { type: 'solid', color: '#ffffff' },
                textColor: '#111827',
            },
            grid: {
                vertLines: { color: '#e5e7eb' },
                horzLines: { color: '#e5e7eb' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#e5e7eb',
            },
            timeScale: {
                borderColor: '#e5e7eb',
            },
        };

        // Inicializar gráficos
        function initCharts() {
            // Gráfico BTC
            btcChart = LightweightCharts.createChart(document.getElementById('btc-chart'), {
                ...darkTheme,
                width: document.getElementById('btc-chart').clientWidth,
                height: document.getElementById('btc-chart').clientHeight,
            });

            btcCandleSeries = btcChart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });

            btcSmaSeries = btcChart.addLineSeries({
                color: '#2196f3',
                lineWidth: 2,
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // Gráfico XAU
            xauChart = LightweightCharts.createChart(document.getElementById('xau-chart'), {
                ...darkTheme,
                width: document.getElementById('xau-chart').clientWidth,
                height: document.getElementById('xau-chart').clientHeight,
            });

            xauCandleSeries = xauChart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });

            xauSmaSeries = xauChart.addLineSeries({
                color: '#2196f3',
                lineWidth: 2,
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // Gráfico de volumen
            volumeChart = LightweightCharts.createChart(document.getElementById('volume-chart'), {
                ...darkTheme,
                width: document.getElementById('volume-chart').clientWidth,
                height: 200,
            });

            volumeSeries = volumeChart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '',
            });

            // Sincronizar crosshair
            syncCharts([btcChart, xauChart, volumeChart]);

            // Tooltips
            setupTooltips();

            // Resize observer
            setupResizeObserver();
        }

        // Sincronizar gráficos
        function syncCharts(charts) {
            charts.forEach((chart, index) => {
                chart.subscribeCrosshairMove(param => {
                    if (!param.time) return;
                    
                    charts.forEach((otherChart, otherIndex) => {
                        if (index !== otherIndex) {
                            otherChart.moveCrosshair(param);
                        }
                    });
                });
            });
        }

        // Configurar tooltips
        function setupTooltips() {
            const tooltip = document.getElementById('tooltip');

            [btcChart, xauChart].forEach((chart, index) => {
                chart.subscribeCrosshairMove(param => {
                    if (!param.time || !param.seriesPrices) {
                        tooltip.style.display = 'none';
                        return;
                    }

                    const symbol = index === 0 ? 'BTC/USD' : 'XAU/USD';
                    const candleData = param.seriesPrices.get(index === 0 ? btcCandleSeries : xauCandleSeries);
                    
                    if (candleData) {
                        const date = new Date(param.time * 1000);
                        tooltip.innerHTML = `
                            <div><strong>${symbol}</strong></div>
                            <div>Fecha: ${date.toLocaleDateString()}</div>
                            <div>O: ${candleData.open?.toFixed(2)}</div>
                            <div>H: ${candleData.high?.toFixed(2)}</div>
                            <div>L: ${candleData.low?.toFixed(2)}</div>
                            <div>C: ${candleData.close?.toFixed(2)}</div>
                        `;

                        tooltip.style.display = 'block';
                        tooltip.style.left = param.point.x + 'px';
                        tooltip.style.top = param.point.y + 'px';
                    }
                });
            });
        }

        // Configurar resize observer
        function setupResizeObserver() {
            const resizeObserver = new ResizeObserver(entries => {
                for (let entry of entries) {
                    const { width, height } = entry.contentRect;
                    if (entry.target.id === 'btc-chart') {
                        btcChart.applyOptions({ width, height });
                    } else if (entry.target.id === 'xau-chart') {
                        xauChart.applyOptions({ width, height });
                    } else if (entry.target.id === 'volume-chart') {
                        volumeChart.applyOptions({ width, height });
                    }
                }
            });

            resizeObserver.observe(document.getElementById('btc-chart'));
            resizeObserver.observe(document.getElementById('xau-chart'));
            resizeObserver.observe(document.getElementById('volume-chart'));
        }

        // Toggle tema
        function toggleTheme() {
            const body = document.body;
            const button = document.getElementById('theme-toggle');
            const isDark = body.getAttribute('data-theme') === 'dark';
            
            const newTheme = isDark ? 'light' : 'dark';
            const themeConfig = isDark ? lightTheme : darkTheme;
            
            body.setAttribute('data-theme', newTheme);
            button.textContent = isDark ? '☀️ Tema Claro' : '🌙 Tema Oscuro';
            
            // Aplicar tema a gráficos
            btcChart.applyOptions(themeConfig);
            xauChart.applyOptions(themeConfig);
            volumeChart.applyOptions(themeConfig);
        }

        // Actualizar datos
        function updateData(data) {
            currentData = data;

            // Actualizar stats
            document.getElementById('mt5-status').className = 
                'status-indicator ' + (data.mt5_connected ? 'status-online' : 'status-offline');
            document.getElementById('mt5-text').textContent = 
                data.mt5_connected ? 'Conectado' : 'Desconectado';

            if (data.account) {
                document.getElementById('balance').textContent = 
                    `$${data.account.balance?.toFixed(2) || '0.00'}`;
                document.getElementById('equity').textContent = 
                    `Equity: $${data.account.equity?.toFixed(2) || '0.00'}`;
            }

            // Posiciones
            const positionsCount = data.positions?.length || 0;
            document.getElementById('positions-count').textContent = positionsCount;
            
            const totalProfit = data.positions?.reduce((sum, pos) => sum + (pos.profit || 0), 0) || 0;
            document.getElementById('total-profit').textContent = 
                `P&L: ${totalProfit >= 0 ? '+' : ''}$${totalProfit.toFixed(2)}`;
            document.getElementById('total-profit').className = 
                'stat-change ' + (totalProfit >= 0 ? 'positive' : 'negative');

            // Tabla de posiciones
            const tbody = document.getElementById('positions-tbody');
            tbody.innerHTML = '';
            data.positions?.forEach(pos => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${pos.symbol}</td>
                    <td>${pos.type}</td>
                    <td>${pos.volume}</td>
                    <td class="${pos.profit >= 0 ? 'positive' : 'negative'}">
                        ${pos.profit >= 0 ? '+' : ''}$${pos.profit.toFixed(2)}
                    </td>
                `;
            });

            // Actualizar gráficos
            if (data.candles_btc?.length) {
                btcCandleSeries.setData(data.candles_btc);
                
                // SMA para BTC
                const btcSma = calculateSMA(data.candles_btc, 20);
                btcSmaSeries.setData(btcSma);

                // Actualizar precio BTC
                const lastBtc = data.candles_btc[data.candles_btc.length - 1];
                const change = data.indicators?.btc_change || 0;
                document.getElementById('btc-price').innerHTML = `
                    $${lastBtc.close.toFixed(2)} 
                    <span class="${change >= 0 ? 'positive' : 'negative'}">
                        ${change >= 0 ? '+' : ''}${change.toFixed(2)} (${(data.indicators?.btc_change_pct || 0).toFixed(2)}%)
                    </span>
                `;
            }

            if (data.candles_xau?.length) {
                xauCandleSeries.setData(data.candles_xau);
                
                // SMA para XAU
                const xauSma = calculateSMA(data.candles_xau, 20);
                xauSmaSeries.setData(xauSma);

                // Actualizar precio XAU
                const lastXau = data.candles_xau[data.candles_xau.length - 1];
                const change = data.indicators?.xau_change || 0;
                document.getElementById('xau-price').innerHTML = `
                    $${lastXau.close.toFixed(2)} 
                    <span class="${change >= 0 ? 'positive' : 'negative'}">
                        ${change >= 0 ? '+' : ''}${change.toFixed(2)} (${(data.indicators?.xau_change_pct || 0).toFixed(2)}%)
                    </span>
                `;

                // Volumen (usando datos de BTC por simplicidad)
                const volumeData = data.candles_btc.map(candle => ({
                    time: candle.time,
                    value: candle.volume,
                    color: candle.close >= candle.open ? '#26a69a' : '#ef5350'
                }));
                volumeSeries.setData(volumeData);
            }
        }

        // Calcular SMA
        function calculateSMA(candles, period) {
            const smaData = [];
            for (let i = period - 1; i < candles.length; i++) {
                const sum = candles.slice(i - period + 1, i + 1).reduce((acc, candle) => acc + candle.close, 0);
                smaData.push({
                    time: candles[i].time,
                    value: sum / period
                });
            }
            return smaData;
        }

        // Cargar datos
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                updateData(data);
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        // Inicialización
        document.addEventListener('DOMContentLoaded', () => {
            initCharts();
            loadData();
            
            // Auto-refresh cada 5 segundos
            setInterval(loadData, 5000);
            
            // Toggle tema
            document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
        });
    </script>
</body>
</html>
        """

    def run(self):
        """Ejecutar el servidor"""
        class CustomHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
            def __init__(self, *args, dashboard_server=None, **kwargs):
                self.dashboard_server = dashboard_server
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(self.dashboard_server.generate_html().encode('utf-8'))
                    
                elif self.path == '/api/data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    data = self.dashboard_server.get_system_data()
                    self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
                    
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'Not Found')

            def log_message(self, format, *args):
                pass  # Suprimir logs del servidor

        def handler(*args, **kwargs):
            return CustomHTTPRequestHandler(*args, dashboard_server=self, **kwargs)
        
        try:
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                print(f"TradingView-Style Dashboard iniciado en puerto {self.port}")
                print(f"Acceso: http://localhost:{self.port}")
                print("Funciones:")
                print("   - Graficos TradingView Lightweight Charts")
                print("   - Sincronizacion de crosshair entre paneles")
                print("   - Tooltips interactivos")
                print("   - Tema oscuro/claro")
                print("   - Auto-refresh cada 5 segundos")
                print("   - Datos en tiempo real desde MT5")
                print("\nPresiona Ctrl+C para detener")
                
                # Abrir navegador automáticamente
                threading.Timer(2.0, lambda: webbrowser.open(f'http://localhost:{self.port}')).start()
                
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\nDashboard detenido por el usuario")
        except Exception as e:
            print(f"Error iniciando dashboard: {e}")

if __name__ == "__main__":
    dashboard = TradingViewDashboardServer(port=8510)
    dashboard.run()