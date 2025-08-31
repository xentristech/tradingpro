@echo off
cls
color 0A
echo ================================================================
echo                   ALGO TRADER V3 - SISTEMA PRINCIPAL
echo                         XentrisTech Trading
echo ================================================================
echo.
echo Iniciando sistema de trading algoritmico...
echo.

REM Cambiar al directorio del proyecto
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no detectado. Por favor instala Python 3.10+
    echo Descarga desde: https://python.org
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

:MENU
echo ================================================================
echo                    SELECCIONA MODO DE EJECUCION
echo ================================================================
echo.
echo   1. MODO DEMO (Recomendado para empezar)
echo   2. MODO PAPER (Trading simulado)
echo   3. MODO LIVE (CUIDADO - Dinero real)
echo   4. Solo Dashboards (Sin trading)
echo   5. Sistema Completo
echo   6. Salir
echo.
set /p modo="Selecciona opcion (1-6): "

if "%modo%"=="1" goto DEMO
if "%modo%"=="2" goto PAPER
if "%modo%"=="3" goto LIVE
if "%modo%"=="4" goto DASHBOARDS
if "%modo%"=="5" goto COMPLETO
if "%modo%"=="6" goto SALIR

echo Opcion invalida
goto MENU

:DEMO
echo.
echo ================================================================
echo                    INICIANDO MODO DEMO
echo ================================================================
set TRADING_MODE=DEMO
goto INICIAR

:PAPER
echo.
echo ================================================================
echo                    INICIANDO MODO PAPER TRADING
echo ================================================================
set TRADING_MODE=PAPER
goto INICIAR

:LIVE
echo.
echo ================================================================
echo           ADVERTENCIA: MODO LIVE - DINERO REAL
echo ================================================================
echo.
echo Estas a punto de operar con DINERO REAL.
echo Asegurate de:
echo - Tener configuradas las credenciales correctas en .env
echo - Haber probado en modo DEMO primero
echo - Entender los riesgos del trading
echo.
set /p confirmar="Escriba CONFIRMAR para continuar: "
if not "%confirmar%"=="CONFIRMAR" goto MENU
set TRADING_MODE=LIVE
goto INICIAR

:DASHBOARDS
echo.
echo ================================================================
echo              INICIANDO SOLO DASHBOARDS
echo ================================================================
echo.
echo Iniciando dashboards en puertos:
echo - 8512: Revolutionary Dashboard
echo - 8516: Chart Simulation  
echo - 8517: TradingView Professional
echo.

REM Iniciar Revolutionary Dashboard
start "Revolutionary Dashboard" cmd /c "python src\ui\dashboards\revolutionary_dashboard_final.py"
timeout /t 2 >nul

REM Iniciar Chart Simulation
start "Chart Simulation" cmd /c "python src\ui\charts\chart_simulation_reviewed.py"
timeout /t 2 >nul

REM Iniciar TradingView Chart
start "TradingView Chart" cmd /c "python src\ui\charts\tradingview_professional_chart.py"
timeout /t 2 >nul

echo.
echo Dashboards iniciados. Abriendo navegador...
timeout /t 3 >nul

REM Abrir navegador con los dashboards
start http://localhost:8512
timeout /t 1 >nul
start http://localhost:8516
timeout /t 1 >nul
start http://localhost:8517

echo.
echo ================================================================
echo Dashboards activos en:
echo - http://localhost:8512 - Revolutionary Dashboard
echo - http://localhost:8516 - Chart Simulation
echo - http://localhost:8517 - TradingView Professional
echo.
echo Presiona Ctrl+C en cada ventana para detener
echo ================================================================
pause
goto MENU

:COMPLETO
echo.
echo ================================================================
echo            INICIANDO SISTEMA COMPLETO
echo ================================================================
set TRADING_MODE=DEMO
goto INICIAR_TODO

:INICIAR
echo.
echo Configurando entorno...
echo.

REM Configurar variables de entorno
set PYTHONPATH=%cd%;%cd%\src
set TRADING_MODE=%TRADING_MODE%

echo Modo de trading: %TRADING_MODE%
echo.

REM Iniciar sistema de ticks
echo Iniciando sistema de ticks...
start "Tick System" cmd /c "python src\data\TICK_SYSTEM_FINAL.py"
timeout /t 3 >nul

REM Iniciar bot principal
echo Iniciando bot de trading...
if exist "launcher.py" (
    start "Trading Bot" cmd /c "python launcher.py --mode %TRADING_MODE%"
) else if exist "src\trading\main_trader.py" (
    start "Trading Bot" cmd /c "python src\trading\main_trader.py"
) else if exist "main.py" (
    start "Trading Bot" cmd /c "python main.py"
) else (
    echo [ERROR] No se encontro archivo principal de trading
)
timeout /t 3 >nul

REM Iniciar dashboards
echo Iniciando dashboards...
start "Dashboard 1" cmd /c "python src\ui\dashboards\revolutionary_dashboard_final.py"
timeout /t 2 >nul
start "Dashboard 2" cmd /c "python src\ui\charts\chart_simulation_reviewed.py"

echo.
echo ================================================================
echo            SISTEMA INICIADO EXITOSAMENTE
echo ================================================================
echo.
echo Componentes activos:
echo - Sistema de ticks: ACTIVO
echo - Bot de trading: ACTIVO (Modo %TRADING_MODE%)
echo - Revolutionary Dashboard: http://localhost:8512
echo - Chart Simulation: http://localhost:8516
echo.
echo Para detener: Cierra todas las ventanas o presiona Ctrl+C
echo ================================================================
echo.
pause
goto MENU

:INICIAR_TODO
echo.
echo Iniciando TODOS los componentes...
echo.

REM Sistema de datos
echo [1/5] Sistema de datos...
start "Tick System" cmd /c "python src\data\TICK_SYSTEM_FINAL.py"
timeout /t 2 >nul

REM Bot principal
echo [2/5] Bot de trading...
start "Main Trader" cmd /c "python src\trading\main_trader.py"
timeout /t 2 >nul

REM Dashboard Revolutionary
echo [3/5] Revolutionary Dashboard...
start "Revolutionary Dashboard" cmd /c "python src\ui\dashboards\revolutionary_dashboard_final.py"
timeout /t 2 >nul

REM Chart Simulation
echo [4/5] Chart Simulation...
start "Chart Simulation" cmd /c "python src\ui\charts\chart_simulation_reviewed.py"
timeout /t 2 >nul

REM TradingView Chart
echo [5/5] TradingView Chart...
start "TradingView" cmd /c "python src\ui\charts\tradingview_professional_chart.py"
timeout /t 2 >nul

echo.
echo ================================================================
echo           SISTEMA COMPLETO INICIADO
echo ================================================================
echo.
echo Servicios activos:
echo.
echo TRADING:
echo - Tick System: Analizando mercado
echo - Trading Bot: Operando en modo %TRADING_MODE%
echo.
echo DASHBOARDS:
echo - http://localhost:8512 - Revolutionary Dashboard
echo - http://localhost:8516 - Chart Simulation
echo - http://localhost:8517 - TradingView Professional
echo.
echo ================================================================
echo.

REM Abrir navegador
start http://localhost:8512
timeout /t 1 >nul
start http://localhost:8516
timeout /t 1 >nul
start http://localhost:8517

pause
goto MENU

:SALIR
echo.
echo Gracias por usar Algo Trader V3
echo.
exit