@echo off
title ALGO TRADER V3 - SISTEMA COMPLETO CON TELEGRAM Y SEÑALES
color 0A
cls

echo ================================================================
echo                    ALGO TRADER V3 PRO
echo         SISTEMA COMPLETO CON IA, TELEGRAM Y SEÑALES
echo                     by XentrisTech  
echo ================================================================
echo.
echo [%TIME%] Iniciando sistema profesional de trading...
echo.
echo CARACTERISTICAS ACTIVAS:
echo   [+] Notificaciones por Telegram
echo   [+] Generador de señales con IA
echo   [+] 6 Estrategias de trading
echo   [+] Analisis multi-timeframe
echo   [+] Dashboards profesionales
echo   [+] Sistema de ticks MT5
echo.
echo ================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python no detectado
        echo Instala Python 3.10+ desde https://python.org
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

REM Ejecutar sistema completo
%PYTHON_CMD% execute_all_pro.py

echo.
echo ================================================================
echo.
pause