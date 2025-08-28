@echo off
title SISTEMA DINAMICO DE GRAFICOS - AlgoTrader MVP v3
color 0A

echo ================================================================
echo     SISTEMA DINAMICO DE GRAFICOS - AlgoTrader MVP v3
echo ================================================================
echo.
echo [INICIANDO] Sistema de graficos dinamicos en tiempo real...
echo.
echo Caracteristicas:
echo   - Graficos LIVE que se actualizan cada 30 segundos
echo   - Dashboard web que se refresca cada 15 segundos  
echo   - Tipos: Candlestick, Line, OHLC, Bar Analysis
echo   - Simbolos: BTC/USD, XAU/USD, EUR/USD
echo   - Integracion con TwelveData API
echo.
echo ================================================================

REM Ir al directorio correcto
cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

REM Generar graficos de ejemplo primero
echo [PASO 1] Generando graficos de ejemplo...
python test_visual_charts.py
if errorlevel 1 (
    echo [ERROR] Error generando graficos de ejemplo
    pause
    exit /b 1
)

echo.
echo [PASO 2] Iniciando Charts Dashboard en puerto 8507...
echo.

REM Mostrar instrucciones
echo ================================================================
echo   INSTRUCCIONES DE USO:
echo ================================================================
echo.
echo 1. El dashboard se abrira automaticamente en segundo plano
echo 2. Abre tu navegador web en: http://localhost:8507
echo 3. Veras los graficos LIVE con indicadores dinamicos
echo 4. Los graficos se actualizan automaticamente cada 30 segundos
echo 5. El dashboard se refresca cada 15 segundos
echo.
echo IMPORTANTE: No cierres esta ventana - mantiene el sistema activo
echo.
echo ================================================================
echo   SISTEMA COMPLETAMENTE ACTIVO
echo ================================================================
echo.
echo URL Dashboard: http://localhost:8507
echo Estado: EJECUTANDOSE
echo Actualizaciones: Cada 15-30 segundos
echo.
echo Presiona Ctrl+C para detener el sistema
echo ================================================================

REM Ejecutar dashboard (esto mantiene la ventana abierta)
python charts_dashboard.py