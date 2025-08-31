@echo off
cls
color 0E
echo ================================================================
echo            VERIFICADOR DE ESTADO - ALGO TRADER V3
echo ================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Python no detectado
        echo.
        echo Instala Python 3.10+ desde https://python.org
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

REM Ejecutar verificador
%PYTHON_CMD% check_system_status.py

pause