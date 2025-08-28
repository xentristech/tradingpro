"""
Charts Dashboard - Dashboard de Gráficas de Trading
Puerto: 8507
Especializado en mostrar gráficas generadas por TwelveData
"""
import http.server
import socketserver
import os
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class ChartsDashboard:
    def __init__(self, port=8507):
        self.port = port
        self.charts_dir = Path("charts")
        self.charts_dir.mkdir(exist_ok=True)
        
    def get_chart_data(self):
        """Obtener información de las gráficas disponibles"""
        try:
            # Buscar en ambos directorios de gráficos
            chart_files = []
            
            # Gráficos básicos
            basic_charts = list(self.charts_dir.glob("*.png"))
            chart_files.extend(basic_charts)
            
            # Gráficos avanzados
            advanced_dir = Path("advanced_charts")
            if advanced_dir.exists():
                advanced_charts = list(advanced_dir.glob("*.png"))
                chart_files.extend(advanced_charts)
            
            chart_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            charts = {
                'trading': [],
                'dashboard': [],
                'advanced': [],  # Nuevo tipo para gráficos avanzados
                'total': len(chart_files),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            for chart_file in chart_files:
                # Leer archivo y convertir a base64
                try:
                    with open(chart_file, 'rb') as f:
                        chart_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    chart_info = {
                        'filename': chart_file.name,
                        'data': chart_data,
                        'modified': datetime.fromtimestamp(chart_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'size': f"{chart_file.stat().st_size / 1024:.1f} KB"
                    }
                    
                    if chart_file.name.startswith('trading_'):
                        charts['trading'].append(chart_info)
                    elif chart_file.name.startswith('dashboard_'):
                        charts['dashboard'].append(chart_info)
                    elif chart_file.name.startswith(('candlestick_', 'ohlc_', 'line_', 'bars_')):
                        charts['advanced'].append(chart_info)
                        
                except Exception as e:
                    print(f"Error leyendo {chart_file}: {e}")
                    continue
            
            return charts
            
        except Exception as e:
            return {
                'trading': [],
                'dashboard': [],
                'advanced': [],
                'total': 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e)
            }
    
    def generate_html(self, charts_data):
        """Generar HTML del dashboard de gráficas"""
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="15">
    <title>LIVE Charts Dashboard - Dynamic TwelveData Graphs</title>
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
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.15);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #FFD700;
        }}
        
        .charts-section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8rem;
            font-weight: bold;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            border-left: 5px solid #FFD700;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
        }}
        
        .chart-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(5px);
        }}
        
        .chart-title {{
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #FFD700;
        }}
        
        .chart-meta {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 15px;
        }}
        
        .chart-image {{
            width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
        }}
        
        .chart-image:hover {{
            transform: scale(1.02);
            cursor: pointer;
        }}
        
        .no-charts {{
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            opacity: 0.8;
        }}
        
        .generate-btn {{
            display: inline-block;
            background: #FFD700;
            color: #333;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 15px;
            transition: background 0.3s ease;
        }}
        
        .generate-btn:hover {{
            background: #FFC107;
        }}
        
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
            margin-top: 40px;
            opacity: 0.7;
            font-size: 0.9rem;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
            cursor: pointer;
        }}
        
        .modal-content {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 95%;
            max-height: 95%;
        }}
        
        .modal img {{
            width: 100%;
            height: auto;
            border-radius: 10px;
        }}
        
        .close-modal {{
            position: absolute;
            top: 20px;
            right: 35px;
            color: #fff;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="auto-refresh">🔄 LIVE Auto-refresh: 15s</div>
    
    <div class="header">
        <h1>🚀 LIVE CHARTS DASHBOARD</h1>
        <p>📈 Dynamic TwelveData Trading Graphs - Puerto 8507</p>
        <p><strong>⏰ Última actualización LIVE:</strong> {charts_data['last_updated']}</p>
        <div style="margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px;">
            <span style="color: #00FF00;">🟢 SISTEMA DINÁMICO ACTIVO</span> | 
            <span style="color: #FFD700;">⚡ Actualizaciones automáticas cada 15-30s</span>
        </div>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{charts_data['total']}</div>
            <div>Total Gráficas</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(charts_data['trading'])}</div>
            <div>Trading Charts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(charts_data['dashboard'])}</div>
            <div>Dashboard Charts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(charts_data['advanced'])}</div>
            <div>Advanced Charts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">🔴 LIVE</div>
            <div>TwelveData API</div>
        </div>
    </div>
"""

        # Trading Charts Section
        if charts_data['trading']:
            html += f"""
    <div class="charts-section">
        <div class="section-title">📈 LIVE TRADING CHARTS - Análisis en Tiempo Real</div>
        <div class="charts-grid">"""
            
            for chart in charts_data['trading']:
                symbol = chart['filename'].replace('trading_', '').replace('.png', '').replace('_', '/')
                html += f"""
            <div class="chart-card">
                <div class="chart-title">{symbol}</div>
                <div class="chart-meta">
                    Actualizado: {chart['modified']} | Tamaño: {chart['size']}
                </div>
                <img src="data:image/png;base64,{chart['data']}" 
                     alt="{chart['filename']}" 
                     class="chart-image" 
                     onclick="openModal(this)">
            </div>"""
            
            html += """
        </div>
    </div>"""

        # Dashboard Charts Section
        if charts_data['dashboard']:
            html += f"""
    <div class="charts-section">
        <div class="section-title">📊 LIVE DASHBOARD CHARTS - Vista Rápida en Tiempo Real</div>
        <div class="charts-grid">"""
            
            for chart in charts_data['dashboard']:
                symbol = chart['filename'].replace('dashboard_', '').replace('.png', '').replace('_', '/')
                html += f"""
            <div class="chart-card">
                <div class="chart-title">{symbol}</div>
                <div class="chart-meta">
                    Actualizado: {chart['modified']} | Tamaño: {chart['size']}
                </div>
                <img src="data:image/png;base64,{chart['data']}" 
                     alt="{chart['filename']}" 
                     class="chart-image" 
                     onclick="openModal(this)">
            </div>"""
            
            html += """
        </div>
    </div>"""

        # Advanced Charts Section  
        if charts_data['advanced']:
            html += f"""
    <div class="charts-section">
        <div class="section-title">🔬 LIVE ADVANCED CHARTS - Velas, Barras y Lineales Dinámicos</div>
        <div class="charts-grid">"""
            
            for chart in charts_data['advanced']:
                # Determinar el tipo de gráfico con indicadores LIVE
                chart_type = chart['filename'].split('_')[0]
                type_names = {
                    'candlestick': '🕯️ Velas Japonesas LIVE',
                    'ohlc': '📊 Barras OHLC LIVE', 
                    'line': '📈 Gráfico Lineal LIVE',
                    'bars': '📉 Análisis de Barras LIVE'
                }
                type_name = type_names.get(chart_type, f'{chart_type} LIVE')
                
                symbol = chart['filename'].replace(f'{chart_type}_', '').replace('.png', '').replace('_', '/').split('_')[0]
                # Detectar si es un gráfico LIVE (contiene "_live")
                is_live = "_live" in chart['filename']
                live_indicator = "🔴 LIVE" if is_live else "📄 Estático"
                
                html += f"""
            <div class="chart-card">
                <div class="chart-title">{symbol} - {type_name}</div>
                <div class="chart-meta">
                    {live_indicator} | Tipo: {type_name} | Actualizado: {chart['modified']} | {chart['size']}
                </div>
                <img src="data:image/png;base64,{chart['data']}" 
                     alt="{chart['filename']}" 
                     class="chart-image" 
                     onclick="openModal(this)">
            </div>"""
            
            html += """
        </div>
    </div>"""

        # No charts message
        if charts_data['total'] == 0:
            html += """
    <div class="no-charts">
        <h3>No hay gráficas disponibles</h3>
        <p>Ejecuta el generador de gráficas para crear visualizaciones</p>
        <a href="#" class="generate-btn" onclick="generateCharts()">Generar Gráficas</a>
    </div>"""

        html += f"""
    <div class="footer">
        <p><strong>CHARTS DASHBOARD</strong> - Puerto 8507</p>
        <p>Gráficas generadas con TwelveData API</p>
        <p>Integrado con AlgoTrader MVP v3.0</p>
    </div>
    
    <!-- Modal para ver gráficas en grande -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="close-modal" onclick="closeModal()">&times;</span>
        <div class="modal-content">
            <img id="modalImage" src="">
        </div>
    </div>
    
    <script>
        function openModal(img) {{
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modal.style.display = 'block';
            modalImg.src = img.src;
        }}
        
        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}
        
        function generateCharts() {{
            alert('Sistema DINÁMICO activo! Los gráficos se actualizan automáticamente.\\n\\nPara control manual:\\n- python dynamic_charts.py\\n- python chart_scheduler.py');
        }}
        
        // Cerrar modal con ESC
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>"""
        
        return html

class ChartsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, dashboard=None, **kwargs):
        self.dashboard = dashboard
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            charts_data = self.dashboard.get_chart_data()
            html = self.dashboard.generate_html(charts_data)
            
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
    dashboard = ChartsDashboard()
    port = 8507
    
    def handler(*args, **kwargs):
        return ChartsHandler(*args, dashboard=dashboard, **kwargs)
    
    print(f"[CHARTS DASHBOARD] Iniciando en puerto {port}")
    print(f"URL: http://localhost:{port}")
    print(f"Directorio de gráficas: {dashboard.charts_dir.absolute()}")
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()