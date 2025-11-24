"""
QUANTUM SIGNAL GENERATOR - Generador de Señales Cuánticas
===========================================================
Integración del sistema Quantum Action con:
- TwelveData API para datos de mercado
- Sistema de señales existente
- Validación con Ollama AI
- Multi-timeframe analysis

Autor: Xentristech Trading AI
Fecha: 2025-01-16
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict

# Agregar path del proyecto
project_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_dir))

# Imports del proyecto
from src.signals.quantum_core import (
    QuantumCore,
    QuantumSignal,
    QuantumMetrics,
    MarketRegime,
    TrailingMode
)
from src.data.twelvedata_client import TwelveDataClient
from src.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class QuantumAnalysis:
    """Análisis cuántico completo de un símbolo"""
    symbol: str
    timeframe: str
    signal: QuantumSignal
    price: float
    atr: float
    volume: float
    timestamp: datetime

    # Métricas adicionales
    velocity: float  # Velocidad del precio
    acceleration: float  # Aceleración
    intensity_score: int  # 0-100

    # Validación AI
    ai_validated: bool
    ai_confidence: float
    ai_comment: str


class QuantumSignalGenerator:
    """
    Generador profesional de señales usando Quantum Action

    Integra:
    - TwelveData para datos limpios
    - Quantum Core para cálculos
    - Ollama para validación AI
    - Multi-timeframe analysis
    """

    def __init__(
        self,
        twelvedata_api_key: Optional[str] = None,
        use_ai_validation: bool = True,
        multi_timeframe: bool = True,
        auto_scaling: bool = True
    ):
        """
        Inicializar generador de señales cuánticas

        Args:
            twelvedata_api_key: API key de TwelveData
            use_ai_validation: Validar señales con Ollama
            multi_timeframe: Análisis multi-timeframe
            auto_scaling: Auto-scaling por régimen
        """
        # TwelveData client (lee API key de .env automáticamente)
        self.twelvedata = TwelveDataClient()

        # Quantum Core
        self.quantum = QuantumCore(
            atr_period=14,
            ema_period=20,
            h_factor=1.0,
            k=2.0,
            auto_scaling=auto_scaling
        )

        # AI Validation
        self.use_ai = use_ai_validation
        if self.use_ai:
            try:
                self.ollama = OllamaClient()
                logger.info("Ollama AI validation enabled")
            except Exception as e:
                logger.warning(f"Ollama not available: {e}")
                self.use_ai = False

        # Multi-timeframe
        self.multi_timeframe = multi_timeframe
        self.timeframes = ['1min', '5min', '15min', '1h'] if multi_timeframe else ['1h']

        # Cache de análisis
        self.last_analysis: Dict[str, QuantumAnalysis] = {}

        logger.info(f"QuantumSignalGenerator initialized (AI: {self.use_ai}, MTF: {multi_timeframe})")


    def get_market_data(
        self,
        symbol: str,
        interval: str = '1h',
        outputsize: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Obtener datos de mercado desde TwelveData

        Args:
            symbol: Símbolo (ej: BTC/USD, EUR/USD)
            interval: Intervalo (1min, 5min, 15min, 1h, 1day)
            outputsize: Número de velas

        Returns:
            DataFrame con OHLCV o None si falla
        """
        try:
            # Usar el cliente TwelveData existente
            data = self.twelvedata.get_time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )

            if data is None or data.empty:
                logger.warning(f"No data for {symbol} {interval}")
                return None

            # Asegurar que tiene las columnas necesarias
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_cols):
                logger.error(f"Missing required columns in {symbol} data")
                return None

            return data

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            return None


    def calculate_velocity_acceleration(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calcular velocidad y aceleración del precio

        Velocidad = ΔP / Δt
        Aceleración = ΔVelocidad / Δt

        Args:
            df: DataFrame con precios

        Returns:
            Tuple(velocity, acceleration)
        """
        if len(df) < 3:
            return 0.0, 0.0

        try:
            close = df['close'].values

            # Velocidad (últimas 2 velas)
            price_now = close[-1]
            price_prev = close[-2]
            velocity = ((price_now - price_prev) / price_prev) * 100  # %

            # Aceleración (cambio de velocidad)
            if len(close) >= 3:
                price_prev2 = close[-3]
                velocity_prev = ((price_prev - price_prev2) / price_prev2) * 100
                acceleration = velocity - velocity_prev
            else:
                acceleration = 0.0

            return velocity, acceleration

        except Exception as e:
            logger.error(f"Error calculating velocity/acceleration: {e}")
            return 0.0, 0.0


    def calculate_intensity_score(
        self,
        velocity: float,
        acceleration: float,
        level: int,
        A: float,
        h: float
    ) -> int:
        """
        Calcular score de intensidad del movimiento (0-100)

        Basado en:
        - Velocidad absoluta
        - Aceleración
        - Nivel cuantizado
        - Magnitud de la Acción

        Args:
            velocity: Velocidad del precio
            acceleration: Aceleración
            level: Nivel cuantizado
            A: Acción actual
            h: Cuanto

        Returns:
            Score de 0-100
        """
        score = 0

        # Score por velocidad
        abs_vel = abs(velocity)
        if abs_vel > 1.0:  # >1% por período
            score += 40
        elif abs_vel > 0.5:
            score += 25
        elif abs_vel > 0.1:
            score += 10

        # Score por aceleración
        abs_acc = abs(acceleration)
        if abs_acc > 0.5:
            score += 30
        elif abs_acc > 0.1:
            score += 15

        # Score por nivel cuantizado
        if abs(level) >= 3:
            score += 20
        elif abs(level) >= 2:
            score += 10

        # Score por magnitud de Acción
        if abs(A) > 2 * h:
            score += 10

        return min(score, 100)


    def validate_with_ai(
        self,
        symbol: str,
        signal: QuantumSignal,
        df: pd.DataFrame
    ) -> Tuple[bool, float, str]:
        """
        Validar señal con Ollama AI

        Args:
            symbol: Símbolo
            signal: Señal cuántica
            df: DataFrame con datos

        Returns:
            Tuple(validated, confidence, comment)
        """
        if not self.use_ai:
            return True, signal.confidence, "AI validation disabled"

        try:
            # Preparar contexto para AI
            context = {
                'symbol': symbol,
                'signal': signal.action,
                'confidence': signal.confidence,
                'reason': signal.reason,
                'action': signal.metrics.action,
                'level': signal.metrics.level,
                'regime': signal.metrics.regime.value,
                'price': df['close'].iloc[-1],
                'divergence_bullish': signal.divergence_bullish,
                'divergence_bearish': signal.divergence_bearish
            }

            prompt = f"""
Analiza esta señal de trading basada en Quantum Action:

Símbolo: {symbol}
Señal: {signal.action}
Confianza: {signal.confidence}%
Razón: {signal.reason}

Métricas Cuánticas:
- Acción A(t): {signal.metrics.action:.6f}
- Nivel cuantizado: {signal.metrics.level}
- Régimen de mercado: {signal.metrics.regime.value}

Divergencias:
- Alcista: {signal.divergence_bullish}
- Bajista: {signal.divergence_bearish}

Precio actual: {df['close'].iloc[-1]:.4f}

Pregunta:
¿Esta señal es confiable? Dame:
1. VALID o INVALID
2. Confianza ajustada (0-100)
3. Comentario breve

Responde en formato: VALID|85|El momentum es fuerte y la divergencia confirma
"""

            response = self.ollama.analyze_with_simple_prompt(prompt)

            # Parsear respuesta
            if not response:
                return True, signal.confidence, "AI no response"

            parts = response.split('|')
            if len(parts) >= 3:
                validated = parts[0].strip().upper() == "VALID"
                ai_conf = float(parts[1].strip())
                comment = parts[2].strip()
                return validated, ai_conf, comment

            return True, signal.confidence, response

        except Exception as e:
            logger.error(f"AI validation error: {e}")
            return True, signal.confidence, f"AI error: {e}"


    def analyze_symbol(
        self,
        symbol: str,
        interval: str = '1h'
    ) -> Optional[QuantumAnalysis]:
        """
        Análisis cuántico completo de un símbolo

        Args:
            symbol: Símbolo a analizar
            interval: Timeframe

        Returns:
            QuantumAnalysis o None si falla
        """
        try:
            # Obtener datos
            df = self.get_market_data(symbol, interval=interval)
            if df is None or len(df) < 50:
                logger.warning(f"Insufficient data for {symbol} {interval}")
                return None

            # Generar señal cuántica
            signal = self.quantum.generate_signal(df)

            # Calcular ATR actual
            atr = self.quantum.calculate_atr(df).iloc[-1]

            # Calcular velocidad y aceleración
            velocity, acceleration = self.calculate_velocity_acceleration(df)

            # Calcular intensity score
            intensity = self.calculate_intensity_score(
                velocity,
                acceleration,
                signal.metrics.level,
                signal.metrics.action,
                signal.metrics.h
            )

            # Validar con AI
            ai_validated, ai_conf, ai_comment = self.validate_with_ai(
                symbol, signal, df
            )

            # Crear análisis completo
            analysis = QuantumAnalysis(
                symbol=symbol,
                timeframe=interval,
                signal=signal,
                price=df['close'].iloc[-1],
                atr=atr,
                volume=df['volume'].iloc[-1],
                timestamp=datetime.now(),
                velocity=velocity,
                acceleration=acceleration,
                intensity_score=intensity,
                ai_validated=ai_validated,
                ai_confidence=ai_conf,
                ai_comment=ai_comment
            )

            # Guardar en cache
            cache_key = f"{symbol}_{interval}"
            self.last_analysis[cache_key] = analysis

            logger.info(f"{symbol} {interval}: {signal.action} ({signal.confidence}%) - AI: {ai_conf}%")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {symbol} {interval}: {e}")
            return None


    def scan_multi_timeframe(
        self,
        symbol: str
    ) -> Dict[str, QuantumAnalysis]:
        """
        Escanear múltiples timeframes para un símbolo

        Args:
            symbol: Símbolo

        Returns:
            Dict {timeframe: QuantumAnalysis}
        """
        results = {}

        for tf in self.timeframes:
            analysis = self.analyze_symbol(symbol, interval=tf)
            if analysis:
                results[tf] = analysis

        return results


    def get_multi_timeframe_consensus(
        self,
        analyses: Dict[str, QuantumAnalysis]
    ) -> Tuple[str, float]:
        """
        Obtener consenso de múltiples timeframes

        Args:
            analyses: Dict de análisis por timeframe

        Returns:
            Tuple(action, consensus_confidence)
        """
        if not analyses:
            return "WAIT", 0

        # Contar señales por tipo
        buy_count = sum(1 for a in analyses.values() if a.signal.action == "BUY")
        exit_count = sum(1 for a in analyses.values() if a.signal.action == "EXIT")
        total = len(analyses)

        # Promediar confianza
        avg_confidence = np.mean([a.signal.confidence for a in analyses.values()])

        # Determinar consenso
        if buy_count >= total * 0.6:  # 60% o más dicen BUY
            return "BUY", avg_confidence * (buy_count / total)
        elif exit_count >= total * 0.6:
            return "EXIT", avg_confidence * (exit_count / total)
        else:
            return "WAIT", avg_confidence * 0.5


    def display_analysis(self, analysis: QuantumAnalysis):
        """Mostrar análisis de forma visual"""
        if not analysis:
            return

        action_icon = {
            "BUY": "🟢",
            "EXIT": "🔴",
            "WAIT": "🟡"
        }.get(analysis.signal.action, "⚪")

        regime_icon = {
            "trend": "📈",
            "range": "↔️",
            "volatile": "⚡",
            "low_energy": "💤"
        }.get(analysis.signal.metrics.regime.value, "")

        print(f"\n{'='*70}")
        print(f"{action_icon} {analysis.symbol} - {analysis.timeframe.upper()}")
        print(f"{'='*70}")
        print(f"💰 Precio: ${analysis.price:.4f}")
        print(f"📊 Señal: {analysis.signal.action} ({analysis.signal.confidence:.1f}%)")
        print(f"💡 Razón: {analysis.signal.reason}")
        print(f"\n🔬 MÉTRICAS CUÁNTICAS:")
        print(f"   Acción A(t): {analysis.signal.metrics.action:.6f}")
        print(f"   Cuanto h: {analysis.signal.metrics.h:.6f}")
        print(f"   Nivel: {analysis.signal.metrics.level}")
        print(f"   Banda Superior: {analysis.signal.metrics.band_upper:.6f}")
        print(f"   Banda Inferior: {analysis.signal.metrics.band_lower:.6f}")
        print(f"   {regime_icon} Régimen: {analysis.signal.metrics.regime.value.upper()}")
        print(f"\n⚡ DINÁMICA:")
        print(f"   Velocidad: {analysis.velocity:+.3f}%")
        print(f"   Aceleración: {analysis.acceleration:+.3f}%")
        print(f"   Intensidad: {analysis.intensity_score}%")
        print(f"\n🔍 DIVERGENCIAS:")
        print(f"   Alcista: {'✅' if analysis.signal.divergence_bullish else '❌'}")
        print(f"   Bajista: {'✅' if analysis.signal.divergence_bearish else '❌'}")

        if analysis.ai_validated:
            print(f"\n🤖 VALIDACIÓN AI:")
            print(f"   Validado: {'✅' if analysis.ai_validated else '❌'}")
            print(f"   Confianza AI: {analysis.ai_confidence:.1f}%")
            print(f"   Comentario: {analysis.ai_comment}")

        print(f"{'='*70}\n")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Cargar variables de entorno
    load_dotenv()

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear generador
    generator = QuantumSignalGenerator(
        use_ai_validation=True,
        multi_timeframe=True,
        auto_scaling=True
    )

    # Símbolos a analizar
    symbols = ['BTC/USD', 'EUR/USD', 'XAU/USD']

    print("\n" + "="*70)
    print("QUANTUM SIGNAL GENERATOR - ANÁLISIS EN TIEMPO REAL")
    print("="*70)

    for symbol in symbols:
        print(f"\n🔍 Analizando {symbol}...")

        # Análisis single timeframe
        analysis = generator.analyze_symbol(symbol, interval='1h')
        if analysis:
            generator.display_analysis(analysis)

        # Multi-timeframe (opcional)
        if generator.multi_timeframe:
            print(f"\n📊 Análisis Multi-Timeframe {symbol}:")
            mtf_analyses = generator.scan_multi_timeframe(symbol)
            consensus, consensus_conf = generator.get_multi_timeframe_consensus(mtf_analyses)
            print(f"   Consenso: {consensus} ({consensus_conf:.1f}%)")
            print(f"   Timeframes analizados: {list(mtf_analyses.keys())}")

    print("\n" + "="*70)
    print("Análisis completado")
    print("="*70)
