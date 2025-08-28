"""
Market Snapshot Generator
Genera una imagen del mercado actual con señal, SL/TP y niveles S/R.

Uso:
  python market_snapshot.py --symbol BTCUSDm --interval 15min --lookback 200 --config configs/.env
Salida:
  charts/market_snapshot.png y charts/market_snapshot.json
"""
import os
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from dotenv import load_dotenv
from data.twelvedata import time_series, indicator


def compute_atr(ts: Dict[str, list], period: int = 14) -> float:
    highs = np.array(ts.get('high', []), dtype=float)
    lows = np.array(ts.get('low', []), dtype=float)
    closes = np.array(ts.get('close', []), dtype=float)
    if len(closes) < period + 1:
        return float((highs[-1] - lows[-1]) if len(highs) and len(lows) else 0)
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    atr = np.mean(trs[-period:]) if len(trs) >= period else np.mean(trs)
    return float(atr)


def last_pivots(ts: Dict[str, list], window: int = 5) -> Tuple[float, float]:
    highs = ts.get('high', [])
    lows = ts.get('low', [])
    n = len(highs)
    res, sup = None, None
    for i in range(n-1-window, window, -1):
        if all(highs[i] > highs[i-k] for k in range(1, window+1)) and all(highs[i] > highs[i+k] for k in range(1, window+1)):
            res = highs[i]
            break
    for i in range(n-1-window, window, -1):
        if all(lows[i] < lows[i-k] for k in range(1, window+1)) and all(lows[i] < lows[i+k] for k in range(1, window+1)):
            sup = lows[i]
            break
    # fallback a últimos extremos
    if res is None:
        res = max(highs[-window:]) if highs else 0
    if sup is None:
        sup = min(lows[-window:]) if lows else 0
    return float(sup), float(res)


def decide_signal(close: float, rsi_last: float, macd_hist_last: float, cmf_last: float, mfi_last: float) -> str:
    # Heurística simple
    if macd_hist_last > 0 and rsi_last >= 55 and cmf_last > 0 and 35 <= mfi_last <= 70:
        return 'COMPRA'
    if macd_hist_last < 0 and rsi_last <= 45 and cmf_last < 0 and 30 <= mfi_last <= 65:
        return 'VENTA'
    return 'NO_OPERAR'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--symbol', default=os.getenv('SYMBOL', 'BTCUSDm'))
    ap.add_argument('--interval', default=os.getenv('SNAPSHOT_TF', '15min'))
    ap.add_argument('--lookback', type=int, default=200)
    ap.add_argument('--config', default='configs/.env')
    args = ap.parse_args()

    # Cargar env seleccionado
    if args.config:
        if Path(args.config).exists():
            load_dotenv(args.config)
        else:
            print(f"⚠️ Config no encontrada: {args.config}. Usando entorno del proceso.")

    # Obtener datos
    ts = time_series(args.symbol, args.interval, args.lookback)
    if not ts or not ts.get('close'):
        raise RuntimeError('No se pudo obtener serie OHLCV. Verifica TWELVEDATA_API_KEY y símbolo.')

    rsi = indicator('rsi', symbol=args.symbol, interval=args.interval, time_period=14).get('rsi', [])
    macd = indicator('macd', symbol=args.symbol, interval=args.interval, fast_period=12, slow_period=26, signal_period=9)
    cmf = indicator('cmf', symbol=args.symbol, interval=args.interval, time_period=20).get('cmf', [])
    mfi = indicator('mfi', symbol=args.symbol, interval=args.interval, time_period=14).get('mfi', [])

    close = ts['close'][-1]
    rsi_last = rsi[-1] if rsi else 50
    macd_hist = macd.get('macd_hist', [])
    macd_hist_last = macd_hist[-1] if macd_hist else 0
    cmf_last = cmf[-1] if cmf else 0
    mfi_last = mfi[-1] if mfi else 50

    atr = compute_atr(ts, 14)
    support, resistance = last_pivots(ts, window=5)

    signal = decide_signal(close, rsi_last, macd_hist_last, cmf_last, mfi_last)

    # SL/TP
    if signal == 'COMPRA':
        sl = max(support * 0.99, close - 1.5 * atr)
        tp = close + 2.5 * atr
    elif signal == 'VENTA':
        sl = min(resistance * 1.01, close + 1.5 * atr)
        tp = close - 2.5 * atr
    else:
        sl = 0.0
        tp = 0.0

    # Plot
    out_dir = Path('charts'); out_dir.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(12, 7))
    gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1])
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax)
    ax3 = fig.add_subplot(gs[2], sharex=ax)

    x = np.arange(len(ts['close']))
    ax.plot(x, ts['close'], label='Close', color='#1f77b4')
    ax.fill_between(x, ts['low'], ts['high'], color='#1f77b4', alpha=0.08, label='Range')
    ax.axhline(support, color='green', linestyle='--', alpha=0.6, label='Soporte')
    ax.axhline(resistance, color='red', linestyle='--', alpha=0.6, label='Resistencia')
    if signal != 'NO_OPERAR':
        ax.axhline(sl, color='orange', linestyle='-', alpha=0.7, label='Stop Loss')
        ax.axhline(tp, color='purple', linestyle='-', alpha=0.7, label='Take Profit')
        ax.scatter(len(x)-1, close, color='gold', s=60, zorder=5)
        ax.annotate(f"{signal}\nEntry: {close:.2f}", xy=(len(x)-1, close), xytext=(-60, 20), textcoords='offset points',
                    bbox=dict(boxstyle='round', fc='w', ec='#888'), arrowprops=dict(arrowstyle='->'))
    ax.set_title(f"{args.symbol} {args.interval} | Close/Range + S/R + SL/TP")
    ax.legend(loc='upper left')

    # Volumen
    ax2.bar(x, ts['volume'], color='#8888ff', alpha=0.6)
    ax2.set_ylabel('Vol')

    # RSI / CMF
    ax3.plot(x[-len(rsi):], rsi, label='RSI', color='#2ca02c') if rsi else None
    ax3.plot(x[-len(cmf):], cmf, label='CMF', color='#d62728') if cmf else None
    ax3.axhline(50, color='#999', linestyle=':')
    ax3.set_ylim(-1, 100)
    ax3.legend(loc='upper left')

    fig.tight_layout()
    out_path = out_dir / 'market_snapshot.png'
    fig.savefig(out_path, dpi=140)
    plt.close(fig)

    # Resumen
    summary = {
        'symbol': args.symbol,
        'interval': args.interval,
        'entry': close,
        'signal': signal,
        'stop_loss': sl,
        'take_profit': tp,
        'support': support,
        'resistance': resistance,
        'atr': atr,
        'rsi': rsi_last,
        'cmf': cmf_last,
        'mfi': mfi_last,
        'macd_hist': macd_hist_last,
        'image_path': str(out_path)
    }
    import json
    with open(out_dir / 'market_snapshot.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print("Imagen guardada en:", out_path)
    print("Resumen:")
    for k, v in summary.items():
        if k != 'image_path':
            print(f"  {k}: {v}")


if __name__ == '__main__':
    main()

