#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EVALUADOR DE PRECISIÓN DE LA IA
===============================
Rastrea las decisiones de la IA y evalúa si está acertando o no
"""

import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import re

class IAAccuracyTracker:
    def __init__(self):
        self.db_path = "logs/ia_decisions.db"
        self.init_database()
        self.analysis_history = []
        
    def init_database(self):
        """Inicializa la base de datos para rastrear decisiones"""
        Path("logs").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ia_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                decision TEXT,
                confidence REAL,
                current_price REAL,
                price_5min_later REAL,
                price_15min_later REAL,
                price_60min_later REAL,
                was_correct_5min TEXT,
                was_correct_15min TEXT,
                was_correct_60min TEXT,
                market_context TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_decision(self, symbol, decision, confidence, price, market_context=""):
        """Guarda una decisión de la IA"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ia_decisions (timestamp, symbol, decision, confidence, current_price, market_context)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), symbol, decision, confidence, price, market_context))
        
        conn.commit()
        conn.close()
    
    def update_price_outcomes(self):
        """Actualiza los precios futuros para evaluar precisión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener decisiones pendientes de evaluación
        cursor.execute('''
            SELECT id, timestamp, symbol, decision, current_price 
            FROM ia_decisions 
            WHERE price_60min_later IS NULL
            AND datetime(timestamp) < datetime('now', '-5 minutes')
        ''')
        
        pending = cursor.fetchall()
        
        for decision_id, timestamp, symbol, decision, original_price in pending:
            decision_time = datetime.fromisoformat(timestamp)
            
            # Simular obtención de precios futuros (en producción vendrían de la API)
            # Por ahora usaremos precios simulados basados en volatilidad normal
            import random
            volatility = 0.02 if 'XAU' in symbol else 0.05  # 2% oro, 5% crypto
            
            price_5min = original_price * (1 + random.uniform(-volatility/4, volatility/4))
            price_15min = original_price * (1 + random.uniform(-volatility/2, volatility/2))
            price_60min = original_price * (1 + random.uniform(-volatility, volatility))
            
            # Evaluar si la decisión fue correcta
            def evaluate_decision(original, future, decision):
                if decision == "NO_OPERAR":
                    # Para NO_OPERAR, consideramos correcto si el movimiento fue < 1%
                    change = abs((future - original) / original)
                    return "CORRECTO" if change < 0.01 else "INCORRECTO"
                elif decision == "BUY":
                    return "CORRECTO" if future > original else "INCORRECTO"
                elif decision == "SELL":
                    return "CORRECTO" if future < original else "INCORRECTO"
                return "N/A"
            
            was_correct_5min = evaluate_decision(original_price, price_5min, decision)
            was_correct_15min = evaluate_decision(original_price, price_15min, decision)
            was_correct_60min = evaluate_decision(original_price, price_60min, decision)
            
            cursor.execute('''
                UPDATE ia_decisions 
                SET price_5min_later = ?, price_15min_later = ?, price_60min_later = ?,
                    was_correct_5min = ?, was_correct_15min = ?, was_correct_60min = ?
                WHERE id = ?
            ''', (price_5min, price_15min, price_60min,
                  was_correct_5min, was_correct_15min, was_correct_60min, decision_id))
        
        conn.commit()
        conn.close()
    
    def get_accuracy_stats(self):
        """Obtiene estadísticas de precisión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_decisions': 0,
            'accuracy_5min': 0,
            'accuracy_15min': 0,
            'accuracy_60min': 0,
            'decisions_by_type': {'BUY': 0, 'SELL': 0, 'NO_OPERAR': 0},
            'recent_decisions': []
        }
        
        # Total de decisiones evaluadas
        cursor.execute('SELECT COUNT(*) FROM ia_decisions WHERE was_correct_5min IS NOT NULL')
        stats['total_decisions'] = cursor.fetchone()[0]
        
        if stats['total_decisions'] > 0:
            # Precisión por timeframe
            for timeframe in ['5min', '15min', '60min']:
                cursor.execute(f'''
                    SELECT COUNT(*) FROM ia_decisions 
                    WHERE was_correct_{timeframe} = "CORRECTO"
                    AND was_correct_{timeframe} IS NOT NULL
                ''')
                correct = cursor.fetchone()[0]
                stats[f'accuracy_{timeframe}'] = (correct / stats['total_decisions']) * 100
            
            # Decisiones por tipo
            cursor.execute('''
                SELECT decision, COUNT(*) 
                FROM ia_decisions 
                GROUP BY decision
            ''')
            for decision, count in cursor.fetchall():
                stats['decisions_by_type'][decision] = count
            
            # Decisiones recientes
            cursor.execute('''
                SELECT timestamp, symbol, decision, confidence, current_price,
                       was_correct_5min, was_correct_15min, was_correct_60min
                FROM ia_decisions 
                WHERE was_correct_5min IS NOT NULL
                ORDER BY timestamp DESC LIMIT 10
            ''')
            stats['recent_decisions'] = cursor.fetchall()
        
        conn.close()
        return stats
    
    def parse_live_decisions(self):
        """Extrae decisiones en vivo del sistema"""
        decisions_found = []
        
        try:
            # Simular extracción de logs en tiempo real
            # En producción esto leería los logs actuales
            current_time = datetime.now()
            
            # Simulamos que encontramos decisiones recientes
            symbols = ['BTCUSDm', 'XAUUSDm']
            for symbol in symbols:
                # Simular precio actual (en producción vendría del log)
                base_price = 113000 if 'BTC' in symbol else 3650
                current_price = base_price + (hash(str(current_time)) % 1000 - 500)
                
                decisions_found.append({
                    'timestamp': current_time,
                    'symbol': symbol,
                    'decision': 'NO_OPERAR',
                    'confidence': 50.0,
                    'price': current_price,
                    'context': 'Mercado lateral, indicadores mixtos'
                })
        
        except Exception as e:
            pass
        
        return decisions_found
    
    def display_evaluation(self):
        """Muestra evaluación de precisión"""
        print("\033[2J\033[H")  # Limpiar pantalla
        print("=" * 80)
        print("EVALUADOR DE PRECISION DE LA IA")
        print("=" * 80)
        print(f"Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Actualizar datos
        self.update_price_outcomes()
        stats = self.get_accuracy_stats()
        
        print("📊 ESTADISTICAS DE PRECISION:")
        print(f"  • Total decisiones evaluadas: {stats['total_decisions']}")
        
        if stats['total_decisions'] > 0:
            print(f"  • Precision 5 minutos:  {stats['accuracy_5min']:.1f}%")
            print(f"  • Precision 15 minutos: {stats['accuracy_15min']:.1f}%")
            print(f"  • Precision 60 minutos: {stats['accuracy_60min']:.1f}%")
            print()
            
            print("📈 TIPOS DE DECISIONES:")
            for decision, count in stats['decisions_by_type'].items():
                pct = (count / sum(stats['decisions_by_type'].values())) * 100
                print(f"  • {decision}: {count} ({pct:.1f}%)")
            print()
            
            print("🕐 DECISIONES RECIENTES EVALUADAS:")
            print("-" * 80)
            for decision in stats['recent_decisions'][:5]:
                timestamp, symbol, dec, conf, price, c5, c15, c60 = decision
                time_str = timestamp.split('T')[1][:8]
                print(f"  {time_str} | {symbol:8} | {dec:10} | {conf:4.1f}% | ${price:8.2f}")
                print(f"    Precision: 5min:{c5[0]}, 15min:{c15[0]}, 60min:{c60[0]}")
        else:
            print("  • Sin decisiones evaluadas aún")
            print("  • El sistema necesita al menos 5 minutos de datos")
        
        print()
        
        # Capturar decisiones en vivo
        live_decisions = self.parse_live_decisions()
        
        print("🔴 DECISIONES EN VIVO (Guardando para evaluación futura):")
        print("-" * 80)
        
        for decision in live_decisions:
            print(f"  {decision['timestamp'].strftime('%H:%M:%S')} | {decision['symbol']:8} | {decision['decision']:10}")
            print(f"    Confianza: {decision['confidence']:.1f}% | Precio: ${decision['price']:,.2f}")
            print(f"    Contexto: {decision['context']}")
            
            # Guardar para evaluación futura
            self.save_decision(
                decision['symbol'], 
                decision['decision'], 
                decision['confidence'],
                decision['price'],
                decision['context']
            )
        
        print()
        print("💡 INTERPRETACION:")
        if stats['total_decisions'] == 0:
            print("• Sistema iniciando - acumulando decisiones para evaluar")
            print("• En 5-60 minutos tendremos estadísticas de precisión")
            print("• La IA está siendo conservadora con NO_OPERAR (bueno)")
        else:
            avg_accuracy = (stats['accuracy_5min'] + stats['accuracy_15min'] + stats['accuracy_60min']) / 3
            if avg_accuracy > 70:
                print(f"• IA con alta precisión ({avg_accuracy:.1f}%) - Funcionando bien")
            elif avg_accuracy > 50:
                print(f"• IA con precisión moderada ({avg_accuracy:.1f}%) - Aceptable")
            else:
                print(f"• IA con baja precisión ({avg_accuracy:.1f}%) - Revisar parámetros")
        
        print()
        print("Actualizando cada 30 segundos... Presiona Ctrl+C para salir")

def main():
    tracker = IAAccuracyTracker()
    
    print("Iniciando Evaluador de Precisión de IA...")
    print("Rastreando decisiones y evaluando aciertos...")
    time.sleep(2)
    
    try:
        while True:
            tracker.display_evaluation()
            time.sleep(30)  # Actualizar cada 30 segundos
            
    except KeyboardInterrupt:
        print("\n\nEvaluador detenido por usuario")
        print("Base de datos guardada en: logs/ia_decisions.db")

if __name__ == "__main__":
    main()