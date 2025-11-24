"""
Quick Account Checker v3.2 - Verifica las cuentas sin duplicación
Con credenciales correctas actualizadas
"""
import MetaTrader5 as mt5
import time
from datetime import datetime
import os
from pathlib import Path

def check_account_independent(account_name, login, password, server, mt5_path=None):
    """Verifica una cuenta de forma independiente"""
    print(f"\n{'='*50}")
    print(f"Verificando: {account_name}")
    print(f"{'='*50}")
    
    try:
        # Cerrar cualquier conexión previa
        mt5.shutdown()
        time.sleep(0.5)
        
        # Inicializar MT5
        if mt5_path and os.path.exists(mt5_path):
            print(f"Usando path: {mt5_path}")
            if not mt5.initialize(path=mt5_path):
                print(f"[ERROR] No se pudo inicializar MT5 con path específico")
                return None
        else:
            if not mt5.initialize():
                print(f"[ERROR] No se pudo inicializar MT5")
                return None
        
        # Intentar login
        if login and password and server:
            print(f"Intentando login: {login} en {server}")
            if not mt5.login(login, password=password, server=server):
                error = mt5.last_error()
                print(f"[ERROR] Login fallido: {error}")
                # Continuar con la cuenta actual si el login falla
        
        # Obtener información de la cuenta
        account_info = mt5.account_info()
        if account_info:
            positions = mt5.positions_get()
            if positions is None:
                positions = []
            
            print(f"[OK] CONECTADO")
            print(f"   Login actual: {account_info.login}")
            print(f"   Servidor: {account_info.server}")
            print(f"   Compañía: {account_info.company}")
            print(f"   Balance: ${account_info.balance:.2f}")
            print(f"   Equity: ${account_info.equity:.2f}")
            print(f"   Posiciones abiertas: {len(positions)}")
            
            # Verificar posiciones sin SL/TP
            problems = 0
            for pos in positions:
                if pos.sl == 0 or pos.tp == 0:
                    problems += 1
                    print(f"   ⚠️ Posición #{pos.ticket} ({pos.symbol}) sin SL/TP")
            
            if problems > 0:
                print(f"   ⚠️ Total problemas: {problems}")
            
            # Verificación de cuenta correcta
            if account_info.login != login:
                print(f"   ⚠️ ADVERTENCIA: Login esperado {login}, obtenido {account_info.login}")
            
            return {
                'name': account_name,
                'login': account_info.login,
                'expected_login': login,
                'server': account_info.server,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'positions': len(positions),
                'problems': problems
            }
        else:
            print(f"[ERROR] No se pudo obtener información de la cuenta")
            return None
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return None
    finally:
        # Siempre cerrar la conexión
        mt5.shutdown()

def main():
    """Función principal"""
    print("""
    ====================================================
         VERIFICADOR DE CUENTAS MULTI-MT5 v3.2       
         Sin Duplicacion - Credenciales Correctas    
    ====================================================
    """)
    
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # CONFIGURACIÓN CORRECTA DE CUENTAS - Solo EXNESS para evitar conflictos
    accounts = [
        {
            'name': 'EXNESS_TRIAL',
            'login': 197678662,
            'password': 'Badboy930218*',
            'server': 'Exness-MT5Trial11',
            'path': 'C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe'
        }
    ]
    
    print("\nCREDENCIALES CONFIGURADAS:")
    print("="*50)
    for account in accounts:
        print(f"{account['name']}:")
        print(f"  Login: {account['login']}")
        print(f"  Servidor: {account['server']}")
        print(f"  Path: {account['path']}")
    
    results = []
    
    # Verificar cada cuenta independientemente
    for account in accounts:
        result = check_account_independent(
            account['name'],
            account['login'],
            account['password'],
            account['server'],
            account['path']
        )
        if result:
            results.append(result)
        time.sleep(1)  # Pequeña pausa entre verificaciones
    
    # Mostrar resumen
    print(f"\n{'='*50}")
    print("RESUMEN FINAL")
    print(f"{'='*50}")
    
    total_positions = sum(r['positions'] for r in results)
    total_problems = sum(r['problems'] for r in results)
    
    print(f"Total cuentas verificadas: {len(results)}")
    print(f"Total posiciones: {total_positions}")
    print(f"Total problemas detectados: {total_problems}")
    
    # Verificar si hay duplicación
    logins = [r['login'] for r in results]
    if len(logins) != len(set(logins)):
        print("\n⚠️ ADVERTENCIA: Se detectaron cuentas duplicadas!")
        print("   Esto puede indicar un problema con la conexión MT5")
        for r in results:
            if r['login'] != r['expected_login']:
                print(f"   {r['name']}: Esperaba {r['expected_login']}, obtuvo {r['login']}")
    else:
        print("\n[SUCCESS] No se detecto duplicacion de cuentas")
        for r in results:
            print(f"   {r['name']}: Login {r['login']} [OK]")
    
    print(f"\n{'='*50}")

if __name__ == "__main__":
    main()
    input("\nPresiona Enter para salir...")
