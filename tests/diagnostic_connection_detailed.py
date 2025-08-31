"""
Diagnóstico Detallado de Conexión Multi-Cuenta
Detecta problemas de conexión y duplicación
"""
import MetaTrader5 as mt5
import time
from datetime import datetime
import os

def test_connection_detailed(account_name, login, password, server, mt5_path):
    """Prueba de conexión detallada con diagnóstico"""
    print(f"\n{'='*60}")
    print(f"PROBANDO: {account_name}")
    print(f"{'='*60}")
    print(f"Login esperado: {login}")
    print(f"Servidor: {server}")
    print(f"Path MT5: {mt5_path}")
    
    # Verificar si el path existe
    if mt5_path and os.path.exists(mt5_path):
        print(f"✅ Path existe: {mt5_path}")
    else:
        print(f"❌ Path NO existe: {mt5_path}")
        print("   ESTE ES EL PROBLEMA - Verifica la ruta de instalación")
        return None
    
    try:
        # Paso 1: Cerrar cualquier conexión existente
        print("\n1. Cerrando conexiones previas...")
        mt5.shutdown()
        time.sleep(1)
        
        # Paso 2: Inicializar MT5
        print("2. Inicializando MT5...")
        if mt5_path and os.path.exists(mt5_path):
            init_result = mt5.initialize(path=mt5_path)
        else:
            init_result = mt5.initialize()
        
        if not init_result:
            error = mt5.last_error()
            print(f"❌ Error al inicializar MT5: {error}")
            return None
        print("✅ MT5 inicializado")
        
        # Paso 3: Intentar login
        print(f"3. Intentando login con credenciales...")
        print(f"   Login: {login}")
        print(f"   Server: {server}")
        
        login_result = mt5.login(login, password=password, server=server)
        
        if not login_result:
            error = mt5.last_error()
            print(f"❌ Login fallido: {error}")
            
            # Diagnóstico adicional
            if error[0] == -10003:
                print("   📝 Error -10003: Credenciales inválidas o servidor incorrecto")
            elif error[0] == -10004:
                print("   📝 Error -10004: Servidor no disponible")
            elif error[0] == -2:
                print("   📝 Error -2: Terminal no encontrado o path incorrecto")
            else:
                print(f"   📝 Código de error: {error[0]}")
                
            # Intentar obtener info de la cuenta actual
            print("\n4. Verificando cuenta actual conectada...")
            account_info = mt5.account_info()
            if account_info:
                print(f"   ⚠️ Cuenta actual: {account_info.login}")
                print(f"   ⚠️ Servidor actual: {account_info.server}")
                print(f"   ⚠️ NO SE PUDO CAMBIAR A {account_name}")
        else:
            print("✅ Login exitoso")
            
            # Paso 4: Verificar cuenta
            print("\n4. Verificando cuenta conectada...")
            account_info = mt5.account_info()
            
            if account_info:
                print(f"   Login actual: {account_info.login}")
                print(f"   Servidor: {account_info.server}")
                print(f"   Compañía: {account_info.company}")
                print(f"   Balance: ${account_info.balance:.2f}")
                print(f"   Equity: ${account_info.equity:.2f}")
                
                # Verificación crítica
                if account_info.login == login:
                    print(f"   ✅ CORRECTO: Conectado a la cuenta esperada")
                else:
                    print(f"   ❌ ERROR: Esperaba {login}, conectado a {account_info.login}")
                    print(f"   ⚠️ DUPLICACIÓN DETECTADA!")
                
                # Obtener posiciones
                positions = mt5.positions_get()
                if positions:
                    print(f"\n   Posiciones abiertas: {len(positions)}")
                    for pos in positions:
                        sl_status = "✅" if pos.sl != 0 else "❌"
                        tp_status = "✅" if pos.tp != 0 else "❌"
                        print(f"   #{pos.ticket} {pos.symbol}: SL{sl_status} TP{tp_status}")
                
                return account_info.login
            else:
                print("❌ No se pudo obtener información de la cuenta")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        mt5.shutdown()
        print("5. Conexión cerrada")

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        DIAGNÓSTICO DETALLADO DE CONEXIÓN MT5              ║
    ║              Detecta problemas de duplicación             ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Configuración de cuentas
    accounts = [
        {
            'name': 'AVA_REAL',
            'login': 89390972,
            'password': 'Naty1140855133$',
            'server': 'Ava-Real 1-MT5',
            'paths_to_try': [
                r'C:\Program Files\MetaTrader 5\terminal64.exe',
                r'C:\Program Files\MetaTrader 5 AVA\terminal64.exe',
                r'C:\Program Files\AVA MetaTrader 5\terminal64.exe',
                r'C:\Program Files (x86)\MetaTrader 5\terminal64.exe'
            ]
        },
        {
            'name': 'EXNESS_TRIAL',
            'login': 197678662,
            'password': 'Badboy930218*',
            'server': 'Exness-MT5Trial11',
            'paths_to_try': [
                r'C:\Program Files\MetaTrader 5 Exness\terminal64.exe',
                r'C:\Program Files\Exness MetaTrader 5\terminal64.exe',
                r'C:\Program Files\MetaTrader 5 - Exness\terminal64.exe',
                r'C:\Program Files (x86)\MetaTrader 5 Exness\terminal64.exe'
            ]
        }
    ]
    
    results = []
    
    for account in accounts:
        # Buscar el path correcto
        correct_path = None
        print(f"\n{'='*60}")
        print(f"Buscando instalación de MT5 para {account['name']}...")
        
        for path in account['paths_to_try']:
            if os.path.exists(path):
                print(f"✅ Encontrado: {path}")
                correct_path = path
                break
            else:
                print(f"❌ No existe: {path}")
        
        if not correct_path:
            print(f"\n⚠️ NO SE ENCONTRÓ MT5 PARA {account['name']}")
            print("Posibles soluciones:")
            print("1. Instala MT5 desde el broker correspondiente")
            print("2. Verifica la ruta de instalación")
            continue
        
        # Probar conexión
        login_result = test_connection_detailed(
            account['name'],
            account['login'],
            account['password'],
            account['server'],
            correct_path
        )
        
        if login_result:
            results.append({
                'name': account['name'],
                'expected': account['login'],
                'actual': login_result
            })
        
        time.sleep(2)
    
    # Análisis de resultados
    print(f"\n{'='*60}")
    print("ANÁLISIS DE RESULTADOS")
    print("="*60)
    
    if len(results) == 0:
        print("❌ No se pudo conectar a ninguna cuenta")
        print("\nPOSIBLES CAUSAS:")
        print("1. MT5 no está instalado correctamente")
        print("2. Las rutas de instalación son incorrectas")
        print("3. Las credenciales son incorrectas")
        
    elif len(results) == 1:
        print(f"⚠️ Solo se conectó a una cuenta: {results[0]['name']}")
        print("\nPROBLEMA:")
        print("La otra cuenta no se puede conectar")
        
    else:
        # Verificar duplicación
        if results[0]['actual'] == results[1]['actual']:
            print("❌ DUPLICACIÓN DETECTADA!")
            print(f"Ambas cuentas muestran login: {results[0]['actual']}")
            print("\nCAUSA:")
            print("MT5 no está cambiando entre cuentas correctamente")
            print("\nSOLUCIONES:")
            print("1. Usar instalaciones separadas de MT5 para cada broker")
            print("2. Asegurarse de que cada MT5 está en una carpeta diferente")
            print("3. Ejecutar cada cuenta en procesos separados")
        else:
            print("✅ NO HAY DUPLICACIÓN")
            for r in results:
                if r['expected'] == r['actual']:
                    print(f"✅ {r['name']}: Login {r['actual']} correcto")
                else:
                    print(f"❌ {r['name']}: Esperaba {r['expected']}, obtuvo {r['actual']}")

if __name__ == "__main__":
    main()
    input("\n\nPresiona Enter para salir...")
