@echo off
cls
echo ========================================================
echo           INSTALADOR DE ALGO TRADER V3
echo              Configuracion Automatica
echo ========================================================
echo.
echo Este instalador:
echo - Verificara Python 3.10+
echo - Instalara todas las dependencias
echo - Configurara el entorno de trading
echo - Creara las carpetas necesarias
echo.
echo ========================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo.
    echo Por favor:
    echo 1. Descarga Python desde https://python.org
    echo 2. Durante la instalacion, marca "Add Python to PATH"
    echo 3. Reinicia este instalador
    echo.
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

REM Ejecutar instalador
python INSTALL.py

echo.
echo ========================================================
echo.
pause