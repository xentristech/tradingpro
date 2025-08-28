import os, json, logging, time
from typing import Dict, Any, Optional
from openai import OpenAI
from .schemas import AIValidationResult, Setup

# ===================== Config cliente =====================
# Si usas Ollama local:
#   OLLAMA_API_BASE=http://localhost:11434/v1
#   OLLAMA_MODEL=llama3.1   (o el modelo que tengas)
# Si usas OpenAI u otro endpoint compatible, ajusta base_url y modelo.

_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1")
_API_KEY  = os.getenv("OPENAI_API_KEY",  "ollama")  # Ollama ignora, pero SDK lo pide
# Default de modelo: si el base_url parece Ollama -> usa uno típico de Ollama; si no, usa un mini de OpenAI
if "localhost" in _API_BASE or "127.0.0.1" in _API_BASE:
    _MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")
else:
    _MODEL = os.getenv("OLLAMA_MODEL", "gpt-4o-mini")

def _client() -> OpenAI:
    return OpenAI(base_url=_API_BASE, api_key=_API_KEY)

# ===================== Utilidades JSON =====================
def _first_json_block(text: str) -> Optional[str]:
    """Extrae el primer bloque {...} de la cadena."""
    if not text:
        return None
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return None

def _chat_json(system_prompt: str, user_prompt: str, max_retries: int = 2) -> Dict[str, Any]:
    """Llama al modelo y devuelve un dict. Reintenta si no es JSON válido."""
    cli = _client()
    for _ in range(max_retries + 1):
        try:
            resp = cli.chat.completions.create(
                model=_MODEL,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
            )
            content = resp.choices[0].message.content if resp and resp.choices else ""
            block = _first_json_block(content or "")
            try:
                if block:
                    return json.loads(block)
                return json.loads(content)
            except Exception:
                time.sleep(0.2)
                continue
        except Exception as e:
            logging.exception("LLM call failed: %s", e)
            time.sleep(0.3)
    return {}

# ===================== Prompts =====================
def _system_decision_with_bounds(precio: float, symbol: str) -> str:
    low, high = precio*0.997, precio*1.003  # ±0.3%
    return (
      "Eres un trader profesional. Usa EXCLUSIVAMENTE los datos del JSON del usuario.\n"
      "Devuelve SOLO JSON válido con este esquema:\n"
      "{ \"tabla\": [ {\"tf\":\"5m\",\"rsi\":0.0,\"macd_hist\":0.0,\"rvol\":0.0}, ... ],\n"
      "  \"senal_final\": \"COMPRA\"|\"VENTA\"|\"NO OPERAR\",\n"
      "  \"razon\":\"str\",\n"
      "  \"setup\": {\"entrada\":0.0,\"sl\":0.0,\"tp\":0.0,\"ratio\":0.0},\n"
      "  \"confianza\": 0.0 }\n"
      f"Símbolo={symbol}. PRECIO_ACTUAL={precio:.2f}. "
      f"entrada DEBE estar en [{low:.2f},{high:.2f}] (±0.3%).\n"
      "Confluencia mínima para operar: |macd_hist| creciente en 2 marcos, RSI sobre 55 (compra) o bajo 45 (venta), "
      "y RVOL >= 1.3 en 5m o 15m. Si no se cumple, responde NO OPERAR.\n"
      "Si faltan velas o el JSON está incompleto, responde NO OPERAR."
    )


_SYSTEM_REEVAL = (
    "Eres un trader que gestiona posiciones abiertas.\n"
    "Responde EXCLUSIVAMENTE en JSON válido con el esquema:\n"
    "{\n"
    '  "accion": "keep" | "breakeven" | "close_partial" | "close_full",\n'
    '  "razon": "string",\n'
    '  "confianza": 0.0..1.0\n'
    "}\n"
    "Usa RVOL bajo y pérdida de momentum para sugerir 'breakeven'. "
    "Usa deterioro claro o invalidación para 'close_partial' o 'close_full'."
)

# ===================== Helpers =====================
def _to_setup(d: Dict[str, Any]) -> Setup:
    try:
        return Setup(
            entrada=float(d.get("entrada", 0.0)),
            sl=float(d.get("sl", 0.0)),
            tp=float(d.get("tp", 0.0)),
        )
    except Exception:
        return Setup()

# ===================== API Pública =====================
def validate_signal(snapshot: Dict[str, Any]) -> AIValidationResult:
    """
    snapshot:
    {
      "symbol":"BTCUSDm",
      "tabla":[{"tf":"5m","rsi":..,"macd_hist":..,"rvol":..}, ...],
      "precio": 118000.0
    }
    """
    try:
        precio = float(snapshot.get("precio", 0.0))
        symbol = str(snapshot.get("symbol", ""))
        system_prompt = _system_decision_with_bounds(precio, symbol)

        user_prompt = json.dumps(snapshot, ensure_ascii=False)
        data = _chat_json(system_prompt, user_prompt)

        senal = str(data.get("senal_final", "NO OPERAR")).upper()
        conf  = float(data.get("confianza", 0.0))
        raw_setup = data.get("setup", {}) or {}
        setup = _to_setup(raw_setup)

        # ---- Guardrails de precios/estructura ----
        if precio > 0:
            low, high = precio * 0.98, precio * 1.02

            # clamp entrada
            if not (low <= setup.entrada <= high):
                setup.entrada = precio

            # Defaults si hay incoherencias (ajústalos o muévelos a settings.yaml)
            DEF_SL = float(os.getenv("DEF_SL_USD", "50"))
            DEF_TP = float(os.getenv("DEF_TP_USD", "100"))

            if senal == "COMPRA":
                if not (setup.sl < setup.entrada):
                    setup.sl = setup.entrada - DEF_SL
                if not (setup.tp > setup.entrada):
                    setup.tp = setup.entrada + DEF_TP
            elif senal == "VENTA":
                if not (setup.tp < setup.entrada):
                    setup.tp = setup.entrada - DEF_TP
                if not (setup.sl > setup.entrada):
                    setup.sl = setup.entrada + DEF_SL

            # ratio seguro
            try:
                risk   = abs(setup.entrada - setup.sl)
                reward = abs(setup.tp - setup.entrada)
                if risk > 0:
                    raw_setup["ratio"] = reward / risk
            except Exception:
                pass

        # Etiqueta válida
        if senal not in ("COMPRA", "VENTA", "NO OPERAR"):
            senal = "NO OPERAR"
            conf = min(conf, 0.2)

        return AIValidationResult(
            senal_final=senal,
            confianza=float(conf),
            accion="keep",
            setup=setup,
            detalles={"raw": data},
        )

    except Exception as e:
        logging.exception("validate_signal exception: %s", e)
        return AIValidationResult(
            senal_final="NO OPERAR",
            confianza=0.0,
            accion="keep",
            setup=Setup(),
            detalles={},
        )

def reevaluate_position(state: Dict[str, Any]) -> AIValidationResult:
    """
    state:
    {
      "symbol":"BTCUSDm","ticket":12345,"side":"LONG"|"SHORT",
      "price_open":..., "sl":..., "tp":..., "profit":..., "rvol":...
    }
    """
    try:
        user_prompt = json.dumps(state, ensure_ascii=False)
        data = _chat_json(_SYSTEM_REEVAL, user_prompt)

        accion = str(data.get("accion", "keep")).lower()
        conf   = float(data.get("confianza", 0.0))
        if accion not in ("keep", "breakeven", "close_partial", "close_full"):
            accion = "keep"
            conf = min(conf, 0.2)

        return AIValidationResult(
            senal_final="NO OPERAR",
            confianza=float(conf),
            accion=accion,
            setup=Setup(),
            detalles={"raw": data},
        )

    except Exception as e:
        logging.exception("reevaluate_position exception: %s", e)
        return AIValidationResult(
            senal_final="NO OPERAR",
            confianza=0.0,
            accion="keep",
            setup=Setup(),
            detalles={},
        )
