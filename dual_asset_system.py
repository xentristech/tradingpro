"""
⚡ SISTEMA DE TRADING DUAL: BTC/USD + XAU/USD
Auto-ajusta parámetros según el activo
Detecta patrones específicos de cada mercado
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

class TradingSymbol(Enum):
    """Símbolos soportados con sus características"""
    BTCUSD = "BTCUSD"
    XAUUSD = "XAUUSD"
    
    @property
    def is_crypto(self):
        return self == TradingSymbol.BTCUSD
    
    @property
    def is_commodity(self):
        return self == TradingSymbol.XAUUSD

@dataclass
class SymbolConfig:
    """Configuración específica por símbolo"""
    symbol: str
    
    # RSI dinámico
    rsi_oversold_base: float
    rsi_overbought_base: float
    rsi_divergence_threshold: float
    
    # ATR y volatilidad
    atr_multiplier: float
    volatility_threshold: float
    
    # Gestión de riesgo
    base_risk_pct: float
    max_risk_pct: float
    pip_value: float
    min_profit_ratio: float
    
    # Timeframes prioritarios
    primary_timeframes: List[str]
    analysis_timeframes: List[str]
    
    # Detección de patrones
    pattern_sensitivity: float
    volume_importance: float
    
    # Horarios de trading (None = 24/7)
    trading_hours: Optional[Tuple[int, int]]
    
    # Niveles específicos
    support_resistance_lookback: int
    breakout_confirmation_pips: float


class DualAssetTradingSystem:
    """
    Sistema de trading optimizado para BTC/USD y XAU/USD
    Auto-detecta el símbolo y ajusta todos los parámetros
    """
    
    # ==================== CONFIGURACIONES ESPECÍFICAS ====================
    
    CONFIGS = {
        "BTCUSD": SymbolConfig(
            symbol="BTCUSD",
            # RSI - Crypto más extremo
            rsi_oversold_base=25,
            rsi_overbought_base=75,
            rsi_divergence_threshold=10,  # Mayor divergencia esperada
            # Volatilidad - Crypto muy volátil
            atr_multiplier=2.0,
            volatility_threshold=0.02,  # 2% movimiento normal
            # Riesgo - Más conservador por volatilidad
            base_risk_pct=0.005,  # 0.5% por trade
            max_risk_pct=0.02,    # 2% máximo
            pip_value=1.0,
            min_profit_ratio=2.5,  # Risk/Reward 1:2.5
            # Timeframes - Más cortos por mercado 24/7
            primary_timeframes=['5min', '15min', '1h'],
            analysis_timeframes=['1min', '5min', '15min', '1h', '4h', '1d'],
            # Detección
            pattern_sensitivity=0.75,
            volume_importance=0.8,  # Volumen muy importante en crypto
            # Trading 24/7
            trading_hours=None,
            # Niveles
            support_resistance_lookback=100,
            breakout_confirmation_pips=50
        ),
        
        "XAUUSD": SymbolConfig(
            symbol="XAUUSD",
            # RSI - Oro más estable
            rsi_oversold_base=30,
            rsi_overbought_base=70,
            rsi_divergence_threshold=7,  # Menor divergencia
            # Volatilidad - Oro menos volátil
            atr_multiplier=1.5,
            volatility_threshold=0.005,  # 0.5% movimiento normal
            # Riesgo - Más agresivo por menor volatilidad
            base_risk_pct=0.01,  # 1% por trade
            max_risk_pct=0.03,   # 3% máximo
            pip_value=0.01,
            min_profit_ratio=2.0,  # Risk/Reward 1:2
            # Timeframes - Más largos por tendencias más claras
            primary_timeframes=['15min', '1h', '4h'],
            analysis_timeframes=['5min', '15min', '1h', '4h', '1d', '1w'],
            # Detección
            pattern_sensitivity=0.85,  # Patrones más confiables
            volume_importance=0.6,     # Volumen menos crítico
            # Trading horas Londres/NY
            trading_hours=(8, 22),  # 8 AM a 10 PM
            # Niveles
            support_resistance_lookback=50,
            breakout_confirmation_pips=3
        )
    }
    
    def __init__(self, symbol: str = None):
        """Inicializa el sistema dual"""
        
        # Auto-detectar símbolo desde .env si no se proporciona
        if symbol is None:
            from dotenv import load_dotenv
            load_dotenv('configs/.env')
            symbol = os.getenv('SYMBOL', 'BTCUSD')
        
        # Normalizar símbolo
        symbol = symbol.upper().replace('/', '').replace('_', '')
        if 'BTC' in symbol:
            symbol = 'BTCUSD'
        elif 'XAU' in symbol or 'GOLD' in symbol:
            symbol = 'XAUUSD'
        
        # Cargar configuración específica
        self.symbol = symbol
        self.config = self.CONFIGS.get(symbol, self.CONFIGS['BTCUSD'])
        
        logger.info(f"🎯 Sistema inicializado para {symbol}")
        logger.info(f"  RSI: {self.config.rsi_oversold_base}/{self.config.rsi_overbought_base}")
        logger.info(f"  Risk: {self.config.base_risk_pct*100}% - {self.config.max_risk_pct*100}%")
        logger.info(f"  Timeframes: {self.config.primary_timeframes}")
        
        # Estado del sistema
        self.market_state = {
            'trend': None,
            'volatility': None,
            'momentum': None,
            'key_levels': [],
            'active_patterns': []
        }
        
        # Historial para aprendizaje
        self.performance_history = []
    
    def get_optimized_settings(self) -> Dict:
        """Retorna configuración optimizada para el símbolo actual"""
        return {
            'symbol': self.symbol,
            'config': vars(self.config),
            'market_state': self.market_state,
            'is_trading_hours': self._is_trading_hours() if self.config.trading_hours else True
        }
    
    def _is_trading_hours(self) -> bool:
        """Verifica si estamos en horario de trading"""
        if self.config.trading_hours is None:
            return True  # 24/7
        
        current_hour = datetime.now().hour
        start, end = self.config.trading_hours
        
        return start <= current_hour < end
