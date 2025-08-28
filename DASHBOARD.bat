@echo off
title AlgoTrader Dashboard Launcher
color 0A

echo ===============================================================
echo              ALGOTRADER DASHBOARD v3.0
echo                 Panel de Control Web
echo ===============================================================
echo.
echo Iniciando dashboard web interactivo...
echo Se abrira automaticamente en tu navegador
echo Auto-refresh cada 30 segundos
echo.
echo Características:
echo    - Estado del sistema en tiempo real
echo    - Informacion de cuenta MT5
echo    - Posiciones abiertas y P^&L
echo    - Estado del bot de trading
echo    - Notificaciones Telegram
echo    - Estado de Ollama IA
echo    - Graficos de senales
echo    - Logs en tiempo real
echo.
echo URL: http://localhost:8501
echo Presiona Ctrl+C para detener
echo ===============================================================
echo.

python launch_dashboard.py

pause
