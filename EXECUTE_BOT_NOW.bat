@echo off
color 0A
title TRADING BOT - LIVE EXECUTION [197678662]
cls

echo ============================================
echo    TRADING BOT - EJECUTANDO AHORA
echo    Cuenta: 197678662 (EXNESS)
echo    Fecha: %DATE% %TIME%
echo ============================================
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo Ejecutando bot...
echo Presione Ctrl+C para detener
echo.
echo ============================================
echo.

python quick_launcher.py

echo.
echo ============================================
echo Bot detenido en %TIME%
echo ============================================
pause