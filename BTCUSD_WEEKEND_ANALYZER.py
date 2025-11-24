#!/usr/bin/env python
"""
BTCUSD WEEKEND ANALYZER - ANÁLISIS MULTITEMPORAL PARA FIN DE SEMANA
===================================================================
Analiza BTCUSD en múltiples temporalidades para encontrar oportunidades de trading
"""

import os
import sys
import time
import requests
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class BTCUSDWeekendAnalyzer:
    """Analizador de BTCUSD para trading de fin de semana"""
    
    def __init__(self):
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'
        self.base_url = 'https://api.twelvedata.com'
        self.symbol = 'BTC/USD'
        
        # Temporalidades de análisis
        self.timeframes = ['1min', '5min', '15min', '30min']
        
        print("BTCUSD Weekend Analyzer inicializado")
        print("Analizando temporalidades:", ', '.join(self.timeframes))
    
    def get_market_data(self, interval, outputsize=20):
        """Obtener datos de mercado para BTCUSD"""
        try:
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': self.symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    return data['values']
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo datos {interval}: {e}")
            return None
    
    def calculate_momentum(self, price_data):
        """Calcular momentum y volatilidad"""
        if not price_data or len(price_data) < 10:
            return None
        
        try:
            # Precios de cierre
            closes = [float(bar['close']) for bar in price_data[:10]]
            
            # Precio actual vs hace N períodos
            current_price = closes[0]
            price_5_ago = closes[4] if len(closes) > 4 else closes[-1]
            price_10_ago = closes[9] if len(closes) > 9 else closes[-1]
            
            # Momentum
            momentum_5 = ((current_price - price_5_ago) / price_5_ago) * 100
            momentum_10 = ((current_price - price_10_ago) / price_10_ago) * 100
            
            # Volatilidad (rango promedio)
            high_low_ranges = []
            for bar in price_data[:5]:
                high = float(bar['high'])
                low = float(bar['low'])
                range_pct = ((high - low) / low) * 100
                high_low_ranges.append(range_pct)
            
            avg_volatility = sum(high_low_ranges) / len(high_low_ranges)
            
            # Volumen (estimado por rango de precios)
            recent_volume = 0
            for bar in price_data[:3]:
                high = float(bar['high'])
                low = float(bar['low'])
                volume_proxy = (high - low) * float(bar['close'])
                recent_volume += volume_proxy
            
            return {
                'current_price': current_price,
                'momentum_5': momentum_5,
                'momentum_10': momentum_10,
                'volatility': avg_volatility,
                'volume_proxy': recent_volume / 3,
                'price_direction': 'UP' if momentum_5 > 0 else 'DOWN'
            }
            
        except Exception as e:
            print(f"Error calculando momentum: {e}")
            return None
    
    def get_technical_indicator(self, indicator, interval, params=None):
        """Obtener indicador técnico específico"""
        try:
            url = f"{self.base_url}/{indicator}"
            request_params = {
                'symbol': self.symbol,
                'interval': interval,
                'outputsize': 5,
                'apikey': self.api_key
            }
            
            if params:
                request_params.update(params)
            
            response = requests.get(url, params=request_params, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and data['values']:
                    return data['values'][0]  # Valor más reciente
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo {indicator}: {e}")
            return None
    
    def analyze_timeframe(self, interval):
        """Analizar una temporalidad específica"""
        print(f"\n--- ANÁLISIS {interval.upper()} ---")
        
        # Obtener datos de precios
        price_data = self.get_market_data(interval, 20)
        if not price_data:
            print(f"❌ Sin datos para {interval}")
            return None
        
        # Calcular momentum y volatilidad
        momentum_data = self.calculate_momentum(price_data)
        if not momentum_data:
            print(f"❌ Error calculando momentum {interval}")
            return None
        
        # Obtener RSI
        rsi_data = self.get_technical_indicator('rsi', interval, {'time_period': 14})
        rsi_value = float(rsi_data['rsi']) if rsi_data else None
        
        # Obtener MACD
        macd_data = self.get_technical_indicator('macd', interval)
        macd_value = float(macd_data['macd']) if macd_data else None
        macd_signal = float(macd_data['macd_signal']) if macd_data else None
        
        time.sleep(0.3)  # Rate limit
        
        # Análisis de señales
        signals = []
        score = 0
        
        # 1. Análisis de momentum
        if momentum_data['momentum_5'] > 2:
            signals.append("🟢 MOMENTUM ALCISTA FUERTE")
            score += 20
        elif momentum_data['momentum_5'] > 0.5:
            signals.append("🟢 Momentum alcista")
            score += 10
        elif momentum_data['momentum_5'] < -2:
            signals.append("🔴 MOMENTUM BAJISTA FUERTE")
            score -= 20
        elif momentum_data['momentum_5'] < -0.5:
            signals.append("🔴 Momentum bajista")
            score -= 10
        
        # 2. Análisis RSI
        if rsi_value:
            if rsi_value < 30:
                signals.append(f"🟢 RSI SOBREVENTA ({rsi_value:.1f})")
                score += 15
            elif rsi_value > 70:
                signals.append(f"🔴 RSI SOBRECOMPRA ({rsi_value:.1f})")
                score -= 15
            elif 40 <= rsi_value <= 60:
                signals.append(f"🟡 RSI neutro ({rsi_value:.1f})")
                score += 5
        
        # 3. Análisis MACD
        if macd_value and macd_signal:
            if macd_value > macd_signal and macd_value > 0:
                signals.append("🟢 MACD alcista")
                score += 10
            elif macd_value < macd_signal and macd_value < 0:
                signals.append("🔴 MACD bajista")
                score -= 10
        
        # 4. Análisis de volatilidad
        if momentum_data['volatility'] > 3:
            signals.append(f"⚡ ALTA VOLATILIDAD ({momentum_data['volatility']:.1f}%)")
            score += 5
        elif momentum_data['volatility'] < 1:
            signals.append(f"😴 Baja volatilidad ({momentum_data['volatility']:.1f}%)")
            score -= 5
        
        # Mostrar resultados
        print(f"💰 Precio actual: ${momentum_data['current_price']:,.2f}")
        print(f"📈 Momentum 5p: {momentum_data['momentum_5']:+.2f}%")
        print(f"📊 Momentum 10p: {momentum_data['momentum_10']:+.2f}%")
        print(f"⚡ Volatilidad: {momentum_data['volatility']:.2f}%")
        if rsi_value:
            print(f"📉 RSI(14): {rsi_value:.1f}")
        
        print("\n🎯 SEÑALES DETECTADAS:")
        for signal in signals:
            print(f"   {signal}")
        
        # Determinar recomendación
        if score >= 25:
            recommendation = "🟢 COMPRA FUERTE"
        elif score >= 15:
            recommendation = "🟢 Compra"
        elif score <= -25:
            recommendation = "🔴 VENTA FUERTE"
        elif score <= -15:
            recommendation = "🔴 Venta"
        else:
            recommendation = "🟡 Neutral/Esperar"
        
        print(f"\n✅ RECOMENDACIÓN {interval}: {recommendation} (Score: {score})")
        
        return {
            'interval': interval,
            'price': momentum_data['current_price'],
            'momentum_5': momentum_data['momentum_5'],
            'momentum_10': momentum_data['momentum_10'],
            'volatility': momentum_data['volatility'],
            'rsi': rsi_value,
            'score': score,
            'recommendation': recommendation,
            'signals': signals
        }
    
    def run_multi_timeframe_analysis(self):
        """Ejecutar análisis completo multitemporal"""
        print("=" * 70)
        print("     BTCUSD WEEKEND TRADING ANALYSIS")
        print("=" * 70)
        print(f"🕐 Análisis ejecutado: {datetime.now().strftime('%H:%M:%S')}")
        print(f"🪙 Símbolo: {self.symbol}")
        print(f"⏰ Temporalidades: {', '.join(self.timeframes)}")
        
        results = []
        
        # Analizar cada temporalidad
        for interval in self.timeframes:
            result = self.analyze_timeframe(interval)
            if result:
                results.append(result)
            time.sleep(1)  # Pausa entre análisis
        
        # Resumen consolidado
        if results:
            print("\n" + "=" * 50)
            print("📊 RESUMEN MULTITEMPORAL")
            print("=" * 50)
            
            total_score = sum(r['score'] for r in results)
            avg_momentum = sum(r['momentum_5'] for r in results) / len(results)
            max_volatility = max(r['volatility'] for r in results)
            
            print(f"📈 Score consolidado: {total_score}")
            print(f"🚀 Momentum promedio: {avg_momentum:+.2f}%")
            print(f"⚡ Volatilidad máxima: {max_volatility:.2f}%")
            
            # Recomendación final
            if total_score >= 40:
                final_rec = "🟢 OPORTUNIDAD DE COMPRA IDENTIFICADA"
            elif total_score <= -40:
                final_rec = "🔴 OPORTUNIDAD DE VENTA IDENTIFICADA"
            elif abs(avg_momentum) > 1.5:
                direction = "COMPRA" if avg_momentum > 0 else "VENTA"
                final_rec = f"🟡 MOMENTUM DETECTADO - CONSIDERAR {direction}"
            else:
                final_rec = "⚪ SIN OPORTUNIDADES CLARAS - ESPERAR"
            
            print(f"\n🎯 RECOMENDACIÓN FINAL: {final_rec}")
            
            # Mejores setups por temporalidad
            print("\n📋 RANKING POR TEMPORALIDAD:")
            sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
            for i, r in enumerate(sorted_results, 1):
                print(f"  {i}. {r['interval']} - {r['recommendation']} (Score: {r['score']})")
        
        print("\n" + "=" * 70)
        return results

def main():
    """Función principal"""
    analyzer = BTCUSDWeekendAnalyzer()
    
    try:
        while True:
            results = analyzer.run_multi_timeframe_analysis()
            
            print(f"\n⏰ Próximo análisis en 5 minutos...")
            print("Presiona Ctrl+C para detener")
            time.sleep(300)  # 5 minutos
            
    except KeyboardInterrupt:
        print("\n\n🛑 Análisis BTCUSD detenido por usuario")
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
    finally:
        print("BTCUSD Weekend Analyzer finalizado")

if __name__ == "__main__":
    main()