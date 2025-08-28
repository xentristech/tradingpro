"""
Trade Validator - Sistema Avanzado de Validación de Operaciones
Valida trades usando IA, TwelveData y gestión automática de SL/TP
Version: 3.0.0
"""
import logging
import asyncio
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import MetaTrader5 as mt5
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TradeAnalysis:
    """Análisis completo de una operación"""
    ticket: int
    symbol: str
    action: str
    is_viable: bool
    confidence: float
    reasons: List[str]
    suggested_sl: Optional[float]
    suggested_tp: Optional[float]
    market_conditions: Dict
    recommendation: str  # 'KEEP', 'MODIFY', 'CLOSE'

class TradeValidator:
    """
    Validador avanzado de operaciones con IA
    """
    
    def __init__(self, twelvedata_api_key: str = None, telegram_notifier = None):
        """
        Inicializa el validador
        Args:
            twelvedata_api_key: API key de TwelveData
            telegram_notifier: Instancia del notificador de Telegram
        """
        self.twelvedata_api_key = twelvedata_api_key
        self.telegram_notifier = telegram_notifier
        self.pending_validations = {}
        
        logger.info("TradeValidator inicializado")
    
    async def validate_all_positions(self) -> List[TradeAnalysis]:
        """
        Valida todas las posiciones abiertas
        Returns:
            Lista de análisis de trades
        """
        if not mt5.initialize():
            logger.error("No se pudo inicializar MT5")
            return []
        
        positions = mt5.positions_get()
        if not positions:
            logger.info("No hay posiciones abiertas para validar")
            return []
        
        analyses = []
        for position in positions:
            try:
                analysis = await self._analyze_position(position)
                analyses.append(analysis)
                
                # Enviar notificación si requiere acción
                if analysis.recommendation != 'KEEP':
                    await self._send_validation_notification(analysis)
                
            except Exception as e:
                logger.error(f"Error validando posición {position.ticket}: {e}")
        
        return analyses
    
    async def _analyze_position(self, position) -> TradeAnalysis:
        """
        Analiza una posición específica
        Args:
            position: Posición de MT5
        Returns:
            TradeAnalysis con el análisis completo
        """
        # Obtener datos de mercado
        market_data = await self._get_market_data(position.symbol)
        
        # Verificar SL/TP
        has_sl = position.sl != 0
        has_tp = position.tp != 0
        
        # Análisis técnico
        technical_analysis = self._perform_technical_analysis(market_data, position)
        
        # Validación con IA
        ai_validation = await self._validate_with_ai(position, market_data, technical_analysis)
        
        # Determinar recomendación
        recommendation = self._determine_recommendation(
            position, has_sl, has_tp, technical_analysis, ai_validation
        )
        
        # Calcular SL/TP sugeridos si no existen
        suggested_sl, suggested_tp = self._calculate_suggested_levels(
            position, market_data, technical_analysis
        )
        
        reasons = []
        if not has_sl:
            reasons.append("❌ Sin Stop Loss configurado")
        if not has_tp:
            reasons.append("❌ Sin Take Profit configurado")
        
        reasons.extend(technical_analysis.get('warnings', []))
        reasons.extend(ai_validation.get('concerns', []))
        
        return TradeAnalysis(
            ticket=position.ticket,
            symbol=position.symbol,
            action="BUY" if position.type == 0 else "SELL",
            is_viable=ai_validation.get('is_viable', True),
            confidence=ai_validation.get('confidence', 0.5),
            reasons=reasons,
            suggested_sl=suggested_sl,
            suggested_tp=suggested_tp,
            market_conditions=market_data,
            recommendation=recommendation
        )
    
    async def _get_market_data(self, symbol: str) -> Dict:
        """
        Obtiene datos de mercado de TwelveData
        Args:
            symbol: Símbolo a consultar
        Returns:
            Dict con datos de mercado
        """
        if not self.twelvedata_api_key:
            logger.warning("No hay API key de TwelveData configurada")
            return self._get_mt5_market_data(symbol)
        
        try:
            # Mapear símbolo MT5 a TwelveData
            td_symbol = self._map_symbol_to_twelvedata(symbol)
            
            # Obtener datos técnicos
            url = f"https://api.twelvedata.com/technical_indicators"
            params = {
                'symbol': td_symbol,
                'interval': '1h',
                'apikey': self.twelvedata_api_key,
                'outputsize': 50,
                'indicators': 'RSI,MACD,BBANDS,ATR,ADX'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'source': 'twelvedata',
                    'symbol': symbol,
                    'technical_indicators': data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"Error TwelveData: {response.status_code}")
                return self._get_mt5_market_data(symbol)
                
        except Exception as e:
            logger.error(f"Error obteniendo datos TwelveData: {e}")
            return self._get_mt5_market_data(symbol)
    
    def _get_mt5_market_data(self, symbol: str) -> Dict:
        """
        Obtiene datos básicos de MT5 como fallback
        """
        try:
            tick = mt5.symbol_info_tick(symbol)
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            
            if tick and rates is not None:
                return {
                    'source': 'mt5',
                    'symbol': symbol,
                    'current_price': tick.bid,
                    'spread': tick.ask - tick.bid,
                    'rates': rates.tolist() if hasattr(rates, 'tolist') else [],
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error obteniendo datos MT5: {e}")
        
        return {'source': 'error', 'symbol': symbol}
    
    def _map_symbol_to_twelvedata(self, mt5_symbol: str) -> str:
        """
        Mapea símbolos MT5 a formato TwelveData
        """
        mapping = {
            'BTCUSDm': 'BTC/USD',
            'BTCUSD': 'BTC/USD',
            'ETHUSDm': 'ETH/USD',
            'ETHUSD': 'ETH/USD',
            'XAUUSDm': 'XAU/USD',
            'XAUUSD': 'XAU/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'USDJPY': 'USD/JPY'
        }
        return mapping.get(mt5_symbol, mt5_symbol)
    
    def _perform_technical_analysis(self, market_data: Dict, position) -> Dict:
        """
        Realiza análisis técnico básico
        """
        analysis = {
            'trend': 'NEUTRAL',
            'strength': 0.5,
            'warnings': [],
            'support_levels': [],
            'resistance_levels': []
        }
        
        try:
            if market_data.get('source') == 'twelvedata':
                # Procesar indicadores de TwelveData
                indicators = market_data.get('technical_indicators', {})
                
                # Analizar RSI
                if 'RSI' in indicators:
                    rsi_data = indicators['RSI']
                    if isinstance(rsi_data, dict) and 'values' in rsi_data:
                        last_rsi = float(rsi_data['values'][0]['rsi'])
                        if last_rsi > 70:
                            analysis['warnings'].append(f"RSI sobrecomprado: {last_rsi:.1f}")
                        elif last_rsi < 30:
                            analysis['warnings'].append(f"RSI sobreventa: {last_rsi:.1f}")
                
                # Analizar MACD
                if 'MACD' in indicators:
                    macd_data = indicators['MACD']
                    if isinstance(macd_data, dict) and 'values' in macd_data:
                        last_macd = macd_data['values'][0]
                        if float(last_macd['macd']) > float(last_macd['macd_signal']):
                            analysis['trend'] = 'BULLISH'
                        else:
                            analysis['trend'] = 'BEARISH'
            
            elif market_data.get('source') == 'mt5':
                # Análisis básico con datos MT5
                rates = market_data.get('rates', [])
                if len(rates) > 20:
                    closes = [r['close'] for r in rates[-20:]]
                    sma_short = sum(closes[-10:]) / 10
                    sma_long = sum(closes) / 20
                    
                    if sma_short > sma_long:
                        analysis['trend'] = 'BULLISH'
                    else:
                        analysis['trend'] = 'BEARISH'
                
                # Verificar spread alto
                spread = market_data.get('spread', 0)
                current_price = market_data.get('current_price', 0)
                if current_price > 0:
                    spread_pct = (spread / current_price) * 100
                    if spread_pct > 0.1:  # Spread > 0.1%
                        analysis['warnings'].append(f"Spread alto: {spread_pct:.3f}%")
        
        except Exception as e:
            logger.error(f"Error en análisis técnico: {e}")
            analysis['warnings'].append("Error en análisis técnico")
        
        return analysis
    
    async def _validate_with_ai(self, position, market_data: Dict, technical_analysis: Dict) -> Dict:
        """
        Valida la operación usando IA (simulado por ahora)
        """
        try:
            # Simular validación IA basada en datos reales
            confidence = 0.7
            is_viable = True
            concerns = []
            
            # Factores que afectan la viabilidad
            if len(technical_analysis.get('warnings', [])) > 2:
                confidence -= 0.2
                concerns.append("Múltiples señales de advertencia técnicas")
            
            if technical_analysis.get('trend') == 'BEARISH' and position.type == 0:  # BUY en tendencia bajista
                confidence -= 0.3
                concerns.append("Posición BUY en tendencia bajista")
            
            if technical_analysis.get('trend') == 'BULLISH' and position.type == 1:  # SELL en tendencia alcista
                confidence -= 0.3
                concerns.append("Posición SELL en tendencia alcista")
            
            # Verificar tiempo de la operación
            position_age = datetime.now() - datetime.fromtimestamp(position.time)
            if position_age > timedelta(hours=24):
                confidence -= 0.1
                concerns.append(f"Posición antigua: {position_age.total_seconds()/3600:.1f} horas")
            
            # Verificar P&L actual
            if position.profit < -100:  # Pérdida > $100
                confidence -= 0.2
                concerns.append(f"Pérdida significativa: ${position.profit:.2f}")
            
            if confidence < 0.3:
                is_viable = False
            
            return {
                'is_viable': is_viable,
                'confidence': max(0.0, min(1.0, confidence)),
                'concerns': concerns,
                'ai_recommendation': 'HOLD' if is_viable else 'CLOSE',
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en validación IA: {e}")
            return {
                'is_viable': True,
                'confidence': 0.5,
                'concerns': ['Error en validación IA'],
                'ai_recommendation': 'HOLD'
            }
    
    def _determine_recommendation(self, position, has_sl: bool, has_tp: bool, 
                                technical_analysis: Dict, ai_validation: Dict) -> str:
        """
        Determina la recomendación final
        """
        # Si no hay SL/TP, siempre recomendar modificación
        if not has_sl or not has_tp:
            return 'MODIFY'
        
        # Si IA dice que no es viable, recomendar cierre
        if not ai_validation.get('is_viable', True):
            return 'CLOSE'
        
        # Si confianza muy baja, recomendar cierre
        if ai_validation.get('confidence', 1.0) < 0.3:
            return 'CLOSE'
        
        # Si hay muchas advertencias, recomendar modificación
        if len(technical_analysis.get('warnings', [])) > 2:
            return 'MODIFY'
        
        return 'KEEP'
    
    def _calculate_suggested_levels(self, position, market_data: Dict, 
                                  technical_analysis: Dict) -> Tuple[Optional[float], Optional[float]]:
        """
        Calcula niveles sugeridos de SL y TP
        """
        try:
            current_price = market_data.get('current_price', position.price_open)
            if current_price == 0 or current_price is None:
                current_price = position.price_open
            
            # ATR para calcular niveles dinámicos
            atr = self._estimate_atr(market_data)
            
            # Si no hay ATR válido, usar un valor fijo basado en el símbolo
            if atr <= 0 or atr > current_price * 0.1:  # ATR no debe ser > 10% del precio
                # Para Forex usar 20-50 pips típicamente
                if 'USD' in position.symbol or 'EUR' in position.symbol:
                    atr = 0.0020  # 20 pips para pares principales
                else:
                    atr = current_price * 0.002  # 0.2% del precio
            
            if position.type == 0:  # BUY
                suggested_sl = current_price - (atr * 1.5)
                suggested_tp = current_price + (atr * 3)
            else:  # SELL
                suggested_sl = current_price + (atr * 1.5) 
                suggested_tp = current_price - (atr * 3)
            
            # Validar que los valores sean razonables
            if suggested_sl <= 0:
                suggested_sl = current_price * 0.98 if position.type == 0 else current_price * 1.02
            if suggested_tp <= 0:
                suggested_tp = current_price * 1.02 if position.type == 0 else current_price * 0.98
            
            return suggested_sl, suggested_tp
            
        except Exception as e:
            logger.error(f"Error calculando niveles: {e}")
            return None, None
    
    def _estimate_atr(self, market_data: Dict) -> float:
        """
        Estima ATR basado en datos disponibles
        """
        try:
            if market_data.get('source') == 'mt5':
                rates = market_data.get('rates', [])
                if len(rates) >= 14:
                    trs = []
                    for i in range(1, min(15, len(rates))):
                        high = rates[i]['high']
                        low = rates[i]['low']
                        prev_close = rates[i-1]['close']
                        
                        tr = max(
                            high - low,
                            abs(high - prev_close),
                            abs(low - prev_close)
                        )
                        trs.append(tr)
                    
                    return sum(trs) / len(trs) if trs else 100
            
            # Fallback: 0.1% del precio actual
            current_price = market_data.get('current_price', 50000)
            return current_price * 0.001
            
        except Exception as e:
            logger.error(f"Error estimando ATR: {e}")
            return 100  # Default
    
    async def _send_validation_notification(self, analysis: TradeAnalysis):
        """
        Envía notificación de validación por Telegram
        """
        if not self.telegram_notifier:
            logger.warning("No hay notificador de Telegram configurado")
            return
        
        try:
            # Generar código de validación
            validation_code = f"VAL{analysis.ticket}{datetime.now().strftime('%H%M')}"
            self.pending_validations[validation_code] = analysis
            
            # Construir mensaje
            action_emoji = "🟢" if analysis.action == "BUY" else "🔴"
            confidence_emoji = "✅" if analysis.confidence > 0.7 else "⚠️" if analysis.confidence > 0.4 else "❌"
            
            message = f"""
🔍 <b>VALIDACIÓN DE OPERACIÓN REQUERIDA</b>

{action_emoji} <b>#{analysis.ticket}</b> - {analysis.symbol} {analysis.action}
{confidence_emoji} <b>Viabilidad:</b> {'SÍ' if analysis.is_viable else 'NO'} (Confianza: {analysis.confidence:.1%})

<b>📋 PROBLEMAS DETECTADOS:</b>
"""
            
            for reason in analysis.reasons:
                message += f"• {reason}\n"
            
            message += f"""
<b>📊 RECOMENDACIÓN:</b> <code>{analysis.recommendation}</code>

<b>🎯 NIVELES SUGERIDOS:</b>
• SL: <code>{f'{analysis.suggested_sl:.5f}' if analysis.suggested_sl is not None else 'N/A'}</code>
• TP: <code>{f'{analysis.suggested_tp:.5f}' if analysis.suggested_tp is not None else 'N/A'}</code>

<b>⚡ ACCIONES DISPONIBLES:</b>
• <code>APPROVE {validation_code}</code> - Aplicar cambios sugeridos
• <code>CLOSE {validation_code}</code> - Cerrar posición
• <code>IGNORE {validation_code}</code> - Mantener sin cambios

<i>⏰ Responde en 5 minutos o se aplicará acción automática</i>
"""
            
            await self.telegram_notifier.send_message(message)
            
            # Programar acción automática en 5 minutos
            asyncio.create_task(self._auto_execute_validation(validation_code, 300))
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
    
    async def _auto_execute_validation(self, validation_code: str, delay: int):
        """
        Ejecuta acción automática después del delay especificado
        """
        await asyncio.sleep(delay)
        
        if validation_code in self.pending_validations:
            analysis = self.pending_validations[validation_code]
            
            if analysis.recommendation == 'MODIFY':
                success = await self._apply_sl_tp(analysis)
                action = "Aplicados SL/TP automáticamente" if success else "Error aplicando SL/TP"
            elif analysis.recommendation == 'CLOSE':
                success = await self._close_position(analysis.ticket)
                action = "Posición cerrada automáticamente" if success else "Error cerrando posición"
            else:
                action = "Mantenida sin cambios"
            
            # Notificar acción automática
            if self.telegram_notifier:
                await self.telegram_notifier.send_message(
                    f"⏰ <b>ACCIÓN AUTOMÁTICA</b>\n\n"
                    f"#{analysis.ticket} - {analysis.symbol}: {action}"
                )
            
            del self.pending_validations[validation_code]
    
    async def process_telegram_command(self, command: str) -> str:
        """
        Procesa comandos de Telegram para validación
        """
        try:
            parts = command.strip().split()
            if len(parts) != 2:
                return "❌ Formato incorrecto. Usa: APPROVE/CLOSE/IGNORE CÓDIGO"
            
            action, code = parts[0].upper(), parts[1].upper()
            
            if code not in self.pending_validations:
                return "❌ Código de validación no válido o expirado"
            
            analysis = self.pending_validations[code]
            
            if action == "APPROVE":
                if analysis.recommendation == 'MODIFY':
                    success = await self._apply_sl_tp(analysis)
                    result = f"✅ SL/TP aplicados a #{analysis.ticket}" if success else f"❌ Error aplicando SL/TP"
                elif analysis.recommendation == 'CLOSE':
                    success = await self._close_position(analysis.ticket)
                    result = f"✅ Posición #{analysis.ticket} cerrada" if success else f"❌ Error cerrando posición"
                else:
                    result = f"✅ Posición #{analysis.ticket} mantenida"
                    
            elif action == "CLOSE":
                success = await self._close_position(analysis.ticket)
                result = f"✅ Posición #{analysis.ticket} cerrada" if success else f"❌ Error cerrando posición"
                
            elif action == "IGNORE":
                result = f"✅ Validación ignorada para #{analysis.ticket}"
                
            else:
                return "❌ Acción no válida. Usa: APPROVE, CLOSE o IGNORE"
            
            del self.pending_validations[code]
            return result
            
        except Exception as e:
            logger.error(f"Error procesando comando Telegram: {e}")
            return f"❌ Error procesando comando: {str(e)}"
    
    async def _apply_sl_tp(self, analysis: TradeAnalysis) -> bool:
        """
        Aplica SL y TP a la posición
        """
        try:
            if not analysis.suggested_sl or not analysis.suggested_tp:
                logger.error("No hay niveles sugeridos para aplicar")
                return False
            
            # Modificar posición
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": analysis.ticket,
                "sl": analysis.suggested_sl,
                "tp": analysis.suggested_tp,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"SL/TP aplicados a posición {analysis.ticket}")
                return True
            else:
                logger.error(f"Error aplicando SL/TP: {result.retcode} - {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Error aplicando SL/TP: {e}")
            return False
    
    async def _close_position(self, ticket: int) -> bool:
        """
        Cierra una posición específica
        """
        try:
            position = None
            positions = mt5.positions_get(ticket=ticket)
            if positions:
                position = positions[0]
            
            if not position:
                logger.error(f"Posición {ticket} no encontrada")
                return False
            
            # Cerrar posición
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
                "magic": 0,
                "comment": "Cerrado por validador IA",
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Posición {ticket} cerrada exitosamente")
                return True
            else:
                logger.error(f"Error cerrando posición: {result.retcode} - {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Error cerrando posición: {e}")
            return False

# Testing
if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    
    # Cargar configuración
    load_dotenv()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear validador
    validator = TradeValidator(
        twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY'),
        telegram_notifier=None  # Agregar instancia real si está disponible
    )
    
    async def test_validation():
        print("\n🔍 PROBANDO VALIDADOR DE TRADES...")
        
        analyses = await validator.validate_all_positions()
        
        if analyses:
            for analysis in analyses:
                print(f"\n📊 ANÁLISIS - Ticket #{analysis.ticket}:")
                print(f"  Symbol: {analysis.symbol}")
                print(f"  Viable: {analysis.is_viable}")
                print(f"  Confidence: {analysis.confidence:.1%}")
                print(f"  Recommendation: {analysis.recommendation}")
                print(f"  Reasons: {analysis.reasons}")
        else:
            print("No hay posiciones para validar")
    
    # Ejecutar test
    asyncio.run(test_validation())