@echo off
cls
color 0E
title ALGO TRADER - SISTEMA PROFESIONAL

echo ================================================================================
echo                     ALGO TRADER BOT - SISTEMA PROFESIONAL
echo                         CON GESTION AUTONOMA AVANZADA
echo ================================================================================
echo.
echo Este sistema incluye:
echo   [+] Breakeven automatico inteligente
echo   [+] Trailing stop dinamico
echo   [+] Take profit parciales
echo   [+] Proteccion de ganancias
echo   [+] Gestion basada en volatilidad
echo   [+] Optimizacion por IA
echo.
echo --------------------------------------------------------------------------------
echo                           MENU PRINCIPAL
echo --------------------------------------------------------------------------------
echo.
echo   [1] INICIAR SISTEMA COMPLETO (Bot + Gestion Avanzada)
echo   [2] Solo Bot de Trading
echo   [3] Solo Gestor de Posiciones
echo   [4] Ver Monitor en Tiempo Real
echo   [5] Configurar Parametros
echo   [6] Ver Historial y Estadisticas
echo   [7] Detener Todo
echo   [0] Salir
echo.
echo --------------------------------------------------------------------------------

choice /C 12345670 /N /M "Selecciona una opcion: "

if errorlevel 8 goto :salir
if errorlevel 7 goto :detener
if errorlevel 6 goto :stats
if errorlevel 5 goto :config
if errorlevel 4 goto :monitor
if errorlevel 3 goto :gestor
if errorlevel 2 goto :bot
if errorlevel 1 goto :completo

:completo
cls
echo ================================================================================
echo                    INICIANDO SISTEMA COMPLETO
echo ================================================================================
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1/4] Verificando MetaTrader 5...
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MT5 ejecutandose
) else (
    echo Abriendo MT5...
    start "" "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
    timeout /t 10 /nobreak >nul
)

echo.
echo [2/4] Iniciando Bot Principal...
start "BOT PRINCIPAL" /min cmd /c ".venv\Scripts\python.exe FINAL_BOT.py"
timeout /t 3 /nobreak >nul

echo [3/4] Iniciando Gestor de Posiciones Inteligente...
start "SMART MANAGER" /min cmd /c ".venv\Scripts\python.exe smart_position_manager.py"
timeout /t 2 /nobreak >nul

echo [4/4] Iniciando Monitor...
echo.
echo ================================================================================
echo                         SISTEMA ACTIVO
echo ================================================================================
echo.
echo Bot Principal:        EJECUTANDOSE
echo Gestor Inteligente:   EJECUTANDOSE  
echo MetaTrader 5:         CONECTADO
echo Modo:                 AUTONOMO PROFESIONAL
echo.
echo El sistema ahora:
echo   - Analiza el mercado cada 20-30 segundos
echo   - Ejecuta trades cuando encuentra oportunidades
echo   - Aplica breakeven automaticamente
echo   - Activa trailing stop dinamico
echo   - Toma ganancias parciales
echo   - Protege las ganancias obtenidas
echo.
echo Presiona cualquier tecla para ver el monitor...
pause >nul
.venv\Scripts\python.exe MONITOR.py
goto :menu

:bot
cls
echo Iniciando solo el Bot de Trading...
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
start "BOT" cmd /c ".venv\Scripts\python.exe FINAL_BOT.py"
echo Bot iniciado. Presiona cualquier tecla para volver al menu...
pause >nul
goto :menu

:gestor
cls
echo Iniciando solo el Gestor de Posiciones...
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
start "GESTOR" cmd /c ".venv\Scripts\python.exe smart_position_manager.py"
echo Gestor iniciado. Presiona cualquier tecla para volver al menu...
pause >nul
goto :menu

:monitor
cls
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
.venv\Scripts\python.exe MONITOR.py
goto :menu

:config
cls
echo ================================================================================
echo                    CONFIGURACION DEL SISTEMA
echo ================================================================================
echo.
echo Abriendo archivo de configuracion...
notepad configs\strategy_config.py
echo.
echo Configuracion actualizada.
pause
goto :menu

:stats
cls
echo ================================================================================
echo                    ESTADISTICAS DEL SISTEMA
echo ================================================================================
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
echo.
echo Ultimas operaciones:
echo --------------------------------------------------------------------------------
if exist logs\smart_positions.log (
    type logs\smart_positions.log | findstr /C:"BREAKEVEN" /C:"TRAILING" /C:"TP PARCIAL" | tail -10
) else (
    echo No hay registros disponibles
)
echo.
pause
goto :menu

:detener
cls
echo Deteniendo todos los procesos...
taskkill /F /IM python.exe >nul 2>&1
echo.
echo [OK] Sistema detenido
pause
goto :menu

:menu
cls
goto :inicio

:salir
exit
