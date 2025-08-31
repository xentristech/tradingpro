@echo off
cls
title ALGO TRADER V3 - EJECUTANDO TODO
color 0A

echo ================================================================
echo                    ALGO TRADER V3
echo              EJECUTANDO SISTEMA COMPLETO
echo ================================================================
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1/4] Iniciando Sistema de Ticks...
start "Tick System" cmd /k python src\data\TICK_SYSTEM_FINAL.py
timeout /t 3 >nul

echo [2/4] Iniciando Revolutionary Dashboard...
start "Dashboard" cmd /k python src\ui\dashboards\revolutionary_dashboard_final.py
timeout /t 3 >nul

echo [3/4] Iniciando Chart Simulation...
start "Charts" cmd /k python src\ui\charts\chart_simulation_reviewed.py
timeout /t 3 >nul

echo [4/4] Iniciando TradingView Professional...
start "TradingView" cmd /k python src\ui\charts\tradingview_professional_chart.py
timeout /t 3 >nul

echo.
echo ================================================================
echo                  ABRIENDO NAVEGADORES
echo ================================================================
echo.

timeout /t 5 >nul

start http://localhost:8512
timeout /t 1 >nul
start http://localhost:8516
timeout /t 1 >nul
start http://localhost:8517

echo.
echo ================================================================
echo              SISTEMA INICIADO EXITOSAMENTE
echo ================================================================
echo.
echo Dashboards disponibles:
echo.
echo   [1] Revolutionary Dashboard: http://localhost:8512
echo   [2] Chart Simulation:       http://localhost:8516
echo   [3] TradingView Pro:        http://localhost:8517
echo.
echo ================================================================
echo.
pause