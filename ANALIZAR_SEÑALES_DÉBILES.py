#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ANALIZADOR DE SEÑALES DÉBILES
=============================
Identifica por qué las señales no superan el 50% de confianza y sugiere ajustes
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import sys

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.ai.ollama_client import OllamaClient
    from src.data.twelvedata_client import TwelveDataClient
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)

class WeakSignalAnalyzer:
    """Analizador especializado en señales de baja confianza"""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.td_client = TwelveDataClient()
        self.analysis_dir = Path("logs/weak_signals_analysis")
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_current_market_conditions(self, symbols=['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']):
        """Analizar condiciones actuales del mercado para entender señales débiles"""
        
        print("🔍 ANALIZANDO CONDICIONES ACTUALES DEL MERCADO...")
        print("="*60)
        
        analysis_results = {}
        
        for symbol in symbols:
            print(f"\n📊 Analizando {symbol}...")
            
            try:
                # Obtener datos de diferentes timeframes
                symbol_clean = symbol.replace('m', '')  # XAUUSDm -> XAUUSD
                
                # Mapear símbolos para TwelveData
                if symbol_clean == 'XAUUSD':
                    td_symbol = 'XAU/USD'
                elif symbol_clean == 'BTCUSD':
                    td_symbol = 'BTC/USD'
                elif symbol_clean == 'EURUSD':
                    td_symbol = 'EUR/USD'
                elif symbol_clean == 'GBPUSD':
                    td_symbol = 'GBP/USD'
                else:
                    td_symbol = symbol_clean
                
                # Obtener datos de múltiples timeframes
                data_5m = self.td_client.get_time_series(td_symbol, interval='5min', outputsize=20)
                data_15m = self.td_client.get_time_series(td_symbol, interval='15min', outputsize=20)
                data_1h = self.td_client.get_time_series(td_symbol, interval='1h', outputsize=20)
                
                if not all([data_5m, data_15m, data_1h]):
                    print(f"❌ No se pudieron obtener datos para {symbol}")
                    continue
                
                # Obtener indicadores técnicos
                indicators_5m = self.td_client.get_technical_indicators(td_symbol, '5min')
                indicators_15m = self.td_client.get_technical_indicators(td_symbol, '15min')
                indicators_1h = self.td_client.get_technical_indicators(td_symbol, '1h')
                
                # Obtener precio actual
                if mt5.initialize():
                    tick = mt5.symbol_info_tick(symbol)
                    current_price = tick.bid if tick else 0
                    mt5.shutdown()
                else:
                    current_price = float(data_5m[0]['close']) if data_5m else 0
                
                # Análisis de volatilidad
                prices_5m = [float(d['close']) for d in data_5m[-10:]]
                volatility = self.calculate_volatility(prices_5m)
                
                # Análisis de tendencia
                trend_analysis = self.analyze_trend(data_5m, data_15m, data_1h)
                
                # Análisis de volumen (si está disponible)
                volume_analysis = self.analyze_volume(data_5m)
                
                # Consolidar análisis
                analysis_results[symbol] = {
                    'current_price': current_price,
                    'volatility': volatility,
                    'trend_analysis': trend_analysis,
                    'volume_analysis': volume_analysis,
                    'indicators_5m': indicators_5m,
                    'indicators_15m': indicators_15m,
                    'indicators_1h': indicators_1h,
                    'data_quality': {
                        '5m_candles': len(data_5m),
                        '15m_candles': len(data_15m),
                        '1h_candles': len(data_1h)
                    }
                }
                
                print(f"  ✅ Precio: ${current_price:.2f}")
                print(f"  📈 Volatilidad: {volatility:.2f}%")
                print(f"  🎯 Tendencia: {trend_analysis.get('overall_trend', 'NEUTRAL')}")
                
            except Exception as e:
                print(f"  ❌ Error analizando {symbol}: {e}")
                continue
        
        return analysis_results
    
    def calculate_volatility(self, prices):
        """Calcular volatilidad como desviación estándar"""
        if len(prices) < 2:
            return 0
        
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / mean_price * 100
        
        return volatility
    
    def analyze_trend(self, data_5m, data_15m, data_1h):
        """Análisis de tendencia en múltiples timeframes"""
        trends = {}
        
        for timeframe, data in [('5m', data_5m), ('15m', data_15m), ('1h', data_1h)]:
            if len(data) < 5:
                trends[timeframe] = 'INSUFFICIENT_DATA'
                continue
            
            # Comparar precios recientes vs anteriores
            recent_avg = sum(float(d['close']) for d in data[:3]) / 3
            older_avg = sum(float(d['close']) for d in data[-3:]) / 3
            
            if recent_avg > older_avg * 1.002:  # 0.2% mayor
                trends[timeframe] = 'UPTREND'
            elif recent_avg < older_avg * 0.998:  # 0.2% menor
                trends[timeframe] = 'DOWNTREND'
            else:
                trends[timeframe] = 'SIDEWAYS'
        
        # Determinar tendencia general
        trend_votes = list(trends.values())
        if trend_votes.count('UPTREND') >= 2:
            overall = 'UPTREND'
        elif trend_votes.count('DOWNTREND') >= 2:
            overall = 'DOWNTREND'
        else:
            overall = 'SIDEWAYS'
        
        return {
            'timeframe_trends': trends,
            'overall_trend': overall
        }
    
    def analyze_volume(self, data):
        """Análisis de volumen"""
        if not data or 'volume' not in data[0]:
            return {'status': 'NO_VOLUME_DATA'}
        
        try:
            volumes = [float(d['volume']) for d in data[-5:] if 'volume' in d]
            if not volumes:
                return {'status': 'NO_VOLUME_DATA'}
            
            avg_volume = sum(volumes) / len(volumes)
            latest_volume = volumes[-1]
            
            volume_trend = 'HIGH' if latest_volume > avg_volume * 1.2 else 'LOW' if latest_volume < avg_volume * 0.8 else 'NORMAL'
            
            return {
                'status': 'AVAILABLE',
                'avg_volume': avg_volume,
                'latest_volume': latest_volume,
                'volume_trend': volume_trend
            }
        except:
            return {'status': 'ERROR_PROCESSING_VOLUME'}
    
    def generate_weakness_diagnosis(self, market_analysis):
        """Generar diagnóstico de por qué las señales son débiles"""
        
        print("\n🤖 GENERANDO DIAGNÓSTICO CON IA...")
        
        # Preparar resumen para IA
        summary = "ANÁLISIS DE MERCADO ACTUAL:\n"
        summary += "="*40 + "\n"
        
        for symbol, analysis in market_analysis.items():
            summary += f"\n{symbol}:\n"
            summary += f"  Precio: ${analysis['current_price']:.2f}\n"
            summary += f"  Volatilidad: {analysis['volatility']:.2f}%\n"
            summary += f"  Tendencia: {analysis['trend_analysis']['overall_trend']}\n"
            
            # Indicadores técnicos
            if analysis['indicators_5m']:
                summary += "  Indicadores 5min: "
                for indicator, value in analysis['indicators_5m'].items():
                    if isinstance(value, (int, float)):
                        summary += f"{indicator}={value:.2f} "
                summary += "\n"
        
        ai_prompt = f"""
Como experto en trading algorítmico, analiza por qué nuestro sistema de señales está generando BAJA CONFIANZA (50% o menos).

DATOS ACTUALES DEL MERCADO:
{summary}

PROBLEMA IDENTIFICADO:
- Las señales generadas tienen confianza ≤50%
- El sistema recomienda NO_OPERAR constantemente
- Necesitamos identificar si es por:
  1. Condiciones de mercado (volatilidad, tendencia, volumen)
  2. Configuración de algoritmos (umbrales, indicadores)
  3. Calidad de datos o timeframes
  4. Parámetros de la IA (modelo, prompts, criterios)

PROPORCIONA:

1. DIAGNÓSTICO PRINCIPAL: ¿Cuál es la causa raíz de las señales débiles?

2. ANÁLISIS DE MERCADO: ¿Las condiciones actuales justifican la baja confianza?

3. AJUSTES RECOMENDADOS:
   - Parámetros de indicadores técnicos
   - Umbrales de confianza
   - Timeframes a usar
   - Criterios de la IA

4. CONFIGURACIÓN SUGERIDA:
   - Valores específicos para mejorar la detección de señales
   - Cambios en la lógica de decisión

5. PLAN DE ACCIÓN: Pasos concretos para implementar las mejoras

Sé específico con números y valores. El objetivo es tener señales de confianza ≥70%.
"""
        
        try:
            ai_response = self.ollama.generate_response(ai_prompt)
            return ai_response
        except Exception as e:
            return f"Error generando diagnóstico IA: {e}"
    
    def save_analysis_report(self, market_analysis, ai_diagnosis):
        """Guardar reporte completo del análisis"""
        timestamp = datetime.now()
        
        report = {
            'analysis_id': f"weak_signals_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            'timestamp': timestamp.isoformat(),
            'timestamp_readable': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'market_analysis': market_analysis,
            'ai_diagnosis': ai_diagnosis,
            'summary_stats': self.calculate_summary_stats(market_analysis)
        }
        
        # Guardar JSON completo
        json_file = self.analysis_dir / f"weak_signals_analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Guardar reporte legible
        readable_report = f"""
ANÁLISIS DE SEÑALES DÉBILES
============================
Fecha: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

DIAGNÓSTICO IA:
{ai_diagnosis}

ESTADÍSTICAS DE MERCADO:
{self.format_market_stats(market_analysis)}

ARCHIVO COMPLETO: {json_file.name}
============================
"""
        
        readable_file = self.analysis_dir / f"diagnosis_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(readable_report)
        
        print(f"💾 Análisis guardado: {readable_file.name}")
        return readable_file
    
    def calculate_summary_stats(self, market_analysis):
        """Calcular estadísticas resumidas"""
        if not market_analysis:
            return {}
        
        volatilities = [a['volatility'] for a in market_analysis.values()]
        trends = [a['trend_analysis']['overall_trend'] for a in market_analysis.values()]
        
        return {
            'symbols_analyzed': len(market_analysis),
            'avg_volatility': sum(volatilities) / len(volatilities) if volatilities else 0,
            'max_volatility': max(volatilities) if volatilities else 0,
            'trend_distribution': {
                'UPTREND': trends.count('UPTREND'),
                'DOWNTREND': trends.count('DOWNTREND'),
                'SIDEWAYS': trends.count('SIDEWAYS')
            }
        }
    
    def format_market_stats(self, market_analysis):
        """Formatear estadísticas para el reporte"""
        if not market_analysis:
            return "Sin datos de mercado"
        
        stats = self.calculate_summary_stats(market_analysis)
        
        return f"""
Símbolos analizados: {stats['symbols_analyzed']}
Volatilidad promedio: {stats['avg_volatility']:.2f}%
Volatilidad máxima: {stats['max_volatility']:.2f}%

Distribución de tendencias:
- UPTREND: {stats['trend_distribution']['UPTREND']} símbolos
- DOWNTREND: {stats['trend_distribution']['DOWNTREND']} símbolos  
- SIDEWAYS: {stats['trend_distribution']['SIDEWAYS']} símbolos
"""
    
    def run_complete_analysis(self):
        """Ejecutar análisis completo de señales débiles"""
        print("="*60)
        print("    ANALIZADOR DE SEÑALES DÉBILES")
        print("    ¿Por qué no superan el 50% de confianza?")
        print("="*60)
        
        try:
            # 1. Analizar condiciones actuales del mercado
            market_analysis = self.analyze_current_market_conditions()
            
            if not market_analysis:
                print("❌ No se pudieron obtener datos del mercado")
                return
            
            # 2. Generar diagnóstico con IA
            ai_diagnosis = self.generate_weakness_diagnosis(market_analysis)
            
            # 3. Guardar reporte
            report_file = self.save_analysis_report(market_analysis, ai_diagnosis)
            
            # 4. Mostrar resultados
            print("\n" + "="*60)
            print("DIAGNÓSTICO COMPLETO:")
            print("="*60)
            print(ai_diagnosis)
            print("="*60)
            
            if report_file:
                print(f"\n📄 Reporte completo: {report_file}")
            
            return market_analysis, ai_diagnosis
            
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Función principal"""
    analyzer = WeakSignalAnalyzer()
    
    try:
        analyzer.run_complete_analysis()
        
        print("\n🎯 SIGUIENTE PASO:")
        print("1. Revisar el diagnóstico IA")
        print("2. Implementar los ajustes sugeridos")
        print("3. Ejecutar VALIDADOR_SEÑALES.py después de los cambios")
        
    except KeyboardInterrupt:
        print("\n⏹️ Análisis interrumpido")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()