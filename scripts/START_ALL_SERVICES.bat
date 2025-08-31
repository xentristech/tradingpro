@echo off
cls
color 0A
echo ============================================================
echo           INICIANDO ALGO TRADER V3 - SISTEMA COMPLETO
echo                     MODO: DEMO/DESARROLLO
echo ============================================================
echo.
echo [%TIME%] Iniciando proceso de arranque...
echo.

REM Verificar Python
echo ============================================================
echo PASO 1: Verificando Python...
echo ============================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no detectado. Intentando con py...
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR CRITICO] Python no esta instalado o no esta en el PATH
        echo Por favor instala Python 3.10+ desde https://python.org
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
        echo [OK] Python detectado usando 'py'
    )
) else (
    set PYTHON_CMD=python
    echo [OK] Python detectado
)

echo.
echo ============================================================
echo PASO 2: Verificando dependencias principales...
echo ============================================================

REM Verificar MetaTrader5
%PYTHON_CMD% -c "import MetaTrader5; print('[OK] MetaTrader5 instalado')" 2>nul
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] MetaTrader5 no instalado
    echo Instalando MetaTrader5...
    %PYTHON_CMD% -m pip install MetaTrader5 --quiet
)

REM Verificar pandas
%PYTHON_CMD% -c "import pandas; print('[OK] Pandas instalado')" 2>nul
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] Pandas no instalado
    echo Instalando pandas...
    %PYTHON_CMD% -m pip install pandas --quiet
)

REM Verificar requests
%PYTHON_CMD% -c "import requests; print('[OK] Requests instalado')" 2>nul
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] Requests no instalado
    echo Instalando requests...
    %PYTHON_CMD% -m pip install requests --quiet
)

echo.
echo ============================================================
echo PASO 3: Iniciando Sistema de Ticks MT5...
echo ============================================================
echo.
echo Lanzando TICK_SYSTEM_FINAL.py en puerto 8508...
start "Tick System" /min %PYTHON_CMD% src\data\TICK_SYSTEM_FINAL.py
timeout /t 2 >nul
echo [OK] Sistema de ticks iniciado

echo.
echo ============================================================
echo PASO 4: Iniciando Dashboards Web...
echo ============================================================
echo.

echo Lanzando Revolutionary Dashboard en puerto 8512...
start "Revolutionary Dashboard" /min %PYTHON_CMD% src\ui\dashboards\revolutionary_dashboard_final.py
timeout /t 2 >nul
echo [OK] Revolutionary Dashboard iniciado

echo.
echo Lanzando Chart Simulation en puerto 8516...
start "Chart Simulation" /min %PYTHON_CMD% src\ui\charts\chart_simulation_reviewed.py
timeout /t 2 >nul
echo [OK] Chart Simulation iniciado

echo.
echo Lanzando TradingView Professional en puerto 8517...
start "TradingView Chart" /min %PYTHON_CMD% src\ui\charts\tradingview_professional_chart.py
timeout /t 2 >nul
echo [OK] TradingView Chart iniciado

echo.
echo ============================================================
echo PASO 5: Verificando servicios...
echo ============================================================
echo.

REM Verificar que los puertos esten escuchando
netstat -an | findstr :8512 >nul
if %errorlevel% equ 0 (
    echo [OK] Dashboard principal activo en puerto 8512
) else (
    echo [ADVERTENCIA] Dashboard principal no responde en puerto 8512
)

netstat -an | findstr :8516 >nul
if %errorlevel% equ 0 (
    echo [OK] Chart Simulation activo en puerto 8516
) else (
    echo [ADVERTENCIA] Chart Simulation no responde en puerto 8516
)

netstat -an | findstr :8517 >nul
if %errorlevel% equ 0 (
    echo [OK] TradingView Chart activo en puerto 8517
) else (
    echo [ADVERTENCIA] TradingView Chart no responde en puerto 8517
)

echo.
echo ============================================================
echo PASO 6: Abriendo navegador...
echo ============================================================
echo.

timeout /t 3 >nul

echo Abriendo Dashboard Principal...
start http://localhost:8512
timeout /t 2 >nul

echo Abriendo Chart Simulation...
start http://localhost:8516
timeout /t 2 >nul

echo Abriendo TradingView Professional...
start http://localhost:8517

echo.
echo ============================================================
echo        SISTEMA INICIADO CORRECTAMENTE
echo ============================================================
echo.
echo SERVICIOS ACTIVOS:
echo.
echo   [1] Sistema de Ticks MT5    - Puerto 8508
echo   [2] Revolutionary Dashboard  - http://localhost:8512
echo   [3] Chart Simulation        - http://localhost:8516
echo   [4] TradingView Pro         - http://localhost:8517
echo.
echo ============================================================
echo.
echo OPCIONES:
echo.
echo   [T] - Iniciar Trading Bot (DEMO)
echo   [L] - Ver logs en tiempo real
echo   [S] - Detener todos los servicios
echo   [R] - Reiniciar servicios
echo   [X] - Salir (mantener servicios activos)
echo.
echo ============================================================
echo.

:MENU
set /p opcion="Selecciona una opcion (T/L/S/R/X): "

if /i "%opcion%"=="T" goto TRADING
if /i "%opcion%"=="L" goto LOGS
if /i "%opcion%"=="S" goto STOP
if /i "%opcion%"=="R" goto RESTART
if /i "%opcion%"=="X" goto EXIT

echo Opcion invalida. Por favor selecciona T, L, S, R o X
goto MENU

:TRADING
echo.
echo ============================================================
echo Iniciando Trading Bot en modo DEMO...
echo ============================================================
start "Trading Bot" %PYTHON_CMD% src\trading\main_trader.py
echo [OK] Trading Bot iniciado
echo.
goto MENU

:LOGS
echo.
echo ============================================================
echo Mostrando logs en tiempo real...
echo ============================================================
echo Presiona Ctrl+C para volver al menu
echo.
if exist logs\algo_trader.log (
    type logs\algo_trader.log
    echo.
    echo Presiona cualquier tecla para continuar...
    pause >nul
) else (
    echo No hay logs disponibles aun.
    pause
)
goto MENU

:STOP
echo.
echo ============================================================
echo Deteniendo todos los servicios...
echo ============================================================
taskkill /FI "WindowTitle eq Tick System*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Revolutionary Dashboard*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Chart Simulation*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq TradingView Chart*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Trading Bot*" /T /F >nul 2>&1
echo [OK] Todos los servicios detenidos
echo.
pause
exit

:RESTART
echo.
echo ============================================================
echo Reiniciando servicios...
echo ============================================================
goto STOP
goto INICIO

:EXIT
echo.
echo ============================================================
echo Los servicios continuan ejecutandose en segundo plano.
echo Para detenerlos, ejecuta este script y selecciona 'S'.
echo ============================================================
echo.
timeout /t 3 >nul
exit