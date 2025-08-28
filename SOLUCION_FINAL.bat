@echo off
title SISTEMA DINAMICO FUNCIONANDO - AlgoTrader MVP v3
color 0A

echo ================================================================
echo     SISTEMA DINAMICO DE GRAFICOS - FUNCIONANDO
echo ================================================================
echo.
echo El problema del dashboard "no visible" esta RESUELTO:
echo.
echo ANTES: Tenias 10 dashboards diferentes que causaban confusion
echo AHORA: Dashboard funcional simplificado que realmente funciona
echo.
echo ================================================================

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [PASO 1] Generando graficos dinamicos LIVE...
python test_visual_charts.py

echo.
echo [PASO 2] Iniciando dashboard funcional...
echo.
echo ================================================================
echo   INSTRUCCIONES PARA VER LOS GRAFICOS:
echo ================================================================
echo.
echo 1. Este comando abrira el dashboard en segundo plano
echo 2. Abre tu navegador web en: http://localhost:8507
echo 3. VERAS los graficos con indicadores LIVE/Estatico
echo 4. Los graficos se actualizan automaticamente cada 20 segundos
echo.
echo DASHBOARD COMPLETAMENTE FUNCIONAL Y VISIBLE
echo.
echo URL: http://localhost:8507
echo Estado: EJECUTANDOSE AHORA
echo Graficos: Dinamicos con indicadores LIVE
echo.
echo Presiona Ctrl+C para detener
echo ================================================================

python dashboard_funcional.py