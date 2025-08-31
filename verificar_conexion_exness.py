#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VERIFICAR CONEXIÓN MT5 - CUENTA EXNESS
=======================================
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import MetaTrader5 as mt5
from datetime import datetime

# Cargar configuración
env_path = Path("configs/.env")
if env_path.exists():
    load_dotenv(env_path)
    print("✓ Configuración cargada desde configs/.env")

print("="*60)
print("   VERIFICANDO CONEXIÓN CON EXNESS MT5")
print("="*60)
print()

# Obtener credenciales
login = int(os.getenv("MT5_LOGIN", "0"))
password = os.getenv("MT5_PASSWORD", "")
server = os.getenv("MT5_SERVER", "")
path = os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")

print("CREDENCIALES CONFIGURADAS:")
print(f"  Usuario: {login}")
print(f"  Server: {server}")
print(f"  Path MT5: {path}")
print()

print("INTENTANDO CONECTAR...")
print("-"*40)

# Intentar inicializar MT5
if not mt5.initialize(path=path, login=login, password=password, server=server):
    error = mt5.last_error()
    print(f"✗ ERROR: No se pudo conectar a MT5")
    print(f"  Código de error: {error}")
    print()
    print("POSIBLES SOLUCIONES:")
    print("1. Verifica que MetaTrader 5 esté instalado")
    print("2. Verifica las credenciales")
    print("3. Asegúrate de que el servidor sea correcto")
    print("4. Intenta abrir MT5 manualmente primero")
    mt5.shutdown()
    sys.exit(1)

print("✅ CONEXIÓN EXITOSA!")
print()

# Obtener información de la cuenta
account = mt5.account_info()
if account:
    print("INFORMACIÓN DE LA CUENTA:")
    print("-"*40)
    print(f"  Número de cuenta: {account.login}")
    print(f"  Servidor: {account.server}")
    print(f"  Nombre: {account.name}")
    print(f"  Compañía: {account.company}")
    print(f"  Divisa: {account.currency}")
    print(f"  Balance: ${account.balance:,.2f}")
    print(f"  Equity: ${account.equity:,.2f}")
    print(f"  Margen libre: ${account.margin_free:,.2f}")
    print(f"  Apalancamiento: 1:{account.leverage}")
    print(f"  Tipo de cuenta: {'DEMO' if account.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else 'REAL'}")
    print()

# Verificar símbolos disponibles
print("VERIFICANDO SÍMBOLOS DISPONIBLES:")
print("-"*40)

# Símbolos populares para probar
test_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]

available_symbols = []
for symbol in test_symbols:
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is not None and symbol_info.visible:
        available_symbols.append(symbol)
        print(f"  ✓ {symbol} - Disponible")
    else:
        print(f"  ✗ {symbol} - No disponible")

if available_symbols:
    print()
    print(f"SÍMBOLO RECOMENDADO: {available_symbols[0]}")
    
    # Obtener precio actual del primer símbolo disponible
    symbol = available_symbols[0]
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"  Precio actual: {tick.bid:.5f} / {tick.ask:.5f}")
        print(f"  Spread: {(tick.ask - tick.bid)*10000:.1f} pips")

# Verificar posiciones abiertas
positions = mt5.positions_get()
print()
print(f"POSICIONES ABIERTAS: {len(positions) if positions else 0}")

if positions:
    for pos in positions:
        print(f"  - {pos.symbol}: {pos.type_description} {pos.volume} lotes")
        print(f"    P&L: ${pos.profit:.2f}")

# Cerrar conexión
mt5.shutdown()

print()
print("="*60)
print("✅ PRUEBA COMPLETADA - SISTEMA LISTO PARA OPERAR")
print("="*60)
print()
print("PRÓXIMOS PASOS:")
print("1. Si todo está correcto, ejecuta: python START_TRADING_SYSTEM.py")
print("2. O usa el bot simple: python simple_bot.py")
print("3. Para ver el dashboard: python simple_dashboard.py")
