from typing import Optional, Dict, Any
from pydantic import BaseModel

class Setup(BaseModel):
    entrada: float = 0.0
    sl: float = 0.0
    tp: float = 0.0

class RuleDecision(BaseModel):
    bias: str                # "BUY" | "SELL" | "NEUTRAL"
    strength: float = 0.0

class AIValidationResult(BaseModel):
    senal_final: str = "NO OPERAR"   # "COMPRA" | "VENTA" | "NO OPERAR"
    confianza: float = 0.0
    accion: str = "keep"             # "keep" | "breakeven" | "close_partial" | "close_full"
    setup: Setup = Setup()
    detalles: Dict[str, Any] = {}
