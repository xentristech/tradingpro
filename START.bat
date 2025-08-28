@echo off
cls
color 0B
title ALGO TRADER BOT - EJECUTANDO

echo ================================================================================
echo                         INICIANDO ALGO TRADER BOT
echo ================================================================================
echo.
echo Este script:
echo   1. Verifica que MT5 este abierto
echo   2. Inicia el bot de trading
echo   3. Muestra las operaciones en tiempo real
echo.
pause

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo.
echo [PASO 1] Verificando MetaTrader 5...
echo --------------------------------------------------------------------------------
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MetaTrader 5 ya esta ejecutandose
) else (
    echo [!] Abriendo MetaTrader 5...
    start "" "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
    echo Esperando 15 segundos para que MT5 se conecte...
    timeout /t 15
)

echo.
echo [PASO 2] Deteniendo procesos anteriores del bot...
echo --------------------------------------------------------------------------------
taskkill /F /IM python.exe >nul 2>&1
echo [OK] Limpieza completada

echo.
echo [PASO 3] Iniciando el bot de trading...
echo --------------------------------------------------------------------------------
echo.

REM Ejecutar el bot y mostrar output
.venv\Scripts\python.exe RUN_BOT_VISIBLE.py

pause
