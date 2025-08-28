@echo off
cls
color 0A
title ALGO TRADER BOT - EJECUTANDO

echo ============================================================
echo                    ALGO TRADER BOT v3                     
echo ============================================================
echo.
echo [%date% %time%] Iniciando sistema...
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

if not exist ".venv\Scripts\python.exe" (
    color 0C
    echo ERROR: No se encuentra el entorno virtual Python
    echo.
    echo Por favor ejecuta primero:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] Entorno virtual encontrado
echo.
echo ------------------------------------------------------------
echo                    INFORMACION DEL SISTEMA                
echo ------------------------------------------------------------

.venv\Scripts\python.exe -c "import sys; print(f'Python: {sys.version.split()[0]}')"
.venv\Scripts\python.exe -c "import MetaTrader5; print('MetaTrader5: Instalado')" 2>nul || echo MetaTrader5: No instalado
.venv\Scripts\python.exe -c "import pandas; print(f'Pandas: {pandas.__version__}')" 2>nul || echo Pandas: No instalado
.venv\Scripts\python.exe -c "from dotenv import load_dotenv; import os; load_dotenv('configs/.env'); print(f'MT5 Login: {os.getenv(\"MT5_LOGIN\")}'); print(f'Symbol: {os.getenv(\"SYMBOL\")}'); print(f'Live Mode: {os.getenv(\"LIVE_TRADING\")}')"

echo.
echo ------------------------------------------------------------
echo                    EJECUTANDO BOT PRINCIPAL               
echo ------------------------------------------------------------
echo.
echo Presiona Ctrl+C para detener el bot
echo.

.venv\Scripts\python.exe FINAL_BOT.py

if errorlevel 1 (
    color 0C
    echo.
    echo ============================================================
    echo                         ERROR                              
    echo ============================================================
    echo El bot encontro un error. Revisa:
    echo   1. Que MetaTrader 5 este abierto
    echo   2. Las credenciales en configs\.env
    echo   3. Los logs en la carpeta logs\
    echo.
) else (
    color 0A
    echo.
    echo ============================================================
    echo                    BOT DETENIDO                           
    echo ============================================================
)

pause
