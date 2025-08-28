# data/candles.py
import time as _time
from typing import List, Dict, Literal
import MetaTrader5 as mt5

_TF_MAP = {
    "5min":  mt5.TIMEFRAME_M5,
    "15min": mt5.TIMEFRAME_M15,
    "1h":    mt5.TIMEFRAME_H1,
}

def fetch_bars(symbol: str, tf: Literal["5min","15min","1h"], count: int = 60) -> List[Dict]:
    """Devuelve las últimas 'count' velas del símbolo en tf como lista de dicts compactos."""
    timeframe = _TF_MAP[tf]
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        return []
    out = []
    for r in rates:
        # compactamos y redondeamos para no inflar tokens
        out.append({
            "t": int(r["time"]),
            "o": round(float(r["open"]), 2),
            "h": round(float(r["high"]), 2),
            "l": round(float(r["low"]), 2),
            "c": round(float(r["close"]), 2),
            "v": float(r["tick_volume"]),
        })
    return out
