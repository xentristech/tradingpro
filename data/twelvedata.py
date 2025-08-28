# data/twelvedata.py
import os, requests, logging, re
from typing import Dict, Any, Optional

# ====== Carga automática del .env (si está disponible) ======
try:
    from dotenv import load_dotenv, find_dotenv
    # Intenta encontrar configs/.env; si no, prueba con ".env" en raíz
    _found = find_dotenv(filename="configs/.env", raise_error_if_not_found=False)
    if _found:
        load_dotenv(_found)
    else:
        load_dotenv(".env")
except Exception:
    # Si no hay python-dotenv o falla, seguimos con variables del entorno del proceso
    pass

BASE_URL = "https://api.twelvedata.com"

class TwelveDataError(Exception):
    pass

# ====== Símbolos ======
def _normalize_symbol(s: Optional[str]) -> str:
    """
    Normaliza un símbolo de bróker a formato para TwelveData.
    - Mantiene 'BTC/USD' o 'BTC:USD' (convierte ':' a '/').
    - Elimina sufijos típicos (m, .i, .pro, .x).
    - Deja 'BTCUSD', 'EURUSD', etc.
    """
    if not s:
        return ""
    s = s.strip().upper()
    if ":" in s:
        s = s.replace(":", "/")
    if "/" in s:
        return s

    # Quita sufijos comunes de bróker al final
    s = re.sub(r"(M|\.I|\.PRO|\.X)$", "", s)

    # Ya debería quedar algo tipo BTCUSD / EURUSD
    return s

def _td_symbol() -> str:
    """
    Obtiene símbolo objetivo para TwelveData:
    - TWELVEDATA_SYMBOL si está definido
    - Si no, SYMBOL del .env/sistema
    - En ambos casos, normalizado
    """
    s = os.getenv("TWELVEDATA_SYMBOL") or os.getenv("SYMBOL") or ""
    return _normalize_symbol(s)

def _symbol_candidates(s: str):
    """
    Devuelve variantes probables para TwelveData (cripto):
    - BTC/USD (preferida)
    - BTCUSD
    - BTC:USD
    """
    s = s.strip().upper()
    # si ya viene con / o : la ponemos primero
    cands = []
    if "/" in s or ":" in s:
        cands.append(s.replace(":", "/"))
    # si viene plano tipo BTCUSD
    if re.fullmatch(r"[A-Z]{6,}", s):
        base, quote = s[:-3], s[-3:]
        cands.append(f"{base}/{quote}")
        cands.append(s)
        cands.append(f"{base}:{quote}")
    else:
        # si vino BTC/USD o BTC:USD, ya lo agregamos arriba;
        # añade también versión sin separador por si acaso
        t = s.replace("/", "").replace(":", "")
        if re.fullmatch(r"[A-Z]{6,}", t):
            cands.append(t)
            base, quote = t[:-3], t[-3:]
            cands.append(f"{base}:{quote}")

    # de-dup conservando orden
    seen, out = set(), []
    for x in cands:
        x = x.replace(":", "/")  # normaliza a slash
        if x not in seen:
            seen.add(x); out.append(x)
    return out or [s]


# ====== HTTP ======
def _request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("TWELVEDATA_API_KEY", "")
    if not api_key:
        raise TwelveDataError("TWELVEDATA_API_KEY no está configurada en configs/.env")

    url = f"{BASE_URL}/{endpoint}"
    q = {**params, "apikey": api_key}

    r = requests.get(url, params=q, timeout=15)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        # Incluye los primeros 200 chars del cuerpo para facilitar diagnóstico
        body = ""
        try:
            body = r.text[:200]
        except Exception:
            pass
        raise TwelveDataError(f"HTTP {e.response.status_code}: {body}") from e

    data = r.json()
    # TwelveData reporta errores lógicos con 'status':'error' o 'message'
    if isinstance(data, dict) and (data.get("status") == "error" or "message" in data):
        # No sobre-interpretamos: devolvemos el mensaje tal cual
        raise TwelveDataError(f"TwelveData error: {data.get('message')}")
    return data

# ====== API ======
def time_series(symbol: Optional[str] = None, interval: str = "5min", outputsize: int = 100) -> Dict[str, Any]:
    """Obtiene serie OHLCV desde TwelveData (time_series). Devuelve dict con listas."""
    sym0 = _normalize_symbol(symbol) if symbol else _td_symbol()
    if not sym0:
        raise TwelveDataError("Símbolo vacío para TwelveData")

    exchange = os.getenv("TWELVEDATA_EXCHANGE", "").strip()
    last_error = None
    for sym in _symbol_candidates(sym0):
        params = {
            "symbol": sym,
            "interval": interval,
            "outputsize": int(outputsize),
            "dp": 8,
            "order": "desc",
        }
        if exchange:
            params["exchange"] = exchange
        try:
            data = _request("time_series", params)
            if not isinstance(data, dict) or "values" not in data:
                last_error = TwelveDataError(f"Respuesta inesperada time_series: {data}")
                continue
            values = list(reversed(data.get("values", [])))
            out = {k: [] for k in ["datetime", "open", "high", "low", "close", "volume"]}
            for row in values:
                try:
                    out["datetime"].append(row.get("datetime"))
                    out["open"].append(float(row.get("open", 0)))
                    out["high"].append(float(row.get("high", 0)))
                    out["low"].append(float(row.get("low", 0)))
                    out["close"].append(float(row.get("close", 0)))
                    out["volume"].append(float(row.get("volume", 0)))
                except Exception:
                    continue
            return out
        except Exception as e:
            last_error = e
            continue
    if last_error:
        raise last_error
    return {}

def price(symbol: Optional[str] = None, interval: Optional[str] = None, outputsize: Optional[int] = None):
    """Compatibilidad: si se pasa interval, retorna OHLCV; si no, precio spot."""
    if interval:
        return time_series(symbol, interval, outputsize or 100)
    sym0 = _normalize_symbol(symbol) if symbol else _td_symbol()
    if not sym0:
        raise TwelveDataError("Símbolo vacío para TwelveData")

    exchange = os.getenv("TWELVEDATA_EXCHANGE", "").strip()
    last_error = None
    for sym in _symbol_candidates(sym0):
        params = {"symbol": sym}
        if exchange:
            params["exchange"] = exchange
        try:
            data = _request("price", params)
            return float(data.get("price"))
        except Exception as e:
            last_error = e
            continue
    if last_error:
        raise last_error
    return None


def indicator(indicator_name: str, symbol: Optional[str] = None, interval: str = "5min", **kwargs) -> Dict[str, Any]:
    """Wrapper genérico de indicadores de TwelveData.
    - Devuelve diccionarios con listas cuando hay 'values'.
    - Soporta llamada: indicator('rsi', symbol=..., interval=...)
    """
    sym0 = _normalize_symbol(symbol) if symbol else _td_symbol()
    if not sym0:
        raise TwelveDataError("Símbolo vacío para TwelveData")

    exchange = os.getenv("TWELVEDATA_EXCHANGE", "").strip()
    last_error = None
    for sym in _symbol_candidates(sym0):
        params = {"symbol": sym, "interval": interval}
        if exchange:
            params["exchange"] = exchange
        params.update(kwargs)
        try:
            data = _request(indicator_name, params)

            # parseo estándar de TwelveData
            if isinstance(data, dict):
                if isinstance(data.get("values"), list) and data["values"]:
                    vals = list(reversed(data["values"]))
                    # devolver todas las series numéricas (excepto datetime)
                    keys = [k for k in vals[0].keys() if k != "datetime"]
                    out = {k: [] for k in keys}
                    for obj in vals:
                        for k in keys:
                            v = obj.get(k)
                            try:
                                out[k].append(float(v))
                            except Exception:
                                out[k].append(None)
                    return out
                else:
                    out = {}
                    for k, v in data.items():
                        try:
                            out[k] = float(v)
                        except Exception:
                            pass
                    if out:
                        return out
            # si no parseó, intenta siguiente candidato
            last_error = TwelveDataError(f"Respuesta inesperada del indicador {indicator_name}: {data}")
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    return {}


# ====== Prueba rápida al ejecutar directamente ======
if __name__ == "__main__":
    sym_in = os.getenv("SYMBOL", "BTCUSDm")
    print("SYMBOL (.env):", sym_in)
    print("TD symbol normalizado:", _normalize_symbol(sym_in), " / auto:", _td_symbol())
    print("price spot:", price(sym_in))
    try:
        ts = time_series(sym_in, "5min")
        print("series 5min close len:", len(ts.get("close", [])))
    except Exception as e:
        print("series error:", e)
    try:
        print("rsi 5min last:", indicator("rsi", symbol=sym_in, interval="5min", time_period=14).get("rsi", [])[-1:])
    except Exception as e:
        print("rsi error:", e)
    try:
        print("macd 5min last hist:", indicator("macd", symbol=sym_in, interval="5min", fast_period=12, slow_period=26, signal_period=9).get("macd_hist", [])[-1:])
    except Exception as e:
        print("macd error:", e)
