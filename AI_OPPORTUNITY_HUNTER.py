#!/usr/bin/env python
"""
AI OPPORTUNITY HUNTER - CAZADOR DE OPORTUNIDADES CON IA
=====================================================
Sistema inteligente que busca oportunidades de trading en tiempo real
Integra todos nuestros sistemas existentes para encontrar las mejores oportunidades
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from src.data.twelvedata_client import TwelveDataClient

class AIOpportunityHunter:
    """Cazador inteligente de oportunidades de trading"""
    
    def __init__(self):
        self.data_client = TwelveDataClient()
        
        # Símbolos a monitorear (expandidos)
        self.symbols = [
            'BTC/USD',   # Bitcoin principal
            'ETH/USD',   # Ethereum
            'EUR/USD',   # Euro
            'GBP/USD',   # Libra
            'USD/JPY',   # Yen
            'XAU/USD',   # Oro
            'XAG/USD',   # Plata
            'AUD/USD',   # Dólar australiano
        ]
        
        # Configuración IA para oportunidades
        self.opportunity_config = {
            'min_confidence': 70,           # Confianza mínima para oportunidad
            'max_risk_level': 5,            # Nivel máximo de riesgo (1-10)
            'volatility_sweet_spot': 0.02,  # Volatilidad ideal (2%)
            'volume_multiplier': 1.5,       # Multiplicador de volumen para oportunidad
            'trend_strength_min': 0.6,      # Fortaleza mínima de tendencia
            'rsi_overbought': 75,           # RSI sobrecomprado
            'rsi_oversold': 25,             # RSI sobrevendido
        }
        
        # Cache de oportunidades
        self.opportunities = []
        self.last_scan = None
        
        print("AI Opportunity Hunter inicializado")
        print(f"- Monitoreando {len(self.symbols)} símbolos")
        print("- Búsqueda de oportunidades con IA avanzada")
        print("- Integración con TwelveData en tiempo real")
    
    def scan_symbol_opportunity(self, symbol):
        """Escanear un símbolo específico buscando oportunidades"""
        try:
            # Obtener datos de mercado
            data = self.data_client.get_time_series(symbol, '1min', 50)
            if data is None:
                return None
            
            # Verificar si los datos están disponibles
            if isinstance(data, dict) and 'values' not in data:
                return None
            elif hasattr(data, 'empty') and data.empty:
                return None
            
            # Extraer candles dependiendo del tipo de datos
            if isinstance(data, dict) and 'values' in data:
                candles = data['values'][:10]  # Últimos 10 candles
            elif hasattr(data, 'to_dict'):
                # Si es DataFrame, convertir a dict
                data_dict = data.to_dict('records')
                candles = data_dict[:10]
            else:
                print(f"Estructura de datos no reconocida para {symbol}")
                return None
                
            if len(candles) < 10:
                return None
            
            # Obtener precios actuales
            current = candles[0]
            prev = candles[1]
            
            current_price = float(current['close'])
            prev_price = float(prev['close'])
            
            # 1. Calcular momentum
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            # 2. Calcular volatilidad simple
            prices = [float(c['close']) for c in candles]
            volatility = (max(prices) - min(prices)) / current_price
            
            # 3. Calcular RSI simple (aproximado)
            price_changes = []
            for i in range(1, min(len(candles), 15)):
                change = float(candles[i-1]['close']) - float(candles[i]['close'])
                price_changes.append(change)
            
            if price_changes:
                gains = [c for c in price_changes if c > 0]
                losses = [abs(c) for c in price_changes if c < 0]
                
                avg_gain = sum(gains) / len(gains) if gains else 0.001
                avg_loss = sum(losses) / len(losses) if losses else 0.001
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50
            
            # 4. Detectar tendencia (MA simple)
            ma5 = sum(prices[:5]) / 5
            ma10 = sum(prices[:10]) / 10
            
            trend_direction = 'ALCISTA' if ma5 > ma10 else 'BAJISTA'
            trend_strength = abs(ma5 - ma10) / current_price
            
            # 5. Análisis de volumen (proxy usando range)
            volume_proxy = sum([float(c['high']) - float(c['low']) for c in candles[:5]]) / 5
            avg_volume = sum([float(c['high']) - float(c['low']) for c in candles]) / len(candles)
            volume_ratio = volume_proxy / avg_volume if avg_volume > 0 else 1.0
            
            # 6. SCORING IA PARA OPORTUNIDAD
            opportunity_score = 0
            signals = []
            
            # Score por momentum
            if abs(price_change) > 0.5:  # Movimiento significativo
                opportunity_score += 20
                signals.append(f"MOMENTUM_{trend_direction}({price_change:+.2f}%)")
            
            # Score por RSI (sobrevendido/sobrecomprado)
            if rsi < self.opportunity_config['rsi_oversold']:
                opportunity_score += 25
                signals.append(f"RSI_OVERSOLD({rsi:.1f})")
            elif rsi > self.opportunity_config['rsi_overbought']:
                opportunity_score += 25
                signals.append(f"RSI_OVERBOUGHT({rsi:.1f})")
            
            # Score por volatilidad en sweet spot
            if 0.01 < volatility < 0.05:  # Volatilidad ideal
                opportunity_score += 15
                signals.append(f"VOLATILIDAD_IDEAL({volatility*100:.1f}%)")
            
            # Score por tendencia fuerte
            if trend_strength > 0.005:  # Tendencia definida
                opportunity_score += 15
                signals.append(f"TENDENCIA_FUERTE_{trend_direction}")
            
            # Score por volumen alto
            if volume_ratio > self.opportunity_config['volume_multiplier']:
                opportunity_score += 15
                signals.append(f"VOLUMEN_ALTO({volume_ratio:.1f}x)")
            
            # Determinar tipo de oportunidad
            opportunity_type = "SCALPING"
            if volatility > 0.03:
                opportunity_type = "SWING"
            elif abs(price_change) > 2:
                opportunity_type = "BREAKOUT"
            elif rsi < 30 or rsi > 70:
                opportunity_type = "REVERSAL"
            
            # Calcular nivel de riesgo (1-10)
            risk_level = min(10, max(1, int(volatility * 100)))
            
            # Solo considerar como oportunidad si score > umbral
            if opportunity_score >= self.opportunity_config['min_confidence']:
                return {
                    'symbol': symbol,
                    'score': opportunity_score,
                    'type': opportunity_type,
                    'direction': trend_direction,
                    'current_price': current_price,
                    'price_change': price_change,
                    'volatility': volatility * 100,
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'risk_level': risk_level,
                    'signals': signals,
                    'timestamp': datetime.now(),
                    'recommendation': self._generate_recommendation(opportunity_score, risk_level, opportunity_type)
                }
            
            return None
            
        except Exception as e:
            print(f"Error escaneando {symbol}: {e}")
            return None
    
    def _generate_recommendation(self, score, risk_level, opp_type):
        """Generar recomendación inteligente"""
        if score >= 85 and risk_level <= 3:
            return "EXCELENTE - EJECUTAR INMEDIATAMENTE"
        elif score >= 75 and risk_level <= 5:
            return f"BUENA - CONSIDERAR {opp_type.upper()}"
        elif score >= 65:
            return f"MODERADA - MONITOREAR DE CERCA"
        else:
            return "DÉBIL - ESPERAR MEJOR MOMENTO"
    
    def scan_all_opportunities(self):
        """Escanear todos los símbolos buscando oportunidades"""
        print(f"\n🔍 ESCANEANDO {len(self.symbols)} SÍMBOLOS...")
        print("=" * 60)
        
        found_opportunities = []
        
        for symbol in self.symbols:
            print(f"📊 Escaneando {symbol}...", end=" ")
            
            opportunity = self.scan_symbol_opportunity(symbol)
            
            if opportunity:
                found_opportunities.append(opportunity)
                print(f"✅ OPORTUNIDAD ({opportunity['score']}%)")
            else:
                print("❌ Sin oportunidades")
            
            time.sleep(0.5)  # Evitar sobrecargar API
        
        # Ordenar por score descendente
        found_opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        self.opportunities = found_opportunities
        self.last_scan = datetime.now()
        
        return found_opportunities
    
    def display_opportunities(self, opportunities=None):
        """Mostrar oportunidades encontradas"""
        if opportunities is None:
            opportunities = self.opportunities
        
        if not opportunities:
            print("\n❌ NO SE ENCONTRARON OPORTUNIDADES")
            return
        
        print(f"\n🎯 OPORTUNIDADES ENCONTRADAS: {len(opportunities)}")
        print("=" * 80)
        
        for i, opp in enumerate(opportunities, 1):
            risk_icon = "🟢" if opp['risk_level'] <= 3 else "🟡" if opp['risk_level'] <= 6 else "🔴"
            direction_icon = "📈" if opp['direction'] == 'ALCISTA' else "📉"
            
            print(f"\n{i}. {direction_icon} {opp['symbol']} - {opp['type']}")
            print(f"   💎 Score IA: {opp['score']}% | {risk_icon} Riesgo: {opp['risk_level']}/10")
            print(f"   💰 Precio: ${opp['current_price']:.4f} ({opp['price_change']:+.2f}%)")
            print(f"   📊 RSI: {opp['rsi']:.1f} | Volatilidad: {opp['volatility']:.1f}%")
            print(f"   🔊 Volumen: {opp['volume_ratio']:.1f}x normal")
            print(f"   🎯 Recomendación: {opp['recommendation']}")
            
            if opp['signals']:
                print(f"   🚨 Señales: {' | '.join(opp['signals'][:3])}")  # Mostrar max 3 señales
        
        print("\n" + "=" * 80)
    
    def get_best_opportunity(self):
        """Obtener la mejor oportunidad disponible"""
        if not self.opportunities:
            return None
        
        # Filtrar por criterios estrictos
        best_opportunities = [
            opp for opp in self.opportunities 
            if opp['score'] >= 75 and opp['risk_level'] <= 5
        ]
        
        return best_opportunities[0] if best_opportunities else None
    
    def run_opportunity_hunt(self):
        """Ejecutar caza de oportunidades completa"""
        try:
            cycle_start = datetime.now()
            print(f"\n🚀 INICIANDO CAZA DE OPORTUNIDADES")
            print(f"⏰ Hora: {cycle_start.strftime('%H:%M:%S')}")
            
            # Escanear todas las oportunidades
            opportunities = self.scan_all_opportunities()
            
            # Mostrar resultados
            self.display_opportunities(opportunities)
            
            # Identificar la mejor oportunidad
            best_opp = self.get_best_opportunity()
            
            if best_opp:
                print(f"\n⭐ MEJOR OPORTUNIDAD:")
                print(f"   🎯 {best_opp['symbol']} - Score: {best_opp['score']}%")
                print(f"   📊 {best_opp['type']} {best_opp['direction']}")
                print(f"   💡 {best_opp['recommendation']}")
            else:
                print(f"\n⚠️  No hay oportunidades que cumplan criterios estrictos")
            
            # Estadísticas del escaneo
            scan_time = (datetime.now() - cycle_start).total_seconds()
            print(f"\n📈 ESTADÍSTICAS DEL ESCANEO:")
            print(f"   Símbolos escaneados: {len(self.symbols)}")
            print(f"   Oportunidades encontradas: {len(opportunities)}")
            print(f"   Tiempo de escaneo: {scan_time:.1f}s")
            print(f"   Ratio éxito: {len(opportunities)/len(self.symbols)*100:.1f}%")
            
            return opportunities
            
        except Exception as e:
            print(f"Error en caza de oportunidades: {e}")
            return []

def main():
    print("=" * 80)
    print("    AI OPPORTUNITY HUNTER - CAZADOR DE OPORTUNIDADES")
    print("=" * 80)
    print("Sistema inteligente de búsqueda de oportunidades de trading")
    print("- Escaneo multi-símbolo en tiempo real")
    print("- Análisis IA para scoring de oportunidades")
    print("- Clasificación automática por tipo y riesgo")
    print("- Recomendaciones inteligentes")
    print()
    
    hunter = AIOpportunityHunter()
    
    try:
        cycle = 0
        
        while True:
            cycle += 1
            
            print(f"\n{'='*20} CICLO #{cycle:03d} {'='*20}")
            
            # Ejecutar caza de oportunidades
            opportunities = hunter.run_opportunity_hunt()
            
            if opportunities:
                best_score = max(opp['score'] for opp in opportunities)
                print(f"\n🏆 Mejor score encontrado: {best_score}%")
            
            print(f"\n⏰ Próximo escaneo en 3 minutos...")
            print("Presiona Ctrl+C para detener")
            
            time.sleep(180)  # 3 minutos entre escaneos
            
    except KeyboardInterrupt:
        print("\n\n🛑 AI Opportunity Hunter detenido por usuario")
    except Exception as e:
        print(f"❌ Error en sistema: {e}")
    finally:
        print("AI Opportunity Hunter finalizado")

if __name__ == "__main__":
    main()