@echo off
cls
color 0A
title ALGO TRADER - EJECUTANDO

:inicio
cls
echo ================================================================================
echo                         ALGO TRADER BOT - EJECUTANDO
echo ================================================================================
echo.
echo Fecha/Hora: %date% %time%
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1] VERIFICANDO SISTEMA...
echo --------------------------------------------------------------------------------
echo.

REM Verificar MT5
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MetaTrader 5 esta ejecutandose
) else (
    echo [!] Iniciando MetaTrader 5...
    start "" "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
    timeout /t 10 /nobreak >nul
)

REM Contar procesos Python
for /f %%i in ('tasklist ^| findstr /c:"python.exe" ^| find /c /v ""') do set PYTHON_COUNT=%%i

if %PYTHON_COUNT% GTR 0 (
    echo [OK] Bot activo con %PYTHON_COUNT% procesos
) else (
    echo [!] Iniciando bot...
    start /min cmd /c ".venv\Scripts\python.exe FINAL_BOT.py"
    timeout /t 5 /nobreak >nul
)

echo.
echo [2] CONFIGURACION ACTUAL:
echo --------------------------------------------------------------------------------
.venv\Scripts\python.exe -c "from dotenv import load_dotenv; import os; load_dotenv('configs/.env'); print(f'   Symbol: {os.getenv(\"SYMBOL\")}'); print(f'   Live Trading: {os.getenv(\"LIVE_TRADING\")}'); print(f'   MT5 Login: {os.getenv(\"MT5_LOGIN\")}'); print(f'   Server: {os.getenv(\"MT5_SERVER\")}')" 2>nul

echo.
echo [3] ULTIMAS SEÑALES DEL BOT:
echo --------------------------------------------------------------------------------
if exist logs\run_*.out.log (
    for /f "delims=" %%i in ('dir /b /o-d logs\run_*.out.log 2^>nul ^| findstr /n "^" ^| findstr "^1:"') do set "LATEST_LOG=%%i"
    set LATEST_LOG=%LATEST_LOG:1:=%
    
    echo Leyendo: logs\%LATEST_LOG%
    echo.
    powershell -Command "Get-Content 'logs\%LATEST_LOG%' -Tail 5 | ForEach-Object { Write-Host $_ }"
) else (
    echo No hay logs disponibles aun...
)

echo.
echo ================================================================================
echo                              OPCIONES
echo ================================================================================
echo.
echo   [R] Refrescar pantalla
echo   [M] Monitor detallado
echo   [S] Detener bot
echo   [X] Salir
echo.
echo --------------------------------------------------------------------------------
choice /C RMSX /N /T 10 /D R /M "Selecciona opcion (se refresca en 10 seg): "

if %errorlevel%==1 goto inicio
if %errorlevel%==2 goto monitor
if %errorlevel%==3 goto stop
if %errorlevel%==4 exit

:monitor
cls
.venv\Scripts\python.exe MONITOR.py
goto inicio

:stop
echo.
echo Deteniendo bot...
taskkill /F /IM python.exe >nul 2>&1
echo Bot detenido.
pause
exit
