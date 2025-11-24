"""
Advanced Signal Scoring System with Multi-Factor Analysis
Author: Trading Pro System
Version: 3.0
"""

import numpy as np
import pandas as pd
import talib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class IndicatorWeight(Enum):
    """Weights for different indicator categories"""
    TREND = 0.25
    MOMENTUM = 0.20
    VOLUME = 0.20
    VOLATILITY = 0.15
    SENTIMENT = 0.10
    ML_PREDICTION = 0.10


@dataclass
class TechnicalIndicators:
    """Container for technical indicator values"""
    # Trend Indicators
    sma_20: float = 0
    sma_50: float = 0
    sma_200: float = 0
    ema_9: float = 0
    ema_21: float = 0
    macd: float = 0
    macd_signal: float = 0
    macd_histogram: float = 0
    adx: float = 0
    plus_di: float = 0
    minus_di: float = 0

    # Momentum Indicators
    rsi: float = 50
    stochastic_k: float = 50
    stochastic_d: float = 50
    cci: float = 0
    williams_r: float = -50
    roc: float = 0

    # Volume Indicators
    obv: float = 0
    volume_sma: float = 0
    volume_ratio: float = 1.0
    mfi: float = 50
    accumulation_distribution: float = 0
    cmf: float = 0  # Chaikin Money Flow

    # Volatility Indicators
    atr: float = 0
    bollinger_upper: float = 0
    bollinger_middle: float = 0
    bollinger_lower: float = 0
    bollinger_bandwidth: float = 0
    keltner_upper: float = 0
    keltner_lower: float = 0
    donchian_upper: float = 0
    donchian_lower: float = 0


@dataclass
class MarketContext:
    """Market context and sentiment indicators"""
    trend_strength: float = 0  # -1 to 1 (bearish to bullish)
    volatility_regime: str = "normal"  # low, normal, high
    volume_profile: str = "average"  # low, average, high, extreme
    market_hours: str = "regular"  # pre, regular, after, closed
    news_sentiment: float = 0  # -1 to 1
    social_sentiment: float = 0  # -1 to 1
    correlation_spy: float = 0  # Correlation with S&P 500
    vix_level: float = 20  # Volatility index
    dollar_strength: float = 0  # DXY influence


@dataclass
class SignalScore:
    """Detailed signal scoring result"""
    overall_score: float  # 0 to 100
    signal_type: SignalType
    confidence: float  # 0 to 1
    strength: float  # 0 to 1

    # Component scores
    trend_score: float = 0
    momentum_score: float = 0
    volume_score: float = 0
    volatility_score: float = 0
    sentiment_score: float = 0
    ml_score: float = 0

    # Additional metrics
    risk_reward_ratio: float = 0
    expected_move: float = 0
    time_horizon: str = "short"  # short, medium, long

    # Detailed breakdown
    component_scores: Dict[str, float] = field(default_factory=dict)
    indicator_signals: Dict[str, str] = field(default_factory=dict)

    # Reasoning
    reasoning: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SignalScoringSystem:
    """
    Advanced multi-factor signal scoring system
    """

    def __init__(self):
        """Initialize the scoring system"""
        self.weights = {
            'trend': IndicatorWeight.TREND.value,
            'momentum': IndicatorWeight.MOMENTUM.value,
            'volume': IndicatorWeight.VOLUME.value,
            'volatility': IndicatorWeight.VOLATILITY.value,
            'sentiment': IndicatorWeight.SENTIMENT.value,
            'ml': IndicatorWeight.ML_PREDICTION.value
        }

        # Score thresholds for signal classification
        self.thresholds = {
            'strong_buy': 75,
            'buy': 60,
            'sell': 40,
            'strong_sell': 25
        }

        # Initialize scoring functions
        self.scoring_functions = {
            'trend': self._score_trend,
            'momentum': self._score_momentum,
            'volume': self._score_volume,
            'volatility': self._score_volatility,
            'sentiment': self._score_sentiment
        }

    def calculate_signal_score(self,
                              data: pd.DataFrame,
                              indicators: Optional[TechnicalIndicators] = None,
                              context: Optional[MarketContext] = None,
                              ml_prediction: Optional[Dict] = None) -> SignalScore:
        """
        Calculate comprehensive signal score

        Args:
            data: Price and volume data (OHLCV)
            indicators: Pre-calculated technical indicators
            context: Market context and sentiment
            ml_prediction: Machine learning model prediction

        Returns:
            SignalScore object with detailed scoring
        """
        # Calculate indicators if not provided
        if indicators is None:
            indicators = self._calculate_indicators(data)

        # Get market context if not provided
        if context is None:
            context = self._analyze_market_context(data)

        # Calculate component scores
        component_scores = {}

        # Trend Analysis
        trend_score, trend_signals = self._score_trend(data, indicators)
        component_scores['trend'] = trend_score

        # Momentum Analysis
        momentum_score, momentum_signals = self._score_momentum(data, indicators)
        component_scores['momentum'] = momentum_score

        # Volume Analysis
        volume_score, volume_signals = self._score_volume(data, indicators)
        component_scores['volume'] = volume_score

        # Volatility Analysis
        volatility_score, volatility_signals = self._score_volatility(data, indicators, context)
        component_scores['volatility'] = volatility_score

        # Sentiment Analysis
        sentiment_score = self._score_sentiment(context)
        component_scores['sentiment'] = sentiment_score

        # ML Score
        ml_score = 50  # Default neutral
        if ml_prediction:
            ml_score = self._score_ml_prediction(ml_prediction)
        component_scores['ml'] = ml_score

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(component_scores)

        # Determine signal type
        signal_type = self._determine_signal_type(overall_score)

        # Calculate confidence and strength
        confidence = self._calculate_confidence(component_scores)
        strength = self._calculate_strength(overall_score, confidence)

        # Calculate risk-reward ratio
        risk_reward = self._calculate_risk_reward(data, indicators)

        # Expected move calculation
        expected_move = self._calculate_expected_move(data, indicators, overall_score)

        # Combine all indicator signals
        all_signals = {**trend_signals, **momentum_signals, **volume_signals, **volatility_signals}

        # Generate reasoning and warnings
        reasoning = self._generate_reasoning(component_scores, all_signals)
        warnings = self._generate_warnings(indicators, context, component_scores)

        return SignalScore(
            overall_score=overall_score,
            signal_type=signal_type,
            confidence=confidence,
            strength=strength,
            trend_score=trend_score,
            momentum_score=momentum_score,
            volume_score=volume_score,
            volatility_score=volatility_score,
            sentiment_score=sentiment_score,
            ml_score=ml_score,
            risk_reward_ratio=risk_reward,
            expected_move=expected_move,
            time_horizon=self._determine_time_horizon(indicators),
            component_scores=component_scores,
            indicator_signals=all_signals,
            reasoning=reasoning,
            warnings=warnings
        )

    def _calculate_indicators(self, data: pd.DataFrame) -> TechnicalIndicators:
        """
        Calculate all technical indicators

        Args:
            data: OHLCV data

        Returns:
            TechnicalIndicators object
        """
        indicators = TechnicalIndicators()

        # Ensure we have enough data
        if len(data) < 200:
            logger.warning("Insufficient data for all indicators")
            return indicators

        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        volume = data['volume'].values

        # Trend Indicators
        indicators.sma_20 = talib.SMA(close, timeperiod=20)[-1]
        indicators.sma_50 = talib.SMA(close, timeperiod=50)[-1]
        indicators.sma_200 = talib.SMA(close, timeperiod=200)[-1]
        indicators.ema_9 = talib.EMA(close, timeperiod=9)[-1]
        indicators.ema_21 = talib.EMA(close, timeperiod=21)[-1]

        macd, macd_signal, macd_hist = talib.MACD(close)
        indicators.macd = macd[-1]
        indicators.macd_signal = macd_signal[-1]
        indicators.macd_histogram = macd_hist[-1]

        indicators.adx = talib.ADX(high, low, close)[-1]
        indicators.plus_di = talib.PLUS_DI(high, low, close)[-1]
        indicators.minus_di = talib.MINUS_DI(high, low, close)[-1]

        # Momentum Indicators
        indicators.rsi = talib.RSI(close)[-1]
        k, d = talib.STOCH(high, low, close)
        indicators.stochastic_k = k[-1]
        indicators.stochastic_d = d[-1]
        indicators.cci = talib.CCI(high, low, close)[-1]
        indicators.williams_r = talib.WILLR(high, low, close)[-1]
        indicators.roc = talib.ROC(close)[-1]

        # Volume Indicators
        indicators.obv = talib.OBV(close, volume)[-1]
        indicators.volume_sma = talib.SMA(volume, timeperiod=20)[-1]
        indicators.volume_ratio = volume[-1] / indicators.volume_sma if indicators.volume_sma > 0 else 1
        indicators.mfi = talib.MFI(high, low, close, volume)[-1]
        indicators.accumulation_distribution = talib.AD(high, low, close, volume)[-1]

        # Volatility Indicators
        indicators.atr = talib.ATR(high, low, close)[-1]
        upper, middle, lower = talib.BBANDS(close)
        indicators.bollinger_upper = upper[-1]
        indicators.bollinger_middle = middle[-1]
        indicators.bollinger_lower = lower[-1]
        indicators.bollinger_bandwidth = (upper[-1] - lower[-1]) / middle[-1] if middle[-1] > 0 else 0

        # Donchian Channels
        indicators.donchian_upper = max(high[-20:])
        indicators.donchian_lower = min(low[-20:])

        return indicators

    def _score_trend(self, data: pd.DataFrame, indicators: TechnicalIndicators) -> Tuple[float, Dict]:
        """
        Score trend indicators

        Returns:
            Tuple of (score 0-100, signal dictionary)
        """
        signals = {}
        score = 50  # Start neutral
        current_price = data['close'].iloc[-1]

        # Moving Average Analysis
        ma_score = 0
        ma_count = 0

        # Price vs Moving Averages
        if current_price > indicators.sma_20:
            ma_score += 20
            signals['sma_20'] = 'bullish'
        else:
            signals['sma_20'] = 'bearish'

        if current_price > indicators.sma_50:
            ma_score += 15
            signals['sma_50'] = 'bullish'
        else:
            signals['sma_50'] = 'bearish'

        if current_price > indicators.sma_200:
            ma_score += 15
            signals['sma_200'] = 'bullish'
        else:
            signals['sma_200'] = 'bearish'

        # Moving Average Alignment (Golden/Death Cross)
        if indicators.sma_50 > indicators.sma_200:
            ma_score += 10
            signals['ma_cross'] = 'golden_cross'
        else:
            signals['ma_cross'] = 'death_cross'

        # MACD Analysis
        macd_score = 0
        if indicators.macd > indicators.macd_signal:
            macd_score += 20
            signals['macd'] = 'bullish'
        else:
            signals['macd'] = 'bearish'

        if indicators.macd_histogram > 0:
            macd_score += 10
            signals['macd_hist'] = 'positive'
        else:
            signals['macd_hist'] = 'negative'

        # ADX Trend Strength
        adx_score = 0
        if indicators.adx > 25:
            signals['trend_strength'] = 'strong'
            if indicators.plus_di > indicators.minus_di:
                adx_score = 20
                signals['adx_direction'] = 'bullish'
            else:
                adx_score = -20
                signals['adx_direction'] = 'bearish'
        else:
            signals['trend_strength'] = 'weak'
            adx_score = 0

        # Combine scores
        total_score = 50 + ma_score + macd_score + adx_score

        # Normalize to 0-100
        score = max(0, min(100, total_score))

        return score, signals

    def _score_momentum(self, data: pd.DataFrame, indicators: TechnicalIndicators) -> Tuple[float, Dict]:
        """
        Score momentum indicators

        Returns:
            Tuple of (score 0-100, signal dictionary)
        """
        signals = {}
        score = 50  # Start neutral

        # RSI Analysis
        rsi_score = 0
        if indicators.rsi > 70:
            rsi_score = -20
            signals['rsi'] = 'overbought'
        elif indicators.rsi > 60:
            rsi_score = 10
            signals['rsi'] = 'bullish'
        elif indicators.rsi > 40:
            rsi_score = 0
            signals['rsi'] = 'neutral'
        elif indicators.rsi > 30:
            rsi_score = -10
            signals['rsi'] = 'bearish'
        else:
            rsi_score = 20  # Oversold - potential bounce
            signals['rsi'] = 'oversold'

        # Stochastic Analysis
        stoch_score = 0
        if indicators.stochastic_k > 80:
            stoch_score = -15
            signals['stochastic'] = 'overbought'
        elif indicators.stochastic_k > indicators.stochastic_d:
            stoch_score = 15
            signals['stochastic'] = 'bullish'
        elif indicators.stochastic_k < 20:
            stoch_score = 15
            signals['stochastic'] = 'oversold'
        else:
            stoch_score = -10
            signals['stochastic'] = 'bearish'

        # CCI Analysis
        cci_score = 0
        if indicators.cci > 100:
            cci_score = 10
            signals['cci'] = 'bullish'
        elif indicators.cci < -100:
            cci_score = -10
            signals['cci'] = 'bearish'
        else:
            cci_score = 0
            signals['cci'] = 'neutral'

        # Williams %R
        williams_score = 0
        if indicators.williams_r > -20:
            williams_score = -10
            signals['williams_r'] = 'overbought'
        elif indicators.williams_r < -80:
            williams_score = 10
            signals['williams_r'] = 'oversold'
        else:
            williams_score = 0
            signals['williams_r'] = 'neutral'

        # Rate of Change
        roc_score = 0
        if indicators.roc > 5:
            roc_score = 15
            signals['roc'] = 'strong_bullish'
        elif indicators.roc > 0:
            roc_score = 5
            signals['roc'] = 'bullish'
        elif indicators.roc > -5:
            roc_score = -5
            signals['roc'] = 'bearish'
        else:
            roc_score = -15
            signals['roc'] = 'strong_bearish'

        # Combine scores
        total_score = 50 + rsi_score + stoch_score + cci_score + williams_score + roc_score

        # Check for divergences
        divergence = self._check_divergences(data, indicators)
        if divergence == 'bullish':
            total_score += 20
            signals['divergence'] = 'bullish_divergence'
        elif divergence == 'bearish':
            total_score -= 20
            signals['divergence'] = 'bearish_divergence'

        # Normalize to 0-100
        score = max(0, min(100, total_score))

        return score, signals

    def _score_volume(self, data: pd.DataFrame, indicators: TechnicalIndicators) -> Tuple[float, Dict]:
        """
        Score volume indicators

        Returns:
            Tuple of (score 0-100, signal dictionary)
        """
        signals = {}
        score = 50  # Start neutral

        # Volume Ratio Analysis
        volume_score = 0
        if indicators.volume_ratio > 2.0:
            volume_score = 20
            signals['volume'] = 'very_high'
        elif indicators.volume_ratio > 1.5:
            volume_score = 10
            signals['volume'] = 'high'
        elif indicators.volume_ratio > 0.5:
            volume_score = 0
            signals['volume'] = 'normal'
        else:
            volume_score = -10
            signals['volume'] = 'low'

        # OBV Trend
        obv_score = 0
        obv_sma = talib.SMA(np.array([indicators.obv]), timeperiod=1)[-1]  # Simplified
        if indicators.obv > obv_sma:
            obv_score = 15
            signals['obv'] = 'bullish'
        else:
            obv_score = -15
            signals['obv'] = 'bearish'

        # Money Flow Index
        mfi_score = 0
        if indicators.mfi > 80:
            mfi_score = -15
            signals['mfi'] = 'overbought'
        elif indicators.mfi > 50:
            mfi_score = 10
            signals['mfi'] = 'bullish'
        elif indicators.mfi > 20:
            mfi_score = -10
            signals['mfi'] = 'bearish'
        else:
            mfi_score = 15
            signals['mfi'] = 'oversold'

        # Accumulation/Distribution
        ad_score = 0
        if indicators.accumulation_distribution > 0:
            ad_score = 10
            signals['ad'] = 'accumulation'
        else:
            ad_score = -10
            signals['ad'] = 'distribution'

        # Price-Volume Trend Analysis
        pv_score = self._analyze_price_volume_trend(data)
        if pv_score > 0:
            signals['price_volume'] = 'bullish'
        else:
            signals['price_volume'] = 'bearish'

        # Combine scores
        total_score = 50 + volume_score + obv_score + mfi_score + ad_score + pv_score

        # Normalize to 0-100
        score = max(0, min(100, total_score))

        return score, signals

    def _score_volatility(self, data: pd.DataFrame, indicators: TechnicalIndicators,
                         context: MarketContext) -> Tuple[float, Dict]:
        """
        Score volatility indicators

        Returns:
            Tuple of (score 0-100, signal dictionary)
        """
        signals = {}
        current_price = data['close'].iloc[-1]

        # Bollinger Bands Analysis
        bb_score = 0
        bb_position = (current_price - indicators.bollinger_lower) / (
            indicators.bollinger_upper - indicators.bollinger_lower
        ) if (indicators.bollinger_upper - indicators.bollinger_lower) > 0 else 0.5

        if bb_position > 0.8:
            bb_score = -15
            signals['bollinger'] = 'upper_band'
        elif bb_position > 0.5:
            bb_score = 5
            signals['bollinger'] = 'above_middle'
        elif bb_position > 0.2:
            bb_score = -5
            signals['bollinger'] = 'below_middle'
        else:
            bb_score = 15
            signals['bollinger'] = 'lower_band'

        # Bollinger Bandwidth (volatility measure)
        bw_score = 0
        if indicators.bollinger_bandwidth < 0.05:
            bw_score = 10  # Low volatility - potential breakout
            signals['volatility'] = 'squeeze'
        elif indicators.bollinger_bandwidth > 0.20:
            bw_score = -10  # High volatility - risky
            signals['volatility'] = 'expansion'
        else:
            bw_score = 0
            signals['volatility'] = 'normal'

        # ATR Analysis
        atr_score = 0
        atr_ratio = indicators.atr / current_price if current_price > 0 else 0
        if atr_ratio > 0.03:
            atr_score = -10
            signals['atr'] = 'high_volatility'
        elif atr_ratio < 0.01:
            atr_score = 5
            signals['atr'] = 'low_volatility'
        else:
            atr_score = 0
            signals['atr'] = 'normal_volatility'

        # Donchian Channel Position
        donchian_score = 0
        donchian_position = (current_price - indicators.donchian_lower) / (
            indicators.donchian_upper - indicators.donchian_lower
        ) if (indicators.donchian_upper - indicators.donchian_lower) > 0 else 0.5

        if donchian_position > 0.8:
            donchian_score = 10
            signals['donchian'] = 'upper_breakout'
        elif donchian_position < 0.2:
            donchian_score = 10
            signals['donchian'] = 'lower_breakout'
        else:
            donchian_score = 0
            signals['donchian'] = 'within_channel'

        # Market Context Adjustment
        context_score = 0
        if context.volatility_regime == "high":
            context_score = -20
            signals['market_volatility'] = 'high'
        elif context.volatility_regime == "low":
            context_score = 10
            signals['market_volatility'] = 'low'
        else:
            context_score = 0
            signals['market_volatility'] = 'normal'

        # Combine scores
        total_score = 50 + bb_score + bw_score + atr_score + donchian_score + context_score

        # Normalize to 0-100
        score = max(0, min(100, total_score))

        return score, {'volatility_signals': signals}

    def _score_sentiment(self, context: MarketContext) -> float:
        """
        Score market sentiment

        Returns:
            Score 0-100
        """
        score = 50  # Start neutral

        # News sentiment
        news_score = context.news_sentiment * 20  # -20 to +20

        # Social sentiment
        social_score = context.social_sentiment * 15  # -15 to +15

        # VIX level (fear gauge)
        vix_score = 0
        if context.vix_level < 15:
            vix_score = 10  # Low fear
        elif context.vix_level < 20:
            vix_score = 5
        elif context.vix_level < 30:
            vix_score = -5
        else:
            vix_score = -15  # High fear

        # Market correlation
        correlation_score = 0
        if abs(context.correlation_spy) > 0.7:
            correlation_score = 5 if context.correlation_spy > 0 else -5

        # Combine scores
        total_score = 50 + news_score + social_score + vix_score + correlation_score

        # Normalize to 0-100
        return max(0, min(100, total_score))

    def _score_ml_prediction(self, ml_prediction: Dict) -> float:
        """
        Score ML model prediction

        Args:
            ml_prediction: Dictionary with 'direction', 'confidence', 'probability'

        Returns:
            Score 0-100
        """
        direction = ml_prediction.get('direction', 'neutral')
        confidence = ml_prediction.get('confidence', 0.5)
        probability = ml_prediction.get('probability', 0.5)

        # Base score from probability
        score = probability * 100

        # Adjust for confidence
        if confidence < 0.6:
            score = 50 + (score - 50) * 0.5  # Move towards neutral
        elif confidence > 0.8:
            score = 50 + (score - 50) * 1.2  # Amplify signal

        return max(0, min(100, score))

    def _calculate_weighted_score(self, component_scores: Dict[str, float]) -> float:
        """
        Calculate weighted overall score

        Args:
            component_scores: Dictionary of component scores

        Returns:
            Overall score 0-100
        """
        weighted_sum = 0
        weight_sum = 0

        for component, score in component_scores.items():
            if component in self.weights:
                weight = self.weights[component]
                weighted_sum += score * weight
                weight_sum += weight

        if weight_sum > 0:
            return weighted_sum / weight_sum
        return 50  # Default neutral

    def _determine_signal_type(self, score: float) -> SignalType:
        """
        Determine signal type from score

        Args:
            score: Overall score 0-100

        Returns:
            SignalType enum
        """
        if score >= self.thresholds['strong_buy']:
            return SignalType.STRONG_BUY
        elif score >= self.thresholds['buy']:
            return SignalType.BUY
        elif score <= self.thresholds['strong_sell']:
            return SignalType.STRONG_SELL
        elif score <= self.thresholds['sell']:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL

    def _calculate_confidence(self, component_scores: Dict[str, float]) -> float:
        """
        Calculate confidence based on agreement between components

        Args:
            component_scores: Dictionary of component scores

        Returns:
            Confidence 0-1
        """
        scores = list(component_scores.values())

        # Calculate standard deviation
        std_dev = np.std(scores)

        # Lower std means higher agreement/confidence
        # Normalize: std of 0 = confidence 1, std of 50 = confidence 0
        confidence = max(0, 1 - (std_dev / 50))

        # Adjust for extreme scores
        avg_score = np.mean(scores)
        if avg_score > 70 or avg_score < 30:
            confidence *= 1.2  # Boost confidence for strong signals

        return min(1.0, confidence)

    def _calculate_strength(self, score: float, confidence: float) -> float:
        """
        Calculate signal strength

        Args:
            score: Overall score
            confidence: Confidence level

        Returns:
            Strength 0-1
        """
        # Distance from neutral (50)
        distance = abs(score - 50) / 50

        # Combine with confidence
        strength = distance * confidence

        return min(1.0, strength)

    def _calculate_risk_reward(self, data: pd.DataFrame, indicators: TechnicalIndicators) -> float:
        """
        Calculate risk-reward ratio

        Args:
            data: OHLCV data
            indicators: Technical indicators

        Returns:
            Risk-reward ratio
        """
        current_price = data['close'].iloc[-1]

        # Use ATR for risk/reward calculation
        atr = indicators.atr

        # Support and resistance levels
        support = min(indicators.bollinger_lower, indicators.donchian_lower)
        resistance = max(indicators.bollinger_upper, indicators.donchian_upper)

        # Calculate risk (distance to support)
        risk = current_price - support

        # Calculate reward (distance to resistance)
        reward = resistance - current_price

        if risk > 0:
            return reward / risk
        return 1.0  # Default

    def _calculate_expected_move(self, data: pd.DataFrame, indicators: TechnicalIndicators,
                                score: float) -> float:
        """
        Calculate expected price move percentage

        Args:
            data: OHLCV data
            indicators: Technical indicators
            score: Overall signal score

        Returns:
            Expected move as percentage
        """
        current_price = data['close'].iloc[-1]

        # Base expected move on ATR
        atr_move = (indicators.atr / current_price) * 100

        # Adjust based on score strength
        score_multiplier = abs(score - 50) / 50  # 0 to 1

        # Expected move
        expected = atr_move * score_multiplier * 2  # Can expect up to 2x ATR move

        # Add direction
        if score < 50:
            expected = -expected

        return expected

    def _check_divergences(self, data: pd.DataFrame, indicators: TechnicalIndicators) -> str:
        """
        Check for price-indicator divergences

        Returns:
            'bullish', 'bearish', or 'none'
        """
        if len(data) < 50:
            return 'none'

        # Simple divergence check using RSI
        price_trend = 1 if data['close'].iloc[-1] > data['close'].iloc[-20] else -1

        # RSI trend (simplified)
        rsi_values = talib.RSI(data['close'].values)
        if len(rsi_values) >= 20:
            rsi_trend = 1 if rsi_values[-1] > rsi_values[-20] else -1

            if price_trend < 0 and rsi_trend > 0:
                return 'bullish'  # Price down, RSI up
            elif price_trend > 0 and rsi_trend < 0:
                return 'bearish'  # Price up, RSI down

        return 'none'

    def _analyze_price_volume_trend(self, data: pd.DataFrame) -> float:
        """
        Analyze price-volume relationship

        Returns:
            Score -20 to +20
        """
        if len(data) < 2:
            return 0

        # Recent price change
        price_change = (data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2]

        # Recent volume change
        volume_change = (data['volume'].iloc[-1] - data['volume'].iloc[-2]) / data['volume'].iloc[-2]

        # Bullish: Price up with volume up
        if price_change > 0 and volume_change > 0:
            return 20
        # Bearish: Price down with volume up
        elif price_change < 0 and volume_change > 0:
            return -20
        # Weak bullish: Price up with volume down
        elif price_change > 0 and volume_change < 0:
            return 5
        # Weak bearish: Price down with volume down
        else:
            return -5

    def _analyze_market_context(self, data: pd.DataFrame) -> MarketContext:
        """
        Analyze market context

        Args:
            data: OHLCV data

        Returns:
            MarketContext object
        """
        context = MarketContext()

        # Simplified context analysis
        returns = data['close'].pct_change()

        # Trend strength
        sma_20 = talib.SMA(data['close'].values, 20)[-1]
        sma_50 = talib.SMA(data['close'].values, 50)[-1]
        if sma_20 > sma_50 * 1.02:
            context.trend_strength = 0.5
        elif sma_20 < sma_50 * 0.98:
            context.trend_strength = -0.5
        else:
            context.trend_strength = 0

        # Volatility regime
        volatility = returns.std()
        if volatility > 0.03:
            context.volatility_regime = "high"
        elif volatility < 0.01:
            context.volatility_regime = "low"
        else:
            context.volatility_regime = "normal"

        # Volume profile
        avg_volume = data['volume'].mean()
        current_volume = data['volume'].iloc[-1]
        if current_volume > avg_volume * 2:
            context.volume_profile = "extreme"
        elif current_volume > avg_volume * 1.5:
            context.volume_profile = "high"
        elif current_volume < avg_volume * 0.5:
            context.volume_profile = "low"
        else:
            context.volume_profile = "average"

        return context

    def _determine_time_horizon(self, indicators: TechnicalIndicators) -> str:
        """
        Determine optimal time horizon for signal

        Returns:
            'short', 'medium', or 'long'
        """
        # Based on ADX and volatility
        if indicators.adx > 40:
            return "short"  # Strong trend, act quickly
        elif indicators.adx > 25:
            return "medium"
        else:
            return "long"  # Weak trend, longer horizon

    def _generate_reasoning(self, component_scores: Dict[str, float],
                           signals: Dict[str, str]) -> List[str]:
        """
        Generate reasoning for the signal

        Returns:
            List of reasoning statements
        """
        reasoning = []

        # Analyze component scores
        for component, score in component_scores.items():
            if score > 70:
                reasoning.append(f"Strong {component} indicators (score: {score:.1f})")
            elif score > 60:
                reasoning.append(f"Positive {component} signals (score: {score:.1f})")
            elif score < 30:
                reasoning.append(f"Weak {component} indicators (score: {score:.1f})")
            elif score < 40:
                reasoning.append(f"Negative {component} signals (score: {score:.1f})")

        # Add specific signal insights
        if 'macd' in signals:
            if signals['macd'] == 'bullish':
                reasoning.append("MACD shows bullish crossover")
            else:
                reasoning.append("MACD shows bearish crossover")

        if 'rsi' in signals:
            if signals['rsi'] == 'overbought':
                reasoning.append("RSI indicates overbought conditions")
            elif signals['rsi'] == 'oversold':
                reasoning.append("RSI indicates oversold conditions")

        if 'volume' in signals:
            if signals['volume'] == 'very_high':
                reasoning.append("Unusually high volume detected")
            elif signals['volume'] == 'low':
                reasoning.append("Low volume suggests weak conviction")

        return reasoning

    def _generate_warnings(self, indicators: TechnicalIndicators,
                          context: MarketContext,
                          component_scores: Dict[str, float]) -> List[str]:
        """
        Generate warnings for potential issues

        Returns:
            List of warning statements
        """
        warnings = []

        # Check for conflicting signals
        scores = list(component_scores.values())
        if np.std(scores) > 30:
            warnings.append("Mixed signals detected across indicators")

        # Volatility warnings
        if context.volatility_regime == "high":
            warnings.append("High market volatility - increased risk")

        # Volume warnings
        if context.volume_profile == "low":
            warnings.append("Low volume - potential false signal")

        # Overbought/Oversold warnings
        if indicators.rsi > 70 and indicators.mfi > 80:
            warnings.append("Multiple overbought indicators")
        elif indicators.rsi < 30 and indicators.mfi < 20:
            warnings.append("Multiple oversold indicators")

        # ADX warning
        if indicators.adx < 20:
            warnings.append("Weak trend - potential choppy market")

        return warnings

    def adjust_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Adjust component weights for scoring

        Args:
            new_weights: Dictionary of component weights (should sum to 1)
        """
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, normalizing...")
            # Normalize weights
            for key in new_weights:
                new_weights[key] /= total

        self.weights.update(new_weights)
        logger.info(f"Weights updated: {self.weights}")

    def set_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Update signal thresholds

        Args:
            thresholds: Dictionary with 'strong_buy', 'buy', 'sell', 'strong_sell'
        """
        self.thresholds.update(thresholds)
        logger.info(f"Thresholds updated: {self.thresholds}")


# Example usage
if __name__ == "__main__":
    # Create sample data
    import yfinance as yf

    # Download sample data
    ticker = "SPY"
    data = yf.download(ticker, period="6mo", interval="1d")
    data.columns = [col.lower() for col in data.columns]

    # Initialize scoring system
    scorer = SignalScoringSystem()

    # Calculate signal score
    signal_score = scorer.calculate_signal_score(data)

    # Print results
    print(f"\n{'='*50}")
    print(f"Signal Analysis for {ticker}")
    print(f"{'='*50}")
    print(f"Overall Score: {signal_score.overall_score:.1f}/100")
    print(f"Signal Type: {signal_score.signal_type.value}")
    print(f"Confidence: {signal_score.confidence:.1%}")
    print(f"Strength: {signal_score.strength:.1%}")

    print(f"\nComponent Scores:")
    print(f"  Trend: {signal_score.trend_score:.1f}")
    print(f"  Momentum: {signal_score.momentum_score:.1f}")
    print(f"  Volume: {signal_score.volume_score:.1f}")
    print(f"  Volatility: {signal_score.volatility_score:.1f}")
    print(f"  Sentiment: {signal_score.sentiment_score:.1f}")
    print(f"  ML Score: {signal_score.ml_score:.1f}")

    print(f"\nRisk Metrics:")
    print(f"  Risk/Reward Ratio: {signal_score.risk_reward_ratio:.2f}")
    print(f"  Expected Move: {signal_score.expected_move:+.1f}%")
    print(f"  Time Horizon: {signal_score.time_horizon}")

    print(f"\nReasoning:")
    for reason in signal_score.reasoning:
        print(f"  - {reason}")

    if signal_score.warnings:
        print(f"\nWarnings:")
        for warning in signal_score.warnings:
            print(f"  ⚠ {warning}")