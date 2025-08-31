#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CONFIGURACIÓN INICIAL - ALGO TRADER V3
======================================
Este script te ayudará a configurar el sistema
"""

import os
import sys
from pathlib import Path

def main():
    print("="*60)
    print("   CONFIGURACIÓN INICIAL - ALGO TRADER V3")
    print("="*60)
    print()
    
    env_path = Path("configs/.env")
    
    print("PASO 1: Configuración de MetaTrader 5")
    print("-" * 40)
    print("\nNecesitas tener MetaTrader 5 instalado y una cuenta (demo o real)")
    print("\nIngresa los siguientes datos:")
    
    mt5_login = input("1. Número de cuenta MT5: ").strip()
    mt5_password = input("2. Contraseña MT5: ").strip()
    mt5_server = input("3. Servidor (ej: MetaQuotes-Demo): ").strip()
    
    print("\nPASO 2: Configuración de Trading")
    print("-" * 40)
    symbol = input("4. Símbolo a operar (ej: EURUSD, BTCUSD): ").strip() or "EURUSD"
    live_trading = input("5. ¿Activar trading real? (si/no): ").strip().lower()
    live_trading = "true" if live_trading == "si" else "false"
    
    print("\nPASO 3: API Keys (opcional)")
    print("-" * 40)
    print("Puedes dejar en blanco si no tienes estas APIs")
    twelvedata_key = input("6. TwelveData API Key (Enter para omitir): ").strip() or "4b8ba8b4e1984d5f8a91234567890abc"
    telegram_token = input("7. Telegram Bot Token (Enter para omitir): ").strip() or "your_telegram_bot_token"
    telegram_chat = input("8. Telegram Chat ID (Enter para omitir): ").strip() or "your_telegram_chat_id"
    
    # Leer el archivo .env actual
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # Usar el ejemplo como base
        example_path = Path(".env.example")
        if example_path.exists():
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = ""
    
    # Actualizar valores
    replacements = {
        'YOUR_MT5_LOGIN': mt5_login,
        'MT5_LOGIN=YOUR_LOGIN_HERE': f'MT5_LOGIN={mt5_login}',
        'MT5_PASSWORD=YOUR_PASSWORD_HERE': f'MT5_PASSWORD={mt5_password}',
        'MT5_SERVER=YourBroker-Demo': f'MT5_SERVER={mt5_server}',
        'MT5_SERVER=YOUR_SERVER_HERE': f'MT5_SERVER={mt5_server}',
        'SYMBOL=BTCUSDm': f'SYMBOL={symbol}',
        'LIVE_TRADING=false': f'LIVE_TRADING={live_trading}',
        'TWELVEDATA_API_KEY=4b8ba8b4e1984d5f8a91234567890abc': f'TWELVEDATA_API_KEY={twelvedata_key}',
        'TELEGRAM_TOKEN=your_telegram_bot_token': f'TELEGRAM_TOKEN={telegram_token}',
        'TELEGRAM_CHAT_ID=your_telegram_chat_id': f'TELEGRAM_CHAT_ID={telegram_chat}',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Guardar configuración
    env_path.parent.mkdir(exist_ok=True)
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("✅ CONFIGURACIÓN GUARDADA EXITOSAMENTE")
    print("="*60)
    print()
    print("Tu archivo de configuración se guardó en: configs/.env")
    print()
    print("PRÓXIMOS PASOS:")
    print("1. Asegúrate de que MetaTrader 5 esté abierto")
    print("2. Ejecuta: python START_TRADING_SYSTEM.py")
    print("3. O usa: START_SYSTEM.bat")
    print()
    print("¡Listo para comenzar a operar!")
    
if __name__ == "__main__":
    main()
