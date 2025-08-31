"""
Sistema de Health Checks
Monitorea la salud de todos los componentes del sistema
"""
import os
import time
import psutil
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
import requests

# Importaciones locales
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class HealthCheck:
    """Health check individual para un componente"""
    
    def __init__(self, name: str, check_function, critical: bool = False):
        """
        Args:
            name: Nombre del componente
            check_function: Función que retorna (bool, mensaje)
            critical: Si es crítico para el funcionamiento
        """
        self.name = name
        self.check_function = check_function
        self.critical = critical
        self.last_check = None
        self.last_status = None
        self.last_message = None
        self.consecutive_failures = 0
    
    def check(self) -> Tuple[bool, str]:
        """Ejecutar health check"""
        try:
            status, message = self.check_function()
            
            # Actualizar estado
            self.last_check = datetime.now()
            self.last_status = status
            self.last_message = message
            
            if status:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
            
            return status, message
            
        except Exception as e:
            self.consecutive_failures += 1
            message = f"Error en check: {str(e)}"
            self.last_status = False
            self.last_message = message
            return False, message

class HealthMonitor:
    """Monitor de salud del sistema completo"""
    
    def __init__(self):
        self.checks = {}
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        self.monitoring_interval = 60  # segundos
        
        # Registrar checks por defecto
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Registrar health checks por defecto"""
        
        # Sistema
        self.add_check(
            'system_resources',
            self._check_system_resources,
            critical=True
        )
        
        # MT5
        self.add_check(
            'mt5_connection',
            self._check_mt5,
            critical=True
        )
        
        # APIs
        self.add_check(
            'twelvedata_api',
            self._check_twelvedata,
            critical=False
        )
        
        # Ollama/IA
        self.add_check(
            'ollama_service',
            self._check_ollama,
            critical=False
        )
        
        # Telegram
        self.add_check(
            'telegram_bot',
            self._check_telegram,
            critical=False
        )
        
        # Base de datos
        self.add_check(
            'database',
            self._check_database,
            critical=False
        )
        
        # Archivos de log
        self.add_check(
            'log_files',
            self._check_log_files,
            critical=False
        )
    
    def add_check(self, name: str, check_function, critical: bool = False):
        """Añadir un health check"""
        self.checks[name] = HealthCheck(name, check_function, critical)
    
    def check_all(self) -> Dict:
        """Ejecutar todos los health checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'healthy': True,
            'checks': {},
            'issues': [],
            'warnings': []
        }
        
        for name, check in self.checks.items():
            status, message = check.check()
            
            results['checks'][name] = {
                'status': 'healthy' if status else 'unhealthy',
                'message': message,
                'critical': check.critical,
                'consecutive_failures': check.consecutive_failures
            }
            
            if not status:
                if check.critical:
                    results['healthy'] = False
                    results['issues'].append(f"{name}: {message}")
                else:
                    results['warnings'].append(f"{name}: {message}")
        
        return results
    
    def start_monitoring(self, interval: int = 60):
        """Iniciar monitoreo continuo"""
        self.monitoring_interval = interval
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("El monitoreo ya está en ejecución")
            return
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Monitoreo de salud iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self):
        """Detener monitoreo continuo"""
        if self.monitoring_thread:
            self.stop_monitoring.set()
            self.monitoring_thread.join(timeout=5)
            logger.info("Monitoreo de salud detenido")
    
    def _monitoring_loop(self):
        """Loop de monitoreo continuo"""
        while not self.stop_monitoring.is_set():
            try:
                results = self.check_all()
                
                # Log de resultados
                if not results['healthy']:
                    logger.error(f"Sistema no saludable: {results['issues']}")
                elif results['warnings']:
                    logger.warning(f"Advertencias de salud: {results['warnings']}")
                else:
                    logger.debug("Todos los health checks pasaron")
                
                # Guardar resultados
                self._save_health_status(results)
                
            except Exception as e:
                logger.error(f"Error en monitoreo de salud: {e}")
            
            # Esperar hasta el siguiente check
            self.stop_monitoring.wait(self.monitoring_interval)
    
    def _save_health_status(self, results: Dict):
        """Guardar estado de salud a archivo"""
        try:
            status_file = Path("data/health_status.json")
            status_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(status_file, 'w') as f:
                json.dump(results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error guardando estado de salud: {e}")
    
    # Health checks específicos
    
    def _check_system_resources(self) -> Tuple[bool, str]:
        """Verificar recursos del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                return False, f"CPU muy alta: {cpu_percent}%"
            
            # Memoria
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return False, f"Memoria muy alta: {memory.percent}%"
            
            # Disco
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                return False, f"Disco casi lleno: {disk.percent}%"
            
            return True, f"CPU: {cpu_percent}%, Mem: {memory.percent}%, Disk: {disk.percent}%"
            
        except Exception as e:
            return False, f"Error verificando recursos: {e}"
    
    def _check_mt5(self) -> Tuple[bool, str]:
        """Verificar conexión con MT5"""
        try:
            # Verificar si MT5 está inicializado
            terminal_info = mt5.terminal_info()
            if not terminal_info:
                return False, "MT5 no conectado"
            
            # Verificar cuenta
            account_info = mt5.account_info()
            if not account_info:
                return False, "No se puede obtener info de cuenta"
            
            return True, f"Conectado a {account_info.server}"
            
        except Exception as e:
            return False, f"Error MT5: {e}"
    
    def _check_twelvedata(self) -> Tuple[bool, str]:
        """Verificar API de TwelveData"""
        try:
            api_key = os.getenv('TWELVEDATA_API_KEY')
            if not api_key:
                return False, "API key no configurada"
            
            # Hacer ping a la API
            url = "https://api.twelvedata.com/api_usage"
            params = {"apikey": api_key}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    used = data.get('current_usage', 0)
                    limit = data.get('plan_limit', 0)
                    return True, f"API OK ({used}/{limit} llamadas)"
            
            return False, f"API respondió con código {response.status_code}"
            
        except requests.Timeout:
            return False, "Timeout conectando a TwelveData"
        except Exception as e:
            return False, f"Error TwelveData: {e}"
    
    def _check_ollama(self) -> Tuple[bool, str]:
        """Verificar servicio Ollama"""
        try:
            base_url = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/v1')
            
            # Quitar /v1 para el health check
            health_url = base_url.replace('/v1', '/api/tags')
            
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [m.get('name') for m in models]
                return True, f"Ollama OK ({len(models)} modelos)"
            
            return False, f"Ollama respondió con código {response.status_code}"
            
        except requests.ConnectionError:
            return False, "Ollama no está ejecutándose"
        except Exception as e:
            return False, f"Error Ollama: {e}"
    
    def _check_telegram(self) -> Tuple[bool, str]:
        """Verificar bot de Telegram"""
        try:
            token = os.getenv('TELEGRAM_TOKEN')
            if not token:
                return False, "Token no configurado"
            
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_name = data.get('result', {}).get('username')
                    return True, f"Bot OK (@{bot_name})"
            
            return False, "No se pudo verificar el bot"
            
        except Exception as e:
            return False, f"Error Telegram: {e}"
    
    def _check_database(self) -> Tuple[bool, str]:
        """Verificar base de datos"""
        try:
            db_path = Path("data/trading.db")
            
            if not db_path.exists():
                return False, "Base de datos no existe"
            
            # Verificar tamaño
            size_mb = db_path.stat().st_size / (1024 * 1024)
            
            if size_mb > 1000:  # Más de 1GB
                return False, f"Base de datos muy grande: {size_mb:.1f}MB"
            
            # Verificar que se puede abrir
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            return True, f"DB OK ({table_count} tablas, {size_mb:.1f}MB)"
            
        except Exception as e:
            return False, f"Error DB: {e}"
    
    def _check_log_files(self) -> Tuple[bool, str]:
        """Verificar archivos de log"""
        try:
            log_dir = Path("logs")
            
            if not log_dir.exists():
                return False, "Directorio de logs no existe"
            
            # Verificar tamaño total
            total_size = sum(f.stat().st_size for f in log_dir.glob("**/*") if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            if size_mb > 500:  # Más de 500MB
                return False, f"Logs muy grandes: {size_mb:.1f}MB"
            
            # Verificar archivos recientes
            log_files = list(log_dir.glob("*.log"))
            if not log_files:
                return False, "No hay archivos de log"
            
            return True, f"Logs OK ({len(log_files)} archivos, {size_mb:.1f}MB)"
            
        except Exception as e:
            return False, f"Error logs: {e}"

# Monitor global
health_monitor = HealthMonitor()
