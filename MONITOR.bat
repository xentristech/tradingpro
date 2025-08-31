@echo off
title Monitor de Sistema - Algo Trader V3
color 0A

echo ========================================
echo   MONITOR DE SISTEMA - ALGO TRADER V3
echo ========================================
echo.
echo Iniciando monitor en tiempo real...
echo.

:: Instalar dependencias si no están
pip install colorama psutil --quiet

:: Ejecutar monitor
python MONITOR_SISTEMA.py

pause
