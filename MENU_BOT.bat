@echo off
cls
title TRADING BOT LAUNCHER
echo ============================================
echo    SELECCIONE COMO INICIAR EL BOT
echo ============================================
echo.
echo 1. Ejecutar BOT PRINCIPAL (Enhanced)
echo 2. Ejecutar BOT ORIGINAL (Orchestrator)
echo 3. Ver estado de cuenta MT5
echo 4. Salir
echo.
set /p choice=Seleccione opcion (1-4): 

cd /d C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2

if "%choice%"=="1" (
    cls
    echo INICIANDO ENHANCED TRADING BOT...
    call .venv\Scripts\activate
    python enhanced_trading_bot.py
    pause
) else if "%choice%"=="2" (
    cls
    echo INICIANDO ORCHESTRATOR BOT...
    call .venv\Scripts\activate
    python orchestrator\run.py
    pause
) else if "%choice%"=="3" (
    cls
    echo VERIFICANDO CUENTA MT5...
    call .venv\Scripts\activate
    python test_mt5_exness.py
    pause
) else if "%choice%"=="4" (
    exit
) else (
    echo Opcion invalida!
    pause
)
