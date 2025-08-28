"""
Orchestrator Mejorado - Loop principal con nuevos componentes
Integra State Manager, Rate Limiter y MT5 Connection Manager
"""
import os
import time
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Importar componentes mejorados
from utils.state_manager import StateManager, TradingState
from utils.rate_limiter import RateLimiter, rate_limited
from utils.mt5_connection import MT5ConnectionManager
from utils.logger_config import TradingLogger

# Importar módulos existentes
from signals.llm_validator import validate_signal
from notifiers.telegram import TelegramNotifier
from data.twelvedata import price as td_price, indicator as td_indicator
from data.features import rvol_from_series
from risk.advanced_risk import AdvancedRiskManager
from ai.agent import AIAgent

# Logger especializado
trade_logger = TradingLogger("Orchestrator")
logger = logging.getLogger(__name__)

def main_loop(components: Dict[str, Any],
              state_manager: StateManager,
              rate_limiter: RateLimiter):
    """
    Loop principal mejorado del sistema de trading
    
    Args:
        components: Diccionario con todos los componentes del sistema
        state_manager: Gestor de estado
        rate_limiter: Controlador de límites de API
    """
    try:
        # Obtener configuración
        symbol = os.getenv('SYMBOL', 'BTCUSDm')
        timeframes = os.getenv('TIMEFRAMES', '5min,15min,1h').split(',')
        min_confidence = float(os.getenv('MIN_CONFIDENCE', '0.75'))
        
        # Comandos de Telegram: PAUSE/RESUME/STOP/STATUS
        notifier = components.get('notifier')
        if notifier:
            cmd = notifier.poll_command(timeout_seconds=1)
            if cmd == 'PAUSE':
                state_manager.update_config({'paused': True})
                notifier.send_message('⏸️ Bot pausado por comando Telegram')
            elif cmd == 'RESUME':
                state_manager.update_config({'paused': False})
                notifier.send_message('▶️ Bot reanudado por comando Telegram')
            elif cmd == 'STOP':
                state_manager.update_config({'paused': True})
                notifier.send_message('🛑 Bot detenido (pausado) por comando Telegram')
                return
            elif cmd == 'STATUS':
                stats = state_manager.get_session_stats()
                notifier.send_message(f"📊 Estado: {state_manager.get_trading_state().value}\nCycles: {stats.get('cycles',0)} | Trades: {stats.get('trades_total',0)} | PnL: ${stats.get('profit_total',0):.2f}")

        # Comandos por archivo (launcher): data/command.txt
        try:
            cmd_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'command.txt')
            cmd_file = os.path.abspath(cmd_file)
            if os.path.exists(cmd_file):
                with open(cmd_file, 'r+', encoding='utf-8', errors='ignore') as f:
                    raw = (f.read() or '').strip()
                    f.seek(0); f.truncate()
                if raw:
                    t = raw.strip().upper()
                    if t == 'PAUSE':
                        state_manager.update_config({'paused': True})
                        if notifier:
                            notifier.send_message('⏸️ Bot pausado por comando local')
                    elif t == 'RESUME':
                        state_manager.update_config({'paused': False})
                        if notifier:
                            notifier.send_message('▶️ Bot reanudado por comando local')
                    elif t == 'STOP':
                        state_manager.update_config({'paused': True})
                        if notifier:
                            notifier.send_message('🛑 Bot detenido (pausado) por comando local')
                        return
                    elif t == 'STATUS' and notifier:
                        stats = state_manager.get_session_stats()
                        notifier.send_message(f"📊 Estado: {state_manager.get_trading_state().value}\nCycles: {stats.get('cycles',0)} | Trades: {stats.get('trades_total',0)} | PnL: ${stats.get('profit_total',0):.2f}")
        except Exception:
            pass

        # Respetar pausa
        cfg = state_manager.get_config()
        if cfg.get('paused'):
            state_manager.set_trading_state(TradingState.PAUSED)
            return

        # Cargar settings y validar horas/régimen
        settings = components.get('settings')
        if settings and getattr(settings, 'ENABLE_MARKET_REGIME', True):
            # Horarios
            from datetime import datetime, time as dtime
            import pytz
            tzname = os.getenv('TZ', 'UTC')
            tz = pytz.timezone(tzname)
            now = datetime.now(tz)
            h_start = settings.MARKET_HOURS_START
            h_end = settings.MARKET_HOURS_END
            try:
                t_start = dtime(int(h_start.split(':')[0]), int(h_start.split(':')[1]))
                t_end = dtime(int(h_end.split(':')[0]), int(h_end.split(':')[1]))
                in_hours = (t_start <= now.time() <= t_end) if t_start <= t_end else (now.time() >= t_start or now.time() <= t_end)
            except Exception:
                in_hours = True
            if not in_hours:
                logger.info("Fuera de horario de trading. Saltando ciclo.")
                state_manager.set_trading_state(TradingState.IDLE)
                return
            if not settings.ALLOW_WEEKENDS and now.weekday() >= 5:
                logger.info("Fin de semana deshabilitado para trading. Saltando ciclo.")
                state_manager.set_trading_state(TradingState.IDLE)
                return
        
        # Actualizar estado
        state_manager.set_trading_state(TradingState.ANALYZING)
        
        # 1. Obtener datos de mercado con rate limiting
        market_data = get_market_data_with_limiting(
            symbol, timeframes, rate_limiter
        )
        
        if not market_data:
            logger.warning("No se pudieron obtener datos de mercado")
            state_manager.set_trading_state(TradingState.IDLE)
            return
        
        # Actualizar estado con datos de mercado (raw)
        state_manager.update_market_data(symbol, {'raw': market_data})
        
        # 2. Calcular indicadores y features
        features = calculate_features(market_data)
        # Guardar features en el state manager para gestión posterior
        state_manager.update_market_data(symbol, {'features': features})
        
        # 3. Validar señal con IA (con rate limiting)
        signal = validate_signal_with_limiting(
            symbol, features, market_data, 
            components.get('signal_validator'),
            rate_limiter
        )

        # 3.1 Orquestación IA (opcional): pedir plan de acciones y convertir a señal
        try:
            settings = components.get('settings')
            if settings and getattr(settings, 'ENABLE_AI_ORCHESTRATION', False):
                # Preparar snapshot compacto
                tabla = []
                precio_actual = 0
                for tf, feat in features.items():
                    tabla.append({
                        'tf': tf,
                        'rsi': feat.get('rsi', 50),
                        'macd_hist': feat.get('macd_hist', 0),
                        'rvol': feat.get('rvol', 1.0),
                        'mfi': feat.get('mfi', 50),
                        'cmf': feat.get('cmf', 0),
                        'obv_slope': feat.get('obv_slope', 0),
                    })
                    if not precio_actual:
                        precio_actual = feat.get('price', 0)
                snapshot = {'symbol': symbol, 'tabla': tabla, 'precio': precio_actual}
                agent = components.get('ai_agent') or AIAgent()
                components['ai_agent'] = agent
                # Cargar política de IA si existe
                policy_text = None
                try:
                    policy_path = os.path.join(os.path.dirname(__file__), '..', 'ai', 'policy.md')
                    policy_path = os.path.abspath(policy_path)
                    if os.path.exists(policy_path):
                        with open(policy_path, 'r', encoding='utf-8') as f:
                            policy_text = f.read()
                except Exception:
                    policy_text = None
                plan = agent.propose_actions(snapshot, system_policy=policy_text)
                if plan and plan.actions:
                    # Tomar primera acción OPEN_POSITION si supera umbral
                    act = next((a for a in plan.actions if a.type == 'OPEN_POSITION'), None)
                    if act and act.confidence >= settings.AI_DECISION_CONFIDENCE_MIN:
                        # Construir objeto compatible con validador
                        class _Setup: pass
                        st = _Setup(); st.sl = act.setup.sl if act.setup else None; st.tp = act.setup.tp if act.setup else None
                        class _Result: pass
                        res = _Result(); res.signal = 'COMPRA' if act.side == 'BUY' else 'VENTA'; res.confidence = act.confidence; res.setup = st; res.reason = act.reason or 'AI plan'
                        # Confirmación humana opcional por Telegram
                        if settings.AI_REQUIRE_HUMAN_CONFIRMATION and components.get('notifier'):
                            import uuid
                            code = uuid.uuid4().hex[:6].upper()
                            ok_msg = components['notifier'].send_action_approval(
                                symbol=symbol,
                                side='BUY' if res.signal == 'COMPRA' else 'SELL',
                                price=precio_actual or 0,
                                sl=float(st.sl or 0),
                                tp=float(st.tp or 0),
                                reason=res.reason,
                                code=code
                            )
                            if ok_msg:
                                approved = components['notifier'].wait_for_approval(code, getattr(settings, 'AI_APPROVAL_TIMEOUT_SECONDS', 60))
                                if not approved:
                                    logger.info("Acción IA no aprobada por humano; se omite")
                                    res = None
                            else:
                                logger.warning("No se pudo enviar solicitud de aprobación; omitiendo acción IA")
                                res = None
                        if res:
                            signal = res
        except Exception:
            pass

        if signal and signal.signal != "NO OPERAR":
            # Calcular ATR y S/R con timeframe primario
            primary_tf = timeframes[0].strip()
            ts = market_data.get(primary_tf, {}).get('price', {})
            closes = ts.get('close', []) or []
            highs = ts.get('high', []) or []
            lows = ts.get('low', []) or []
            atr = compute_atr_from_series(highs, lows, closes, period=14)
            support, resistance = compute_sr_from_series(highs, lows, window=5)
            current_price = closes[-1] if closes else features.get(primary_tf, {}).get('price', 0)

            # Régimen: volatilidad máxima (ATR/Price)
            if settings and getattr(settings, 'ENABLE_MARKET_REGIME', True) and current_price:
                vol_ratio = (atr / current_price) if atr else 0
                if vol_ratio > settings.VOLATILITY_MAX:
                    logger.info(f"Gating por volatilidad: ATR/Price {vol_ratio:.2%} > {settings.VOLATILITY_MAX:.2%}")
                    # Registrar alerta de gating en el estado
                    try:
                        state_manager.log_error(f"Gating: Volatilidad alta ATR/Price {vol_ratio:.2%} > {settings.VOLATILITY_MAX:.2%}")
                    except Exception:
                        pass
                    state_manager.set_trading_state(TradingState.IDLE)
                    return

            # Asegurar SL/TP básicos si el validador no los provee
            side_buy = (signal.signal.upper() == 'COMPRA')
            default_sl = 0
            if atr:
                if side_buy:
                    base_sl = current_price - 1.5 * atr
                    default_sl = max(base_sl, (support * 0.99) if support else base_sl)
                else:
                    base_sl = current_price + 1.5 * atr
                    default_sl = min(base_sl, (resistance * 1.01) if resistance else base_sl)
            default_tp = 0
            if atr:
                default_tp = (current_price + 2.5 * atr) if side_buy else (current_price - 2.5 * atr)
            try:
                if not getattr(signal, 'setup', None):
                    class _Setup: pass
                    signal.setup = _Setup()
                if not getattr(signal.setup, 'sl', None):
                    signal.setup.sl = default_sl
                if not getattr(signal.setup, 'tp', None):
                    signal.setup.tp = default_tp
            except Exception:
                pass
            # Registrar señal
            state_manager.add_signal({
                'symbol': symbol,
                'signal': signal.signal,
                'confidence': signal.confidence,
                'setup': signal.setup.__dict__ if signal.setup else {}
            })
            
            # Notificar señal
            if 'notifier' in components:
                components['notifier'].send_signal_alert(
                    symbol, signal.signal, signal.confidence, signal.reason
                )
            
            # 4. Evaluar con Risk Manager
            if signal.confidence >= min_confidence:
                # Métricas de riesgo avanzadas (VaR, Sharpe, Kelly) con retornos del timeframe primario
                hist_returns = []
                try:
                    closes_arr = closes[-200:] if closes else []
                    hist_returns = [
                        (closes_arr[i] / closes_arr[i-1] - 1.0) for i in range(1, len(closes_arr))
                    ] if len(closes_arr) > 2 else []
                except Exception:
                    hist_returns = []

                risk_manager = components.get('risk_manager')
                if risk_manager:
                    try:
                        sl_val = getattr(signal.setup, 'sl', default_sl)
                        tp_val = getattr(signal.setup, 'tp', default_tp)
                        rm = risk_manager.calculate_position_metrics(
                            symbol=symbol,
                            entry_price=current_price,
                            stop_loss=sl_val,
                            take_profit=tp_val,
                            historical_returns=hist_returns
                        )
                        ok, reason = risk_manager.should_take_trade(rm)
                        if not ok:
                            logger.info(f"Bloqueado por RiskManager: {reason}")
                            state_manager.log_error(f"Risk gate: {reason}")
                            return
                    except Exception as e:
                        logger.warning(f"No se pudieron calcular métricas de riesgo: {e}")

                should_trade = evaluate_risk(
                    signal,
                    risk_manager,
                    state_manager,
                    features=features
                )
                
                if should_trade:
                    # 5. Ejecutar trade
                    execute_trade(
                        symbol, signal, 
                        components.get('mt5_manager'),
                        state_manager,
                        components.get('notifier')
                    )
        
        # 6. Gestionar posiciones existentes
        manage_open_positions(
            components.get('mt5_manager'),
            state_manager,
            components.get('notifier')
        )

        # 7. Enviar resumen diario si corresponde (incluye VaR/Sharpe, PnL y métricas por símbolo)
        try:
            from datetime import datetime
            now = datetime.now()
            report_hour = int(os.getenv('REPORT_HOUR', '23'))
            conf = state_manager.get_config()
            last_report = conf.get('last_daily_report')
            date_str = now.strftime('%Y-%m-%d')
            due = (last_report != date_str and now.hour >= report_hour)
            if due and components.get('notifier'):
                stats = state_manager.get_session_stats()
                total = stats.get('trades_total', 0)
                won = stats.get('trades_won', 0)
                stats['win_rate'] = (won / total) if total else 0.0
                # Adjuntar PnL por símbolo
                md = state_manager.get_market_data(symbol) or {}
                stats['pnl_by_symbol'] = (state_manager._state.get('pnl_by_symbol') if hasattr(state_manager, '_state') else {})
                # Recalcular VaR y Sharpe del timeframe primario global y por símbolo
                import numpy as np
                try:
                    closes = ((md.get('raw') or {}).get(timeframes[0].strip(), {}) or {}).get('price', {}).get('close', []) or []
                    if len(closes) > 10:
                        rets = [(closes[i]/closes[i-1]-1.0) for i in range(1, len(closes))]
                        var_percentile = (1-0.95) * 100
                        stats['var_95'] = abs(float(np.percentile(np.array(rets), var_percentile))) * abs(stats.get('profit_total', 0))
                        rf = 0.02/252
                        ex = np.array(rets) - rf
                        stats['sharpe_ratio'] = float(np.mean(ex)/np.std(ex) * np.sqrt(252)) if np.std(ex) else 0.0
                except Exception:
                    pass

                # Métricas por símbolo (si hay market_data guardado)
                metrics_by_symbol = {}
                try:
                    for sym in stats.get('pnl_by_symbol', {}).keys():
                        mds = state_manager.get_market_data(sym) or {}
                        c = ((mds.get('raw') or {}).get(timeframes[0].strip(), {}) or {}).get('price', {}).get('close', []) or []
                        if len(c) > 10:
                            r = [(c[i]/c[i-1]-1.0) for i in range(1, len(c))]
                            vp = (1-0.95)*100
                            var_s = abs(float(np.percentile(np.array(r), vp))) * abs(stats.get('pnl_by_symbol', {}).get(sym, 0))
                            rf = 0.02/252
                            exs = np.array(r) - rf
                            sh = float(np.mean(exs)/np.std(exs) * np.sqrt(252)) if np.std(exs) else 0.0
                            metrics_by_symbol[sym] = {'var_95': var_s, 'sharpe_ratio': sh}
                except Exception:
                    pass
                if metrics_by_symbol:
                    stats['metrics_by_symbol'] = metrics_by_symbol
                components['notifier'].send_daily_summary(stats)
                state_manager.update_config({'last_daily_report': date_str})
        except Exception:
            pass
        
        # Actualizar estado
        state_manager.set_trading_state(TradingState.IDLE)
        
    except Exception as e:
        logger.error(f"Error en main loop: {e}", exc_info=True)
        state_manager.log_error(str(e), critical=True)
        state_manager.set_trading_state(TradingState.ERROR)
        
        # Notificar error crítico
        if 'notifier' in components:
            components['notifier'].send_error_message(str(e))


@rate_limited('twelvedata', cost=3.0)  # 3+ llamadas (por timeframe)
def get_market_data_with_limiting(symbol: str, 
                                 timeframes: List[str],
                                 rate_limiter: RateLimiter) -> Dict[str, Any]:
    """
    Obtiene datos de mercado con rate limiting
    
    Args:
        symbol: Símbolo a consultar
        timeframes: Lista de timeframes
        rate_limiter: Controlador de límites
        
    Returns:
        Dict con datos de mercado
    """
    market_data = {}
    
    for tf in timeframes:
        try:
            # Serie OHLCV
            price_data = td_price(symbol=symbol, interval=tf, outputsize=120)

            # Indicadores principales
            rsi_data = td_indicator('rsi', symbol=symbol, interval=tf, outputsize=120, time_period=14)
            macd_data = td_indicator('macd', symbol=symbol, interval=tf, outputsize=120, fast_period=12, slow_period=26, signal_period=9)

            # Indicadores de volumen/liquidez
            mfi_data = td_indicator('mfi', symbol=symbol, interval=tf, outputsize=120, time_period=14)
            obv_data = td_indicator('obv', symbol=symbol, interval=tf, outputsize=120)
            cmf_data = td_indicator('cmf', symbol=symbol, interval=tf, outputsize=120, time_period=20)
            ad_data = td_indicator('ad', symbol=symbol, interval=tf, outputsize=120)

            market_data[tf] = {
                'price': price_data,
                'rsi': rsi_data,
                'macd': macd_data,
                'mfi': mfi_data,
                'obv': obv_data,
                'cmf': cmf_data,
                'ad': ad_data,
            }
            
            logger.debug(f"Datos obtenidos para {symbol} {tf}")
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para {tf}: {e}")
    
    return market_data


def calculate_features(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula features e indicadores adicionales
    
    Args:
        market_data: Datos de mercado
        
    Returns:
        Dict con features calculadas
    """
    features = {}
    
    try:
        for tf, data in market_data.items():
            if 'price' in data and data['price'] is not None:
                # Estructura de listas
                prices = data['price'].get('close', [])[-100:]
                volumes = data['price'].get('volume', [])[-100:]
                
                # Calcular RVOL
                rvol = rvol_from_series(volumes, window=20)
                
                # RSI actual
                rsi = (data.get('rsi', {}).get('rsi', [50]) or [50])[-1]
                
                # MACD histogram
                macd_hist = 0
                if 'macd' in data and data['macd'] is not None:
                    macd_vals = data['macd'].get('macd_hist', [0]) or [0]
                    macd_hist = macd_vals[-1] if macd_vals else 0

                # Volume-based indicators
                mfi = (data.get('mfi', {}).get('mfi', [50]) or [50])[-1]
                cmf = (data.get('cmf', {}).get('cmf', [0]) or [0])[-1]
                obv_list = data.get('obv', {}).get('obv', []) or []
                obv_slope = 0.0
                if len(obv_list) >= 5:
                    obv_slope = (obv_list[-1] - obv_list[-5]) / 5.0 if obv_list[-5] is not None else 0.0
                ad_list = data.get('ad', {}).get('ad', []) or []
                ad_delta = 0.0
                if len(ad_list) >= 2 and ad_list[-2] is not None:
                    ad_delta = ad_list[-1] - ad_list[-2]
                
                features[tf] = {
                    'price': prices[-1] if prices else 0,
                    'rvol': rvol,
                    'rsi': rsi,
                    'macd_hist': macd_hist,
                    'mfi': mfi,
                    'cmf': cmf,
                    'obv_slope': obv_slope,
                    'ad_delta': ad_delta,
                }
                
    except Exception as e:
        logger.error(f"Error calculando features: {e}")
    
    return features


def compute_atr_from_series(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    try:
        import numpy as np
        if not closes or len(closes) < period + 1:
            return float((highs[-1] - lows[-1]) if highs and lows else 0)
        trs = []
        for i in range(1, len(closes)):
            h, l, pc = highs[i], lows[i], closes[i-1]
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        return float(np.mean(trs[-period:]))
    except Exception:
        return 0.0


def compute_sr_from_series(highs: List[float], lows: List[float], window: int = 5) -> tuple:
    support, resistance = None, None
    n = len(highs)
    try:
        for i in range(n-1-window, window, -1):
            if all(highs[i] > highs[i-k] for k in range(1, window+1)) and all(highs[i] > highs[i+k] for k in range(1, window+1)):
                resistance = highs[i]; break
        for i in range(n-1-window, window, -1):
            if all(lows[i] < lows[i-k] for k in range(1, window+1)) and all(lows[i] < lows[i+k] for k in range(1, window+1)):
                support = lows[i]; break
    except Exception:
        pass
    if resistance is None and highs:
        resistance = max(highs[-window:])
    if support is None and lows:
        support = min(lows[-window:])
    return float(support or 0), float(resistance or 0)


@rate_limited('ollama', cost=1.0)
def validate_signal_with_limiting(symbol: str,
                                 features: Dict[str, Any],
                                 market_data: Dict[str, Any],
                                 validator_func,
                                 rate_limiter: RateLimiter):
    """
    Valida señal con IA aplicando rate limiting
    
    Args:
        symbol: Símbolo
        features: Features calculadas
        market_data: Datos de mercado
        validator_func: Función validadora
        rate_limiter: Controlador de límites
        
    Returns:
        Resultado de validación o None
    """
    if not validator_func:
        return None
    
    try:
        # Preparar snapshot para validación
        tabla = []
        precio_actual = 0
        
        for tf, feat in features.items():
            tabla.append({
                'tf': tf,
                'rsi': feat.get('rsi', 50),
                'macd_hist': feat.get('macd_hist', 0),
                'rvol': feat.get('rvol', 1.0),
                'mfi': feat.get('mfi', 50),
                'cmf': feat.get('cmf', 0),
                'obv_slope': feat.get('obv_slope', 0),
            })
            
            if precio_actual == 0:
                precio_actual = feat.get('price', 0)
        
        snapshot = {
            'symbol': symbol,
            'tabla': tabla,
            'precio': precio_actual
        }
        
        # Validar con IA
        result = validator_func(snapshot)
        
        logger.info(f"Señal validada: {result.signal} (Confianza: {result.confidence:.2%})")
        
        return result
        
    except Exception as e:
        logger.error(f"Error validando señal: {e}")
        return None


def evaluate_risk(signal: Any,
                 risk_manager: AdvancedRiskManager,
                 state_manager: StateManager,
                 features: Optional[Dict[str, Any]] = None) -> bool:
    """
    Evalúa el riesgo de la operación
    
    Args:
        signal: Señal validada
        risk_manager: Gestor de riesgo
        state_manager: Gestor de estado
        
    Returns:
        bool: True si se debe tomar la operación
    """
    if not risk_manager:
        logger.warning("Risk Manager no disponible, omitiendo evaluación")
        return True
    
    try:
        # Obtener estadísticas de sesión
        stats = state_manager.get_session_stats()
        
        # Verificar límites diarios
        max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '200'))
        if stats.get('profit_total', 0) < -max_daily_loss:
            logger.warning(f"Límite de pérdida diaria alcanzado: ${stats['profit_total']:.2f}")
            state_manager.log_error("Límite de pérdida diaria alcanzado")
            return False
        
        # Verificar número máximo de posiciones
        max_positions = int(os.getenv('MAX_POSITIONS', '3'))
        open_positions = len(state_manager.get_positions())
        if open_positions >= max_positions:
            logger.warning(f"Máximo de posiciones alcanzado: {open_positions}/{max_positions}")
            return False
        
        # Gating básico por volumen/liquidez y flujo (si hay features)
        if features:
            # promedios simples
            rvols = [f.get('rvol', 1.0) for f in features.values() if isinstance(f, dict)]
            cmfs = [f.get('cmf', 0.0) for f in features.values() if isinstance(f, dict)]
            avg_rvol = sum(rvols) / len(rvols) if rvols else 1.0
            avg_cmf = sum(cmfs) / len(cmfs) if cmfs else 0.0

            # Evitar operar en baja liquidez
            if avg_rvol < 0.8:
                logger.info(f"Gating: RVOL bajo ({avg_rvol:.2f}), no operar")
                try:
                    state_manager.log_error(f"Gating: RVOL bajo ({avg_rvol:.2f})")
                except Exception:
                    pass
                return False

            # Alinear dirección con flujo de dinero (CMF)
            if getattr(signal, 'signal', '').upper() == 'COMPRA' and avg_cmf < -0.05:
                logger.info(f"Gating: CMF promedio negativo ({avg_cmf:.2f}) en señal de compra")
                try:
                    state_manager.log_error(f"Gating: CMF promedio negativo ({avg_cmf:.2f}) en señal de compra")
                except Exception:
                    pass
                return False
            if getattr(signal, 'signal', '').upper() == 'VENTA' and avg_cmf > 0.05:
                logger.info(f"Gating: CMF promedio positivo ({avg_cmf:.2f}) en señal de venta")
                try:
                    state_manager.log_error(f"Gating: CMF promedio positivo ({avg_cmf:.2f}) en señal de venta")
                except Exception:
                    pass
                return False

        # Calcular tamaño de posición con gestión de riesgo avanzada (placeholder)
        # Aquí puedes usar risk_manager para sizing dinámico con volatilidad/rv ol
        
        return True
        
    except Exception as e:
        logger.error(f"Error evaluando riesgo: {e}")
        return False


def execute_trade(symbol: str,
                 signal: Any,
                 mt5_manager: MT5ConnectionManager,
                 state_manager: StateManager,
                 notifier: Optional[TelegramNotifier]):
    """
    Ejecuta una operación de trading
    
    Args:
        symbol: Símbolo
        signal: Señal validada
        mt5_manager: Gestor de MT5
        state_manager: Gestor de estado
        notifier: Notificador de Telegram
    """
    if not mt5_manager:
        logger.error("MT5 Manager no disponible")
        return
    
    try:
        state_manager.set_trading_state(TradingState.PLACING_ORDER)
        
        # Obtener información del símbolo
        symbol_info = mt5_manager.get_symbol_info(symbol)
        if not symbol_info:
            logger.error(f"No se pudo obtener info del símbolo {symbol}")
            return
        
        # Obtener tick actual
        tick = mt5_manager.get_symbol_tick(symbol)
        if not tick:
            logger.error(f"No se pudo obtener tick para {symbol}")
            return
        
        # Preparar orden
        import MetaTrader5 as mt5
        side_buy = signal.signal.upper() == "COMPRA"
        order_type = mt5.ORDER_TYPE_BUY if side_buy else mt5.ORDER_TYPE_SELL
        price = tick.ask if side_buy else tick.bid

        # Normalizar SL/TP a requisitos del símbolo (stops level, dígitos)
        sl_val = float(signal.setup.sl if signal.setup else 0) if getattr(signal, 'setup', None) else 0.0
        tp_val = float(signal.setup.tp if signal.setup else 0) if getattr(signal, 'setup', None) else 0.0
        try:
            digits = getattr(symbol_info, 'digits', 5) or 5
            point = getattr(symbol_info, 'point', 0.0001) or 0.0001
            stops_level = getattr(symbol_info, 'stops_level', 0) or 0
            min_dist = stops_level * point
            if side_buy:
                if sl_val <= 0 or sl_val >= price:
                    sl_val = price - max(min_dist, 1.5 * abs(tp_val - price) if tp_val > price else min_dist)
                if tp_val <= price:
                    tp_val = price + max(min_dist * 2, 2.5 * abs(price - sl_val) if sl_val < price else min_dist * 2)
            else:
                if sl_val <= 0 or sl_val <= price:
                    sl_val = price + max(min_dist, 1.5 * abs(price - tp_val) if tp_val < price else min_dist)
                if tp_val >= price:
                    tp_val = price - max(min_dist * 2, 2.5 * abs(sl_val - price) if sl_val > price else min_dist * 2)
            sl_val = round(sl_val, digits)
            tp_val = round(tp_val, digits)
        except Exception:
            pass

        # Sizing dinámico por riesgo (ATR/SL)
        # Distancia a SL en precio
        stop_price = float(signal.setup.sl if getattr(signal, 'setup', None) and signal.setup.sl else 0)
        stop_dist = abs(price - stop_price) if stop_price else max(price * 0.01, 1e-6)
        
        # Equity y parámetros
        equity = None
        try:
            acc = mt5_manager.get_account_info()
            equity = float(getattr(acc, 'equity', 0)) if acc else None
        except Exception:
            equity = None
        if not equity or equity <= 0:
            equity = float(os.getenv('INITIAL_CAPITAL', '10000'))

        risk_frac = float(os.getenv('MAX_RISK_PER_TRADE', '0.02'))
        risk_amount = equity * risk_frac

        pip_value = float(os.getenv('PIP_VALUE', '1.0'))
        raw_volume = risk_amount / max(stop_dist * pip_value, 1e-9)

        # Ajustar a step y límites del símbolo
        vmin = getattr(symbol_info, 'volume_min', 0.01) or 0.01
        vmax = getattr(symbol_info, 'volume_max', 100.0) or 100.0
        vstep = getattr(symbol_info, 'volume_step', 0.01) or 0.01

        # Redondeo al múltiplo de step hacia abajo (no exceder riesgo)
        steps = max(int(raw_volume / vstep), 1)
        volume = steps * vstep
        volume = max(vmin, min(volume, vmax))
        
        # Log de parámetros finales antes de enviar la orden
        try:
            dlog = getattr(symbol_info, 'digits', 5) or 5
            logger.info(
                f"Orden {'BUY' if side_buy else 'SELL'} {symbol} | price={price:.{dlog}f} "
                f"sl={sl_val:.{dlog}f} tp={tp_val:.{dlog}f} vol={volume} equity={equity:.2f} risk={risk_frac:.2%}"
            )
        except Exception:
            logger.info(
                f"Orden {'BUY' if side_buy else 'SELL'} {symbol} | price={price} sl={sl_val} tp={tp_val} vol={volume}"
            )

        # Preparar request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": float(price),
            "sl": float(sl_val),
            "tp": float(tp_val),
            "deviation": int(os.getenv('MT5_DEVIATION', 20)),
            "magic": int(os.getenv('MT5_MAGIC', 20250817)),
            "comment": f"Bot {signal.confidence:.0%}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        
        # Ejecutar orden
        result = mt5_manager.place_order(request)
        
        if result:
            # Registrar posición en state manager
            from utils.state_manager import Position
            
            position = Position(
                ticket=result.order,
                symbol=symbol,
                type="BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL",
                volume=volume,
                entry_price=price,
                current_price=price,
                sl=sl_val,
                tp=tp_val,
                profit=0,
                open_time=datetime.now()
            )
            
            state_manager.add_position(position)
            state_manager.set_trading_state(TradingState.POSITION_OPEN)
            
            # Notificar
            if notifier:
                notifier.send_trade_opened(
                    result.order, symbol,
                    "BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL",
                    volume, price,
                    sl_val,
                    tp_val
                )
            
            trade_logger.trade_opened(
                result.order, symbol,
                "BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL",
                volume, price
            )

            # Guardar registro CSV en logs/trades.csv
            try:
                import csv
                os.makedirs('logs', exist_ok=True)
                csv_path = os.path.join('logs', 'trades.csv')
                rr = 0.0
                try:
                    dist_sl = abs(price - sl_val)
                    dist_tp = abs(tp_val - price)
                    rr = (dist_tp / dist_sl) if dist_sl else 0.0
                except Exception:
                    rr = 0.0
                row = {
                    'timestamp': datetime.now().isoformat(timespec='seconds'),
                    'ticket': result.order,
                    'symbol': symbol,
                    'side': 'BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': float(volume),
                    'entry': float(price),
                    'sl': float(sl_val),
                    'tp': float(tp_val),
                    'rr': round(rr, 4),
                    'confidence': getattr(signal, 'confidence', 0.0),
                    'reason': getattr(signal, 'reason', '') or ''
                }
                write_header = not os.path.exists(csv_path)
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    w = csv.DictWriter(f, fieldnames=list(row.keys()))
                    if write_header:
                        w.writeheader()
                    w.writerow(row)
            except Exception as e:
                logger.warning(f"No se pudo escribir logs/trades.csv: {e}")
            
        else:
            logger.error("Fallo al ejecutar orden")
            state_manager.set_trading_state(TradingState.ERROR)
            
    except Exception as e:
        logger.error(f"Error ejecutando trade: {e}", exc_info=True)
        state_manager.log_error(str(e), critical=True)
        state_manager.set_trading_state(TradingState.ERROR)


def manage_open_positions(mt5_manager: MT5ConnectionManager,
                         state_manager: StateManager,
                         notifier: Optional[TelegramNotifier]):
    """
    Gestiona las posiciones abiertas
    
    Args:
        mt5_manager: Gestor de MT5
        state_manager: Gestor de estado
        notifier: Notificador de Telegram
    """
    if not mt5_manager:
        return
    
    try:
        state_manager.set_trading_state(TradingState.MANAGING_POSITION)
        
        # Obtener posiciones desde MT5
        mt5_positions = mt5_manager.get_open_positions()
        
        # Sincronizar con state manager
        state_positions = state_manager.get_positions()
        
        for mt5_pos in mt5_positions:
            ticket = mt5_pos.ticket
            
            # Actualizar información en state manager
            if ticket in state_positions:
                state_manager.update_position(
                    ticket,
                    current_price=mt5_pos.price_current,
                    profit=mt5_pos.profit
                )
            
            # Gestión de posición (trailing stop, breakeven, etc.)
            manage_single_position(mt5_pos, mt5_manager, state_manager)
        
        # Verificar posiciones cerradas
        for ticket in list(state_positions.keys()):
            if not any(p.ticket == ticket for p in mt5_positions):
                # Posición fue cerrada
                pos_info = state_positions[ticket]
                duration = (datetime.now() - datetime.fromisoformat(
                    pos_info['open_time']
                )).total_seconds() / 60
                
                state_manager.remove_position(ticket, pos_info.get('profit', 0))
                
                # Notificar
                if notifier:
                    # Determinar cierre por TP/SL aproximado
                    side = pos_info.get('type', '')
                    entry = pos_info.get('entry_price') or 0.0
                    close_price = pos_info.get('current_price') or 0.0
                    slv = pos_info.get('sl') or 0.0
                    tpv = pos_info.get('tp') or 0.0
                    hit = 'MANUAL'
                    try:
                        if side.upper() == 'BUY':
                            if tpv and close_price >= tpv * 0.999:
                                hit = 'TP'
                            elif slv and close_price <= slv * 1.001:
                                hit = 'SL'
                        elif side.upper() == 'SELL':
                            if tpv and close_price <= tpv * 1.001:
                                hit = 'TP'
                            elif slv and close_price >= slv * 0.999:
                                hit = 'SL'
                    except Exception:
                        hit = 'MANUAL'

                    # R:R aproximado
                    rr = 0.0
                    try:
                        dist_sl = abs(entry - slv) if entry and slv else 0.0
                        dist_tp = abs(tpv - entry) if entry and tpv else 0.0
                        rr = (dist_tp / dist_sl) if dist_sl else 0.0
                    except Exception:
                        rr = 0.0

                    notifier.send_trade_closed(
                        ticket,
                        pos_info['symbol'],
                        pos_info.get('profit', 0),
                        duration,
                        entry=entry,
                        close=close_price,
                        sl=slv,
                        tp=tpv,
                        rr=rr,
                        side=side,
                        hit=hit,
                    )
                
                trade_logger.trade_closed(
                    ticket,
                    pos_info.get('profit', 0),
                    duration
                )

                # Registrar cierre en CSV
                try:
                    import csv
                    import os as _os
                    _os.makedirs('logs', exist_ok=True)
                    csv_path = _os.path.join('logs', 'trades_closed.csv')
                    entry = pos_info.get('entry_price') or 0.0
                    close_price = pos_info.get('current_price') or 0.0
                    sl = pos_info.get('sl') or 0.0
                    tp = pos_info.get('tp') or 0.0
                    rr = 0.0
                    try:
                        dist_sl = abs(entry - sl) if entry and sl else 0.0
                        dist_tp = abs(tp - entry) if entry and tp else 0.0
                        rr = (dist_tp / dist_sl) if dist_sl else 0.0
                    except Exception:
                        rr = 0.0
                    row = {
                        'timestamp': datetime.now().isoformat(timespec='seconds'),
                        'ticket': ticket,
                        'symbol': pos_info.get('symbol'),
                        'side': pos_info.get('type', ''),
                        'volume': pos_info.get('volume', 0.0),
                        'entry': float(entry),
                        'close': float(close_price),
                        'sl': float(sl),
                        'tp': float(tp),
                        'rr': round(rr, 4),
                        'pnl': float(pos_info.get('profit', 0.0)),
                        'duration_min': round(duration, 2),
                        'hit': hit
                    }
                    write_header = not _os.path.exists(csv_path)
                    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                        w = csv.DictWriter(f, fieldnames=list(row.keys()))
                        if write_header:
                            w.writeheader()
                        w.writerow(row)
                except Exception as e:
                    logger.warning(f"No se pudo escribir logs/trades_closed.csv: {e}")
        
    except Exception as e:
        logger.error(f"Error gestionando posiciones: {e}")
        state_manager.log_error(str(e))


def manage_single_position(position: Any, mt5_manager: MT5ConnectionManager, state_manager: StateManager):
    """
    Gestiona una posición individual (trailing stop, breakeven, etc.)
    
    Args:
        position: Posición MT5
        mt5_manager: Gestor de MT5
    """
    try:
        # Obtener configuración
        use_breakeven = os.getenv('USE_BREAKEVEN', 'true').lower() == 'true'
        use_trailing = os.getenv('USE_TRAILING', 'true').lower() == 'true'
        be_trigger = float(os.getenv('BREAKEVEN_TRIGGER', os.getenv('BREAKEVEN_TRIGGER', '0.001')))
        trailing_dist = float(os.getenv('TRAILING_DISTANCE', os.getenv('TRAILING_DISTANCE', '0.002')))
        trailing_atr_mult = float(os.getenv('TRAILING_ATR_MULT', os.getenv('TRAILING_ATR_MULT', '1.5')))

        # Usar point/pip del símbolo si está disponible
        sym_info = mt5_manager.get_symbol_info(position.symbol)
        point = getattr(sym_info, 'point', 0.0001) if sym_info else 0.0001

        # Beneficio flotante en precio aprox. (simplificado)
        import MetaTrader5 as mt5
        is_buy = (position.type == mt5.ORDER_TYPE_BUY)
        price_move = (position.price_current - position.price_open) if is_buy else (position.price_open - position.price_current)
        profit_ratio = price_move / position.price_open if position.price_open else 0

        # Breakeven: mover SL a precio de entrada cuando supera umbral
        if use_breakeven and profit_ratio > be_trigger:
            if position.sl != position.price_open:
                logger.info(f"Moviendo a breakeven posición {position.ticket}")
                mt5_manager.modify_position(position.ticket, sl=position.price_open)

        # Trailing: mantener SL a distancia relativa, ajustada por ATR y CMF
        if use_trailing and profit_ratio > be_trigger:
            desired_gap = position.price_current * trailing_dist

            # Datos de mercado para ATR y CMF
            md = state_manager.get_market_data(position.symbol) or {}
            raw = (md.get('raw') or {})
            feats = (md.get('features') or {})
            timeframes = os.getenv('TIMEFRAMES', '5min,15min,1h').split(',')
            primary_tf = timeframes[0].strip()

            # ATR del timeframe primario si hay series
            try:
                ts = (raw.get(primary_tf) or {}).get('price') or {}
                highs = ts.get('high', []) or []
                lows = ts.get('low', []) or []
                closes = ts.get('close', []) or []
                atr_val = compute_atr_from_series(highs, lows, closes, period=14)
                desired_gap = max(desired_gap, atr_val * trailing_atr_mult)
            except Exception:
                pass

            # Ajuste por CMF: si fluye en contra, estrechar trailing
            cmf = 0.0
            try:
                cmf = float((feats.get(primary_tf) or {}).get('cmf', 0.0))
            except Exception:
                cmf = 0.0
            if is_buy and cmf < 0:
                desired_gap *= 0.7
            if (not is_buy) and cmf > 0:
                desired_gap *= 0.7
            if is_buy:
                new_sl = max(position.sl or 0, position.price_current - desired_gap)
                # nunca por debajo de breakeven si ya aplicado
                new_sl = max(new_sl, position.price_open)
                if new_sl > (position.sl or 0):
                    logger.info(f"Ajustando trailing stop BUY {position.ticket} -> SL {new_sl:.5f}")
                    mt5_manager.modify_position(position.ticket, sl=new_sl)
            else:
                new_sl = min(position.sl or position.price_open, position.price_current + desired_gap)
                new_sl = min(new_sl, position.price_open)
                if (position.sl is None) or (new_sl < position.sl):
                    logger.info(f"Ajustando trailing stop SELL {position.ticket} -> SL {new_sl:.5f}")
                    mt5_manager.modify_position(position.ticket, sl=new_sl)
                    
    except Exception as e:
        logger.error(f"Error gestionando posición {position.ticket}: {e}")
