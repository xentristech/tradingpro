import os
from typing import List, Optional, Any
import MetaTrader5 as _mt5

_initialized = False

def init() -> bool:
    """
    Inicializa MT5 con variables de entorno:
    MT5_PATH, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, MT5_TIMEOUT
    """
    global _initialized
    if _initialized:
        return True
    path = os.getenv("MT5_PATH")
    login = os.getenv("MT5_LOGIN")
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER")
    timeout = int(os.getenv("MT5_TIMEOUT", "60000"))
    ok = _mt5.initialize(path=path,
                         login=int(login) if login else None,
                         password=password,
                         server=server,
                         timeout=timeout)
    _initialized = bool(ok)
    return _initialized

def shutdown():
    global _initialized
    try:
        _mt5.shutdown()
    finally:
        _initialized = False

def last_error() -> Any:
    try:
        return _mt5.last_error()
    except Exception:
        return None

def symbol_select(symbol: str, enable: bool = True) -> bool:
    try:
        return _mt5.symbol_select(symbol, enable)
    except Exception:
        return False

def positions(symbol: Optional[str] = None) -> List[Any]:
    """
    Retorna lista de posiciones abiertas. Si symbol se pasa, filtra por símbolo.
    """
    try:
        pos = _mt5.positions_get(symbol=symbol) if symbol else _mt5.positions_get()
        return list(pos or [])
    except Exception:
        return []

def move_to_breakeven(ticket: int, price_open: float) -> bool:
    """
    Mueve el SL al precio de entrada.
    """
    try:
        position = next((p for p in positions() if int(p.ticket) == int(ticket)), None)
        if not position:
            return False
        request = {
            "action": _mt5.TRADE_ACTION_SLTP,
            "position": int(ticket),
            "sl": float(price_open),
            "tp": float(position.tp or 0.0)
        }
        res = _mt5.order_send(request)
        return getattr(res, "retcode", 0) == _mt5.TRADE_RETCODE_DONE
    except Exception:
        return False

def close_position(ticket: int, volume: Optional[float] = None) -> bool:
    """
    Cierra una posición total o parcialmente. Si volume es None, usa el volumen completo.
    """
    try:
        position = next((p for p in positions() if int(p.ticket) == int(ticket)), None)
        if not position:
            return False

        sym = position.symbol
        symbol_info = _mt5.symbol_info(sym)
        if not symbol_info:
            return False

        if position.type == _mt5.ORDER_TYPE_BUY:
            order_type = _mt5.ORDER_TYPE_SELL
            price = _mt5.symbol_info_tick(sym).bid
        else:
            order_type = _mt5.ORDER_TYPE_BUY
            price = _mt5.symbol_info_tick(sym).ask

        vol = float(volume) if volume is not None else float(position.volume)
        vol = max(vol, float(symbol_info.volume_min or 0.01))

        request = {
            "action": _mt5.TRADE_ACTION_DEAL,
            "symbol": sym,
            "position": int(ticket),
            "type": order_type,
            "volume": vol,
            "price": float(price),
            "deviation": int(os.getenv("MT5_DEVIATION", "20")),
            "magic": int(os.getenv("MT5_MAGIC", "20250817")),
            "comment": "algo-bot close",
            "type_time": _mt5.ORDER_TIME_GTC,
            "type_filling": _mt5.ORDER_FILLING_FOK if symbol_info.trade_fill_mode == 0 else _mt5.ORDER_FILLING_FOK
        }
        res = _mt5.order_send(request)
        return getattr(res, "retcode", 0) in (_mt5.TRADE_RETCODE_DONE, _mt5.TRADE_RETCODE_PLACED)
    except Exception:
        return False
