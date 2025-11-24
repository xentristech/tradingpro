#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MONITOR DE RIESGO EN TIEMPO REAL - ALGO TRADER V3
=================================================
Sistema de monitoreo y alertas de riesgo avanzado
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import winsound  # Para Windows
import pandas as pd
import numpy as np

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importar módulos del proyecto
from src.journal.trading_journal import get_journal
from src.broker.mt5_connection import MT5Connection
from src.notifiers.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class RiskMonitor:
    """Monitor de riesgo en tiempo real con alertas inteligentes"""
    
    def __init__(self):
        """Inicializa el monitor de riesgo"""
        self.journal = get_journal()
        self.mt5 = MT5Connection()
        self.telegram = TelegramNotifier()
        
        # Configuración de límites de riesgo
        self.risk_limits = {
            'max_daily_drawdown': 5.0,  # %
            'max_total_drawdown': 10.0,  # %
            'max_exposure': 30.0,  # %
            'min_margin_level': 200.0,  # %
            'max_consecutive_losses': 3,
            'max_daily_trades': 10,
            'max_position_size': 0.1,  # lotes
            'min_win_rate': 40.0,  # %
            'max_correlation_exposure': 50.0  # % exposición en pares correlacionados
        }
        
        # Estado del monitor
        self.is_running = False
        self.check_interval = 30  # segundos
        self.alerts_sent = {}  # Para evitar spam de alertas
        self.alert_cooldown = 300  # 5 minutos entre alertas del mismo tipo
        
        # Historial de métricas
        self.metrics_history = []
        self.max_metrics_history = 100
        
        # Contadores
        self.consecutive_losses = 0
        self.daily_trades = 0
        self.last_trade_date = None
        
        # Log de alertas
        self.alerts_log_file = Path("logs/risk_alerts.csv")
        self.alerts_log_file.parent.mkdir(parents=True, exist_ok=True)
        
    def play_alert_sound(self, severity: str = 'warning'):
        """Reproduce sonido de alerta según severidad"""
        try:
            if sys.platform == 'win32':
                if severity == 'critical':
                    # Sonido crítico - múltiples beeps
                    for _ in range(3):
                        winsound.Beep(1000, 500)  # Frecuencia 1000Hz, duración 500ms
                        time.sleep(0.1)
                elif severity == 'warning':
                    # Sonido de advertencia
                    winsound.Beep(800, 300)
                else:
                    # Sonido informativo
                    winsound.Beep(600, 200)
            else:
                # Para Linux/Mac usar print con bell character
                print('\a')  # Bell character
        except Exception as e:
            logger.warning(f"No se pudo reproducir sonido: {e}")
            
    def send_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Envía alerta por Telegram y sonido local"""
        # Verificar cooldown
        now = datetime.now()
        if alert_type in self.alerts_sent:
            last_sent = self.alerts_sent[alert_type]
            if (now - last_sent).seconds < self.alert_cooldown:
                return  # No enviar si está en cooldown
        
        # Formatear mensaje según severidad
        if severity == 'critical':
            emoji = "🚨🔴"
            prefix = "ALERTA CRÍTICA"
        elif severity == 'warning':
            emoji = "⚠️🟡"
            prefix = "ADVERTENCIA"
        else:
            emoji = "ℹ️🔵"
            prefix = "INFORMACIÓN"
        
        # Construir mensaje completo
        full_message = f"""
{emoji} **{prefix}** {emoji}

{message}

Hora: {now.strftime('%H:%M:%S')}
Sistema: AlgoTrader V3
"""
        
        # Enviar a Telegram
        if self.telegram and self.telegram.is_active:
            try:
                self.telegram.send_message(full_message, parse_mode='Markdown')
                logger.info(f"Alerta enviada: {alert_type}")
            except Exception as e:
                logger.error(f"Error enviando alerta Telegram: {e}")
        
        # Reproducir sonido local
        self.play_alert_sound(severity)
        
        # Registrar alerta
        self.alerts_sent[alert_type] = now
        self.log_alert(alert_type, message, severity)
        
    def log_alert(self, alert_type: str, message: str, severity: str):
        """Registra alerta en archivo CSV"""
        try:
            alert_data = {
                'timestamp': datetime.now().isoformat(),
                'type': alert_type,
                'severity': severity,
                'message': message
            }
            
            # Leer existente o crear nuevo
            if self.alerts_log_file.exists():
                df = pd.read_csv(self.alerts_log_file)
            else:
                df = pd.DataFrame(columns=['timestamp', 'type', 'severity', 'message'])
            
            # Añadir nueva alerta
            df = pd.concat([df, pd.DataFrame([alert_data])], ignore_index=True)
            
            # Guardar (mantener solo últimas 1000 alertas)
            df.tail(1000).to_csv(self.alerts_log_file, index=False)
            
        except Exception as e:
            logger.error(f"Error registrando alerta: {e}")
            
    def check_drawdown(self, account_info) -> Dict:
        """Verifica drawdown actual y máximo"""
        if not account_info:
            return {'status': 'error', 'message': 'Sin datos de cuenta'}
        
        balance = account_info.balance
        equity = account_info.equity
        
        # Drawdown actual
        current_dd = ((balance - equity) / balance * 100) if balance > 0 else 0
        
        # Drawdown máximo histórico
        max_dd = self.journal._calculate_max_drawdown_percent()
        
        # Verificar límites
        alerts = []
        
        if current_dd > self.risk_limits['max_total_drawdown']:
            self.send_alert(
                'max_drawdown',
                f"Drawdown máximo alcanzado: {current_dd:.2f}%\n"
                f"Límite: {self.risk_limits['max_total_drawdown']}%\n"
                f"⚠️ CONSIDERAR DETENER TRADING",
                'critical'
            )
            alerts.append('critical')
            
        elif current_dd > self.risk_limits['max_daily_drawdown']:
            self.send_alert(
                'daily_drawdown',
                f"Drawdown diario elevado: {current_dd:.2f}%\n"
                f"Límite diario: {self.risk_limits['max_daily_drawdown']}%",
                'warning'
            )
            alerts.append('warning')
        
        return {
            'current_drawdown': current_dd,
            'max_drawdown': max_dd,
            'alerts': alerts
        }
        
    def check_exposure(self, positions: List, account_info) -> Dict:
        """Verifica exposición total y por símbolo"""
        if not positions or not account_info:
            return {'status': 'ok', 'total_exposure': 0}
        
        equity = account_info.equity
        total_exposure = 0
        symbol_exposure = {}
        
        # Calcular exposición
        for pos in positions:
            position_value = pos.volume * pos.price_current
            total_exposure += position_value
            
            if pos.symbol not in symbol_exposure:
                symbol_exposure[pos.symbol] = 0
            symbol_exposure[pos.symbol] += position_value
        
        # Exposición como % del equity
        exposure_percent = (total_exposure / equity * 100) if equity > 0 else 0
        
        # Verificar límites
        alerts = []
        
        if exposure_percent > self.risk_limits['max_exposure']:
            self.send_alert(
                'high_exposure',
                f"Exposición total alta: {exposure_percent:.2f}%\n"
                f"Límite: {self.risk_limits['max_exposure']}%\n"
                f"Exposición: ${total_exposure:.2f}",
                'warning'
            )
            alerts.append('warning')
        
        # Verificar concentración en un solo símbolo
        for symbol, value in symbol_exposure.items():
            symbol_percent = (value / equity * 100) if equity > 0 else 0
            if symbol_percent > 15:  # Más del 15% en un solo símbolo
                self.send_alert(
                    f'concentration_{symbol}',
                    f"Alta concentración en {symbol}: {symbol_percent:.2f}%\n"
                    f"Valor: ${value:.2f}",
                    'warning'
                )
                alerts.append('concentration')
        
        return {
            'total_exposure': total_exposure,
            'exposure_percent': exposure_percent,
            'symbol_exposure': symbol_exposure,
            'alerts': alerts
        }
        
    def check_positions_protection(self, positions: List) -> Dict:
        """Verifica que todas las posiciones tengan SL/TP"""
        if not positions:
            return {'status': 'ok', 'unprotected': []}
        
        unprotected = []
        
        for pos in positions:
            has_sl = pos.sl != 0.0
            has_tp = pos.tp != 0.0
            
            if not has_sl:
                unprotected.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'issue': 'Sin Stop Loss'
                })
                
                self.send_alert(
                    f'no_sl_{pos.ticket}',
                    f"⚠️ POSICIÓN SIN STOP LOSS\n"
                    f"Ticket: {pos.ticket}\n"
                    f"Símbolo: {pos.symbol}\n"
                    f"Tipo: {'BUY' if pos.type == 0 else 'SELL'}\n"
                    f"Volumen: {pos.volume}",
                    'critical'
                )
        
        return {
            'total_positions': len(positions),
            'unprotected_count': len(unprotected),
            'unprotected': unprotected
        }
        
    def check_margin_level(self, account_info) -> Dict:
        """Verifica el nivel de margen"""
        if not account_info or account_info.margin == 0:
            return {'status': 'ok', 'margin_level': float('inf')}
        
        margin_level = (account_info.equity / account_info.margin) * 100
        
        alerts = []
        
        if margin_level < self.risk_limits['min_margin_level']:
            self.send_alert(
                'low_margin',
                f"⚠️ MARGIN LEVEL CRÍTICO: {margin_level:.2f}%\n"
                f"Mínimo requerido: {self.risk_limits['min_margin_level']}%\n"
                f"Equity: ${account_info.equity:.2f}\n"
                f"Margin usado: ${account_info.margin:.2f}",
                'critical'
            )
            alerts.append('critical')
            
        elif margin_level < self.risk_limits['min_margin_level'] * 2:
            self.send_alert(
                'margin_warning',
                f"Margin level bajo: {margin_level:.2f}%\n"
                f"Se recomienda precaución",
                'warning'
            )
            alerts.append('warning')
        
        return {
            'margin_level': margin_level,
            'margin_used': account_info.margin,
            'free_margin': account_info.margin_free,
            'alerts': alerts
        }
        
    def check_consecutive_losses(self) -> Dict:
        """Verifica rachas de pérdidas"""
        recent_trades = self.journal.trades[-10:] if len(self.journal.trades) >= 10 else self.journal.trades
        
        consecutive_losses = 0
        for trade in reversed(recent_trades):
            if trade.result == 'LOSS':
                consecutive_losses += 1
            elif trade.result == 'WIN':
                break
        
        alerts = []
        
        if consecutive_losses >= self.risk_limits['max_consecutive_losses']:
            self.send_alert(
                'consecutive_losses',
                f"⚠️ RACHA DE PÉRDIDAS: {consecutive_losses} trades seguidos\n"
                f"Límite: {self.risk_limits['max_consecutive_losses']}\n"
                f"Se recomienda pausar y revisar estrategia",
                'warning'
            )
            alerts.append('warning')
        
        return {
            'consecutive_losses': consecutive_losses,
            'alerts': alerts
        }
        
    def check_daily_limits(self) -> Dict:
        """Verifica límites diarios de trading"""
        today = datetime.now().date()
        
        # Contar trades de hoy
        today_trades = [
            t for t in self.journal.trades
            if t.entry_time and datetime.fromisoformat(t.entry_time).date() == today
        ]
        
        daily_count = len(today_trades)
        daily_pnl = sum(t.profit_usd for t in today_trades if t.profit_usd)
        
        alerts = []
        
        if daily_count >= self.risk_limits['max_daily_trades']:
            self.send_alert(
                'max_daily_trades',
                f"Límite diario de trades alcanzado: {daily_count}\n"
                f"Máximo permitido: {self.risk_limits['max_daily_trades']}\n"
                f"PnL del día: ${daily_pnl:.2f}",
                'warning'
            )
            alerts.append('warning')
        
        return {
            'daily_trades': daily_count,
            'daily_pnl': daily_pnl,
            'alerts': alerts
        }
        
    def analyze_correlation_risk(self, positions: List) -> Dict:
        """Analiza riesgo de correlación entre posiciones"""
        if len(positions) < 2:
            return {'status': 'ok', 'correlation_risk': 'low'}
        
        # Grupos de símbolos correlacionados
        correlation_groups = {
            'USD_pairs': ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD'],
            'JPY_pairs': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY'],
            'Gold_related': ['XAUUSD', 'XAGUSD'],
            'Crypto': ['BTCUSD', 'ETHUSD', 'BNBUSD']
        }
        
        # Analizar exposición por grupo
        group_exposure = {}
        
        for pos in positions:
            symbol_base = pos.symbol.replace('m', '')  # Quitar sufijo 'm'
            
            for group_name, symbols in correlation_groups.items():
                if any(s in symbol_base for s in symbols):
                    if group_name not in group_exposure:
                        group_exposure[group_name] = {'buy': 0, 'sell': 0}
                    
                    if pos.type == 0:  # BUY
                        group_exposure[group_name]['buy'] += pos.volume
                    else:  # SELL
                        group_exposure[group_name]['sell'] += pos.volume
        
        # Verificar exposición excesiva en un grupo
        alerts = []
        high_correlation = False
        
        for group_name, exposure in group_exposure.items():
            total_group = exposure['buy'] + exposure['sell']
            net_exposure = abs(exposure['buy'] - exposure['sell'])
            
            if total_group > 0.2:  # Más de 0.2 lotes en grupo correlacionado
                self.send_alert(
                    f'correlation_{group_name}',
                    f"Alta exposición en {group_name}:\n"
                    f"Buy: {exposure['buy']:.2f} lotes\n"
                    f"Sell: {exposure['sell']:.2f} lotes\n"
                    f"Exposición neta: {net_exposure:.2f} lotes",
                    'warning'
                )
                alerts.append('correlation')
                high_correlation = True
        
        return {
            'group_exposure': group_exposure,
            'high_correlation': high_correlation,
            'alerts': alerts
        }
        
    def generate_risk_report(self) -> Dict:
        """Genera reporte completo de riesgo"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Conectar a MT5
        if not self.mt5.connect():
            report['status'] = 'error'
            report['message'] = 'No se pudo conectar a MT5'
            return report
        
        # Obtener datos
        account_info = self.mt5.account_info
        positions = self.mt5.get_positions()
        
        # Ejecutar todos los checks
        report['checks']['drawdown'] = self.check_drawdown(account_info)
        report['checks']['exposure'] = self.check_exposure(positions, account_info)
        report['checks']['protection'] = self.check_positions_protection(positions)
        report['checks']['margin'] = self.check_margin_level(account_info)
        report['checks']['losses'] = self.check_consecutive_losses()
        report['checks']['daily'] = self.check_daily_limits()
        report['checks']['correlation'] = self.analyze_correlation_risk(positions)
        
        # Calcular score de riesgo general (0-100, donde 100 es máximo riesgo)
        risk_score = self.calculate_risk_score(report['checks'])
        report['risk_score'] = risk_score
        
        # Determinar estado general
        if risk_score > 80:
            report['status'] = 'critical'
            report['recommendation'] = 'DETENER TRADING INMEDIATAMENTE'
        elif risk_score > 60:
            report['status'] = 'warning'
            report['recommendation'] = 'Reducir exposición y revisar estrategia'
        elif risk_score > 40:
            report['status'] = 'caution'
            report['recommendation'] = 'Monitorear de cerca'
        else:
            report['status'] = 'normal'
            report['recommendation'] = 'Condiciones normales de trading'
        
        # Guardar en historial
        self.metrics_history.append(report)
        if len(self.metrics_history) > self.max_metrics_history:
            self.metrics_history = self.metrics_history[-self.max_metrics_history:]
        
        return report
        
    def calculate_risk_score(self, checks: Dict) -> float:
        """Calcula un score de riesgo general (0-100)"""
        score = 0
        
        # Drawdown (peso: 30%)
        dd = checks.get('drawdown', {}).get('current_drawdown', 0)
        score += min(30, (dd / self.risk_limits['max_total_drawdown']) * 30)
        
        # Exposición (peso: 25%)
        exp = checks.get('exposure', {}).get('exposure_percent', 0)
        score += min(25, (exp / self.risk_limits['max_exposure']) * 25)
        
        # Protección (peso: 20%)
        unprotected = checks.get('protection', {}).get('unprotected_count', 0)
        total_pos = checks.get('protection', {}).get('total_positions', 1)
        if total_pos > 0:
            score += (unprotected / total_pos) * 20
        
        # Margin level (peso: 15%)
        margin = checks.get('margin', {}).get('margin_level', float('inf'))
        if margin != float('inf'):
            margin_score = max(0, (self.risk_limits['min_margin_level'] * 2 - margin) / self.risk_limits['min_margin_level'])
            score += min(15, margin_score * 15)
        
        # Rachas de pérdidas (peso: 10%)
        losses = checks.get('losses', {}).get('consecutive_losses', 0)
        score += min(10, (losses / self.risk_limits['max_consecutive_losses']) * 10)
        
        return min(100, score)
        
    def monitor_loop(self):
        """Bucle principal de monitoreo"""
        logger.info("Monitor de riesgo iniciado")
        
        while self.is_running:
            try:
                # Generar reporte
                report = self.generate_risk_report()
                
                # Log del estado
                logger.info(f"Risk Score: {report.get('risk_score', 0):.1f} - "
                          f"Status: {report.get('status', 'unknown')}")
                
                # Esperar antes del siguiente check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor detenido por usuario")
                break
            except Exception as e:
                logger.error(f"Error en monitor: {e}")
                time.sleep(self.check_interval)
        
        logger.info("Monitor de riesgo detenido")
        
    def start(self, background: bool = True):
        """Inicia el monitor de riesgo"""
        self.is_running = True
        
        if background:
            # Ejecutar en hilo separado
            monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            monitor_thread.start()
            logger.info("Monitor de riesgo iniciado en segundo plano")
            return monitor_thread
        else:
            # Ejecutar en primer plano
            self.monitor_loop()
            
    def stop(self):
        """Detiene el monitor de riesgo"""
        self.is_running = False
        logger.info("Deteniendo monitor de riesgo...")


if __name__ == "__main__":
    # Test del monitor
    monitor = RiskMonitor()
    
    print("=" * 60)
    print("MONITOR DE RIESGO - ALGO TRADER V3")
    print("=" * 60)
    print()
    
    # Generar un reporte de prueba
    print("Generando reporte de riesgo...")
    report = monitor.generate_risk_report()
    
    print(f"\nRisk Score: {report.get('risk_score', 0):.1f}/100")
    print(f"Status: {report.get('status', 'unknown').upper()}")
    print(f"Recomendación: {report.get('recommendation', 'N/A')}")
    print()
    
    # Mostrar detalles
    if 'checks' in report:
        checks = report['checks']
        
        print("VERIFICACIONES:")
        print("-" * 40)
        
        # Drawdown
        dd = checks.get('drawdown', {})
        print(f"Drawdown actual: {dd.get('current_drawdown', 0):.2f}%")
        print(f"Drawdown máximo: {dd.get('max_drawdown', 0):.2f}%")
        
        # Exposición
        exp = checks.get('exposure', {})
        print(f"Exposición total: {exp.get('exposure_percent', 0):.2f}%")
        
        # Protección
        prot = checks.get('protection', {})
        print(f"Posiciones sin protección: {prot.get('unprotected_count', 0)}")
        
        # Margin
        margin = checks.get('margin', {})
        print(f"Margin level: {margin.get('margin_level', 0):.2f}%")
        
        # Pérdidas consecutivas
        losses = checks.get('losses', {})
        print(f"Pérdidas consecutivas: {losses.get('consecutive_losses', 0)}")
        
        # Trades diarios
        daily = checks.get('daily', {})
        print(f"Trades hoy: {daily.get('daily_trades', 0)}")
        print(f"PnL del día: ${daily.get('daily_pnl', 0):.2f}")
    
    print()
    print("Opciones:")
    print("1. Iniciar monitor continuo")
    print("2. Ejecutar check único")
    print("3. Ver historial de alertas")
    print("0. Salir")
    
    choice = input("\nSelecciona opción: ")
    
    if choice == "1":
        print("\nIniciando monitor continuo...")
        print("Presiona Ctrl+C para detener")
        monitor.start(background=False)
        
    elif choice == "2":
        print("\nEjecutando check único...")
        # Ya se ejecutó arriba
        
    elif choice == "3":
        if monitor.alerts_log_file.exists():
            df = pd.read_csv(monitor.alerts_log_file)
            print("\nÚltimas 10 alertas:")
            print(df.tail(10).to_string())
        else:
            print("No hay historial de alertas")
    
    print("\n¡Monitor finalizado!")