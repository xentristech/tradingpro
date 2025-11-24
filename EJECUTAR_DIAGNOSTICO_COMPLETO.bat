@echo off
cls
echo ============================================================
echo    DIAGNOSTICO Y EJECUCION DE SEÑALES DE TRADING
echo ============================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo.
    echo Por favor instala Python 3.8 o superior desde:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1] Verificando sistema...
echo.

REM Ejecutar diagnóstico
python DIAGNOSTICO_Y_EJECUCION.py

echo.
echo ============================================================
echo Diagnostico completado
echo.

REM Preguntar si ejecutar trading
echo Deseas iniciar el sistema de trading? (S/N)
set /p respuesta=

if /i "%respuesta%"=="S" (
    echo.
    echo Iniciando sistema de trading...
    python main.py start --mode demo
) else (
    echo.
    echo Sistema en espera. Puedes ejecutar manualmente:
    echo   - Generar señales: python SIGNAL_GENERATOR_LIVE.py
    echo   - Iniciar trading: python main.py start
    echo   - Monitorear: python MONITOR_SISTEMA.py
)

echo.
pause
