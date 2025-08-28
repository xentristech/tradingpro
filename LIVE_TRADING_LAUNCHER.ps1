# Enhanced Trading Bot - Live Trading Launcher for Exness
# Account: 197678662

Write-Host "`n" -NoNewline
Write-Host "================================================================" -ForegroundColor Red
Write-Host "     LIVE TRADING LAUNCHER - REAL MONEY AT RISK!              " -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Red
Write-Host ""

# Activate virtual environment
Write-Host "Activating Python environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Display account information
Write-Host "`n📊 ACCOUNT INFORMATION:" -ForegroundColor Yellow
Write-Host "   Account Number: 197678662" -ForegroundColor White
Write-Host "   Broker: Exness" -ForegroundColor White
Write-Host "   Server: Exness-MT5Trial11" -ForegroundColor White
Write-Host "   Symbol: BTCUSDm" -ForegroundColor White
Write-Host "   Risk per Trade: 1%" -ForegroundColor White
Write-Host "   Stop Loss: $50 USD" -ForegroundColor White
Write-Host "   Take Profit: $100 USD" -ForegroundColor White

# Safety check
Write-Host "`n⚠️  SAFETY FEATURES:" -ForegroundColor Yellow
Write-Host "   ✓ Maximum 1 concurrent trade" -ForegroundColor Green
Write-Host "   ✓ 1% risk per trade limit" -ForegroundColor Green
Write-Host "   ✓ Telegram notifications active" -ForegroundColor Green
Write-Host "   ✓ Emergency stop loss enabled" -ForegroundColor Green

# Menu
Write-Host "`n📋 SELECT OPERATION:" -ForegroundColor Cyan
Write-Host "   1. Verify All Systems (Recommended)" -ForegroundColor White
Write-Host "   2. Start LIVE Trading (Real Money)" -ForegroundColor Red
Write-Host "   3. Start DEMO Trading (Safe)" -ForegroundColor Green
Write-Host "   4. Run Backtest" -ForegroundColor White
Write-Host "   5. Check Account Balance" -ForegroundColor White
Write-Host "   6. Emergency STOP All Trades" -ForegroundColor Red
Write-Host "   0. Exit" -ForegroundColor White

$choice = Read-Host "`nEnter your choice (0-6)"

switch ($choice) {
    1 {
        Write-Host "`n🔍 Running System Verification..." -ForegroundColor Yellow
        python test_mt5_exness.py
        
        Write-Host "`n📱 Testing Telegram..." -ForegroundColor Yellow
        python -c "
import requests, os
from dotenv import load_dotenv
load_dotenv('configs/.env')
token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {'chat_id': chat_id, 'text': '✅ Bot verification successful!'}
r = requests.post(url, data=data)
if r.status_code == 200:
    print('✅ Telegram working!')
else:
    print('❌ Telegram failed!')
"
        
        Write-Host "`n📊 Testing TwelveData..." -ForegroundColor Yellow
        python -c "
import requests, os
from dotenv import load_dotenv
load_dotenv('configs/.env')
api_key = os.getenv('TWELVEDATA_API_KEY')
url = f'https://api.twelvedata.com/price?symbol=BTC/USD&apikey={api_key}'
r = requests.get(url)
if r.status_code == 200:
    data = r.json()
    if 'price' in data:
        print(f'✅ BTC/USD Price: ${float(data[\"price\"]):,.2f}')
else:
    print('❌ TwelveData failed!')
"
    }
    2 {
        Write-Host "`n" -NoNewline
        Write-Host "════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host "         ⚠️  LIVE TRADING WARNING ⚠️           " -ForegroundColor Yellow
        Write-Host "════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host ""
        Write-Host "You are about to start trading with REAL MONEY!" -ForegroundColor Red
        Write-Host "• You can lose all your capital" -ForegroundColor Yellow
        Write-Host "• Monitor the bot constantly" -ForegroundColor Yellow
        Write-Host "• Have an emergency plan ready" -ForegroundColor Yellow
        Write-Host ""
        
        $confirm = Read-Host "Type 'START LIVE' to confirm (or anything else to cancel)"
        
        if ($confirm -eq "START LIVE") {
            Write-Host "`n🚀 Starting LIVE Trading Bot..." -ForegroundColor Red
            Write-Host "Press Ctrl+C to stop at any time" -ForegroundColor Yellow
            
            # Send Telegram notification
            python -c "
import requests, os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv('configs/.env')
token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
url = f'https://api.telegram.org/bot{token}/sendMessage'
msg = f'🔴 LIVE TRADING STARTED\n\nAccount: 197678662\nTime: {datetime.now()}\n\n⚠️ Real money at risk!'
data = {'chat_id': chat_id, 'text': msg}
requests.post(url, data=data)
"
            
            # Start the bot
            python enhanced_trading_bot.py
        } else {
            Write-Host "`nLive trading cancelled." -ForegroundColor Green
        }
    }
    3 {
        Write-Host "`n🟢 Switching to DEMO mode..." -ForegroundColor Green
        
        # Switch to demo in config
        python -c "
content = open('configs/.env', 'r').read()
content = content.replace('LIVE_TRADING=true', 'LIVE_TRADING=false')
open('configs/.env', 'w').write(content)
print('✅ Switched to DEMO mode')
"
        
        Write-Host "Starting bot in DEMO mode (safe)..." -ForegroundColor Green
        python enhanced_trading_bot.py
    }
    4 {
        Write-Host "`n📊 Running Backtest..." -ForegroundColor Cyan
        python -c "from enhanced_trading_bot import EnhancedTradingBot; bot = EnhancedTradingBot(); bot.run_backtest()"
    }
    5 {
        Write-Host "`n💰 Checking Account Balance..." -ForegroundColor Cyan
        python -c "
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
load_dotenv('configs/.env')

path = os.getenv('MT5_PATH')
login = int(os.getenv('MT5_LOGIN'))
password = os.getenv('MT5_PASSWORD')
server = os.getenv('MT5_SERVER')

if mt5.initialize(path=path, login=login, password=password, server=server):
    account = mt5.account_info()
    if account:
        print(f'Account: {account.login}')
        print(f'Balance: ${account.balance:.2f}')
        print(f'Equity: ${account.equity:.2f}')
        print(f'Margin Free: ${account.margin_free:.2f}')
        print(f'Profit: ${account.profit:.2f}')
    mt5.shutdown()
"
    }
    6 {
        Write-Host "`n🛑 EMERGENCY STOP - Closing all positions..." -ForegroundColor Red
        python -c "
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
load_dotenv('configs/.env')

if mt5.initialize():
    positions = mt5.positions_get()
    if positions:
        for pos in positions:
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'position': pos.ticket,
                'symbol': pos.symbol,
                'volume': pos.volume,
                'type': mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                'price': mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask,
                'magic': 20250817,
                'comment': 'Emergency close'
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f'✅ Closed position {pos.ticket}')
            else:
                print(f'❌ Failed to close {pos.ticket}: {result.comment}')
    else:
        print('No open positions')
    mt5.shutdown()
"
        Write-Host "Emergency stop completed." -ForegroundColor Yellow
    }
    0 {
        Write-Host "`nExiting..." -ForegroundColor Cyan
        exit
    }
    default {
        Write-Host "`nInvalid choice!" -ForegroundColor Red
    }
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
