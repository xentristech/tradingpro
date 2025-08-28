# data/mini_indicators.py
from typing import List

def rsi_last(closes: List[float], period: int = 14) -> float | None:
    if len(closes) < period + 1: return None
    gains = sum(max(closes[i]-closes[i-1], 0.0) for i in range(-period, 0))
    losses = sum(max(closes[i-1]-closes[i], 0.0) for i in range(-period, 0))
    if losses == 0: return 100.0
    rs = (gains/period) / (losses/period)
    return 100.0 - (100.0/(1.0+rs))

def macd_hist_last(closes: List[float], fast=12, slow=26, signal=9) -> float | None:
    if len(closes) < slow + signal + 5: return None
    def ema(vals: List[float], n: int) -> List[float]:
        k = 2/(n+1)
        out = []
        e = sum(vals[:n])/n
        out.append(e)
        for v in vals[n:]:
            e = v*k + e*(1-k)
            out.append(e)
        return out
    ef = ema(closes, fast); es = ema(closes, slow)
    m = [ef[-len(es)+i]-es[i] for i in range(len(es))]
    s = ema(m, signal)
    L = min(len(m), len(s))
    h = [m[-L+i]-s[-L+i] for i in range(L)]
    return h[-1] if h else None

def rel_volume_last(vols: List[float], lookback: int = 20) -> float | None:
    if len(vols) < lookback + 1: return None
    avg = sum(vols[-(lookback+1):-1]) / lookback
    if avg <= 0: return None
    return vols[-1] / avg
