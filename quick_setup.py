#!/usr/bin/env python
"""
Quick Setup - Configuración rápida para nuevos usuarios
Guía interactiva para configurar el sistema desde cero
"""
import os
import sys
import subprocess
from pathlib import Path
import shutil
import time
from datetime import datetime

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Imprime el header del instalador"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{'':>20}🚀 ALGO TRADER v3.0 - QUICK SETUP{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_step(step_num, total, description):
    """Imprime el paso actual"""
    print(f"\n{Colors.YELLOW}[Paso {step_num}/{total}]{Colors.RESET} {Colors.BOLD}{description}{Colors.RESET}")
    print("-" * 50)

def check_python():
    """Verifica versión de Python"""
    version = sys.version_info
    if version >= (3, 10):
        print(f"{Colors.GREEN}✅ Python {version.major}.{version.minor}.{version.micro} detectado{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}❌ Python {version.major}.{version.minor} detectado. Se requiere 3.10+{Colors.RESET}")
        return False

def create_venv():
    """Crea entorno virtual"""
    print("Creando entorno virtual...")
    
    venv_path = Path('.venv')
    
    if venv_path.exists():
        response = input(f"{Colors.YELLOW}Ya existe un entorno virtual. ¿Recrear? (s/n): {Colors.RESET}")
        if response.lower() != 's':
            return True
        shutil.rmtree(venv_path)
    
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', '.venv'])
        print(f"{Colors.GREEN}✅ Entorno virtual creado{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Error creando entorno virtual: {e}{Colors.RESET}")
        return False

def install_dependencies():
    """Instala dependencias"""
    print("Instalando dependencias...")
    
    # Determinar el comando pip según el OS
    if sys.platform == 'win32':
        pip_cmd = ['.venv\\Scripts\\python.exe', '-m', 'pip']
    else:
        pip_cmd = ['.venv/bin/python', '-m', 'pip']
    
    try:
        # Actualizar pip
        print("  Actualizando pip...")
        subprocess.check_call(pip_cmd + ['install', '--upgrade', 'pip'], 
                            stdout=subprocess.DEVNULL)
        
        # Instalar requirements
        print("  Instalando paquetes (esto puede tomar varios minutos)...")
        subprocess.check_call(pip_cmd + ['install', '-r', 'requirements.txt'])
        
        print(f"{Colors.GREEN}✅ Dependencias instaladas{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Error instalando dependencias: {e}{Colors.RESET}")
        return False

def setup_configuration():
    """Configura archivos .env y settings.yaml"""
    print("Configurando sistema...")
    
    # Crear directorio configs si no existe
    configs_dir = Path('configs')
    configs_dir.mkdir(exist_ok=True)
    
    # Configurar .env
    env_file = configs_dir / '.env'
    
    if env_file.exists():
        response = input(f"{Colors.YELLOW}.env ya existe. ¿Sobrescribir? (s/n): {Colors.RESET}")
        if response.lower() != 's':
            return True
    
    print("\n📝 Configuración básica:")
    print("(Presiona Enter para usar valores por defecto)")
    
    config = {}
    
    # MT5 Configuration
    print(f"\n{Colors.BOLD}MetaTrader 5:{Colors.RESET}")
    config['MT5_PATH'] = input("  Ruta a MT5 (ej: C:\\Program Files\\MetaTrader 5\\terminal64.exe): ").strip()
    config['MT5_LOGIN'] = input("  Número de cuenta MT5: ").strip()
    config['MT5_PASSWORD'] = input("  Contraseña MT5: ").strip()
    config['MT5_SERVER'] = input("  Servidor MT5 (ej: Exness-MT5Trial11): ").strip()
    
    # Trading Configuration
    print(f"\n{Colors.BOLD}Trading:{Colors.RESET}")
    config['SYMBOL'] = input("  Símbolo a operar (default: BTCUSDm): ").strip() or "BTCUSDm"
    config['LIVE_TRADING'] = 'false'  # Siempre empezar en demo
    
    # APIs (opcional)
    print(f"\n{Colors.BOLD}APIs (opcional, presiona Enter para omitir):{Colors.RESET}")
    config['TWELVEDATA_API_KEY'] = input("  TwelveData API Key: ").strip() or ""
    config['TELEGRAM_TOKEN'] = input("  Telegram Bot Token: ").strip() or ""
    config['TELEGRAM_CHAT_ID'] = input("  Telegram Chat ID: ").strip() or ""
    
    # IA Configuration
    print(f"\n{Colors.BOLD}IA:{Colors.RESET}")
    use_ollama = input("  ¿Usar Ollama local? (s/n, default: s): ").strip().lower()
    
    if use_ollama != 'n':
        config['OLLAMA_API_BASE'] = 'http://localhost:11434/v1'
        config['OLLAMA_MODEL'] = input("  Modelo Ollama (default: deepseek-r1:14b): ").strip() or "deepseek-r1:14b"
    else:
        config['OLLAMA_API_BASE'] = input("  OpenAI API Base: ").strip()
        config['OLLAMA_MODEL'] = input("  Modelo (default: gpt-4o-mini): ").strip() or "gpt-4o-mini"
        config['OPENAI_API_KEY'] = input("  OpenAI API Key: ").strip()
    
    # Valores por defecto
    defaults = {
        'MT5_TIMEOUT': '60000',
        'MT5_DEVIATION': '20',
        'MT5_MAGIC': '20250817',
        'DEF_SL_USD': '50.0',
        'DEF_TP_USD': '100.0',
        'PIP_VALUE': '1.0',
        'TZ': 'America/New_York',
        'LOG_LEVEL': 'INFO',
        'POLL_SECONDS': '20',
        'MIN_CONFIDENCE': '0.75',
        'MAX_POSITIONS': '3',
        'MAX_DAILY_LOSS': '200.0',
        'INITIAL_CAPITAL': '10000',
        'MAX_RISK_PER_TRADE': '0.02',
        'MAX_PORTFOLIO_RISK': '0.06',
        'USE_BREAKEVEN': 'true',
        'USE_TRAILING': 'true'
    }
    
    # Combinar configuración
    final_config = {**defaults, **{k: v for k, v in config.items() if v}}
    
    # Escribir .env
    with open(env_file, 'w') as f:
        f.write("# ========================================\n")
        f.write("# ALGO TRADER v3.0 - CONFIGURACIÓN\n")
        f.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# ========================================\n\n")
        
        categories = {
            'MT5': ['MT5_PATH', 'MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER', 
                   'MT5_TIMEOUT', 'MT5_DEVIATION', 'MT5_MAGIC'],
            'TRADING': ['SYMBOL', 'LIVE_TRADING', 'DEF_SL_USD', 'DEF_TP_USD', 
                       'PIP_VALUE', 'MIN_CONFIDENCE', 'MAX_POSITIONS', 
                       'MAX_DAILY_LOSS'],
            'RISK': ['INITIAL_CAPITAL', 'MAX_RISK_PER_TRADE', 'MAX_PORTFOLIO_RISK',
                    'USE_BREAKEVEN', 'USE_TRAILING'],
            'APIs': ['TWELVEDATA_API_KEY', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'],
            'IA': ['OLLAMA_API_BASE', 'OLLAMA_MODEL', 'OPENAI_API_KEY'],
            'SYSTEM': ['TZ', 'LOG_LEVEL', 'POLL_SECONDS']
        }
        
        for category, keys in categories.items():
            f.write(f"# === {category} ===\n")
            for key in keys:
                if key in final_config and final_config[key]:
                    # Ocultar passwords parcialmente
                    if 'PASSWORD' in key or 'KEY' in key or 'TOKEN' in key:
                        value = final_config[key]
                        if len(value) > 8:
                            display_value = value[:3] + '*' * (len(value)-6) + value[-3:]
                            f.write(f"# {key}={display_value} (oculto)\n")
                            f.write(f"{key}={value}\n")
                        else:
                            f.write(f"{key}={value}\n")
                    else:
                        f.write(f"{key}={final_config[key]}\n")
            f.write("\n")
    
    # Crear settings.yaml
    settings_file = configs_dir / 'settings.yaml'
    
    if not settings_file.exists():
        with open(settings_file, 'w') as f:
            f.write(f"""symbols:
  - {final_config.get('SYMBOL', 'BTCUSDm')}

telegram:
  enabled: {'true' if final_config.get('TELEGRAM_TOKEN') else 'false'}
  parse_mode: HTML

trade_enabled: true
min_confidence: {final_config.get('MIN_CONFIDENCE', '0.75')}

risk_management:
  use_breakeven: true
  use_trailing: true
  trailing_distance: 30
  breakeven_trigger: 20
""")
    
    print(f"{Colors.GREEN}✅ Configuración creada{Colors.RESET}")
    return True

def setup_ollama():
    """Configura Ollama si es necesario"""
    print("Verificando Ollama...")
    
    # Verificar si Ollama está instalado
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Ollama detectado{Colors.RESET}")
            
            # Verificar modelo
            model = os.getenv('OLLAMA_MODEL', 'deepseek-r1:14b')
            print(f"  Verificando modelo {model}...")
            
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True)
            
            if model.split(':')[0] in result.stdout:
                print(f"{Colors.GREEN}  ✅ Modelo {model} disponible{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}  ⚠️ Modelo {model} no encontrado{Colors.RESET}")
                response = input("  ¿Descargar ahora? (s/n): ")
                
                if response.lower() == 's':
                    print(f"  Descargando {model} (esto puede tomar tiempo)...")
                    subprocess.run(['ollama', 'pull', model])
            
            return True
    except FileNotFoundError:
        print(f"{Colors.YELLOW}⚠️ Ollama no está instalado{Colors.RESET}")
        print("  Descarga desde: https://ollama.ai/download")
        print("  O usa OpenAI configurando OLLAMA_API_BASE en .env")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Error verificando Ollama: {e}{Colors.RESET}")
        return False

def test_mt5_connection():
    """Prueba conexión con MT5"""
    print("Probando conexión con MT5...")
    
    try:
        # Usar el entorno virtual
        if sys.platform == 'win32':
            python_cmd = '.venv\\Scripts\\python.exe'
        else:
            python_cmd = '.venv/bin/python'
        
        # Crear script de prueba temporal
        test_script = """
import os
from dotenv import load_dotenv
load_dotenv('configs/.env')

try:
    from utils.mt5_connection import MT5ConnectionManager
    mt5 = MT5ConnectionManager(max_retries=2)
    
    if mt5.connect():
        account = mt5.get_account_info()
        if account:
            print(f"OK|{account.login}|{account.balance}")
        else:
            print("ERROR|No account info")
        mt5.disconnect()
    else:
        print("ERROR|Connection failed")
except Exception as e:
    print(f"ERROR|{e}")
"""
        
        with open('_test_mt5.py', 'w') as f:
            f.write(test_script)
        
        # Ejecutar prueba
        result = subprocess.run([python_cmd, '_test_mt5.py'], 
                              capture_output=True, text=True, timeout=30)
        
        # Limpiar
        os.unlink('_test_mt5.py')
        
        if result.stdout.startswith('OK'):
            parts = result.stdout.strip().split('|')
            print(f"{Colors.GREEN}✅ Conectado a MT5{Colors.RESET}")
            print(f"  Cuenta: {parts[1]}")
            print(f"  Balance: ${parts[2]}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️ No se pudo conectar a MT5{Colors.RESET}")
            if 'ERROR' in result.stdout:
                error = result.stdout.split('|')[1] if '|' in result.stdout else result.stdout
                print(f"  Error: {error}")
            print("  Verifica que MT5 esté abierto y las credenciales sean correctas")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{Colors.YELLOW}⚠️ Timeout conectando a MT5{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ Error probando MT5: {e}{Colors.RESET}")
        return False

def create_directories():
    """Crea estructura de directorios"""
    print("Creando estructura de directorios...")
    
    directories = [
        'logs',
        'data',
        'backups',
        'exports'
    ]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    
    print(f"{Colors.GREEN}✅ Directorios creados{Colors.RESET}")
    return True

def final_instructions():
    """Muestra instrucciones finales"""
    print(f"\n{Colors.GREEN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{'':>20}✅ INSTALACIÓN COMPLETADA{Colors.RESET}")
    print(f"{Colors.GREEN}{'='*70}{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Próximos pasos:{Colors.RESET}")
    print(f"1. {Colors.BLUE}Verificar el sistema:{Colors.RESET}")
    print(f"   python health_check.py\n")
    
    print(f"2. {Colors.BLUE}Iniciar en modo DEMO:{Colors.RESET}")
    print(f"   python main_trader.py --mode demo\n")
    
    print(f"3. {Colors.BLUE}O usar el launcher de Windows:{Colors.RESET}")
    print(f"   TRADER.bat\n")
    
    print(f"4. {Colors.BLUE}Abrir el dashboard:{Colors.RESET}")
    print(f"   streamlit run streamlit_app.py\n")
    
    print(f"{Colors.YELLOW}⚠️ IMPORTANTE:{Colors.RESET}")
    print("• Siempre prueba en DEMO antes de usar dinero real")
    print("• Revisa y ajusta la configuración en configs/.env")
    print("• Lee la documentación en README_V3.md")
    print("• Únete al canal de Telegram para soporte\n")
    
    print(f"{Colors.BOLD}Archivos importantes:{Colors.RESET}")
    print("• configs/.env        - Configuración principal")
    print("• configs/settings.yaml - Parámetros de trading")
    print("• main_trader.py      - Punto de entrada principal")
    print("• health_check.py     - Verificador del sistema")
    print("• streamlit_app.py    - Dashboard web\n")
    
    print(f"{Colors.GREEN}¡Buena suerte con tu trading!{Colors.RESET} 🚀")

def main():
    """Función principal del setup"""
    print_header()
    
    # Verificar que estamos en el directorio correcto
    if not Path('main_trader.py').exists():
        print(f"{Colors.RED}❌ Error: No se encontró main_trader.py{Colors.RESET}")
        print("Asegúrate de ejecutar este script desde el directorio del proyecto")
        return 1
    
    total_steps = 8
    current_step = 0
    
    # Paso 1: Verificar Python
    current_step += 1
    print_step(current_step, total_steps, "Verificar Python")
    if not check_python():
        print(f"\n{Colors.RED}Setup abortado. Instala Python 3.10+{Colors.RESET}")
        return 1
    
    # Paso 2: Crear entorno virtual
    current_step += 1
    print_step(current_step, total_steps, "Crear entorno virtual")
    if not create_venv():
        return 1
    
    # Paso 3: Instalar dependencias
    current_step += 1
    print_step(current_step, total_steps, "Instalar dependencias")
    if not install_dependencies():
        print(f"\n{Colors.YELLOW}Continuando con errores en dependencias...{Colors.RESET}")
    
    # Paso 4: Configurar sistema
    current_step += 1
    print_step(current_step, total_steps, "Configurar sistema")
    if not setup_configuration():
        return 1
    
    # Paso 5: Crear directorios
    current_step += 1
    print_step(current_step, total_steps, "Crear estructura de directorios")
    create_directories()
    
    # Paso 6: Configurar Ollama
    current_step += 1
    print_step(current_step, total_steps, "Configurar IA (Ollama)")
    setup_ollama()
    
    # Paso 7: Probar MT5
    current_step += 1
    print_step(current_step, total_steps, "Probar conexión MT5")
    test_mt5_connection()
    
    # Paso 8: Instrucciones finales
    current_step += 1
    print_step(current_step, total_steps, "Finalizar setup")
    final_instructions()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelado por el usuario{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error inesperado: {e}{Colors.RESET}")
        sys.exit(1)
