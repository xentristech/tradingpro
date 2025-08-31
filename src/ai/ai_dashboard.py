"""
AI Dashboard - Dashboard de Análisis con Inteligencia Artificial
Puerto: 8505
Especializado en mostrar análisis IA y señales de Ollama
"""
import http.server
import socketserver
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import ollama

class AIDashboard:
    def __init__(self, port=8505):
        self.port = port
        self.log_files = {
            'ai_signals': 'logs/ai_signal_generator.log',
            'multi_account': 'logs/multi_account.log',
            'trade_validator': 'logs/trade_validator.log'
        }
    
    def check_ollama_status(self):
        """Verificar estado de Ollama"""
        try:
            client = ollama.Client()
            models = client.list()
            return {
                'status': 'ONLINE',
                'models': [model['name'] for model in models.get('models', [])],
                'count': len(models.get('models', []))
            }
        except Exception as e:
            return {
                'status': 'OFFLINE',
                'error': str(e),
                'models': [],
                'count': 0
            }
    
    def parse_log_file(self, log_path, hours=2):
        """Parsear archivo de log para extraer información de IA"""
        try:
            log_file = Path(log_path)
            if not log_file.exists():
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            entries = []
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line in lines[-200:]:  # Últimas 200 líneas
                try:
                    # Extraer timestamp
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        timestamp_str = timestamp_match.group(1)
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        if timestamp < cutoff_time:
                            continue
                    
                    # Detectar diferentes tipos de eventos IA
                    entry = None
                    
                    # Señales de Ollama
                    if '[OLLAMA]' in line:
                        match = re.search(r'\[OLLAMA\]\s+([A-Z/]+):\s+(BUY|SELL|HOLD)\s+\(Confianza:\s+([\d.]+)%\)', line)
                        if match:
                            entry = {
                                'timestamp': timestamp_str,
                                'type': 'AI_SIGNAL',
                                'symbol': match.group(1),
                                'action': match.group(2),
                                'confidence': float(match.group(3)),
                                'source': 'Ollama DeepSeek R1'
                            }
                    
                    # Validaciones de trade
                    elif 'TradeValidator' in line or 'trade_validator' in line:
                        if 'viable:' in line.lower():
                            entry = {
                                'timestamp': timestamp_str,
                                'type': 'TRADE_VALIDATION',
                                'content': line.strip(),
                                'source': 'Trade Validator'
                            }
                    
                    # Análisis de IA
                    elif 'analisis' in line.lower() or 'analysis' in line.lower():
                        entry = {
                            'timestamp': timestamp_str,
                            'type': 'AI_ANALYSIS',
                            'content': line.strip(),
                            'source': 'AI System'
                        }
                    
                    # Notificaciones enviadas
                    elif 'Notificacion enviada' in line or 'Notification sent' in line:
                        entry = {
                            'timestamp': timestamp_str,
                            'type': 'NOTIFICATION',
                            'content': line.strip(),
                            'source': 'Notification System'
                        }
                    
                    if entry:
                        entries.append(entry)
                        
                except Exception:
                    continue
            
            return sorted(entries, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            return [{'error': str(e), 'file': log_path}]
    
    def get_ai_signals(self):
        """Obtener señales de IA recientes"""
        signals = []
        
        # Parsear logs de AI Signal Generator
        ai_entries = self.parse_log_file(self.log_files['ai_signals'], hours=6)
        
        for entry in ai_entries:
            if entry.get('type') == 'AI_SIGNAL':
                signals.append({
                    'timestamp': entry['timestamp'],
                    'symbol': entry['symbol'],
                    'action': entry['action'],
                    'confidence': entry['confidence'],
                    'source': entry['source'],
                    'quality': 'HIGH' if entry['confidence'] >= 75 else 'MEDIUM' if entry['confidence'] >= 50 else 'LOW'
                })
        
        return signals[:10]  # Últimas 10 señales
    
    def get_validation_activity(self):
        """Obtener actividad de validación de trades"""
        validations = []
        
        # Parsear logs de Multi Account Manager y Trade Validator
        for log_name, log_path in self.log_files.items():
            entries = self.parse_log_file(log_path, hours=1)
            
            for entry in entries:
                if entry.get('type') in ['TRADE_VALIDATION', 'NOTIFICATION']:
                    validations.append({
                        'timestamp': entry['timestamp'],
                        'type': entry['type'],
                        'content': entry['content'][:100] + '...' if len(entry['content']) > 100 else entry['content'],
                        'source': log_name
                    })
        
        return sorted(validations, key=lambda x: x['timestamp'], reverse=True)[:15]
    
    def get_system_data(self):
        """Obtener todos los datos del sistema IA"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ollama': self.check_ollama_status(),
            'ai_signals': self.get_ai_signals(),
            'validations': self.get_validation_activity(),
            'stats': self.calculate_ai_stats()
        }
    
    def calculate_ai_stats(self):
        """Calcular estadísticas de IA"""
        signals = self.get_ai_signals()
        validations = self.get_validation_activity()
        
        # Estadísticas de señales
        signal_stats = {
            'total': len(signals),
            'buy_signals': len([s for s in signals if s['action'] == 'BUY']),
            'sell_signals': len([s for s in signals if s['action'] == 'SELL']),
            'hold_signals': len([s for s in signals if s['action'] == 'HOLD']),
            'high_confidence': len([s for s in signals if s['quality'] == 'HIGH']),
            'avg_confidence': sum([s['confidence'] for s in signals]) / len(signals) if signals else 0
        }
        
        # Estadísticas de validaciones
        validation_stats = {
            'total': len(validations),
            'trade_validations': len([v for v in validations if v['type'] == 'TRADE_VALIDATION']),
            'notifications': len([v for v in validations if v['type'] == 'NOTIFICATION'])
        }
        
        return {
            'signals': signal_stats,
            'validations': validation_stats
        }
    
    def generate_html(self, data):
        """Generar HTML del dashboard de IA"""
        
        ollama = data['ollama']
        signals = data['ai_signals']
        validations = data['validations']
        stats = data['stats']
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="10">
    <title>AI Dashboard - Análisis con IA</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2D1B69 0%, #11998e 100%);
            color: white;
            min-height: 100vh;
            padding: 15px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 25px;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        
        .status-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .status-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }}
        
        .status-title {{
            font-size: 1.2rem;
            font-weight: bold;
        }}
        
        .status-badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        
        .status-online {{ background: #4CAF50; }}
        .status-offline {{ background: #f44336; }}
        
        .ai-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: ai-pulse 3s infinite;
        }}
        
        .ai-online {{ background: #00ff88; }}
        .ai-offline {{ background: #ff4444; }}
        
        @keyframes ai-pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.7; transform: scale(1.1); }}
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-top: 15px;
        }}
        
        .stat-item {{
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 1.4rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.8rem;
            opacity: 0.8;
        }}
        
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 25px;
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
        }}
        
        .signals-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .signal-item {{
            background: rgba(0,0,0,0.2);
            margin-bottom: 10px;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid;
        }}
        
        .signal-buy {{ border-left-color: #4CAF50; }}
        .signal-sell {{ border-left-color: #f44336; }}
        .signal-hold {{ border-left-color: #FFC107; }}
        
        .signal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .signal-symbol {{
            font-weight: bold;
            font-size: 1.1rem;
        }}
        
        .signal-action {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        
        .action-buy {{ background: #4CAF50; color: white; }}
        .action-sell {{ background: #f44336; color: white; }}
        .action-hold {{ background: #FFC107; color: black; }}
        
        .signal-details {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        .confidence {{
            font-weight: bold;
        }}
        
        .confidence-high {{ color: #4CAF50; }}
        .confidence-medium {{ color: #FFC107; }}
        .confidence-low {{ color: #ff7043; }}
        
        .validation-item {{
            background: rgba(0,0,0,0.15);
            margin-bottom: 8px;
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #2196F3;
        }}
        
        .validation-header {{
            font-size: 0.85rem;
            opacity: 0.8;
            margin-bottom: 5px;
        }}
        
        .validation-content {{
            font-size: 0.9rem;
            line-height: 1.3;
        }}
        
        .validations-list {{
            max-height: 400px;
            overflow-y: auto;
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
        
        .footer {{
            text-align: center;
            margin-top: 25px;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
        
        .full-width {{
            grid-column: 1 / -1;
        }}
        
        .models-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        
        .model-badge {{
            background: rgba(33, 150, 243, 0.3);
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
            border: 1px solid rgba(33, 150, 243, 0.5);
        }}
    </style>
</head>
<body>
    <div class="auto-refresh">
        <div class="ai-indicator ai-{'online' if ollama['status'] == 'ONLINE' else 'offline'}"></div>
        AI Dashboard - 10s
    </div>
    
    <div class="header">
        <h1>AI DASHBOARD</h1>
        <p>Análisis con Inteligencia Artificial - Puerto 8505</p>
        <p><strong>Última actualización:</strong> {data['timestamp']}</p>
    </div>
    
    <div class="status-grid">
        <div class="status-card">
            <div class="status-header">
                <div class="status-title">
                    <div class="ai-indicator ai-{'online' if ollama['status'] == 'ONLINE' else 'offline'}"></div>
                    Estado Ollama
                </div>
                <span class="status-badge status-{'online' if ollama['status'] == 'ONLINE' else 'offline'}">{ollama['status']}</span>
            </div>
            <p><strong>Modelos disponibles:</strong> {ollama['count']}</p>
            {'<div class="models-list">' + ''.join([f'<span class="model-badge">{model}</span>' for model in ollama['models'][:5]]) + '</div>' if ollama['models'] else '<p style="opacity: 0.7;">Sin modelos disponibles</p>'}
            {f'<p style="color: #ff7043; margin-top: 10px;"><strong>Error:</strong> {ollama["error"]}</p>' if ollama['status'] == 'OFFLINE' and 'error' in ollama else ''}
        </div>
        
        <div class="status-card">
            <div class="status-header">
                <div class="status-title">Estadísticas de Señales</div>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{stats['signals']['total']}</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number positive">{stats['signals']['buy_signals']}</div>
                    <div class="stat-label">BUY</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number negative">{stats['signals']['sell_signals']}</div>
                    <div class="stat-label">SELL</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{stats['signals']['high_confidence']}</div>
                    <div class="stat-label">Alta Conf.</div>
                </div>
            </div>
            <p style="margin-top: 10px;"><strong>Confianza promedio:</strong> {stats['signals']['avg_confidence']:.1f}%</p>
        </div>
        
        <div class="status-card">
            <div class="status-header">
                <div class="status-title">Actividad del Sistema</div>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{stats['validations']['total']}</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{stats['validations']['trade_validations']}</div>
                    <div class="stat-label">Validaciones</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{stats['validations']['notifications']}</div>
                    <div class="stat-label">Notificaciones</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="section">
            <div class="section-title">
                <div class="ai-indicator ai-online"></div>
                Señales de IA Recientes
            </div>
            <div class="signals-list">"""
        
        if signals:
            for signal in signals:
                action_class = f"action-{signal['action'].lower()}"
                signal_class = f"signal-{signal['action'].lower()}"
                confidence_class = f"confidence-{signal['quality'].lower()}"
                
                html += f"""
                <div class="signal-item {signal_class}">
                    <div class="signal-header">
                        <span class="signal-symbol">{signal['symbol']}</span>
                        <span class="signal-action {action_class}">{signal['action']}</span>
                    </div>
                    <div class="signal-details">
                        <span>Confianza: <span class="confidence {confidence_class}">{signal['confidence']:.1f}%</span></span>
                        <span>{signal['timestamp'].split(' ')[1]}</span>
                    </div>
                    <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 5px;">
                        {signal['source']} - Calidad: {signal['quality']}
                    </div>
                </div>"""
        else:
            html += '<p style="text-align: center; opacity: 0.7; margin: 20px 0;">No hay señales recientes</p>'
        
        html += """
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Actividad de Validación</div>
            <div class="validations-list">"""
        
        if validations:
            for validation in validations:
                html += f"""
                <div class="validation-item">
                    <div class="validation-header">
                        {validation['timestamp'].split(' ')[1]} - {validation['source']} - {validation['type']}
                    </div>
                    <div class="validation-content">
                        {validation['content']}
                    </div>
                </div>"""
        else:
            html += '<p style="text-align: center; opacity: 0.7; margin: 20px 0;">No hay actividad de validación</p>'
        
        html += """
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p><strong>AI DASHBOARD</strong> - Puerto 8505</p>
        <p>Análisis con Ollama DeepSeek R1 y sistemas de validación IA</p>
    </div>
</body>
</html>"""
        
        return html

class AIHandler(http.server.SimpleHTTPRequestHandler):
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
    dashboard = AIDashboard()
    port = 8505
    
    def handler(*args, **kwargs):
        return AIHandler(*args, dashboard=dashboard, **kwargs)
    
    print(f"[AI DASHBOARD] Iniciando en puerto {port}")
    print(f"URL: http://localhost:{port}")
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()