#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA DE LOGGING COMPLETO DE SEÑALES
======================================
Registra todas las señales generadas con detalles completos para análisis posterior
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
import logging

class SignalLogger:
    """Logger completo de señales para análisis posterior"""
    
    def __init__(self, log_dir="logs/signals"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de log
        self.json_log = self.log_dir / f"signals_{datetime.now().strftime('%Y%m%d')}.json"
        self.csv_log = self.log_dir / f"signals_{datetime.now().strftime('%Y%m%d')}.csv"
        self.analysis_log = self.log_dir / f"analysis_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Inicializar CSV si no existe
        self.init_csv_log()
        
        # Logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('SignalLogger')
        
    def init_csv_log(self):
        """Inicializar archivo CSV con headers"""
        if not self.csv_log.exists():
            headers = [
                'timestamp', 'symbol', 'signal_type', 'confidence', 'price_at_signal',
                'ai_recommendation', 'strategy_used', 'indicators_summary',
                'market_conditions', 'reason_no_trade', 'entry_price', 'sl', 'tp',
                'trade_executed', 'result_after_1h', 'result_after_4h', 'result_after_24h',
                'max_profit_pips', 'max_loss_pips', 'final_result', 'analysis_notes'
            ]
            
            with open(self.csv_log, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def log_signal(self, signal_data):
        """
        Registrar una señal completa
        
        Args:
            signal_data (dict): Datos completos de la señal
                - symbol: str
                - signal_type: str ('BUY', 'SELL', 'NO_OPERAR')
                - confidence: float
                - price_at_signal: float
                - ai_recommendation: str
                - strategy_used: str
                - indicators: dict
                - market_conditions: dict
                - reason_no_trade: str (si aplica)
                - entry_details: dict (si se ejecutó)
        """
        try:
            timestamp = datetime.now()
            
            # Preparar datos completos
            full_signal = {
                'id': f"{signal_data['symbol']}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                'timestamp': timestamp.isoformat(),
                'timestamp_readable': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                **signal_data,
                'logged_at': timestamp.isoformat()
            }
            
            # Guardar en JSON (formato completo)
            self.save_to_json(full_signal)
            
            # Guardar en CSV (formato tabular para análisis)
            self.save_to_csv(full_signal)
            
            self.logger.info(f"[SIGNAL LOGGED] {signal_data['symbol']}: {signal_data['signal_type']} "
                           f"(Conf: {signal_data.get('confidence', 0):.1f}%)")
            
        except Exception as e:
            self.logger.error(f"Error logging signal: {e}")
    
    def save_to_json(self, signal_data):
        """Guardar en archivo JSON"""
        try:
            # Leer datos existentes
            signals = []
            if self.json_log.exists():
                with open(self.json_log, 'r', encoding='utf-8') as f:
                    signals = json.load(f)
            
            # Agregar nueva señal
            signals.append(signal_data)
            
            # Guardar
            with open(self.json_log, 'w', encoding='utf-8') as f:
                json.dump(signals, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
    
    def save_to_csv(self, signal_data):
        """Guardar en archivo CSV"""
        try:
            # Preparar fila CSV
            row = [
                signal_data.get('timestamp_readable', ''),
                signal_data.get('symbol', ''),
                signal_data.get('signal_type', ''),
                signal_data.get('confidence', 0),
                signal_data.get('price_at_signal', 0),
                signal_data.get('ai_recommendation', ''),
                signal_data.get('strategy_used', ''),
                json.dumps(signal_data.get('indicators', {})),
                json.dumps(signal_data.get('market_conditions', {})),
                signal_data.get('reason_no_trade', ''),
                signal_data.get('entry_price', ''),
                signal_data.get('sl', ''),
                signal_data.get('tp', ''),
                signal_data.get('trade_executed', False),
                '', '', '',  # Results (to be filled later)
                '', '', '',  # Max profit/loss, final result
                ''  # Analysis notes
            ]
            
            # Escribir fila
            with open(self.csv_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
                
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
    
    def log_market_analysis(self, symbol, analysis_data):
        """
        Registrar análisis detallado del mercado
        
        Args:
            symbol: str
            analysis_data: dict con indicadores, patrones, etc.
        """
        try:
            timestamp = datetime.now()
            
            analysis_entry = {
                'id': f"analysis_{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                'timestamp': timestamp.isoformat(),
                'timestamp_readable': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'analysis_type': 'market_scan',
                **analysis_data
            }
            
            # Leer análisis existente
            analyses = []
            if self.analysis_log.exists():
                with open(self.analysis_log, 'r', encoding='utf-8') as f:
                    analyses = json.load(f)
            
            # Agregar nuevo análisis
            analyses.append(analysis_entry)
            
            # Mantener solo últimos 1000 análisis
            analyses = analyses[-1000:]
            
            # Guardar
            with open(self.analysis_log, 'w', encoding='utf-8') as f:
                json.dump(analyses, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"[ANALYSIS LOGGED] {symbol}: Market scan completed")
            
        except Exception as e:
            self.logger.error(f"Error logging analysis: {e}")
    
    def get_daily_stats(self):
        """Obtener estadísticas del día"""
        try:
            stats = {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'no_operate': 0,
                'avg_confidence': 0,
                'signals_above_70': 0,
                'signals_50_70': 0,
                'signals_below_50': 0,
                'trades_executed': 0
            }
            
            if not self.json_log.exists():
                return stats
            
            with open(self.json_log, 'r', encoding='utf-8') as f:
                signals = json.load(f)
            
            if not signals:
                return stats
            
            # Calcular estadísticas
            stats['total_signals'] = len(signals)
            
            confidences = []
            for signal in signals:
                signal_type = signal.get('signal_type', 'NO_OPERAR')
                confidence = signal.get('confidence', 0)
                
                if signal_type == 'BUY':
                    stats['buy_signals'] += 1
                elif signal_type == 'SELL':
                    stats['sell_signals'] += 1
                else:
                    stats['no_operate'] += 1
                
                confidences.append(confidence)
                
                if confidence >= 70:
                    stats['signals_above_70'] += 1
                elif confidence >= 50:
                    stats['signals_50_70'] += 1
                else:
                    stats['signals_below_50'] += 1
                
                if signal.get('trade_executed', False):
                    stats['trades_executed'] += 1
            
            if confidences:
                stats['avg_confidence'] = sum(confidences) / len(confidences)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting daily stats: {e}")
            return stats
    
    def create_daily_report(self):
        """Crear reporte diario"""
        try:
            stats = self.get_daily_stats()
            
            report = f"""
REPORTE DIARIO DE SEÑALES - {datetime.now().strftime('%Y-%m-%d')}
================================================================

ESTADÍSTICAS GENERALES:
- Total señales analizadas: {stats['total_signals']}
- Señales BUY: {stats['buy_signals']}
- Señales SELL: {stats['sell_signals']} 
- NO_OPERAR: {stats['no_operate']}
- Trades ejecutados: {stats['trades_executed']}

DISTRIBUCIÓN POR CONFIANZA:
- Confianza ≥70%: {stats['signals_above_70']} señales
- Confianza 50-70%: {stats['signals_50_70']} señales
- Confianza <50%: {stats['signals_below_50']} señales
- Confianza promedio: {stats['avg_confidence']:.1f}%

ARCHIVOS GENERADOS:
- JSON completo: {self.json_log.name}
- CSV para análisis: {self.csv_log.name}
- Análisis de mercado: {self.analysis_log.name}

SIGUIENTE PASO:
Usar VALIDADOR_SEÑALES.py para analizar efectividad
================================================================
"""
            
            # Guardar reporte
            report_file = self.log_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(report)
            return report
            
        except Exception as e:
            self.logger.error(f"Error creating daily report: {e}")
            return None

# Instancia global para uso fácil
signal_logger = SignalLogger()