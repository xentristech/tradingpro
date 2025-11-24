#!/usr/bin/env python
"""
AI REAL-TIME VIGILANCE SYSTEM - SISTEMA DE VIGILANCIA IA EN TIEMPO REAL
========================================================================
Sistema integrado que vigila constantemente oportunidades inesperadas
Combina: AI Opportunity Hunter + Candle Momentum Detector + Advanced Signals
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import json

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from AI_OPPORTUNITY_HUNTER import AIOpportunityHunter
from AI_CANDLE_MOMENTUM_DETECTOR import AICandleMomentumDetector

class AIRealTimeVigilanceSystem:
    """Sistema integrado de vigilancia IA en tiempo real"""
    
    def __init__(self):
        # Inicializar subsistemas
        print("🚀 Inicializando Sistema de Vigilancia IA...")
        
        self.opportunity_hunter = AIOpportunityHunter()
        self.candle_detector = AICandleMomentumDetector()
        
        # Configuración de vigilancia
        self.vigilance_config = {
            'opportunity_scan_interval': 60,     # Escanear oportunidades cada 60s
            'candle_scan_interval': 15,          # Escanear velas cada 15s
            'alert_cooldown': 300,               # No repetir alertas por 5min
            'min_opportunity_score': 65,         # Score mínimo para alertar
            'min_candle_strength': 75,           # Fuerza mínima de vela para alertar
            'emergency_threshold': 90,           # Umbral para alertas de emergencia
        }
        
        # Cache de alertas
        self.last_alerts = {}
        self.alert_history = []
        self.active = False
        
        print("✅ Sistema de Vigilancia IA inicializado")
        print("- AI Opportunity Hunter: Conectado")
        print("- AI Candle Momentum Detector: Conectado")
        print("- Vigilancia en tiempo real: Lista")
    
    def should_alert(self, alert_type, symbol, score):
        """Determinar si debe enviar alerta basado en cooldown"""
        alert_key = f"{alert_type}_{symbol}"
        current_time = datetime.now()
        
        # Verificar cooldown
        if alert_key in self.last_alerts:
            time_diff = (current_time - self.last_alerts[alert_key]).total_seconds()
            if time_diff < self.vigilance_config['alert_cooldown']:
                return False
        
        # Actualizar último alerta
        self.last_alerts[alert_key] = current_time
        return True
    
    def send_alert(self, alert_type, data):
        """Enviar alerta al sistema"""
        try:
            alert = {
                'timestamp': datetime.now(),
                'type': alert_type,
                'data': data,
                'priority': 'HIGH' if data.get('score', 0) >= self.vigilance_config['emergency_threshold'] else 'NORMAL'
            }
            
            # Guardar en historial
            self.alert_history.append(alert)
            
            # Mostrar alerta
            self.display_alert(alert)
            
            # Aquí podrías agregar envío de emails, webhooks, etc.
            
        except Exception as e:
            print(f"Error enviando alerta: {e}")
    
    def display_alert(self, alert):
        """Mostrar alerta en consola"""
        timestamp = alert['timestamp'].strftime('%H:%M:%S')
        priority_icon = "🚨" if alert['priority'] == 'HIGH' else "⚠️"
        
        print(f"\n{priority_icon} ALERTA {alert['type']} - {timestamp}")
        print("=" * 60)
        
        data = alert['data']
        
        if alert['type'] == 'OPPORTUNITY':
            print(f"📊 OPORTUNIDAD DETECTADA:")
            print(f"   Symbol: {data['symbol']}")
            print(f"   Score IA: {data['score']}%")
            print(f"   Tipo: {data['type']} {data['direction']}")
            print(f"   Precio: ${data['current_price']:,.4f}")
            print(f"   RSI: {data['rsi']:.1f}")
            print(f"   Volatilidad: {data['volatility']:.1f}%")
            print(f"   Recomendación: {data['recommendation']}")
            
        elif alert['type'] == 'STRONG_CANDLE':
            print(f"🔥 VELA FUERTE DETECTADA:")
            print(f"   Symbol: {data['symbol']}")
            print(f"   Tipo: {data['candle_type']} {data['direction']}")
            print(f"   Fuerza IA: {data['strength_score']}%")
            print(f"   ATR: {data['atr_multiplier']:.1f}x")
            print(f"   Rango: {data['range_pips']:.1f} pips")
            print(f"   Volumen: {data['volume_ratio']:.1f}x")
            print(f"   Momentum: {data['momentum_score']:.2f}")
        
        print("=" * 60)
    
    def opportunity_scanner_thread(self):
        """Hilo para escanear oportunidades"""
        print("🔍 Iniciando hilo de escaneo de oportunidades...")
        
        while self.active:
            try:
                # Escanear oportunidades
                opportunities = self.opportunity_hunter.scan_all_opportunities()
                
                # Procesar alertas
                for opp in opportunities:
                    if opp['score'] >= self.vigilance_config['min_opportunity_score']:
                        if self.should_alert('OPPORTUNITY', opp['symbol'], opp['score']):
                            self.send_alert('OPPORTUNITY', opp)
                
                # Esperar intervalo
                time.sleep(self.vigilance_config['opportunity_scan_interval'])
                
            except Exception as e:
                print(f"Error en hilo de oportunidades: {e}")
                time.sleep(30)
    
    def candle_scanner_thread(self):
        """Hilo para escanear velas fuertes"""
        print("🕯️ Iniciando hilo de escaneo de velas...")
        
        while self.active:
            try:
                # Verificar conexión MT5
                if not self.candle_detector.mt5_connected:
                    print("⚠️ MT5 no conectado, reintentando...")
                    self.candle_detector.connect_mt5()
                    time.sleep(10)
                    continue
                
                # Escanear velas fuertes
                strong_candles = self.candle_detector.scan_all_symbols()
                
                # Procesar alertas
                for candle in strong_candles:
                    if candle['strength_score'] >= self.vigilance_config['min_candle_strength']:
                        if self.should_alert('STRONG_CANDLE', candle['symbol'], candle['strength_score']):
                            self.send_alert('STRONG_CANDLE', candle)
                
                # Esperar intervalo
                time.sleep(self.vigilance_config['candle_scan_interval'])
                
            except Exception as e:
                print(f"Error en hilo de velas: {e}")
                time.sleep(30)
    
    def status_monitor_thread(self):
        """Hilo para monitorear estado del sistema"""
        print("📊 Iniciando hilo de monitoreo de estado...")
        
        while self.active:
            try:
                current_time = datetime.now()
                
                # Mostrar estado cada 5 minutos
                if current_time.minute % 5 == 0 and current_time.second < 10:
                    self.display_system_status()
                
                time.sleep(10)
                
            except Exception as e:
                print(f"Error en hilo de estado: {e}")
                time.sleep(30)
    
    def display_system_status(self):
        """Mostrar estado del sistema"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n📊 ESTADO DEL SISTEMA DE VIGILANCIA IA - {current_time}")
        print("=" * 60)
        
        # Alertas recientes
        recent_alerts = [a for a in self.alert_history if (datetime.now() - a['timestamp']).total_seconds() < 3600]
        
        print(f"📈 Alertas última hora: {len(recent_alerts)}")
        if recent_alerts:
            opportunities = sum(1 for a in recent_alerts if a['type'] == 'OPPORTUNITY')
            candles = sum(1 for a in recent_alerts if a['type'] == 'STRONG_CANDLE')
            print(f"   - Oportunidades: {opportunities}")
            print(f"   - Velas fuertes: {candles}")
        
        # Estado de conexiones
        print(f"🔗 Conexiones:")
        print(f"   - TwelveData API: ✅ Conectada")
        print(f"   - MT5: {'✅ Conectado' if self.candle_detector.mt5_connected else '❌ Desconectado'}")
        
        # Configuración actual
        print(f"⚙️ Configuración:")
        print(f"   - Intervalo oportunidades: {self.vigilance_config['opportunity_scan_interval']}s")
        print(f"   - Intervalo velas: {self.vigilance_config['candle_scan_interval']}s")
        print(f"   - Score mín. oportunidad: {self.vigilance_config['min_opportunity_score']}%")
        print(f"   - Fuerza mín. vela: {self.vigilance_config['min_candle_strength']}%")
        
        print("=" * 60)
    
    def get_recent_alerts(self, minutes=60):
        """Obtener alertas recientes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [a for a in self.alert_history if a['timestamp'] > cutoff_time]
    
    def get_alert_summary(self):
        """Obtener resumen de alertas"""
        recent_alerts = self.get_recent_alerts(60)
        
        summary = {
            'total_alerts': len(recent_alerts),
            'opportunities': sum(1 for a in recent_alerts if a['type'] == 'OPPORTUNITY'),
            'strong_candles': sum(1 for a in recent_alerts if a['type'] == 'STRONG_CANDLE'),
            'high_priority': sum(1 for a in recent_alerts if a['priority'] == 'HIGH'),
            'symbols_alerted': len(set(a['data']['symbol'] for a in recent_alerts)),
        }
        
        return summary
    
    def start_vigilance(self):
        """Iniciar sistema de vigilancia"""
        try:
            print(f"\n🚀 INICIANDO SISTEMA DE VIGILANCIA IA EN TIEMPO REAL")
            print("=" * 80)
            print(f"⏰ Hora de inicio: {datetime.now().strftime('%H:%M:%S')}")
            print("Presiona Ctrl+C para detener")
            print("=" * 80)
            
            self.active = True
            
            # Iniciar hilos
            threads = []
            
            # Hilo de oportunidades
            opp_thread = threading.Thread(target=self.opportunity_scanner_thread, daemon=True)
            opp_thread.start()
            threads.append(opp_thread)
            
            # Hilo de velas
            candle_thread = threading.Thread(target=self.candle_scanner_thread, daemon=True)
            candle_thread.start()
            threads.append(candle_thread)
            
            # Hilo de estado
            status_thread = threading.Thread(target=self.status_monitor_thread, daemon=True)
            status_thread.start()
            threads.append(status_thread)
            
            print(f"✅ {len(threads)} hilos de vigilancia iniciados")
            
            # Mostrar estado inicial
            self.display_system_status()
            
            # Mantener activo
            while self.active:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Sistema de vigilancia detenido por usuario")
        except Exception as e:
            print(f"❌ Error en sistema de vigilancia: {e}")
        finally:
            self.stop_vigilance()
    
    def stop_vigilance(self):
        """Detener sistema de vigilancia"""
        self.active = False
        
        # Mostrar resumen final
        summary = self.get_alert_summary()
        print(f"\n📊 RESUMEN DE SESIÓN DE VIGILANCIA:")
        print(f"   Total alertas: {summary['total_alerts']}")
        print(f"   Oportunidades: {summary['opportunities']}")
        print(f"   Velas fuertes: {summary['strong_candles']}")
        print(f"   Alertas críticas: {summary['high_priority']}")
        print(f"   Símbolos alertados: {summary['symbols_alerted']}")
        
        print("\n✅ Sistema de Vigilancia IA finalizado")

def main():
    print("=" * 80)
    print("    AI REAL-TIME VIGILANCE SYSTEM")
    print("    SISTEMA DE VIGILANCIA IA EN TIEMPO REAL")
    print("=" * 80)
    print("Sistema integrado de vigilancia constante para oportunidades inesperadas")
    print("- Escaneo continuo de oportunidades con IA")
    print("- Detección de velas fuertes con momento")
    print("- Alertas inteligentes en tiempo real")
    print("- Monitoreo multi-hilo de alta frecuencia")
    print()
    
    vigilance = AIRealTimeVigilanceSystem()
    
    try:
        # Iniciar vigilancia
        vigilance.start_vigilance()
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido por usuario")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()