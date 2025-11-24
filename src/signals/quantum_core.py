"""
QUANTUM ACTION CORE - Núcleo del Sistema de Acción Cuantizada
===============================================================
Implementación del sistema "Quantum Action" basado en principios de física:
- A(t) = EMA(|ΔP| - ATR)  [Acción como momentum neto vs volatilidad]
- Cuantización en niveles discretos
- Quantum Bands para zonas de fuerza
- Divergencias entre Acción y Precio
- Auto-Scaling por régimen de mercado

Inspirado en conceptos de:
- Energía Cinética (movimiento del precio)
- Energía Potencial (volatilidad/ruido)
- Acción Física (integral de la diferencia)
- Cuantización (niveles discretos de energía)

Autor: Xentristech Trading AI
Fecha: 2025-01-16
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Regímenes de mercado para Auto-Scaling"""
    TREND = "trend"
    RANGE = "range"
    VOLATILE = "volatile"
    LOW_ENERGY = "low_energy"


class TrailingMode(Enum):
    """Modos de trailing stop"""
    ATR = "atr"
    H = "h"
    BAND = "quantum_band"
    LEVEL = "level_adaptive"


@dataclass
class QuantumMetrics:
    """Métricas del sistema cuántico"""
    action: float  # A(t) - Acción suavizada
    h: float  # Cuanto (desviación estándar de la acción)
    level: int  # Nivel cuantizado
    band_upper: float  # Banda superior
    band_lower: float  # Banda inferior
    regime: MarketRegime  # Régimen actual del mercado


@dataclass
class QuantumSignal:
    """Señal generada por el sistema cuántico"""
    action: str  # "BUY", "SELL", "EXIT", "WAIT"
    confidence: float  # 0-100
    reason: str
    metrics: QuantumMetrics
    divergence_bullish: bool
    divergence_bearish: bool
    timestamp: pd.Timestamp


class QuantumCore:
    """
    Núcleo del sistema Quantum Action

    Fórmulas principales:
    - T = |ΔP| = |P_t - P_{t-1}|  (energía cinética)
    - V = ATR  (energía potencial / volatilidad)
    - Raw Action = T - V
    - A(t) = EMA(T - V)  (acción suavizada)
    - h = std(A)  (cuanto de acción)
    - level = round(A / h)  (cuantización)
    - Bands = A ± k·h  (bandas cuánticas)
    """

    def __init__(
        self,
        atr_period: int = 14,
        ema_period: int = 20,
        h_factor: float = 1.0,
        k: float = 2.0,
        div_lookback: int = 5,
        auto_scaling: bool = True
    ):
        """
        Inicializar sistema cuántico

        Args:
            atr_period: Período para ATR (volatilidad)
            ema_period: Período para EMA de la acción
            h_factor: Multiplicador para h (cuanto)
            k: Multiplicador para bandas cuánticas
            div_lookback: Períodos para detectar divergencias
            auto_scaling: Activar auto-scaling por régimen
        """
        self.atr_period = atr_period
        self.ema_period = ema_period
        self.h_factor = h_factor
        self.k = k
        self.div_lookback = div_lookback
        self.auto_scaling = auto_scaling

        # Cache de datos históricos
        self.price_history: List[float] = []
        self.action_history: List[float] = []
        self.atr_history: List[float] = []

        logger.info(f"QuantumCore inicializado: ATR={atr_period}, EMA={ema_period}, h={h_factor}, k={k}")


    def calculate_atr(self, df: pd.DataFrame, period: Optional[int] = None) -> pd.Series:
        """
        Calcular Average True Range (ATR)

        ATR = EMA(True Range)
        True Range = max(High-Low, |High-Close_prev|, |Low-Close_prev|)

        Args:
            df: DataFrame con columnas 'high', 'low', 'close'
            period: Período para ATR (default: self.atr_period)

        Returns:
            Series con valores de ATR
        """
        if period is None:
            period = self.atr_period

        high = df['high']
        low = df['low']
        close = df['close']

        # Calcular True Range
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Suavizar con EMA
        atr = tr.ewm(alpha=1/period, adjust=False).mean()

        return atr


    def calculate_action(
        self,
        df: pd.DataFrame,
        atr_period: Optional[int] = None,
        ema_period: Optional[int] = None
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcular Acción Cuantizada A(t)

        Fórmula:
        1. T = |ΔP| = |close_t - close_{t-1}|  (movimiento absoluto)
        2. V = ATR  (volatilidad)
        3. Raw = T - V  (acción bruta)
        4. A(t) = EMA(Raw)  (acción suavizada)

        Args:
            df: DataFrame con datos OHLC
            atr_period: Período para ATR
            ema_period: Período para EMA

        Returns:
            Tuple(A, h, level):
                - A: Serie con valores de Acción
                - h: Valor del cuanto (scalar)
                - level: Serie con niveles cuantizados
        """
        if atr_period is None:
            atr_period = self.atr_period
        if ema_period is None:
            ema_period = self.ema_period

        close = df['close']

        # 1. Energía Cinética (momentum absoluto)
        T = (close - close.shift(1)).abs()

        # 2. Energía Potencial (volatilidad)
        V = self.calculate_atr(df, period=atr_period)

        # 3. Acción bruta (momentum neto)
        raw_action = T - V

        # 4. Acción suavizada
        A = raw_action.ewm(span=ema_period, adjust=False).mean()

        # 5. Calcular h (cuanto) = desviación estándar de la acción
        h = np.nanstd(A.values) * self.h_factor
        if h == 0 or np.isnan(h):
            h = 1e-8  # Evitar división por cero

        # 6. Cuantizar en niveles
        # Evitar división por cero y valores no finitos
        with np.errstate(divide='ignore', invalid='ignore'):
            level_float = np.round(A / h)
            # Reemplazar NaN e infinitos con 0
            level_float = np.nan_to_num(level_float, nan=0.0, posinf=0.0, neginf=0.0)
            level_array = level_float.astype(int)
            # Convertir a Series para mantener el índice
            level = pd.Series(level_array, index=A.index)

        return A, h, level


    def calculate_quantum_bands(
        self,
        A: pd.Series,
        h: float,
        k: Optional[float] = None
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calcular Bandas Cuánticas

        Bands = A(t) ± k·h

        Interpretación:
        - Band Upper: Zona de fuerza extrema (breakout potencial)
        - Band Lower: Zona de agotamiento (reversal potencial)

        Args:
            A: Serie de Acción
            h: Cuanto
            k: Multiplicador de bandas

        Returns:
            Tuple(upper_band, lower_band)
        """
        if k is None:
            k = self.k

        upper_band = A + k * h
        lower_band = A - k * h

        return upper_band, lower_band


    def detect_divergence(
        self,
        price: pd.Series,
        action: pd.Series,
        lookback: Optional[int] = None
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Detectar divergencias entre Precio y Acción

        Divergencia Alcista:
        - Precio hace mínimo más bajo
        - Acción hace mínimo más alto
        → Señal de posible giro alcista

        Divergencia Bajista:
        - Precio hace máximo más alto
        - Acción hace máximo más bajo
        → Señal de posible giro bajista

        Args:
            price: Serie de precios
            action: Serie de Acción
            lookback: Períodos para comparar

        Returns:
            Tuple(bullish_div, bearish_div):
                Series booleanas con divergencias detectadas
        """
        if lookback is None:
            lookback = self.div_lookback

        # Divergencia Alcista: precio ↓, acción ↑
        bullish_div = (
            (price < price.shift(lookback)) &
            (action > action.shift(lookback))
        )

        # Divergencia Bajista: precio ↑, acción ↓
        bearish_div = (
            (price > price.shift(lookback)) &
            (action < action.shift(lookback))
        )

        return bullish_div, bearish_div


    def detect_market_regime(
        self,
        A: pd.Series,
        h: float,
        atr: pd.Series
    ) -> MarketRegime:
        """
        Detectar régimen del mercado para Auto-Scaling

        Regímenes:
        - TREND: A(t) > 2·h (acción fuerte direccional)
        - RANGE: |A(t)| < h (acción contenida)
        - VOLATILE: ATR muy alto respecto a h
        - LOW_ENERGY: |A(t)| < 0.3·h (movimiento mínimo)

        Args:
            A: Serie de Acción
            h: Cuanto
            atr: Serie de ATR

        Returns:
            MarketRegime
        """
        A_current = A.iloc[-1] if len(A) > 0 else 0
        atr_current = atr.iloc[-1] if len(atr) > 0 else 0

        # Tendencia: Acción por encima de 2h
        if abs(A_current) > 2 * h:
            return MarketRegime.TREND

        # Rango: Acción contenida dentro de ±h
        if abs(A_current) < h:
            return MarketRegime.RANGE

        # Volátil: ATR muy grande respecto a h
        if atr_current > 3 * h:
            return MarketRegime.VOLATILE

        # Baja energía: Acción muy pequeña
        if abs(A_current) < 0.3 * h:
            return MarketRegime.LOW_ENERGY

        return MarketRegime.RANGE  # Default


    def auto_scale_parameters(self, regime: MarketRegime) -> Dict[str, any]:
        """
        Auto-Scaling de parámetros según régimen de mercado

        Ajusta dinámicamente:
        - ATR_Period
        - EMA_Period
        - h_factor
        - k (bandas)
        - trailing_mode

        Args:
            regime: Régimen detectado

        Returns:
            Dict con parámetros optimizados
        """
        if regime == MarketRegime.TREND:
            return {
                'atr_period': 14,
                'ema_period': 20,
                'h_factor': 1.0,
                'k': 2.0,
                'trailing_mode': TrailingMode.LEVEL
            }

        elif regime == MarketRegime.RANGE:
            return {
                'atr_period': 20,
                'ema_period': 30,
                'h_factor': 1.3,
                'k': 1.5,
                'trailing_mode': TrailingMode.BAND
            }

        elif regime == MarketRegime.VOLATILE:
            return {
                'atr_period': 10,
                'ema_period': 15,
                'h_factor': 1.8,
                'k': 3.0,
                'trailing_mode': TrailingMode.ATR
            }

        elif regime == MarketRegime.LOW_ENERGY:
            return {
                'atr_period': 30,
                'ema_period': 40,
                'h_factor': 0.8,
                'k': 1.0,
                'trailing_mode': TrailingMode.H
            }

        # Default
        return {
            'atr_period': 14,
            'ema_period': 20,
            'h_factor': 1.0,
            'k': 2.0,
            'trailing_mode': TrailingMode.ATR
        }


    def calculate_trailing_stop(
        self,
        price: float,
        A: float,
        h: float,
        atr: float,
        level: int,
        mode: TrailingMode,
        multiplier: float = 1.5
    ) -> float:
        """
        Calcular Trailing Stop dinámico

        4 Modos:
        1. ATR: TSL = price - multiplier·ATR
        2. H: TSL = price - multiplier·h
        3. BAND: TSL = A - k·h (banda inferior)
        4. LEVEL: Adaptativo según nivel cuantizado

        Args:
            price: Precio actual
            A: Acción actual
            h: Cuanto
            atr: ATR actual
            level: Nivel cuantizado
            mode: Modo de trailing
            multiplier: Multiplicador

        Returns:
            Precio del trailing stop
        """
        if mode == TrailingMode.ATR:
            return price - multiplier * atr

        elif mode == TrailingMode.H:
            return price - multiplier * h

        elif mode == TrailingMode.BAND:
            return A - self.k * h

        elif mode == TrailingMode.LEVEL:
            # Adaptativo por nivel
            if level >= 3:
                # Trailing agresivo en impulso fuerte
                return price - (atr + h) * multiplier * 0.7
            elif level >= 1:
                # Trailing normal
                return price - (atr + h) * multiplier
            else:
                # Level 0 → cierre inmediato
                return price - (atr + h) * 2.5

        return price - multiplier * atr  # Default


    def generate_quantum_metrics(self, df: pd.DataFrame) -> QuantumMetrics:
        """
        Generar métricas cuánticas completas

        Args:
            df: DataFrame con datos OHLC

        Returns:
            QuantumMetrics con todos los valores calculados
        """
        # Calcular componentes
        A, h, level = self.calculate_action(df)
        band_upper, band_lower = self.calculate_quantum_bands(A, h)
        atr = self.calculate_atr(df)
        regime = self.detect_market_regime(A, h, atr)

        # Auto-scaling si está activado
        if self.auto_scaling:
            new_params = self.auto_scale_parameters(regime)
            # Actualizar parámetros internos
            self.atr_period = new_params['atr_period']
            self.ema_period = new_params['ema_period']
            self.h_factor = new_params['h_factor']
            self.k = new_params['k']

        return QuantumMetrics(
            action=A.iloc[-1],
            h=h,
            level=level.iloc[-1],
            band_upper=band_upper.iloc[-1],
            band_lower=band_lower.iloc[-1],
            regime=regime
        )


    def generate_signal(
        self,
        df: pd.DataFrame,
        enter_level: int = 2,
        exit_level: int = 0
    ) -> QuantumSignal:
        """
        Generar señal de trading basada en Quantum Action

        Lógica de señales:

        BUY (LONG):
        - Divergencia alcista + A > band_upper, O
        - level cruza de ≤0 a ≥2 con A subiendo

        SELL/EXIT:
        - Divergencia bajista, O
        - A < band_lower, O
        - level ≤ 0, O
        - A decreciente

        Args:
            df: DataFrame con datos OHLC
            enter_level: Nivel mínimo para entrada
            exit_level: Nivel máximo para salida

        Returns:
            QuantumSignal con acción y métricas
        """
        # Calcular métricas
        metrics = self.generate_quantum_metrics(df)
        A, h, level = self.calculate_action(df)
        band_upper, band_lower = self.calculate_quantum_bands(A, h)

        # Detectar divergencias
        bullish_div, bearish_div = self.detect_divergence(df['close'], A)

        # Valores actuales y previos
        A_now = A.iloc[-1]
        A_prev = A.iloc[-2] if len(A) > 1 else A_now
        level_now = level.iloc[-1]
        level_prev = level.iloc[-2] if len(level) > 1 else level_now

        # Divergencias actuales
        has_bullish_div = bullish_div.iloc[-1] if len(bullish_div) > 0 else False
        has_bearish_div = bearish_div.iloc[-1] if len(bearish_div) > 0 else False

        # SEÑAL DE COMPRA (LONG)
        long_signal = False
        confidence = 0
        reason = ""

        # Condición 1: Divergencia alcista + Acción rompiendo banda superior
        if has_bullish_div and A_now > band_upper.iloc[-1]:
            long_signal = True
            confidence = 90
            reason = "Divergencia alcista + Ruptura banda superior"

        # Condición 2: Level cruza umbral con A creciente
        elif level_prev <= exit_level and level_now >= enter_level and A_now > A_prev:
            long_signal = True
            confidence = 80
            reason = f"Nivel cuantizado {level_now} + Acción creciente"

        # SEÑALES DE SALIDA
        exit_signal = False

        # Condición 1: Divergencia bajista
        if has_bearish_div:
            exit_signal = True
            confidence = 95
            reason = "Divergencia bajista detectada"

        # Condición 2: Acción rompe banda inferior
        elif A_now < band_lower.iloc[-1]:
            exit_signal = True
            confidence = 85
            reason = "Ruptura banda inferior - Agotamiento"

        # Condición 3: Nivel vuelve a zona muerta
        elif level_now <= exit_level:
            exit_signal = True
            confidence = 75
            reason = f"Nivel {level_now} - Sin momentum"

        # Condición 4: Acción perdiendo fuerza
        elif A_now < A_prev:
            exit_signal = True
            confidence = 65
            reason = "Acción decreciente"

        # Determinar acción final
        if long_signal:
            action = "BUY"
        elif exit_signal:
            action = "EXIT"
        else:
            action = "WAIT"
            confidence = 50
            reason = "Sin señal clara - Esperar"

        return QuantumSignal(
            action=action,
            confidence=confidence,
            reason=reason,
            metrics=metrics,
            divergence_bullish=has_bullish_div,
            divergence_bearish=has_bearish_div,
            timestamp=pd.Timestamp.now()
        )


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear sistema cuántico
    quantum = QuantumCore(
        atr_period=14,
        ema_period=20,
        h_factor=1.0,
        k=2.0,
        auto_scaling=True
    )

    # Datos de ejemplo (deberías usar datos reales de TwelveData o MT5)
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', periods=100, freq='1H')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)

    df = pd.DataFrame({
        'time': dates,
        'open': prices,
        'high': prices + np.random.rand(100) * 0.3,
        'low': prices - np.random.rand(100) * 0.3,
        'close': prices + np.random.randn(100) * 0.1,
        'volume': np.random.randint(1000, 10000, 100)
    })

    # Generar señal
    signal = quantum.generate_signal(df)

    print("\n" + "="*60)
    print("QUANTUM ACTION SYSTEM - TEST")
    print("="*60)
    print(f"Señal: {signal.action}")
    print(f"Confianza: {signal.confidence}%")
    print(f"Razón: {signal.reason}")
    print(f"\nMétricas:")
    print(f"  Acción A(t): {signal.metrics.action:.6f}")
    print(f"  Cuanto h: {signal.metrics.h:.6f}")
    print(f"  Nivel: {signal.metrics.level}")
    print(f"  Banda Superior: {signal.metrics.band_upper:.6f}")
    print(f"  Banda Inferior: {signal.metrics.band_lower:.6f}")
    print(f"  Régimen: {signal.metrics.regime.value}")
    print(f"\nDivergencias:")
    print(f"  Alcista: {signal.divergence_bullish}")
    print(f"  Bajista: {signal.divergence_bearish}")
    print("="*60)
