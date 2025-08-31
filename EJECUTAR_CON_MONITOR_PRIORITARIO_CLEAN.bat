@echo off
echo ========================================
echo    ALGO TRADER V3 - CON MONITOR PRIORITARIO CLEAN
echo ========================================
echo.
echo Sistema optimizado con monitor SL/TP prioritario SIN UNICODE
echo El monitor se ejecuta independiente de la IA
echo Presiona Ctrl+C para detener
echo.

cd /d "%~dp0"

:RESTART
echo [%DATE% %TIME%] Iniciando sistema con monitor prioritario CLEAN...
python START_TRADING_SYSTEM_MONITOR_PRIORITY_CLEAN.py

echo.
echo [%DATE% %TIME%] Sistema detenido. Reiniciando en 10 segundos...
timeout /t 10 /nobreak

echo [%DATE% %TIME%] Reiniciando sistema...
goto RESTART