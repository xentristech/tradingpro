@echo off
cls
color 0B
echo ================================================================
echo              TEST DE NOTIFICACIONES TELEGRAM
echo                    ALGO TRADER V3
echo ================================================================
echo.
echo Este test verificara y enviara mensajes de prueba a Telegram
echo.
echo ================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python no detectado
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

REM Ejecutar test
%PYTHON_CMD% test_telegram.py

pause