"""
Verificación Rápida del Sistema
"""
import os
import sys

print("\n" + "="*60)
print(" VERIFICACIÓN DEL SISTEMA ALGO TRADER v3.0")
print("="*60)

# Verificar Python
print(f"\n✅ Python {sys.version}")

# Verificar módulos críticos
modules_to_check = [
    'pandas',
    'numpy', 
    'requests',
    'MetaTrader5',
    'aiohttp',
    'dotenv'
]

print("\n📦 Verificando módulos:")
missing = []

for module in modules_to_check:
    try:
        __import__(module)
        print(f"  ✅ {module}")
    except ImportError:
        print(f"  ❌ {module} - NO INSTALADO")
        missing.append(module)

# Verificar estructura de archivos
print("\n📂 Verificando estructura:")
dirs = ['broker', 'core', 'data', 'ml', 'risk', 'signals', 'notifiers', 'utils', 'configs', 'logs', 'storage']
for dir_name in dirs:
    if os.path.exists(dir_name):
        print(f"  ✅ {dir_name}/")
    else:
        print(f"  ❌ {dir_name}/ - NO EXISTE")
        os.makedirs(dir_name, exist_ok=True)
        print(f"     ➜ Creado {dir_name}/")

# Verificar archivos principales
print("\n📄 Verificando archivos principales:")
files = [
    'main.py',
    'configs/.env',
    'broker/mt5_connection.py',
    'core/bot_manager.py',
    'data/data_manager.py',
    'risk/risk_manager.py'
]

for file in files:
    if os.path.exists(file):
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} - NO EXISTE")

# Resumen
print("\n" + "="*60)
if missing:
    print("⚠️  ACCIÓN REQUERIDA:")
    print("\nInstala los módulos faltantes con:")
    print(f"pip install {' '.join(missing)}")
    
    print("\nO ejecuta:")
    print("pip install pandas numpy requests MetaTrader5 python-dotenv aiohttp colorlog")
else:
    print("✅ SISTEMA LISTO PARA USAR")
    print("\nEjecuta START_SYSTEM.bat para comenzar")

print("="*60)
