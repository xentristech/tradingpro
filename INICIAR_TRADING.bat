@echo off
cls
color 0A
echo ==============================================================
echo        SISTEMA DE TRADING AUTOMATICO v4.0
echo ==============================================================
echo.
echo [+] Iniciando sistema completo...
echo [+] Credenciales cargadas desde configs/.env
echo.

REM Instalar dependencias si es necesario
echo [1/4] Verificando dependencias...
pip install MetaTrader5 requests python-dotenv pandas numpy --quiet 2>nul

echo [2/4] Configuracion detectada...
echo.

REM Mostrar configuración
echo CONFIGURACION ACTUAL:
echo ---------------------
python -c "from dotenv import load_dotenv; import os; load_dotenv('configs/.env'); print(f'MT5 Login: {os.getenv(\"MT5_LOGIN\")}'); print(f'MT5 Server: {os.getenv(\"MT5_SERVER\")}'); print(f'Modo: DEMO' if os.getenv('LIVE_TRADING', 'false')=='false' else 'Modo: LIVE')"
echo.

echo [3/4] Conectando a MetaTrader 5...
echo.

echo [4/4] Ejecutando sistema de trading...
echo ==============================================================
echo.

REM Ejecutar el sistema
python EJECUTAR_SISTEMA_COMPLETO.py

echo.
echo ==============================================================
echo Sistema detenido
echo.
pause
