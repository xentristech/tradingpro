@echo off
echo ===============================================
echo   ENHANCED TRADING BOT - LIVE TRADING
echo   EXNESS ACCOUNT: 197678662
echo ===============================================
echo.
echo WARNING: LIVE TRADING WITH REAL MONEY!
echo.
echo Starting Python environment...
call .venv\Scripts\activate

echo.
echo Configuration:
echo - Account: 197678662 (Exness)
echo - Symbol: BTCUSDm
echo - Risk per trade: 1%%
echo - Stop Loss: $50
echo - Take Profit: $100
echo.

echo Testing connections...
python -c "from dotenv import load_dotenv; import os; load_dotenv('configs/.env'); print('Config loaded. Live trading:', os.getenv('LIVE_TRADING'))"

echo.
echo Choose an option:
echo 1. Run VERIFICATION (Recommended first)
echo 2. Start LIVE TRADING (Real money)
echo 3. Test connections only
echo 4. Switch to DEMO mode
echo 5. Exit
echo.

set /p choice=Enter your choice (1-5): 

if "%choice%"=="1" (
    echo.
    echo Running verification...
    python live_trading_verification.py
) else if "%choice%"=="2" (
    echo.
    echo WARNING: Starting LIVE TRADING!
    echo Press Ctrl+C to stop at any time
    timeout /t 5
    python enhanced_trading_bot.py
) else if "%choice%"=="3" (
    echo.
    echo Testing connections...
    python test_mt5_exness.py
) else if "%choice%"=="4" (
    echo.
    echo Switching to DEMO mode...
    python -c "content = open('configs/.env').read(); open('configs/.env', 'w').write(content.replace('LIVE_TRADING=true', 'LIVE_TRADING=false')); print('Switched to DEMO mode')"
) else if "%choice%"=="5" (
    echo.
    echo Exiting...
    exit
) else (
    echo Invalid choice!
)

echo.
pause
