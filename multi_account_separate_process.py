"""
Multi Account Manager Alternative - Procesos Separados
Evita duplicación ejecutando cada cuenta independientemente
"""
import subprocess
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('configs/.env')

def create_account_monitor_script(account_name, login, password, server, mt5_path):
    """Crea un script Python para monitorear una cuenta específica"""
    
    script_content = f'''"""
Monitor para cuenta {account_name}
Generado automáticamente
"""
import MetaTrader5 as mt5
import time
from datetime import datetime

def monitor_account():
    # Configuración
    LOGIN = {login}
    PASSWORD = "{password}"
    SERVER = "{server}"
    MT5_PATH = r"{mt5_path}"
    
    print(f"Monitoreando {account_name} - Login: {{LOGIN}}")
    
    # Inicializar MT5
    if not mt5.initialize(path=MT5_PATH if MT5_PATH else None):
        print("Error inicializando MT5")
        return
    
    # Login
    if not mt5.login(LOGIN, password=PASSWORD, server=SERVER):
        print(f"Error en login: {{mt5.last_error()}}")
        mt5.shutdown()
        return
    
    # Obtener información
    account = mt5.account_info()
    positions = mt5.positions_get()
    
    if account:
        print(f"\\n📊 {account_name.upper()}")
        print(f"   Login: {{account.login}}")
        print(f"   Balance: ${{account.balance:.2f}}")
        print(f"   Equity: ${{account.equity:.2f}}")
        print(f"   Posiciones: {{len(positions) if positions else 0}}")
        
        if positions:
            for pos in positions:
                sl_status = "✅" if pos.sl != 0 else "❌"
                tp_status = "✅" if pos.tp != 0 else "❌"
                print(f"   #{{pos.ticket}} {{pos.symbol}}: SL{{sl_status}} TP{{tp_status}}")
    
    mt5.shutdown()

if __name__ == "__main__":
    monitor_account()
'''
    
    # Guardar script
    script_path = f"monitor_{account_name.lower()}.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return script_path

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     EXNESS ACCOUNT MANAGER - PROCESOS SEPARADOS           ║
    ║         Configurado para cuenta EXNESS únicamente         ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Configuración de cuentas - Solo EXNESS
    accounts = [
        {
            'name': 'EXNESS_TRIAL',
            'login': 197678662,
            'password': 'Badboy930218*',
            'server': 'Exness-MT5Trial11',
            'mt5_path': os.getenv('MT5_PATH', r'C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe')
        }
    ]
    
    print("Creando scripts de monitoreo individuales...")
    scripts = []
    
    for account in accounts:
        # Verificar path
        if not os.path.exists(account['mt5_path']):
            print(f"⚠️ {account['name']}: MT5 no encontrado en {account['mt5_path']}")
            continue
            
        # Crear script
        script_path = create_account_monitor_script(
            account['name'],
            account['login'],
            account['password'],
            account['server'],
            account['mt5_path']
        )
        scripts.append(script_path)
        print(f"✅ Script creado: {script_path}")
    
    print("\n" + "="*60)
    print("EJECUTANDO MONITOREO EN PROCESOS SEPARADOS")
    print("="*60)
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verificando cuentas...")
            
            # Ejecutar cada script en proceso separado
            for script in scripts:
                try:
                    # Ejecutar script y capturar salida
                    result = subprocess.run(
                        ['python', script],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    # Mostrar resultado
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(f"Error: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Timeout ejecutando {script}")
                except Exception as e:
                    print(f"❌ Error ejecutando {script}: {e}")
            
            print("\n" + "-"*60)
            print("Esperando 120 segundos para siguiente verificación...")
            print("Presiona Ctrl+C para detener")
            time.sleep(120)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoreo detenido por el usuario")
        
        # Limpiar scripts temporales
        print("\nLimpiando scripts temporales...")
        for script in scripts:
            try:
                os.remove(script)
                print(f"✅ Eliminado: {script}")
            except:
                pass

if __name__ == "__main__":
    main()
