@echo off
title AlgoTrader Simple Dashboard
color 0A

echo ===============================================================
echo              ALGOTRADER SIMPLE DASHBOARD v3.0
echo                 Panel de Control HTML
echo ===============================================================
echo.
echo Iniciando dashboard web HTML simple...
echo.
echo Caracteristicas:
echo    - Estado del sistema en tiempo real
echo    - Informacion de cuenta MT5  
echo    - Posiciones abiertas y P^&L
echo    - Estado del bot de trading
echo    - Senales recientes
echo    - Auto-refresh cada 30 segundos
echo    - Sin dependencias complejas
echo.
echo URL: http://localhost:8502
echo Se abrira automaticamente en tu navegador
echo Presiona Ctrl+C para detener
echo ===============================================================
echo.

python simple_dashboard.py

pause