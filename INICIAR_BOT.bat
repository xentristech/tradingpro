@echo off
title Algo Trader Bot - Launcher
cls
echo ========================================
echo     ALGO TRADER BOT - LAUNCHER
echo ========================================
echo.

REM Cambiar al directorio del proyecto
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

REM Verificar si existe el entorno virtual
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Entorno virtual no encontrado
    echo Por favor, ejecuta primero:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Ejecutar el script de inicio
echo Iniciando sistema...
echo.
.venv\Scripts\python.exe START_BOT.py

pause
