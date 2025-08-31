from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AISignalSetup(BaseModel):
    sl: Optional[float] = Field(None, description="Stop loss price")
    tp: Optional[float] = Field(None, description="Take profit price")


class AIAction(BaseModel):
    type: Literal['NO_OP', 'OPEN_POSITION', 'MODIFY_POSITION', 'CLOSE_POSITION']
    symbol: str
    side: Optional[Literal['BUY', 'SELL']] = None
    volume_hint: Optional[float] = None
    confidence: float = 0.0
    reason: Optional[str] = None
    setup: Optional[AISignalSetup] = None


class AIPlan(BaseModel):
    actions: List[AIAction] = Field(default_factory=list)
    notes: Optional[str] = None

