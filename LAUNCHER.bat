@echo off
cls
color 0B
title ALGO TRADER - LAUNCHER

:menu
cls
echo ================================================================================
echo                           ALGO TRADER BOT v3.0                               
echo                         SISTEMA DE TRADING CON IA                            
echo ================================================================================
echo.
echo                              MENU PRINCIPAL
echo.
echo   [1] EJECUTAR BOT (Simple)
echo   [2] EJECUTAR SISTEMA COMPLETO (Bot + Gestor Inteligente)  
echo   [3] VERIFICAR SISTEMA
echo   [4] VERIFICAR IA (Ollama)
echo   [5] VER LOGS
echo   [0] SALIR
echo.
echo --------------------------------------------------------------------------------
choice /C 123450 /N /M "Selecciona una opcion: "

if errorlevel 6 exit
if errorlevel 5 goto logs
if errorlevel 4 goto check_ia
if errorlevel 3 goto check_system
if errorlevel 2 goto full_system
if errorlevel 1 goto simple_bot

:simple_bot
cls
echo ================================================================================
echo                      EJECUTANDO BOT SIMPLE
echo ================================================================================
echo.
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
echo Iniciando...
echo.
.venv\Scripts\python.exe FINAL_BOT.py
pause
goto menu

:full_system
cls
echo ================================================================================
echo                    EJECUTANDO SISTEMA COMPLETO
echo ================================================================================
echo.
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
echo [1/2] Iniciando Bot Principal...
start "BOT" /min cmd /c ".venv\Scripts\python.exe FINAL_BOT.py"
timeout /t 3 >nul

echo [2/2] Iniciando Gestor de Posiciones...
start "GESTOR" /min cmd /c ".venv\Scripts\python.exe smart_position_manager.py"
timeout /t 2 >nul

echo.
echo ================================================================================
echo Sistema completo ejecutandose en segundo plano
echo.
echo Bot Trading: ACTIVO
echo Gestor Inteligente: ACTIVO
echo.
echo Para detener: Cierra las ventanas o presiona Ctrl+C
echo ================================================================================
pause
goto menu

:check_system
cls
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
.venv\Scripts\python.exe VERIFICAR_TODO.py
pause
goto menu

:check_ia
cls
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
.venv\Scripts\python.exe ollama_setup.py
pause
goto menu

:logs
cls
echo ================================================================================
echo                           ULTIMOS LOGS
echo ================================================================================
echo.
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
if exist logs\*.log (
    dir logs\*.log /O-D /B | head -5
    echo.
    echo --- ULTIMAS LINEAS ---
    type logs\*.log 2>nul | tail -20
) else (
    echo No hay logs disponibles
)
pause
goto menu
