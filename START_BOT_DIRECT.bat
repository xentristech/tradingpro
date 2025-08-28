@echo off
cls
color 0E
echo ============================================
echo    TRADING BOT - DIRECT EXECUTION
echo    Account: 197678662 (EXNESS)
echo ============================================
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak > nul

cd /d C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2

echo.
echo Activating Python environment...
call .venv\Scripts\activate

echo.
echo Running main orchestrator...
echo.

python -u orchestrator\run.py

echo.
echo ============================================
echo If you see this, the bot has stopped
echo ============================================
pause
