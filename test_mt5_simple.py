import MetaTrader5 as mt5
print("Testing MT5...")
result = mt5.initialize()
print("Initialize result:", result)
print("Last error:", mt5.last_error())
mt5.shutdown()
