@echo off
color 0A
title ENHANCED TRADING BOT - LIVE [197678662]
echo ============================================
echo    ENHANCED TRADING BOT - EXNESS ACCOUNT
echo    Account: 197678662
echo    Starting at %TIME%
echo ============================================
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo Activating Python environment...
call .venv\Scripts\activate

echo.
echo Starting Enhanced Trading Bot...
echo Press Ctrl+C to stop
echo.
echo ============================================
echo.

python enhanced_trading_bot.py

if errorlevel 1 (
    echo.
    echo Bot stopped or error occurred
    echo Trying alternative start method...
    python orchestrator\run.py
)

echo.
echo ============================================
echo Bot stopped at %TIME%
echo ============================================
pause
