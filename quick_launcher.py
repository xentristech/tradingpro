#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick Bot Launcher - Simple execution without encoding issues
"""
import os
import sys
import time
from dotenv import load_dotenv

# Change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add to Python path
sys.path.insert(0, script_dir)

print("="*50)
print("   QUICK BOT LAUNCHER")
print("   Account: 197678662 (EXNESS)")
print("="*50)

# Load environment
load_dotenv('configs/.env')

try:
    import MetaTrader5 as mt5
    print("[OK] MetaTrader5 imported successfully")
    
    # Test MT5 connection
    path = os.getenv("MT5_PATH")
    login = int(os.getenv("MT5_LOGIN"))
    password = os.getenv("MT5_PASSWORD") 
    server = os.getenv("MT5_SERVER")
    
    print(f"[INFO] Connecting to MT5...")
    print(f"[INFO] Login: {login}")
    print(f"[INFO] Server: {server}")
    
    # Initialize MT5
    if not mt5.initialize(path=path, login=login, password=password, server=server):
        print(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")
        print("Press Enter to exit...")
        input()
        sys.exit(1)
    
    print("[OK] MT5 connected successfully")
    
    # Get account info
    account_info = mt5.account_info()
    if account_info:
        print(f"[INFO] Balance: ${account_info.balance}")
        print(f"[INFO] Equity: ${account_info.equity}")
        print(f"[INFO] Login: {account_info.login}")
    
    # Test symbol
    symbol = os.getenv("SYMBOL", "BTCUSDm")
    print(f"[INFO] Testing symbol: {symbol}")
    
    if mt5.symbol_select(symbol, True):
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            print(f"[OK] Symbol {symbol} available")
            print(f"[INFO] Spread: {symbol_info.spread}")
        else:
            print(f"[WARNING] Symbol info not available for {symbol}")
    else:
        print(f"[ERROR] Failed to select symbol {symbol}")
    
    print("\n" + "="*50)
    print("   STARTING TRADING BOT...")
    print("   Press Ctrl+C to stop")
    print("="*50)
    
    # Simple trading loop
    count = 0
    while True:
        try:
            count += 1
            print(f"[{count:04d}] Bot running... {time.strftime('%H:%M:%S')}")
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                print(f"[PRICE] {symbol}: Bid={tick.bid}, Ask={tick.ask}")
            
            # Check positions
            positions = mt5.positions_get(symbol=symbol)
            print(f"[POSITIONS] Open: {len(positions) if positions else 0}")
            
            # Wait 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n[STOP] Bot stopped by user")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(10)
    
    # Cleanup
    mt5.shutdown()
    print("[OK] MT5 connection closed")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Please install MetaTrader5: pip install MetaTrader5")
except Exception as e:
    print(f"[ERROR] {e}")
    
finally:
    print("\nPress Enter to exit...")
    try:
        input()
    except:
        pass