@echo off
cls
color 0B
title ALGO TRADER - Iniciando MT5 y Bot

echo ╔════════════════════════════════════════════════════════════════╗
echo ║           ALGO TRADER BOT - INICIALIZACIÓN COMPLETA           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1/4] Verificando MetaTrader 5...
echo ────────────────────────────────────────────────────────────────
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ✓ MetaTrader 5 ya está ejecutándose
) else (
    echo Iniciando MetaTrader 5...
    start "" "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
    echo Esperando 10 segundos para que MT5 se inicie...
    timeout /t 10 >nul
)

echo.
echo [2/4] Verificando conexión con MT5...
echo ────────────────────────────────────────────────────────────────
.venv\Scripts\python.exe -c "import MetaTrader5 as mt5; print('✓ Librería MT5 instalada') if mt5 else print('✗ Error')"

echo.
echo [3/4] Conectando a la cuenta...
echo ────────────────────────────────────────────────────────────────
.venv\Scripts\python.exe CONECTAR_MT5.py

echo.
echo [4/4] Estado del Bot...
echo ────────────────────────────────────────────────────────────────
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /C "python.exe" > temp.txt
set /p count=<temp.txt
del temp.txt

if %count% GTR 0 (
    color 0A
    echo ✓ Bot ejecutándose con %count% procesos Python activos
    echo.
    echo ╔════════════════════════════════════════════════════════════════╗
    echo ║                    BOT OPERANDO CORRECTAMENTE                 ║
    echo ╚════════════════════════════════════════════════════════════════╝
) else (
    color 0E
    echo ⚠ Bot no detectado. Iniciando...
    echo.
    start /min .venv\Scripts\python.exe -m orchestrator.run
    start /min .venv\Scripts\python.exe -m orchestrator.positions
    timeout /t 5 >nul
    echo ✓ Bot iniciado
)

echo.
echo ────────────────────────────────────────────────────────────────
echo OPCIONES:
echo   [M] Ver Monitor en tiempo real
echo   [L] Ver Logs
echo   [D] Detener Bot
echo   [X] Salir
echo ────────────────────────────────────────────────────────────────
echo.
choice /C MLDX /N /M "Selecciona una opción: "

if errorlevel 4 goto :end
if errorlevel 3 goto :stop
if errorlevel 2 goto :logs
if errorlevel 1 goto :monitor

:monitor
echo.
echo Abriendo monitor...
.venv\Scripts\python.exe MONITOR.py
goto :end

:logs
echo.
echo Mostrando últimos logs...
dir logs\*.out.log /O-D /B | head -5
echo.
type logs\positions_*.out.log | tail -50
pause
goto :end

:stop
echo.
echo Deteniendo bot...
taskkill /F /IM python.exe 2>nul
echo Bot detenido
pause
goto :end

:end
exit
