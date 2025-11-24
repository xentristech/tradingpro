#!/usr/bin/env python
"""
AI AUTO BREAKEVEN SYSTEM - SISTEMA AUTOMÁTICO DE BREAK-EVEN CON IA
================================================================
Sistema inteligente que aplica break-even automático basado en AI
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

class AIAutoBreakevenSystem:
    """Sistema automático de break-even con inteligencia artificial"""
    
    def __init__(self):
        # Configuración de AI para break-even inteligente
        self.ai_breakeven_config = {
            'min_profit_threshold': 8,         # Mínimo 8 USD para considerar BE
            'risk_assessment_period': 300,     # 5 minutos para evaluar riesgo
            'momentum_weight': 0.4,            # Peso del momentum
            'time_weight': 0.3,                # Peso del tiempo
            'profit_weight': 0.3,              # Peso de la ganancia
            'confidence_threshold': 0.6,       # 60% confianza mínima para BE
        }
        
        # Parámetros dinámicos por símbolo
        self.symbol_breakeven_params = {
            'FOREX': {
                'min_pips_trigger': 12,
                'safety_offset_pips': 3,
                'time_factor': 1.0,
                'volatility_adjustment': 1.0
            },
            'GOLD': {
                'min_pips_trigger': 8,
                'safety_offset_pips': 2,
                'time_factor': 0.8,
                'volatility_adjustment': 0.6
            },
            'CRYPTO': {
                'min_pips_trigger': 20,
                'safety_offset_pips': 5,
                'time_factor': 1.2,
                'volatility_adjustment': 1.5
            }
        }
        
        # Estados del sistema AI
        self.ai_breakeven_state = {
            'positions_analyzed': {},
            'breakeven_applied': set(),
            'risk_assessments': {},
            'performance_tracking': {}
        }
        
        print("AI Auto Breakeven System inicializado")
        print("- Break-even inteligente basado en AI")
        print("- Evaluación de riesgo en tiempo real")
        print("- Protección automática de ganancias")
    
    def identify_symbol_type(self, symbol):
        """Identificar tipo de símbolo"""
        if any(crypto in symbol for crypto in ['BTC', 'ETH', 'ADA', 'XRP']):
            return 'CRYPTO'
        elif 'XAU' in symbol or 'GOLD' in symbol:
            return 'GOLD'
        else:
            return 'FOREX'
    
    def calculate_pips(self, symbol, price_diff):
        """Calcular pips según símbolo"""
        if 'JPY' in symbol:
            return price_diff * 100
        elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
            return price_diff
        elif 'XAU' in symbol:
            return price_diff * 10
        else:
            return price_diff * 10000
    
    def assess_breakeven_risk(self, position):
        """Evaluación de riesgo para break-even usando AI"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            entry_time = datetime.fromtimestamp(position.time)
            duration_minutes = (datetime.now() - entry_time).total_seconds() / 60
            
            # Calcular pips de ganancia
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, position.price_open - position.price_current)
            
            # Inicializar score de riesgo
            risk_score = 0.0
            risk_factors = []
            
            # 1. Análisis de ganancia (peso: 30%)
            profit_score = 0
            if position.profit >= 50:
                profit_score = 0.9
                risk_factors.append("PROFIT_HIGH")
            elif position.profit >= 25:
                profit_score = 0.7
                risk_factors.append("PROFIT_GOOD")
            elif position.profit >= 15:
                profit_score = 0.5
                risk_factors.append("PROFIT_MODERATE")
            elif position.profit >= 8:
                profit_score = 0.3
                risk_factors.append("PROFIT_LOW")
            else:
                profit_score = 0.1
                risk_factors.append("PROFIT_MINIMAL")
            
            risk_score += profit_score * self.ai_breakeven_config['profit_weight']
            
            # 2. Análisis temporal (peso: 30%)
            time_score = 0
            if duration_minutes > 60:  # >1 hora
                if pips_profit > 0:
                    time_score = 0.8
                    risk_factors.append("TIME_MATURE_POSITIVE")
                else:
                    time_score = 0.2
                    risk_factors.append("TIME_MATURE_NEGATIVE")
            elif duration_minutes > 30:  # >30 min
                if pips_profit > 5:
                    time_score = 0.6
                    risk_factors.append("TIME_DEVELOPING")
                else:
                    time_score = 0.4
                    risk_factors.append("TIME_SLOW_DEVELOPMENT")
            elif duration_minutes > 15:  # >15 min
                time_score = 0.5
                risk_factors.append("TIME_RECENT")
            else:  # <15 min
                time_score = 0.3
                risk_factors.append("TIME_VERY_RECENT")
            
            risk_score += time_score * self.ai_breakeven_config['time_weight']
            
            # 3. Análisis de momentum (peso: 40%)
            momentum_score = 0
            
            # Simular momentum basado en la relación profit/time
            if duration_minutes > 0:
                profit_per_minute = position.profit / duration_minutes
                
                if profit_per_minute > 1.5:  # >$1.5/min
                    momentum_score = 0.9
                    risk_factors.append("MOMENTUM_VERY_STRONG")
                elif profit_per_minute > 0.8:  # >$0.8/min
                    momentum_score = 0.7
                    risk_factors.append("MOMENTUM_STRONG")
                elif profit_per_minute > 0.3:  # >$0.3/min
                    momentum_score = 0.5
                    risk_factors.append("MOMENTUM_MODERATE")
                elif profit_per_minute > 0.1:  # >$0.1/min
                    momentum_score = 0.3
                    risk_factors.append("MOMENTUM_WEAK")
                else:
                    momentum_score = 0.1
                    risk_factors.append("MOMENTUM_VERY_WEAK")
            
            risk_score += momentum_score * self.ai_breakeven_config['momentum_weight']
            
            # Almacenar evaluación
            self.ai_breakeven_state['risk_assessments'][ticket] = {
                'timestamp': datetime.now(),
                'risk_score': risk_score,
                'risk_factors': risk_factors,
                'pips_profit': pips_profit,
                'profit_usd': position.profit,
                'duration_minutes': duration_minutes
            }
            
            return risk_score, risk_factors
            
        except Exception as e:
            print(f"Error en evaluación de riesgo AI: {e}")
            return 0.0, ["ERROR_ASSESSMENT"]
    
    def should_apply_ai_breakeven(self, position):
        """Determinar si aplicar break-even usando AI"""
        try:
            ticket = position.ticket
            symbol = position.symbol
            symbol_type = self.identify_symbol_type(symbol)
            params = self.symbol_breakeven_params[symbol_type]
            
            # Verificar si ya se aplicó
            if ticket in self.ai_breakeven_state['breakeven_applied']:
                return False, "Break-even ya aplicado"
            
            # Calcular pips de ganancia
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, position.price_open - position.price_current)
            
            # Verificar ganancia mínima
            if pips_profit < params['min_pips_trigger']:
                return False, f"Pips insuficientes ({pips_profit:.1f} < {params['min_pips_trigger']})"
            
            # Verificar ganancia mínima en USD
            if position.profit < self.ai_breakeven_config['min_profit_threshold']:
                return False, f"Profit insuficiente (${position.profit:.2f} < ${self.ai_breakeven_config['min_profit_threshold']})"
            
            # Evaluación de riesgo AI
            risk_score, risk_factors = self.assess_breakeven_risk(position)
            
            # Verificar confianza AI
            if risk_score < self.ai_breakeven_config['confidence_threshold']:
                return False, f"Confianza AI baja ({risk_score:.2f} < {self.ai_breakeven_config['confidence_threshold']:.2f})"
            
            return True, f"AI autoriza BE (score: {risk_score:.2f}, pips: {pips_profit:.1f})"
            
        except Exception as e:
            return False, f"Error evaluando BE: {e}"
    
    def apply_ai_breakeven(self, position):
        """Aplicar break-even inteligente con AI"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            symbol_type = self.identify_symbol_type(symbol)
            params = self.symbol_breakeven_params[symbol_type]
            
            # Verificar autorización AI
            should_apply, reason = self.should_apply_ai_breakeven(position)
            
            if not should_apply:
                return False, reason
            
            # Calcular nuevo SL con offset de seguridad
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False, "No se pudo obtener info del símbolo"
            
            point = symbol_info.point
            safety_offset = params['safety_offset_pips']
            
            if position.type == 0:  # BUY
                if 'XAU' in symbol:
                    new_sl = position.price_open + (safety_offset * point * 10)
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    new_sl = position.price_open + (safety_offset * point)
                else:
                    new_sl = position.price_open + (safety_offset * point * 10)
            else:  # SELL
                if 'XAU' in symbol:
                    new_sl = position.price_open - (safety_offset * point * 10)
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    new_sl = position.price_open - (safety_offset * point)
                else:
                    new_sl = position.price_open - (safety_offset * point * 10)
            
            # Aplicar orden
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 777777,
                "comment": f"AI-BE-{safety_offset}p"
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                # Registrar break-even aplicado
                self.ai_breakeven_state['breakeven_applied'].add(ticket)
                
                # Registrar performance
                self.ai_breakeven_state['performance_tracking'][ticket] = {
                    'timestamp': datetime.now(),
                    'old_sl': position.sl,
                    'new_sl': new_sl,
                    'profit_protected': position.profit,
                    'reason': reason
                }
                
                return True, f"AI BE aplicado: SL={new_sl:.5f}, offset={safety_offset}p"
            else:
                return False, f"Error MT5: {result.comment}"
                
        except Exception as e:
            return False, f"Error aplicando AI breakeven: {e}"
    
    def run_ai_breakeven_cycle(self):
        """Ejecutar ciclo completo de break-even AI"""
        if not mt5.initialize():
            print("Error conectando a MT5")
            return
        
        positions = mt5.positions_get()
        if not positions:
            print("No hay posiciones para evaluar break-even")
            return
        
        print(f"\\nAI BREAKEVEN EVALUANDO {len(positions)} POSICIONES:")
        print("=" * 60)
        
        results = {
            'evaluated': 0,
            'breakeven_applied': 0,
            'already_protected': 0,
            'insufficient_profit': 0,
            'low_confidence': 0,
            'errors': 0
        }
        
        for position in positions:
            results['evaluated'] += 1
            
            # Verificar si ya tiene break-even
            if position.ticket in self.ai_breakeven_state['breakeven_applied']:
                results['already_protected'] += 1
                continue
            
            # Calcular métricas
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(position.symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(position.symbol, position.price_open - position.price_current)
            
            # Evaluación AI
            risk_score, risk_factors = self.assess_breakeven_risk(position)
            
            print(f"\\n{position.symbol} #{position.ticket}:")
            print(f"  Ganancia: {pips_profit:.1f} pips | ${position.profit:.2f}")
            print(f"  AI Risk Score: {risk_score:.2f}")
            print(f"  Factores: {', '.join(risk_factors[:2])}")
            
            # Intentar aplicar break-even
            success, message = self.apply_ai_breakeven(position)
            
            if success:
                print(f"  -> AI BREAKEVEN APLICADO: {message}")
                results['breakeven_applied'] += 1
            else:
                print(f"  -> {message}")
                
                if "insuficient" in message.lower():
                    results['insufficient_profit'] += 1
                elif "confianza" in message.lower():
                    results['low_confidence'] += 1
                elif "error" in message.lower():
                    results['errors'] += 1
        
        print(f"\\n" + "=" * 50)
        print("RESUMEN AI BREAKEVEN:")
        print(f"  Posiciones evaluadas: {results['evaluated']}")
        print(f"  Breakeven AI aplicados: {results['breakeven_applied']}")
        print(f"  Ya protegidas: {results['already_protected']}")
        print(f"  Profit insuficiente: {results['insufficient_profit']}")
        print(f"  Confianza baja: {results['low_confidence']}")
        print(f"  Errores: {results['errors']}")
        print("=" * 50)
        
        return results

def main():
    print("=" * 70)
    print("    AI AUTO BREAKEVEN SYSTEM")
    print("=" * 70)
    print("Sistema automático de break-even con inteligencia artificial")
    print("- Evaluación de riesgo en tiempo real")
    print("- Protección inteligente de ganancias")
    print("- Break-even automático basado en AI")
    print()
    
    ai_breakeven = AIAutoBreakevenSystem()
    
    try:
        cycle = 0
        
        while True:
            cycle += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\\n[CICLO AI BE {cycle:03d}] {current_time}")
            
            # Ejecutar evaluación AI
            results = ai_breakeven.run_ai_breakeven_cycle()
            
            if results and results['breakeven_applied'] > 0:
                print(f"\\nAI protegió {results['breakeven_applied']} posiciones con break-even inteligente")
            
            print("\\nEsperando 30 segundos para próxima evaluación AI...")
            print("Presiona Ctrl+C para detener sistema AI")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\\n\\nSistema AI Breakeven detenido por usuario")
    except Exception as e:
        print(f"Error en sistema AI: {e}")
    finally:
        if mt5.initialize():
            mt5.shutdown()
        print("AI Auto Breakeven System finalizado")

if __name__ == "__main__":
    main()