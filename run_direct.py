"""
EJECUTOR DIRECTO SIN ENTORNO VIRTUAL
Ejecuta el bot usando el Python del sistema
"""
import sys
import os
import subprocess

print("="*70)
print(" "*20 + "SOLUCIONANDO PROBLEMA DE PYTHON")
print("="*70)
print()

# Cambiar al directorio correcto
os.chdir(r"C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2")

print("1. Verificando Python del sistema...")

# Buscar Python
python_paths = [
    r"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe",
    r"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe",
    r"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe",
    r"C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe",
    r"C:\Python313\python.exe",
    r"C:\Python312\python.exe",
    r"C:\Python311\python.exe",
    r"C:\Python310\python.exe",
]

python_exe = None
for path in python_paths:
    if os.path.exists(path):
        python_exe = path
        print(f"   ✅ Python encontrado: {path}")
        break

if not python_exe:
    # Intentar con el Python del PATH
    try:
        result = subprocess.run(["python", "--version"], capture_output=True)
        if result.returncode == 0:
            python_exe = "python"
            print(f"   ✅ Python encontrado en el PATH")
    except:
        pass

if not python_exe:
    print("   ❌ No se encontró Python")
    print("\nInstala Python desde: https://python.org/downloads/")
    input("\nPresiona Enter para salir...")
    sys.exit(1)

print()
print("2. Instalando librerías necesarias...")

# Instalar librerías esenciales
libs = [
    "MetaTrader5",
    "python-dotenv",
    "pandas",
    "numpy", 
    "requests",
    "openai",
    "pyyaml",
    "pytz"
]

for lib in libs:
    print(f"   Instalando {lib}...")
    subprocess.run([python_exe, "-m", "pip", "install", lib], 
                   stdout=subprocess.DEVNULL, 
                   stderr=subprocess.DEVNULL)

print("   ✅ Librerías instaladas")
print()

print("3. Ejecutando el bot...")
print("-"*70)
print()

# Ejecutar el bot
subprocess.run([python_exe, "FINAL_BOT.py"])

print()
input("Presiona Enter para salir...")
