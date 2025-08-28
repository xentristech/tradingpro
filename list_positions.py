import MetaTrader5 as mt5, os
from dotenv import load_dotenv
load_dotenv(os.path.join("configs",".env"))

path = os.getenv("MT5_PATH")
login = int(os.getenv("MT5_LOGIN","0") or 0)
password = os.getenv("MT5_PASSWORD","")
server = os.getenv("MT5_SERVER","")

ok = mt5.initialize(path, login=login, password=password, server=server, timeout=int(os.getenv("MT5_TIMEOUT","60000")))
print("mt5.init:", ok, mt5.last_error())
if ok:
    poss = mt5.positions_get()
    print("positions:", len(poss) if poss else 0)
    for p in poss or []:
        print(dict(ticket=p.ticket, symbol=p.symbol, type=p.type, volume=p.volume, price_open=p.price_open, sl=p.sl, tp=p.tp, profit=p.profit))
    mt5.shutdown()

