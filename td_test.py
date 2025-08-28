import os
from dotenv import load_dotenv
load_dotenv(os.path.join("configs",".env"))

from data.twelvedata import indicator, price
sym = os.getenv("TWELVEDATA_SYMBOL") or os.getenv("SYMBOL","BTCUSDm")

print("price:", price(sym))
print("rsi 5min:", indicator(sym, "rsi", "5min", time_period=14))
print("macd 5min:", indicator(sym, "macd", "5min", fast_period=12, slow_period=26, signal_period=9))
