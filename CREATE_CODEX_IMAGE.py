"""
Genera un archivo de imagen del proyecto para OpenAI Codex
Incluye toda la estructura, código fuente y documentación
"""
import os
from pathlib import Path
from datetime import datetime

# Configuración
BASE_DIR = Path(r"C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2")
OUTPUT_DIR = BASE_DIR / "codex_export"
OUTPUT_DIR.mkdir(exist_ok=True)

# Extensiones a incluir
CODE_EXTENSIONS = {'.py', '.mq5', '.mq4'}
CONFIG_EXTENSIONS = {'.env', '.yaml', '.yml', '.json', '.txt', '.ini'}
DOC_EXTENSIONS = {'.md', '.rst'}

# Directorios a ignorar
IGNORE_DIRS = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', 'env',
               'backups', 'logs', 'data', 'charts', 'assets', 'storage',
               'codex_export', 'advanced_charts', 'deprecated', 'tests'}

# Archivos a ignorar por patrón
IGNORE_PATTERNS = {'reporte_detallado_', 'diario_trades_', '.log', '.pkl', '.joblib'}

# Límite de tamaño por archivo (100KB)
MAX_FILE_SIZE = 100 * 1024

def should_ignore(path):
    """Verificar si un archivo o directorio debe ignorarse"""
    path_str = str(path).lower()

    # Ignorar directorios específicos
    for ignore_dir in IGNORE_DIRS:
        if ignore_dir.lower() in path_str.split(os.sep):
            return True

    # Ignorar patrones
    for pattern in IGNORE_PATTERNS:
        if pattern.lower() in path_str.lower():
            return True

    return False

def get_file_content(file_path, max_size=MAX_FILE_SIZE):
    """Obtener contenido de un archivo con límite de tamaño"""
    try:
        if file_path.stat().st_size > max_size:
            return f"[ARCHIVO MUY GRANDE: {file_path.stat().st_size / 1024:.1f}KB - TRUNCADO]"

        # Intentar leer con diferentes encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        return "[ERROR: No se pudo decodificar el archivo]"
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def generate_tree(directory, prefix="", max_depth=3, current_depth=0):
    """Generar árbol de directorios"""
    if current_depth >= max_depth:
        return ""

    tree = ""
    try:
        entries = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        entries = [e for e in entries if not should_ignore(e)]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                tree += f"{prefix}{connector}{entry.name}/\n"
                extension = "    " if is_last else "│   "
                tree += generate_tree(entry, prefix + extension, max_depth, current_depth + 1)
            else:
                size = entry.stat().st_size / 1024
                tree += f"{prefix}{connector}{entry.name} ({size:.1f}KB)\n"
    except PermissionError:
        pass

    return tree

def collect_files_by_category(base_dir):
    """Recolectar archivos organizados por categoría"""
    categories = {
        'SISTEMAS_PRINCIPALES': [],
        'CODIGO_FUENTE_SRC': [],
        'MODULOS_IA': [],
        'SENALES_ESTRATEGIAS': [],
        'GESTION_RIESGO': [],
        'BROKER_MT5': [],
        'CONFIGURACION': [],
        'UTILIDADES': [],
        'DOCUMENTACION': [],
    }

    # Sistemas principales (archivos en raíz)
    main_systems = [
        'START_TRADING_SYSTEM.py', 'START_TRADING_SYSTEM_MONITOR_PRIORITY_CLEAN.py',
        'QUANTUM_TRADING_SYSTEM.py', 'SISTEMA_DEFINITIVO_FUNCIONAL.py',
        'SISTEMA_COMPLETO_FUNCIONAL.py', 'pro_trading_bot.py', 'main.py',
        'launcher.py', 'enhanced_trading_bot.py', 'FINAL_BOT.py'
    ]

    for name in main_systems:
        path = base_dir / name
        if path.exists():
            categories['SISTEMAS_PRINCIPALES'].append(path)

    # Código fuente src/
    src_dir = base_dir / 'src'
    if src_dir.exists():
        for file_path in src_dir.rglob('*.py'):
            if not should_ignore(file_path):
                categories['CODIGO_FUENTE_SRC'].append(file_path)

    # Módulos IA
    for pattern in ['AI_*.py', 'OLLAMA_*.py', 'DEEPSEEK_*.py']:
        for file_path in base_dir.glob(pattern):
            if not should_ignore(file_path):
                categories['MODULOS_IA'].append(file_path)

    ai_dir = base_dir / 'ai'
    if ai_dir.exists():
        for file_path in ai_dir.rglob('*.py'):
            if not should_ignore(file_path):
                categories['MODULOS_IA'].append(file_path)

    # Señales y estrategias
    signals_dir = base_dir / 'signals'
    if signals_dir.exists():
        for file_path in signals_dir.rglob('*.py'):
            if not should_ignore(file_path):
                categories['SENALES_ESTRATEGIAS'].append(file_path)

    for pattern in ['SIGNAL_*.py', 'GENERATE_*.py', 'ADVANCED_SIGNAL_GENERATOR.py']:
        for file_path in base_dir.glob(pattern):
            if not should_ignore(file_path) and file_path not in categories['SENALES_ESTRATEGIAS']:
                categories['SENALES_ESTRATEGIAS'].append(file_path)

    # Gestión de riesgo
    risk_dir = base_dir / 'risk'
    if risk_dir.exists():
        for file_path in risk_dir.rglob('*.py'):
            if not should_ignore(file_path):
                categories['GESTION_RIESGO'].append(file_path)

    for pattern in ['EMERGENCY_*.py', 'TRAILING_*.py', 'BREAKEVEN_*.py', 'APLICAR_*.py']:
        for file_path in base_dir.glob(pattern):
            if not should_ignore(file_path) and file_path not in categories['GESTION_RIESGO']:
                categories['GESTION_RIESGO'].append(file_path)

    # Broker/MT5
    broker_dir = base_dir / 'broker'
    if broker_dir.exists():
        for file_path in broker_dir.rglob('*'):
            if file_path.is_file() and not should_ignore(file_path):
                if file_path.suffix in CODE_EXTENSIONS:
                    categories['BROKER_MT5'].append(file_path)

    for pattern in ['EXNESS_*.py', 'MT5_*.py', 'CONECTAR_MT5.py', '*.mq5']:
        for file_path in base_dir.glob(pattern):
            if not should_ignore(file_path) and file_path not in categories['BROKER_MT5']:
                categories['BROKER_MT5'].append(file_path)

    # Configuración
    for pattern in ['.env', '.env.example', 'requirements*.txt', 'setup.py']:
        for file_path in base_dir.glob(pattern):
            if not should_ignore(file_path):
                categories['CONFIGURACION'].append(file_path)

    for config_dir in ['config', 'configs']:
        cd = base_dir / config_dir
        if cd.exists():
            for file_path in cd.rglob('*'):
                if file_path.is_file() and not should_ignore(file_path):
                    categories['CONFIGURACION'].append(file_path)

    # Utilidades
    for util_dir in ['utils', 'tools', 'core']:
        ud = base_dir / util_dir
        if ud.exists():
            for file_path in ud.rglob('*.py'):
                if not should_ignore(file_path):
                    categories['UTILIDADES'].append(file_path)

    # Documentación
    for file_path in base_dir.glob('*.md'):
        if not should_ignore(file_path):
            categories['DOCUMENTACION'].append(file_path)

    docs_dir = base_dir / 'docs'
    if docs_dir.exists():
        for file_path in docs_dir.rglob('*.md'):
            if not should_ignore(file_path):
                categories['DOCUMENTACION'].append(file_path)

    # Eliminar duplicados y ordenar
    for cat in categories:
        categories[cat] = sorted(set(categories[cat]), key=lambda x: str(x))

    return categories

print("=" * 70)
print("GENERANDO IMAGEN DEL PROYECTO PARA OPENAI CODEX")
print("=" * 70)
print(f"Directorio base: {BASE_DIR}")
print(f"Directorio salida: {OUTPUT_DIR}\n")

# Recolectar archivos
print("Recolectando archivos...")
categories = collect_files_by_category(BASE_DIR)

total_files = sum(len(files) for files in categories.values())
print(f"Total de archivos a incluir: {total_files}\n")

# Generar archivo principal para Codex
output_file = OUTPUT_DIR / "ALGO_TRADER_CODEX_IMAGE.txt"

with open(output_file, 'w', encoding='utf-8') as f:
    # Header
    f.write("=" * 80 + "\n")
    f.write("ALGO-TRADER MVP V2 - PROYECTO COMPLETO PARA OPENAI CODEX\n")
    f.write("=" * 80 + "\n")
    f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Archivos incluidos: {total_files}\n")
    f.write("=" * 80 + "\n\n")

    # Descripción del proyecto
    f.write("## DESCRIPCION DEL PROYECTO\n\n")
    f.write("""
Sistema de trading algorítmico automatizado para MetaTrader 5 (Exness).

CARACTERISTICAS PRINCIPALES:
- Trading automatizado 24/7 con múltiples estrategias
- Integración de IA (Ollama/DeepSeek) para análisis de mercado
- Sistema cuántico de trading basado en física
- Gestión de riesgo avanzada con ATR dinámico
- Dashboards en tiempo real con Streamlit
- Notificaciones por Telegram
- Soporte para Forex, Crypto y Metales

TECNOLOGIAS:
- Python 3.9+
- MetaTrader 5 API
- TwelveData API (datos de mercado)
- Ollama (IA local con DeepSeek)
- Streamlit (dashboards)
- Scikit-learn (ML)

SIMBOLOS SOPORTADOS:
- EURUSD, GBPUSD (Forex)
- XAUUSD (Oro)
- BTCUSD, ETHUSD (Crypto)
""")
    f.write("\n" + "=" * 80 + "\n\n")

    # Estructura del proyecto
    f.write("## ESTRUCTURA DEL PROYECTO\n\n")
    f.write("```\n")
    f.write("algo-trader-mvp-v2/\n")
    f.write(generate_tree(BASE_DIR, max_depth=2))
    f.write("```\n\n")
    f.write("=" * 80 + "\n\n")

    # Contenido por categoría
    for category, files in categories.items():
        if not files:
            continue

        f.write(f"\n{'#' * 80}\n")
        f.write(f"## {category}\n")
        f.write(f"{'#' * 80}\n")
        f.write(f"# Archivos: {len(files)}\n\n")

        for file_path in files:
            relative_path = file_path.relative_to(BASE_DIR)
            f.write(f"\n{'=' * 70}\n")
            f.write(f"### FILE: {relative_path}\n")
            f.write(f"{'=' * 70}\n\n")

            content = get_file_content(file_path)

            # Detectar tipo de archivo para syntax highlighting
            ext = file_path.suffix.lower()
            lang = {
                '.py': 'python',
                '.mq5': 'cpp',
                '.mq4': 'cpp',
                '.json': 'json',
                '.yaml': 'yaml',
                '.yml': 'yaml',
                '.md': 'markdown',
                '.env': 'bash',
                '.txt': 'text',
            }.get(ext, 'text')

            f.write(f"```{lang}\n")
            f.write(content)
            if not content.endswith('\n'):
                f.write('\n')
            f.write("```\n")

        print(f"  {category}: {len(files)} archivos")

print(f"\nArchivo generado: {output_file}")
print(f"Tamaño: {output_file.stat().st_size / (1024*1024):.2f} MB")

# Generar también versiones más pequeñas por categoría
print("\nGenerando archivos por categoría...")

for category, files in categories.items():
    if not files:
        continue

    cat_file = OUTPUT_DIR / f"CODEX_{category}.txt"

    with open(cat_file, 'w', encoding='utf-8') as f:
        f.write(f"# {category} - ALGO TRADER MVP V2\n")
        f.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Archivos: {len(files)}\n\n")

        for file_path in files:
            relative_path = file_path.relative_to(BASE_DIR)
            f.write(f"\n{'=' * 60}\n")
            f.write(f"# FILE: {relative_path}\n")
            f.write(f"{'=' * 60}\n\n")

            content = get_file_content(file_path)
            f.write(content)
            if not content.endswith('\n'):
                f.write('\n')

    size_kb = cat_file.stat().st_size / 1024
    print(f"  {cat_file.name}: {size_kb:.1f} KB")

# Resumen final
print("\n" + "=" * 70)
print("EXPORTACION COMPLETADA")
print("=" * 70)
print(f"\nDirectorio: {OUTPUT_DIR}")
print("\nArchivos generados:")
for f in sorted(OUTPUT_DIR.glob("*.txt")):
    size = f.stat().st_size / 1024
    print(f"  - {f.name} ({size:.1f} KB)")

total_size = sum(f.stat().st_size for f in OUTPUT_DIR.glob("*.txt")) / (1024*1024)
print(f"\nTamaño total: {total_size:.2f} MB")
print("\nEstos archivos están listos para usar con OpenAI Codex!")
