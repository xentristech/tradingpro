"""
Telegram Notifier - Sistema mejorado de notificaciones
Notificaciones estructuradas para trading con formato mejorado
"""
import os
import time
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Sistema de notificaciones por Telegram mejorado
    """
    
    def __init__(self):
        """Inicializa el notificador de Telegram"""
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram no configurado. Token o Chat ID faltante")
        else:
            logger.info(f"Telegram configurado para chat {self.chat_id[:5]}***")
        # Estado para getUpdates
        self._state_file = Path('data/telegram_state.json')
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Envía un mensaje a Telegram
        
        Args:
            message: Mensaje a enviar
            parse_mode: Modo de parseo (HTML, Markdown, MarkdownV2)
            
        Returns:
            bool: True si se envió exitosamente
        """
        if not self.enabled:
            logger.debug(f"Telegram deshabilitado. Mensaje no enviado: {message[:50]}...")
            return False
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.debug("Mensaje enviado a Telegram")
                return True
            else:
                logger.warning(f"Error enviando a Telegram: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Excepción enviando a Telegram: {e}")
            return False

    def _load_last_update_id(self) -> int:
        try:
            if self._state_file.exists():
                import json
                data = json.load(open(self._state_file, 'r'))
                return int(data.get('last_update_id', 0))
        except Exception:
            pass
        return 0

    def _save_last_update_id(self, update_id: int):
        try:
            import json
            with open(self._state_file, 'w') as f:
                json.dump({'last_update_id': int(update_id)}, f)
        except Exception:
            pass

    def send_action_approval(self, symbol: str, side: str, price: float, sl: float, tp: float, reason: str = "", code: str = "") -> bool:
        """Envía una solicitud de aprobación con un código único."""
        msg = f"""
🧠 <b>APROBACIÓN REQUERIDA</b>

Símbolo: {symbol}
Acción: {side}
Precio: {price:.5f}
SL: {sl:.5f} | TP: {tp:.5f}
Motivo: {reason or 'AI plan'}

Responde este chat con:
  <code>APPROVE {code}</code> para aprobar, o
  <code>REJECT {code}</code> para rechazar.
        """
        return self.send_message(msg)

    def wait_for_approval(self, code: str, timeout_seconds: int = 60) -> bool:
        """Espera aprobación del mensaje via getUpdates. Requiere que el bot no tenga webhook activo."""
        if not self.enabled:
            return False
        import time
        end = time.time() + timeout_seconds
        last_id = self._load_last_update_id()
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {"timeout": 5, "allowed_updates": ["message"]}
        while time.time() < end:
            try:
                if last_id:
                    params["offset"] = last_id + 1
                r = requests.get(url, params=params, timeout=10)
                if r.status_code != 200:
                    time.sleep(2)
                    continue
                data = r.json()
                for upd in data.get('result', []):
                    last_id = max(last_id, upd.get('update_id', last_id))
                    msg = upd.get('message') or {}
                    chat = str((msg.get('chat') or {}).get('id'))
                    text = (msg.get('text') or '').strip()
                    if not text:
                        continue
                    # Filtrar por chat objetivo (si está seteado)
                    if self.chat_id and chat != str(self.chat_id):
                        continue
                    if text.upper() == f"APPROVE {code}".upper():
                        self._save_last_update_id(last_id)
                        return True
                    if text.upper() == f"REJECT {code}".upper():
                        self._save_last_update_id(last_id)
                        return False
                self._save_last_update_id(last_id)
            except Exception as e:
                logger.warning(f"Telegram getUpdates fallo: {e}")
            time.sleep(2)
        return False

    def poll_command(self, timeout_seconds: int = 5) -> Optional[str]:
        """Consulta comandos simples: PAUSE, RESUME, STOP, STATUS.
        Devuelve el último comando recibido o None si no hay.
        Requiere modo polling (sin webhook)."""
        if not self.enabled:
            return None
        import time
        end = time.time() + timeout_seconds
        last_id = self._load_last_update_id()
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {"timeout": 5, "allowed_updates": ["message"]}
        cmd = None
        while time.time() < end:
            try:
                if last_id:
                    params["offset"] = last_id + 1
                r = requests.get(url, params=params, timeout=10)
                if r.status_code != 200:
                    time.sleep(2)
                    continue
                data = r.json()
                for upd in data.get('result', []):
                    last_id = max(last_id, upd.get('update_id', last_id))
                    msg = upd.get('message') or {}
                    chat = str((msg.get('chat') or {}).get('id'))
                    text = (msg.get('text') or '').strip()
                    if not text:
                        continue
                    if self.chat_id and chat != str(self.chat_id):
                        continue
                    t = text.upper().strip()
                    if t in ("PAUSE", "RESUME", "STOP", "STATUS"):
                        cmd = t
                self._save_last_update_id(last_id)
                if cmd:
                    return cmd
            except Exception as e:
                logger.debug(f"poll_command error: {e}")
                break
        return None
    
    def send_startup_message(self, mode: str):
        """Envía mensaje de inicio del sistema"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
🚀 <b>SISTEMA INICIADO</b>

⏰ Hora: {timestamp}
📊 Modo: {mode.upper()}
💼 Cuenta: {os.getenv('MT5_LOGIN', 'N/A')}
📈 Símbolo: {os.getenv('SYMBOL', 'N/A')}
🤖 IA: {os.getenv('OLLAMA_MODEL', 'N/A')}

Sistema de trading activo y monitoreando mercados.
        """
        
        self.send_message(message)
    
    def send_shutdown_message(self):
        """Envía mensaje de cierre del sistema"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
🛑 <b>SISTEMA DETENIDO</b>

⏰ Hora: {timestamp}

Sistema de trading detenido correctamente.
        """
        
        self.send_message(message)
    
    def send_trade_opened(self, ticket: int, symbol: str, side: str, 
                         volume: float, price: float, sl: float, tp: float):
        """Notifica apertura de operación"""
        emoji = "🟢" if side == "BUY" else "🔴"
        # Detalles adicionales: distancias y R:R
        try:
            dist_sl = abs(price - sl) if sl else 0.0
            dist_tp = abs(tp - price) if tp else 0.0
            rr = (dist_tp / dist_sl) if dist_sl else 0.0
        except Exception:
            dist_sl = 0.0; dist_tp = 0.0; rr = 0.0
        risk_pct = 0.0
        try:
            risk_pct = float(os.getenv('MAX_RISK_PER_TRADE', '0.0')) * 100
        except Exception:
            risk_pct = 0.0
        
        message = f"""
{emoji} <b>NUEVA OPERACIÓN</b>

📋 Ticket: {ticket}
📊 {side} {volume} {symbol}
💰 Precio: {price:.5f}
🛡️ SL: {sl:.5f}
🎯 TP: {tp:.5f}
📏 ΔSL: {dist_sl:.5f} | ΔTP: {dist_tp:.5f}
⚖️ R:R ≈ {rr:.2f} | Riesgo/trade: {risk_pct:.1f}%
⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        
        self.send_message(message)
    
    def send_trade_closed(self, ticket: int, symbol: str, profit: float, 
                         duration_minutes: float, **kwargs):
        """Notifica cierre de operación con detalles opcionales.
        kwargs opcionales: entry, close, sl, tp, rr, side, hit
        """
        emoji = "✅" if profit > 0 else "❌"
        status = "GANANCIA" if profit > 0 else "PÉRDIDA"
        entry = kwargs.get('entry')
        close = kwargs.get('close')
        sl = kwargs.get('sl')
        tp = kwargs.get('tp')
        rr = kwargs.get('rr')
        side = kwargs.get('side')
        hit = kwargs.get('hit')  # 'TP' | 'SL' | 'MANUAL' | None

        lines = [
            f"{emoji} <b>OPERACIÓN CERRADA</b>",
            "",
            f"📋 Ticket: {ticket}",
            f"📊 Símbolo: {symbol}",
            f"💵 Resultado: ${profit:.2f} ({status})",
            f"⏱️ Duración: {duration_minutes:.1f} minutos",
        ]
        if side:
            lines.append(f"📍 Lado: {side}")
        if entry is not None and close is not None:
            try:
                lines.append(f"💰 Entry/Close: {float(entry):.5f} → {float(close):.5f}")
            except Exception:
                pass
        if sl is not None and tp is not None:
            try:
                lines.append(f"🛡️ SL: {float(sl):.5f} | 🎯 TP: {float(tp):.5f}")
            except Exception:
                pass
        if rr is not None:
            try:
                lines.append(f"⚖️ R:R objetivo ≈ {float(rr):.2f}")
            except Exception:
                pass
        if hit:
            lines.append(f"🏁 Cierre por: {hit}")
        lines.append(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

        self.send_message("\n".join(lines))
    
    def send_signal_alert(self, symbol: str, signal: str, confidence: float, 
                          reason: str = ""):
        """Notifica detección de señal"""
        emoji_map = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸️"}
        emoji = emoji_map.get(signal, "🔔")
        
        message = f"""
{emoji} <b>SEÑAL DETECTADA</b>

📊 Símbolo: {symbol}
📍 Señal: {signal}
🎯 Confianza: {confidence:.1%}
📝 Razón: {reason if reason else 'Confluencia de indicadores'}
⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        
        self.send_message(message)
    
    def send_error_message(self, error: str):
        """Notifica un error del sistema"""
        message = f"""
⚠️ <b>ERROR EN SISTEMA</b>

🔧 Error: {error}
⏰ {datetime.now().strftime('%H:%M:%S')}

Revisar logs para más detalles.
        """
        
        self.send_message(message)
    
    def send_daily_summary(self, stats: Dict[str, Any]):
        """Envía resumen diario de operaciones con métricas opcionales y por símbolo"""
        pnl_by_symbol = stats.get('pnl_by_symbol', {}) or {}
        var95 = stats.get('var_95')
        sharpe = stats.get('sharpe_ratio')
        metrics_by_symbol = stats.get('metrics_by_symbol', {}) or {}

        lines = [
            "📊 <b>RESUMEN DIARIO</b>",
            "",
            f"📈 Trades totales: {stats.get('trades_total', 0)}",
            f"✅ Ganados: {stats.get('trades_won', 0)}",
            f"❌ Perdidos: {stats.get('trades_lost', 0)}",
            f"📉 Win Rate: {stats.get('win_rate', 0):.1%}",
            "",
            f"💰 P&L Total: ${stats.get('profit_total', 0):.2f}",
            f"📊 Max Drawdown: ${stats.get('max_drawdown', 0):.2f}",
        ]
        if var95 is not None:
            lines.append(f"🧮 VaR(95%): ${float(var95):.2f}")
        if sharpe is not None:
            lines.append(f"⚖️ Sharpe: {float(sharpe):.2f}")

        if pnl_by_symbol:
            lines.append("")
            lines.append("🔎 P&L por símbolo:")
            for sym, pnl in pnl_by_symbol.items():
                lines.append(f" • {sym}: ${float(pnl):.2f}")

        if metrics_by_symbol:
            lines.append("")
            lines.append("🧮 Métricas por símbolo:")
            for sym, m in metrics_by_symbol.items():
                v = m.get('var_95'); s = m.get('sharpe_ratio')
                extra = []
                if v is not None:
                    extra.append(f"VaR95=${float(v):.2f}")
                if s is not None:
                    extra.append(f"Sharpe={float(s):.2f}")
                if extra:
                    lines.append(f" • {sym}: " + ", ".join(extra))

        lines.append("")
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.send_message("\n".join(lines))
    
    def send_risk_alert(self, message_text: str):
        """Envía alerta de riesgo"""
        message = f"""
🚨 <b>ALERTA DE RIESGO</b>

⚠️ {message_text}
⏰ {datetime.now().strftime('%H:%M:%S')}

Sistema en modo precaución.
        """
        
        self.send_message(message)


# Función auxiliar para testing
def send_message(text: str) -> bool:
    """
    Función wrapper para compatibilidad con código existente
    
    Args:
        text: Mensaje a enviar
        
    Returns:
        bool: True si se envió exitosamente
    """
    notifier = TelegramNotifier()
    return notifier.send_message(text)
