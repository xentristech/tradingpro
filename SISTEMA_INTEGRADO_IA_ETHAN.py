#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 SISTEMA INTEGRADO DE ANÁLISIS Y SEÑALES CON IA
Combina el análisis de mercado con el generador de señales existente
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import MetaTrader5 as mt5
import time

# Configurar paths
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))
sys.path.insert(0, str(project_path / 'src'))

# Importar módulos existentes del sistema
try:
    from src.signals.advanced_signal_generator import AdvancedSignalGenerator
    from src.ai.ollama_client import OllamaClient
    from src.data.twelvedata_client import TwelveDataClient
    from src.notifiers.telegram_notifier import TelegramNotifier
    print("✅ Módulos del sistema cargados correctamente")
except ImportError as e:
    print(f"⚠️ Algunos módulos no están disponibles: {e}")
    print("Continuando con funcionalidad básica...")

class IntegratedAISystem:
    """Sistema integrado que combina análisis personal con señales existentes"""
    
    def __init__(self, operator_name="ETHAN"):
        self.operator_name = operator_name
        self.start_time = datetime.now()
        
        # Intentar cargar componentes existentes
        try:
            self.signal_generator = AdvancedSignalGenerator()
            self.ollama = OllamaClient()
            self.td_client = TwelveDataClient()
            self.telegram = TelegramNotifier()
            self.has_full_system = True
        except:
            self.has_full_system = False
            print("⚠️ Sistema funcionando en modo básico")
    
    def personal_greeting(self):
        """Saludo ultra personalizado para ETHAN"""
        hour = datetime.now().hour
        day_name = datetime.now().strftime('%A')
        
        # Saludos especiales para ETHAN
        if self.operator_name == "ETHAN":
            print("\n" + "🌟"*30)
            print(f"   ¡BIENVENIDO {self.operator_name}! - ELITE TRADER")
            print("🌟"*30)
            
            if hour < 12:
                print(f"\n   ☀️ ¡Buenos días campeón! Listo para conquistar el mercado?")
            elif hour < 18:
                print(f"\n   🚀 ¡Buenas tardes maestro! Los mercados te esperan")
            else:
                print(f"\n   🌙 ¡Buenas noches guerrero! Sesión nocturna activada")
                
            print(f"   📅 {day_name} - {datetime.now().strftime('%d/%m/%Y')}")
            print(f"   ⏰ {datetime.now().strftime('%H:%M:%S')}")
            
            # Mensaje motivacional especial
            print("\n   💎 RECORDATORIO DEL DÍA:")
            messages = [
                "El éxito es la suma de pequeños esfuerzos repetidos día tras día",
                "Los grandes traders no nacen, se forjan con disciplina",
                "Cada operación es una oportunidad de aprender y mejorar",
                "La paciencia es la clave del trading exitoso",
                "Gestiona el riesgo y las ganancias llegarán"
            ]
            import random
            print(f"   '{random.choice(messages)}'")
            print()
    
    def check_existing_signals(self):
        """Verificar si hay señales del sistema existente"""
        print("\n🔍 VERIFICANDO SEÑALES EXISTENTES...")
        print("-"*60)
        
        signals_file = project_path / "logs" / "signals.json"
        
        if signals_file.exists():
            try:
                import json
                with open(signals_file, 'r') as f:
                    signals = json.load(f)
                    
                if signals and isinstance(signals, list):
                    recent = signals[-5:] if len(signals) > 5 else signals
                    print(f"✅ {len(signals)} señales encontradas en el sistema")
                    
                    print("\n📊 Últimas señales generadas:")
                    for sig in recent:
                        symbol = sig.get('symbol', 'N/A')
                        action = sig.get('action', 'N/A')
                        confidence = sig.get('confidence', 0)
                        time = sig.get('timestamp', '')
                        
                        if confidence > 70:
                            print(f"   🟢 {symbol}: {action} ({confidence:.1f}%) - {time}")
                        elif confidence > 50:
                            print(f"   🟡 {symbol}: {action} ({confidence:.1f}%) - {time}")
                        else:
                            print(f"   🔴 {symbol}: {action} ({confidence:.1f}%) - {time}")
                    
                    return True
            except Exception as e:
                print(f"⚠️ Error leyendo señales: {e}")
        else:
            print("📝 No hay señales previas registradas")
            
        return False
    
    def run_signal_generator(self):
        """Ejecutar el generador de señales existente"""
        if not self.has_full_system:
            print("\n⚠️ Generador de señales no disponible")
            return
            
        print("\n🤖 ACTIVANDO GENERADOR DE SEÑALES AVANZADO...")
        print("-"*60)
        
        try:
            # Ejecutar generador
            signals = self.signal_generator.generate_signals()
            
            if signals:
                print(f"✅ {len(signals)} nuevas señales generadas")
                
                for signal in signals:
                    print(f"\n📍 Señal: {signal.symbol}")
                    print(f"   Acción: {signal.action}")
                    print(f"   Confianza: {signal.confidence:.1f}%")
                    print(f"   Entry: {signal.entry_price:.5f}")
                    print(f"   SL: {signal.stop_loss:.5f}")
                    print(f"   TP: {signal.take_profit:.5f}")
                    
                    # Enviar a Telegram si está configurado
                    if hasattr(self, 'telegram'):
                        self.telegram.send_signal(signal)
            else:
                print("📊 No hay señales nuevas en este momento")
                
        except Exception as e:
            print(f"❌ Error generando señales: {e}")
    
    def analyze_with_ollama(self):
        """Análisis con IA de Ollama"""
        if not self.has_full_system or not hasattr(self, 'ollama'):
            print("\n⚠️ Ollama no disponible para análisis IA")
            return
            
        print("\n🧠 ANÁLISIS CON INTELIGENCIA ARTIFICIAL...")
        print("-"*60)
        
        try:
            # Obtener datos del mercado
            market_data = self.get_market_summary()
            
            # Crear prompt para Ollama
            prompt = f"""
            Analiza las siguientes condiciones de mercado y genera recomendaciones de trading:
            
            {market_data}
            
            Proporciona:
            1. Evaluación general del mercado
            2. Mejor oportunidad de trading ahora
            3. Niveles clave a vigilar
            4. Gestión de riesgo recomendada
            
            Sé específico y directo.
            """
            
            response = self.ollama.generate_response(prompt)
            
            print("💡 ANÁLISIS IA:")
            print(response)
            
        except Exception as e:
            print(f"❌ Error en análisis IA: {e}")
    
    def get_market_summary(self):
        """Obtener resumen del mercado"""
        summary = []
        symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD', 'GBPUSD']
        
        if mt5.initialize():
            for symbol in symbols:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    summary.append(f"{symbol}: Bid={tick.bid:.5f} Ask={tick.ask:.5f}")
            mt5.shutdown()
            
        return "\n".join(summary) if summary else "No hay datos disponibles"
    
    def system_health_check(self):
        """Verificar salud del sistema"""
        print("\n🏥 VERIFICACIÓN DE SALUD DEL SISTEMA")
        print("-"*60)
        
        health_status = {
            'MT5': False,
            'Ollama': False,
            'TwelveData': False,
            'Telegram': False,
            'Signals': False
        }
        
        # Verificar MT5
        if mt5.initialize():
            health_status['MT5'] = True
            mt5.shutdown()
            
        # Verificar otros componentes
        if self.has_full_system:
            if hasattr(self, 'ollama'):
                health_status['Ollama'] = True
            if hasattr(self, 'td_client'):
                health_status['TwelveData'] = True
            if hasattr(self, 'telegram'):
                health_status['Telegram'] = True
            if hasattr(self, 'signal_generator'):
                health_status['Signals'] = True
        
        # Mostrar estado
        for component, status in health_status.items():
            if status:
                print(f"   ✅ {component}: OPERATIVO")
            else:
                print(f"   ❌ {component}: NO DISPONIBLE")
                
        # Calcular salud general
        operational = sum(health_status.values())
        total = len(health_status)
        health_pct = (operational / total) * 100
        
        print(f"\n   📊 Salud del sistema: {health_pct:.0f}% ({operational}/{total} componentes)")
        
        if health_pct == 100:
            print("   🟢 SISTEMA 100% OPERATIVO")
        elif health_pct >= 60:
            print("   🟡 SISTEMA PARCIALMENTE OPERATIVO")
        else:
            print("   🔴 SISTEMA CON PROBLEMAS CRÍTICOS")
            
        return health_status
    
    def run_complete_cycle(self):
        """Ejecutar ciclo completo de análisis"""
        
        # Saludo personal
        self.personal_greeting()
        
        # Verificar salud del sistema
        health = self.system_health_check()
        
        # Verificar señales existentes
        self.check_existing_signals()
        
        # Si el sistema está saludable, generar nuevas señales
        if health['MT5'] and health['Signals']:
            self.run_signal_generator()
            
        # Análisis con IA si está disponible
        if health['Ollama']:
            self.analyze_with_ollama()
            
        # Estadísticas de sesión
        print("\n📈 ESTADÍSTICAS DE SESIÓN")
        print("-"*60)
        runtime = datetime.now() - self.start_time
        print(f"   ⏱️ Tiempo ejecutando: {runtime}")
        print(f"   🔄 Próxima actualización: en 5 minutos")
        
        print("\n" + "="*60)
        print(f"   ✅ CICLO COMPLETADO PARA {self.operator_name}")
        print("="*60)

def main():
    """Función principal"""
    
    # Configurar nombre del operador
    operator_name = os.getenv("OPERATOR_NAME", "ETHAN")
    
    # Crear sistema integrado
    system = IntegratedAISystem(operator_name)
    
    try:
        print("\n🚀 INICIANDO SISTEMA INTEGRADO DE TRADING CON IA")
        print("="*60)
        
        # Ejecutar ciclo inicial
        system.run_complete_cycle()
        
        print("\n⏳ Sistema en modo automático - Actualización cada 5 minutos")
        print("   Presiona Ctrl+C para detener")
        
        # Loop continuo
        cycle_count = 1
        while True:
            time.sleep(300)  # 5 minutos
            cycle_count += 1
            
            print(f"\n\n{'='*60}")
            print(f"   🔄 CICLO #{cycle_count}")
            print(f"{'='*60}")
            
            system.run_complete_cycle()
            
    except KeyboardInterrupt:
        print(f"\n\n👋 ¡Hasta pronto {operator_name}! Sistema detenido correctamente")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    main()
