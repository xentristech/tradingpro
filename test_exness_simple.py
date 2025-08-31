import MetaTrader5 as mt5
import time

print("="*50)
print("TEST RÁPIDO - CONEXIÓN EXNESS")
print("="*50)

# Datos de la cuenta Exness
login = 197678662
password = "Badboy930218*"
server = "Exness-MT5Trial11"
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"

print(f"\nConectando a:")
print(f"  Usuario: {login}")
print(f"  Server: {server}")
print(f"  Path: {path}")

# Intentar conectar
print("\nIniciando MT5...")
if not mt5.initialize():
    print("Error: No se pudo inicializar MT5 básico")
    print("Intentando con credenciales...")
    
    if not mt5.initialize(path=path, login=login, password=password, server=server):
        error = mt5.last_error()
        print(f"ERROR: {error}")
        print("\nVerifica:")
        print("1. Que MetaTrader 5 esté instalado")
        print("2. Las credenciales sean correctas")
        print("3. El servidor sea 'Exness-MT5Trial11'")
    else:
        print("✓ CONECTADO CON CREDENCIALES")
else:
    print("✓ MT5 INICIALIZADO")
    
    # Intentar login
    print("\nIntentando login...")
    authorized = mt5.login(login, password, server)
    if authorized:
        print("✓ LOGIN EXITOSO")
    else:
        print("✗ Error en login")

# Información de cuenta
account = mt5.account_info()
if account:
    print(f"\n✅ CUENTA CONECTADA:")
    print(f"  Número: {account.login}")
    print(f"  Balance: ${account.balance:.2f}")
    print(f"  Server: {account.server}")
    print(f"  Broker: {account.company}")
else:
    print("\n✗ No se pudo obtener info de cuenta")

# Cerrar
mt5.shutdown()
print("\nPrueba completada")
