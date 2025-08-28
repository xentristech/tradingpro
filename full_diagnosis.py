#!/usr/bin/env python
"""
Sistema de Diagnóstico Completo para Algo Trader v3
Detecta problemas y genera recomendaciones
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

def print_section(title):
    """Imprime sección formateada"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_python():
    """Verifica instalación de Python"""
    print_section("PYTHON CHECK")
    print(f"Version: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Path: {sys.path[:3]}")
    return sys.version_info >= (3, 10)

def check_dependencies():
    """Verifica dependencias críticas"""
    print_section("DEPENDENCIES CHECK")
    
    required_modules = {
        # Core
        'MetaTrader5': {'required': True, 'install': 'MetaTrader5'},
        'pandas': {'required': True, 'install': 'pandas'},
        'numpy': {'required': True, 'install': 'numpy'},
        'requests': {'required': True, 'install': 'requests'},
        'dotenv': {'required': True, 'install': 'python-dotenv'},
        
        # Trading
        'ta': {'required': False, 'install': 'ta'},
        'twelvedata': {'required': False, 'install': 'twelvedata'},
        
        # ML
        'sklearn': {'required': False, 'install': 'scikit-learn'},
        'xgboost': {'required': False, 'install': 'xgboost'},
        
        # Web
        'streamlit': {'required': False, 'install': 'streamlit'},
        
        # Utils
        'yaml': {'required': True, 'install': 'PyYAML'},
        'pytz': {'required': True, 'install': 'pytz'},
    }
    
    missing_required = []
    missing_optional = []
    
    for module, info in required_modules.items():
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            if info['required']:
                missing_required.append(info['install'])
                print(f"  ❌ {module} (REQUIRED)")
            else:
                missing_optional.append(info['install'])
                print(f"  ⚠️  {module} (optional)")
    
    return missing_required, missing_optional

def check_project_structure():
    """Verifica estructura del proyecto"""
    print_section("PROJECT STRUCTURE CHECK")
    
    required_dirs = [
        'broker',
        'core', 
        'data',
        'configs',
        'logs',
        'ml',
        'risk',
        'storage',
        'utils'
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✅ {dir_name}/")
        else:
            missing_dirs.append(dir_name)
            print(f"  ❌ {dir_name}/ (MISSING)")
    
    return missing_dirs

def check_config_files():
    """Verifica archivos de configuración"""
    print_section("CONFIGURATION CHECK")
    
    config_dir = Path('configs')
    env_file = config_dir / '.env'
    
    if not env_file.exists():
        print("  ❌ .env file missing")
        return False
    
    print("  ✅ .env file exists")
    
    # Verificar variables críticas
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    critical_vars = [
        'TWELVEDATA_API_KEY',
        'MT5_LOGIN',
        'MT5_PASSWORD',
        'MT5_SERVER',
        'SYMBOL'
    ]
    
    missing_vars = []
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * 8}")
        else:
            missing_vars.append(var)
            print(f"  ❌ {var}: NOT SET")
    
    return len(missing_vars) == 0

def check_custom_modules():
    """Verifica módulos personalizados"""
    print_section("CUSTOM MODULES CHECK")
    
    modules_to_check = [
        ('broker.mt5_connection', 'MT5Connection'),
        ('core.system_manager', 'SystemManager'),
        ('data.twelvedata', 'TwelveDataAPI'),
        ('risk.advanced_risk', 'AdvancedRiskManager'),
        ('ml.trading_models', 'MLPipeline')
    ]
    
    working_modules = []
    broken_modules = []
    
    for module_path, class_name in modules_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"  ✅ {module_path}.{class_name}")
                working_modules.append(module_path)
            else:
                print(f"  ⚠️  {module_path} (missing {class_name})")
                broken_modules.append(module_path)
        except Exception as e:
            print(f"  ❌ {module_path}: {str(e)[:40]}")
            broken_modules.append(module_path)
    
    return working_modules, broken_modules

def test_mt5_connection():
    """Prueba conexión con MT5"""
    print_section("MT5 CONNECTION TEST")
    
    try:
        import MetaTrader5 as mt5
        
        # Inicializar MT5
        if not mt5.initialize():
            print(f"  ❌ Failed to initialize MT5: {mt5.last_error()}")
            return False
        
        print(f"  ✅ MT5 initialized")
        
        # Obtener info de cuenta
        account = mt5.account_info()
        if account:
            print(f"  ✅ Account: {account.login}")
            print(f"  ✅ Balance: ${account.balance:.2f}")
            print(f"  ✅ Server: {account.server}")
        else:
            print(f"  ❌ No account info")
            
        mt5.shutdown()
        return True
        
    except Exception as e:
        print(f"  ❌ MT5 Test failed: {e}")
        return False

def test_data_api():
    """Prueba API de datos"""
    print_section("DATA API TEST")
    
    api_key = os.getenv('TWELVEDATA_API_KEY')
    if not api_key:
        print("  ❌ No API key configured")
        return False
    
    try:
        import requests
        response = requests.get(
            f"https://api.twelvedata.com/price",
            params={'symbol': 'BTC/USD', 'apikey': api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                print(f"  ✅ API Working - BTC/USD: ${data['price']}")
                return True
            else:
                print(f"  ⚠️  API responded but no price data")
        else:
            print(f"  ❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ API Test failed: {e}")
    
    return False

def generate_fix_script(issues):
    """Genera script para corregir problemas"""
    print_section("GENERATING FIX SCRIPT")
    
    fix_commands = []
    
    # Instalar dependencias faltantes
    if issues.get('missing_required'):
        fix_commands.append("# Install required dependencies")
        fix_commands.append(f"pip install {' '.join(issues['missing_required'])}")
    
    if issues.get('missing_optional'):
        fix_commands.append("\n# Install optional dependencies")
        fix_commands.append(f"pip install {' '.join(issues['missing_optional'])}")
    
    # Crear directorios faltantes
    if issues.get('missing_dirs'):
        fix_commands.append("\n# Create missing directories")
        for dir_name in issues['missing_dirs']:
            fix_commands.append(f"mkdir -p {dir_name}")
    
    # Crear archivo de configuración
    if issues.get('missing_config'):
        fix_commands.append("\n# Copy config template")
        fix_commands.append("cp configs/.env.template configs/.env")
        fix_commands.append("# Edit configs/.env and add your API keys")
    
    # Guardar script
    fix_script = "\n".join(fix_commands)
    
    with open('fix_issues.sh', 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Auto-generated fix script\n\n")
        f.write(fix_script)
    
    with open('fix_issues.bat', 'w') as f:
        f.write("@echo off\n")
        f.write("REM Auto-generated fix script\n\n")
        f.write(fix_script.replace('mkdir -p', 'mkdir'))
    
    print("  ✅ Fix scripts generated: fix_issues.sh (Linux) / fix_issues.bat (Windows)")
    
    return fix_script

def main():
    """Función principal de diagnóstico"""
    print("\n" + "🔍" * 30)
    print(" ALGO TRADER V3 - FULL SYSTEM DIAGNOSIS")
    print("🔍" * 30)
    
    issues = {}
    all_ok = True
    
    # 1. Check Python
    if not check_python():
        print("\n⚠️  Python 3.10+ required")
        all_ok = False
    
    # 2. Check dependencies
    missing_req, missing_opt = check_dependencies()
    if missing_req:
        issues['missing_required'] = missing_req
        all_ok = False
    if missing_opt:
        issues['missing_optional'] = missing_opt
    
    # 3. Check structure
    missing_dirs = check_project_structure()
    if missing_dirs:
        issues['missing_dirs'] = missing_dirs
        all_ok = False
    
    # 4. Check config
    if not check_config_files():
        issues['missing_config'] = True
        all_ok = False
    
    # 5. Check custom modules  
    working, broken = check_custom_modules()
    if broken:
        issues['broken_modules'] = broken
        all_ok = False
    
    # 6. Test MT5
    mt5_ok = test_mt5_connection()
    if not mt5_ok:
        issues['mt5_connection'] = True
        all_ok = False
    
    # 7. Test Data API
    api_ok = test_data_api()
    if not api_ok:
        issues['api_connection'] = True
    
    # Generate report
    print_section("DIAGNOSIS REPORT")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_ready': all_ok,
        'issues': issues,
        'recommendations': []
    }
    
    if all_ok:
        print("  ✅ System is READY to trade!")
        report['recommendations'].append("System ready. Run 'python main.py start' to begin trading")
    else:
        print("  ⚠️  System needs attention")
        
        if issues.get('missing_required'):
            report['recommendations'].append(f"Install required packages: {', '.join(issues['missing_required'])}")
        
        if issues.get('mt5_connection'):
            report['recommendations'].append("Check MT5 credentials in configs/.env")
            report['recommendations'].append("Ensure MT5 terminal is installed")
        
        if issues.get('api_connection'):
            report['recommendations'].append("Verify TwelveData API key")
        
        if issues.get('broken_modules'):
            report['recommendations'].append("Fix broken modules or reinstall dependencies")
    
    # Save report
    with open('diagnosis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to diagnosis_report.json")
    
    # Generate fix script if needed
    if issues:
        generate_fix_script(issues)
        print("\n🔧 Run fix_issues.bat to resolve issues automatically")
    
    print("\n" + "="*60)
    print(f" Status: {'✅ READY' if all_ok else '⚠️  NEEDS FIXES'}")
    print("="*60)
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
