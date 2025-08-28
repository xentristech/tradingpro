#!/usr/bin/env python
"""
Migration Script - Migración del sistema v2 a v3
Preserva configuraciones y datos mientras actualiza la estructura
"""
import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
import argparse

class AlgoTraderMigration:
    """
    Herramienta de migración de Algo Trader v2 a v3
    """
    
    def __init__(self, backup_dir="backups"):
        """
        Inicializa el migrador
        
        Args:
            backup_dir: Directorio para backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.migration_log = []
        
    def log(self, message, level="INFO"):
        """Registra mensaje en el log"""
        entry = f"[{level}] {datetime.now().strftime('%H:%M:%S')} - {message}"
        print(entry)
        self.migration_log.append(entry)
    
    def backup_current_system(self):
        """Crea backup completo del sistema actual"""
        self.log("Creando backup del sistema actual...")
        
        backup_path = self.backup_dir / f"backup_v2_{self.timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # Archivos y carpetas a respaldar
        items_to_backup = [
            'configs/.env',
            'configs/settings.yaml',
            'data/trading.db',
            'logs/',
            'FINAL_BOT.py',
            'enhanced_trading_bot.py',
            'orchestrator/positions.py',
            'orchestrator/antespositions.py'
        ]
        
        backed_up = []
        
        for item in items_to_backup:
            source = Path(item)
            if source.exists():
                if source.is_file():
                    dest = backup_path / source.name
                    shutil.copy2(source, dest)
                    backed_up.append(str(source))
                elif source.is_dir():
                    dest = backup_path / source.name
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                    backed_up.append(str(source))
        
        self.log(f"Backup creado en: {backup_path}")
        self.log(f"Archivos respaldados: {len(backed_up)}")
        
        # Guardar manifiesto del backup
        manifest = {
            'timestamp': self.timestamp,
            'version': 'v2',
            'files': backed_up
        }
        
        with open(backup_path / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return backup_path
    
    def check_dependencies(self):
        """Verifica e instala dependencias faltantes"""
        self.log("Verificando dependencias...")
        
        missing_deps = []
        
        # Dependencias nuevas en v3
        new_dependencies = [
            'psutil',     # Para monitoreo del sistema
            'colorlog',   # Para logs con color
            'watchdog',   # Para monitoreo de archivos
            'schedule'    # Para tareas programadas
        ]
        
        for dep in new_dependencies:
            try:
                __import__(dep)
                self.log(f"  ✓ {dep} instalado")
            except ImportError:
                missing_deps.append(dep)
                self.log(f"  ✗ {dep} faltante", "WARNING")
        
        if missing_deps:
            self.log("Instalando dependencias faltantes...")
            import subprocess
            
            for dep in missing_deps:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                    self.log(f"  ✓ {dep} instalado exitosamente")
                except subprocess.CalledProcessError:
                    self.log(f"  ✗ Error instalando {dep}", "ERROR")
        
        return len(missing_deps) == 0
    
    def migrate_configuration(self):
        """Migra archivos de configuración"""
        self.log("Migrando configuración...")
        
        # Actualizar .env con nuevas variables
        env_file = Path('configs/.env')
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            # Nuevas variables para v3
            new_vars = {
                'LOG_LEVEL': 'INFO',
                'USE_BREAKEVEN': 'true',
                'USE_TRAILING': 'true',
                'INITIAL_CAPITAL': '10000',
                'MAX_RISK_PER_TRADE': '0.02',
                'MAX_PORTFOLIO_RISK': '0.06'
            }
            
            added_vars = []
            
            for var, default in new_vars.items():
                if var not in env_content:
                    env_content += f"\n# Añadido en v3\n{var}={default}"
                    added_vars.append(var)
            
            # Guardar .env actualizado
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            if added_vars:
                self.log(f"  Variables añadidas: {', '.join(added_vars)}")
        else:
            self.log("  ⚠️ No se encontró .env", "WARNING")
    
    def cleanup_old_files(self):
        """Limpia archivos duplicados y obsoletos"""
        self.log("Limpiando archivos obsoletos...")
        
        # Lista de archivos a eliminar (duplicados)
        old_files = [
            'BOT.bat',
            'EJECUTAR_BOT.bat',
            'START.bat',
            'START_BOT.bat',
            'INICIAR_BOT.bat',
            'RUN.bat',
            'RUN_BOT.bat',
            'EJECUTAR_AHORA.bat',
            'EJECUTAR_CORREGIDO.bat',
            'EJECUTAR_SISTEMA.bat',
            'CHECK.bat',
            'DETENER_BOT.bat',
            'FIX_AND_RUN.bat',
            'GO.bat',
            'LAUNCHER.bat',
            'MENU_BOT.bat',
            'SISTEMA_PRO.bat',
            'VERIFICAR.bat',
            'VER_ESTADO.bat'
        ]
        
        removed = []
        
        for file in old_files:
            file_path = Path(file)
            if file_path.exists():
                try:
                    file_path.unlink()
                    removed.append(file)
                except Exception as e:
                    self.log(f"  Error eliminando {file}: {e}", "WARNING")
        
        if removed:
            self.log(f"  Archivos eliminados: {len(removed)}")
            
            # Crear archivo con lista de eliminados
            with open(self.backup_dir / f"removed_files_{self.timestamp}.txt", 'w') as f:
                f.write('\n'.join(removed))
    
    def create_symbolic_links(self):
        """Crea enlaces simbólicos para compatibilidad"""
        self.log("Creando enlaces de compatibilidad...")
        
        # Mapeo de archivos antiguos a nuevos
        links = {
            'ejecutar_bot.py': 'main_trader.py',
            'FINAL_BOT.py': 'main_trader.py'
        }
        
        created = []
        
        for old_name, new_name in links.items():
            old_path = Path(old_name)
            new_path = Path(new_name)
            
            if not old_path.exists() and new_path.exists():
                try:
                    # En Windows, crear copia en lugar de symlink
                    if sys.platform == 'win32':
                        shutil.copy2(new_path, old_path)
                    else:
                        old_path.symlink_to(new_path)
                    
                    created.append(old_name)
                except Exception as e:
                    self.log(f"  Error creando enlace {old_name}: {e}", "WARNING")
        
        if created:
            self.log(f"  Enlaces creados: {', '.join(created)}")
    
    def update_imports(self):
        """Actualiza imports en archivos personalizados"""
        self.log("Actualizando imports...")
        
        # Archivos que pueden tener imports personalizados
        custom_files = []
        
        # Buscar archivos Python personalizados
        for file in Path('.').glob('custom_*.py'):
            custom_files.append(file)
        
        for file in Path('.').glob('my_*.py'):
            custom_files.append(file)
        
        if custom_files:
            self.log(f"  Archivos personalizados encontrados: {len(custom_files)}")
            
            # Mapeo de imports antiguos a nuevos
            import_map = {
                'from orchestrator.positions import': 'from orchestrator.run import',
                'from broker.mt5 import init': 'from utils.mt5_connection import MT5ConnectionManager',
                'from notifiers.telegram import send_message': 'from notifiers.telegram import TelegramNotifier'
            }
            
            for file_path in custom_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original = content
                    
                    for old_import, new_import in import_map.items():
                        content = content.replace(old_import, new_import)
                    
                    if content != original:
                        # Backup del archivo original
                        backup_file = self.backup_dir / f"{file_path.name}.bak"
                        shutil.copy2(file_path, backup_file)
                        
                        # Guardar archivo actualizado
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        self.log(f"    ✓ {file_path.name} actualizado")
                except Exception as e:
                    self.log(f"    ✗ Error actualizando {file_path}: {e}", "ERROR")
    
    def verify_migration(self):
        """Verifica que la migración fue exitosa"""
        self.log("Verificando migración...")
        
        checks = {
            'main_trader.py': 'Punto de entrada principal',
            'utils/state_manager.py': 'State Manager',
            'utils/rate_limiter.py': 'Rate Limiter',
            'utils/mt5_connection.py': 'MT5 Connection Manager',
            'TRADER.bat': 'Launcher unificado'
        }
        
        all_ok = True
        
        for file, description in checks.items():
            if Path(file).exists():
                self.log(f"  ✓ {description}")
            else:
                self.log(f"  ✗ {description} faltante", "ERROR")
                all_ok = False
        
        return all_ok
    
    def save_migration_report(self):
        """Guarda reporte de migración"""
        report_file = self.backup_dir / f"migration_report_{self.timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write(f"REPORTE DE MIGRACIÓN - ALGO TRADER v2 -> v3\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            for entry in self.migration_log:
                f.write(entry + "\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("Migración completada\n")
        
        self.log(f"Reporte guardado en: {report_file}")
    
    def rollback(self, backup_path):
        """Revierte la migración desde un backup"""
        self.log("Iniciando rollback...")
        
        try:
            # Leer manifiesto del backup
            manifest_file = backup_path / 'manifest.json'
            
            if not manifest_file.exists():
                self.log("No se encontró manifiesto de backup", "ERROR")
                return False
            
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            # Restaurar archivos
            for item in manifest['files']:
                source = backup_path / Path(item).name
                dest = Path(item)
                
                if source.exists():
                    if source.is_file():
                        shutil.copy2(source, dest)
                    elif source.is_dir():
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    
                    self.log(f"  Restaurado: {item}")
            
            self.log("Rollback completado")
            return True
            
        except Exception as e:
            self.log(f"Error durante rollback: {e}", "ERROR")
            return False
    
    def run(self, skip_backup=False, skip_cleanup=False):
        """
        Ejecuta la migración completa
        
        Args:
            skip_backup: Si saltar el backup
            skip_cleanup: Si saltar la limpieza de archivos
            
        Returns:
            bool: True si la migración fue exitosa
        """
        print("\n" + "="*60)
        print(" "*15 + "MIGRACIÓN ALGO TRADER v2 -> v3")
        print("="*60 + "\n")
        
        try:
            # 1. Backup
            if not skip_backup:
                backup_path = self.backup_current_system()
            else:
                self.log("Saltando backup (--skip-backup)")
            
            # 2. Verificar dependencias
            self.check_dependencies()
            
            # 3. Migrar configuración
            self.migrate_configuration()
            
            # 4. Limpiar archivos obsoletos
            if not skip_cleanup:
                self.cleanup_old_files()
            else:
                self.log("Saltando limpieza (--skip-cleanup)")
            
            # 5. Crear enlaces de compatibilidad
            self.create_symbolic_links()
            
            # 6. Actualizar imports
            self.update_imports()
            
            # 7. Verificar migración
            success = self.verify_migration()
            
            # 8. Guardar reporte
            self.save_migration_report()
            
            if success:
                print("\n" + "="*60)
                print(" "*20 + "✅ MIGRACIÓN EXITOSA")
                print("="*60)
                print("\nPróximos pasos:")
                print("1. Revisa el archivo .env y ajusta las nuevas variables")
                print("2. Ejecuta: python health_check.py")
                print("3. Inicia el sistema: python main_trader.py --mode demo")
                print(f"\nBackup guardado en: {backup_path if not skip_backup else 'N/A'}")
            else:
                print("\n" + "="*60)
                print(" "*20 + "⚠️ MIGRACIÓN CON ADVERTENCIAS")
                print("="*60)
                print("\nRevisa el reporte de migración para más detalles")
                
                if not skip_backup:
                    print(f"\nPara revertir los cambios:")
                    print(f"python migrate.py --rollback {backup_path}")
            
            return success
            
        except Exception as e:
            self.log(f"Error fatal durante migración: {e}", "ERROR")
            self.save_migration_report()
            
            print("\n" + "="*60)
            print(" "*20 + "❌ MIGRACIÓN FALLIDA")
            print("="*60)
            print(f"\nError: {e}")
            
            if not skip_backup and 'backup_path' in locals():
                print(f"\nPara revertir los cambios:")
                print(f"python migrate.py --rollback {backup_path}")
            
            return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Herramienta de migración de Algo Trader v2 a v3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python migrate.py                    # Migración completa con backup
  python migrate.py --skip-backup      # Migración sin backup
  python migrate.py --skip-cleanup     # Migración sin eliminar archivos
  python migrate.py --rollback backups/backup_v2_20250101_120000  # Revertir
        """
    )
    
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Saltar creación de backup"
    )
    
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="No eliminar archivos obsoletos"
    )
    
    parser.add_argument(
        "--rollback",
        type=str,
        metavar="PATH",
        help="Revertir migración desde backup"
    )
    
    parser.add_argument(
        "--backup-dir",
        type=str,
        default="backups",
        help="Directorio para backups (default: backups)"
    )
    
    args = parser.parse_args()
    
    # Crear migrador
    migrator = AlgoTraderMigration(backup_dir=args.backup_dir)
    
    # Ejecutar rollback si se especifica
    if args.rollback:
        backup_path = Path(args.rollback)
        if not backup_path.exists():
            print(f"❌ No se encontró el backup: {backup_path}")
            sys.exit(1)
        
        success = migrator.rollback(backup_path)
        sys.exit(0 if success else 1)
    
    # Ejecutar migración
    success = migrator.run(
        skip_backup=args.skip_backup,
        skip_cleanup=args.skip_cleanup
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
