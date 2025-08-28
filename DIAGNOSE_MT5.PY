import os, sys
from dotenv import load_dotenv
import MetaTrader5 as mt5

print("=== MT5 Diagnosis ===")

env = sys.argv[1] if len(sys.argv) > 1 else os.path.join("configs", ".env")
print("[i] Using env:", env)

if os.path.exists(env):
    load_dotenv(env)

print("MT5_PATH =", os.getenv("MT5_PATH"))
print("MT5_LOGIN =", os.getenv("MT5_LOGIN"))
print("MT5_SERVER =", os.getenv("MT5_SERVER"))
print("MT5_TIMEOUT =", os.getenv("MT5_TIMEOUT"))
print("SYMBOL =", os.getenv("SYMBOL"))
print("MT5_PASSWORD = ********")

ok = mt5.initialize(
    path=os.getenv("MT5_PATH"),
    login=int(os.getenv("MT5_LOGIN", "0")),
    password=os.getenv("MT5_PASSWORD"),
    server=os.getenv("MT5_SERVER"),
    timeout=int(os.getenv("MT5_TIMEOUT", "60000")),
)

print("initialize ->", ok, " last_error:", mt5.last_error())

if ok:
    ai = mt5.account_info()
    print("account_info:", ai)
    sym = os.getenv("SYMBOL", "BTCUSD")
    si = mt5.symbol_info(sym)
    print("symbol_info:", si)
    if si and not si.visible:
        mt5.symbol_select(sym, True)
        print("visible now:", mt5.symbol_info(sym).visible)
    if si:
        print("tick:", mt5.symbol_info_tick(sym))
    mt5.shutdown()
    print("Done.")
