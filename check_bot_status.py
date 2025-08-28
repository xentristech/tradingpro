"""
CHECK BOT STATUS
Quick check if bot is running
"""
import os
import psutil
import MetaTrader5 as mt5
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('configs/.env')

print("\n" + "="*60)
print("  BOT STATUS CHECK")
print("="*60)

# Check for Python processes
print("\n1. Checking for running Python processes...")
python_running = False
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'python' in proc.info['name'].lower():
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'enhanced_trading_bot' in cmdline or 'orchestrator' in cmdline or 'run.py' in cmdline:
                print(f"   ✅ Bot process found! PID: {proc.info['pid']}")
                python_running = True
                break
    except:
        pass

if not python_running:
    print("   ⚠️  No bot process detected")

# Check MT5 connection
print("\n2. Checking MT5 account...")
try:
    if mt5.initialize(
        login=int(os.getenv('MT5_LOGIN')),
        password=os.getenv('MT5_PASSWORD'),
        server=os.getenv('MT5_SERVER')
    ):
        account = mt5.account_info()
        if account:
            print(f"   ✅ MT5 Connected")
            print(f"   Account: {account.login}")
            print(f"   Balance: ${account.balance:.2f}")
            print(f"   Equity: ${account.equity:.2f}")
            
            # Check for open positions
            positions = mt5.positions_get()
            if positions:
                print(f"\n3. Open Positions: {len(positions)}")
                for pos in positions:
                    print(f"   #{pos.ticket}: {pos.symbol} {'BUY' if pos.type == 0 else 'SELL'} {pos.volume} lots")
                    print(f"   P&L: ${pos.profit:.2f}")
            else:
                print("\n3. No open positions")
                
        mt5.shutdown()
except Exception as e:
    print(f"   ❌ MT5 Error: {e}")

# Check logs
print("\n4. Checking recent logs...")
log_files = ['logs/enhanced_bot.log', 'logs/run_2024.out.log', 'logs/auto_execute.log']
found_log = False

for log_file in log_files:
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_lines = lines[-5:]  # Last 5 lines
                    print(f"   Found {log_file}:")
                    for line in last_lines:
                        print(f"     {line.strip()[:80]}")
                    found_log = True
                    break
        except:
            pass

if not found_log:
    print("   No recent log activity")

# Summary
print("\n" + "="*60)
print("  SUMMARY")
print("="*60)

if python_running:
    print("✅ Bot appears to be RUNNING")
    print("\nCheck the CMD window titled:")
    print('   "ENHANCED TRADING BOT - LIVE [197678662]"')
else:
    print("⚠️  Bot may not be running")
    print("\nTo start the bot:")
    print("   1. Double-click RUN_BOT.bat")
    print("   2. Or run: python enhanced_trading_bot.py")

print(f"\nTime: {datetime.now().strftime('%H:%M:%S')}")
print("="*60)
