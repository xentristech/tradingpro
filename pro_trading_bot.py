"""
SISTEMA DE TRADING AUTÓNOMO PROFESIONAL
Bot Principal con Gestión Avanzada Integrada
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configurar encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Agregar path del proyecto
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# Importar módulos
from dotenv import load_dotenv
import MetaTrader5 as mt5
from smart_position_manager import SmartPositionManager
from signals.llm_validator import validate_signal
from notifiers.telegram import send_message
from data.twelvedata import price as td_price, indicator as td_indicator

# Cargar configuración
load_dotenv('.env')

class ProfessionalTradingBot:
    """Bot de Trading Profesional con IA y Gestión Autónoma"""
    
    def __init__(self):
        self.symbol = os.getenv("TRADING_SYMBOL", "BTCUSD")
        self.live_trading = os.getenv("LIVE_TRADING", "false").lower() == "true"
        self.position_manager = SmartPositionManager()
        self.logger = self._setup_logger()
        self.stats = {
            "signals_analyzed": 0,
            "trades_opened": 0,
            "trades_closed": 0,
            "profit_total": 0.0,
            "win_rate": 0.0
        }
        
    def _setup_logger(self):
        """Configurar logging profesional"""
        logger = logging.getLogger('ProBot')
        logger.setLevel(logging.INFO)
        
        # Crear directorio de logs si no existe
        Path("logs").mkdir(exist_ok=True)
        
        # Handler para archivo
        fh = logging.FileHandler('logs/pro_bot.log')
        fh.setLevel(logging.INFO)
        
        # Handler para consola con colores
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formato profesional
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def initialize_mt5(self) -> bool:
        """Inicializar conexión con MT5"""
        try:
            path = os.getenv("MT5_PATH")
            login = int(os.getenv("MT5_LOGIN"))
            password = os.getenv("MT5_PASSWORD")
            server = os.getenv("MT5_SERVER")
            
            if not mt5.initialize(path=path, login=login, password=password, server=server):
                self.logger.error(f"Error MT5: {mt5.last_error()}")
                return False
                
            account = mt5.account_info()
            if account:
                self.logger.info("="*70)
                self.logger.info("🏦 CUENTA CONECTADA")
                self.logger.info(f"   Número: {account.login}")
                self.logger.info(f"   Balance: ${account.balance:.2f}")
                self.logger.info(f"   Equity: ${account.equity:.2f}")
                self.logger.info(f"   Modo: {'LIVE ⚠️' if self.live_trading else 'DEMO ✅'}")
                self.logger.info("="*70)
                return True
                
        except Exception as e:
            self.logger.error(f"Error inicializando MT5: {e}")
            
        return False
    
    def get_market_analysis(self) -> Dict:
        """Análisis completo del mercado"""
        analysis = {
            "symbol": self.symbol,
            "timestamp": datetime.now().isoformat(),
            "price": 0,
            "indicators": {},
            "signal": "NEUTRAL",
            "confidence": 0.0
        }
        
        try:
            # Precio actual
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                analysis["price"] = tick.bid
                
            # Indicadores técnicos
            timeframes = ["5min", "15min", "1h"]
            for tf in timeframes:
                analysis["indicators"][tf] = {
                    "rsi": self.get_indicator_value("rsi", tf),
                    "macd": self.get_indicator_value("macd", tf),
                    "atr": self.get_indicator_value("atr", tf)
                }
                
            # Validación con IA - Crear snapshot correcto
            snapshot = {
                "symbol": self.symbol,
                "precio": analysis["price"],
                "tabla": []
            }
            
            # Convertir indicadores a formato tabla esperado por IA
            for tf, indicators in analysis["indicators"].items():
                tabla_entry = {
                    "tf": tf,
                    "rsi": indicators.get("rsi", 50.0),
                    "macd_hist": indicators.get("macd", 0.0),
                    "rvol": 1.0  # Volumen relativo por defecto
                }
                snapshot["tabla"].append(tabla_entry)
            
            ai_result = validate_signal(snapshot)
            if ai_result and ai_result.senal_final != "NO OPERAR":
                analysis["signal"] = ai_result.senal_final
                analysis["confidence"] = ai_result.confianza
                
                # Enviar notificación de señal por Telegram si es fuerte
                if analysis["signal"] != "NEUTRAL" and analysis["confidence"] > 0.6:
                    try:
                        from notifiers.telegram_notifier import send_signal_notification
                        signal_data = {
                            'symbol': self.symbol,
                            'direction': analysis["signal"],
                            'strength': analysis["confidence"],
                            'confidence': analysis["confidence"],
                            'price': analysis["price"],
                            'reasons': [f"Señal validada por IA con {analysis['confidence']:.1%} confianza"],
                            'entry_price': analysis["price"],
                            'stop_loss': 0,
                            'take_profit': 0
                        }
                        send_signal_notification(signal_data)
                        self.logger.info(f"📱 Señal enviada por Telegram: {analysis['signal']} {analysis['confidence']:.1%}")
                    except Exception as e:
                        self.logger.warning(f"Error enviando señal por Telegram: {e}")
                
        except Exception as e:
            self.logger.error(f"Error en análisis: {e}")
            
        return analysis
    
    def get_indicator_value(self, indicator: str, timeframe: str) -> float:
        """Obtener valor de indicador"""
        try:
            data = td_indicator(self.symbol, indicator, timeframe)
            if data and "values" in data:
                return float(data["values"][0].get(indicator, 0))
        except:
            pass
        return 0
    
    def should_open_position(self, analysis: Dict) -> bool:
        """Determinar si abrir posición"""
        # Verificaciones de seguridad
        if not self.live_trading and analysis["confidence"] < 0.7:
            return False
            
        if analysis["signal"] == "NEUTRAL":
            return False
            
        # Verificar límites de riesgo
        positions = mt5.positions_get(symbol=self.symbol)
        if positions and len(positions) >= 3:
            self.logger.warning("Máximo de posiciones alcanzado")
            return False
            
        # Verificar drawdown
        account = mt5.account_info()
        if account:
            if account.margin_level and account.margin_level < 200:
                self.logger.warning("Nivel de margen bajo")
                return False
                
        return True
    
    def calculate_position_size(self) -> float:
        """Calcular tamaño de posición basado en gestión de riesgo"""
        account = mt5.account_info()
        if not account:
            return 0.01
            
        # Risk 1% de la cuenta
        risk_amount = account.balance * 0.01
        
        # Calcular tamaño basado en SL
        sl_points = 50  # Default
        symbol_info = mt5.symbol_info(self.symbol)
        
        if symbol_info:
            point_value = symbol_info.point
            min_volume = symbol_info.volume_min
            max_volume = symbol_info.volume_max
            
            # Calcular lotes
            volume = risk_amount / (sl_points * point_value * 10)
            
            # Aplicar límites
            volume = max(min_volume, min(volume, max_volume))
            
            # Redondear al step
            volume_step = symbol_info.volume_step
            volume = round(volume / volume_step) * volume_step
            
            return volume
            
        return 0.01
    
    def execute_trade(self, signal: str, analysis: Dict) -> bool:
        """Ejecutar operación con gestión profesional"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info or not symbol_info.visible:
                self.logger.error(f"Símbolo {self.symbol} no disponible")
                return False
                
            # Calcular precio, SL y TP
            price = symbol_info.ask if signal == "BUY" else symbol_info.bid
            
            # SL y TP dinámicos basados en ATR
            atr = analysis["indicators"].get("15min", {}).get("atr", 50)
            
            if signal == "BUY":
                sl = price - (atr * 2 * symbol_info.point)
                tp = price + (atr * 3 * symbol_info.point)
                order_type = mt5.ORDER_TYPE_BUY
            else:
                sl = price + (atr * 2 * symbol_info.point)
                tp = price - (atr * 3 * symbol_info.point)
                order_type = mt5.ORDER_TYPE_SELL
                
            # Calcular volumen
            volume = self.calculate_position_size()
            
            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": int(os.getenv("MT5_MAGIC", "20250817")),
                "comment": f"ProBot_{signal}_{analysis['confidence']:.2f}"
            }
            
            # Ejecutar
            if self.live_trading:
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    self.stats["trades_opened"] += 1
                    
                    # Mensaje de éxito
                    msg = (f"✅ TRADE EJECUTADO\n"
                          f"Tipo: {signal}\n"
                          f"Símbolo: {self.symbol}\n"
                          f"Volumen: {volume}\n"
                          f"Precio: {price:.5f}\n"
                          f"SL: {sl:.5f}\n"
                          f"TP: {tp:.5f}\n"
                          f"Confianza: {analysis['confidence']:.1%}")
                    
                    self.logger.info(msg.replace('\n', ' | '))
                    send_message(msg)
                    
                    # Notificar éxito por Telegram
                    try:
                        from notifiers.telegram_notifier import send_execution_notification
                        execution_data = {
                            'success': True,
                            'symbol': self.symbol,
                            'order_type': signal,
                            'volume': volume,
                            'price': price,
                            'ticket': result.order,
                            'magic': request.get('magic'),
                            'retcode': result.retcode
                        }
                        send_execution_notification(execution_data)
                    except Exception as e:
                        self.logger.warning(f"Error enviando notificación de ejecución: {e}")
                    
                    return True
                else:
                    # Error en ejecución
                    error_msg = f"Error ejecutando orden: Retcode {result.retcode if result else 'None'}"
                    self.logger.error(error_msg)
                    
                    # Notificar error por Telegram
                    try:
                        from notifiers.telegram_notifier import send_execution_notification
                        execution_data = {
                            'success': False,
                            'symbol': self.symbol,
                            'order_type': signal,
                            'volume': volume,
                            'price': price,
                            'retcode': result.retcode if result else 'UNKNOWN',
                            'error_message': error_msg
                        }
                        send_execution_notification(execution_data)
                    except Exception as e:
                        self.logger.warning(f"Error enviando notificación de error: {e}")
                    
                    return False
            else:
                # Modo demo
                self.logger.info(f"📝 DEMO: {signal} {volume} @ {price:.5f}")
                
                # Notificar ejecución demo por Telegram
                try:
                    from notifiers.telegram_notifier import send_execution_notification
                    execution_data = {
                        'success': True,
                        'symbol': self.symbol,
                        'order_type': f"{signal} (DEMO)",
                        'volume': volume,
                        'price': price,
                        'ticket': 'DEMO',
                        'magic': request.get('magic'),
                        'retcode': 'DEMO_SUCCESS'
                    }
                    send_execution_notification(execution_data)
                except Exception as e:
                    self.logger.warning(f"Error enviando notificación demo: {e}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error en ejecución: {e}")
            
        return False
    
    def display_dashboard(self):
        """Mostrar dashboard en consola"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        account = mt5.account_info()
        positions = mt5.positions_get(symbol=self.symbol)
        
        print("="*80)
        print(" "*20 + "🤖 ALGO TRADER PRO - SISTEMA AUTÓNOMO")
        print("="*80)
        print()
        
        # Estado de cuenta
        if account:
            profit_today = account.profit
            profit_color = "🟢" if profit_today >= 0 else "🔴"
            
            print("📊 ESTADO DE CUENTA")
            print("-"*40)
            print(f"  Balance:     ${account.balance:,.2f}")
            print(f"  Equity:      ${account.equity:,.2f}")
            print(f"  Margen:      ${account.margin:,.2f}")
            print(f"  P&L Hoy:     {profit_color} ${profit_today:+,.2f}")
            print()
            
        # Posiciones activas
        print("💼 POSICIONES ACTIVAS")
        print("-"*40)
        if positions:
            total_profit = 0
            for pos in positions:
                tipo = "BUY" if pos.type == 0 else "SELL"
                profit_icon = "🟢" if pos.profit >= 0 else "🔴"
                total_profit += pos.profit
                
                print(f"  #{pos.ticket} | {tipo:4} | Vol: {pos.volume:.2f} | "
                     f"P&L: {profit_icon} ${pos.profit:+.2f}")
                     
            print(f"\n  Total P&L: {'🟢' if total_profit >= 0 else '🔴'} ${total_profit:+,.2f}")
        else:
            print("  No hay posiciones abiertas")
            
        print()
        
        # Estadísticas
        print("📈 ESTADÍSTICAS DE SESIÓN")
        print("-"*40)
        print(f"  Señales analizadas:  {self.stats['signals_analyzed']}")
        print(f"  Trades abiertos:     {self.stats['trades_opened']}")
        print(f"  Trades cerrados:     {self.stats['trades_closed']}")
        
        win_rate = 0
        if self.stats['trades_closed'] > 0:
            win_rate = (self.stats['trades_closed'] - self.stats['trades_opened']) / self.stats['trades_closed']
            
        print(f"  Win Rate:            {win_rate:.1%}")
        print()
        
        # Sistema de gestión
        print("⚙️ GESTIÓN AUTOMÁTICA")
        print("-"*40)
        print("  ✅ Breakeven automático activo")
        print("  ✅ Trailing stop dinámico activo")
        print("  ✅ Take profit parcial activo")
        print("  ✅ Protección de ganancias activa")
        print()
        
        print("="*80)
        print(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
    
    def run(self):
        """Loop principal del bot profesional"""
        self.logger.info("="*70)
        self.logger.info("🚀 SISTEMA DE TRADING PROFESIONAL INICIADO")
        self.logger.info("="*70)
        
        if not self.initialize_mt5():
            self.logger.error("No se pudo inicializar MT5")
            return
            
        # Iniciar gestor de posiciones en paralelo
        import threading
        position_thread = threading.Thread(target=self.position_manager.run_forever)
        position_thread.daemon = True
        position_thread.start()
        
        self.logger.info("✅ Gestor de posiciones iniciado")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                
                # Dashboard cada 10 ciclos
                if cycle % 10 == 0:
                    self.display_dashboard()
                    
                # Análisis de mercado
                self.logger.info(f"🔍 Analizando mercado... (Ciclo #{cycle})")
                analysis = self.get_market_analysis()
                self.stats["signals_analyzed"] += 1
                
                # Log del análisis
                self.logger.info(f"   Precio: {analysis['price']:.2f}")
                self.logger.info(f"   Señal: {analysis['signal']}")
                self.logger.info(f"   Confianza: {analysis['confidence']:.1%}")
                
                # Decidir si operar
                if self.should_open_position(analysis):
                    self.logger.info("🎯 Oportunidad detectada!")
                    if self.execute_trade(analysis['signal'], analysis):
                        self.logger.info("✅ Trade ejecutado exitosamente")
                        
                        # Notificar
                        msg = f"🤖 Nueva operación {analysis['signal']} @ {analysis['price']:.2f}"
                        send_message(msg)
                        
                # Esperar antes del siguiente ciclo
                time.sleep(30)
                
            except KeyboardInterrupt:
                self.logger.info("Sistema detenido por el usuario")
                break
            except Exception as e:
                self.logger.error(f"Error en loop principal: {e}")
                time.sleep(60)
                
        mt5.shutdown()
        self.logger.info("Sistema finalizado")

if __name__ == "__main__":
    bot = ProfessionalTradingBot()
    bot.run()
