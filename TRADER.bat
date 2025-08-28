@echo off
REM ============================================
REM ALGO TRADER v3.0 - LAUNCHER UNIFICADO
REM ============================================
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
color 0A

cd /d "%~dp0"

echo.
echo ============================================
echo      🤖 ALGO TRADER v3.0 - LAUNCHER
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no encontrado
    echo    Instala Python 3.10+ desde python.org
    pause
    exit /b 1
)

REM Menu principal
:MENU
echo Selecciona una opción:
echo.
echo   [1] 🚀 INICIAR BOT (Demo)
echo   [2] 📊 INICIAR BOT (Paper Trading)
echo   [3] ⚠️  INICIAR BOT (LIVE - Real Money)
echo   [4] 🔍 VERIFICAR SISTEMA
echo   [5] 📦 INSTALAR/ACTUALIZAR DEPENDENCIAS
echo   [6] 📈 ABRIR DASHBOARD (Streamlit)
echo   [7] 📝 VER LOGS
echo   [8] 🖼️  GENERAR SNAPSHOT DEL MERCADO
echo   [9] ⚙️  CONFIGURAR .env
echo   [10] ⚙️  CONFIGURAR settings.yaml
echo   [11] 📬 ENVIAR RESUMEN DIARIO AHORA
echo   [12] 🎛️  TOGGLES RÁPIDOS (.env)
echo   [13] 🧪 VERIFICADOR POST-INSTALACIÓN
echo   [14] ⏸️  PAUSAR BOT (local)
echo   [15] ▶️  REANUDAR BOT (local)
echo   [16] 🛑  DETENER BOT (local)
echo   [17] 📊  ESTADO (local)
echo   [0] ❌ SALIR
echo.

set /p choice="Opción (0-9): "

if "%choice%"=="1" goto START_DEMO
if "%choice%"=="2" goto START_PAPER
if "%choice%"=="3" goto START_LIVE
if "%choice%"=="4" goto CHECK_SYSTEM
if "%choice%"=="5" goto INSTALL_DEPS
if "%choice%"=="6" goto START_DASHBOARD
if "%choice%"=="7" goto VIEW_LOGS
if "%choice%"=="8" goto MARKET_SNAPSHOT
if "%choice%"=="9" goto EDIT_CONFIG
if "%choice%"=="10" goto EDIT_SETTINGS
if "%choice%"=="11" goto SEND_DAILY_SUMMARY
if "%choice%"=="12" goto QUICK_TOGGLES
if "%choice%"=="13" goto POST_INSTALL
if "%choice%"=="14" goto PAUSE_LOCAL
if "%choice%"=="15" goto RESUME_LOCAL
if "%choice%"=="16" goto STOP_LOCAL
if "%choice%"=="17" goto STATUS_LOCAL
if "%choice%"=="0" goto EXIT

echo.
echo ⚠️ Opción inválida. Intenta de nuevo.
echo.
pause
cls
goto MENU

:POST_INSTALL
echo.
echo 🧪 Ejecutando verificador post-instalación...
echo.
python tools\post_install_check.py --config configs\.env --symbol BTCUSDm --interval 15min
echo.
pause
goto MENU

:SEND_DAILY_SUMMARY
echo.
echo 📬 Enviando resumen diario a Telegram...
echo.
python cli.py trade summary --config configs\.env
echo.
pause
goto MENU

:QUICK_TOGGLES
echo.
echo 🎛️ Toggles rápidos (.env overrides)
echo.
echo   [1] Alternar ALLOW_WEEKENDS (true/false)
echo   [2] Ajustar VOLATILITY_MAX (ej: 0.05)
echo   [3] Ajustar REPORT_HOUR (0-23)
echo   [4] Ajustar MARKET_HOURS_START/END
echo   [5] Volver al menú
echo.
set /p tsel="Opción (1-5): "
if "%tsel%"=="1" goto TOGGLE_WEEKENDS
if "%tsel%"=="2" goto SET_VOLMAX
if "%tsel%"=="3" goto SET_REPHOUR
if "%tsel%"=="4" goto SET_MARKETHOURS
goto MENU

:TOGGLE_WEEKENDS
for /f "tokens=2 delims==" %%v in ('findstr /B /C:"ALLOW_WEEKENDS=" configs\.env 2^>nul') do set cur=%%v
if /I "%cur%"=="true" (
  set newval=false
) else (
  set newval=true
)
python tools\toggle_settings.py --config configs\.env --key ALLOW_WEEKENDS --value %newval%
echo Hecho: ALLOW_WEEKENDS=%newval%
pause
goto QUICK_TOGGLES

:SET_VOLMAX
set /p vmax="Nuevo VOLATILITY_MAX (ej: 0.06): "
if "%vmax%"=="" goto QUICK_TOGGLES
python tools\toggle_settings.py --config configs\.env --key VOLATILITY_MAX --value %vmax%
echo Hecho: VOLATILITY_MAX=%vmax%
pause
goto QUICK_TOGGLES

:SET_REPHOUR
set /p rh="Nuevo REPORT_HOUR (0-23): "
if "%rh%"=="" goto QUICK_TOGGLES
python tools\toggle_settings.py --config configs\.env --key REPORT_HOUR --value %rh%
echo Hecho: REPORT_HOUR=%rh%
pause
goto QUICK_TOGGLES

:SET_MARKETHOURS
set /p hs="Inicio (HH:MM): "
set /p he="Fin (HH:MM): "
if not "%hs%"=="" python tools\toggle_settings.py --config configs\.env --key MARKET_HOURS_START --value %hs%
if not "%he%"=="" python tools\toggle_settings.py --config configs\.env --key MARKET_HOURS_END --value %he%
echo Hecho.
pause
goto QUICK_TOGGLES

:EDIT_SETTINGS
echo.
echo ⚙️ Abriendo settings.yaml...
echo.
if exist "configs\settings.yaml" (
    notepad configs\settings.yaml
) else (
    echo ⚠️ settings.yaml no encontrado. Creando desde ejemplo...
    if exist "configs\settings.yaml.example" (
        copy configs\settings.yaml.example configs\settings.yaml >nul
        notepad configs\settings.yaml
    ) else (
        echo ❌ No se encontró settings.yaml.example
    )
)
echo.
pause
goto MENU

:START_DEMO
echo.
echo 🚀 Iniciando bot en modo DEMO...
echo.
python cli.py trade run --mode demo --config configs/.env
if errorlevel 1 (
    echo.
    echo ❌ Error ejecutando el bot
    pause
)
goto MENU

:START_PAPER
echo.
echo 📊 Iniciando bot en modo PAPER TRADING...
echo.
python cli.py trade run --mode paper --config configs/.env
if errorlevel 1 (
    echo.
    echo ❌ Error ejecutando el bot
    pause
)
goto MENU

:START_LIVE
echo.
echo ============================================
echo ⚠️  ADVERTENCIA - MODO LIVE TRADING
echo ============================================
echo.
echo   ESTÁS A PUNTO DE OPERAR CON DINERO REAL
echo   
echo   ¿Estás ABSOLUTAMENTE SEGURO?
echo.
echo   Escribe "SI ACEPTO EL RIESGO" para continuar
echo   o cualquier otra cosa para cancelar
echo.
set /p confirm="Tu respuesta: "

if /i "%confirm%"=="SI ACEPTO EL RIESGO" (
    echo.
    echo 💰 Iniciando bot en modo LIVE...
    echo.
    set /p db="¿Abrir dashboard (Streamlit) en otra ventana? (S/n): "
    if /I "%db%"=="S" (
        start "" cmd /k ".venv\Scripts\activate.bat && streamlit run streamlit_app.py --server.port 8502 --server.address 127.0.0.1"
    )
    python cli.py trade run --mode live --config configs/.env
    if errorlevel 1 (
        echo.
        echo ❌ Error ejecutando el bot
        pause
    )
) else (
    echo.
    echo ✅ Operación cancelada. Buena decisión.
    echo.
    pause
)
goto MENU

:CHECK_SYSTEM
echo.
echo 🔍 Verificando sistema...
python cli.py trade check --config configs/.env
if errorlevel 1 (
    echo.
    echo ❌ Error en la verificacion del sistema
    pause
)
goto MENU

:MARKET_SNAPSHOT
echo.
echo 🖼️ Generando imagen del mercado con SL/TP y S/R...
echo.
set /p sym="Símbolo (ENTER=usar de .env): "
set /p tf="Timeframe (5min/15min/1h/4h) [ENTER=15min]: "
if "%sym%"=="" set sym=
if "%tf%"=="" set tf=15min

if "%sym%"=="" (
  python cli.py trade snapshot --config configs/.env --interval %tf%
) else (
  python cli.py trade snapshot --config configs/.env --symbol %sym% --interval %tf%
)
if errorlevel 1 (
  echo.
  echo ❌ No se pudo generar el snapshot. Verifica TWELVEDATA_API_KEY.
  pause
) else (
  echo.
  echo ✅ Imagen generada en charts\market_snapshot.png
  pause
)
goto MENU

:INSTALL_DEPS
echo.
echo 📦 Instalando/Actualizando dependencias...
echo.

REM Crear entorno virtual si no existe
if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
)

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo ✅ Dependencias instaladas
echo.
pause
goto MENU

:START_DASHBOARD
echo.
echo 📈 Abriendo dashboard...
echo.

REM Activar entorno virtual si existe
if exist ".venv" (
    call .venv\Scripts\activate.bat
)

REM Iniciar Streamlit en nueva ventana
start "" cmd /k ".venv\Scripts\activate.bat && streamlit run streamlit_app.py --server.port 8502 --server.address 127.0.0.1"

echo.
echo ✅ Dashboard iniciado en http://127.0.0.1:8502
echo.
pause
goto MENU

:VIEW_LOGS
echo.
echo 📝 Mostrando últimas líneas de logs...
echo.

if exist "logs\algo_trader_*.log" (
    REM Mostrar últimas 50 líneas del log más reciente
    for /f "delims=" %%i in ('dir /b /od logs\algo_trader_*.log') do set latest=%%i
    echo.
    echo Archivo: logs\!latest!
    echo ----------------------------------------
    powershell -command "Get-Content logs\!latest! -Tail 50"
) else (
    echo No se encontraron archivos de log.
)

echo.
pause
goto MENU

:EDIT_CONFIG
echo.
echo ⚙️ Abriendo configuración...
echo.

if exist "configs\.env" (
    notepad configs\.env
) else (
    echo.
    echo ⚠️ Archivo .env no encontrado.
    echo    Creando desde template...
    if exist "configs\.env.example" (
        copy configs\.env.example configs\.env
        notepad configs\.env
    ) else (
        echo ❌ No se encontró .env.example
    )
)

echo.
pause
goto MENU

:EXIT
echo.
echo 👋 Hasta luego!
echo.
timeout /t 2 >nul
exit /b 0


:PAUSE_LOCAL
echo PAUSE> data\command.txt
echo Enviado comando PAUSE. Si el bot está corriendo, se pausará.
pause
goto MENU

:RESUME_LOCAL
echo RESUME> data\command.txt
echo Enviado comando RESUME. Si el bot está corriendo, reanudará.
pause
goto MENU

:STOP_LOCAL
echo STOP> data\command.txt
echo Enviado comando STOP. El bot se detendrá (pausado) en el siguiente ciclo.
pause
goto MENU

:STATUS_LOCAL
echo STATUS> data\command.txt
echo Solicitado estado. Revisa Telegram o logs para respuesta.
pause
goto MENU
