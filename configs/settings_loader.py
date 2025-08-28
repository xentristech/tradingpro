"""
Settings Loader - Valida y carga settings.yaml con Pydantic.
Permite valores por defecto y overrides por variables de entorno.
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
import os
import yaml


class TradingSettings(BaseModel):
    # Gating de mercado
    RVOL_MIN: float = Field(0.8, description="Umbral mínimo de RVOL para operar")
    CMF_BUY_MIN: float = Field(0.0, description="CMF promedio mínimo para COMPRA")
    CMF_SELL_MAX: float = Field(0.0, description="CMF promedio máximo para VENTA")

    # Gestión de posiciones
    BREAKEVEN_TRIGGER: float = Field(0.001, description="Umbral de breakeven (ratio)")
    TRAILING_DISTANCE: float = Field(0.002, description="Trailing porcentaje relativo")
    TRAILING_ATR_MULT: float = Field(1.5, description="Multiplicador ATR para trailing")

    # Reportes
    REPORT_HOUR: int = Field(23, description="Hora del día para reporte (0-23)" )

    # Horarios / régimen
    MARKET_HOURS_START: str = Field("00:00", description="Inicio horario de trading HH:MM")
    MARKET_HOURS_END: str = Field("23:59", description="Fin horario de trading HH:MM")
    ALLOW_WEEKENDS: bool = Field(True, description="Permitir trading fines de semana")
    VOLATILITY_MAX: float = Field(0.05, description="ATR/Price máximo permitido")
    ENABLE_MARKET_REGIME: bool = Field(True, description="Activar filtros de horario/volatilidad")
    # IA / Orquestación
    ENABLE_AI_ORCHESTRATION: bool = Field(False, description="Permitir que la IA proponga acciones")
    AI_DECISION_CONFIDENCE_MIN: float = Field(0.7, description="Confianza mínima de IA para considerar acción")
    AI_MAX_ACTIONS: int = Field(1, description="Máximo de acciones por ciclo")
    AI_REQUIRE_HUMAN_CONFIRMATION: bool = Field(False, description="Requerir confirmación humana (off para fully-auto)")
    AI_APPROVAL_TIMEOUT_SECONDS: int = Field(60, description="Tiempo máximo para aprobar acción IA")

    @validator('REPORT_HOUR')
    def _hour_range(cls, v):
        if not (0 <= v <= 23):
            raise ValueError('REPORT_HOUR debe estar entre 0 y 23')
        return v


def load_settings(path: str = 'configs/settings.yaml') -> TradingSettings:
    data = {}
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        data = {}

    # Overrides por entorno
    def envf(key: str, cast):
        val = os.getenv(key)
        if val is None:
            return None
        try:
            return cast(val)
        except Exception:
            return None

    overrides = {
        'RVOL_MIN': envf('RVOL_MIN', float),
        'CMF_BUY_MIN': envf('CMF_BUY_MIN', float),
        'CMF_SELL_MAX': envf('CMF_SELL_MAX', float),
        'BREAKEVEN_TRIGGER': envf('BREAKEVEN_TRIGGER', float),
        'TRAILING_DISTANCE': envf('TRAILING_DISTANCE', float),
        'TRAILING_ATR_MULT': envf('TRAILING_ATR_MULT', float),
        'REPORT_HOUR': envf('REPORT_HOUR', int),
        'MARKET_HOURS_START': os.getenv('MARKET_HOURS_START'),
        'MARKET_HOURS_END': os.getenv('MARKET_HOURS_END'),
        'ALLOW_WEEKENDS': envf('ALLOW_WEEKENDS', lambda v: str(v).lower() == 'true'),
        'VOLATILITY_MAX': envf('VOLATILITY_MAX', float),
        'ENABLE_MARKET_REGIME': envf('ENABLE_MARKET_REGIME', lambda v: str(v).lower() == 'true'),
        'ENABLE_AI_ORCHESTRATION': envf('ENABLE_AI_ORCHESTRATION', lambda v: str(v).lower() == 'true'),
        'AI_DECISION_CONFIDENCE_MIN': envf('AI_DECISION_CONFIDENCE_MIN', float),
        'AI_MAX_ACTIONS': envf('AI_MAX_ACTIONS', int),
        'AI_REQUIRE_HUMAN_CONFIRMATION': envf('AI_REQUIRE_HUMAN_CONFIRMATION', lambda v: str(v).lower() == 'true'),
        'AI_APPROVAL_TIMEOUT_SECONDS': envf('AI_APPROVAL_TIMEOUT_SECONDS', int),
    }
    for k, v in list(overrides.items()):
        if v is not None:
            data[k] = v

    return TradingSettings(**data)
