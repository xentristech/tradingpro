"""
Dashboard Funcional - Dashboard que realmente funciona
==================================================
"""

import http.server
import socketserver
import base64
from datetime import datetime
from pathlib import Path

def main():
    port = 8507
    charts_dir = Path("advanced_charts")
    
    print("DASHBOARD FUNCIONAL - AlgoTrader MVP v3")
    print("="*40)
    print(f"Puerto: {port}")
    print(f"URL: http://localhost:{port}")
    
    # Verificar gráficos
    if charts_dir.exists():
        chart_files = list(charts_dir.glob("*.png"))
        live_charts = [f for f in chart_files if "_live" in f.name]
        print(f"Graficos totales: {len(chart_files)}")
        print(f"Graficos LIVE: {len(live_charts)}")
    else:
        print("Directorio advanced_charts no existe")
        chart_files = []
    
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/' or self.path == '/index.html':
                try:
                    # Generar HTML simple
                    current_time = datetime.now().strftime('%H:%M:%S')
                    charts = []
                    
                    if charts_dir.exists():
                        for chart_file in charts_dir.glob("*.png"):
                            try:
                                with open(chart_file, 'rb') as f:
                                    chart_data = base64.b64encode(f.read()).decode('utf-8')
                                
                                is_live = "_live" in chart_file.name
                                charts.append({
                                    'name': chart_file.name,
                                    'data': chart_data,
                                    'is_live': is_live
                                })
                            except Exception as e:
                                print(f"Error con {chart_file}: {e}")
                    
                    # HTML simple
                    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dashboard AlgoTrader</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="20">
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #333; color: white; padding: 20px; text-align: center; }}
        .live {{ color: red; font-weight: bold; }}
        .chart {{ background: white; margin: 20px 0; padding: 15px; border-radius: 5px; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dashboard Dinamico AlgoTrader</h1>
        <p>Actualizado: {current_time} | Graficos: {len(charts)} | Auto-refresh: 20s</p>
    </div>
"""
                    
                    if charts:
                        for chart in charts:
                            status = "<span class='live'>LIVE</span>" if chart['is_live'] else "Estatico"
                            html += f"""
    <div class="chart">
        <h3>{chart['name']} - {status}</h3>
        <img src="data:image/png;base64,{chart['data']}" alt="{chart['name']}">
    </div>
"""
                    else:
                        html += """
    <div class="chart">
        <h3>No hay graficos disponibles</h3>
        <p>Ejecuta: python test_visual_charts.py</p>
    </div>
"""
                    
                    html += "</body></html>"
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))
                    
                except Exception as e:
                    self.send_error(500, str(e))
            else:
                self.send_error(404)
        
        def log_message(self, format, *args):
            pass  # No mostrar logs
    
    if len(chart_files) == 0:
        print("\n[AVISO] No hay graficos. Ejecuta primero:")
        print("python test_visual_charts.py")
        print("\nLuego inicia el dashboard de nuevo")
        return
    
    try:
        print(f"\n[INICIANDO] Dashboard en http://localhost:{port}")
        print("Presiona Ctrl+C para detener")
        print("="*40)
        
        with socketserver.TCPServer(("", port), MyHandler) as httpd:
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n[DETENIDO]")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()