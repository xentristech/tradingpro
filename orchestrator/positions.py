# orchestrator/positions.py
import os
import time
import math
import traceback
from typing import Dict, Optional, List

from dotenv import load_dotenv

from notifiers.telegram import send_message
from utils.time import now_tz
from data.candles import fetch_bars
from data.mini_indicators import rel_volume_last
from signals.llm_validator import reevaluate_position


# ================= Utilidades =================

def _safe_float(v, default=math.nan) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _side_from_mt5(type_int: int) -> str:
    # MT5 position type: 0=BUY, 1=SELL
    return "LONG" if type_int == 0 else "SHORT"


def _pretty_msg(symbol: str, ticket: int, accion: str, conf: float, razon: str, profit: float) -> str:
    ts = now_tz().strftime("%Y-%m-%d %H:%M:%S")
    razon = (razon or "").strip()
    if not razon:
        razon = "—"
    return (
        f"*{symbol}* {ts}\n"
        f"Acción: {accion.upper()} (conf={conf:.2f}) | Ticket: {ticket}\n"
        f"Profit: {profit:.2f}\n"
        f"Razón: {razon}"
    )


def _calc_rvol(symbol: str, tf: str = "5min", lookback: int = 20) -> Optional[float]:
    """
    RVOL = vol_actual / promedio(vol N últimas)
    """
    try:
        bars = fetch_bars(symbol, tf, count=max(lookback + 5, 30)) or []
        vols = [b.get("v", 0.0) for b in bars if b and "v" in b]
        if len(vols) >= lookback:
            return float(rel_volume_last(vols, lookback=lookback))
    except Exception:
        pass
    return None


# =============== MT5 helpers (solo si LIVE_TRADING=true) ===============

_mt5_ready = False

def _mt5_init_if_needed():
    global _mt5_ready
    if _mt5_ready:
        return
    # Tu wrapper ya maneja lectura de credenciales del .env
    from broker import mt5
    mt5.init()
    _mt5_ready = True


def _mt5_positions_get(symbol: str):
    """
    Pide posiciones por símbolo. Si el bróker ignora el filtro,
    hacemos una pasada adicional para quedarnos SOLO con el símbolo.
    """
    import MetaTrader5 as mt5
    try:
        rows = mt5.positions_get(symbol=symbol) or []
        # Filtro defensivo por si el bróker devuelve todo:
        return [p for p in rows if getattr(p, "symbol", "") == symbol]
    except Exception:
        return []


def _mt5_modify_sl_tp(ticket: int, sl: float, tp: float) -> bool:
    try:
        from broker.mt5 import modify_sl_tp  # si tienes wrapper
        return bool(modify_sl_tp(ticket, sl, tp))
    except Exception:
        # Fallback directo a MT5
        try:
            import MetaTrader5 as mt5
            pos = next((p for p in mt5.positions_get() or [] if p.ticket == ticket), None)
            if not pos:
                return False
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": sl if sl > 0 else 0.0,
                "tp": tp if tp > 0 else 0.0,
            }
            res = mt5.order_send(request)
            return res is not None and res.retcode == mt5.TRADE_RETCODE_DONE
        except Exception:
            return False


def _mt5_close_partial(ticket: int, volume: float) -> bool:
    try:
        from broker.mt5 import close_partial
        return bool(close_partial(ticket, volume))
    except Exception:
        return False  # Fallback omitido


def _mt5_close_full(ticket: int) -> bool:
    try:
        from broker.mt5 import close_full
        return bool(close_full(ticket))
    except Exception:
        return False  # Fallback omitido


# =================== Main loop ===================

def main():
    # Entorno
    load_dotenv(os.path.join("configs", ".env"))

    symbol = os.getenv("SYMBOL", "BTCUSDm")
    loop_seconds = int(os.getenv("POSITIONS_LOOP_SECONDS", os.getenv("LOOP_SECONDS", "20")))
    live_trading = os.getenv("LIVE_TRADING", "false").lower() in ("1", "true", "yes")

    if live_trading:
        try:
            _mt5_init_if_needed()
            print("[positions] MT5 init OK")
        except Exception as e:
            print("[positions] MT5 init failed:", e)

    print(f"[positions] Running for SYMBOL={symbol} | every {loop_seconds}s | live_trading={live_trading}")

    while True:
        try:
            # 1) Obtener posiciones abiertas del símbolo
            positions = _mt5_positions_get(symbol) if live_trading else []

            if not positions:
                # No hay posiciones → dormir y seguir
                time.sleep(loop_seconds)
                continue

            # 2) Calcular RVOL una sola vez por loop
            rvol_val = _calc_rvol(symbol, "5min", 20)
            rvol = _safe_float(rvol_val, 1.0)

            # 3) Reevaluar cada posición
            for p in positions:
                ticket = int(getattr(p, "ticket", 0))
                pos_symbol = str(getattr(p, "symbol", ""))
                if pos_symbol != symbol:
                    # Defensa extra, por si se coló otra
                    continue

                side = _side_from_mt5(int(getattr(p, "type", 0)))
                price_open = _safe_float(getattr(p, "price_open", 0.0), 0.0)
                sl = _safe_float(getattr(p, "sl", 0.0), 0.0)
                tp = _safe_float(getattr(p, "tp", 0.0), 0.0)
                profit = _safe_float(getattr(p, "profit", 0.0), 0.0)

                state: Dict = {
                    "symbol": symbol,
                    "ticket": ticket,
                    "side": side,
                    "price_open": price_open,
                    "sl": sl,
                    "tp": tp,
                    "profit": profit,
                    "rvol": rvol,
                }

                try:
                    ai = reevaluate_position(state)
                except Exception as e:
                    print("[positions] reevaluate_position error:", e)
                    print(traceback.format_exc())
                    continue

                accion = (getattr(ai, "accion", "keep") or "keep").lower()
                conf = _safe_float(getattr(ai, "confianza", 0.0), 0.0)
                razon = ""
                try:
                    raw = getattr(ai, "detalles", {}).get("raw", {})
                    razon = str(raw.get("razon", ""))[:200]
                except Exception:
                    pass

                msg = _pretty_msg(symbol, ticket, accion, conf, razon, profit)
                print("[positions]", msg.replace("\n", " | "))

                # Telegram (no bloqueante)
                try:
                    send_message(msg)
                except Exception:
                    pass

                # 4) Ejecutar acción (solo si LIVE_TRADING=true)
                if not live_trading:
                    continue

                if accion == "breakeven":
                    # mover SL al precio de entrada
                    if price_open > 0:
                        ok = _mt5_modify_sl_tp(ticket, sl=price_open, tp=tp)
                        print(f"[positions] breakeven ticket={ticket} -> {ok}")

                elif accion == "close_partial":
                    # cerrar 50% como ejemplo
                    volume = _safe_float(getattr(p, "volume", 0.0), 0.0) * 0.5
                    if volume > 0:
                        ok = _mt5_close_partial(ticket, volume)
                        print(f"[positions] close_partial ticket={ticket}, vol={volume} -> {ok}")

                elif accion == "close_full":
                    ok = _mt5_close_full(ticket)
                    print(f"[positions] close_full ticket={ticket} -> {ok}")

                else:
                    # keep
                    pass

            time.sleep(loop_seconds)

        except KeyboardInterrupt:
            print("[positions] Stopped by user")
            break
        except Exception as e:
            print("[positions] Loop exception:", e)
            print(traceback.format_exc())
            time.sleep(5)


if __name__ == "__main__":
    main()
