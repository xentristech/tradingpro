#!/usr/bin/env python
"""
System Health Check - Verificación completa del sistema
Verifica todos los componentes críticos del sistema de trading
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import json

# Configurar encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Imprime el header del verificador"""
    print("\n" + "="*70)
    print(" "*20 + "🔍 SYSTEM HEALTH CHECK v3.0")
    print("="*70)
    print()

def check_mark(status):
    """Retorna marca de verificación según estado"""
    if status == "OK":
        return f"{Colors.GREEN}✅{Colors.RESET}"
    elif status == "WARNING":
        return f"{Colors.YELLOW}⚠️{Colors.RESET}"
    else:
        return f"{Colors.RED}❌{Colors.RESET}"

def check_python():
    """Verifica versión de Python"""
    print(f"{Colors.BOLD}1. Python Environment:{Colors.RESET}")
    
    version = sys.version_info
    status = "OK" if version >= (3, 10) else "ERROR"
    
    print(f"   {check_mark(status)} Python {version.major}.{version.minor}.{version.micro}")
    
    if status == "ERROR":
        print(f"      {Colors.RED}Requiere Python 3.10 o superior{Colors.RESET}")
    
    # Verificar arquitectura
    import platform
    arch = platform.machine()
    is_64 = sys.maxsize > 2**32
    
    print(f"   {check_mark('OK' if is_64 else 'ERROR')} Arquitectura: {arch} ({'64-bit' if is_64 else '32-bit'})")
    
    return status == "OK"

def check_dependencies():
    """Verifica dependencias instaladas"""
    print(f"\n{Colors.BOLD}2. Dependencias Core:{Colors.RESET}")
    
    dependencies = {
        'MetaTrader5': 'MetaTrader5',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'requests': 'requests',
        'dotenv': 'dotenv',
        'yaml': 'yaml',
        'openai': 'openai',
        'streamlit': 'streamlit'
    }
    
    all_ok = True
    
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"   {check_mark('OK')} {name}")
        except ImportError:
            print(f"   {check_mark('ERROR')} {name} - NO INSTALADO")
            all_ok = False
    
    return all_ok

def check_configuration():
    """Verifica archivos de configuración"""
    print(f"\n{Colors.BOLD}3. Configuración:{Colors.RESET}")
    
    config_files = {
        'configs/.env': 'Variables de entorno',
        'configs/settings.yaml': 'Configuración de trading',
        'requirements.txt': 'Lista de dependencias'
    }
    
    all_ok = True
    
    for file_path, description in config_files.items():
        if os.path.exists(file_path):
            print(f"   {check_mark('OK')} {description}")
            
            # Verificar contenido básico de .env
            if file_path == 'configs/.env':
                from dotenv import load_dotenv
                load_dotenv(file_path)
                
                critical_vars = [
                    'MT5_LOGIN',
                    'MT5_PASSWORD',
                    'MT5_SERVER',
                    'SYMBOL'
                ]
                
                for var in critical_vars:
                    value = os.getenv(var)
                    if value:
                        # Ocultar valores sensibles
                        if 'PASSWORD' in var:
                            display_value = '*' * len(value)
                        else:
                            display_value = value[:3] + '***' if len(value) > 3 else value
                        print(f"      • {var}: {display_value}")
                    else:
                        print(f"      {check_mark('WARNING')} {var}: NO CONFIGURADO")
        else:
            print(f"   {check_mark('ERROR')} {description} - NO ENCONTRADO")
            all_ok = False
    
    return all_ok

def check_mt5_connection():
    """Verifica conexión con MetaTrader 5"""
    print(f"\n{Colors.BOLD}4. MetaTrader 5:{Colors.RESET}")
    
    try:
        from utils.mt5_connection import MT5ConnectionManager
        
        print(f"   {check_mark('OK')} Módulo MT5 importado")
        
        # Intentar conectar
        print("   🔄 Intentando conectar...")
        mt5_manager = MT5ConnectionManager(max_retries=2, retry_delay=2)
        
        if mt5_manager.connect():
            print(f"   {check_mark('OK')} Conectado a MT5")
            
            # Obtener info de cuenta
            account = mt5_manager.get_account_info()
            if account:
                print(f"      • Cuenta: {account.login}")
                print(f"      • Balance: ${account.balance:.2f}")
                print(f"      • Servidor: {account.server}")
                
                # Verificar símbolo
                symbol = os.getenv('SYMBOL', 'BTCUSDm')
                symbol_info = mt5_manager.get_symbol_info(symbol)
                
                if symbol_info:
                    print(f"   {check_mark('OK')} Símbolo {symbol} disponible")
                else:
                    print(f"   {check_mark('ERROR')} Símbolo {symbol} no disponible")
            
            mt5_manager.disconnect()
            return True
        else:
            print(f"   {check_mark('ERROR')} No se pudo conectar a MT5")
            print(f"      • Verifica que MT5 esté abierto")
            print(f"      • Verifica credenciales en .env")
            return False
            
    except Exception as e:
        print(f"   {check_mark('ERROR')} Error: {str(e)}")
        return False

def check_telegram():
    """Verifica configuración de Telegram"""
    print(f"\n{Colors.BOLD}5. Telegram:{Colors.RESET}")
    
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print(f"   {check_mark('WARNING')} Telegram no configurado (opcional)")
        return True
    
    try:
        from notifiers.telegram import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        if notifier.enabled:
            print(f"   {check_mark('OK')} Telegram configurado")
            print(f"      • Chat ID: {chat_id[:5]}***")
            
            # Enviar mensaje de prueba
            test_message = f"🔍 Test de conexión - {datetime.now().strftime('%H:%M:%S')}"
            
            if notifier.send_message(test_message):
                print(f"   {check_mark('OK')} Mensaje de prueba enviado")
            else:
                print(f"   {check_mark('WARNING')} No se pudo enviar mensaje")
        else:
            print(f"   {check_mark('WARNING')} Telegram deshabilitado")
            
        return True
        
    except Exception as e:
        print(f"   {check_mark('ERROR')} Error: {str(e)}")
        return False

def check_ollama():
    """Verifica conexión con Ollama"""
    print(f"\n{Colors.BOLD}6. IA (Ollama/OpenAI):{Colors.RESET}")
    
    api_base = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/v1')
    model = os.getenv('OLLAMA_MODEL', 'deepseek-r1:14b')
    
    print(f"   • API Base: {api_base}")
    print(f"   • Modelo: {model}")
    
    try:
        import requests
        
        # Verificar si Ollama está corriendo
        if 'localhost' in api_base or '127.0.0.1' in api_base:
            # Es Ollama local
            try:
                # Verificar endpoint de Ollama
                ollama_url = api_base.replace('/v1', '')
                response = requests.get(f"{ollama_url}/api/tags", timeout=2)
                
                if response.status_code == 200:
                    print(f"   {check_mark('OK')} Ollama está ejecutándose")
                    
                    # Verificar modelo
                    models = response.json().get('models', [])
                    model_names = [m.get('name', '') for m in models]
                    
                    if any(model in name for name in model_names):
                        print(f"   {check_mark('OK')} Modelo {model} disponible")
                    else:
                        print(f"   {check_mark('WARNING')} Modelo {model} no encontrado")
                        print(f"      Modelos disponibles: {', '.join(model_names)}")
                else:
                    print(f"   {check_mark('ERROR')} Ollama no responde")
                    
            except Exception:
                print(f"   {check_mark('WARNING')} Ollama no está ejecutándose")
                print(f"      • Instala Ollama desde https://ollama.ai")
                print(f"      • Ejecuta: ollama pull {model}")
        else:
            # Es OpenAI o compatible
            print(f"   {check_mark('OK')} Usando endpoint externo")
            
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                print(f"   {check_mark('OK')} API Key configurada")
            else:
                print(f"   {check_mark('WARNING')} API Key no configurada")
        
        return True
        
    except Exception as e:
        print(f"   {check_mark('ERROR')} Error: {str(e)}")
        return False

def check_data_sources():
    """Verifica fuentes de datos"""
    print(f"\n{Colors.BOLD}7. Fuentes de Datos:{Colors.RESET}")
    
    # TwelveData
    api_key = os.getenv('TWELVEDATA_API_KEY')
    
    if api_key:
        print(f"   {check_mark('OK')} TwelveData API Key configurada")
        
        # Test de conexión
        try:
            import requests
            response = requests.get(
                'https://api.twelvedata.com/price',
                params={'symbol': 'EUR/USD', 'apikey': api_key},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"   {check_mark('OK')} TwelveData respondiendo")
            else:
                print(f"   {check_mark('WARNING')} TwelveData error: {response.status_code}")
                
        except Exception as e:
            print(f"   {check_mark('WARNING')} No se pudo verificar TwelveData")
    else:
        print(f"   {check_mark('WARNING')} TwelveData no configurado")
        print(f"      • Obtén API key en https://twelvedata.com")
    
    return True

def check_directories():
    """Verifica estructura de directorios"""
    print(f"\n{Colors.BOLD}8. Estructura de Directorios:{Colors.RESET}")
    
    directories = [
        'configs',
        'data',
        'logs',
        'utils',
        'orchestrator',
        'signals',
        'risk',
        'broker',
        'notifiers',
        'ml',
        'backtesting'
    ]
    
    all_ok = True
    
    for directory in directories:
        if os.path.isdir(directory):
            print(f"   {check_mark('OK')} {directory}/")
        else:
            print(f"   {check_mark('ERROR')} {directory}/ - NO ENCONTRADO")
            all_ok = False
    
    return all_ok

def check_state_manager():
    """Verifica State Manager"""
    print(f"\n{Colors.BOLD}9. State Manager:{Colors.RESET}")
    
    try:
        from utils.state_manager import StateManager
        
        sm = StateManager()
        health = sm.get_health_status()
        
        print(f"   {check_mark('OK')} State Manager operativo")
        print(f"      • Estado: {health['trading_state']}")
        print(f"      • Ciclos: {health['cycles']}")
        print(f"      • Errores: {health['errors']}")
        
        sm.shutdown()
        return True
        
    except Exception as e:
        print(f"   {check_mark('ERROR')} Error: {str(e)}")
        return False

def check_rate_limiter():
    """Verifica Rate Limiter"""
    print(f"\n{Colors.BOLD}10. Rate Limiter:{Colors.RESET}")
    
    try:
        from utils.rate_limiter import RateLimiter
        
        rl = RateLimiter()
        
        print(f"   {check_mark('OK')} Rate Limiter operativo")
        
        # Mostrar límites configurados
        for api_name in ['twelvedata', 'ollama', 'telegram']:
            remaining = rl.get_remaining_calls(api_name)
            print(f"      • {api_name}: {remaining['per_minute']}/min, {remaining['per_hour']}/hr")
        
        return True
        
    except Exception as e:
        print(f"   {check_mark('ERROR')} Error: {str(e)}")
        return False

def generate_report(results):
    """Genera reporte final"""
    print("\n" + "="*70)
    print(" "*25 + f"{Colors.BOLD}REPORTE FINAL{Colors.RESET}")
    print("="*70)
    
    total_checks = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total_checks - passed
    
    percentage = (passed / total_checks) * 100 if total_checks > 0 else 0
    
    # Determinar estado general
    if percentage >= 90:
        status = "EXCELENTE"
        color = Colors.GREEN
    elif percentage >= 70:
        status = "BUENO"
        color = Colors.GREEN
    elif percentage >= 50:
        status = "ACEPTABLE"
        color = Colors.YELLOW
    else:
        status = "CRÍTICO"
        color = Colors.RED
    
    print(f"\n   {color}{Colors.BOLD}Estado General: {status}{Colors.RESET}")
    print(f"   Verificaciones exitosas: {passed}/{total_checks} ({percentage:.1f}%)")
    
    # Componentes críticos
    critical_components = ['python', 'dependencies', 'configuration', 'mt5']
    critical_ok = all(results.get(comp, False) for comp in critical_components)
    
    if critical_ok:
        print(f"\n   {check_mark('OK')} Todos los componentes críticos funcionando")
        print(f"   {Colors.GREEN}✅ SISTEMA LISTO PARA OPERAR{Colors.RESET}")
    else:
        print(f"\n   {check_mark('ERROR')} Hay componentes críticos con problemas")
        print(f"   {Colors.RED}❌ SISTEMA NO ESTÁ LISTO{Colors.RESET}")
        
        print("\n   Componentes que requieren atención:")
        for comp, status in results.items():
            if not status and comp in critical_components:
                print(f"      • {comp.upper()}")
    
    # Guardar reporte
    report_file = f"logs/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('logs', exist_ok=True)
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'status': status,
        'percentage': percentage,
        'results': results,
        'critical_ok': critical_ok
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n   📄 Reporte guardado en: {report_file}")

def main():
    """Función principal"""
    print_header()
    
    results = {}
    
    # Ejecutar todas las verificaciones
    checks = [
        ('python', check_python),
        ('dependencies', check_dependencies),
        ('configuration', check_configuration),
        ('directories', check_directories),
        ('state_manager', check_state_manager),
        ('rate_limiter', check_rate_limiter),
        ('mt5', check_mt5_connection),
        ('telegram', check_telegram),
        ('ollama', check_ollama),
        ('data_sources', check_data_sources),
    ]
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n{Colors.RED}Error ejecutando {name}: {e}{Colors.RESET}")
            results[name] = False
        
        time.sleep(0.5)  # Pausa entre checks
    
    # Generar reporte
    generate_report(results)
    
    print("\n" + "="*70)
    print(f"{Colors.BOLD}Verificación completada{Colors.RESET}")
    print("="*70)
    
    # Retornar código de salida
    critical_components = ['python', 'dependencies', 'configuration']
    critical_ok = all(results.get(comp, False) for comp in critical_components)
    
    return 0 if critical_ok else 1

if __name__ == "__main__":
    sys.exit(main())
