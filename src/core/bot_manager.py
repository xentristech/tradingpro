"""
Bot Manager - Sistema Central de Control del Trading Bot
Version: 3.0.0
"""
import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pandas as pd

# Configurar path
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from broker.mt5_connection import MT5Connection
from data.data_manager import DataManager
from signals.signal_generator import SignalGenerator
from risk.risk_manager import RiskManager
from ml.ml_predictor import MLPredictor
from notifiers.telegram_notifier import TelegramNotifier
from utils.logger_config import setup_logging

logger = logging.getLogger(__name__)

class BotManager:
    """
    Gestor principal del bot de trading
    Coordina todos los componentes del sistema
    """
    
    def __init__(self, config_path: str = 'configs/.env'):
        """
        Inicializa el bot manager
        Args:
            config_path: Ruta al archivo de configuración
        """
        # Configurar logging
        self.logger = setup_logging()
        
        # Cargar configuración
        from dotenv import load_dotenv
        load_dotenv(config_path)
        
        self.config = self._load_config()
        
        # Estado del bot
        self.is_running = False
        self.is_live = self.config['live_trading']
        self.symbol = self.config['symbol']
        
        # Inicializar componentes
        self._initialize_components()
        
        # Estadísticas
        self.stats = {
            'start_time': None,
            'trades_total': 0,
            'trades_won': 0,
            'trades_lost': 0,
            'profit_total': 0.0,
            'max_drawdown': 0.0
        }
        
        logger.info(f"BotManager inicializado - Símbolo: {self.symbol} - Live: {self.is_live}")
    
    def _load_config(self) -> Dict:
        """Carga la configuración del sistema"""
        return {
            'symbol': os.getenv('SYMBOL', 'BTCUSDm'),
            'twelvedata_symbol': os.getenv('TWELVEDATA_SYMBOL', 'BTC/USD'),
            'live_trading': os.getenv('LIVE_TRADING', 'false').lower() == 'true',
            'risk_per_trade': float(os.getenv('RISK_PER_TRADE', '0.01')),
            'max_concurrent_trades': int(os.getenv('MAX_CONCURRENT_TRADES', '1')),
            'def_sl_usd': float(os.getenv('DEF_SL_USD', '50')),
            'def_tp_usd': float(os.getenv('DEF_TP_USD', '100')),
            'telegram_enabled': os.getenv('TELEGRAM_TOKEN', '') != '',
            'ml_enabled': os.getenv('ML_ENABLED', 'true').lower() == 'true',
            'ollama_enabled': os.getenv('OLLAMA_API_BASE', '') != ''
        }
    
    def _initialize_components(self):
        """Inicializa todos los componentes del sistema"""
        logger.info("Inicializando componentes...")
        
        # Broker
        try:
            self.broker = MT5Connection()
            logger.info("✅ Broker MT5 inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando MT5: {e}")
            self.broker = None
        
        # Data Manager
        try:
            self.data_manager = DataManager(self.config)
            logger.info("✅ Data Manager inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Data Manager: {e}")
            self.data_manager = None
        
        # Signal Generator
        try:
            self.signal_generator = SignalGenerator()
            logger.info("✅ Signal Generator inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Signal Generator: {e}")
            self.signal_generator = None
        
        # Risk Manager
        try:
            initial_capital = self._get_account_balance()
            self.risk_manager = RiskManager(
                initial_capital=initial_capital,
                risk_per_trade=self.config['risk_per_trade']
            )
            logger.info("✅ Risk Manager inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Risk Manager: {e}")
            self.risk_manager = None
        
        # ML Predictor (opcional)
        if self.config['ml_enabled']:
            try:
                self.ml_predictor = MLPredictor()
                logger.info("✅ ML Predictor inicializado")
            except Exception as e:
                logger.warning(f"⚠️ ML Predictor no disponible: {e}")
                self.ml_predictor = None
        else:
            self.ml_predictor = None
        
        # Notifier
        if self.config['telegram_enabled']:
            try:
                self.notifier = TelegramNotifier()
                logger.info("✅ Telegram Notifier inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Telegram no disponible: {e}")
                self.notifier = None
        else:
            self.notifier = None
    
    def _get_account_balance(self) -> float:
        """Obtiene el balance de la cuenta"""
        if self.broker and self.broker.connect():
            account = self.broker.get_account_info()
            if account:
                return account.balance
        return 10000.0  # Default
    
    async def start(self):
        """Inicia el bot de trading"""
        logger.info("🚀 Iniciando Bot de Trading...")
        
        # Verificar componentes críticos
        if not self._check_critical_components():
            logger.error("❌ Componentes críticos no disponibles")
            return False
        
        # Conectar broker
        if self.broker and not self.broker.connect():
            logger.error("❌ No se pudo conectar al broker")
            return False
        
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        # Notificar inicio
        await self._notify(
            f"🤖 Bot Iniciado\n"
            f"Símbolo: {self.symbol}\n"
            f"Modo: {'LIVE' if self.is_live else 'DEMO'}\n"
            f"Balance: ${self._get_account_balance():.2f}"
        )
        
        logger.info("✅ Bot iniciado correctamente")
        
        # Loop principal
        await self._trading_loop()
        
        return True
    
    def _check_critical_components(self) -> bool:
        """Verifica que los componentes críticos estén disponibles"""
        critical = [
            (self.broker, "Broker"),
            (self.data_manager, "Data Manager"),
            (self.signal_generator, "Signal Generator"),
            (self.risk_manager, "Risk Manager")
        ]
        
        for component, name in critical:
            if component is None:
                logger.error(f"❌ Componente crítico no disponible: {name}")
                return False
        
        return True
    
    async def _trading_loop(self):
        """Loop principal de trading"""
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                logger.info(f"\n{'='*50}")
                logger.info(f"Ciclo #{cycle_count} - {datetime.now()}")
                logger.info(f"{'='*50}")
                
                # Ejecutar ciclo de trading
                await self._execute_trading_cycle()
                
                # Esperar antes del siguiente ciclo
                await asyncio.sleep(60)  # 1 minuto
                
            except KeyboardInterrupt:
                logger.info("⚠️ Interrupción por usuario")
                break
                
            except Exception as e:
                logger.error(f"❌ Error en trading loop: {e}", exc_info=True)
                await self._notify(f"❌ Error: {str(e)[:200]}")
                await asyncio.sleep(300)  # 5 minutos en caso de error
    
    async def _execute_trading_cycle(self):
        """Ejecuta un ciclo completo de trading"""
        
        # 1. Obtener datos de mercado
        logger.info("📊 Obteniendo datos de mercado...")
        market_data = await self._get_market_data()
        
        if market_data is None:
            logger.warning("⚠️ No se pudieron obtener datos de mercado")
            return
        
        # 2. Generar señales
        logger.info("📈 Generando señales...")
        signals = self._generate_signals(market_data)
        
        # 3. Obtener predicción ML (si está habilitado)
        ml_prediction = None
        if self.ml_predictor:
            logger.info("🤖 Obteniendo predicción ML...")
            ml_prediction = self._get_ml_prediction(market_data)
        
        # 4. Evaluar riesgo
        logger.info("⚖️ Evaluando riesgo...")
        risk_assessment = self._assess_risk(signals, ml_prediction)
        
        # 5. Gestionar posiciones existentes
        await self._manage_positions()
        
        # 6. Ejecutar nuevas operaciones
        if risk_assessment['trade_allowed']:
            await self._execute_trades(signals, risk_assessment)
        
        # 7. Actualizar estadísticas
        self._update_stats()
        
        # 8. Reportar estado
        await self._report_status()
    
    async def _get_market_data(self) -> Optional[pd.DataFrame]:
        """Obtiene datos de mercado actualizados"""
        if not self.data_manager:
            return None
        
        try:
            # Obtener datos de múltiples timeframes
            data = {}
            timeframes = ['5min', '15min', '1h', '4h']
            
            for tf in timeframes:
                df = await self.data_manager.get_data(
                    symbol=self.config['twelvedata_symbol'],
                    interval=tf,
                    outputsize=100
                )
                if df is not None:
                    data[tf] = df
            
            return data if data else None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos: {e}")
            return None
    
    def _generate_signals(self, market_data: Dict) -> Dict:
        """Genera señales de trading"""
        if not self.signal_generator or not market_data:
            return {}
        
        try:
            signals = {}
            
            for timeframe, data in market_data.items():
                signal = self.signal_generator.generate(data)
                signals[timeframe] = signal
            
            # Consenso de señales
            consensus = self._calculate_signal_consensus(signals)
            signals['consensus'] = consensus
            
            logger.info(f"📊 Señales generadas: {consensus}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generando señales: {e}")
            return {}
    
    def _calculate_signal_consensus(self, signals: Dict) -> str:
        """Calcula el consenso de múltiples señales"""
        if not signals:
            return 'neutral'
        
        votes = {'buy': 0, 'sell': 0, 'neutral': 0}
        
        # Pesos por timeframe
        weights = {
            '5min': 0.15,
            '15min': 0.25,
            '1h': 0.35,
            '4h': 0.25
        }
        
        for tf, signal in signals.items():
            if tf in weights and 'direction' in signal:
                direction = signal['direction']
                strength = signal.get('strength', 0.5)
                weight = weights[tf]
                
                if direction in votes:
                    votes[direction] += weight * strength
        
        # Determinar consenso
        max_vote = max(votes.values())
        threshold = 0.3
        
        if max_vote < threshold:
            return 'neutral'
        
        for direction, vote in votes.items():
            if vote == max_vote:
                return direction
        
        return 'neutral'
    
    def _get_ml_prediction(self, market_data: Dict) -> Optional[Dict]:
        """Obtiene predicción del modelo ML"""
        if not self.ml_predictor or not market_data:
            return None
        
        try:
            # Usar datos de 1h para predicción
            if '1h' in market_data:
                prediction = self.ml_predictor.predict(market_data['1h'])
                logger.info(f"🤖 Predicción ML: {prediction}")
                return prediction
                
        except Exception as e:
            logger.warning(f"Error en predicción ML: {e}")
        
        return None
    
    def _assess_risk(self, signals: Dict, ml_prediction: Optional[Dict]) -> Dict:
        """Evalúa el riesgo de la operación"""
        if not self.risk_manager:
            return {'trade_allowed': False, 'reason': 'Risk manager not available'}
        
        try:
            # Obtener posiciones actuales
            positions = []
            if self.broker:
                positions = self.broker.get_positions(self.symbol)
            
            # Evaluar riesgo
            assessment = self.risk_manager.evaluate_trade(
                symbol=self.symbol,
                signal_strength=signals.get('consensus', 'neutral'),
                current_positions=len(positions),
                max_positions=self.config['max_concurrent_trades']
            )
            
            logger.info(f"⚖️ Evaluación de riesgo: {assessment}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error evaluando riesgo: {e}")
            return {'trade_allowed': False, 'reason': str(e)}
    
    async def _manage_positions(self):
        """Gestiona posiciones abiertas"""
        if not self.broker:
            return
        
        positions = self.broker.get_positions(self.symbol)
        
        for position in positions:
            try:
                # Evaluar si cerrar posición
                should_close, reason = self._should_close_position(position)
                
                if should_close:
                    logger.info(f"📉 Cerrando posición {position.ticket}: {reason}")
                    if self.broker.close_position(position.ticket):
                        await self._notify(
                            f"📉 Posición cerrada\n"
                            f"Ticket: {position.ticket}\n"
                            f"Profit: ${position.profit:.2f}\n"
                            f"Razón: {reason}"
                        )
                
                # Actualizar trailing stop si aplica
                else:
                    self._update_trailing_stop(position)
                    
            except Exception as e:
                logger.error(f"Error gestionando posición {position.ticket}: {e}")
    
    def _should_close_position(self, position) -> Tuple[bool, str]:
        """Determina si una posición debe cerrarse"""
        # Lógica para determinar cierre
        # Por ahora, solo cerrar si hay señal contraria fuerte
        return False, ""
    
    def _update_trailing_stop(self, position):
        """Actualiza trailing stop de una posición"""
        # Implementar lógica de trailing stop
        pass
    
    async def _execute_trades(self, signals: Dict, risk_assessment: Dict):
        """Ejecuta nuevas operaciones"""
        if not self.broker or not signals:
            return
        
        consensus = signals.get('consensus', 'neutral')
        
        if consensus == 'neutral':
            logger.info("📊 Sin señal clara, esperando...")
            return
        
        try:
            # Calcular tamaño de posición
            position_size = self.risk_manager.calculate_position_size(
                symbol=self.symbol,
                stop_loss_pips=50  # Default
            )
            
            # Obtener precio actual
            tick = self.broker.get_tick(self.symbol)
            if not tick:
                logger.error("No se pudo obtener precio actual")
                return
            
            # Preparar orden
            order_type = 'buy' if consensus == 'buy' else 'sell'
            price = tick.ask if order_type == 'buy' else tick.bid
            
            # Calcular SL y TP
            pip_value = 0.0001 if 'JPY' not in self.symbol else 0.01
            sl_distance = 50 * pip_value
            tp_distance = 100 * pip_value
            
            if order_type == 'buy':
                sl = price - sl_distance
                tp = price + tp_distance
            else:
                sl = price + sl_distance
                tp = price - tp_distance
            
            # Ejecutar orden
            logger.info(f"📈 Ejecutando {order_type.upper()} {position_size} {self.symbol}")
            
            if self.is_live:
                result = self.broker.place_order(
                    symbol=self.symbol,
                    order_type=order_type,
                    volume=position_size,
                    sl=sl,
                    tp=tp,
                    comment=f"AlgoBot-{consensus}"
                )
                
                if result:
                    self.stats['trades_total'] += 1
                    await self._notify(
                        f"✅ Nueva operación\n"
                        f"Tipo: {order_type.upper()}\n"
                        f"Símbolo: {self.symbol}\n"
                        f"Volumen: {position_size}\n"
                        f"Precio: {price:.5f}\n"
                        f"SL: {sl:.5f} | TP: {tp:.5f}"
                    )
            else:
                logger.info(f"📝 DEMO: {order_type.upper()} {position_size} @ {price:.5f}")
                
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
    
    def _update_stats(self):
        """Actualiza estadísticas del bot"""
        if not self.broker:
            return
        
        try:
            # Obtener historial reciente
            history = self.broker.get_history(days=1)
            
            if not history.empty:
                # Calcular estadísticas del día
                today_trades = history[history['time'].dt.date == datetime.now().date()]
                
                if not today_trades.empty:
                    self.stats['trades_today'] = len(today_trades)
                    self.stats['profit_today'] = today_trades['profit'].sum()
                    
        except Exception as e:
            logger.warning(f"Error actualizando estadísticas: {e}")
    
    async def _report_status(self):
        """Reporta el estado actual del bot"""
        if self.stats['trades_total'] % 10 == 0 and self.stats['trades_total'] > 0:
            # Reportar cada 10 trades
            win_rate = (self.stats['trades_won'] / self.stats['trades_total'] * 100) if self.stats['trades_total'] > 0 else 0
            
            report = (
                f"📊 Reporte de Estado\n"
                f"{'='*20}\n"
                f"Trades totales: {self.stats['trades_total']}\n"
                f"Win rate: {win_rate:.1f}%\n"
                f"Profit total: ${self.stats['profit_total']:.2f}\n"
                f"Max Drawdown: {self.stats['max_drawdown']:.1f}%"
            )
            
            logger.info(report)
            await self._notify(report)
    
    async def _notify(self, message: str):
        """Envía notificación"""
        if self.notifier:
            try:
                await self.notifier.send_message(message)
            except Exception as e:
                logger.warning(f"Error enviando notificación: {e}")
    
    async def stop(self):
        """Detiene el bot de trading"""
        logger.info("⏹️ Deteniendo bot...")
        
        self.is_running = False
        
        # Cerrar todas las posiciones si está configurado
        if self.broker and os.getenv('CLOSE_ON_STOP', 'false').lower() == 'true':
            positions = self.broker.get_positions(self.symbol)
            for position in positions:
                logger.info(f"Cerrando posición {position.ticket}")
                self.broker.close_position(position.ticket)
        
        # Desconectar broker
        if self.broker:
            self.broker.disconnect()
        
        # Notificar
        runtime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else None
        await self._notify(
            f"🛑 Bot Detenido\n"
            f"Runtime: {runtime}\n"
            f"Trades: {self.stats['trades_total']}\n"
            f"Profit: ${self.stats['profit_total']:.2f}"
        )
        
        logger.info("✅ Bot detenido correctamente")
    
    def get_status(self) -> Dict:
        """Obtiene el estado actual del bot"""
        return {
            'running': self.is_running,
            'mode': 'LIVE' if self.is_live else 'DEMO',
            'symbol': self.symbol,
            'stats': self.stats,
            'components': {
                'broker': self.broker is not None,
                'data': self.data_manager is not None,
                'signals': self.signal_generator is not None,
                'risk': self.risk_manager is not None,
                'ml': self.ml_predictor is not None,
                'notifier': self.notifier is not None
            }
        }

# Para testing
if __name__ == "__main__":
    import asyncio
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y ejecutar bot
    bot = BotManager()
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        asyncio.run(bot.stop())
