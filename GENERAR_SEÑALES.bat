@echo off
echo ============================================================
echo GENERADOR DE SEÑALES DE TRADING v4.0
echo ============================================================
echo.
echo Analizando mercados en tiempo real...
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python 3.8 o superior
    pause
    exit /b 1
)

REM Instalar dependencias si es necesario
echo Verificando dependencias...
pip install requests --quiet 2>nul

REM Ejecutar el generador de señales
echo.
echo Iniciando análisis...
echo ============================================================
python simple_signals.py

echo.
echo ============================================================
echo Análisis completado
echo.
pause
