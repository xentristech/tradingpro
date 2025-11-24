#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 SISTEMA DE ANÁLISIS DE MERCADO CON IA PERSONALIZADO
Análisis completo del mercado con saludo personal para el operador
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import json
import time

# Configurar paths
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

class MarketAnalyzerAI:
    """Analizador de mercado con IA personalizado"""
    
    def __init__(self, operator_name="OPERADOR"):
        self.operator_name = operator_name
        self.symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD', 'GBPUSD']
        self.analysis_results = {}
        
    def personal_greeting(self):
        """Saludo personalizado basado en la hora"""
        hour = datetime.now().hour
        
        greetings = {
            (5, 12): "Buenos días",
            (12, 18): "Buenas tardes", 
            (18, 24): "Buenas noches",
            (0, 5): "Buenas madrugadas"
        }
        
        greeting = "Hola"
        for time_range, greet in greetings.items():
            if time_range[0] <= hour < time_range[1]:
                greeting = greet
                break
        
        print("="*60)
        print(f"   🎯 {greeting} {self.operator_name}!")
        print("="*60)
        print(f"   Fecha: {datetime.now().strftime('%A %d de %B del %Y')}")
        print(f"   Hora: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        print()
        
        # Mensaje motivacional
        messages = [
            "💪 ¡Hoy es un gran día para operar!",
            "🚀 ¡Vamos por esas ganancias!",
            "📈 ¡El mercado está esperando tus decisiones!",
            "⚡ ¡Momento de brillar en el trading!",
            "🎯 ¡Enfocados en los objetivos del día!"
        ]
        
        import random
        print(f"   {random.choice(messages)}")
        print()
        
    def check_mt5_connection(self):
        """Verificar conexión con MT5"""
        print("🔌 VERIFICANDO CONEXIÓN MT5...")
        print("-"*40)
        
        if not mt5.initialize():
            print("❌ MT5 no está conectado")
            return False
            
        account = mt5.account_info()
        if account:
            print(f"✅ Conectado a cuenta: {account.login}")
            print(f"   Balance: ${account.balance:.2f}")
            print(f"   Equity: ${account.equity:.2f}")
            print(f"   Profit actual: ${account.profit:.2f}")
            
            # Verificar posiciones
            positions = mt5.positions_get()
            if positions:
                print(f"   📊 Posiciones abiertas: {len(positions)}")
                total_profit = sum(p.profit for p in positions)
                print(f"   💰 P&L total: ${total_profit:.2f}")
            else:
                print(f"   📊 No hay posiciones abiertas")
                
            return True
        else:
            print("⚠️ MT5 conectado pero sin cuenta activa")
            return False
    
    def analyze_market_conditions(self):
        """Análisis de condiciones actuales del mercado"""
        print("\n📊 ANÁLISIS DE MERCADO EN TIEMPO REAL")
        print("="*60)
        
        market_status = {
            'trending': [],
            'ranging': [],
            'volatile': [],
            'calm': []
        }
        
        for symbol in self.symbols:
            print(f"\n🔍 Analizando {symbol}...")
            
            # Obtener datos del símbolo
            if not mt5.symbol_select(symbol, True):
                print(f"   ⚠️ {symbol} no disponible")
                continue
                
            # Obtener tick actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print(f"   ⚠️ Sin datos para {symbol}")
                continue
                
            # Obtener barras históricas
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
            if rates is None or len(rates) < 20:
                print(f"   ⚠️ Datos históricos insuficientes")
                continue
                
            # Calcular indicadores básicos
            closes = [r['close'] for r in rates]
            highs = [r['high'] for r in rates]
            lows = [r['low'] for r in rates]
            
            # Precio actual
            current_price = tick.bid
            print(f"   💵 Precio: {current_price:.5f}")
            
            # Calcular tendencia (SMA)
            sma20 = sum(closes[-20:]) / 20
            sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma20
            
            if current_price > sma20 > sma50:
                trend = "ALCISTA 📈"
                market_status['trending'].append(symbol)
            elif current_price < sma20 < sma50:
                trend = "BAJISTA 📉"
                market_status['trending'].append(symbol)
            else:
                trend = "LATERAL ➡️"
                market_status['ranging'].append(symbol)
                
            print(f"   📊 Tendencia: {trend}")
            
            # Calcular volatilidad (ATR simplificado)
            ranges = []
            for i in range(1, min(14, len(rates))):
                high_low = rates[i]['high'] - rates[i]['low']
                high_close = abs(rates[i]['high'] - rates[i-1]['close'])
                low_close = abs(rates[i]['low'] - rates[i-1]['close'])
                ranges.append(max(high_low, high_close, low_close))
                
            atr = sum(ranges) / len(ranges) if ranges else 0
            volatility_pct = (atr / current_price) * 100 if current_price > 0 else 0
            
            if volatility_pct > 1.0:
                volatility = "ALTA ⚡"
                market_status['volatile'].append(symbol)
            elif volatility_pct > 0.5:
                volatility = "MEDIA 🔄"
            else:
                volatility = "BAJA 😴"
                market_status['calm'].append(symbol)
                
            print(f"   🌊 Volatilidad: {volatility} ({volatility_pct:.2f}%)")
            
            # Calcular momentum (cambio % últimas 20 barras)
            if len(closes) >= 20:
                momentum = ((closes[-1] - closes[-20]) / closes[-20]) * 100
                momentum_str = f"{momentum:+.2f}%"
                
                if abs(momentum) > 2:
                    print(f"   ⚡ Momentum: FUERTE {momentum_str}")
                elif abs(momentum) > 0.5:
                    print(f"   🔄 Momentum: MODERADO {momentum_str}")
                else:
                    print(f"   😴 Momentum: DÉBIL {momentum_str}")
            
            # Guardar análisis
            self.analysis_results[symbol] = {
                'price': current_price,
                'trend': trend,
                'volatility': volatility_pct,
                'momentum': momentum if 'momentum' in locals() else 0
            }
            
        return market_status
    
    def generate_ai_recommendations(self, market_status):
        """Generar recomendaciones basadas en IA"""
        print("\n🤖 RECOMENDACIONES DE LA IA")
        print("="*60)
        
        # Análisis general del mercado
        total_symbols = len(self.symbols)
        trending = len(market_status['trending'])
        volatile = len(market_status['volatile'])
        
        print("\n📊 RESUMEN DEL MERCADO:")
        print(f"   • Mercados en tendencia: {trending}/{total_symbols}")
        print(f"   • Mercados volátiles: {volatile}/{total_symbols}")
        print(f"   • Mercados laterales: {len(market_status['ranging'])}/{total_symbols}")
        print(f"   • Mercados calmados: {len(market_status['calm'])}/{total_symbols}")
        
        # Recomendaciones basadas en condiciones
        print("\n💡 RECOMENDACIONES:")
        
        if trending > total_symbols / 2:
            print("   ✅ CONDICIONES FAVORABLES para trading de tendencia")
            print("   📈 Estrategia sugerida: Seguimiento de tendencia")
            print("   🎯 Buscar pullbacks en mercados alcistas")
            if market_status['trending']:
                print(f"   ⭐ Mejores oportunidades: {', '.join(market_status['trending'])}")
        elif volatile:
            print("   ⚡ ALTA VOLATILIDAD detectada")
            print("   🛡️ Estrategia sugerida: Reducir tamaño de posiciones")
            print("   ⚠️ Usar stops más amplios")
            print(f"   🔥 Símbolos volátiles: {', '.join(market_status['volatile'])}")
        else:
            print("   ➡️ MERCADO LATERAL predominante")
            print("   📊 Estrategia sugerida: Trading de rangos")
            print("   🎯 Buscar soportes y resistencias")
        
        # Análisis por símbolo
        print("\n🎯 ANÁLISIS ESPECÍFICO:")
        
        for symbol, data in self.analysis_results.items():
            print(f"\n   {symbol}:")
            
            # Determinar acción basada en condiciones
            action = "ESPERAR"
            confidence = 50
            
            if data['trend'] == "ALCISTA 📈" and data['momentum'] > 1:
                action = "COMPRA"
                confidence = min(70 + data['momentum'] * 5, 95)
            elif data['trend'] == "BAJISTA 📉" and data['momentum'] < -1:
                action = "VENTA"
                confidence = min(70 + abs(data['momentum']) * 5, 95)
            elif data['volatility'] < 0.3:
                action = "NO OPERAR"
                confidence = 30
                
            # Mostrar recomendación
            if action == "COMPRA":
                print(f"      🟢 SEÑAL DE {action} (Confianza: {confidence:.0f}%)")
            elif action == "VENTA":
                print(f"      🔴 SEÑAL DE {action} (Confianza: {confidence:.0f}%)")
            elif action == "NO OPERAR":
                print(f"      ⏸️ {action} - Volatilidad muy baja")
            else:
                print(f"      ⏳ {action} - Condiciones no óptimas")
                
            # Niveles clave
            if data['price'] > 0:
                sl_distance = data['price'] * 0.01  # 1% stop loss
                tp_distance = data['price'] * 0.02  # 2% take profit
                
                if action in ["COMPRA", "VENTA"]:
                    if action == "COMPRA":
                        sl = data['price'] - sl_distance
                        tp = data['price'] + tp_distance
                    else:
                        sl = data['price'] + sl_distance
                        tp = data['price'] - tp_distance
                        
                    print(f"      📍 Entry: {data['price']:.5f}")
                    print(f"      🛑 Stop Loss: {sl:.5f}")
                    print(f"      🎯 Take Profit: {tp:.5f}")
    
    def market_schedule_alert(self):
        """Alertas sobre horarios de mercado"""
        print("\n⏰ HORARIOS DE MERCADO")
        print("="*60)
        
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        
        # Forex (Domingo 22:00 - Viernes 22:00 UTC)
        if weekday == 6:  # Domingo
            if hour >= 22:
                print("   ✅ FOREX: Mercado ABIERTO")
            else:
                print(f"   ⏳ FOREX: Abre en {22-hour} horas")
        elif weekday == 5:  # Viernes
            if hour < 22:
                print("   ✅ FOREX: Mercado ABIERTO")
            else:
                print("   🔴 FOREX: Mercado CERRADO")
        elif weekday < 5:  # Lunes a Jueves
            print("   ✅ FOREX: Mercado ABIERTO")
        else:  # Sábado
            print("   🔴 FOREX: Mercado CERRADO (fin de semana)")
            
        # Crypto
        print("   ✅ CRYPTO: Mercado ABIERTO 24/7")
        
        # Sesiones importantes
        print("\n   📍 SESIONES PRINCIPALES:")
        
        # Convertir a hora Colombia (UTC-5)
        colombia_hour = (hour - 5) % 24
        
        sessions = {
            "Sydney": (21, 6),
            "Tokyo": (0, 9),
            "Londres": (8, 17),
            "Nueva York": (13, 22)
        }
        
        for session, (start, end) in sessions.items():
            if start <= colombia_hour < end or (start > end and (colombia_hour >= start or colombia_hour < end)):
                print(f"      🟢 {session}: ACTIVA")
            else:
                print(f"      ⚫ {session}: Cerrada")
    
    def save_analysis_report(self):
        """Guardar reporte del análisis"""
        timestamp = datetime.now()
        report_dir = project_path / "logs" / "analysis_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report = {
            'timestamp': timestamp.isoformat(),
            'operator': self.operator_name,
            'analysis': self.analysis_results,
            'execution_time': datetime.now().isoformat()
        }
        
        # Guardar JSON
        report_file = report_dir / f"analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n📁 Reporte guardado: {report_file.name}")
        
    def run_complete_analysis(self):
        """Ejecutar análisis completo"""
        
        # Saludo personal
        self.personal_greeting()
        
        # Verificar MT5
        if not self.check_mt5_connection():
            print("\n❌ No se puede continuar sin conexión MT5")
            print("Por favor, abre MetaTrader 5 y vuelve a intentar")
            return False
            
        # Analizar mercado
        market_status = self.analyze_market_conditions()
        
        # Generar recomendaciones IA
        self.generate_ai_recommendations(market_status)
        
        # Alertas de horario
        self.market_schedule_alert()
        
        # Guardar reporte
        self.save_analysis_report()
        
        # Mensaje final
        print("\n" + "="*60)
        print("   ✅ ANÁLISIS COMPLETADO")
        print("="*60)
        print(f"\n   ¡Buena suerte en tus operaciones, {self.operator_name}!")
        print("   Recuerda: Opera con disciplina y gestiona tu riesgo 🛡️")
        print()
        
        return True

def main():
    """Función principal"""
    
    # Obtener nombre del operador
    operator_name = os.getenv("OPERATOR_NAME", "TRADER")
    
    # Crear analizador
    analyzer = MarketAnalyzerAI(operator_name)
    
    try:
        # Ejecutar análisis
        success = analyzer.run_complete_analysis()
        
        if success:
            print("\n🔄 El análisis se actualizará automáticamente cada 5 minutos")
            print("Presiona Ctrl+C para detener")
            
            # Loop continuo
            while True:
                time.sleep(300)  # Esperar 5 minutos
                print("\n" + "="*60)
                print("   🔄 ACTUALIZANDO ANÁLISIS...")
                print("="*60)
                analyzer.run_complete_analysis()
                
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego! Sistema detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Limpiar pantalla
    os.system('cls' if os.name == 'nt' else 'clear')
    main()
