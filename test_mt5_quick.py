#!/usr/bin/env python
"""
Test rápido de conexión MT5
"""
import MetaTrader5 as mt5
import time
from dotenv import load_dotenv
import os

def test_mt5_connection():
    print("=== TEST RAPIDO MT5 ===")
    
    # Cargar configuración
    load_dotenv('configs/.env')
    login = int(os.getenv('MT5_LOGIN', '0'))
    password = os.getenv('MT5_PASSWORD', '')
    server = os.getenv('MT5_SERVER', '')
    
    print(f"Login: {login}")
    print(f"Server: {server}")
    print(f"Password: {'*' * len(password)}")
    
    # Test 1: Initialize
    print("\n1. Inicializando MT5...")
    if not mt5.initialize():
        print(f"ERROR initialize: {mt5.last_error()}")
        return False
    else:
        print("OK MT5 inicializado correctamente")
    
    # Test 2: Login
    print("\n2. Conectando a cuenta...")
    authorized = mt5.login(login=login, password=password, server=server)
    if not authorized:
        print(f"ERROR Error login: {mt5.last_error()}")
        mt5.shutdown()
        return False
    else:
        print("OK Login exitoso")
    
    # Test 3: Account info
    print("\n3. Obteniendo info de cuenta...")
    account_info = mt5.account_info()
    if account_info is None:
        print(f"ERROR Error account_info: {mt5.last_error()}")
        mt5.shutdown()
        return False
    else:
        print(f"OK Cuenta: {account_info.login}")
        print(f"   Balance: ${account_info.balance:.2f}")
        print(f"   Leverage: 1:{account_info.leverage}")
        print(f"   Server: {account_info.server}")
    
    # Test 4: Positions
    print("\n4. Verificando posiciones...")
    positions = mt5.positions_get()
    if positions is None:
        print(f"ERROR Error positions: {mt5.last_error()}")
    else:
        print(f"OK Posiciones encontradas: {len(positions)}")
        for pos in positions:
            print(f"   - {pos.symbol}: {pos.type} {pos.volume} (Profit: ${pos.profit:.2f})")
    
    print(f"\n5. Last error: {mt5.last_error()}")
    
    mt5.shutdown()
    print("\nOK Test completado exitosamente")
    return True

if __name__ == "__main__":
    test_mt5_connection()