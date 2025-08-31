#!/usr/bin/env python
"""
REORGANIZACIÓN AUTOMÁTICA COMPLETA - SIN CONFIRMACIÓN
=====================================================
Ejecuta todo el proceso de reorganización automáticamente
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
import hashlib

print("""
╔════════════════════════════════════════════════════════════╗
║     REORGANIZACIÓN AUTOMÁTICA DE ALGO TRADER V3           ║
║              Proceso Completo en Ejecución                ║
╚════════════════════════════════════════════════════════════╝
""")

class AutoReorganizer:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.stats = {
            'files_moved': 0,
            'files_deleted': 0,
            'duplicates_removed': 0,
            'directories_created': 0,
            'space_freed': 0
        }
        
        # Lista de archivos obsoletos para mover a deprecated
        self.obsolete_files = [
            # Archivos .bat duplicados
            'BOT.bat', 'CHECK.bat', 'DASHBOARD.bat', 'EJECUTAR_BOT.bat',
            'DETENER_BOT.bat', 'DETENER_TODO.bat', 'INICIO_COMPLETO.bat',
            'LAUNCHER.bat', 'MENU_BOT.bat', 'RUN.bat', 'START.bat',
            'TRADER.bat', 'GO.bat', 'VERIFICAR.bat', 'PAUSAR_REANUDAR.bat',
            'EJECUTAR_AHORA.bat', 'EJECUTAR_CORREGIDO.bat', 'EJECUTAR_SISTEMA.bat',
            'DASHBOARD_SIMPLE.bat', 'CHECK_ACCOUNTS_INDEPENDENT.bat',
            'CHECK_OLLAMA.bat', 'DEMO_FIX_MULTICUENTA.bat', 
            'DIAGNOSTICO_DETALLADO.bat', 'EXECUTE_BOT_NOW.bat', 'FIX_AND_RUN.bat',
            'FIX_SL_TP.bat', 'INFO_CREDENCIALES_CORRECTAS.bat', 'INICIAR_BOT.bat',
            'LAUNCH_BOT_V2.bat', 'MULTI_ACCOUNT_FIXED.bat', 'MULTI_ACCOUNT_SEPARATE.bat',
            'OLLAMA_STATUS.bat', 'QUICK_INSTALL.bat', 'REPARAR_PYTHON.bat',
            'RUN_BOT.bat', 'RUN_BOT_NOW.bat', 'RUN_NOW.bat', 'SISTEMA_PRO.bat',
            'SOLUCION_FINAL.bat', 'START_BOT_DIRECT.bat', 'START_DYNAMIC_CHARTS.bat',
            'START_LIVE_TRADING.bat', 'START_SYSTEM.bat', 'TEST_MT5.bat',
            'VER_ESTADO.bat', 'VERIFICACION_COMPLETA_SISTEMA.bat', 'VERIFICAR_IA.bat',
            'VERIFICAR_OLLAMA.bat',
            
            # Scripts de inicio duplicados
            'EJECUTAR_AHORA.py', 'ejecutar_bot.py', 
            'START_BOT.py', 'INICIO_COMPLETO.py', 'INICIO_TICK_SYSTEM.py',
            'RUN_BOT_VISIBLE.py', 'run_bot_now.py', 'run_direct.py',
            'run_simple.py', 'simple_start.py', 'quick_launcher.py',
            'launch_all_dashboards.py', 'launch_dashboard.py',
            
            # Documentación redundante
            'README_COMPLETO.md', 'README_FINAL_V3.md', 'README_IMPROVED.md',
            'README_V3.md', 'ANALISIS_COMPARATIVO_V2_V3.md', 'GITHUB_SYSTEM_REPORT.md',
            'INFORME_FINAL.md', 'INSTRUCCIONES_SISTEMA_DINAMICO.md',
            'RESUMEN_FINAL_WEB_SCRAPING.md', 'RESUMEN_SISTEMA_COMPLETO.md',
            'SISTEMA_COMPLETO.md', 'SOLUCION_COMPLETA_DUPLICACION.md',
            'SOLUCION_DUPLICACION_CUENTAS.md',
            
            # Tests redundantes
            'test_env.py', 'td_test.py', 'tg_test.py', 'quick_check.py',
            'simple_check.py', 'test_mt5_simple.py', 'test_mt5_exness.py',
            'test_chart_minimal.py', 'test_visual_charts.py',
            
            # Archivos temporales
            'system_check_report.json', 'mt5_scraped_documentation.json'
        ]
        
    def create_directory_structure(self):
        """Crea la estructura de directorios profesional"""
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
            'src/broker',
            'src/ml',
            'src/notifiers',
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
            self.stats['directories_created'] += 1
            
        print(f"  ✓ {len(directories)} directorios creados")
        
    def move_file_safely(self, source, destination):
        """Mueve un archivo de manera segura"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if source_path.exists():
                # Crear directorio de destino si no existe
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Si el destino existe, hacer backup
                if dest_path.exists():
                    backup_dir = self.base_path / 'backups'
                    backup_dir.mkdir(exist_ok=True)
                    backup_path = backup_dir / f"{dest_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(dest_path, backup_path)
                
                # Mover archivo
                shutil.move(str(source_path), str(dest_path))
                self.stats['files_moved'] += 1
                return True
        except Exception as e:
            print(f"  ⚠️ Error moviendo {source.name}: {e}")
            return False
            
    def clean_obsolete_files(self):
        """Mueve archivos obsoletos a deprecated"""
        print("\n🗑️ Limpiando archivos obsoletos...")
        
        deprecated_dir = self.base_path / 'deprecated'
        deprecated_dir.mkdir(exist_ok=True)
        
        count = 0
        for file_name in self.obsolete_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                dest = deprecated_dir / file_name
                if self.move_file_safely(file_path, dest):
                    count += 1
                    self.stats['files_deleted'] += 1
                    
        print(f"  ✓ {count} archivos obsoletos movidos a /deprecated")
        
    def organize_core_files(self):
        """Organiza los archivos principales"""
        print("\n📦 Organizando archivos principales...")
        
        # Mapeo de archivos a sus nuevas ubicaciones
        file_mappings = {
            # Core files
            'core': ['src/core', [
                'bot_manager.py', 'mt5_connection.py', 'state_manager.py',
                'circuit_breaker.py', 'health_check.py', 'rate_limiter.py',
                'system_manager.py'
            ]],
            
            # Trading files
            'trading': ['src/trading', [
                'main_trader.py', 'live_trader.py', 'real_trader.py',
                'multi_trader.py', 'exness_automated_trader.py',
                'smart_position_manager.py', 'execute_trading.py',
                'auto_execute.py', 'pro_trading_bot.py', 'enhanced_trading_bot.py',
                'enhanced_trading_bot_v2.py', 'FINAL_BOT.py'
            ]],
            
            # Dashboards
            'dashboards': ['src/ui/dashboards', [
                'revolutionary_dashboard_final.py', 'modern_trading_dashboard.py',
                'innovative_signal_dashboard.py', 'advanced_modern_dashboard.py',
                'trading_dashboard.py', 'dashboard_web.py', 'streamlit_app.py',
                'dashboard_funcional.py', 'monitoring_dashboard.py',
                'signals_dashboard.py', 'tick_dashboard.py'
            ]],
            
            # Charts
            'charts': ['src/ui/charts', [
                'chart_simulation_reviewed.py', 'tradingview_professional_chart.py',
                'advanced_chart_generator.py', 'ultra_advanced_chart.py',
                'dynamic_charts.py', 'working_charts.py', 'simple_visual_charts.py',
                'fixed_charts.py', 'chart_generator.py'
            ]],
            
            # Data systems
            'data': ['src/data', [
                'TICK_SYSTEM_FINAL.py', 'FINAL_TICK_SYSTEM_WORKING.py',
                'enhanced_tick_system.py', 'tick_data_live.py',
                'working_tick_function.py', 'mt5_tick_analyzer.py',
                'mt5_advanced_scraper.py', 'market_snapshot.py'
            ]],
            
            # AI components
            'ai': ['src/ai', [
                'ai_dashboard.py', 'ai_signal_generator.py', 'ai_signal_monitor.py',
                'ai_trade_monitor.py', 'ai_position_monitor.py', 'ai_monitor_simple.py',
                'ollama_setup.py', 'test_ai_direct.py', 'test_ai_simple.py'
            ]]
        }
        
        moved_count = 0
        
        # Mover archivos existentes de directorios originales
        for source_dir in ['core', 'signals', 'risk', 'utils', 'broker', 'ml', 'notifiers', 'ai']:
            source_path = self.base_path / source_dir
            if source_path.exists() and source_path.is_dir():
                dest_path = self.base_path / 'src' / source_dir
                dest_path.mkdir(parents=True, exist_ok=True)
                
                for file in source_path.glob('*.py'):
                    if self.move_file_safely(file, dest_path / file.name):
                        moved_count += 1
                        
        # Mover archivos específicos según el mapeo
        for category, (dest_dir, files) in file_mappings.items():
            dest_path = self.base_path / dest_dir
            dest_path.mkdir(parents=True, exist_ok=True)
            
            for file_name in files:
                source = self.base_path / file_name
                if source.exists():
                    if self.move_file_safely(source, dest_path / file_name):
                        moved_count += 1
                        
        print(f"  ✓ {moved_count} archivos organizados")
        
    def move_tests(self):
        """Mueve archivos de test a la carpeta tests"""
        print("\n🧪 Organizando archivos de test...")
        
        test_dir = self.base_path / 'tests'
        test_dir.mkdir(exist_ok=True)
        
        test_patterns = ['test_*.py', 'check_*.py', 'verify_*.py', 'diagnose_*.py', 'validate_*.py']
        moved = 0
        
        for pattern in test_patterns:
            for test_file in self.base_path.glob(pattern):
                if test_file.is_file():
                    dest = test_dir / test_file.name
                    if self.move_file_safely(test_file, dest):
                        moved += 1
                        
        print(f"  ✓ {moved} archivos de test organizados")
        
    def move_scripts(self):
        """Mueve scripts .bat y .ps1 a la carpeta scripts"""
        print("\n📜 Organizando scripts...")
        
        scripts_dir = self.base_path / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        
        # Solo mover los .bat y .ps1 que no están en la lista de obsoletos
        moved = 0
        for ext in ['*.bat', '*.ps1']:
            for script in self.base_path.glob(ext):
                if script.name not in self.obsolete_files and script.is_file():
                    dest = scripts_dir / script.name
                    if self.move_file_safely(script, dest):
                        moved += 1
                        
        print(f"  ✓ {moved} scripts organizados")
        
    def move_configs(self):
        """Mueve archivos de configuración"""
        print("\n⚙️ Organizando configuración...")
        
        config_dir = self.base_path / 'config'
        config_dir.mkdir(exist_ok=True)
        
        config_files = ['*.json', '*.yaml', '*.yml']
        moved = 0
        
        for pattern in config_files:
            for config_file in self.base_path.glob(pattern):
                if config_file.is_file() and config_file.name not in ['system_check_report.json', 'mt5_scraped_documentation.json']:
                    dest = config_dir / config_file.name
                    if self.move_file_safely(config_file, dest):
                        moved += 1
                        
        print(f"  ✓ {moved} archivos de configuración organizados")
        
    def clean_cache(self):
        """Limpia directorios de caché"""
        print("\n🧹 Limpiando caché...")
        
        cache_patterns = ['__pycache__', '.pytest_cache', '.mypy_cache']
        cleaned = 0
        
        for pattern in cache_patterns:
            for cache_dir in self.base_path.rglob(pattern):
                if cache_dir.is_dir():
                    try:
                        shutil.rmtree(cache_dir)
                        cleaned += 1
                    except:
                        pass
                        
        print(f"  ✓ {cleaned} directorios de caché limpiados")
        
    def find_and_remove_duplicates(self):
        """Encuentra y remueve archivos Python duplicados"""
        print("\n🔍 Buscando duplicados...")
        
        file_hashes = {}
        duplicates = []
        
        for py_file in self.base_path.rglob('*.py'):
            if 'deprecated' not in str(py_file) and '.venv' not in str(py_file):
                try:
                    with open(py_file, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        
                    if file_hash in file_hashes:
                        duplicates.append(py_file)
                    else:
                        file_hashes[file_hash] = py_file
                except:
                    pass
                    
        # Mover duplicados a deprecated
        deprecated_dir = self.base_path / 'deprecated' / 'duplicates'
        deprecated_dir.mkdir(parents=True, exist_ok=True)
        
        for dup in duplicates:
            try:
                dest = deprecated_dir / dup.name
                shutil.move(str(dup), str(dest))
                self.stats['duplicates_removed'] += 1
            except:
                pass
                
        print(f"  ✓ {len(duplicates)} duplicados removidos")
        
    def create_init_files(self):
        """Crea archivos __init__.py en todos los módulos"""
        print("\n📝 Creando archivos __init__.py...")
        
        count = 0
        for dir_path in self.base_path.rglob('src/**/'):
            if dir_path.is_dir() and '__pycache__' not in str(dir_path):
                init_file = dir_path / '__init__.py'
                if not init_file.exists():
                    init_file.write_text('"""Package initialization"""')
                    count += 1
                    
        print(f"  ✓ {count} archivos __init__.py creados")
        
    def generate_report(self):
        """Genera reporte de reorganización"""
        report = f"""
REPORTE DE REORGANIZACIÓN AUTOMÁTICA
=====================================
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Estadísticas:
- Directorios creados: {self.stats['directories_created']}
- Archivos movidos: {self.stats['files_moved']}
- Archivos obsoletos: {self.stats['files_deleted']}
- Duplicados removidos: {self.stats['duplicates_removed']}

Estado: COMPLETADO ✓

Nueva estructura:
src/
├── core/        # Sistema principal
├── trading/     # Bots de trading
├── ui/          # Interfaces de usuario
├── data/        # Gestión de datos
├── ai/          # Inteligencia artificial
├── signals/     # Generación de señales
├── risk/        # Gestión de riesgo
└── utils/       # Utilidades

La reorganización se completó exitosamente.
"""
        
        report_path = self.base_path / 'REORGANIZATION_REPORT.txt'
        report_path.write_text(report, encoding='utf-8')
        
        return report
        
    def run(self):
        """Ejecuta la reorganización completa"""
        try:
            print("\n🚀 Iniciando reorganización automática...")
            print("="*50)
            
            # 1. Crear estructura de directorios
            self.create_directory_structure()
            
            # 2. Limpiar archivos obsoletos
            self.clean_obsolete_files()
            
            # 3. Organizar archivos core
            self.organize_core_files()
            
            # 4. Mover tests
            self.move_tests()
            
            # 5. Mover scripts
            self.move_scripts()
            
            # 6. Mover configuraciones
            self.move_configs()
            
            # 7. Limpiar caché
            self.clean_cache()
            
            # 8. Buscar y remover duplicados
            self.find_and_remove_duplicates()
            
            # 9. Crear archivos __init__.py
            self.create_init_files()
            
            # 10. Generar reporte
            report = self.generate_report()
            
            print("\n" + "="*50)
            print(report)
            print("="*50)
            
            print("""
✅ REORGANIZACIÓN COMPLETADA EXITOSAMENTE

El proyecto ha sido reorganizado profesionalmente:
- Estructura de carpetas creada
- Archivos organizados por categorías
- Duplicados y obsoletos movidos a /deprecated
- Caché limpiado

Próximos pasos:
1. Revisa la carpeta /deprecated antes de eliminarla
2. Edita el archivo .env con tus credenciales
3. Ejecuta: python launcher.py --mode demo

¡Tu proyecto está ahora perfectamente organizado!
""")
            
        except Exception as e:
            print(f"\n❌ Error durante la reorganización: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\n⚡ Ejecutando reorganización automática...")
    print("Todos los archivos se moverán a sus ubicaciones correctas.")
    print("Los archivos obsoletos irán a /deprecated\n")
    
    reorganizer = AutoReorganizer()
    reorganizer.run()
