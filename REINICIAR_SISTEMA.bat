@echo off
echo ========================================
echo    REINICIANDO ALGO TRADER V3
echo ========================================
echo.

echo Deteniendo procesos Python...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Iniciando sistema con nueva configuracion...
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"
.venv\Scripts\python.exe START_TRADING_SYSTEM.py

pause
