#!/usr/bin/env python
"""
Test de Conexión MT5 - Quantum Trading System
==============================================
Verifica la conexión con MetaTrader 5
"""

import os
import sys
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Cargar variables de entorno
load_dotenv()

def test_mt5_connection():
    """Test de conexión a MT5"""

    print("=" * 70)
    print("QUANTUM TRADING SYSTEM - TEST DE CONEXIÓN MT5")
    print("=" * 70)
    print()

    # Obtener credenciales
    login = os.getenv('MT5_LOGIN')
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    path = os.getenv('MT5_PATH', 'C:\Program Files\MetaTrader 5\terminal64.exe')

    print(f"📋 Configuración:")
    print(f"   Login: {login}")
    print(f"   Server: {server}")
    print(f"   Path: {path}")
    print()

    # Inicializar MT5
    print("🔄 Inicializando MT5...")

    if not mt5.initialize(
        path=path,
        login=int(login),
        password=password,
        server=server
    ):
        print(f"❌ Error al inicializar MT5: {mt5.last_error()}")
        mt5.shutdown()
        return False

    print("✅ MT5 inicializado correctamente")
    print()

    # Obtener información de la cuenta
    account_info = mt5.account_info()

    if account_info is None:
        print(f"❌ Error al obtener información de cuenta: {mt5.last_error()}")
        mt5.shutdown()
        return False

    print("=" * 70)
    print("📊 INFORMACIÓN DE LA CUENTA")
    print("=" * 70)
    print(f"   Login: {account_info.login}")
    print(f"   Servidor: {account_info.server}")
    print(f"   Nombre: {account_info.name}")
    print(f"   Balance: ${account_info.balance:.2f}")
    print(f"   Equity: ${account_info.equity:.2f}")
    print(f"   Margin: ${account_info.margin:.2f}")
    print(f"   Free Margin: ${account_info.margin_free:.2f}")
    print(f"   Profit: ${account_info.profit:.2f}")
    print(f"   Apalancamiento: 1:{account_info.leverage}")
    print(f"   Moneda: {account_info.currency}")
    print()

    # Cerrar conexión
    mt5.shutdown()
    print("✅ Test completado exitosamente")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = test_mt5_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
