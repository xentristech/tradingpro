#!/usr/bin/env python3
"""
CHART SIMULATION REVISADO
========================
Revisión del elemento gráfico chart simulation
Implementación funcional y optimizada del chart avanzado
"""

import http.server
import socketserver
import json
import threading
import time
import random
from datetime import datetime, timedelta

print("[CHART REVIEW] Iniciando revisión del chart simulation...")

class ChartSimulationReviewed:
    def __init__(self, port=8516):
        self.port = port
        self.price_data = []
        self.is_running = False
        print(f"[CHART] Inicializado en puerto {port}")
        
        # Generar datos base
        self.generate_base_data()
        
    def generate_base_data(self):
        """Generar datos base para simulación"""
        base_price = 2650.50  # XAUUSD
        
        for i in range(50):
            timestamp = datetime.now() - timedelta(minutes=50-i)
            price = base_price + random.uniform(-20, 20)
            volume = random.randint(1000, 5000)
            
            self.price_data.append({
                'time': timestamp.strftime("%H:%M"),
                'price': round(price, 2),
                'volume': volume,
                'change': random.uniform(-2, 2)
            })
            
            base_price = price
            
        print(f"[DATA] Generados {len(self.price_data)} puntos de datos")
        
    def get_chart_html(self):
        """Generar HTML del chart simulación"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chart Simulation Reviewed</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 10px;
            border: 1px solid #333;
        }}
        .chart-container {{
            background: #111;
            border-radius: 10px;
            padding: 20px;
            border: 2px solid #333;
            margin-bottom: 20px;
        }}
        #priceChart {{
            width: 100%;
            height: 400px;
            background: #000;
            border: 1px solid #444;
            border-radius: 5px;
        }}
        .controls {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }}
        .control-btn {{
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }}
        .control-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }}
        .status-panel {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .status-card {{
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #444;
            text-align: center;
        }}
        .status-value {{
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .updating {{
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CHART SIMULATION REVIEWED</h1>
            <p>Revisión del elemento gráfico - Chart simulation avanzado</p>
            <p><strong>Tiempo real</strong> | <strong>Datos dinámicos</strong> | <strong>Canvas HTML5</strong></p>
        </div>
        
        <div class="chart-container">
            <h3>Grafico de Precios en Tiempo Real</h3>
            <canvas id="priceChart"></canvas>
            
            <div class="controls">
                <button class="control-btn" onclick="toggleAnimation()">Toggle Animacion</button>
                <button class="control-btn" onclick="resetChart()">Reset Chart</button>
                <button class="control-btn" onclick="changeTimeframe()">Cambiar Timeframe</button>
            </div>
        </div>
        
        <div class="status-panel">
            <div class="status-card">
                <div>Precio Actual</div>
                <div class="status-value updating" id="currentPrice">$2,650.50</div>
            </div>
            <div class="status-card">
                <div>Cambio</div>
                <div class="status-value" id="priceChange">+1.25</div>
            </div>
            <div class="status-card">
                <div>Volumen</div>
                <div class="status-value" id="volume">2,450</div>
            </div>
            <div class="status-card">
                <div>Última Actualización</div>
                <div class="status-value" id="lastUpdate">--:--</div>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('priceChart');
        const ctx = canvas.getContext('2d');
        
        // Configurar canvas
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        
        let priceData = {json.dumps(self.price_data)};
        let animationRunning = true;
        let currentIndex = 0;
        
        // Función principal de dibujo
        function drawChart() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Grid de fondo
            drawGrid();
            
            // Dibujar línea de precio
            drawPriceLine();
            
            // Dibujar puntos de datos
            drawDataPoints();
            
            // Actualizar información
            updateStatusPanel();
        }}
        
        function drawGrid() {{
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 1;
            
            // Líneas verticales
            for (let i = 0; i < 10; i++) {{
                const x = (canvas.width / 10) * i;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}
            
            // Líneas horizontales
            for (let i = 0; i < 8; i++) {{
                const y = (canvas.height / 8) * i;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}
        }}
        
        function drawPriceLine() {{
            if (priceData.length < 2) return;
            
            ctx.strokeStyle = '#4CAF50';
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            const maxPrice = Math.max(...priceData.map(d => d.price));
            const minPrice = Math.min(...priceData.map(d => d.price));
            const priceRange = maxPrice - minPrice || 1;
            
            priceData.forEach((point, index) => {{
                if (index > currentIndex) return;
                
                const x = (canvas.width / (priceData.length - 1)) * index;
                const y = canvas.height - ((point.price - minPrice) / priceRange) * canvas.height;
                
                if (index === 0) {{
                    ctx.moveTo(x, y);
                }} else {{
                    ctx.lineTo(x, y);
                }}
            }});
            
            ctx.stroke();
        }}
        
        function drawDataPoints() {{
            const maxPrice = Math.max(...priceData.map(d => d.price));
            const minPrice = Math.min(...priceData.map(d => d.price));
            const priceRange = maxPrice - minPrice || 1;
            
            priceData.forEach((point, index) => {{
                if (index > currentIndex) return;
                
                const x = (canvas.width / (priceData.length - 1)) * index;
                const y = canvas.height - ((point.price - minPrice) / priceRange) * canvas.height;
                
                // Punto actual más grande
                if (index === currentIndex) {{
                    ctx.fillStyle = '#FF6B35';
                    ctx.beginPath();
                    ctx.arc(x, y, 6, 0, 2 * Math.PI);
                    ctx.fill();
                }} else {{
                    ctx.fillStyle = '#4CAF50';
                    ctx.beginPath();
                    ctx.arc(x, y, 3, 0, 2 * Math.PI);
                    ctx.fill();
                }}
            }});
        }}
        
        function updateStatusPanel() {{
            if (currentIndex >= priceData.length) return;
            
            const current = priceData[currentIndex];
            document.getElementById('currentPrice').textContent = `$` + current.price.toLocaleString();
            document.getElementById('priceChange').textContent = current.change > 0 ? `+$` + current.change.toFixed(2) : `$` + current.change.toFixed(2);
            document.getElementById('volume').textContent = current.volume.toLocaleString();
            document.getElementById('lastUpdate').textContent = current.time;
            
            // Cambiar color según el cambio
            const changeElement = document.getElementById('priceChange');
            changeElement.style.color = current.change > 0 ? '#4CAF50' : '#f44336';
        }}
        
        // Animación automática
        function animate() {{
            if (animationRunning) {{
                currentIndex = (currentIndex + 1) % priceData.length;
                drawChart();
            }}
            
            setTimeout(animate, 2000); // Actualizar cada 2 segundos
        }}
        
        // Controles
        function toggleAnimation() {{
            animationRunning = !animationRunning;
        }}
        
        function resetChart() {{
            currentIndex = 0;
            drawChart();
        }}
        
        function changeTimeframe() {{
            // Simular cambio de timeframe generando nuevos datos
            for (let i = 0; i < priceData.length; i++) {{
                priceData[i].price += Math.random() * 4 - 2;
                priceData[i].change = Math.random() * 4 - 2;
            }}
            drawChart();
        }}
        
        // Inicializar
        drawChart();
        animate();
        
        // Redimensionar canvas
        window.addEventListener('resize', () => {{
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            drawChart();
        }});
    </script>
</body>
</html>
        """

class ReviewHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, chart=None, **kwargs):
        self.chart = chart
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.chart.get_chart_html().encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass

def main():
    print("[REVIEW] Iniciando revisión del chart simulation...")
    
    chart = ChartSimulationReviewed(port=8516)
    
    def handler(*args, **kwargs):
        return ReviewHandler(*args, chart=chart, **kwargs)
    
    print("=" * 60)
    print(" CHART SIMULATION REVIEWED")
    print("=" * 60)
    print("[OK] Revision completada del elemento chart simulation")
    print("[OK] Chart funcional con datos dinamicos")
    print("[OK] Canvas HTML5 real con animaciones")
    print("[OK] Controles interactivos")
    print("[OK] Actualizacion en tiempo real")
    print(f"[URL] http://localhost:{chart.port}")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", chart.port), handler) as httpd:
            print(f"[SERVER] Chart Simulation ejecutándose en puerto {chart.port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOPPED] Chart Simulation detenido")
    except Exception as e:
        print(f"[ERROR] Error en Chart Simulation: {e}")

if __name__ == "__main__":
    main()