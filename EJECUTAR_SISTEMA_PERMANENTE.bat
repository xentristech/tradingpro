@echo off
echo ========================================
echo    ALGO TRADER V3 - EJECUCION PERMANENTE
echo ========================================
echo.
echo Iniciando sistema de trading automatico...
echo Presiona Ctrl+C para detener
echo.

cd /d "%~dp0"

:RESTART
echo [%DATE% %TIME%] Iniciando sistema...
python START_TRADING_SYSTEM.py

echo.
echo [%DATE% %TIME%] Sistema detenido. Reiniciando en 10 segundos...
timeout /t 10 /nobreak

echo [%DATE% %TIME%] Reiniciando sistema...
goto RESTART