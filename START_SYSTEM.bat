@echo off
REM ===========================================
REM ALGO TRADER V3.0 - SISTEMA DE ARRANQUE COMPLETO
REM ===========================================
cls
color 0A
title ALGO TRADER v3.0 - Professional Trading Bot

echo.
echo  ============================================
echo      ALGO TRADER v3.0 - TRADING BOT
echo           Sistema Profesional de Trading
echo  ============================================
echo.

:MENU
echo.
echo  [1] INICIAR BOT (Modo Demo)
echo  [2] INICIAR BOT (Modo Live) - CUIDADO!
echo  [3] Ver Estado del Sistema
echo  [4] Ejecutar Pruebas
echo  [5] Ver Logs
echo  [6] Detener Bot
echo  [7] Instalar/Actualizar Dependencias
echo  [8] Verificar Configuracion
echo  [9] Salir
echo.
set /p opcion="Selecciona una opcion: "

if "%opcion%"=="1" goto START_DEMO
if "%opcion%"=="2" goto START_LIVE
if "%opcion%"=="3" goto STATUS
if "%opcion%"=="4" goto TEST
if "%opcion%"=="5" goto LOGS
if "%opcion%"=="6" goto STOP
if "%opcion%"=="7" goto INSTALL
if "%opcion%"=="8" goto CONFIG
if "%opcion%"=="9" goto EXIT

echo.
echo Opcion invalida!
pause
goto MENU

:START_DEMO
cls
echo.
echo ============================================
echo   INICIANDO BOT EN MODO DEMO
echo ============================================
echo.
call .venv\Scripts\activate.bat
python main.py start --mode demo
pause
goto MENU

:START_LIVE
cls
echo.
echo ============================================
echo   ADVERTENCIA: MODO LIVE
echo   Esto realizara operaciones REALES
echo ============================================
echo.
set /p confirm="Estas SEGURO? (SI/NO): "
if /i "%confirm%"=="SI" (
    call .venv\Scripts\activate.bat
    python main.py start --mode live
) else (
    echo Cancelado por seguridad
)
pause
goto MENU

:STATUS
cls
echo.
echo ============================================
echo   ESTADO DEL SISTEMA
echo ============================================
echo.
call .venv\Scripts\activate.bat
python main.py status
pause
goto MENU

:TEST
cls
echo.
echo ============================================
echo   EJECUTANDO PRUEBAS DEL SISTEMA
echo ============================================
echo.
call .venv\Scripts\activate.bat
python main.py test
pause
goto MENU

:LOGS
cls
echo.
echo ============================================
echo   LOGS RECIENTES
echo ============================================
echo.
if exist "logs\algo_trader_%date:~-4%%date:~3,2%%date:~0,2%.log" (
    type "logs\algo_trader_%date:~-4%%date:~3,2%%date:~0,2%.log" | more
) else (
    echo No hay logs del dia de hoy
    dir logs\*.log 2>nul
)
pause
goto MENU

:STOP
cls
echo.
echo ============================================
echo   DETENIENDO BOT
echo ============================================
echo.
call .venv\Scripts\activate.bat
python main.py stop
pause
goto MENU

:INSTALL
cls
echo.
echo ============================================
echo   INSTALANDO/ACTUALIZANDO DEPENDENCIAS
echo ============================================
echo.
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Dependencias actualizadas!
pause
goto MENU

:CONFIG
cls
echo.
echo ============================================
echo   VERIFICACION DE CONFIGURACION
echo ============================================
echo.
if exist "configs\.env" (
    echo [OK] Archivo .env encontrado
    echo.
    echo Variables configuradas:
    echo -----------------------
    findstr "=" configs\.env | findstr /v "#" | findstr /v "PASSWORD"
) else (
    echo [ERROR] No se encuentra configs\.env
    echo.
    if exist "configs\.env.template" (
        echo Copiando template...
        copy configs\.env.template configs\.env
        echo Por favor edita configs\.env con tus credenciales
    )
)
pause
goto MENU

:EXIT
cls
echo.
echo ============================================
echo   Gracias por usar ALGO TRADER v3.0
echo ============================================
echo.
timeout /t 2 >nul
exit
