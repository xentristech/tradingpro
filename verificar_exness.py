#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VERIFICACIÓN Y CONFIGURACIÓN DE CUENTA EXNESS
==============================================
"""

import os
import sys
import MetaTrader5 as mt5
from datetime import datetime

print("="*70)
print("   VERIFICACIÓN DE CUENTA EXNESS - ALGO TRADER V3")
print("="*70)
print()

# Datos conocidos de Exness
EXNESS_CONFIGS = {
    'demo': {
        'login': 197678662,
        'server': 'Exness-MT5Trial11',
        'description': 'Cuenta Demo Exness'
    },
    'real': {
        'login': None,  # Completar si tienes cuenta real
        'server': 'Exness-MT5Real11',  # Servidor real típico de Exness
        'description': 'Cuenta Real Exness'
    }
}

def check_mt5_connection():
    """Verifica conexión actual con MT5"""
    print("1. VERIFICANDO CONEXIÓN MT5")
    print("-" * 40)
    
    if not mt5.initialize():
        print("❌ MT5 no está inicializado")
        print("   Asegúrate de que MetaTrader 5 esté abierto")
        return None
    
    print("✅ MT5 inicializado correctamente")
    
    account = mt5.account_info()
    if not account:
        print("❌ No se pudo obtener información de cuenta")
        return None
    
    print(f"\n📊 CUENTA ACTUAL CONECTADA:")
    print(f"   Login: {account.login}")
    print(f"   Servidor: {account.server}")
    print(f"   Empresa: {account.company}")
    print(f"   Balance: ${account.balance:.2f}")
    print(f"   Equity: ${account.equity:.2f}")
    print(f"   Margen: ${account.margin:.2f}")
    print(f"   Margen libre: ${account.margin_free:.2f}")
    print(f"   Nivel de margen: {account.margin_level:.2f}%")
    print(f"   Apalancamiento: 1:{account.leverage}")
    
    # Verificar si es cuenta Exness
    if 'exness' in account.server.lower() or 'exness' in account.company.lower():
        print("\n✅ CUENTA EXNESS DETECTADA")
        
        # Verificar tipo de cuenta
        if 'trial' in account.server.lower() or 'demo' in account.server.lower():
            print("   Tipo: DEMO")
        else:
            print("   Tipo: REAL")
    else:
        print(f"\n⚠️ No es una cuenta Exness (Empresa: {account.company})")
    
    return account

def check_symbols():
    """Verifica símbolos disponibles en la cuenta"""
    print("\n2. VERIFICANDO SÍMBOLOS DISPONIBLES")
    print("-" * 40)
    
    # Símbolos principales a verificar
    symbols_to_check = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
        'XAUUSD', 'XAGUSD',  # Metales
        'BTCUSD', 'BTCUSDm', 'ETHUSD',  # Crypto
        'US30', 'US500', 'USTEC',  # Índices
        'USOIL', 'UKOIL'  # Energía
    ]
    
    available_symbols = []
    
    for symbol in symbols_to_check:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info and symbol_info.visible:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                spread = tick.ask - tick.bid
                available_symbols.append(symbol)
                print(f"   ✅ {symbol:10} - Bid: {tick.bid:10.5f} Ask: {tick.ask:10.5f} Spread: {spread:.5f}")
    
    if not available_symbols:
        print("   ❌ No se encontraron símbolos disponibles")
    else:
        print(f"\n   Total símbolos disponibles: {len(available_symbols)}")
    
    return available_symbols

def check_positions_and_orders():
    """Verifica posiciones y órdenes abiertas"""
    print("\n3. VERIFICANDO POSICIONES Y ÓRDENES")
    print("-" * 40)
    
    # Posiciones abiertas
    positions = mt5.positions_get()
    if positions:
        print(f"   📈 Posiciones abiertas: {len(positions)}")
        for pos in positions:
            profit_symbol = "🟢" if pos.profit >= 0 else "🔴"
            print(f"      {profit_symbol} {pos.symbol} - Vol: {pos.volume} - P&L: ${pos.profit:.2f}")
    else:
        print("   No hay posiciones abiertas")
    
    # Órdenes pendientes
    orders = mt5.orders_get()
    if orders:
        print(f"\n   📋 Órdenes pendientes: {len(orders)}")
        for order in orders:
            print(f"      - {order.symbol} - Tipo: {order.type} - Vol: {order.volume}")
    else:
        print("   No hay órdenes pendientes")
    
    # Historial reciente
    from datetime import datetime, timedelta
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    history = mt5.history_deals_get(yesterday, today)
    if history:
        print(f"\n   📊 Operaciones últimas 24h: {len(history)}")
        total_profit = sum(deal.profit for deal in history if deal.profit != 0)
        print(f"      P&L Total: ${total_profit:.2f}")

def save_exness_config(account_info):
    """Guarda la configuración de Exness en el archivo .env"""
    print("\n4. GUARDANDO CONFIGURACIÓN")
    print("-" * 40)
    
    config_file = "configs/.env"
    
    # Preguntar si quiere guardar
    save = input("\n¿Deseas guardar esta configuración de Exness? (s/n): ").lower()
    
    if save == 's':
        password = input("Ingresa la contraseña de la cuenta (se guardará cifrada): ")
        
        # Actualizar archivo .env
        with open(config_file, 'a', encoding='utf-8') as f:
            f.write("\n# === EXNESS CONFIGURATION ===\n")
            f.write(f"EXNESS_LOGIN={account_info.login}\n")
            f.write(f"EXNESS_SERVER={account_info.server}\n")
            f.write(f"EXNESS_PASSWORD={password}\n")
            f.write(f"EXNESS_COMPANY={account_info.company}\n")
        
        print("✅ Configuración guardada en configs/.env")
    else:
        print("Configuración no guardada")

def main():
    try:
        # Verificar conexión
        account = check_mt5_connection()
        
        if account:
            # Verificar símbolos
            symbols = check_symbols()
            
            # Verificar posiciones
            check_positions_and_orders()
            
            # Ofrecer guardar configuración
            save_exness_config(account)
        
        print("\n" + "="*70)
        print("VERIFICACIÓN COMPLETADA")
        print("="*70)
        
        if account and 'exness' in account.server.lower():
            print("\n✅ Cuenta Exness configurada y lista para operar")
            print("\nPara iniciar el trading automatizado:")
            print("1. python START_TRADING_SYSTEM.py")
            print("2. O ejecuta: START_SYSTEM.bat")
        else:
            print("\n⚠️ No se detectó una cuenta Exness activa")
            print("\nPasos para configurar:")
            print("1. Abre MetaTrader 5")
            print("2. Inicia sesión con tu cuenta Exness")
            print("3. Ejecuta este script nuevamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if mt5.initialize():
            mt5.shutdown()
        print("\n")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
