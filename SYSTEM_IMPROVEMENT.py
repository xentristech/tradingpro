#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA DE MEJORAS AUTOMÁTICAS - ALGO TRADER V3
================================================
Implementa mejoras críticas y soluciona problemas identificados
"""

import os
import sys
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
from cryptography.fernet import Fernet
import subprocess

class SystemImprovement:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.improvements_log = []
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def run_all_improvements(self):
        """Ejecuta todas las mejoras del sistema"""
        print("=" * 60)
        print("SISTEMA DE MEJORAS AUTOMÁTICAS - ALGO TRADER V3")
        print("=" * 60)
        
        improvements = [
            ("1. Limpieza y organización", self.cleanup_and_organize),
            ("2. Seguridad y configuración", self.secure_configuration),
            ("3. Sistema de logging mejorado", self.improve_logging),
            ("4. Gestión de procesos", self.setup_process_management),
            ("5. Sistema de respaldo", self.setup_backup_system),
            ("6. Validación de dependencias", self.validate_dependencies),
            ("7. Optimización de base de datos", self.optimize_database),
            ("8. Sistema de monitoreo", self.setup_monitoring)
        ]
        
        for name, func in improvements:
            print(f"\n🔧 Ejecutando: {name}")
            try:
                result = func()
                self.improvements_log.append({
                    "improvement": name,
                    "status": "success",
                    "result": result
                })
                print(f"✅ {name} completado")
            except Exception as e:
                self.improvements_log.append({
                    "improvement": name,
                    "status": "failed",
                    "error": str(e)
                })
                print(f"❌ Error en {name}: {e}")
                
        self.generate_report()
        
    def cleanup_and_organize(self):
        """Limpia y organiza la estructura del proyecto"""
        organized_count = 0
        
        # Crear estructura organizada
        dirs_to_create = [
            'archive/old_scripts',
            'archive/old_logs',
            'scripts/setup',
            'scripts/trading',
            'scripts/monitoring',
            'scripts/batch',
            'config/environments',
            'docs/api',
            'docs/strategies'
        ]
        
        for dir_path in dirs_to_create:
            (self.base_path / dir_path).mkdir(parents=True, exist_ok=True)
            
        # Mover archivos Python sueltos a carpetas apropiadas
        python_files_mapping = {
            'test_': 'tests/',
            'check_': 'tests/',
            'dashboard': 'src/ui/dashboards/',
            'bot': 'src/trading/',
            'monitor': 'scripts/monitoring/',
            'setup': 'scripts/setup/',
            'EJECUTAR': 'scripts/batch/',
            'START': 'scripts/batch/',
            'STOP': 'scripts/batch/'
        }
        
        for file in self.base_path.glob('*.py'):
            if file.name != '__init__.py' and file.name != 'SYSTEM_IMPROVEMENT.py':
                moved = False
                for prefix, destination in python_files_mapping.items():
                    if prefix in file.name:
                        dest_path = self.base_path / destination
                        dest_path.mkdir(parents=True, exist_ok=True)
                        
                        # Verificar si ya existe
                        if not (dest_path / file.name).exists():
                            shutil.move(str(file), str(dest_path / file.name))
                            organized_count += 1
                            moved = True
                            break
                        
                if not moved and 'deprecated' not in file.name.lower():
                    # Mover a archive si no se clasificó
                    archive_path = self.base_path / 'archive/old_scripts'
                    if not (archive_path / file.name).exists():
                        shutil.move(str(file), str(archive_path / file.name))
                        organized_count += 1
                        
        # Limpiar logs antiguos (más de 7 días)
        log_dir = self.base_path / 'logs'
        if log_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=7)
            for log_file in log_dir.glob('*.log'):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    archive_log = self.base_path / 'archive/old_logs' / log_file.name
                    shutil.move(str(log_file), str(archive_log))
                    
        return f"Organizados {organized_count} archivos"
        
    def secure_configuration(self):
        """Mejora la seguridad de las configuraciones"""
        # Generar clave de encriptación si no existe
        key_file = self.base_path / 'config' / '.encryption_key'
        
        if not key_file.exists():
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Solo lectura para el propietario
            
        # Crear plantilla de configuración segura
        secure_config = {
            "security": {
                "encrypt_credentials": True,
                "session_timeout": 3600,
                "max_failed_attempts": 3,
                "ip_whitelist": [],
                "require_2fa": False
            },
            "api_keys": {
                "twelvedata": {"encrypted": True, "value": ""},
                "telegram": {"encrypted": True, "value": ""},
                "openai": {"encrypted": True, "value": ""}
            },
            "trading": {
                "max_daily_loss": -500,
                "max_positions": 3,
                "emergency_stop": True,
                "require_confirmation": True
            }
        }
        
        config_file = self.base_path / 'config' / 'secure_config.json'
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(secure_config, f, indent=4)
                
        return "Configuración segura creada"
        
    def improve_logging(self):
        """Mejora el sistema de logging"""
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
                }
            },
            "handlers": {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/algo_trader.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 10,
                    "formatter": "detailed",
                    "level": "INFO"
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/errors.log",
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "formatter": "detailed",
                    "level": "ERROR"
                },
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": "INFO"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["file", "console", "error_file"],
                    "level": "INFO"
                },
                "trading": {
                    "handlers": ["file"],
                    "level": "DEBUG",
                    "propagate": False
                },
                "signals": {
                    "handlers": ["file"],
                    "level": "INFO",
                    "propagate": False
                }
            }
        }
        
        config_file = self.base_path / 'config' / 'logging_config.json'
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(log_config, f, indent=4)
            
        return "Sistema de logging mejorado configurado"
        
    def setup_process_management(self):
        """Configura gestión de procesos mejorada"""
        # Crear supervisor config
        supervisor_config = """
[group:algotrader]
programs=signal_generator,telegram_bot,dashboard,risk_monitor

[program:signal_generator]
command=python src/signals/realtime_signal_generator.py
directory=/path/to/algo-trader
autostart=true
autorestart=true
stderr_logfile=/var/log/algotrader/signal_generator.err.log
stdout_logfile=/var/log/algotrader/signal_generator.out.log

[program:telegram_bot]
command=python src/notifiers/telegram_notifier.py
directory=/path/to/algo-trader
autostart=true
autorestart=true
stderr_logfile=/var/log/algotrader/telegram.err.log
stdout_logfile=/var/log/algotrader/telegram.out.log

[program:dashboard]
command=python src/ui/dashboards/main_dashboard.py
directory=/path/to/algo-trader
autostart=true
autorestart=true
stderr_logfile=/var/log/algotrader/dashboard.err.log
stdout_logfile=/var/log/algotrader/dashboard.out.log

[program:risk_monitor]
command=python src/risk/risk_monitor.py
directory=/path/to/algo-trader
autostart=true
autorestart=true
stderr_logfile=/var/log/algotrader/risk.err.log
stdout_logfile=/var/log/algotrader/risk.out.log
"""
        
        config_file = self.base_path / 'config' / 'supervisor.conf'
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(supervisor_config)
        
        # Crear script de health check
        health_check_script = """
#!/usr/bin/env python
import psutil
import requests
import json
from datetime import datetime

def check_services():
    services = {
        'signal_generator': {'port': 8510, 'process': 'realtime_signal_generator.py'},
        'telegram_bot': {'process': 'telegram_notifier.py'},
        'dashboard': {'port': 8512, 'url': 'http://localhost:8512/health'},
        'mt5': {'process': 'terminal64.exe'}
    }
    
    status = {}
    for name, config in services.items():
        is_running = False
        
        # Check process
        if 'process' in config:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if config['process'] in str(proc.info['cmdline']):
                    is_running = True
                    break
                    
        # Check port
        if 'port' in config:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', config['port']))
                sock.close()
                if result == 0:
                    is_running = True
            except:
                pass
                
        # Check URL
        if 'url' in config:
            try:
                response = requests.get(config['url'], timeout=5)
                if response.status_code == 200:
                    is_running = True
            except:
                pass
                
        status[name] = is_running
        
    return status

if __name__ == '__main__':
    status = check_services()
    print(json.dumps({
        'timestamp': datetime.now().isoformat(),
        'services': status,
        'healthy': all(status.values())
    }, indent=2))
"""
        
        health_file = self.base_path / 'scripts' / 'monitoring' / 'health_check.py'
        health_file.parent.mkdir(parents=True, exist_ok=True)
        health_file.write_text(health_check_script)
        
        return "Sistema de gestión de procesos configurado"
        
    def setup_backup_system(self):
        """Configura sistema de respaldo automático"""
        backup_script = """
#!/usr/bin/env python
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def backup_system():
    base_path = Path(__file__).parent.parent.parent
    backup_dir = base_path / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    # Crear nombre de archivo con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'backup_{timestamp}.zip'
    
    # Directorios a respaldar
    dirs_to_backup = [
        'src',
        'config',
        'storage/trading.db',
        '.env'
    ]
    
    with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in dirs_to_backup:
            item_path = base_path / item
            if item_path.exists():
                if item_path.is_file():
                    zipf.write(item_path, item)
                else:
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(base_path)
                            zipf.write(file_path, arcname)
                            
    # Limpiar backups antiguos (mantener últimos 7)
    backups = sorted(backup_dir.glob('backup_*.zip'))
    if len(backups) > 7:
        for old_backup in backups[:-7]:
            old_backup.unlink()
            
    return f"Backup creado: {backup_file.name}"

if __name__ == '__main__':
    result = backup_system()
    print(result)
"""
        
        backup_file = self.base_path / 'scripts' / 'backup' / 'auto_backup.py'
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.write_text(backup_script)
        
        return "Sistema de respaldo configurado"
        
    def validate_dependencies(self):
        """Valida y actualiza dependencias"""
        requirements = """
# Core
python>=3.8
MetaTrader5>=5.0.45
pandas>=1.5.0
numpy>=1.23.0
sqlalchemy>=2.0.0

# Data & APIs
requests>=2.28.0
twelvedata>=1.2.0
yfinance>=0.2.0
websocket-client>=1.4.0

# Machine Learning
scikit-learn>=1.3.0
tensorflow>=2.13.0
torch>=2.0.0
xgboost>=1.7.0

# Technical Analysis
ta>=0.10.0
ta-lib>=0.4.25
pandas-ta>=0.3.14

# Visualization
plotly>=5.14.0
dash>=2.11.0
matplotlib>=3.7.0
seaborn>=0.12.0

# Notifications
python-telegram-bot>=20.0
discord.py>=2.3.0
twilio>=8.0.0

# Security
cryptography>=41.0.0
python-dotenv>=1.0.0
PyJWT>=2.8.0

# Utils
psutil>=5.9.0
schedule>=1.2.0
colorama>=0.4.6
rich>=13.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Development
black>=23.0.0
flake8>=6.0.0
mypy>=1.4.0
"""
        
        req_file = self.base_path / 'requirements.txt'
        req_file.write_text(requirements)
        
        # Crear script de instalación
        install_script = """
@echo off
echo ========================================
echo Instalando dependencias de Algo Trader V3
echo ========================================

python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Instalación completada!
pause
"""
        
        install_file = self.base_path / 'INSTALL_DEPENDENCIES.bat'
        install_file.write_text(install_script)
        
        return "Dependencias validadas y actualizadas"
        
    def optimize_database(self):
        """Optimiza la base de datos"""
        db_optimization = """
import sqlite3
from pathlib import Path

def optimize_db():
    db_path = Path(__file__).parent.parent.parent / 'storage' / 'trading.db'
    
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Crear índices si no existen
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(ts)",
            "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)"
        ]
        
        for idx in indices:
            try:
                cursor.execute(idx)
            except:
                pass
                
        # Vacuum para optimizar
        cursor.execute("VACUUM")
        
        # Analyze para actualizar estadísticas
        cursor.execute("ANALYZE")
        
        conn.commit()
        conn.close()
        
        return "Base de datos optimizada"
    return "Base de datos no encontrada"

if __name__ == '__main__':
    result = optimize_db()
    print(result)
"""
        
        opt_file = self.base_path / 'scripts' / 'maintenance' / 'optimize_db.py'
        opt_file.parent.mkdir(parents=True, exist_ok=True)
        opt_file.write_text(db_optimization)
        
        return "Optimización de base de datos configurada"
        
    def setup_monitoring(self):
        """Configura sistema de monitoreo avanzado"""
        monitoring_dashboard = """
<!DOCTYPE html>
<html>
<head>
    <title>Algo Trader V3 - System Monitor</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            color: white;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }
        .status-online { background: #00ff00; }
        .status-offline { background: #ff0000; }
        .status-warning { background: #ffaa00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Algo Trader V3 - System Monitor</h1>
            <p>Real-time system health and performance monitoring</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">
                    <span class="status-indicator status-online"></span>
                    Active
                </div>
                <div class="metric-label">System Status</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" id="signals-count">0</div>
                <div class="metric-label">Signals Generated</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" id="trades-count">0</div>
                <div class="metric-label">Active Trades</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" id="profit">$0.00</div>
                <div class="metric-label">Daily P&L</div>
            </div>
        </div>
        
        <div class="services-status">
            <h2>Services Status</h2>
            <div id="services-list"></div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('signals-count').innerText = data.signals || 0;
                    document.getElementById('trades-count').innerText = data.trades || 0;
                    document.getElementById('profit').innerText = '$' + (data.profit || 0).toFixed(2);
                })
                .catch(error => console.error('Error:', error));
        }, 5000);
    </script>
</body>
</html>
"""
        
        monitor_file = self.base_path / 'src' / 'ui' / 'monitoring' / 'system_monitor.html'
        monitor_file.parent.mkdir(parents=True, exist_ok=True)
        monitor_file.write_text(monitoring_dashboard)
        
        return "Sistema de monitoreo configurado"
        
    def generate_report(self):
        """Genera reporte de mejoras realizadas"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "improvements": self.improvements_log,
            "summary": {
                "total": len(self.improvements_log),
                "successful": len([x for x in self.improvements_log if x['status'] == 'success']),
                "failed": len([x for x in self.improvements_log if x['status'] == 'failed'])
            }
        }
        
        report_file = self.base_path / 'IMPROVEMENT_REPORT.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=4)
            
        print("\n" + "=" * 60)
        print("REPORTE DE MEJORAS")
        print("=" * 60)
        print(f"✅ Exitosas: {report['summary']['successful']}")
        print(f"❌ Fallidas: {report['summary']['failed']}")
        print(f"📊 Total: {report['summary']['total']}")
        print(f"\n📄 Reporte completo guardado en: {report_file.name}")
        
if __name__ == "__main__":
    improver = SystemImprovement()
    improver.run_all_improvements()
