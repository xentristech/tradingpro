import sys
import os

print("Python Version:", sys.version)
print("Current Directory:", os.getcwd())
print("\nIntentando importar módulos...")

try:
    import MetaTrader5 as mt5
    print("✓ MetaTrader5 importado")
except ImportError as e:
    print("✗ Error importando MetaTrader5:", e)

try:
    import pandas
    print("✓ pandas importado")
except ImportError as e:
    print("✗ Error importando pandas:", e)

try:
    import requests
    print("✓ requests importado")
except ImportError as e:
    print("✗ Error importando requests:", e)

try:
    from dotenv import load_dotenv
    print("✓ python-dotenv importado")
    
    # Cargar configuración
    env_path = os.path.join(os.getcwd(), "configs", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Archivo .env cargado desde: {env_path}")
        
        # Verificar configuraciones básicas
        mt5_login = os.getenv("MT5_LOGIN", "NO_CONFIGURADO")
        print(f"\nConfiguración MT5:")
        print(f"  Login: {mt5_login}")
        print(f"  Server: {os.getenv('MT5_SERVER', 'NO_CONFIGURADO')}")
    else:
        print(f"✗ No se encontró archivo .env en: {env_path}")
        
except ImportError as e:
    print("✗ Error importando python-dotenv:", e)

print("\n¡Test completado!")
