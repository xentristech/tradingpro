#!/usr/bin/env python
"""
REORGANIZACIÓN COMPLETA DEL PROYECTO ALGO TRADER V3
=====================================================
Este script reorganiza todo el proyecto de manera profesional,
eliminando duplicados y creando una estructura limpia.

Autor: XentrisTech
Fecha: 2025
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import hashlib

class ProjectReorganizer:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.stats = {
            'files_moved': 0,
            'files_deleted': 0,
            'duplicates_removed': 0,
            'errors': []
        }
        
        # Mapeo de archivos a sus nuevas ubicaciones
        self.file_mapping = {
            # Core system files
            'core': [
                'bot_manager.py',
                'mt5_connection.py', 
                'state_manager.py',
                'circuit_breaker.py',
                'health_check.py',
                'rate_limiter.py',
                'system_manager.py'
            ],
            
            # Trading components
            'src/trading': [
                'main_trader.py',
                'live_trader.py',
                'real_trader.py',
                'multi_trader.py',
                'exness_automated_trader.py',
                'smart_position_manager.py',
                'execute_trading.py',
                'auto_execute.py'
            ],
            
            # UI - Dashboards principales
            'src/ui/dashboards': [
                'revolutionary_dashboard_final.py',
                'modern_trading_dashboard.py',
                'innovative_signal_dashboard.py',
                'advanced_modern_dashboard.py',
                'trading_dashboard.py',
                'dashboard_web.py',
                'streamlit_app.py'
            ],
            
            # UI - Charts
            'src/ui/charts': [
                'chart_simulation_reviewed.py',
                'tradingview_professional_chart.py',
                'advanced_chart_generator.py',
                'ultra_advanced_chart.py',
                'dynamic_charts.py',
                'working_charts.py',
                'simple_visual_charts.py'
            ],
            
            # Sistemas de datos
            'src/data': [
                'TICK_SYSTEM_FINAL.py',
                'FINAL_TICK_SYSTEM_WORKING.py',
                'enhanced_tick_system.py',
                'tick_data_live.py',
                'working_tick_function.py',
                'mt5_tick_analyzer.py'
            ],
            
            # AI/ML components
            'src/ai': [
                'ai_dashboard.py',
                'ai_signal_generator.py',
                'ai_signal_monitor.py',
                'ai_trade_monitor.py',
                'ai_position_monitor.py',
                'ai_monitor_simple.py',
                'ollama_setup.py'
            ],
            
            # Tests
            'tests': [
                'test_*.py',  # Todos los archivos que empiezan con test_
                'check_*.py', # Todos los archivos de verificación
                'diagnose_*.py',
                'diagnostic_*.py',
                'verify_*.py',
                'validate_*.py'
            ],
            
            # Scripts y utilidades
            'scripts': [
                '*.bat',  # Todos los archivos batch
                '*.ps1'   # Todos los scripts PowerShell
            ],
            
            # Configuración
            'config': [
                '.env',
                '*.json',
                '*.yaml',
                '*.yml'
            ],
            
            # Documentación
            'docs': [
                '*.md',  # Todos los archivos markdown
                'requirements.txt'
            ]
        }
        
        # Archivos obsoletos para eliminar
        self.deprecated_files = [
            'BOT.bat',
            'CHECK.bat',
            'DASHBOARD.bat',
            'EJECUTAR_BOT.bat',
            'DETENER_BOT.bat',
            'INICIO_COMPLETO.bat',
            'LAUNCHER.bat',
            'MENU_BOT.bat',
            'RUN.bat',
            'START.bat',
            'TRADER.bat',
            'GO.bat'
        ]
        
    def calculate_file_hash(self, filepath):
        """Calcula el hash MD5 de un archivo para detectar duplicados"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def find_duplicates(self):
        """Encuentra archivos duplicados basándose en su contenido"""
        print("\n🔍 Buscando archivos duplicados...")
        
        file_hashes = {}
        duplicates = []
        
        for file_path in self.base_path.glob('*.py'):
            if file_path.is_file():
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        duplicates.append((file_path, file_hashes[file_hash]))
                    else:
                        file_hashes[file_hash] = file_path
        
        return duplicates
    
    def create_directory_structure(self):
        """Crea la estructura de directorios necesaria"""
        print("\n📁 Creando estructura de directorios...")
        
        directories = [
            'src/core',
            'src/trading',
            'src/ui/dashboards',
            'src/ui/charts',
            'src/data',
            'src/ai',
            'src/signals',
            'src/risk',
            'src/utils',
            'tests/unit',
            'tests/integration',
            'scripts/startup',
            'scripts/maintenance',
            'config',
            'docs/api',
            'docs/guides',
            'deprecated',
            'backups'
        ]
        
        for dir_path in directories:
            full_path = self.base_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
    def move_file_safely(self, source, destination):
        """Mueve un archivo de manera segura"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if source_path.exists():
                # Crear backup si el destino existe
                if dest_path.exists():
                    backup_path = self.base_path / 'backups' / f"{dest_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(dest_path, backup_path)
                
                # Mover archivo
                shutil.move(str(source_path), str(dest_path))
                self.stats['files_moved'] += 1
                return True
        except Exception as e:
            self.stats['errors'].append(f"Error moviendo {source}: {e}")
            return False
    
    def organize_files(self):
        """Organiza los archivos según el mapeo definido"""
        print("\n📦 Organizando archivos...")
        
        # Mover archivos core existentes
        core_dir = self.base_path / 'core'
        if core_dir.exists():
            for file in core_dir.glob('*.py'):
                dest = self.base_path / 'src' / 'core' / file.name
                self.move_file_safely(file, dest)
        
        # Mover otros directorios existentes
        existing_dirs = ['signals', 'risk', 'utils', 'broker', 'ml', 'notifiers']
        for dir_name in existing_dirs:
            source_dir = self.base_path / dir_name
            if source_dir.exists():
                dest_dir = self.base_path / 'src' / dir_name
                dest_dir.mkdir(parents=True, exist_ok=True)
                for file in source_dir.glob('*.py'):
                    self.move_file_safely(file, dest_dir / file.name)
        
        # Mover archivos específicos
        for category, files in self.file_mapping.items():
            dest_dir = self.base_path / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            for file_pattern in files:
                if '*' in file_pattern:
                    # Es un patrón, buscar todos los archivos que coincidan
                    for file in self.base_path.glob(file_pattern):
                        if file.is_file() and file.parent == self.base_path:
                            self.move_file_safely(file, dest_dir / file.name)
                else:
                    # Es un archivo específico
                    source = self.base_path / file_pattern
                    if source.exists():
                        self.move_file_safely(source, dest_dir / file_pattern)
    
    def clean_deprecated(self):
        """Mueve archivos obsoletos a la carpeta deprecated"""
        print("\n🗑️ Limpiando archivos obsoletos...")
        
        deprecated_dir = self.base_path / 'deprecated'
        
        # Mover archivos batch duplicados
        for file in self.deprecated_files:
            source = self.base_path / file
            if source.exists():
                self.move_file_safely(source, deprecated_dir / file)
                self.stats['files_deleted'] += 1
    
    def create_unified_launcher(self):
        """Crea un launcher unificado para el sistema"""
        print("\n🚀 Creando launcher unificado...")
        
        launcher_content = '''#!/usr/bin/env python
"""
ALGO TRADER V3 - LAUNCHER UNIFICADO
====================================
Sistema principal de inicio y gestión
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class AlgoTraderLauncher:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.processes = {}
        
    def start_system(self, mode='demo'):
        """Inicia el sistema completo"""
        print(f"🚀 Iniciando Algo Trader en modo {mode.upper()}")
        
        # 1. Verificar dependencias
        self.check_dependencies()
        
        # 2. Iniciar servicios core
        self.start_core_services()
        
        # 3. Iniciar dashboards
        self.start_dashboards()
        
        # 4. Iniciar bot de trading
        self.start_trading_bot(mode)
        
        print("✅ Sistema iniciado completamente")
        
    def check_dependencies(self):
        """Verifica que todas las dependencias estén instaladas"""
        try:
            import MetaTrader5
            import pandas
            import streamlit
            print("✅ Dependencias verificadas")
        except ImportError as e:
            print(f"❌ Falta dependencia: {e}")
            sys.exit(1)
    
    def start_core_services(self):
        """Inicia los servicios principales"""
        # Iniciar sistema de ticks
        tick_system = self.base_path / 'src' / 'data' / 'TICK_SYSTEM_FINAL.py'
        if tick_system.exists():
            self.processes['tick_system'] = subprocess.Popen(
                [sys.executable, str(tick_system)],
                cwd=str(self.base_path)
            )
            print("✅ Sistema de ticks iniciado")
    
    def start_dashboards(self):
        """Inicia los dashboards web"""
        dashboards = [
            ('revolutionary_dashboard_final.py', 8512),
            ('chart_simulation_reviewed.py', 8516),
            ('tradingview_professional_chart.py', 8517)
        ]
        
        for dashboard, port in dashboards:
            dashboard_path = self.base_path / 'src' / 'ui' / 'dashboards' / dashboard
            if dashboard_path.exists():
                self.processes[dashboard] = subprocess.Popen(
                    [sys.executable, str(dashboard_path)],
                    cwd=str(self.base_path)
                )
                print(f"✅ Dashboard iniciado en puerto {port}")
    
    def start_trading_bot(self, mode):
        """Inicia el bot de trading"""
        os.environ['TRADING_MODE'] = mode.upper()
        
        bot_path = self.base_path / 'src' / 'trading' / 'main_trader.py'
        if bot_path.exists():
            self.processes['trading_bot'] = subprocess.Popen(
                [sys.executable, str(bot_path)],
                cwd=str(self.base_path)
            )
            print(f"✅ Bot de trading iniciado en modo {mode}")
    
    def stop_system(self):
        """Detiene todos los procesos"""
        print("⏹️ Deteniendo sistema...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                process.terminate()
                print(f"✅ {name} detenido")
        
        print("✅ Sistema detenido completamente")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Algo Trader V3 Launcher')
    parser.add_argument('--mode', choices=['demo', 'paper', 'live'], 
                       default='demo', help='Modo de trading')
    parser.add_argument('--action', choices=['start', 'stop', 'restart'], 
                       default='start', help='Acción a realizar')
    
    args = parser.parse_args()
    launcher = AlgoTraderLauncher()
    
    if args.action == 'start':
        launcher.start_system(args.mode)
    elif args.action == 'stop':
        launcher.stop_system()
    elif args.action == 'restart':
        launcher.stop_system()
        launcher.start_system(args.mode)
'''
        
        launcher_path = self.base_path / 'launcher.py'
        launcher_path.write_text(launcher_content, encoding='utf-8')
        
        # Crear archivo batch para Windows
        batch_content = '''@echo off
echo ========================================
echo    ALGO TRADER V3 - SISTEMA PRINCIPAL
echo ========================================
echo.

python launcher.py --mode demo --action start

pause
'''
        batch_path = self.base_path / 'START_SYSTEM.bat'
        batch_path.write_text(batch_content)
        
    def create_readme(self):
        """Crea un README actualizado y limpio"""
        print("\n📝 Creando documentación actualizada...")
        
        readme_content = '''# ALGO TRADER V3 - Sistema Profesional de Trading Algorítmico

## 📋 Descripción
Sistema avanzado de trading algorítmico con inteligencia artificial, análisis técnico y gestión de riesgo automatizada.

## 🏗️ Estructura del Proyecto

```
algo-trader-v3/
├── src/                    # Código fuente principal
│   ├── core/              # Núcleo del sistema
│   ├── trading/           # Lógica de trading
│   ├── data/              # Gestión de datos y ticks
│   ├── ui/                # Interfaces de usuario
│   │   ├── dashboards/    # Dashboards web
│   │   └── charts/        # Sistemas de gráficos
│   ├── ai/                # Inteligencia artificial
│   ├── signals/           # Generación de señales
│   ├── risk/              # Gestión de riesgo
│   └── utils/             # Utilidades
├── tests/                 # Pruebas
├── scripts/              # Scripts de utilidad
├── config/               # Configuración
├── docs/                 # Documentación
└── launcher.py           # Iniciador principal
```

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.10+
- MetaTrader 5
- Cuenta de trading (demo o real)

### Instalación
```bash
# Clonar repositorio
git clone https://github.com/yourusername/algo-trader-v3.git

# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales
cp config/.env.example config/.env
# Editar .env con tus credenciales
```

### Uso

#### Modo Demo (Recomendado para empezar)
```bash
python launcher.py --mode demo --action start
```

#### Modo Paper Trading
```bash
python launcher.py --mode paper --action start
```

#### Modo Live (⚠️ Dinero Real)
```bash
python launcher.py --mode live --action start
```

## 📊 Dashboards Disponibles

| Dashboard | Puerto | URL | Descripción |
|-----------|--------|-----|-------------|
| Revolutionary | 8512 | http://localhost:8512 | Dashboard principal con IA |
| Chart Simulation | 8516 | http://localhost:8516 | Simulación de gráficos |
| TradingView Pro | 8517 | http://localhost:8517 | Gráficos profesionales |

## 🤖 Características Principales

- ✅ Trading automatizado con MT5
- ✅ Análisis con IA (Ollama/Deepseek)
- ✅ Machine Learning predictivo
- ✅ Gestión de riesgo avanzada
- ✅ Múltiples estrategias de trading
- ✅ Backtesting integrado
- ✅ Notificaciones por Telegram
- ✅ Web scraping de datos
- ✅ Análisis de ticks en tiempo real

## 📈 Estrategias Implementadas

1. **Scalping con IA**: Operaciones rápidas basadas en predicciones
2. **Swing Trading**: Posiciones a medio plazo con análisis técnico
3. **Grid Trading**: Red de órdenes para mercados laterales
4. **Martingala Controlada**: Con límites de riesgo estrictos

## ⚙️ Configuración

Editar `config/.env`:

```env
# Cuenta MT5
MT5_LOGIN=tu_login
MT5_PASSWORD=tu_password
MT5_SERVER=tu_servidor

# Telegram (opcional)
TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id

# Trading
RISK_PERCENT=2.0
MAX_POSITIONS=3
```

## 🛡️ Gestión de Riesgo

- Stop Loss dinámico
- Take Profit adaptativo
- Límite de pérdida diaria: -$500
- Drawdown máximo: -20%
- Tamaño de posición calculado por riesgo

## 🧪 Testing

```bash
# Tests unitarios
pytest tests/unit/

# Tests de integración
pytest tests/integration/

# Test completo del sistema
python tests/full_system_test.py
```

## 📞 Soporte

- Email: support@xentristech.com
- Telegram: @AlgoTraderSupport
- Documentación: [docs/](./docs/)

## ⚠️ Advertencia

Este software opera en mercados financieros reales. El trading conlleva riesgos significativos. 
No nos responsabilizamos por pérdidas. Use bajo su propio riesgo.

## 📄 Licencia

Copyright (c) 2025 XentrisTech. Todos los derechos reservados.
'''
        
        readme_path = self.base_path / 'README.md'
        readme_path.write_text(readme_content, encoding='utf-8')
    
    def generate_report(self):
        """Genera un reporte de la reorganización"""
        print("\n📊 Generando reporte...")
        
        report = f"""
REPORTE DE REORGANIZACIÓN
=========================
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Estadísticas:
- Archivos movidos: {self.stats['files_moved']}
- Archivos eliminados: {self.stats['files_deleted']}
- Duplicados removidos: {self.stats['duplicates_removed']}
- Errores encontrados: {len(self.stats['errors'])}

Errores:
{chr(10).join(self.stats['errors']) if self.stats['errors'] else 'Ninguno'}

La reorganización se ha completado exitosamente.
Nueva estructura creada en /src con todos los componentes organizados.
"""
        
        report_path = self.base_path / 'REORGANIZATION_REPORT.txt'
        report_path.write_text(report, encoding='utf-8')
        
        return report
    
    def run(self):
        """Ejecuta la reorganización completa"""
        print("""
╔═══════════════════════════════════════════════════════╗
║          REORGANIZACIÓN DE ALGO TRADER V3            ║
║                  Sistema Automático                   ║
╚═══════════════════════════════════════════════════════╝
        """)
        
        # 1. Crear estructura de directorios
        self.create_directory_structure()
        
        # 2. Buscar y eliminar duplicados
        duplicates = self.find_duplicates()
        if duplicates:
            print(f"\n⚠️ Encontrados {len(duplicates)} archivos duplicados")
            for dup, original in duplicates:
                deprecated_dir = self.base_path / 'deprecated'
                self.move_file_safely(dup, deprecated_dir / dup.name)
                self.stats['duplicates_removed'] += 1
        
        # 3. Organizar archivos
        self.organize_files()
        
        # 4. Limpiar archivos obsoletos
        self.clean_deprecated()
        
        # 5. Crear launcher unificado
        self.create_unified_launcher()
        
        # 6. Actualizar documentación
        self.create_readme()
        
        # 7. Generar reporte
        report = self.generate_report()
        
        print("\n" + "="*50)
        print(report)
        print("="*50)
        
        print("""
✅ REORGANIZACIÓN COMPLETADA

Próximos pasos:
1. Revisar la nueva estructura en /src
2. Ejecutar: python launcher.py --mode demo
3. Acceder a los dashboards en los puertos configurados

¡El proyecto está ahora organizado profesionalmente!
        """)

if __name__ == "__main__":
    reorganizer = ProjectReorganizer()
    
    print("\n⚠️ ADVERTENCIA: Este script reorganizará todo el proyecto.")
    print("Se crearán backups de los archivos importantes.")
    
    response = input("\n¿Desea continuar? (s/n): ")
    
    if response.lower() == 's':
        reorganizer.run()
    else:
        print("Reorganización cancelada.")
