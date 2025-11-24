"""
Script para crear archivos ZIP con los componentes importantes del proyecto
"""
import zipfile
import os
from pathlib import Path
from datetime import datetime

# Directorio base del proyecto
BASE_DIR = Path(r"C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2")
BACKUP_DIR = BASE_DIR / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Crear directorio de backups
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def add_files_to_zip(zip_file, files, base_path=BASE_DIR):
    """Agregar archivos al ZIP"""
    added = 0
    for file_pattern in files:
        if '*' in file_pattern:
            # Es un patrón glob
            for file_path in base_path.glob(file_pattern):
                if file_path.is_file() and file_path.stat().st_size < 10_000_000:  # Max 10MB
                    arcname = str(file_path.relative_to(base_path))
                    try:
                        zip_file.write(file_path, arcname)
                        added += 1
                    except Exception as e:
                        print(f"  Error: {file_path.name}: {e}")
        else:
            file_path = base_path / file_pattern
            if file_path.exists() and file_path.is_file():
                arcname = str(file_path.relative_to(base_path))
                try:
                    zip_file.write(file_path, arcname)
                    added += 1
                except Exception as e:
                    print(f"  Error: {file_path.name}: {e}")
    return added

def add_directory_to_zip(zip_file, dir_name, base_path=BASE_DIR, extensions=None):
    """Agregar directorio completo al ZIP"""
    dir_path = base_path / dir_name
    added = 0
    if dir_path.exists():
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                # Filtrar por extensión si se especifica
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                # Ignorar __pycache__ y archivos muy grandes
                if '__pycache__' in str(file_path):
                    continue
                if file_path.stat().st_size > 10_000_000:  # Max 10MB
                    continue
                arcname = str(file_path.relative_to(base_path))
                try:
                    zip_file.write(file_path, arcname)
                    added += 1
                except Exception as e:
                    print(f"  Error: {file_path.name}: {e}")
    return added

print("=" * 60)
print("CREANDO BACKUPS DEL PROYECTO ALGO-TRADER")
print("=" * 60)
print(f"Directorio de backups: {BACKUP_DIR}\n")

# 1. SISTEMAS PRINCIPALES DE TRADING
print("1. Creando ZIP: SISTEMAS_PRINCIPALES.zip")
sistemas_principales = [
    "START_TRADING_SYSTEM.py",
    "START_TRADING_SYSTEM_FIXED.py",
    "START_TRADING_SYSTEM_MONITOR_PRIORITY.py",
    "START_TRADING_SYSTEM_MONITOR_PRIORITY_CLEAN.py",
    "START_TRADING_SYSTEM_TECHNICAL_ONLY.py",
    "START_TRADING_SYSTEM_CON_DIRECTOR.py",
    "QUANTUM_TRADING_SYSTEM.py",
    "SISTEMA_DEFINITIVO_FUNCIONAL.py",
    "SISTEMA_COMPLETO_FUNCIONAL.py",
    "SISTEMA_COMPLETO_INTEGRADO.py",
    "SISTEMA_OPTIMIZADO.py",
    "SISTEMA_PERMANENTE.py",
    "SISTEMA_INTEGRADO_IA_ETHAN.py",
    "pro_trading_bot.py",
    "enhanced_trading_bot.py",
    "enhanced_trading_bot_v2.py",
    "FINAL_BOT.py",
    "simple_bot.py",
    "main.py",
    "launcher.py",
    "launcher_pro.py",
]
with zipfile.ZipFile(BACKUP_DIR / "01_SISTEMAS_PRINCIPALES.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, sistemas_principales)
print(f"   -> {count} archivos agregados\n")

# 2. CÓDIGO FUENTE (src/)
print("2. Creando ZIP: CODIGO_FUENTE_SRC.zip")
with zipfile.ZipFile(BACKUP_DIR / "02_CODIGO_FUENTE_SRC.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_directory_to_zip(zf, "src", extensions=['.py', '.json', '.yaml', '.yml'])
print(f"   -> {count} archivos agregados\n")

# 3. CORE MODULES
print("3. Creando ZIP: CORE_MODULES.zip")
with zipfile.ZipFile(BACKUP_DIR / "03_CORE_MODULES.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_directory_to_zip(zf, "core", extensions=['.py', '.json'])
print(f"   -> {count} archivos agregados\n")

# 4. MÓDULOS DE IA
print("4. Creando ZIP: MODULOS_IA.zip")
ai_files = [
    "AI_*.py",
    "OLLAMA_*.py",
    "DEEPSEEK_*.py",
    "ANALISIS_IA_*.py",
    "ANALISIS_MERCADO_IA_PERSONAL.py",
]
with zipfile.ZipFile(BACKUP_DIR / "04_MODULOS_IA.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, ai_files)
    count += add_directory_to_zip(zf, "ai", extensions=['.py', '.json'])
    count += add_directory_to_zip(zf, "ml", extensions=['.py', '.json', '.pkl', '.joblib'])
print(f"   -> {count} archivos agregados\n")

# 5. CONFIGURACIONES
print("5. Creando ZIP: CONFIGURACIONES.zip")
config_files = [
    ".env",
    ".env.example",
    "requirements.txt",
    "requirements_*.txt",
    "setup.py",
    "config/*",
    "configs/*",
]
with zipfile.ZipFile(BACKUP_DIR / "05_CONFIGURACIONES.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, config_files)
    count += add_directory_to_zip(zf, "config")
    count += add_directory_to_zip(zf, "configs")
print(f"   -> {count} archivos agregados\n")

# 6. UTILIDADES
print("6. Creando ZIP: UTILIDADES.zip")
with zipfile.ZipFile(BACKUP_DIR / "06_UTILIDADES.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_directory_to_zip(zf, "utils", extensions=['.py'])
    count += add_directory_to_zip(zf, "tools", extensions=['.py'])
print(f"   -> {count} archivos agregados\n")

# 7. SEÑALES Y ESTRATEGIAS
print("7. Creando ZIP: SENALES_ESTRATEGIAS.zip")
signal_files = [
    "SIGNAL_*.py",
    "GENERATE_*.py",
    "ADVANCED_SIGNAL_GENERATOR.py",
    "signal_executor.py",
    "simple_signals.py",
]
with zipfile.ZipFile(BACKUP_DIR / "07_SENALES_ESTRATEGIAS.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, signal_files)
    count += add_directory_to_zip(zf, "signals", extensions=['.py', '.json'])
print(f"   -> {count} archivos agregados\n")

# 8. GESTIÓN DE RIESGO
print("8. Creando ZIP: GESTION_RIESGO.zip")
risk_files = [
    "EMERGENCY_*.py",
    "APPLY_BREAKEVEN_*.py",
    "APLICAR_BREAKEVEN_*.py",
    "APLICAR_TRAILING_*.py",
    "TRAILING_*.py",
    "SMART_BREAKEVEN_*.py",
    "ADVANCED_AI_TRAILING_SYSTEM.py",
    "PROTEGER_GANANCIAS_*.py",
    "ASEGURAR_GANANCIAS.py",
    "risk_simple.py",
]
with zipfile.ZipFile(BACKUP_DIR / "08_GESTION_RIESGO.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, risk_files)
    count += add_directory_to_zip(zf, "risk", extensions=['.py'])
print(f"   -> {count} archivos agregados\n")

# 9. DASHBOARDS
print("9. Creando ZIP: DASHBOARDS.zip")
dashboard_files = [
    "*dashboard*.py",
    "DASHBOARD_*.py",
    "launch_*.py",
    "chart_*.py",
    "charts_dashboard.py",
    "VISOR_*.py",
]
with zipfile.ZipFile(BACKUP_DIR / "09_DASHBOARDS.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, dashboard_files)
    count += add_directory_to_zip(zf, "dashboard", extensions=['.py', '.html', '.css', '.js'])
print(f"   -> {count} archivos agregados\n")

# 10. MONITORES
print("10. Creando ZIP: MONITORES.zip")
monitor_files = [
    "MONITOR*.py",
    "monitor_*.py",
    "CHECK_*.py",
    "check_*.py",
    "DIAGNOSTICO*.py",
    "VERIFICAR_*.py",
    "verificar_*.py",
]
with zipfile.ZipFile(BACKUP_DIR / "10_MONITORES.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, monitor_files)
print(f"   -> {count} archivos agregados\n")

# 11. DOCUMENTACIÓN
print("11. Creando ZIP: DOCUMENTACION.zip")
doc_files = [
    "README*.md",
    "*.md",
    "docs/*",
]
with zipfile.ZipFile(BACKUP_DIR / "11_DOCUMENTACION.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, doc_files)
    count += add_directory_to_zip(zf, "docs", extensions=['.md', '.txt', '.rst', '.pdf'])
print(f"   -> {count} archivos agregados\n")

# 12. SCRIPTS BAT/PS1
print("12. Creando ZIP: SCRIPTS_EJECUCION.zip")
script_files = [
    "*.bat",
    "*.ps1",
]
with zipfile.ZipFile(BACKUP_DIR / "12_SCRIPTS_EJECUCION.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, script_files)
print(f"   -> {count} archivos agregados\n")

# 13. BROKER/MT5 INTEGRATION
print("13. Creando ZIP: BROKER_MT5.zip")
broker_files = [
    "CONECTAR_MT5.py",
    "EXNESS_*.py",
    "MT5_*.py",
    "abrir_mt5.py",
    "activate_symbols.py",
    "*.mq5",
]
with zipfile.ZipFile(BACKUP_DIR / "13_BROKER_MT5.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, broker_files)
    count += add_directory_to_zip(zf, "broker", extensions=['.py', '.mq5', '.mq4'])
print(f"   -> {count} archivos agregados\n")

# 14. NOTIFICADORES (Telegram)
print("14. Creando ZIP: NOTIFICADORES.zip")
with zipfile.ZipFile(BACKUP_DIR / "14_NOTIFICADORES.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_directory_to_zip(zf, "notifiers", extensions=['.py'])
    # Agregar archivos de telegram
    telegram_files = ["*TELEGRAM*.py", "*telegram*.py"]
    count += add_files_to_zip(zf, telegram_files)
print(f"   -> {count} archivos agregados\n")

# 15. BACKTESTING
print("15. Creando ZIP: BACKTESTING.zip")
backtest_files = [
    "backtester.py",
]
with zipfile.ZipFile(BACKUP_DIR / "15_BACKTESTING.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    count = add_files_to_zip(zf, backtest_files)
    count += add_directory_to_zip(zf, "backtesting", extensions=['.py', '.json'])
print(f"   -> {count} archivos agregados\n")

# RESUMEN FINAL
print("=" * 60)
print("BACKUP COMPLETADO")
print("=" * 60)
print(f"\nUbicación: {BACKUP_DIR}")
print("\nArchivos ZIP creados:")
for zip_file in sorted(BACKUP_DIR.glob("*.zip")):
    size_mb = zip_file.stat().st_size / (1024 * 1024)
    print(f"  - {zip_file.name} ({size_mb:.2f} MB)")

total_size = sum(f.stat().st_size for f in BACKUP_DIR.glob("*.zip")) / (1024 * 1024)
print(f"\nTamaño total: {total_size:.2f} MB")
print("\n¡Backups creados exitosamente!")
