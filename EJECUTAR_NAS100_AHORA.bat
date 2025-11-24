@echo off
cls
echo ======================================================================
echo           EJECUTANDO TRADE NAS100 - STRONG BUY SIGNAL
echo ======================================================================
echo.

REM Verificar e instalar MetaTrader5 si es necesario
echo [1/3] Verificando MetaTrader5...
python -c "import MetaTrader5" 2>nul
if %errorlevel% neq 0 (
    echo Instalando MetaTrader5...
    pip install MetaTrader5 --quiet
    echo MetaTrader5 instalado!
) else (
    echo MetaTrader5 ya instalado
)

echo.
echo [2/3] Cargando configuracion...
echo.

REM Mostrar configuración
python -c "import os; from pathlib import Path; import sys; sys.path.insert(0, str(Path('.') / 'configs')); from dotenv import load_dotenv; load_dotenv('configs/.env'); print(f'MT5 Login: {os.getenv(\"MT5_LOGIN\")}'); print(f'MT5 Server: {os.getenv(\"MT5_SERVER\")}'); print(f'Modo: DEMO' if os.getenv('LIVE_TRADING', 'false')=='false' else 'Modo: LIVE')"

echo.
echo [3/3] Ejecutando trade NAS100...
echo ======================================================================
echo.

REM Ejecutar el trade
python EJECUTAR_TRADE_NAS100.py

echo.
echo ======================================================================
echo.
pause
