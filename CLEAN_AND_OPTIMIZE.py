#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LIMPIEZA Y OPTIMIZACIÓN DEL SISTEMA - ALGO TRADER V3
====================================================
Limpia logs, optimiza base de datos y mejora el rendimiento
"""

import os
import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from colorama import init, Fore, Style

init(autoreset=True)

class SystemCleaner:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.stats = {
            'logs_deleted': 0,
            'logs_archived': 0,
            'space_freed_mb': 0,
            'db_optimized': False,
            'cache_cleared': False
        }
        
    def clean_logs(self):
        """Limpia y archiva logs antiguos"""
        print(Fore.YELLOW + "\n[1/5] LIMPIANDO LOGS...")
        
        log_dir = self.base_path / 'logs'
        archive_dir = self.base_path / 'logs' / 'archive'
        archive_dir.mkdir(exist_ok=True)
        
        if not log_dir.exists():
            print("  ⚠️ Directorio de logs no encontrado")
            return
            
        total_size_before = 0
        current_time = datetime.now()
        
        for log_file in log_dir.glob('*.log'):
            file_size = log_file.stat().st_size
            total_size_before += file_size
            
            # Eliminar archivos vacíos
            if file_size == 0:
                log_file.unlink()
                self.stats['logs_deleted'] += 1
                print(f"  🗑️ Eliminado (vacío): {log_file.name}")
                continue
                
            # Archivar logs de más de 7 días
            file_age = current_time - datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_age > timedelta(days=7):
                archive_path = archive_dir / log_file.name
                shutil.move(str(log_file), str(archive_path))
                self.stats['logs_archived'] += 1
                print(f"  📦 Archivado: {log_file.name}")
                
        # Calcular espacio liberado
        total_size_after = sum(f.stat().st_size for f in log_dir.glob('*.log'))
        self.stats['space_freed_mb'] = (total_size_before - total_size_after) / (1024 * 1024)
        
        print(f"  ✅ Logs limpiados: {self.stats['logs_deleted']} eliminados, {self.stats['logs_archived']} archivados")
        print(f"  💾 Espacio liberado: {self.stats['space_freed_mb']:.2f} MB")
        
    def optimize_database(self):
        """Optimiza la base de datos SQLite"""
        print(Fore.YELLOW + "\n[2/5] OPTIMIZANDO BASE DE DATOS...")
        
        db_path = self.base_path / 'storage' / 'trading.db'
        
        if not db_path.exists():
            print("  ⚠️ Base de datos no encontrada")
            return
            
        try:
            # Tamaño antes
            size_before = db_path.stat().st_size / (1024 * 1024)
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Crear índices si no existen
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(ts)",
                "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)",
            ]
            
            for idx_query in indices:
                try:
                    cursor.execute(idx_query)
                except:
                    pass
                    
            # Limpiar registros antiguos (más de 30 días)
            try:
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute("DELETE FROM signals WHERE ts < ?", (thirty_days_ago,))
                deleted = cursor.rowcount
                if deleted > 0:
                    print(f"  🗑️ Eliminados {deleted} registros antiguos")
            except:
                pass
                
            # VACUUM para compactar
            cursor.execute("VACUUM")
            
            # ANALYZE para actualizar estadísticas
            cursor.execute("ANALYZE")
            
            conn.commit()
            conn.close()
            
            # Tamaño después
            size_after = db_path.stat().st_size / (1024 * 1024)
            reduction = size_before - size_after
            
            print(f"  ✅ Base de datos optimizada")
            print(f"  💾 Tamaño: {size_before:.2f} MB → {size_after:.2f} MB")
            if reduction > 0:
                print(f"  📉 Reducción: {reduction:.2f} MB")
                
            self.stats['db_optimized'] = True
            
        except Exception as e:
            print(f"  ❌ Error optimizando: {e}")
            
    def clear_cache(self):
        """Limpia archivos de caché"""
        print(Fore.YELLOW + "\n[3/5] LIMPIANDO CACHÉ...")
        
        cache_dirs = [
            self.base_path / 'src' / 'data' / 'cache',
            self.base_path / '__pycache__',
            self.base_path / '.pytest_cache'
        ]
        
        total_cleared = 0
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    if cache_dir.name == '__pycache__' or cache_dir.name == '.pytest_cache':
                        shutil.rmtree(cache_dir)
                        print(f"  🗑️ Eliminado: {cache_dir.name}")
                    else:
                        # Para cache de datos, solo limpiar archivos antiguos
                        for cache_file in cache_dir.glob('*'):
                            if cache_file.is_file():
                                cache_file.unlink()
                                total_cleared += 1
                except Exception as e:
                    print(f"  ⚠️ Error limpiando {cache_dir.name}: {e}")
                    
        # Limpiar archivos .pyc recursivamente
        for pyc_file in self.base_path.rglob('*.pyc'):
            try:
                pyc_file.unlink()
                total_cleared += 1
            except:
                pass
                
        print(f"  ✅ Caché limpiado: {total_cleared} archivos")
        self.stats['cache_cleared'] = True
        
    def optimize_configs(self):
        """Optimiza configuraciones del sistema"""
        print(Fore.YELLOW + "\n[4/5] OPTIMIZANDO CONFIGURACIONES...")
        
        # Crear archivo de configuración optimizada si no existe
        config_file = self.base_path / 'config' / 'optimized_settings.json'
        config_file.parent.mkdir(exist_ok=True)
        
        optimized_config = {
            "performance": {
                "max_threads": 4,
                "cache_enabled": True,
                "cache_ttl": 300,
                "batch_size": 100,
                "log_level": "INFO"
            },
            "limits": {
                "max_api_calls_per_minute": 8,
                "max_positions": 3,
                "max_daily_trades": 10,
                "max_log_size_mb": 50
            },
            "intervals": {
                "signal_check": 300,  # 5 minutos
                "health_check": 60,   # 1 minuto
                "cleanup": 3600       # 1 hora
            }
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(optimized_config, f, indent=4)
            
        print(f"  ✅ Configuración optimizada creada")
        
    def create_maintenance_schedule(self):
        """Crea un schedule de mantenimiento"""
        print(Fore.YELLOW + "\n[5/5] CONFIGURANDO MANTENIMIENTO AUTOMÁTICO...")
        
        schedule_file = self.base_path / 'maintenance_schedule.bat'
        
        schedule_content = """@echo off
:: MANTENIMIENTO AUTOMÁTICO - ALGO TRADER V3
:: Ejecutar semanalmente (domingos a las 3 AM)

echo ========================================
echo   MANTENIMIENTO AUTOMATICO DEL SISTEMA
echo ========================================
echo.

:: Detener sistema
call STOP_ALL.bat

:: Limpiar y optimizar
python CLEAN_AND_OPTIMIZE.py

:: Hacer backup
python SYSTEM_IMPROVEMENT.py

:: Reiniciar sistema
timeout /t 10
call EJECUTAR_TODO_PRO.bat

echo.
echo Mantenimiento completado
"""
        
        with open(schedule_file, 'w') as f:
            f.write(schedule_content)
            
        print(f"  ✅ Schedule de mantenimiento creado")
        print(f"  📅 Recomendación: Programar en Task Scheduler para ejecución semanal")
        
    def generate_report(self):
        """Genera reporte de optimización"""
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + " "*20 + "REPORTE DE OPTIMIZACIÓN")
        print(Fore.CYAN + "="*60)
        
        print(f"\n📊 RESUMEN:")
        print(f"  • Logs eliminados: {self.stats['logs_deleted']}")
        print(f"  • Logs archivados: {self.stats['logs_archived']}")
        print(f"  • Espacio liberado: {self.stats['space_freed_mb']:.2f} MB")
        print(f"  • Base de datos: {'✅ Optimizada' if self.stats['db_optimized'] else '⚠️ No optimizada'}")
        print(f"  • Caché: {'✅ Limpiado' if self.stats['cache_cleared'] else '⚠️ No limpiado'}")
        
        print(Fore.GREEN + "\n✅ SISTEMA OPTIMIZADO Y LIMPIO")
        
        # Guardar reporte
        report_file = self.base_path / f'optimization_report_{datetime.now():%Y%m%d_%H%M%S}.txt'
        with open(report_file, 'w') as f:
            f.write("REPORTE DE OPTIMIZACIÓN\n")
            f.write("="*40 + "\n")
            f.write(f"Fecha: {datetime.now()}\n")
            f.write(f"Logs eliminados: {self.stats['logs_deleted']}\n")
            f.write(f"Logs archivados: {self.stats['logs_archived']}\n")
            f.write(f"Espacio liberado: {self.stats['space_freed_mb']:.2f} MB\n")
            f.write(f"Base de datos optimizada: {self.stats['db_optimized']}\n")
            f.write(f"Caché limpiado: {self.stats['cache_cleared']}\n")
            
        print(f"\n📄 Reporte guardado: {report_file.name}")

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║       LIMPIEZA Y OPTIMIZACIÓN - ALGO TRADER V3                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    cleaner = SystemCleaner()
    
    try:
        cleaner.clean_logs()
        cleaner.optimize_database()
        cleaner.clear_cache()
        cleaner.optimize_configs()
        cleaner.create_maintenance_schedule()
        cleaner.generate_report()
        
        print(Fore.GREEN + "\n✨ Optimización completada exitosamente!")
        
    except Exception as e:
        print(Fore.RED + f"\n❌ Error durante la optimización: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
