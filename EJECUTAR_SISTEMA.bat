@echo off
cls
color 0A
title ALGO TRADER - SISTEMA COMPLETO

echo ================================================================================
echo                         ALGO TRADER BOT v3.0
echo                      SISTEMA PROFESIONAL COMPLETO
echo ================================================================================
echo.
echo Este sistema ejecutara:
echo   1. Verificacion del sistema
echo   2. Apertura de MetaTrader 5
echo   3. Conexion a la cuenta
echo   4. Inicio del bot de trading
echo   5. Gestor de posiciones inteligente
echo.
echo --------------------------------------------------------------------------------
pause

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

REM ===========================================
REM PASO 1: VERIFICAR SISTEMA
REM ===========================================
echo.
echo [PASO 1/5] VERIFICANDO SISTEMA...
echo --------------------------------------------------------------------------------

REM Verificar Python
.venv\Scripts\python.exe --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Python no encontrado en el entorno virtual
    echo Ejecuta: python -m venv .venv
    pause
    exit /b 1
)
echo [OK] Python encontrado

REM Verificar archivo .env
if not exist "configs\.env" (
    color 0C
    echo ERROR: No existe configs\.env
    echo Copia configs\.env.example a configs\.env y configura tus credenciales
    pause
    exit /b 1
)
echo [OK] Archivo de configuracion encontrado

REM ===========================================
REM PASO 2: ABRIR MT5
REM ===========================================
echo.
echo [PASO 2/5] VERIFICANDO METATRADER 5...
echo --------------------------------------------------------------------------------

tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe" >NUL
if %errorlevel% equ 0 (
    echo [OK] MetaTrader 5 ya esta ejecutandose
) else (
    echo [!] MetaTrader 5 no detectado
    echo Abriendo MetaTrader 5...
    
    REM Intentar abrir MT5
    if exist "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe" (
        start "" "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
    ) else if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
        start "" "C:\Program Files\MetaTrader 5\terminal64.exe"
    ) else (
        color 0E
        echo.
        echo ADVERTENCIA: No se encontro MT5
        echo Por favor, abre MetaTrader 5 manualmente
        echo.
        pause
    )
    
    echo Esperando 15 segundos para que MT5 se inicie...
    timeout /t 15 /nobreak >nul
)

REM ===========================================
REM PASO 3: VERIFICAR CONEXION
REM ===========================================
echo.
echo [PASO 3/5] VERIFICANDO CONEXION A MT5...
echo --------------------------------------------------------------------------------

.venv\Scripts\python.exe -c "import MetaTrader5 as mt5; print('OK' if mt5.initialize() else 'ERROR'); mt5.shutdown()" 2>nul | findstr "OK" >nul
if %errorlevel% equ 0 (
    echo [OK] Conexion a MT5 exitosa
) else (
    echo [!] No se pudo conectar automaticamente
    echo Ejecutando verificacion detallada...
    echo.
    .venv\Scripts\python.exe abrir_mt5.py
    echo.
)

REM ===========================================
REM PASO 4: MENU DE OPCIONES
REM ===========================================
:menu
cls
color 0B
echo ================================================================================
echo                         ALGO TRADER BOT v3.0
echo                          MENU PRINCIPAL
echo ================================================================================
echo.
echo   [1] EJECUTAR SISTEMA COMPLETO (Bot + Gestor Inteligente)
echo   [2] Solo Bot de Trading
echo   [3] Solo Gestor de Posiciones
echo   [4] Verificar Sistema
echo   [5] Monitor en Tiempo Real
echo   [6] Ver Logs
echo   [7] Detener Todo
echo   [0] Salir
echo.
echo --------------------------------------------------------------------------------

choice /C 12345670 /N /M "Selecciona una opcion: "

if errorlevel 8 goto :exit
if errorlevel 7 goto :stop
if errorlevel 6 goto :logs
if errorlevel 5 goto :monitor
if errorlevel 4 goto :verify
if errorlevel 3 goto :positions
if errorlevel 2 goto :bot
if errorlevel 1 goto :full

REM ===========================================
REM OPCION 1: SISTEMA COMPLETO
REM ===========================================
:full
cls
echo ================================================================================
echo                    INICIANDO SISTEMA COMPLETO
echo ================================================================================
echo.

echo [1/3] Iniciando Bot Principal...
start "BOT_TRADING" /min cmd /c ".venv\Scripts\python.exe FINAL_BOT.py 2>&1 | tee logs\bot.log"
timeout /t 3 /nobreak >nul

echo [2/3] Iniciando Gestor de Posiciones Inteligente...
start "POSITION_MANAGER" /min cmd /c ".venv\Scripts\python.exe smart_position_manager.py 2>&1 | tee logs\positions.log"
timeout /t 2 /nobreak >nul

echo [3/3] Sistema iniciado correctamente
echo.
echo ================================================================================
echo                         SISTEMA ACTIVO
echo ================================================================================
echo.
echo   Bot Trading:     EJECUTANDOSE
echo   Gestor:          EJECUTANDOSE
echo   MT5:             CONECTADO
echo.
echo   El sistema ahora opera de forma autonoma:
echo     - Analiza el mercado constantemente
echo     - Ejecuta trades con IA
echo     - Aplica breakeven automatico
echo     - Trailing stop dinamico
echo     - Take profit parciales
echo.
pause
goto :menu

REM ===========================================
REM OPCION 2: SOLO BOT
REM ===========================================
:bot
cls
echo Iniciando Bot de Trading...
start "BOT" cmd /c ".venv\Scripts\python.exe FINAL_BOT.py & pause"
timeout /t 3 /nobreak >nul
echo Bot iniciado
pause
goto :menu

REM ===========================================
REM OPCION 3: SOLO GESTOR
REM ===========================================
:positions
cls
echo Iniciando Gestor de Posiciones...
start "GESTOR" cmd /c ".venv\Scripts\python.exe smart_position_manager.py & pause"
timeout /t 3 /nobreak >nul
echo Gestor iniciado
pause
goto :menu

REM ===========================================
REM OPCION 4: VERIFICAR
REM ===========================================
:verify
cls
.venv\Scripts\python.exe VERIFICAR_TODO.py
pause
goto :menu

REM ===========================================
REM OPCION 5: MONITOR
REM ===========================================
:monitor
cls
.venv\Scripts\python.exe MONITOR.py
pause
goto :menu

REM ===========================================
REM OPCION 6: LOGS
REM ===========================================
:logs
cls
echo ================================================================================
echo                            ULTIMOS LOGS
echo ================================================================================
echo.
if exist logs\bot.log (
    echo --- BOT TRADING ---
    type logs\bot.log | findstr /N "." | findstr "^[0-9]*:" | sort /R | head -10
    echo.
)
if exist logs\positions.log (
    echo --- GESTOR POSICIONES ---
    type logs\positions.log | findstr /N "." | findstr "^[0-9]*:" | sort /R | head -10
    echo.
)
if exist logs\smart_positions.log (
    echo --- GESTIONES REALIZADAS ---
    type logs\smart_positions.log | findstr /C:"BREAKEVEN" /C:"TRAILING" /C:"TP PARCIAL"
)
pause
goto :menu

REM ===========================================
REM OPCION 7: DETENER
REM ===========================================
:stop
cls
echo Deteniendo todos los procesos...
taskkill /F /IM python.exe 2>nul
echo.
echo [OK] Todos los procesos detenidos
pause
goto :menu

REM ===========================================
REM SALIR
REM ===========================================
:exit
exit
