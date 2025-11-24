#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DIAGNOSTICO DE SEÑALES DEBILES
==============================
Identifica por que las señales no superan el 50% de confianza
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except:
        locale.setlocale(locale.LC_ALL, '')

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.ai.ollama_client import OllamaClient
    from src.data.twelvedata_client import TwelveDataClient
except ImportError as e:
    print(f"Error importando modulos: {e}")
    sys.exit(1)

class SignalDiagnostic:
    """Diagnosticador de señales debiles"""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.td_client = TwelveDataClient()
        self.analysis_dir = Path("logs/diagnostics")
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_market_now(self):
        """Analizar mercado actual para diagnosticar señales debiles"""
        
        print("ANALIZANDO CONDICIONES ACTUALES DEL MERCADO...")
        print("="*60)
        
        symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']
        results = {}
        
        for symbol in symbols:
            print(f"\nAnalizando {symbol}...")
            
            try:
                # Mapear simbolos
                if 'XAU' in symbol:
                    td_symbol = 'XAU/USD'
                elif 'BTC' in symbol:
                    td_symbol = 'BTC/USD'
                elif 'EUR' in symbol:
                    td_symbol = 'EUR/USD'
                elif 'GBP' in symbol:
                    td_symbol = 'GBP/USD'
                else:
                    continue
                
                # Obtener precio actual
                if mt5.initialize():
                    tick = mt5.symbol_info_tick(symbol)
                    current_price = tick.bid if tick else 0
                    mt5.shutdown()
                else:
                    current_price = 0
                
                # Obtener datos historicos
                data_5m = self.td_client.get_time_series(td_symbol, interval='5min', outputsize=20)
                data_1h = self.td_client.get_time_series(td_symbol, interval='1h', outputsize=20)
                
                if not data_5m or not data_1h:
                    print(f"  ERROR: No se pudieron obtener datos para {symbol}")
                    continue
                
                # Calcular volatilidad
                prices = [float(d['close']) for d in data_5m[-10:]]
                volatility = self.calculate_volatility(prices)
                
                # Analizar tendencia
                trend = self.analyze_trend_simple(data_5m, data_1h)
                
                # Obtener indicadores
                indicators = self.td_client.get_technical_indicators(td_symbol, '5min')
                
                results[symbol] = {
                    'price': current_price,
                    'volatility': volatility,
                    'trend': trend,
                    'indicators': indicators,
                    'data_quality': len(data_5m)
                }
                
                print(f"  Precio: ${current_price:.2f}")
                print(f"  Volatilidad: {volatility:.2f}%")
                print(f"  Tendencia: {trend}")
                
            except Exception as e:
                print(f"  ERROR: {e}")
                continue
        
        return results
    
    def calculate_volatility(self, prices):
        """Calcular volatilidad basica"""
        if len(prices) < 2:
            return 0
        
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / mean_price * 100
        
        return volatility
    
    def analyze_trend_simple(self, data_5m, data_1h):
        """Analisis basico de tendencia"""
        if len(data_5m) < 5 or len(data_1h) < 3:
            return 'INSUFFICIENT_DATA'
        
        # Comparar precios recientes
        recent_5m = sum(float(d['close']) for d in data_5m[:3]) / 3
        older_5m = sum(float(d['close']) for d in data_5m[-3:]) / 3
        
        recent_1h = float(data_1h[0]['close'])
        older_1h = float(data_1h[-1]['close'])
        
        # Determinar tendencia
        if recent_5m > older_5m * 1.005 and recent_1h > older_1h * 1.01:
            return 'FUERTE_UPTREND'
        elif recent_5m > older_5m * 1.002:
            return 'UPTREND'
        elif recent_5m < older_5m * 0.995 and recent_1h < older_1h * 0.99:
            return 'FUERTE_DOWNTREND'
        elif recent_5m < older_5m * 0.998:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def generate_diagnosis(self, market_data):
        """Generar diagnostico con IA"""
        
        print("\nGENERANDO DIAGNOSTICO CON IA...")
        
        # Preparar resumen
        summary = "ANALISIS ACTUAL DEL MERCADO:\n"
        summary += "="*40 + "\n"
        
        for symbol, data in market_data.items():
            summary += f"\n{symbol}:\n"
            summary += f"  Precio: ${data['price']:.2f}\n"
            summary += f"  Volatilidad: {data['volatility']:.2f}%\n"
            summary += f"  Tendencia: {data['trend']}\n"
            summary += f"  Indicadores disponibles: {len(data.get('indicators', {}))}\n"
        
        # Prompt para IA
        prompt = f"""
Eres un experto en trading algoritmico. Nuestro sistema genera señales con BAJA CONFIANZA (50% o menos).

DATOS ACTUALES:
{summary}

PROBLEMA:
- Sistema recomienda NO_OPERAR constantemente
- Confianza promedio: 50%
- Necesitamos identificar la causa raiz

ANALIZA:

1. CAUSA PRINCIPAL: ¿Por que las señales son debiles?
   - ¿Es por condiciones de mercado?
   - ¿Configuracion de algoritmos?
   - ¿Parametros de IA?

2. CONDICIONES DE MERCADO: 
   - ¿La volatilidad es adecuada?
   - ¿Las tendencias son claras?
   - ¿Hay oportunidades de trading?

3. RECOMENDACIONES ESPECIFICAS:
   - Ajustar umbrales de confianza
   - Modificar indicadores tecnicos
   - Cambiar timeframes
   - Mejorar criterios de IA

4. VALORES CONCRETOS:
   - Que parametros cambiar
   - Que valores usar
   - Como mejorar la detección

5. PLAN DE ACCION:
   Pasos especificos para implementar mejoras

Objetivo: Lograr señales con confianza >=70%
"""
        
        try:
            response = self.ollama.generate_response(prompt)
            return response
        except Exception as e:
            return f"Error en diagnostico IA: {e}"
    
    def save_diagnosis(self, market_data, ai_diagnosis):
        """Guardar diagnostico completo"""
        timestamp = datetime.now()
        
        # Crear reporte
        report = {
            'diagnosis_id': f"diagnosis_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            'timestamp': timestamp.isoformat(),
            'market_data': market_data,
            'ai_diagnosis': ai_diagnosis,
            'summary': self.create_summary(market_data)
        }
        
        # Guardar JSON
        json_file = self.analysis_dir / f"diagnosis_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Crear reporte legible
        readable_report = f"""
DIAGNOSTICO DE SEÑALES DEBILES
==============================
Fecha: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

DIAGNOSTICO IA:
{ai_diagnosis}

RESUMEN DE MERCADO:
{self.format_summary(market_data)}

ARCHIVO COMPLETO: {json_file.name}
==============================
"""
        
        text_file = self.analysis_dir / f"diagnosis_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(readable_report)
        
        print(f"DIAGNOSTICO GUARDADO: {text_file.name}")
        return text_file
    
    def create_summary(self, market_data):
        """Crear resumen estadistico"""
        if not market_data:
            return {}
        
        volatilities = [d['volatility'] for d in market_data.values()]
        trends = [d['trend'] for d in market_data.values()]
        
        return {
            'symbols_count': len(market_data),
            'avg_volatility': sum(volatilities) / len(volatilities),
            'max_volatility': max(volatilities),
            'trend_distribution': {
                'UPTREND': trends.count('UPTREND') + trends.count('FUERTE_UPTREND'),
                'DOWNTREND': trends.count('DOWNTREND') + trends.count('FUERTE_DOWNTREND'),
                'SIDEWAYS': trends.count('SIDEWAYS')
            }
        }
    
    def format_summary(self, market_data):
        """Formatear resumen para reporte"""
        if not market_data:
            return "Sin datos disponibles"
        
        summary = self.create_summary(market_data)
        
        return f"""
Simbolos analizados: {summary['symbols_count']}
Volatilidad promedio: {summary['avg_volatility']:.2f}%
Volatilidad maxima: {summary['max_volatility']:.2f}%

Distribucion de tendencias:
- UPTREND: {summary['trend_distribution']['UPTREND']}
- DOWNTREND: {summary['trend_distribution']['DOWNTREND']}
- SIDEWAYS: {summary['trend_distribution']['SIDEWAYS']}
"""
    
    def run_full_diagnosis(self):
        """Ejecutar diagnostico completo"""
        print("="*60)
        print("    DIAGNOSTICO DE SEÑALES DEBILES")
        print("    Por que no superan el 50% de confianza?")
        print("="*60)
        
        try:
            # Analizar mercado actual
            market_data = self.analyze_market_now()
            
            if not market_data:
                print("ERROR: No se pudieron obtener datos del mercado")
                return
            
            # Generar diagnostico IA
            ai_diagnosis = self.generate_diagnosis(market_data)
            
            # Guardar resultados
            report_file = self.save_diagnosis(market_data, ai_diagnosis)
            
            # Mostrar resultados
            print("\n" + "="*60)
            print("DIAGNOSTICO COMPLETO:")
            print("="*60)
            print(ai_diagnosis)
            print("="*60)
            
            if report_file:
                print(f"\nREPORTE COMPLETO: {report_file}")
            
            print("\nSIGUIENTE PASO:")
            print("1. Implementar ajustes sugeridos")
            print("2. Reiniciar sistema de señales")  
            print("3. Monitorear mejoras en confianza")
            
        except Exception as e:
            print(f"ERROR EN DIAGNOSTICO: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Funcion principal"""
    diagnostic = SignalDiagnostic()
    
    try:
        diagnostic.run_full_diagnosis()
        
    except KeyboardInterrupt:
        print("\nDIAGNOSTICO INTERRUMPIDO")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()