#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BOT SIMPLE PARA EXNESS - CONFIGURACIÓN ACTUALIZADA
==================================================
"""
import os
import sys
import time
from datetime import datetime

print("="*60)
print("   BOT DE TRADING - CUENTA EXNESS")
print("="*60)

# Configuración directa para Exness
MT5_LOGIN = 197678662
MT5_PASSWORD = "Badboy930218*"
MT5_SERVER = "Exness-MT5Trial11"
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
SYMBOL = "EURUSD"

print(f"\nCONFIGURACIÓN:")
print(f"  Cuenta: {MT5_LOGIN}")
print(f"  Server: {MT5_SERVER}")
print(f"  Símbolo: {SYMBOL}")
print("-"*60)

try:
    import MetaTrader5 as mt5
    print("✓ MetaTrader5 importado")
except ImportError as e:
    print(f"✗ Error importando MetaTrader5: {e}")
    print("\nInstala con: pip install MetaTrader5")
    sys.exit(1)

print("\nCONECTANDO A MT5...")

# Inicializar MT5
if not mt5.initialize(path=MT5_PATH, login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
    error = mt5.last_error()
    print(f"✗ Error de conexión: {error}")
    print("\nVERIFICA:")
    print("1. MetaTrader 5 esté instalado")
    print("2. Las credenciales sean correctas")
    print("3. El servidor sea 'Exness-MT5Trial11'")
    mt5.shutdown()
    sys.exit(1)

print("✅ CONECTADO A MT5")

# Información de cuenta
account = mt5.account_info()
if account:
    print(f"\nINFORMACIÓN DE CUENTA:")
    print(f"  Login: {account.login}")
    print(f"  Broker: {account.company}")
    print(f"  Balance: ${account.balance:.2f}")
    print(f"  Equity: ${account.equity:.2f}")
    print(f"  Margen libre: ${account.margin_free:.2f}")
    print(f"  Apalancamiento: 1:{account.leverage}")

# Verificar símbolo
print(f"\nVERIFICANDO SÍMBOLO {SYMBOL}...")
if not mt5.symbol_select(SYMBOL, True):
    print(f"✗ Error: {SYMBOL} no disponible")
    
    # Buscar símbolos disponibles
    symbols = mt5.symbols_get()
    forex_symbols = [s.name for s in symbols if "USD" in s.name and s.visible][:5]
    
    if forex_symbols:
        print(f"\nSímbolos disponibles: {', '.join(forex_symbols)}")
        SYMBOL = forex_symbols[0]
        print(f"Usando: {SYMBOL}")
        mt5.symbol_select(SYMBOL, True)
else:
    print(f"✓ {SYMBOL} disponible")

# Obtener precio actual
tick = mt5.symbol_info_tick(SYMBOL)
if tick:
    print(f"\nPRECIO ACTUAL {SYMBOL}:")
    print(f"  Bid: {tick.bid:.5f}")
    print(f"  Ask: {tick.ask:.5f}")
    print(f"  Spread: {(tick.ask - tick.bid)*10000:.1f} pips")

# Verificar posiciones
positions = mt5.positions_get()
print(f"\nPOSICIONES ABIERTAS: {len(positions) if positions else 0}")

if positions:
    for pos in positions:
        print(f"  {pos.symbol}: {pos.type_description} {pos.volume} lotes")
        print(f"    Entrada: {pos.price_open:.5f}")
        print(f"    P&L: ${pos.profit:.2f}")

print("\n" + "="*60)
print("SISTEMA DE TRADING SIMPLE - LOOP PRINCIPAL")
print("="*60)
print("Presiona Ctrl+C para detener\n")

# Loop principal simple
ciclo = 0
try:
    while True:
        ciclo += 1
        hora = datetime.now().strftime("%H:%M:%S")
        
        # Obtener precio actual
        tick = mt5.symbol_info_tick(SYMBOL)
        if tick:
            print(f"[{hora}] Ciclo {ciclo:04d} | {SYMBOL}: {tick.bid:.5f} / {tick.ask:.5f}", end="\r")
        
        # Aquí puedes agregar tu lógica de trading
        # Por ejemplo: análisis técnico, generación de señales, etc.
        
        time.sleep(5)  # Esperar 5 segundos
        
except KeyboardInterrupt:
    print("\n\nDeteniendo bot...")

# Cerrar conexión
mt5.shutdown()
print("✓ Conexión cerrada")
print("\nBot detenido correctamente")
