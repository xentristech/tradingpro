#!/usr/bin/env python
"""
AI TRADE PERFORMANCE EVALUATOR - SISTEMA INTELIGENTE DE EVALUACION DE TRADES
===========================================================================
Sistema con AI que evalúa trades activos y aplica break-even y trailing inteligentes
"""

import os
import sys
import time
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from pathlib import Path

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Añadir path del proyecto
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

class AITradeEvaluator:
    """Sistema de AI para evaluar y gestionar trades activos"""
    
    def __init__(self):
        # Configuración de AI para evaluación de trades
        self.evaluation_criteria = {
            'profit_protection_threshold': 10,  # $10 USD mínimo para proteger
            'strong_position_pips': 15,         # 15+ pips = posición fuerte
            'weak_position_pips': 5,            # <5 pips = posición débil
            'time_threshold_minutes': 30,       # 30 min para evaluar performance
            'risk_threshold_percentage': 2.0,   # 2% máximo riesgo por posición
        }
        
        # Parámetros dinámicos de AI
        self.ai_params = {
            'aggressive_breakeven': {'trigger': 8, 'offset': 2},
            'conservative_breakeven': {'trigger': 20, 'offset': 5},
            'aggressive_trailing': {'trigger': 12, 'distance': 8},
            'conservative_trailing': {'trigger': 30, 'distance': 15}
        }
        
        # Estados de AI
        self.ai_state = {
            'positions_evaluated': {},
            'breakeven_applied': set(),
            'trailing_active': set(),
            'ai_recommendations': {}
        }
        
        print("AI Trade Evaluator inicializado con parametros inteligentes")
    
    def evaluate_trade_performance(self, position):
        """Evaluación de AI para performance de trade"""
        try:
            # Obtener datos de la posición
            symbol = position.symbol
            ticket = position.ticket
            entry_price = position.price_open
            current_price = position.price_current
            profit_usd = position.profit
            position_type = position.type
            open_time = datetime.fromtimestamp(position.time)
            duration_minutes = (datetime.now() - open_time).total_seconds() / 60
            
            # Calcular pips de ganancia
            if position_type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, current_price - entry_price)
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, entry_price - current_price)
            
            # AI EVALUATION ALGORITHM
            ai_score = 0
            ai_signals = []
            
            # 1. Análisis de profitabilidad (peso: 40%)
            if profit_usd >= 50:
                ai_score += 40
                ai_signals.append("PROFIT_HIGH")
            elif profit_usd >= 20:
                ai_score += 25
                ai_signals.append("PROFIT_MEDIUM")
            elif profit_usd >= 10:
                ai_score += 15
                ai_signals.append("PROFIT_LOW")
            elif profit_usd < -20:
                ai_score -= 30
                ai_signals.append("LOSS_HIGH")
            
            # 2. Análisis de momentum en pips (peso: 30%)
            if pips_profit >= 25:
                ai_score += 30
                ai_signals.append("MOMENTUM_STRONG")
            elif pips_profit >= 15:
                ai_score += 20
                ai_signals.append("MOMENTUM_GOOD")
            elif pips_profit >= 5:
                ai_score += 10
                ai_signals.append("MOMENTUM_WEAK")
            elif pips_profit < -10:
                ai_score -= 25
                ai_signals.append("MOMENTUM_NEGATIVE")
            
            # 3. Análisis temporal (peso: 20%)
            if duration_minutes > 120:  # >2 horas
                if pips_profit > 0:
                    ai_score += 15
                    ai_signals.append("TIME_MATURE_POSITIVE")
                else:
                    ai_score -= 20
                    ai_signals.append("TIME_MATURE_NEGATIVE")
            elif duration_minutes > 60:  # >1 hora
                if pips_profit > 10:
                    ai_score += 10
                    ai_signals.append("TIME_DEVELOPING")
            
            # 4. Análisis de símbolo específico (peso: 10%)
            if 'XAU' in symbol:  # Oro más volátil
                if abs(pips_profit) > 15:
                    ai_score += 10
                    ai_signals.append("GOLD_VOLATILITY_GOOD")
            elif 'BTC' in symbol:  # Crypto muy volátil
                if abs(pips_profit) > 50:
                    ai_score += 10
                    ai_signals.append("CRYPTO_VOLATILITY_GOOD")
            else:  # Forex estándar
                if abs(pips_profit) > 10:
                    ai_score += 5
                    ai_signals.append("FOREX_MOVEMENT_GOOD")
            
            # Determinar estrategia de AI
            if ai_score >= 60:
                strategy = "PROTECT_AGGRESSIVELY"
            elif ai_score >= 30:
                strategy = "PROTECT_MODERATELY"
            elif ai_score >= 10:
                strategy = "MONITOR_CLOSELY"
            elif ai_score <= -20:
                strategy = "CUT_LOSSES"
            else:
                strategy = "HOLD_POSITION"
            
            return {
                'ticket': ticket,
                'symbol': symbol,
                'pips_profit': pips_profit,
                'profit_usd': profit_usd,
                'duration_minutes': duration_minutes,
                'ai_score': ai_score,
                'ai_signals': ai_signals,
                'strategy': strategy,
                'recommendation': self.get_ai_recommendation(strategy, pips_profit, profit_usd)
            }
            
        except Exception as e:
            print(f"Error evaluando trade {position.ticket}: {e}")
            return None
    
    def get_ai_recommendation(self, strategy, pips_profit, profit_usd):
        """Obtener recomendación específica de AI"""
        if strategy == "PROTECT_AGGRESSIVELY":
            return {
                'action': 'APPLY_AGGRESSIVE_PROTECTION',
                'breakeven_trigger': 8,
                'trailing_trigger': 12,
                'trailing_distance': 8,
                'reason': f'Trade muy exitoso ({pips_profit:.1f} pips, ${profit_usd:.2f})'
            }
        elif strategy == "PROTECT_MODERATELY":
            return {
                'action': 'APPLY_MODERATE_PROTECTION',
                'breakeven_trigger': 15,
                'trailing_trigger': 20,
                'trailing_distance': 12,
                'reason': f'Trade rentable ({pips_profit:.1f} pips, ${profit_usd:.2f})'
            }
        elif strategy == "MONITOR_CLOSELY":
            return {
                'action': 'MONITOR_ONLY',
                'breakeven_trigger': 25,
                'trailing_trigger': 35,
                'trailing_distance': 15,
                'reason': f'Trade en desarrollo ({pips_profit:.1f} pips)'
            }
        elif strategy == "CUT_LOSSES":
            return {
                'action': 'CONSIDER_CLOSING',
                'reason': f'Trade perdedor significativo ({pips_profit:.1f} pips, ${profit_usd:.2f})'
            }
        else:
            return {
                'action': 'HOLD_CURRENT',
                'reason': f'Trade estable ({pips_profit:.1f} pips)'
            }
    
    def calculate_pips(self, symbol, price_diff):
        """Calcular pips según el símbolo"""
        if 'JPY' in symbol:
            return price_diff * 100
        elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
            return price_diff
        elif 'XAU' in symbol:
            return price_diff * 10
        else:
            return price_diff * 10000
    
    def apply_ai_breakeven(self, position, recommendation):
        """Aplicar break-even inteligente basado en AI"""
        try:
            ticket = position.ticket
            
            if ticket in self.ai_state['breakeven_applied']:
                return False
            
            trigger = recommendation['breakeven_trigger']
            symbol = position.symbol
            
            # Calcular pips actuales
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, position.price_open - position.price_current)
            
            if pips_profit < trigger:
                return False
            
            # Calcular nuevo SL con AI
            point = mt5.symbol_info(symbol).point
            
            if position.type == 0:  # BUY
                if 'XAU' in symbol:
                    new_sl = position.price_open + (3 * point * 10)
                elif 'BTC' in symbol:
                    new_sl = position.price_open + (5 * point)
                else:
                    new_sl = position.price_open + (3 * point * 10)
            else:  # SELL
                if 'XAU' in symbol:
                    new_sl = position.price_open - (3 * point * 10)
                elif 'BTC' in symbol:
                    new_sl = position.price_open - (5 * point)
                else:
                    new_sl = position.price_open - (3 * point * 10)
            
            # Aplicar orden
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 888888,
                "comment": f"AI-BE-{recommendation['action'][:3]}"
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.ai_state['breakeven_applied'].add(ticket)
                print(f"  -> AI BREAKEVEN aplicado: {symbol} #{ticket}")
                print(f"     Pips: {pips_profit:.1f} -> SL: {new_sl:.5f}")
                print(f"     Razon AI: {recommendation['reason']}")
                return True
            else:
                print(f"  -> Error AI breakeven: {result.comment}")
                return False
                
        except Exception as e:
            print(f"Error aplicando AI breakeven: {e}")
            return False
    
    def apply_ai_trailing(self, position, recommendation):
        """Aplicar trailing stop inteligente basado en AI"""
        try:
            if recommendation['action'] not in ['APPLY_AGGRESSIVE_PROTECTION', 'APPLY_MODERATE_PROTECTION']:
                return False
            
            ticket = position.ticket
            symbol = position.symbol
            
            trigger = recommendation['trailing_trigger']
            distance = recommendation['trailing_distance']
            
            # Calcular pips actuales
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, position.price_open - position.price_current)
            
            if pips_profit < trigger:
                return False
            
            # Calcular nuevo trailing SL
            point = mt5.symbol_info(symbol).point
            
            if position.type == 0:  # BUY
                if 'XAU' in symbol:
                    new_sl = position.price_current - (distance * point * 10)
                elif 'BTC' in symbol:
                    new_sl = position.price_current - (distance * point)
                else:
                    new_sl = position.price_current - (distance * point * 10)
                
                # Solo mover SL si mejora
                if position.sl != 0 and new_sl <= position.sl:
                    return False
            else:  # SELL
                if 'XAU' in symbol:
                    new_sl = position.price_current + (distance * point * 10)
                elif 'BTC' in symbol:
                    new_sl = position.price_current + (distance * point)
                else:
                    new_sl = position.price_current + (distance * point * 10)
                
                # Solo mover SL si mejora
                if position.sl != 0 and new_sl >= position.sl:
                    return False
            
            # Aplicar orden
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 888888,
                "comment": f"AI-TR-{recommendation['action'][:3]}"
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.ai_state['trailing_active'].add(ticket)
                print(f"  -> AI TRAILING aplicado: {symbol} #{ticket}")
                print(f"     Pips: {pips_profit:.1f} -> SL: {position.sl:.5f} -> {new_sl:.5f}")
                print(f"     Distancia: {distance} pips")
                return True
            else:
                print(f"  -> Error AI trailing: {result.comment}")
                return False
                
        except Exception as e:
            print(f"Error aplicando AI trailing: {e}")
            return False
    
    def run_ai_evaluation_cycle(self):
        """Ejecutar ciclo completo de evaluación de AI"""
        if not mt5.initialize():
            print("Error conectando a MT5")
            return
        
        positions = mt5.positions_get()
        if not positions:
            print("No hay posiciones para evaluar")
            return
        
        print(f"\\nAI EVALUANDO {len(positions)} POSICIONES ACTIVAS:")
        print("-" * 60)
        
        ai_actions = {
            'breakeven_applied': 0,
            'trailing_applied': 0,
            'recommendations': 0,
            'evaluations': 0
        }
        
        for position in positions:
            evaluation = self.evaluate_trade_performance(position)
            if not evaluation:
                continue
            
            ai_actions['evaluations'] += 1
            
            print(f"\\n{evaluation['symbol']} #{evaluation['ticket']}:")
            print(f"  Performance: {evaluation['pips_profit']:.1f} pips | ${evaluation['profit_usd']:.2f}")
            print(f"  AI Score: {evaluation['ai_score']}")
            print(f"  Estrategia AI: {evaluation['strategy']}")
            print(f"  Señales: {', '.join(evaluation['ai_signals'][:2])}")
            
            recommendation = evaluation['recommendation']
            
            # Aplicar recomendación de AI
            if recommendation['action'] in ['APPLY_AGGRESSIVE_PROTECTION', 'APPLY_MODERATE_PROTECTION']:
                print(f"  Acción AI: {recommendation['action']}")
                
                # Aplicar break-even AI
                if self.apply_ai_breakeven(position, recommendation):
                    ai_actions['breakeven_applied'] += 1
                
                # Aplicar trailing AI
                if self.apply_ai_trailing(position, recommendation):
                    ai_actions['trailing_applied'] += 1
                
                ai_actions['recommendations'] += 1
            
            elif recommendation['action'] == 'CONSIDER_CLOSING':
                print(f"  WARNING AI: {recommendation['reason']}")
                print("  -> Considerar cerrar manualmente esta posición")
            
            else:
                print(f"  Estado AI: {recommendation['reason']}")
        
        print(f"\\n" + "=" * 50)
        print("RESUMEN AI:")
        print(f"  Posiciones evaluadas: {ai_actions['evaluations']}")
        print(f"  Breakeven AI aplicados: {ai_actions['breakeven_applied']}")
        print(f"  Trailing AI aplicados: {ai_actions['trailing_applied']}")
        print(f"  Recomendaciones ejecutadas: {ai_actions['recommendations']}")
        print("=" * 50)
        
        return ai_actions

def main():
    print("=" * 70)
    print("    AI TRADE PERFORMANCE EVALUATOR")
    print("=" * 70)
    print("Sistema inteligente de evaluación y gestión de trades activos")
    print()
    
    evaluator = AITradeEvaluator()
    
    try:
        while True:
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\\n[{current_time}] INICIANDO EVALUACION AI...")
            
            # Ejecutar evaluación de AI
            results = evaluator.run_ai_evaluation_cycle()
            
            if results and (results['breakeven_applied'] > 0 or results['trailing_applied'] > 0):
                print(f"\\nAI ejecutó {results['breakeven_applied'] + results['trailing_applied']} acciones protectoras")
            
            print("\\nEsperando 60 segundos para próxima evaluación...")
            print("Presiona Ctrl+C para detener")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\\n\\nSistema AI detenido por usuario")
    except Exception as e:
        print(f"Error en sistema AI: {e}")
    finally:
        if mt5.initialize():
            mt5.shutdown()
        print("AI Trade Evaluator finalizado")

if __name__ == "__main__":
    main()