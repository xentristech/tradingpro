"""
Trading Bot Mejorado con todas las nuevas características
Versión 2.0 - Basado en análisis XAU/USD
Author: XentrisTech
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Configurar path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_bot_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Nuevos módulos avanzados
from data.advanced.critical_change_detector import CriticalChangeDetector, CriticalAlert
from data.advanced.multi_timeframe_analyzer import MultiTimeframeAnalyzer, TimeframeSignal
from risk.advanced.adaptive_risk_manager import AdaptiveRiskManager, RiskParameters

# Módulos existentes
from core.mt5_connection import MT5Connection
from data.twelvedata import get_time_series
from notifiers.telegram_notifier import TelegramNotifier
from broker.mt5_connector import MT5Connector

class EnhancedTradingBotV2:
    """
    Bot de trading con detección avanzada de cambios críticos
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa el bot mejorado
        
        Args:
            config: Diccionario de configuración
        """
        # Cargar configuración
        if config is None:
            config = self._load_config()
        
        self.config = config
        self.symbol = config.get('symbol', 'XAUUSD')
        self.is_live = config.get('live_trading', False)
        
        logger.info(f"Iniciando Enhanced Trading Bot V2 para {self.symbol}")
        logger.info(f"Modo: {'LIVE' if self.is_live else 'DEMO'}")
        
        # Inicializar componentes existentes
        try:
            self.mt5 = MT5Connection()
            self.broker = MT5Connector(config)
            self.notifier = TelegramNotifier(
                token=config.get('telegram_token'),
                chat_id=config.get('telegram_chat_id')
            )
        except Exception as e:
            logger.error(f"Error inicializando componentes base: {e}")
            
        # Inicializar nuevos componentes avanzados
        self.change_detector = CriticalChangeDetector(
            symbol=self.symbol,
            sensitivity=config.get('sensitivity', 0.7)
        )
        
        self.mtf_analyzer = MultiTimeframeAnalyzer(self.symbol)
        
        self.risk_manager = AdaptiveRiskManager(
            account_balance=config.get('initial_capital', 10000),
            base_risk_pct=config.get('base_risk', 0.01),
            max_risk_pct=config.get('max_risk', 0.03),
            max_positions=config.get('max_positions', 3),
            data_file='data/risk_history.json'
        )
        
        # Estado del bot
        self.running = False
        self.last_alert_time = None
        self.positions = []
        self.market_data = {}
        self.last_signals = {}
        self.emergency_stop = False
        
        # Configuración de trading
        self.min_confidence = config.get('min_confidence', 60)
        self.min_alignment = config.get('min_alignment', 60)
        self.max_spread = config.get('max_spread', 5)
        
        # Timeframes a analizar
        self.timeframes = ['5min', '15min', '1h', '4h', '1day']
        
    def _load_config(self) -> Dict:
        """Carga configuración desde archivo .env"""
        from dotenv import load_dotenv
        
        load_dotenv('configs/.env')
        
        return {
            'symbol': os.getenv('SYMBOL', 'BTCUSD'),
            'twelvedata_api_key': os.getenv('TWELVEDATA_API_KEY'),
            'twelvedata_symbol': os.getenv('TWELVEDATA_SYMBOL', 'BTC/USD'),
            'telegram_token': os.getenv('TELEGRAM_TOKEN'),
            'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
            'live_trading': os.getenv('LIVE_TRADING', 'false').lower() == 'true',
            'initial_capital': float(os.getenv('INITIAL_CAPITAL', '10000')),
            'base_risk': float(os.getenv('BASE_RISK', '0.01')),
            'max_risk': float(os.getenv('MAX_RISK', '0.03')),
            'sensitivity': float(os.getenv('SENSITIVITY', '0.7')),
            'min_confidence': float(os.getenv('MIN_CONFIDENCE', '60')),
            'min_alignment': float(os.getenv('MIN_ALIGNMENT', '60')),
            'max_positions': int(os.getenv('MAX_POSITIONS', '3')),
            'max_spread': float(os.getenv('MAX_SPREAD', '5'))
        }
    
    async def start(self):
        """Inicia el bot"""
        self.running = True
        logger.info("Bot iniciado correctamente")
        
        # Enviar notificación de inicio
        await self.notifier.send_message(
            f"🤖 Enhanced Trading Bot V2 Iniciado\n"
            f"Símbolo: {self.symbol}\n"
            f"Modo: {'LIVE ⚠️' if self.is_live else 'DEMO 📊'}\n"
            f"Capital: ${self.risk_manager.account_balance:,.2f}\n"
            f"Riesgo por trade: {self.risk_manager.base_risk_pct:.1%}"
        )
        
        # Loop principal
        cycle_count = 0
        while self.running and not self.emergency_stop:
            try:
                cycle_count += 1
                logger.info(f"=== Ciclo de Trading #{cycle_count} ===")
                
                await self._trading_cycle()
                
                # Esperar antes del próximo ciclo
                await asyncio.sleep(60)  # 1 minuto entre ciclos
                
            except KeyboardInterrupt:
                logger.info("Interrupción por usuario")
                break
            except Exception as e:
                logger.error(f"Error en ciclo de trading: {e}", exc_info=True)
                await self.notifier.send_message(f"❌ Error: {e}")
                await asyncio.sleep(300)  # Esperar 5 minutos en error
        
        await self.stop()
    
    async def _trading_cycle(self):
        """Ciclo principal de trading con análisis avanzado"""
        
        # 1. Obtener datos multi-temporales
        logger.info("1. Obteniendo datos del mercado...")
        self.market_data = await self._fetch_multi_timeframe_data()
        
        if not self.market_data:
            logger.warning("No se pudieron obtener datos del mercado")
            return
        
        # 2. Detectar cambios críticos
        logger.info("2. Escaneando cambios críticos...")
        alerts = self.change_detector.run_full_scan(self.market_data)
        
        if alerts:
            logger.warning(f"Detectadas {len(alerts)} alertas críticas")
            for alert in alerts[:3]:  # Mostrar máximo 3 alertas
                logger.warning(f"  - {alert.severity}: {alert.message}")
        
        # 3. Procesar alertas críticas
        for alert in alerts:
            await self._process_critical_alert(alert)
        
        # 4. Análisis multi-temporal
        logger.info("3. Analizando múltiples temporalidades...")
        mtf_signals = self.mtf_analyzer.analyze_all_timeframes(self.market_data)
        consensus = self.mtf_analyzer.get_consensus_signal(mtf_signals)
        
        logger.info(f"Consenso: {consensus['direction']} "
                   f"(Fuerza: {consensus['strength']:.1f}%, "
                   f"Confianza: {consensus['confidence']:.1f}%, "
                   f"Alineación: {consensus['alignment']:.1f}%)")
        
        # Guardar señales
        self.last_signals = {
            'mtf_signals': mtf_signals,
            'consensus': consensus,
            'alerts': alerts,
            'timestamp': datetime.now()
        }
        
        # 5. Evaluación de posiciones existentes
        await self._evaluate_positions(consensus, alerts)
        
        # 6. Búsqueda de nuevas oportunidades (solo si no hay alertas críticas)
        critical_alerts = [a for a in alerts if a.severity == 'CRITICAL']
        if not critical_alerts:
            await self._look_for_opportunities(consensus, mtf_signals)
        else:
            logger.warning("Saltando búsqueda de oportunidades por alertas críticas")
        
        # 7. Actualizar estado y reportar
        await self._update_status(consensus, alerts)
    
    async def _fetch_multi_timeframe_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de múltiples temporalidades"""
        data = {}
        
        # Mapeo de timeframes para TwelveData
        timeframe_map = {
            '5min': '5min',
            '15min': '15min',
            '1h': '1h',
            '4h': '4h',
            '1day': '1day'
        }
        
        for tf_key, tf_value in timeframe_map.items():
            try:
                # Obtener datos de TwelveData
                df = get_time_series(
                    symbol=self.config.get('twelvedata_symbol', self.symbol),
                    interval=tf_value,
                    outputsize=100,
                    api_key=self.config['twelvedata_api_key']
                )
                
                if df is not None and not df.empty:
                    # Calcular indicadores
                    df = self._calculate_indicators(df)
                    data[tf_key] = df
                    logger.debug(f"Datos {tf_key}: {len(df)} velas")
                    
            except Exception as e:
                logger.error(f"Error obteniendo datos {tf_key}: {e}")
        
        return data
    
    async def _process_critical_alert(self, alert: CriticalAlert):
        """Procesa una alerta crítica"""
        logger.warning(f"Procesando alerta {alert.severity}: {alert.type}")
        
        # Notificar
        emoji_map = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': 'ℹ️'
        }
        
        message = f"{emoji_map.get(alert.severity, '❗')} **{alert.severity}**\n"
        message += f"{alert.message}\n"
        message += f"Acción: {alert.action}"
        
        await self.notifier.send_message(message)
        
        # Acciones según severidad y tipo
        if alert.severity == 'CRITICAL':
            if alert.action == 'CLOSE_ALL':
                await self._close_all_positions("Alerta CRÍTICA detectada")
                self.emergency_stop = True  # Detener trading
            elif alert.action == 'STOP_TRADING':
                self.emergency_stop = True
                logger.critical("Trading detenido por alerta crítica")
                
        elif alert.severity == 'HIGH':
            if alert.action == 'CLOSE_LONGS':
                await self._close_positions_by_type('buy')
            elif alert.action == 'CLOSE_SHORTS':
                await self._close_positions_by_type('sell')
            elif alert.action == 'REDUCE_POSITION':
                await self._reduce_positions(0.5)  # Reducir 50%
            elif alert.action == 'ADJUST_STOPS':
                new_stop = alert.indicators.get('next_target')
                await self._tighten_stops(new_stop)
                
        elif alert.severity == 'MEDIUM':
            if alert.action == 'TIGHTEN_STOPS':
                await self._tighten_stops()
            elif alert.action == 'REDUCE_SIZE':
                await self._reduce_positions(0.25)  # Reducir 25%
    
    async def _evaluate_positions(self, consensus: Dict, alerts: List[CriticalAlert]):
        """Evalúa posiciones existentes"""
        if not self.positions:
            return
        
        for position in self.positions[:]:  # Copia para poder modificar
            try:
                # Verificar si hay alertas que afecten la posición
                critical_alerts = [a for a in alerts if a.severity in ['HIGH', 'CRITICAL']]
                
                if critical_alerts:
                    # Evaluar si cerrar
                    should_close, reason = self._should_close_position(position, critical_alerts, consensus)
                    
                    if should_close:
                        await self._close_position(position, reason)
                    else:
                        # Ajustar stop loss
                        new_sl = self._calculate_dynamic_stop(position, self.market_data.get('1h', pd.DataFrame()))
                        if new_sl and abs(new_sl - position.get('sl', 0)) > 0.0001:
                            await self._modify_position_stop(position, new_sl)
                
                # Evaluar trailing stop
                await self._update_trailing_stop(position)
                
            except Exception as e:
                logger.error(f"Error evaluando posición {position.get('ticket')}: {e}")
    
    async def _look_for_opportunities(self, consensus: Dict, signals: Dict[str, TimeframeSignal]):
        """Busca nuevas oportunidades de trading"""
        
        # Verificar condiciones mínimas
        if consensus['confidence'] < self.min_confidence:
            logger.info(f"Confianza insuficiente ({consensus['confidence']:.1f}% < {self.min_confidence}%)")
            return
        
        if consensus['alignment'] < self.min_alignment:
            logger.info(f"Alineación insuficiente ({consensus['alignment']:.1f}% < {self.min_alignment}%)")
            return
        
        # Verificar que no estemos en máximo de posiciones
        if len(self.positions) >= self.risk_manager.max_positions:
            logger.info(f"Máximo de posiciones alcanzado ({len(self.positions)}/{self.risk_manager.max_positions})")
            return
        
        # Preparar condiciones de mercado para risk manager
        market_conditions = self._prepare_market_conditions(signals, consensus)
        
        # Determinar entrada
        signal_type = None
        entry_price = self._get_current_price()
        
        if consensus['direction'] == 'BULLISH' and consensus['strength'] > 65:
            signal_type = 'BUY'
            stop_loss = self._find_stop_level('long', entry_price)
            
        elif consensus['direction'] == 'BEARISH' and consensus['strength'] > 65:
            signal_type = 'SELL'
            stop_loss = self._find_stop_level('short', entry_price)
        
        if signal_type:
            # Calcular parámetros de riesgo
            risk_params = self.risk_manager.calculate_dynamic_position_size(
                entry_price=entry_price,
                stop_loss=stop_loss,
                market_conditions=market_conditions,
                symbol=self.symbol
            )
            
            # Verificar si la confianza es suficiente
            if risk_params.confidence_level >= self.min_confidence:
                await self._execute_trade(signal_type, risk_params, consensus)
            else:
                logger.info(f"Confianza de riesgo insuficiente: {risk_params.confidence_level:.1f}%")
    
    async def _execute_trade(self, signal_type: str, risk_params: RiskParameters, consensus: Dict):
        """Ejecuta una operación"""
        
        # Verificar spread
        current_spread = await self._get_spread()
        if current_spread > self.max_spread:
            logger.warning(f"Spread muy alto: {current_spread} > {self.max_spread}")
            return
        
        # Preparar orden
        order = {
            'symbol': self.symbol,
            'type': signal_type.lower(),
            'volume': risk_params.position_size,
            'price': risk_params.entry_price,
            'sl': risk_params.stop_loss,
            'tp': risk_params.take_profit,
            'comment': f"EBv2_{consensus['alignment']:.0f}%_C{risk_params.confidence_level:.0f}"
        }
        
        # Log detallado
        logger.info(f"""
        📊 EJECUTANDO OPERACIÓN:
        Tipo: {signal_type}
        Símbolo: {self.symbol}
        Precio: {risk_params.entry_price:.5f}
        Tamaño: {risk_params.position_size:.4f}
        Stop Loss: {risk_params.stop_loss:.5f} ({abs(risk_params.entry_price - risk_params.stop_loss)/risk_params.entry_price*100:.2f}%)
        Take Profit: {risk_params.take_profit:.5f} ({abs(risk_params.take_profit - risk_params.entry_price)/risk_params.entry_price*100:.2f}%)
        R:R Ratio: 1:{risk_params.risk_reward_ratio:.1f}
        Riesgo: {risk_params.risk_per_trade:.2%}
        Confianza: {risk_params.confidence_level:.0f}%
        Consenso: {consensus['direction']} ({consensus['strength']:.1f}%)
        """)
        
        # Notificar
        message = f"📊 **Nueva Operación**\n"
        message += f"Símbolo: {self.symbol}\n"
        message += f"Tipo: {signal_type}\n"
        message += f"Precio: {risk_params.entry_price:.5f}\n"
        message += f"SL: {risk_params.stop_loss:.5f}\n"
        message += f"TP: {risk_params.take_profit:.5f}\n"
        message += f"Riesgo: {risk_params.risk_per_trade:.2%}\n"
        message += f"Confianza: {risk_params.confidence_level:.0f}%"
        
        await self.notifier.send_message(message)
        
        # Ejecutar si es live
        if self.is_live:
            try:
                result = await self.broker.place_order(order)
                
                if result and result.get('success'):
                    # Añadir a posiciones
                    position = {
                        'ticket': result.get('ticket'),
                        'symbol': self.symbol,
                        'type': signal_type.lower(),
                        'entry_price': risk_params.entry_price,
                        'position_size': risk_params.position_size,
                        'sl': risk_params.stop_loss,
                        'tp': risk_params.take_profit,
                        'entry_time': datetime.now(),
                        'risk_params': risk_params
                    }
                    
                    self.positions.append(position)
                    self.risk_manager.add_position({
                        'id': str(result.get('ticket')),
                        'symbol': self.symbol,
                        'direction': signal_type.lower(),
                        'entry_price': risk_params.entry_price,
                        'position_size': risk_params.position_size,
                        'entry_time': datetime.now()
                    })
                    
                    logger.info(f"Operación ejecutada exitosamente: Ticket #{result.get('ticket')}")
                else:
                    logger.error(f"Error ejecutando operación: {result}")
                    
            except Exception as e:
                logger.error(f"Error ejecutando orden: {e}")
        else:
            logger.info("MODO DEMO - Operación simulada (no ejecutada)")
            
            # Simular posición en demo
            position = {
                'ticket': f"DEMO_{datetime.now().timestamp()}",
                'symbol': self.symbol,
                'type': signal_type.lower(),
                'entry_price': risk_params.entry_price,
                'position_size': risk_params.position_size,
                'sl': risk_params.stop_loss,
                'tp': risk_params.take_profit,
                'entry_time': datetime.now(),
                'risk_params': risk_params
            }
            self.positions.append(position)
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos"""
        
        if len(df) < 20:
            return df
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'])
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volume
        if 'volume' in df.columns:
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _prepare_market_conditions(self, signals: Dict[str, TimeframeSignal], consensus: Dict) -> Dict:
        """Prepara condiciones de mercado para el risk manager"""
        
        # Obtener datos del timeframe principal (1h)
        df_1h = self.market_data.get('1h', pd.DataFrame())
        
        conditions = {
            'atr': df_1h['atr'].iloc[-1] if 'atr' in df_1h.columns and len(df_1h) > 0 else 0,
            'avg_atr': df_1h['atr'].mean() if 'atr' in df_1h.columns and len(df_1h) > 20 else 0,
            'rsi': df_1h['rsi'].iloc[-1] if 'rsi' in df_1h.columns and len(df_1h) > 0 else 50,
            'timeframe_alignment': consensus.get('alignment', 50),
            'signal_quality': consensus.get('quality', 50),
            'trend_strength': consensus.get('strength', 50),
            'volume_confirmation': False,
            'pattern_confirmation': False,
            'divergence_detected': False,
            'volatility_spike': False,
            'trading_session': self._get_trading_session(),
            'technical_confirmations': 0
        }
        
        # Verificar volumen
        if '1h' in signals:
            conditions['volume_confirmation'] = signals['1h'].volume_ratio > 1.2
        
        # Verificar divergencias en alertas recientes
        if hasattr(self, 'last_signals') and 'alerts' in self.last_signals:
            for alert in self.last_signals['alerts']:
                if 'DIVERGENCE' in alert.type:
                    conditions['divergence_detected'] = True
                if 'VOLATILITY' in alert.type:
                    conditions['volatility_spike'] = True
        
        # Contar confirmaciones técnicas
        confirmations = 0
        if conditions['rsi'] > 30 and conditions['rsi'] < 70:
            confirmations += 1
        if conditions['timeframe_alignment'] > 60:
            confirmations += 2
        if conditions['volume_confirmation']:
            confirmations += 1
        
        conditions['technical_confirmations'] = confirmations
        
        # Calcular percentil de volatilidad
        if 'atr' in df_1h.columns and len(df_1h) >= 50:
            recent_atr = df_1h['atr'].iloc[-50:].values
            current_atr = conditions['atr']
            percentile = (recent_atr < current_atr).sum() / len(recent_atr) * 100
            conditions['volatility_percentile'] = percentile
        else:
            conditions['volatility_percentile'] = 50
        
        return conditions
    
    def _get_current_price(self) -> float:
        """Obtiene el precio actual"""
        # Intentar desde datos más recientes
        for tf in ['5min', '15min', '1h']:
            if tf in self.market_data and len(self.market_data[tf]) > 0:
                return self.market_data[tf]['close'].iloc[-1]
        
        # Si no hay datos, usar MT5
        try:
            tick = self.mt5.get_symbol_info_tick(self.symbol)
            if tick:
                return (tick.bid + tick.ask) / 2
        except:
            pass
        
        return 0
    
    def _find_stop_level(self, direction: str, entry_price: float) -> float:
        """Encuentra nivel de stop loss dinámico"""
        
        # Obtener ATR para stop dinámico
        atr = 0
        for tf in ['1h', '4h', '1day']:
            if tf in self.market_data and 'atr' in self.market_data[tf].columns:
                atr = self.market_data[tf]['atr'].iloc[-1]
                break
        
        # Si no hay ATR, usar porcentaje fijo
        if atr == 0:
            atr = entry_price * 0.01  # 1% default
        
        # Multiplicador según dirección y condiciones
        multiplier = 1.5  # Default
        
        # Ajustar por volatilidad
        if hasattr(self, 'last_signals') and 'consensus' in self.last_signals:
            volatility_percentile = self.last_signals.get('volatility_percentile', 50)
            if volatility_percentile > 75:
                multiplier = 2.0
            elif volatility_percentile < 25:
                multiplier = 1.0
        
        if direction == 'long':
            stop_loss = entry_price - (atr * multiplier)
            
            # Buscar soporte cercano
            for tf in ['1h', '4h']:
                if tf in self.market_data and len(self.market_data[tf]) >= 20:
                    recent_low = self.market_data[tf]['low'].iloc[-20:].min()
                    if recent_low < stop_loss and recent_low > entry_price * 0.97:
                        stop_loss = recent_low - (entry_price * 0.0005)  # Pequeño buffer
                        break
        else:  # short
            stop_loss = entry_price + (atr * multiplier)
            
            # Buscar resistencia cercana
            for tf in ['1h', '4h']:
                if tf in self.market_data and len(self.market_data[tf]) >= 20:
                    recent_high = self.market_data[tf]['high'].iloc[-20:].max()
                    if recent_high > stop_loss and recent_high < entry_price * 1.03:
                        stop_loss = recent_high + (entry_price * 0.0005)  # Pequeño buffer
                        break
        
        return stop_loss
    
    def _should_close_position(self, 
                              position: Dict, 
                              alerts: List[CriticalAlert],
                              consensus: Dict) -> Tuple[bool, str]:
        """Determina si se debe cerrar una posición"""
        
        # Verificar alertas críticas
        for alert in alerts:
            if alert.severity == 'CRITICAL':
                return True, f"Alerta crítica: {alert.type}"
            
            if alert.severity == 'HIGH':
                # Cerrar longs en señales bajistas
                if position['type'] == 'buy' and alert.action in ['CLOSE_LONGS', 'CLOSE_ALL']:
                    return True, f"Alerta HIGH: {alert.message}"
                
                # Cerrar shorts en señales alcistas
                if position['type'] == 'sell' and alert.action in ['CLOSE_SHORTS', 'CLOSE_ALL']:
                    return True, f"Alerta HIGH: {alert.message}"
        
        # Verificar cambio de dirección fuerte
        if consensus['confidence'] > 70:
            if position['type'] == 'buy' and consensus['direction'] == 'BEARISH':
                return True, "Cambio de dirección a BEARISH con alta confianza"
            if position['type'] == 'sell' and consensus['direction'] == 'BULLISH':
                return True, "Cambio de dirección a BULLISH con alta confianza"
        
        return False, ""
    
    def _calculate_dynamic_stop(self, position: Dict, df: pd.DataFrame) -> Optional[float]:
        """Calcula stop loss dinámico"""
        
        if df.empty or 'atr' not in df.columns:
            return None
        
        current_price = self._get_current_price()
        atr = df['atr'].iloc[-1]
        
        if position['type'] == 'buy':
            # Para longs, stop por debajo del precio actual
            new_stop = current_price - (atr * 1.5)
            
            # Solo mover stop si es mayor que el actual (trailing)
            if new_stop > position.get('sl', 0):
                return new_stop
                
        else:  # sell
            # Para shorts, stop por encima del precio actual
            new_stop = current_price + (atr * 1.5)
            
            # Solo mover stop si es menor que el actual (trailing)
            if new_stop < position.get('sl', float('inf')):
                return new_stop
        
        return None
    
    async def _update_trailing_stop(self, position: Dict):
        """Actualiza trailing stop de una posición"""
        
        current_price = self._get_current_price()
        entry_price = position['entry_price']
        current_sl = position.get('sl', 0)
        
        # Calcular profit actual
        if position['type'] == 'buy':
            profit_pips = current_price - entry_price
            in_profit = profit_pips > 0
            
            # Si está en profit considerable, ajustar stop
            if in_profit and profit_pips > (entry_price * 0.005):  # 0.5% en profit
                # Mover stop a breakeven + pequeño profit
                new_sl = entry_price + (entry_price * 0.001)  # 0.1% de profit asegurado
                
                # Si ya pasó 1% de profit, trailing más agresivo
                if profit_pips > (entry_price * 0.01):
                    new_sl = current_price - (current_price * 0.005)  # Trail a 0.5%
                
                if new_sl > current_sl:
                    await self._modify_position_stop(position, new_sl)
                    
        else:  # sell
            profit_pips = entry_price - current_price
            in_profit = profit_pips > 0
            
            if in_profit and profit_pips > (entry_price * 0.005):
                new_sl = entry_price - (entry_price * 0.001)
                
                if profit_pips > (entry_price * 0.01):
                    new_sl = current_price + (current_price * 0.005)
                
                if new_sl < current_sl:
                    await self._modify_position_stop(position, new_sl)
    
    async def _close_position(self, position: Dict, reason: str):
        """Cierra una posición"""
        logger.info(f"Cerrando posición {position['ticket']}: {reason}")
        
        if self.is_live:
            try:
                result = await self.broker.close_position(position['ticket'])
                if result and result.get('success'):
                    # Actualizar risk manager
                    exit_price = result.get('price', self._get_current_price())
                    trade_result = self.risk_manager.close_position(
                        position_id=str(position['ticket']),
                        exit_price=exit_price,
                        exit_time=datetime.now()
                    )
                    
                    # Remover de posiciones
                    self.positions.remove(position)
                    
                    # Notificar
                    pnl = trade_result.pnl if trade_result else 0
                    message = f"📕 Posición Cerrada\n"
                    message += f"Razón: {reason}\n"
                    message += f"PnL: ${pnl:.2f}"
                    await self.notifier.send_message(message)
                    
            except Exception as e:
                logger.error(f"Error cerrando posición: {e}")
        else:
            # Modo demo - solo remover
            self.positions.remove(position)
            logger.info("DEMO - Posición cerrada")
    
    async def _close_all_positions(self, reason: str):
        """Cierra todas las posiciones abiertas"""
        if not self.positions:
            return
        
        logger.warning(f"Cerrando TODAS las posiciones: {reason}")
        
        for position in self.positions[:]:
            await self._close_position(position, reason)
    
    async def _close_positions_by_type(self, position_type: str):
        """Cierra posiciones de un tipo específico"""
        positions_to_close = [p for p in self.positions if p['type'] == position_type]
        
        for position in positions_to_close:
            await self._close_position(position, f"Cierre por tipo {position_type}")
    
    async def _reduce_positions(self, reduction_pct: float):
        """Reduce el tamaño de las posiciones"""
        logger.info(f"Reduciendo posiciones en {reduction_pct*100:.0f}%")
        
        for position in self.positions:
            # Aquí implementarías la lógica de reducción parcial
            # Por ahora, cerramos si la reducción es mayor al 40%
            if reduction_pct > 0.4:
                await self._close_position(position, f"Reducción {reduction_pct*100:.0f}%")
    
    async def _tighten_stops(self, target_level: Optional[float] = None):
        """Ajusta los stops de todas las posiciones"""
        for position in self.positions:
            if target_level:
                await self._modify_position_stop(position, target_level)
            else:
                # Ajustar basado en ATR actual
                new_sl = self._calculate_dynamic_stop(
                    position,
                    self.market_data.get('1h', pd.DataFrame())
                )
                if new_sl:
                    await self._modify_position_stop(position, new_sl)
    
    async def _modify_position_stop(self, position: Dict, new_sl: float):
        """Modifica el stop loss de una posición"""
        if self.is_live:
            try:
                result = await self.broker.modify_position(
                    ticket=position['ticket'],
                    sl=new_sl,
                    tp=position.get('tp')
                )
                
                if result and result.get('success'):
                    position['sl'] = new_sl
                    logger.info(f"Stop modificado para {position['ticket']}: {new_sl:.5f}")
                    
            except Exception as e:
                logger.error(f"Error modificando stop: {e}")
        else:
            position['sl'] = new_sl
            logger.info(f"DEMO - Stop modificado: {new_sl:.5f}")
    
    async def _get_spread(self) -> float:
        """Obtiene el spread actual"""
        try:
            tick = self.mt5.get_symbol_info_tick(self.symbol)
            if tick:
                return tick.ask - tick.bid
        except:
            pass
        
        return 0
    
    def _get_trading_session(self) -> str:
        """Determina la sesión de trading actual"""
        from datetime import datetime
        import pytz
        
        try:
            utc_now = datetime.now(pytz.UTC)
            hour = utc_now.hour
            
            if 22 <= hour or hour < 7:
                return 'ASIA'
            elif 7 <= hour < 12:
                return 'LONDON'
            elif 12 <= hour < 21:
                return 'NEWYORK'
            else:
                return 'OVERLAP'
        except:
            return 'UNKNOWN'
    
    async def _update_status(self, consensus: Dict, alerts: List[CriticalAlert]):
        """Actualiza y reporta el estado del bot"""
        
        # Obtener métricas de riesgo
        risk_metrics = self.risk_manager.get_risk_metrics()
        
        # Resumen de alertas
        alert_summary = self.change_detector.get_alert_summary()
        
        # Log de estado cada 5 ciclos
        if not hasattr(self, '_status_counter'):
            self._status_counter = 0
        
        self._status_counter += 1
        
        if self._status_counter % 5 == 0:
            status_message = f"""
            📊 ESTADO DEL SISTEMA
            ========================
            Balance: ${risk_metrics['account_balance']:,.2f}
            PnL Total: ${risk_metrics['total_pnl']:,.2f} ({risk_metrics['total_return']:.1f}%)
            Posiciones Abiertas: {len(self.positions)}/{self.risk_manager.max_positions}
            
            📈 Performance:
            Win Rate: {risk_metrics['win_rate']:.1%}
            Trades Totales: {risk_metrics['total_trades']}
            Max Drawdown: {risk_metrics['max_drawdown']:.1f}%
            Sharpe Ratio: {risk_metrics['sharpe_ratio']}
            
            🎯 Señal Actual:
            Dirección: {consensus['direction']}
            Fuerza: {consensus['strength']:.1f}%
            Confianza: {consensus['confidence']:.1f}%
            
            ⚠️ Alertas Recientes:
            Críticas: {alert_summary['critical']}
            Altas: {alert_summary['high']}
            Medias: {alert_summary['medium']}
            """
            
            logger.info(status_message)
            
            # Enviar resumen cada 20 ciclos
            if self._status_counter % 20 == 0:
                await self.notifier.send_message(status_message)
    
    async def stop(self):
        """Detiene el bot de forma segura"""
        self.running = False
        
        logger.info("Deteniendo bot...")
        
        # Cerrar todas las posiciones
        if self.positions:
            await self._close_all_positions("Bot detenido")
        
        # Guardar estado final
        self.risk_manager._save_history()
        
        # Notificar
        await self.notifier.send_message(
            f"🛑 Bot Detenido\n"
            f"Balance Final: ${self.risk_manager.account_balance:,.2f}\n"
            f"PnL Total: ${self.risk_manager.total_pnl:,.2f}"
        )
        
        logger.info("Bot detenido correctamente")

# Punto de entrada
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Trading Bot V2')
    parser.add_argument('--live', action='store_true', help='Activar modo live')
    parser.add_argument('--symbol', default=None, help='Símbolo a operar')
    parser.add_argument('--debug', action='store_true', help='Modo debug')
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configuración opcional desde argumentos
    config_override = {}
    if args.live:
        config_override['live_trading'] = True
        print("⚠️ MODO LIVE ACTIVADO - SE EJECUTARÁN OPERACIONES REALES")
        response = input("¿Estás seguro? (yes/no): ")
        if response.lower() != 'yes':
            print("Operación cancelada")
            sys.exit(0)
    
    if args.symbol:
        config_override['symbol'] = args.symbol
    
    # Crear y ejecutar bot
    bot = EnhancedTradingBotV2(config_override)
    
    try:
        # Ejecutar bot
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\nBot detenido por usuario")
        asyncio.run(bot.stop())
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
