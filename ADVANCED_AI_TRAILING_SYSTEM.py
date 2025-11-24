#!/usr/bin/env python
"""
ADVANCED AI TRAILING SYSTEM - SISTEMA AVANZADO DE TRAILING STOP CON IA
=====================================================================
Sistema de trailing stop que se adapta dinámicamente usando AI
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

class AdvancedAITrailingSystem:
    """Sistema avanzado de trailing con inteligencia artificial"""
    
    def __init__(self):
        # Configuración de AI para trailing adaptativo
        self.ai_config = {
            'volatility_threshold': 0.02,      # 2% volatilidad para ajustar
            'momentum_factor': 1.5,            # Factor de momentum
            'profit_protection_ratio': 0.6,    # Proteger 60% de ganancia
            'max_trailing_distance': 50,       # Máximo 50 pips
            'min_trailing_distance': 5,        # Mínimo 5 pips
            'adaptive_step_size': 3,           # Pasos adaptativos
        }
        
        # Estados del sistema AI
        self.ai_state = {
            'position_history': {},           # Historial de precios por posición
            'volatility_data': {},           # Datos de volatilidad
            'trailing_adjustments': {},      # Ajustes de trailing realizados
            'performance_metrics': {}        # Métricas de performance
        }
        
        # Parámetros por tipo de símbolo con AI
        self.symbol_ai_params = {
            'FOREX': {
                'base_distance': 12,
                'volatility_multiplier': 1.0,
                'momentum_sensitivity': 0.8,
                'min_profit_pips': 15
            },
            'GOLD': {
                'base_distance': 8,
                'volatility_multiplier': 0.6,
                'momentum_sensitivity': 1.2,
                'min_profit_pips': 10
            },
            'CRYPTO': {
                'base_distance': 25,
                'volatility_multiplier': 1.5,
                'momentum_sensitivity': 1.0,
                'min_profit_pips': 30
            }
        }
        
        print("Advanced AI Trailing System inicializado")
        print("- Trailing adaptativo basado en volatilidad")
        print("- Protección dinámica de ganancias")
        print("- Ajustes automáticos por momentum")
    
    def identify_symbol_type(self, symbol):
        """Identificar tipo de símbolo para AI"""
        if any(crypto in symbol for crypto in ['BTC', 'ETH', 'ADA', 'XRP']):
            return 'CRYPTO'
        elif 'XAU' in symbol or 'GOLD' in symbol:
            return 'GOLD'
        else:
            return 'FOREX'
    
    def calculate_volatility(self, symbol, position):
        """Calcular volatilidad usando AI"""
        try:
            ticket = position.ticket
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return 0.02  # Volatilidad default
            
            current_price = tick.bid if position.type == 0 else tick.ask
            
            # Almacenar historial de precios
            if ticket not in self.ai_state['position_history']:
                self.ai_state['position_history'][ticket] = []
            
            history = self.ai_state['position_history'][ticket]
            history.append({
                'timestamp': datetime.now(),
                'price': current_price,
                'profit': position.profit
            })
            
            # Mantener solo últimos 20 registros
            if len(history) > 20:
                history.pop(0)
            
            # Calcular volatilidad si tenemos suficientes datos
            if len(history) < 5:
                return 0.02  # Volatilidad default
            
            # Calcular desviación estándar de precios
            prices = [h['price'] for h in history[-10:]]
            mean_price = sum(prices) / len(prices)
            variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
            volatility = (variance ** 0.5) / mean_price
            
            # Almacenar volatilidad calculada
            self.ai_state['volatility_data'][ticket] = volatility
            
            return volatility
            
        except Exception as e:
            print(f"Error calculando volatilidad AI: {e}")
            return 0.02
    
    def calculate_momentum_score(self, position):
        """Calcular score de momentum usando AI"""
        try:
            ticket = position.ticket
            
            if ticket not in self.ai_state['position_history']:
                return 0
            
            history = self.ai_state['position_history'][ticket]
            
            if len(history) < 3:
                return 0
            
            # Analizar tendencia de ganancias
            recent_profits = [h['profit'] for h in history[-5:]]
            
            if len(recent_profits) < 2:
                return 0
            
            # Calcular momentum basado en aceleración de ganancias
            profit_changes = []
            for i in range(1, len(recent_profits)):
                change = recent_profits[i] - recent_profits[i-1]
                profit_changes.append(change)
            
            if not profit_changes:
                return 0
            
            # Score de momentum (-1 a 1)
            avg_change = sum(profit_changes) / len(profit_changes)
            
            # Normalizar score
            if avg_change > 5:
                return 1.0  # Momentum muy fuerte
            elif avg_change > 2:
                return 0.7  # Momentum fuerte
            elif avg_change > 0.5:
                return 0.3  # Momentum moderado
            elif avg_change > -0.5:
                return 0.0  # Sin momentum
            elif avg_change > -2:
                return -0.3  # Momentum negativo
            else:
                return -1.0  # Momentum muy negativo
                
        except Exception as e:
            print(f"Error calculando momentum AI: {e}")
            return 0
    
    def calculate_ai_trailing_distance(self, position):
        """Calcular distancia de trailing óptima usando AI"""
        try:
            symbol = position.symbol
            symbol_type = self.identify_symbol_type(symbol)
            base_params = self.symbol_ai_params[symbol_type]
            
            # Calcular volatilidad y momentum
            volatility = self.calculate_volatility(symbol, position)
            momentum_score = self.calculate_momentum_score(position)
            
            # Distancia base
            base_distance = base_params['base_distance']
            
            # Ajuste por volatilidad
            volatility_adjustment = volatility * base_params['volatility_multiplier'] * 100
            
            # Ajuste por momentum
            momentum_adjustment = momentum_score * base_params['momentum_sensitivity'] * 5
            
            # Calcular distancia final
            ai_distance = base_distance + volatility_adjustment + momentum_adjustment
            
            # Aplicar límites
            ai_distance = max(self.ai_config['min_trailing_distance'], ai_distance)
            ai_distance = min(self.ai_config['max_trailing_distance'], ai_distance)
            
            return round(ai_distance, 1)
            
        except Exception as e:
            print(f"Error calculando distancia AI: {e}")
            return 15  # Default
    
    def should_apply_ai_trailing(self, position):
        """Determinar si aplicar trailing usando AI"""
        try:
            symbol = position.symbol
            symbol_type = self.identify_symbol_type(symbol)
            min_profit_pips = self.symbol_ai_params[symbol_type]['min_profit_pips']
            
            # Calcular pips de ganancia
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(symbol, position.price_open - position.price_current)
            
            # Verificar ganancia mínima
            if pips_profit < min_profit_pips:
                return False, f"Ganancia insuficiente ({pips_profit:.1f} < {min_profit_pips})"
            
            # Análisis de momentum
            momentum_score = self.calculate_momentum_score(position)
            
            # No aplicar trailing si momentum es muy negativo
            if momentum_score < -0.5:
                return False, f"Momentum negativo fuerte ({momentum_score:.2f})"
            
            # Verificar si ya se aplicó trailing recientemente
            ticket = position.ticket
            if ticket in self.ai_state['trailing_adjustments']:
                last_adjustment = self.ai_state['trailing_adjustments'][ticket]['timestamp']
                time_diff = (datetime.now() - last_adjustment).total_seconds()
                
                # Esperar al menos 60 segundos entre ajustes
                if time_diff < 60:
                    return False, "Muy pronto para nuevo ajuste"
            
            return True, f"AI autoriza trailing (pips: {pips_profit:.1f}, momentum: {momentum_score:.2f})"
            
        except Exception as e:
            print(f"Error evaluando AI trailing: {e}")
            return False, "Error en evaluación AI"
    
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
    
    def apply_advanced_ai_trailing(self, position):
        """Aplicar trailing stop avanzado con AI"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            
            # Verificar si debe aplicarse
            should_apply, reason = self.should_apply_ai_trailing(position)
            
            if not should_apply:
                return False, reason
            
            # Calcular distancia AI
            ai_distance = self.calculate_ai_trailing_distance(position)
            
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False, "No se pudo obtener info del símbolo"
            
            point = symbol_info.point
            
            # Calcular nuevo SL
            if position.type == 0:  # BUY
                if 'XAU' in symbol:
                    new_sl = position.price_current - (ai_distance * point * 10)
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    new_sl = position.price_current - (ai_distance * point)
                else:
                    new_sl = position.price_current - (ai_distance * point * 10)
                
                # Verificar mejora
                if position.sl != 0 and new_sl <= position.sl:
                    return False, f"SL no mejora ({new_sl:.5f} <= {position.sl:.5f})"
            else:  # SELL
                if 'XAU' in symbol:
                    new_sl = position.price_current + (ai_distance * point * 10)
                elif any(crypto in symbol for crypto in ['BTC', 'ETH']):
                    new_sl = position.price_current + (ai_distance * point)
                else:
                    new_sl = position.price_current + (ai_distance * point * 10)
                
                # Verificar mejora
                if position.sl != 0 and new_sl >= position.sl:
                    return False, f"SL no mejora ({new_sl:.5f} >= {position.sl:.5f})"
            
            # Aplicar orden
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 999999,
                "comment": f"AI-Trail-{ai_distance:.0f}p"
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                # Registrar ajuste
                self.ai_state['trailing_adjustments'][ticket] = {
                    'timestamp': datetime.now(),
                    'old_sl': position.sl,
                    'new_sl': new_sl,
                    'distance': ai_distance,
                    'reason': reason
                }
                
                return True, f"AI trailing aplicado: dist={ai_distance:.1f}p, SL={new_sl:.5f}"
            else:
                return False, f"Error MT5: {result.comment}"
                
        except Exception as e:
            return False, f"Error aplicando AI trailing: {e}"
    
    def run_ai_trailing_cycle(self):
        """Ejecutar ciclo completo de trailing AI"""
        if not mt5.initialize():
            print("Error conectando a MT5")
            return
        
        positions = mt5.positions_get()
        if not positions:
            print("No hay posiciones para gestionar con AI")
            return
        
        print(f"\\nAI TRAILING GESTIONANDO {len(positions)} POSICIONES:")
        print("=" * 60)
        
        results = {
            'evaluated': 0,
            'trailing_applied': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for position in positions:
            results['evaluated'] += 1
            
            # Calcular métricas actuales
            if position.type == 0:  # BUY
                pips_profit = self.calculate_pips(position.symbol, position.price_current - position.price_open)
            else:  # SELL
                pips_profit = self.calculate_pips(position.symbol, position.price_open - position.price_current)
            
            volatility = self.calculate_volatility(position.symbol, position)
            momentum = self.calculate_momentum_score(position)
            ai_distance = self.calculate_ai_trailing_distance(position)
            
            print(f"\\n{position.symbol} #{position.ticket}:")
            print(f"  Ganancia: {pips_profit:.1f} pips | ${position.profit:.2f}")
            print(f"  AI Volatilidad: {volatility*100:.2f}%")
            print(f"  AI Momentum: {momentum:.2f}")
            print(f"  AI Distancia: {ai_distance:.1f} pips")
            
            # Aplicar AI trailing
            success, message = self.apply_advanced_ai_trailing(position)
            
            if success:
                print(f"  -> AI TRAILING APLICADO: {message}")
                results['trailing_applied'] += 1
            else:
                print(f"  -> {message}")
                if "Error" in message:
                    results['errors'] += 1
                else:
                    results['skipped'] += 1
        
        print(f"\\n" + "=" * 50)
        print("RESUMEN AI TRAILING:")
        print(f"  Posiciones evaluadas: {results['evaluated']}")
        print(f"  Trailing AI aplicados: {results['trailing_applied']}")
        print(f"  Omitidas: {results['skipped']}")
        print(f"  Errores: {results['errors']}")
        print("=" * 50)
        
        return results

def main():
    print("=" * 70)
    print("    ADVANCED AI TRAILING SYSTEM")
    print("=" * 70)
    print("Sistema de trailing stop con inteligencia artificial avanzada")
    print("- Ajustes dinámicos basados en volatilidad")
    print("- Análisis de momentum en tiempo real")
    print("- Protección adaptativa de ganancias")
    print()
    
    ai_trailing = AdvancedAITrailingSystem()
    
    try:
        cycle = 0
        
        while True:
            cycle += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\\n[CICLO AI {cycle:03d}] {current_time}")
            
            # Ejecutar análisis AI
            results = ai_trailing.run_ai_trailing_cycle()
            
            if results and results['trailing_applied'] > 0:
                print(f"\\nAI aplicó {results['trailing_applied']} ajustes de trailing inteligentes")
            
            print("\\nEsperando 45 segundos para próximo ciclo AI...")
            print("Presiona Ctrl+C para detener sistema AI")
            time.sleep(45)
            
    except KeyboardInterrupt:
        print("\\n\\nSistema AI Trailing detenido por usuario")
    except Exception as e:
        print(f"Error en sistema AI: {e}")
    finally:
        if mt5.initialize():
            mt5.shutdown()
        print("Advanced AI Trailing System finalizado")

if __name__ == "__main__":
    main()