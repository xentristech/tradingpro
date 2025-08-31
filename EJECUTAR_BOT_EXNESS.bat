@echo off
cls
echo ================================================
echo    EJECUTANDO BOT TRADING - CUENTA EXNESS
echo ================================================
echo.
echo Usuario: 197678662
echo Server: Exness-MT5Trial11
echo.
echo Iniciando bot...
echo.

cd /d "%~dp0"
.venv\Scripts\python.exe bot_exness.py

pause
