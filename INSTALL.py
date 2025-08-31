#!/usr/bin/env python
"""
INSTALADOR AUTOMÁTICO DE ALGO TRADER V3
========================================
Instala todas las dependencias y configura el entorno
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class AlgoTraderInstaller:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.os_type = platform.system()
        self.errors = []
        
    def check_python_version(self):
        """Verifica la versión de Python"""
        print(f"🐍 Python {self.python_version} detectado")
        
        if sys.version_info < (3, 10):
            print("❌ Se requiere Python 3.10 o superior")
            sys.exit(1)
        else:
            print("✅ Versión de Python correcta")
            
    def create_virtual_env(self):
        """Crea un entorno virtual"""
        print("\n📦 Creando entorno virtual...")
        
        venv_path = self.base_path / '.venv'
        
        if not venv_path.exists():
            try:
                subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
                print("✅ Entorno virtual creado")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"Error creando venv: {e}")
                return False
        else:
            print("✅ Entorno virtual ya existe")
            
        return True
        
    def install_requirements(self):
        """Instala los paquetes requeridos"""
        print("\n📚 Instalando dependencias...")
        
        # Actualizar pip primero
        print("Actualizando pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      capture_output=True)
        
        # Lista de paquetes esenciales
        essential_packages = [
            'MetaTrader5>=5.0.45',
            'pandas>=1.3.0',
            'numpy>=1.21.0',
            'requests>=2.26.0',
            'python-dotenv>=0.19.0',
            'streamlit>=1.10.0',
            'plotly>=5.3.0',
            'scikit-learn>=1.0.0',
            'ta>=0.10.0',
            'beautifulsoup4>=4.9.0',
            'aiohttp>=3.8.0',
            'psutil>=5.8.0',
            'colorlog>=6.6.0',
            'tqdm>=4.62.0',
            'schedule>=1.1.0'
        ]
        
        # Instalar paquetes esenciales
        for package in essential_packages:
            print(f"Instalando {package}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
                print(f"✅ {package.split('>=')[0]} instalado")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"Error instalando {package}: {e}")
                print(f"⚠️ Error con {package}, continuando...")
        
        # Paquetes opcionales
        optional_packages = [
            'xgboost>=1.5.0',
            'backtrader>=1.9.0',
            'yfinance>=0.1.70',
            'ccxt>=2.5.0'
        ]
        
        print("\nInstalando paquetes opcionales...")
        for package in optional_packages:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True, timeout=60)
                print(f"✅ {package.split('>=')[0]} instalado")
            except:
                print(f"⚠️ {package.split('>=')[0]} no se pudo instalar (opcional)")
                
    def install_talib(self):
        """Instala TA-Lib (requiere instalación especial en Windows)"""
        print("\n📊 Instalando TA-Lib...")
        
        if self.os_type == "Windows":
            print("""
⚠️ TA-Lib requiere instalación manual en Windows:

1. Descarga el archivo .whl desde:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
   
2. Selecciona la versión para tu Python ({self.python_version}) y arquitectura

3. Instala con: pip install TA_Lib-[version].whl

TA-Lib es opcional pero recomendado para análisis técnico avanzado.
""")
        else:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'TA-Lib'], 
                             check=True, capture_output=True)
                print("✅ TA-Lib instalado")
            except:
                print("⚠️ TA-Lib no se pudo instalar (opcional)")
                
    def check_mt5(self):
        """Verifica la instalación de MetaTrader 5"""
        print("\n🏦 Verificando MetaTrader 5...")
        
        try:
            import MetaTrader5 as mt5
            if mt5.initialize():
                info = mt5.terminal_info()
                if info:
                    print(f"✅ MT5 detectado: {info.name}")
                    mt5.shutdown()
                else:
                    print("⚠️ MT5 instalado pero no hay terminal activo")
            else:
                print("⚠️ MT5 no se pudo inicializar. Asegúrate de tener MT5 instalado")
        except ImportError:
            print("❌ Módulo MT5 no instalado")
            self.errors.append("MetaTrader5 no se pudo instalar")
            
    def setup_directories(self):
        """Crea las carpetas necesarias"""
        print("\n📁 Creando estructura de directorios...")
        
        directories = [
            'logs',
            'data/historical',
            'data/realtime',
            'models',
            'reports',
            'backups',
            'config'
        ]
        
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            
        print("✅ Directorios creados")
        
    def create_config_file(self):
        """Crea el archivo de configuración si no existe"""
        print("\n⚙️ Configurando archivo .env...")
        
        env_file = self.base_path / '.env'
        env_example = self.base_path / '.env.example'
        
        if not env_file.exists() and env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Archivo .env creado desde plantilla")
            print("⚠️ IMPORTANTE: Edita .env con tus credenciales")
        elif env_file.exists():
            print("✅ Archivo .env ya existe")
        else:
            print("⚠️ No se encontró .env.example")
            
    def test_installation(self):
        """Prueba que todo esté instalado correctamente"""
        print("\n🧪 Verificando instalación...")
        
        modules_to_test = [
            ('pandas', 'Pandas'),
            ('numpy', 'NumPy'),
            ('MetaTrader5', 'MetaTrader5'),
            ('streamlit', 'Streamlit'),
            ('plotly', 'Plotly'),
            ('sklearn', 'Scikit-learn'),
            ('requests', 'Requests'),
            ('dotenv', 'Python-dotenv')
        ]
        
        all_ok = True
        for module, name in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {name}")
            except ImportError:
                print(f"❌ {name}")
                all_ok = False
                
        return all_ok
        
    def print_summary(self):
        """Imprime un resumen de la instalación"""
        print("\n" + "="*60)
        print("RESUMEN DE INSTALACIÓN")
        print("="*60)
        
        if self.errors:
            print("\n⚠️ Se encontraron algunos errores:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ Instalación completada sin errores")
            
        print("""
📋 PRÓXIMOS PASOS:
1. Edita el archivo .env con tus credenciales de trading
2. Asegúrate de tener MetaTrader 5 instalado
3. Ejecuta: python launcher.py --mode demo

📚 DOCUMENTACIÓN:
- README.md: Guía general
- docs/: Documentación detallada

🚀 INICIO RÁPIDO:
- Windows: Ejecuta START_SYSTEM.bat
- Linux/Mac: python launcher.py

💡 TIPS:
- Empieza siempre en modo DEMO
- Revisa los logs en la carpeta logs/
- Los dashboards están en http://localhost:8512

¿Necesitas ayuda? Revisa la documentación o contacta soporte.
""")
        
    def run(self):
        """Ejecuta la instalación completa"""
        print("""
╔════════════════════════════════════════════════════════╗
║         INSTALADOR DE ALGO TRADER V3                  ║
║              Sistema Automático                        ║
╚════════════════════════════════════════════════════════╝
        """)
        
        # 1. Verificar Python
        self.check_python_version()
        
        # 2. Crear entorno virtual (opcional)
        # self.create_virtual_env()
        
        # 3. Instalar dependencias
        self.install_requirements()
        
        # 4. Intentar instalar TA-Lib
        self.install_talib()
        
        # 5. Verificar MT5
        self.check_mt5()
        
        # 6. Crear directorios
        self.setup_directories()
        
        # 7. Crear archivo de configuración
        self.create_config_file()
        
        # 8. Verificar instalación
        success = self.test_installation()
        
        # 9. Mostrar resumen
        self.print_summary()
        
        return success

if __name__ == "__main__":
    installer = AlgoTraderInstaller()
    
    print("\n🚀 Este instalador configurará Algo Trader V3")
    print("Instalará todas las dependencias necesarias")
    
    response = input("\n¿Desea continuar? (s/n): ")
    
    if response.lower() == 's':
        success = installer.run()
        if success:
            print("\n✅ ¡Instalación exitosa!")
        else:
            print("\n⚠️ Instalación completada con advertencias")
    else:
        print("Instalación cancelada.")
