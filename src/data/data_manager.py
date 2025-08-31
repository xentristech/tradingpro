"""
Data Manager - Obtención y preparación de datos de mercado

Responsabilidad:
- Obtener series OHLCV desde TwelveData (si hay API key)
- Fallback a datos sintéticos en modo demo o sin red
- Calcular indicadores básicos requeridos por el SignalGenerator
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import os

import pandas as pd
import numpy as np


@dataclass
class DataManagerConfig:
    symbol: str
    twelvedata_symbol: str
    api_key: Optional[str]
    exchange: Optional[str]


class DataManager:
    """Proveedor de datos con indicadores para múltiples timeframes."""

    def __init__(self, config: Dict):
        self.cfg = DataManagerConfig(
            symbol=config.get("symbol", "BTCUSDm"),
            twelvedata_symbol=config.get("twelvedata_symbol", "BTC/USD"),
            api_key=os.getenv("TWELVEDATA_API_KEY"),
            exchange=os.getenv("TWELVEDATA_EXCHANGE"),
        )

    async def get_data(self, symbol: str, interval: str, outputsize: int = 100):
        """
        Retorna DataFrame OHLCV con indicadores para el `interval` solicitado.
        Prioriza TwelveData; usa datos sintéticos si falla o no hay API key.
        """
        df = None
        if self.cfg.api_key:
            try:
                df = self._fetch_twelvedata(symbol=symbol, interval=interval, outputsize=outputsize)
            except Exception:
                df = None

        if df is None or df.empty:
            df = self._generate_synthetic(symbol=symbol, interval=interval, length=outputsize)

        try:
            df = self._ensure_indicators(df)
        except Exception:
            pass

        return df

    def _fetch_twelvedata(self, symbol: str, interval: str, outputsize: int) -> pd.DataFrame:
        import requests

        base = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": str(outputsize),
            "apikey": self.cfg.api_key,
        }
        if self.cfg.exchange:
            params["exchange"] = self.cfg.exchange

        resp = requests.get(base, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        values = data.get("values") or data.get("data")
        if not values:
            return pd.DataFrame()

        df = pd.DataFrame(values)
        df = df.rename(columns={
            "datetime": "datetime",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })

        for c in ["open", "high", "low", "close", "volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            df = df.dropna(subset=["datetime"]).sort_values("datetime")
            df = df.set_index("datetime")

        return df

    def _generate_synthetic(self, symbol: str, interval: str, length: int) -> pd.DataFrame:
        freq_map = {
            "1min": "1min",
            "5min": "5min",
            "15min": "15min",
            "30min": "30min",
            "1h": "1H",
            "4h": "4H",
            "1day": "1D",
            "1D": "1D",
        }
        freq = freq_map.get(interval, "1H")

        idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=max(length, 60), freq=freq)
        rng = np.random.default_rng()
        steps = rng.normal(0, 50, len(idx)).cumsum()
        base = 50000.0
        close = np.maximum(base + steps, 1)
        open_ = close + rng.normal(0, 20, len(idx))
        high = np.maximum.reduce([open_, close]) + np.abs(rng.normal(0, 30, len(idx)))
        low = np.minimum.reduce([open_, close]) - np.abs(rng.normal(0, 30, len(idx)))
        volume = np.abs(rng.normal(5000, 1500, len(idx)))

        df = pd.DataFrame({
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }, index=idx)
        return df

    def _ensure_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df

        df["sma_20"] = df["close"].rolling(20, min_periods=1).mean()
        df["sma_50"] = df["close"].rolling(50, min_periods=1).mean()

        df["rsi"] = self._rsi(df["close"], period=14)

        mid = df["close"].rolling(20, min_periods=1).mean()
        std = df["close"].rolling(20, min_periods=1).std(ddof=0)
        df["bb_middle"], df["bb_upper"], df["bb_lower"] = mid, mid + 2 * std, mid - 2 * std

        df["atr"] = self._atr(df, period=14)

        ema12 = self._ema(df["close"], span=12)
        ema26 = self._ema(df["close"], span=26)
        macd = ema12 - ema26
        macd_signal = self._ema(macd, span=9)
        df["macd"] = macd
        df["macd_signal"] = macd_signal
        df["macd_histogram"] = macd - macd_signal

        df["volume_sma"] = df["volume"].rolling(20, min_periods=1).mean()
        return df

    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(period, min_periods=1).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    @staticmethod
    def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        return tr.rolling(period, min_periods=1).mean()

