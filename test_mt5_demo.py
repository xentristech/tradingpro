#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test rápido de conexión MT5 con cuenta demo
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar configuración
env_path = Path("configs/.env")
load_dotenv(env_path)

print("="*60)
print("   TEST DE CONEXIÓN MT5 - CUENTA DEMO")
print("="*60)

try:
    import MetaTrader5 as mt5
    
    # Leer configuración
    login = os.getenv("MT5_LOGIN", "5043260986")
    password = os.getenv("MT5_PASSWORD", "Demo123456")
    server = os.getenv("MT5_SERVER", "MetaQuotes-Demo")
    
    print(f"\nIntentando conectar con:")
    print(f"  Login: {login}")
    print(f"  Server: {server}")
    print(f"  Password: {'*' * len(password)}")
    
    # Intentar conexión
    print("\nConectando a MT5...")
    
    # Inicializar MT5
    if not mt5.initialize():
        print("✗ No se pudo inicializar MT5")
        print("  Asegúrate de que MetaTrader 5 esté instalado")
        sys.exit(1)
    
    print("✓ MT5 inicializado")
    
    # Intentar login
    authorized = mt5.login(int(login), password, server)
    
    if authorized:
        print("✓ LOGIN EXITOSO!")
        
        # Mostrar info de cuenta
        account = mt5.account_info()
        if account:
            print(f"\n📊 INFORMACIÓN DE CUENTA:")
            print(f"  Número: {account.login}")
            print(f"  Balance: ${account.balance:.2f}")
            print(f"  Equity: ${account.equity:.2f}")
            print(f"  Servidor: {account.server}")
            print(f"  Divisa: {account.currency}")
            print(f"  Apalancamiento: 1:{account.leverage}")
            
        # Verificar símbolos disponibles
        symbols = mt5.symbols_get()
        if symbols:
            print(f"\n📈 Símbolos disponibles: {len(symbols)}")
            
            # Mostrar algunos populares
            popular = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
            print("\n  Símbolos populares:")
            for sym in popular:
                symbol_info = mt5.symbol_info(sym)
                if symbol_info:
                    print(f"    ✓ {sym}: ${symbol_info.bid:.5f}")
                else:
                    print(f"    ✗ {sym}: No disponible")
    else:
        error = mt5.last_error()
        print(f"✗ LOGIN FALLIDO")
        print(f"  Error: {error}")
        print("\n  Posibles soluciones:")
        print("  1. Verifica que MT5 esté abierto")
        print("  2. Prueba con estas credenciales de demo:")
        print("     - Server: MetaQuotes-Demo")
        print("     - Login: Crear nueva cuenta demo en MT5")
    
    # Cerrar conexión
    mt5.shutdown()
    print("\n✓ Conexión cerrada correctamente")
    
except ImportError:
    print("✗ MetaTrader5 no está instalado")
    print("  Ejecuta: pip install MetaTrader5")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*60)
input("Presiona Enter para salir...")
