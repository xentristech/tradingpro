"""
Signal Generator - Generador de Señales de Trading
Combina múltiples estrategias y técnicas de análisis
Version: 3.0.0
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalDirection(Enum):
    """Dirección de la señal"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"

@dataclass
class TradingSignal:
    """Estructura de una señal de trading"""
    direction: SignalDirection
    strength: float  # 0.0 a 1.0
    confidence: float  # 0.0 a 1.0
    strategy: str
    reasons: List[str]
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'direction': self.direction.value,
            'strength': self.strength,
            'confidence': self.confidence,
            'strategy': self.strategy,
            'reasons': self.reasons,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }

class SignalGenerator:
    """
    Generador de señales de trading usando múltiples estrategias
    """
    
    def __init__(self):
        """Inicializa el generador de señales"""
        self.strategies = {
            'trend_following': self._trend_following_strategy,
            'mean_reversion': self._mean_reversion_strategy,
            'momentum': self._momentum_strategy,
            'support_resistance': self._support_resistance_strategy,
            'pattern_recognition': self._pattern_recognition_strategy
        }
        
        # Pesos para cada estrategia
        self.strategy_weights = {
            'trend_following': 0.25,
            'mean_reversion': 0.20,
            'momentum': 0.25,
            'support_resistance': 0.15,
            'pattern_recognition': 0.15
        }
        
        logger.info("SignalGenerator inicializado con {} estrategias".format(len(self.strategies)))
    
    def generate(self, data: pd.DataFrame) -> Dict:
        """
        Genera señales de trading basadas en los datos
        Args:
            data: DataFrame con datos OHLCV e indicadores
        Returns:
            Dict con señal consolidada
        """
        if data is None or data.empty:
            return self._neutral_signal()
        
        # Generar señales de cada estrategia
        signals = []
        for name, strategy_func in self.strategies.items():
            try:
                signal = strategy_func(data)
                if signal:
                    signals.append((name, signal))
            except Exception as e:
                logger.warning(f"Error en estrategia {name}: {e}")
        
        # Consolidar señales
        if signals:
            consolidated = self._consolidate_signals(signals)
            return consolidated.to_dict()
        
        return self._neutral_signal()
    
    def _trend_following_strategy(self, data: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Estrategia de seguimiento de tendencia
        Usa cruces de medias móviles y dirección de tendencia
        """
        try:
            if 'sma_20' not in data.columns or 'sma_50' not in data.columns:
                return None
            
            # Obtener últimos valores
            last_close = data['close'].iloc[-1]
            sma_20 = data['sma_20'].iloc[-1]
            sma_50 = data['sma_50'].iloc[-1]
            
            # Verificar NaN
            if pd.isna(sma_20) or pd.isna(sma_50):
                return None
            
            # Cruces de medias
            sma_20_prev = data['sma_20'].iloc[-2]
            sma_50_prev = data['sma_50'].iloc[-2]
            
            reasons = []
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            
            # Golden Cross
            if sma_20_prev <= sma_50_prev and sma_20 > sma_50:
                direction = SignalDirection.BUY
                strength = 0.8
                reasons.append("Golden Cross detectado")
            
            # Death Cross
            elif sma_20_prev >= sma_50_prev and sma_20 < sma_50:
                direction = SignalDirection.SELL
                strength = 0.8
                reasons.append("Death Cross detectado")
            
            # Tendencia alcista
            elif sma_20 > sma_50 and last_close > sma_20:
                direction = SignalDirection.BUY
                strength = 0.6
                reasons.append("Tendencia alcista confirmada")
            
            # Tendencia bajista
            elif sma_20 < sma_50 and last_close < sma_20:
                direction = SignalDirection.SELL
                strength = 0.6
                reasons.append("Tendencia bajista confirmada")
            
            if direction != SignalDirection.NEUTRAL:
                # Calcular SL y TP basados en ATR
                atr = data['atr'].iloc[-1] if 'atr' in data.columns else (data['high'].iloc[-1] - data['low'].iloc[-1])
                
                if direction == SignalDirection.BUY:
                    sl = last_close - (atr * 1.5)
                    tp = last_close + (atr * 3)
                else:
                    sl = last_close + (atr * 1.5)
                    tp = last_close - (atr * 3)
                
                return TradingSignal(
                    direction=direction,
                    strength=strength,
                    confidence=0.7,
                    strategy='trend_following',
                    reasons=reasons,
                    entry_price=last_close,
                    stop_loss=sl,
                    take_profit=tp
                )
                
        except Exception as e:
            logger.error(f"Error en trend_following_strategy: {e}")
        
        return None
    
    def _mean_reversion_strategy(self, data: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Estrategia de reversión a la media
        Identifica sobrecompra/sobreventa y divergencias
        """
        try:
            if 'rsi' not in data.columns or 'bb_upper' not in data.columns:
                return None
            
            last_close = data['close'].iloc[-1]
            rsi = data['rsi'].iloc[-1]
            bb_upper = data['bb_upper'].iloc[-1]
            bb_lower = data['bb_lower'].iloc[-1]
            bb_middle = data['bb_middle'].iloc[-1]
            
            if pd.isna(rsi) or pd.isna(bb_upper):
                return None
            
            reasons = []
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            
            # RSI sobreventa + precio en banda inferior
            if rsi < 30 and last_close <= bb_lower:
                direction = SignalDirection.BUY
                strength = 0.7
                reasons.append(f"RSI sobreventa ({rsi:.1f})")
                reasons.append("Precio en banda inferior de Bollinger")
            
            # RSI sobrecompra + precio en banda superior
            elif rsi > 70 and last_close >= bb_upper:
                direction = SignalDirection.SELL
                strength = 0.7
                reasons.append(f"RSI sobrecompra ({rsi:.1f})")
                reasons.append("Precio en banda superior de Bollinger")
            
            # Reversión desde extremos
            elif rsi < 35 and last_close < bb_middle:
                direction = SignalDirection.BUY
                strength = 0.5
                reasons.append("Posible reversión desde niveles bajos")
            
            elif rsi > 65 and last_close > bb_middle:
                direction = SignalDirection.SELL
                strength = 0.5
                reasons.append("Posible reversión desde niveles altos")
            
            if direction != SignalDirection.NEUTRAL:
                # SL y TP basados en Bollinger Bands
                if direction == SignalDirection.BUY:
                    sl = bb_lower - (bb_middle - bb_lower) * 0.2
                    tp = bb_middle
                else:
                    sl = bb_upper + (bb_upper - bb_middle) * 0.2
                    tp = bb_middle
                
                return TradingSignal(
                    direction=direction,
                    strength=strength,
                    confidence=0.6,
                    strategy='mean_reversion',
                    reasons=reasons,
                    entry_price=last_close,
                    stop_loss=sl,
                    take_profit=tp
                )
                
        except Exception as e:
            logger.error(f"Error en mean_reversion_strategy: {e}")
        
        return None
    
    def _momentum_strategy(self, data: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Estrategia de momentum
        Usa MACD y cambios de volumen
        """
        try:
            if 'macd' not in data.columns or 'volume' not in data.columns:
                return None
            
            macd = data['macd'].iloc[-1]
            macd_signal = data['macd_signal'].iloc[-1]
            macd_hist = data['macd_histogram'].iloc[-1]
            volume = data['volume'].iloc[-1]
            volume_sma = data['volume_sma'].iloc[-1] if 'volume_sma' in data.columns else data['volume'].rolling(20).mean().iloc[-1]
            
            if pd.isna(macd) or pd.isna(macd_signal):
                return None
            
            # Historial de MACD
            macd_prev = data['macd'].iloc[-2]
            signal_prev = data['macd_signal'].iloc[-2]
            
            reasons = []
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            
            # Cruce alcista de MACD con volumen alto
            if macd_prev <= signal_prev and macd > macd_signal and volume > volume_sma * 1.2:
                direction = SignalDirection.BUY
                strength = 0.8
                reasons.append("Cruce alcista de MACD")
                reasons.append("Volumen por encima del promedio")
            
            # Cruce bajista de MACD
            elif macd_prev >= signal_prev and macd < macd_signal:
                direction = SignalDirection.SELL
                strength = 0.8
                reasons.append("Cruce bajista de MACD")
            
            # Momentum alcista fuerte
            elif macd > 0 and macd_hist > 0 and macd_hist > data['macd_histogram'].iloc[-2]:
                direction = SignalDirection.BUY
                strength = 0.6
                reasons.append("Momentum alcista creciente")
            
            # Momentum bajista fuerte
            elif macd < 0 and macd_hist < 0 and macd_hist < data['macd_histogram'].iloc[-2]:
                direction = SignalDirection.SELL
                strength = 0.6
                reasons.append("Momentum bajista creciente")
            
            if direction != SignalDirection.NEUTRAL:
                last_close = data['close'].iloc[-1]
                atr = data['atr'].iloc[-1] if 'atr' in data.columns else (data['high'].iloc[-1] - data['low'].iloc[-1])
                
                if direction == SignalDirection.BUY:
                    sl = last_close - (atr * 1.2)
                    tp = last_close + (atr * 2.5)
                else:
                    sl = last_close + (atr * 1.2)
                    tp = last_close - (atr * 2.5)
                
                return TradingSignal(
                    direction=direction,
                    strength=strength,
                    confidence=0.65,
                    strategy='momentum',
                    reasons=reasons,
                    entry_price=last_close,
                    stop_loss=sl,
                    take_profit=tp
                )
                
        except Exception as e:
            logger.error(f"Error en momentum_strategy: {e}")
        
        return None
    
    def _support_resistance_strategy(self, data: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Estrategia de soporte y resistencia
        Identifica niveles clave y rupturas
        """
        try:
            # Calcular niveles de soporte y resistencia
            highs = data['high'].rolling(window=20).max()
            lows = data['low'].rolling(window=20).min()
            
            resistance = highs.iloc[-1]
            support = lows.iloc[-1]
            last_close = data['close'].iloc[-1]
            prev_close = data['close'].iloc[-2]
            
            reasons = []
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            
            # Ruptura de resistencia
            if prev_close <= resistance and last_close > resistance:
                direction = SignalDirection.BUY
                strength = 0.7
                reasons.append(f"Ruptura de resistencia en {resistance:.2f}")
            
            # Ruptura de soporte
            elif prev_close >= support and last_close < support:
                direction = SignalDirection.SELL
                strength = 0.7
                reasons.append(f"Ruptura de soporte en {support:.2f}")
            
            # Rebote en soporte
            elif last_close > support and last_close < support * 1.02:
                direction = SignalDirection.BUY
                strength = 0.5
                reasons.append(f"Rebote en soporte {support:.2f}")
            
            # Rebote en resistencia
            elif last_close < resistance and last_close > resistance * 0.98:
                direction = SignalDirection.SELL
                strength = 0.5
                reasons.append(f"Rebote en resistencia {resistance:.2f}")
            
            if direction != SignalDirection.NEUTRAL:
                if direction == SignalDirection.BUY:
                    sl = support * 0.98
                    tp = resistance * 1.02
                else:
                    sl = resistance * 1.02
                    tp = support * 0.98
                
                return TradingSignal(
                    direction=direction,
                    strength=strength,
                    confidence=0.6,
                    strategy='support_resistance',
                    reasons=reasons,
                    entry_price=last_close,
                    stop_loss=sl,
                    take_profit=tp
                )
                
        except Exception as e:
            logger.error(f"Error en support_resistance_strategy: {e}")
        
        return None
    
    def _pattern_recognition_strategy(self, data: pd.DataFrame) -> Optional[TradingSignal]:
        """
        Estrategia de reconocimiento de patrones
        Identifica patrones de velas japonesas
        """
        try:
            if len(data) < 3:
                return None
            
            # Últimas 3 velas
            last_3 = data.tail(3)
            
            reasons = []
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            
            # Detectar patrones
            pattern = self._detect_candlestick_pattern(last_3)
            
            if pattern == 'bullish_engulfing':
                direction = SignalDirection.BUY
                strength = 0.7
                reasons.append("Patrón envolvente alcista")
            
            elif pattern == 'bearish_engulfing':
                direction = SignalDirection.SELL
                strength = 0.7
                reasons.append("Patrón envolvente bajista")
            
            elif pattern == 'hammer':
                direction = SignalDirection.BUY
                strength = 0.6
                reasons.append("Patrón martillo")
            
            elif pattern == 'shooting_star':
                direction = SignalDirection.SELL
                strength = 0.6
                reasons.append("Patrón estrella fugaz")
            
            elif pattern == 'doji':
                # Doji indica indecisión, considerar contexto
                if 'rsi' in data.columns:
                    rsi = data['rsi'].iloc[-1]
                    if rsi < 40:
                        direction = SignalDirection.BUY
                        strength = 0.4
                        reasons.append("Doji en zona de sobreventa")
                    elif rsi > 60:
                        direction = SignalDirection.SELL
                        strength = 0.4
                        reasons.append("Doji en zona de sobrecompra")
            
            if direction != SignalDirection.NEUTRAL:
                last_close = data['close'].iloc[-1]
                atr = data['atr'].iloc[-1] if 'atr' in data.columns else (data['high'].iloc[-1] - data['low'].iloc[-1])
                
                if direction == SignalDirection.BUY:
                    sl = last_close - atr
                    tp = last_close + (atr * 2)
                else:
                    sl = last_close + atr
                    tp = last_close - (atr * 2)
                
                return TradingSignal(
                    direction=direction,
                    strength=strength,
                    confidence=0.55,
                    strategy='pattern_recognition',
                    reasons=reasons,
                    entry_price=last_close,
                    stop_loss=sl,
                    take_profit=tp
                )
                
        except Exception as e:
            logger.error(f"Error en pattern_recognition_strategy: {e}")
        
        return None
    
    def _detect_candlestick_pattern(self, candles: pd.DataFrame) -> str:
        """
        Detecta patrones de velas japonesas
        Args:
            candles: Últimas 3 velas
        Returns:
            Nombre del patrón detectado o 'none'
        """
        if len(candles) < 2:
            return 'none'
        
        # Última y penúltima vela
        last = candles.iloc[-1]
        prev = candles.iloc[-2]
        
        # Calcular cuerpos
        last_body = abs(last['close'] - last['open'])
        prev_body = abs(prev['close'] - prev['open'])
        
        # Bullish Engulfing
        if (prev['close'] < prev['open'] and  # Vela bajista previa
            last['close'] > last['open'] and  # Vela alcista actual
            last['open'] <= prev['close'] and  # Apertura debajo del cierre previo
            last['close'] >= prev['open']):   # Cierre encima de apertura previa
            return 'bullish_engulfing'
        
        # Bearish Engulfing
        if (prev['close'] > prev['open'] and  # Vela alcista previa
            last['close'] < last['open'] and  # Vela bajista actual
            last['open'] >= prev['close'] and  # Apertura encima del cierre previo
            last['close'] <= prev['open']):   # Cierre debajo de apertura previa
            return 'bearish_engulfing'
        
        # Hammer
        lower_wick = min(last['open'], last['close']) - last['low']
        upper_wick = last['high'] - max(last['open'], last['close'])
        if lower_wick > last_body * 2 and upper_wick < last_body * 0.3:
            return 'hammer'
        
        # Shooting Star
        if upper_wick > last_body * 2 and lower_wick < last_body * 0.3:
            return 'shooting_star'
        
        # Doji
        if last_body < (last['high'] - last['low']) * 0.1:
            return 'doji'
        
        return 'none'
    
    def _consolidate_signals(self, signals: List[Tuple[str, TradingSignal]]) -> TradingSignal:
        """
        Consolida múltiples señales en una señal final
        Args:
            signals: Lista de tuplas (estrategia, señal)
        Returns:
            Señal consolidada
        """
        # Calcular consenso ponderado
        buy_score = 0.0
        sell_score = 0.0
        neutral_score = 0.0
        all_reasons = []
        
        for strategy_name, signal in signals:
            weight = self.strategy_weights.get(strategy_name, 0.1)
            weighted_strength = signal.strength * weight
            
            if signal.direction == SignalDirection.BUY:
                buy_score += weighted_strength
            elif signal.direction == SignalDirection.SELL:
                sell_score += weighted_strength
            else:
                neutral_score += weighted_strength
            
            # Agregar razones con el nombre de la estrategia
            for reason in signal.reasons:
                all_reasons.append(f"[{strategy_name}] {reason}")
        
        # Determinar dirección final
        if buy_score > sell_score and buy_score > 0.3:
            direction = SignalDirection.BUY
            strength = min(buy_score, 1.0)
        elif sell_score > buy_score and sell_score > 0.3:
            direction = SignalDirection.SELL
            strength = min(sell_score, 1.0)
        else:
            direction = SignalDirection.NEUTRAL
            strength = 0.0
        
        # Calcular confianza basada en consenso
        total_signals = len(signals)
        if total_signals > 0:
            agreeing_signals = sum(1 for _, s in signals if s.direction == direction)
            confidence = agreeing_signals / total_signals
        else:
            confidence = 0.0
        
        # Tomar precio de entrada de la primera señal válida
        entry_price = None
        stop_loss = None
        take_profit = None
        
        for _, signal in signals:
            if signal.direction == direction:
                if entry_price is None:
                    entry_price = signal.entry_price
                if stop_loss is None:
                    stop_loss = signal.stop_loss
                if take_profit is None:
                    take_profit = signal.take_profit
        
        return TradingSignal(
            direction=direction,
            strength=strength,
            confidence=confidence,
            strategy='consolidated',
            reasons=all_reasons[:5],  # Limitar a 5 razones principales
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def _neutral_signal(self) -> Dict:
        """Retorna una señal neutral"""
        return TradingSignal(
            direction=SignalDirection.NEUTRAL,
            strength=0.0,
            confidence=0.0,
            strategy='none',
            reasons=['Sin señal clara']
        ).to_dict()

# Testing
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear generador
    generator = SignalGenerator()
    
    # Crear datos de prueba
    import numpy as np
    
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    prices = 50000 + np.cumsum(np.random.randn(100) * 100)
    
    data = pd.DataFrame({
        'datetime': dates,
        'open': prices + np.random.randn(100) * 50,
        'high': prices + np.abs(np.random.randn(100) * 100),
        'low': prices - np.abs(np.random.randn(100) * 100),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })
    data.set_index('datetime', inplace=True)
    
    # Agregar indicadores básicos
    data['sma_20'] = data['close'].rolling(20).mean()
    data['sma_50'] = data['close'].rolling(50).mean()
    data['rsi'] = 50 + np.random.randn(100) * 20
    data['macd'] = np.random.randn(100) * 10
    data['macd_signal'] = data['macd'].rolling(9).mean()
    data['macd_histogram'] = data['macd'] - data['macd_signal']
    data['bb_middle'] = data['close'].rolling(20).mean()
    data['bb_upper'] = data['bb_middle'] + data['close'].rolling(20).std() * 2
    data['bb_lower'] = data['bb_middle'] - data['close'].rolling(20).std() * 2
    data['atr'] = np.random.rand(100) * 100 + 50
    data['volume_sma'] = data['volume'].rolling(20).mean()
    
    # Generar señal
    signal = generator.generate(data)
    
    print("\n📊 SEÑAL GENERADA:")
    print(f"Dirección: {signal['direction']}")
    print(f"Fuerza: {signal['strength']:.2f}")
    print(f"Confianza: {signal['confidence']:.2f}")
    print(f"Estrategia: {signal['strategy']}")
    print(f"Razones:")
    for reason in signal['reasons']:
        print(f"  - {reason}")
    
    if signal['entry_price']:
        print(f"\nPrecio entrada: ${signal['entry_price']:.2f}")
        print(f"Stop Loss: ${signal['stop_loss']:.2f}")
        print(f"Take Profit: ${signal['take_profit']:.2f}")
