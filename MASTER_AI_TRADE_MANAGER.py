#!/usr/bin/env python
"""
MASTER AI TRADE MANAGER - SISTEMA MAESTRO DE GESTION DE TRADES CON IA
===================================================================
Sistema integrado que combina todos los componentes AI para gestión completa
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

# Importar todos los sistemas AI
from AI_TRADE_PERFORMANCE_EVALUATOR import AITradeEvaluator
from AI_AUTO_BREAKEVEN_SYSTEM import AIAutoBreakevenSystem
from ADVANCED_AI_TRAILING_SYSTEM import AdvancedAITrailingSystem

class MasterAITradeManager:
    """Sistema maestro que integra todos los componentes AI"""
    
    def __init__(self):
        print("=" * 70)
        print("    MASTER AI TRADE MANAGER - SISTEMA INTEGRADO")
        print("=" * 70)
        print("Inicializando todos los sistemas AI...")
        
        # Inicializar todos los subsistemas AI
        self.performance_evaluator = AITradeEvaluator()
        self.breakeven_system = AIAutoBreakevenSystem()
        self.trailing_system = AdvancedAITrailingSystem()
        
        # Configuración maestra
        self.master_config = {
            'performance_cycle_interval': 60,    # Evaluar performance cada 60s
            'breakeven_cycle_interval': 30,      # Evaluar breakeven cada 30s
            'trailing_cycle_interval': 45,       # Evaluar trailing cada 45s
            'master_cycle_interval': 90,         # Ciclo maestro cada 90s
            'min_positions_for_analysis': 1,     # Mínimo 1 posición para análisis
        }
        
        # Estados maestros
        self.master_state = {
            'last_performance_check': None,
            'last_breakeven_check': None,
            'last_trailing_check': None,
            'total_ai_actions': 0,
            'ai_recommendations_given': 0,
            'positions_under_management': set()
        }
        
        print("\\n✅ SISTEMAS AI INICIALIZADOS:")
        print("   1. AI Trade Performance Evaluator")
        print("   2. AI Auto Breakeven System")  
        print("   3. Advanced AI Trailing System")
        print("\\n🤖 MASTER AI TRADE MANAGER LISTO")
        print("=" * 70)
    
    def get_current_positions_summary(self):
        """Obtener resumen de posiciones actuales"""
        if not mt5.initialize():
            return None
        
        positions = mt5.positions_get()
        if not positions:
            return {"count": 0, "positions": []}
        
        summary = {
            "count": len(positions),
            "total_profit": sum(p.profit for p in positions),
            "profitable": len([p for p in positions if p.profit > 0]),
            "losing": len([p for p in positions if p.profit < 0]),
            "positions": positions
        }
        
        return summary
    
    def should_run_performance_analysis(self):
        """Determinar si ejecutar análisis de performance"""
        if not self.master_state['last_performance_check']:
            return True
        
        time_diff = (datetime.now() - self.master_state['last_performance_check']).total_seconds()
        return time_diff >= self.master_config['performance_cycle_interval']
    
    def should_run_breakeven_analysis(self):
        """Determinar si ejecutar análisis de breakeven"""
        if not self.master_state['last_breakeven_check']:
            return True
        
        time_diff = (datetime.now() - self.master_state['last_breakeven_check']).total_seconds()
        return time_diff >= self.master_config['breakeven_cycle_interval']
    
    def should_run_trailing_analysis(self):
        """Determinar si ejecutar análisis de trailing"""
        if not self.master_state['last_trailing_check']:
            return True
        
        time_diff = (datetime.now() - self.master_state['last_trailing_check']).total_seconds()
        return time_diff >= self.master_config['trailing_cycle_interval']
    
    def run_integrated_ai_analysis(self):
        """Ejecutar análisis AI integrado completo"""
        # Obtener resumen de posiciones
        positions_summary = self.get_current_positions_summary()
        
        if not positions_summary or positions_summary['count'] < self.master_config['min_positions_for_analysis']:
            return {
                'status': 'NO_POSITIONS',
                'message': f"Sin posiciones para análisis (mínimo: {self.master_config['min_positions_for_analysis']})",
                'actions_taken': 0
            }
        
        print(f"\\n🎯 ANÁLISIS MAESTRO AI - {positions_summary['count']} POSICIONES")
        print(f"   Rentables: {positions_summary['profitable']} | Perdedoras: {positions_summary['losing']}")
        print(f"   P&L Total: ${positions_summary['total_profit']:.2f}")
        print("-" * 60)
        
        total_actions = 0
        analysis_results = {}
        
        # 1. ANÁLISIS DE PERFORMANCE (si corresponde)
        if self.should_run_performance_analysis():
            print("\\n🧠 EJECUTANDO ANÁLISIS DE PERFORMANCE AI...")
            performance_results = self.performance_evaluator.run_ai_evaluation_cycle()
            
            if performance_results:
                analysis_results['performance'] = performance_results
                total_actions += performance_results.get('breakeven_applied', 0)
                total_actions += performance_results.get('trailing_applied', 0)
                self.master_state['ai_recommendations_given'] += performance_results.get('recommendations', 0)
                
                print(f"   ✅ Performance AI: {performance_results.get('evaluations', 0)} evaluaciones")
            
            self.master_state['last_performance_check'] = datetime.now()
        
        # 2. ANÁLISIS DE BREAKEVEN (si corresponde)
        if self.should_run_breakeven_analysis():
            print("\\n🛡️ EJECUTANDO ANÁLISIS DE BREAKEVEN AI...")
            breakeven_results = self.breakeven_system.run_ai_breakeven_cycle()
            
            if breakeven_results:
                analysis_results['breakeven'] = breakeven_results
                total_actions += breakeven_results.get('breakeven_applied', 0)
                
                if breakeven_results.get('breakeven_applied', 0) > 0:
                    print(f"   ✅ {breakeven_results['breakeven_applied']} break-even aplicados por AI")
                else:
                    print(f"   ℹ️ Break-even AI: {breakeven_results.get('insufficient_profit', 0)} con profit insuficiente")
            
            self.master_state['last_breakeven_check'] = datetime.now()
        
        # 3. ANÁLISIS DE TRAILING (si corresponde)
        if self.should_run_trailing_analysis():
            print("\\n🔄 EJECUTANDO ANÁLISIS DE TRAILING AI...")
            trailing_results = self.trailing_system.run_ai_trailing_cycle()
            
            if trailing_results:
                analysis_results['trailing'] = trailing_results
                total_actions += trailing_results.get('trailing_applied', 0)
                
                if trailing_results.get('trailing_applied', 0) > 0:
                    print(f"   ✅ {trailing_results['trailing_applied']} trailing stops aplicados por AI")
                else:
                    print(f"   ℹ️ Trailing AI: {trailing_results.get('skipped', 0)} posiciones omitidas")
            
            self.master_state['last_trailing_check'] = datetime.now()
        
        # Actualizar estados maestros
        self.master_state['total_ai_actions'] += total_actions
        
        return {
            'status': 'COMPLETED',
            'positions_analyzed': positions_summary['count'],
            'total_actions_taken': total_actions,
            'analysis_results': analysis_results,
            'summary': f"{total_actions} acciones AI ejecutadas en {positions_summary['count']} posiciones"
        }
    
    def display_master_summary(self, cycle_results):
        """Mostrar resumen del ciclo maestro"""
        print("\\n" + "=" * 60)
        print("📊 RESUMEN MAESTRO AI:")
        print("=" * 60)
        
        if cycle_results['status'] == 'NO_POSITIONS':
            print(f"   {cycle_results['message']}")
        else:
            print(f"   Posiciones analizadas: {cycle_results['positions_analyzed']}")
            print(f"   Acciones AI ejecutadas: {cycle_results['total_actions_taken']}")
            print(f"   Total acciones históricas: {self.master_state['total_ai_actions']}")
            
            # Detalles por subsistema
            if 'analysis_results' in cycle_results:
                results = cycle_results['analysis_results']
                
                if 'performance' in results:
                    perf = results['performance']
                    print(f"   Performance AI: {perf.get('evaluations', 0)} eval, {perf.get('recommendations', 0)} rec")
                
                if 'breakeven' in results:
                    be = results['breakeven']
                    print(f"   Breakeven AI: {be.get('breakeven_applied', 0)} aplicados")
                
                if 'trailing' in results:
                    tr = results['trailing']
                    print(f"   Trailing AI: {tr.get('trailing_applied', 0)} aplicados")
        
        print("=" * 60)
    
    def run_master_ai_cycle(self, duration_minutes=None):
        """Ejecutar ciclo maestro AI continuamente"""
        print("\\n🚀 INICIANDO SISTEMA MAESTRO AI...")
        print(f"   Intervalos: Performance({self.master_config['performance_cycle_interval']}s), "
              f"Breakeven({self.master_config['breakeven_cycle_interval']}s), "
              f"Trailing({self.master_config['trailing_cycle_interval']}s)")
        
        if duration_minutes:
            print(f"   Duración: {duration_minutes} minutos")
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
        else:
            end_time = None
            print("   Duración: Indefinida (Ctrl+C para detener)")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # Verificar si debe terminar
                if end_time and datetime.now() >= end_time:
                    print(f"\\n⏰ Tiempo completado: {duration_minutes} minutos")
                    break
                
                print(f"\\n🤖 [MASTER CYCLE {cycle:03d}] {current_time}")
                
                # Ejecutar análisis AI integrado
                cycle_results = self.run_integrated_ai_analysis()
                
                # Mostrar resumen
                self.display_master_summary(cycle_results)
                
                # Esperar antes del próximo ciclo maestro
                wait_time = self.master_config['master_cycle_interval']
                print(f"\\n⏳ Esperando {wait_time} segundos para próximo ciclo maestro...")
                print("   (Ctrl+C para detener sistema)")
                
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\\n\\n⏹️ Sistema Maestro AI detenido por usuario")
        except Exception as e:
            print(f"\\n❌ Error en sistema maestro: {e}")
        finally:
            if mt5.initialize():
                mt5.shutdown()
            print("\\n✅ Master AI Trade Manager finalizado correctamente")
            print(f"   Total acciones AI ejecutadas: {self.master_state['total_ai_actions']}")
            print(f"   Total recomendaciones dadas: {self.master_state['ai_recommendations_given']}")

def main():
    print("MASTER AI TRADE MANAGER")
    print("Sistema integrado de gestión de trades con IA")
    print()
    
    # Crear instancia del sistema maestro
    master_ai = MasterAITradeManager()
    
    try:
        print("\\n¿Ejecutar análisis inmediato? (s/n): ", end="")
        if input().lower().startswith('s'):
            print("\\n🔍 EJECUTANDO ANÁLISIS INMEDIATO...")
            immediate_results = master_ai.run_integrated_ai_analysis()
            master_ai.display_master_summary(immediate_results)
        
        print("\\n¿Ejecutar sistema maestro continuo? (s/n): ", end="")
        if input().lower().startswith('s'):
            duration_input = input("¿Por cuántos minutos? (Enter = indefinido): ").strip()
            duration = int(duration_input) if duration_input.isdigit() else None
            
            master_ai.run_master_ai_cycle(duration)
        else:
            print("✅ Análisis completado")
            
    except Exception as e:
        print(f"Error en main: {e}")

if __name__ == "__main__":
    main()