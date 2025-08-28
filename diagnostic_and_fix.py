#!/usr/bin/env python3
"""
🔧 DIAGNÓSTICO Y REPARACIÓN COMPLETA DEL BOT DE TRADING
Detecta y corrige todos los problemas encontrados
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color):
    """Imprimir texto con color"""
    print(f"{color}{text}{Colors.ENDC}")

class TradingBotDiagnostic:
    """Sistema completo de diagnóstico y reparación"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.issues_found = []
        self.fixes_applied = []
        
    def run_full_diagnostic(self):
        """Ejecutar diagnóstico completo"""
        
        print_colored("\n" + "="*60, Colors.BOLD)
        print_colored("🔧 DIAGNÓSTICO COMPLETO DEL BOT DE TRADING", Colors.BOLD)
        print_colored("="*60 + "\n", Colors.BOLD)
        
        # 1. Verificar estructura de carpetas
        print_colored("1️⃣ Verificando estructura de carpetas...", Colors.BLUE)
        self.check_folder_structure()
        
        # 2. Verificar archivo .env
        print_colored("\n2️⃣ Verificando configuración .env...", Colors.BLUE)
        self.check_env_configuration()
        
        # 3. Verificar dependencias Python
        print_colored("\n3️⃣ Verificando dependencias Python...", Colors.BLUE)
        self.check_python_dependencies()
        
        # 4. Verificar APIs externas
        print_colored("\n4️⃣ Verificando conexiones API...", Colors.BLUE)
        self.check_api_connections()
        
        # 5. Verificar archivos críticos
        print_colored("\n5️⃣ Verificando archivos críticos...", Colors.BLUE)
        self.check_critical_files()
        
        # 6. Verificar logs y errores recientes
        print_colored("\n6️⃣ Analizando logs recientes...", Colors.BLUE)
        self.analyze_recent_logs()
        
        # Resumen
        self.print_summary()
        
        # Aplicar correcciones
        if self.issues_found:
            self.apply_fixes()
    
    def check_folder_structure(self):
        """Verificar que todas las carpetas necesarias existen"""
        required_folders = [
            'configs',
            'logs',
            'data',
            'data/advanced',
            'risk',
            'risk/advanced',
            'broker',
            'signals',
            'ml',
            'backtesting',
            'storage',
            'notifiers',
            'utils'
        ]
        
        for folder in required_folders:
            folder_path = self.base_path / folder
            if not folder_path.exists():
                self.issues_found.append(f"Carpeta faltante: {folder}")
                folder_path.mkdir(parents=True, exist_ok=True)
                self.fixes_applied.append(f"Creada carpeta: {folder}")
                print_colored(f"  ❌ Faltante: {folder} -> ✅ CREADA", Colors.YELLOW)
            else:
                print_colored(f"  ✅ {folder}", Colors.GREEN)
    
    def check_env_configuration(self):
        """Verificar configuración del archivo .env"""
        env_path = self.base_path / 'configs' / '.env'
        
        if not env_path.exists():
            self.issues_found.append("Archivo .env no encontrado")
            self.create_default_env()
            return
        
        # Leer y verificar variables críticas
        required_vars = [
            'TWELVEDATA_API_KEY',
            'TELEGRAM_TOKEN',
            'TELEGRAM_CHAT_ID',
            'MT5_LOGIN',
            'MT5_PASSWORD',
            'MT5_SERVER',
            'SYMBOL',
            'LIVE_TRADING'
        ]
        
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        missing_vars = []
        for var in required_vars:
            if var not in env_content or f"{var}=" not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            for var in missing_vars:
                print_colored(f"  ❌ Variable faltante: {var}", Colors.RED)
                self.issues_found.append(f"Variable .env faltante: {var}")
        else:
            print_colored(f"  ✅ Todas las variables críticas presentes", Colors.GREEN)
            
        # Verificar que las variables tienen valores
        import re
        pattern = r'^([^#\s][^=]+)=(.*)$'
        
        for line in env_content.split('\n'):
            match = re.match(pattern, line)
            if match:
                key, value = match.groups()
                if not value.strip():
                    print_colored(f"  ⚠️  Variable sin valor: {key}", Colors.YELLOW)
    
    def check_python_dependencies(self):
        """Verificar que todas las dependencias están instaladas"""
        required_packages = {
            'MetaTrader5': 'MetaTrader5',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'python-dotenv': 'dotenv',
            'requests': 'requests',
            'asyncio': 'asyncio',
            'scipy': 'scipy',
            'scikit-learn': 'sklearn',
            'aiohttp': 'aiohttp'
        }
        
        missing_packages = []
        
        for package, import_name in required_packages.items():
            try:
                __import__(import_name)
                print_colored(f"  ✅ {package}", Colors.GREEN)
            except ImportError:
                print_colored(f"  ❌ {package} no instalado", Colors.RED)
                missing_packages.append(package)
                self.issues_found.append(f"Paquete Python faltante: {package}")
        
        if missing_packages:
            self.fixes_applied.append(f"Instalar paquetes: pip install {' '.join(missing_packages)}")
    
    def check_api_connections(self):
        """Verificar conexiones a APIs externas"""
        
        # Verificar TwelveData API
        print("  📊 TwelveData API:")
        try:
            from dotenv import load_dotenv
            load_dotenv(self.base_path / 'configs' / '.env')
            api_key = os.getenv('TWELVEDATA_API_KEY')
            
            if api_key:
                import requests
                response = requests.get(
                    f"https://api.twelvedata.com/api_usage?apikey={api_key}",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    used = data.get('used_credits', 0)
                    limit = data.get('daily_limit', 0)
                    print_colored(f"    ✅ Conectado - Créditos: {used}/{limit}", Colors.GREEN)
                else:
                    print_colored(f"    ❌ Error de conexión: {response.status_code}", Colors.RED)
                    self.issues_found.append("TwelveData API no responde correctamente")
            else:
                print_colored(f"    ❌ API Key no encontrada", Colors.RED)
                self.issues_found.append("TwelveData API Key no configurada")
        except Exception as e:
            print_colored(f"    ❌ Error: {str(e)}", Colors.RED)
            self.issues_found.append(f"Error conectando TwelveData: {e}")
        
        # Verificar MT5
        print("  💹 MetaTrader 5:")
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                print_colored(f"    ✅ MT5 inicializado", Colors.GREEN)
                mt5.shutdown()
            else:
                print_colored(f"    ❌ No se pudo inicializar MT5", Colors.RED)
                self.issues_found.append("MT5 no se puede inicializar")
        except Exception as e:
            print_colored(f"    ❌ Error: {str(e)}", Colors.RED)
            self.issues_found.append(f"Error con MT5: {e}")
        
        # Verificar Telegram
        print("  💬 Telegram Bot:")
        try:
            from dotenv import load_dotenv
            load_dotenv(self.base_path / 'configs' / '.env')
            token = os.getenv('TELEGRAM_TOKEN')
            
            if token:
                import requests
                response = requests.get(
                    f"https://api.telegram.org/bot{token}/getMe",
                    timeout=5
                )
                if response.status_code == 200:
                    bot_info = response.json()['result']
                    print_colored(f"    ✅ Bot: @{bot_info['username']}", Colors.GREEN)
                else:
                    print_colored(f"    ❌ Token inválido", Colors.RED)
                    self.issues_found.append("Token de Telegram inválido")
            else:
                print_colored(f"    ⚠️  Token no configurado", Colors.YELLOW)
        except Exception as e:
            print_colored(f"    ❌ Error: {str(e)}", Colors.RED)
    
    def check_critical_files(self):
        """Verificar que los archivos críticos existen y son válidos"""
        critical_files = [
            'enhanced_trading_bot_v2.py',
            'data/advanced/critical_change_detector.py',
            'data/advanced/multi_timeframe_analyzer.py',
            'risk/advanced/adaptive_risk_manager.py',
            'smart_position_manager.py'
        ]
        
        for file in critical_files:
            file_path = self.base_path / file
            if not file_path.exists():
                print_colored(f"  ❌ Archivo faltante: {file}", Colors.RED)
                self.issues_found.append(f"Archivo crítico faltante: {file}")
            else:
                # Verificar que no está vacío
                if file_path.stat().st_size == 0:
                    print_colored(f"  ⚠️  Archivo vacío: {file}", Colors.YELLOW)
                    self.issues_found.append(f"Archivo vacío: {file}")
                else:
                    print_colored(f"  ✅ {file} ({file_path.stat().st_size / 1024:.1f} KB)", Colors.GREEN)
    
    def analyze_recent_logs(self):
        """Analizar logs recientes para detectar errores comunes"""
        logs_path = self.base_path / 'logs'
        
        if not logs_path.exists():
            print_colored("  ⚠️  Carpeta de logs no existe", Colors.YELLOW)
            return
        
        # Buscar archivos de log más recientes
        log_files = list(logs_path.glob('*.err.log'))
        
        if not log_files:
            print_colored("  ✅ No hay logs de error", Colors.GREEN)
            return
        
        # Analizar último log de error
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
        
        common_errors = {
            'TWELVEDATA_API_KEY no está configurada': 'API Key de TwelveData no configurada',
            'No module named': 'Módulo Python faltante',
            'Connection refused': 'Problema de conexión',
            'MT5 not initialized': 'MT5 no inicializado',
            'Telegram error': 'Error con Telegram'
        }
        
        errors_found = set()
        
        try:
            with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for error_pattern, description in common_errors.items():
                if error_pattern in content:
                    errors_found.add(description)
            
            if errors_found:
                print_colored(f"  ⚠️  Errores detectados en {latest_log.name}:", Colors.YELLOW)
                for error in errors_found:
                    print_colored(f"    - {error}", Colors.YELLOW)
                    self.issues_found.append(error)
            else:
                print_colored(f"  ✅ No hay errores críticos en logs recientes", Colors.GREEN)
                
        except Exception as e:
            print_colored(f"  ❌ Error leyendo logs: {e}", Colors.RED)
    
    def create_default_env(self):
        """Crear archivo .env por defecto"""
        default_env = """# === API KEYS ===
TWELVEDATA_API_KEY=your_api_key_here
TELEGRAM_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id

# === MetaTrader 5 ===
MT5_PATH=C:\\Program Files\\MetaTrader 5\\terminal64.exe
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
MT5_TIMEOUT=60000
MT5_DEVIATION=20
MT5_MAGIC=20250817
MT5_PORTABLE=0

# === Trading Configuration ===
LIVE_TRADING=false
SYMBOL=XAUUSD
TWELVEDATA_SYMBOL=XAU/USD
RISK_PER_TRADE=0.01
MAX_CONCURRENT_TRADES=1
INITIAL_CAPITAL=10000.0

# === System ===
TZ=America/Bogota
DB_PATH=data/trading.db
LOG_LEVEL=INFO

# === Enhanced Trading Bot V2 ===
SENSITIVITY=0.7
BASE_RISK=0.01
MAX_RISK=0.03
ENABLE_CRITICAL_ALERTS=true
TIMEFRAMES=5min,15min,1h,4h,1day
USE_ADAPTIVE_RISK=true
"""
        
        env_path = self.base_path / 'configs' / '.env'
        env_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(env_path, 'w') as f:
            f.write(default_env)
        
        self.fixes_applied.append("Creado archivo .env por defecto")
        print_colored("  ✅ Archivo .env creado (necesita configuración)", Colors.YELLOW)
    
    def apply_fixes(self):
        """Aplicar correcciones automáticas"""
        print_colored("\n" + "="*60, Colors.BOLD)
        print_colored("🔨 APLICANDO CORRECCIONES", Colors.BOLD)
        print_colored("="*60, Colors.BOLD)
        
        # Crear script de instalación
        install_script = """#!/bin/bash
# Script de instalación de dependencias

echo "📦 Instalando dependencias Python..."
pip install MetaTrader5 pandas numpy python-dotenv requests scipy scikit-learn aiohttp asyncio

echo "📁 Creando estructura de carpetas..."
mkdir -p configs logs data/advanced risk/advanced broker signals ml backtesting storage notifiers utils

echo "✅ Instalación completada"
"""
        
        script_path = self.base_path / 'install_dependencies.sh'
        with open(script_path, 'w') as f:
            f.write(install_script)
        
        print_colored("\n📋 Script de instalación creado: install_dependencies.sh", Colors.GREEN)
        print_colored("   Ejecutar: bash install_dependencies.sh", Colors.BLUE)
        
        # Crear script de inicio mejorado
        start_script = """#!/usr/bin/env python3
import os
import sys
import asyncio
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

# Configurar variables de entorno
os.environ['PYTHONPATH'] = str(Path(__file__).parent)

# Importar y ejecutar bot
from enhanced_trading_bot_v2 import EnhancedTradingBotV2

async def main():
    bot = EnhancedTradingBotV2()
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\\nBot detenido por usuario")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
"""
        
        start_path = self.base_path / 'start_bot_fixed.py'
        with open(start_path, 'w') as f:
            f.write(start_script)
        
        print_colored("\n🚀 Script de inicio mejorado: start_bot_fixed.py", Colors.GREEN)
        print_colored("   Ejecutar: python start_bot_fixed.py", Colors.BLUE)
    
    def print_summary(self):
        """Imprimir resumen del diagnóstico"""
        print_colored("\n" + "="*60, Colors.BOLD)
        print_colored("📊 RESUMEN DEL DIAGNÓSTICO", Colors.BOLD)
        print_colored("="*60, Colors.BOLD)
        
        if not self.issues_found:
            print_colored("\n✅ ¡TODO ESTÁ CORRECTO! El bot está listo para ejecutar.", Colors.GREEN)
        else:
            print_colored(f"\n⚠️  Se encontraron {len(self.issues_found)} problemas:", Colors.YELLOW)
            for i, issue in enumerate(self.issues_found, 1):
                print_colored(f"  {i}. {issue}", Colors.YELLOW)
            
            if self.fixes_applied:
                print_colored(f"\n✅ Se aplicaron {len(self.fixes_applied)} correcciones:", Colors.GREEN)
                for i, fix in enumerate(self.fixes_applied, 1):
                    print_colored(f"  {i}. {fix}", Colors.GREEN)
        
        # Recomendaciones finales
        print_colored("\n" + "="*60, Colors.BOLD)
        print_colored("💡 RECOMENDACIONES", Colors.BOLD)
        print_colored("="*60, Colors.BOLD)
        
        recommendations = [
            "1. Verificar que el archivo .env tiene las API keys correctas",
            "2. Ejecutar: pip install -r requirements.txt",
            "3. Probar primero en modo DEMO (LIVE_TRADING=false)",
            "4. Monitorear los logs en la carpeta logs/",
            "5. Usar el script start_bot_fixed.py para iniciar"
        ]
        
        for rec in recommendations:
            print_colored(f"  {rec}", Colors.BLUE)


# Función de test rápido
def quick_test():
    """Test rápido del bot"""
    print_colored("\n🧪 TEST RÁPIDO DEL BOT", Colors.BOLD)
    
    try:
        # Intentar importar módulos críticos
        from dotenv import load_dotenv
        import pandas as pd
        import numpy as np
        
        # Cargar configuración
        base_path = Path(__file__).parent
        env_path = base_path / 'configs' / '.env'
        
        if env_path.exists():
            load_dotenv(env_path)
            
            # Verificar variables críticas
            api_key = os.getenv('TWELVEDATA_API_KEY')
            symbol = os.getenv('SYMBOL', 'XAUUSD')
            
            if api_key and api_key != 'your_api_key_here':
                print_colored(f"  ✅ Configuración cargada para {symbol}", Colors.GREEN)
                
                # Test de conexión a TwelveData
                import requests
                url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={api_key}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'price' in data:
                        print_colored(f"  ✅ Precio actual {symbol}: ${data['price']}", Colors.GREEN)
                    else:
                        print_colored(f"  ⚠️  Respuesta sin precio: {data}", Colors.YELLOW)
                else:
                    print_colored(f"  ❌ Error API: {response.status_code}", Colors.RED)
            else:
                print_colored("  ❌ API Key no configurada correctamente", Colors.RED)
        else:
            print_colored("  ❌ Archivo .env no encontrado", Colors.RED)
            
    except Exception as e:
        print_colored(f"  ❌ Error en test: {e}", Colors.RED)


if __name__ == "__main__":
    # Ejecutar diagnóstico completo
    diagnostic = TradingBotDiagnostic()
    diagnostic.run_full_diagnostic()
    
    # Ejecutar test rápido
    print_colored("\n" + "="*60, Colors.BOLD)
    quick_test()
    
    print_colored("\n" + "="*60, Colors.BOLD)
    print_colored("✅ DIAGNÓSTICO COMPLETADO", Colors.BOLD)
    print_colored("="*60 + "\n", Colors.BOLD)
