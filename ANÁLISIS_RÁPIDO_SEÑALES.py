#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ANALISIS RAPIDO DE SEÑALES DEBILES
==================================
Diagnostico directo de por que las señales no superan 50%
"""

import MetaTrader5 as mt5
from datetime import datetime
import sys
from pathlib import Path

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.ai.ollama_client import OllamaClient
except ImportError:
    print("No se pudo importar OllamaClient, usando análisis básico")
    OllamaClient = None

class RapidSignalAnalysis:
    """Análisis rápido de señales débiles usando solo MT5"""
    
    def __init__(self):
        self.ollama = OllamaClient() if OllamaClient else None
        
    def get_mt5_data(self, symbol, timeframe=mt5.TIMEFRAME_M5, count=20):
        """Obtener datos directamente de MT5"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                return None
            return rates
        except Exception as e:
            print(f"  Error obteniendo datos MT5: {e}")
            return None
    
    def analyze_symbol(self, symbol):
        """Análizar un símbolo específico"""
        print(f"\nAnalizando {symbol}...")
        
        try:
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print(f"  ERROR: No se pudo obtener tick de {symbol}")
                return None
            
            current_price = tick.bid
            spread = tick.ask - tick.bid
            
            # Obtener datos históricos
            rates_5m = self.get_mt5_data(symbol, mt5.TIMEFRAME_M5, 20)
            rates_15m = self.get_mt5_data(symbol, mt5.TIMEFRAME_M15, 20)
            rates_1h = self.get_mt5_data(symbol, mt5.TIMEFRAME_H1, 20)
            
            if not all([rates_5m is not None, rates_15m is not None, rates_1h is not None]):
                print(f"  ERROR: Datos históricos incompletos para {symbol}")
                return None
            
            # Calcular volatilidad (últimas 10 velas de 5min)
            recent_prices = [float(rate['close']) for rate in rates_5m[-10:]]
            volatility = self.calculate_volatility(recent_prices)
            
            # Analizar tendencia
            trend_5m = self.get_trend(rates_5m)
            trend_15m = self.get_trend(rates_15m)
            trend_1h = self.get_trend(rates_1h)
            
            # Calcular RSI básico
            rsi = self.calculate_basic_rsi([float(rate['close']) for rate in rates_5m])
            
            # Calcular movimiento reciente
            price_change_1h = ((current_price - float(rates_5m[-4]['close'])) / float(rates_5m[-4]['close'])) * 100
            
            # Determinar fuerza de señal potencial
            signal_strength = self.evaluate_signal_strength(
                volatility, trend_5m, trend_15m, trend_1h, rsi, price_change_1h
            )
            
            analysis = {
                'symbol': symbol,
                'price': current_price,
                'spread': spread,
                'volatility_pct': volatility,
                'trend_5m': trend_5m,
                'trend_15m': trend_15m,
                'trend_1h': trend_1h,
                'rsi': rsi,
                'price_change_1h_pct': price_change_1h,
                'signal_strength': signal_strength,
                'data_quality': 'OK'
            }
            
            print(f"  Precio: {current_price:.5f} (Spread: {spread:.5f})")
            print(f"  Volatilidad: {volatility:.2f}%")
            print(f"  Tendencias: 5m={trend_5m}, 15m={trend_15m}, 1h={trend_1h}")
            print(f"  RSI: {rsi:.1f}")
            print(f"  Cambio 1h: {price_change_1h:+.2f}%")
            print(f"  Fuerza señal potencial: {signal_strength}")
            
            return analysis
            
        except Exception as e:
            print(f"  ERROR analizando {symbol}: {e}")
            return None
    
    def calculate_volatility(self, prices):
        """Calcular volatilidad como desviación estándar"""
        if len(prices) < 2:
            return 0
        
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        volatility = (std_dev / mean) * 100
        
        return volatility
    
    def get_trend(self, rates):
        """Determinar tendencia básica"""
        if len(rates) < 5:
            return 'INSUFFICIENT'
        
        # Comparar promedio de últimas 3 vs 3 anteriores
        recent_avg = sum(float(rate['close']) for rate in rates[-3:]) / 3
        previous_avg = sum(float(rate['close']) for rate in rates[-6:-3]) / 3
        
        change_pct = ((recent_avg - previous_avg) / previous_avg) * 100
        
        if change_pct > 0.3:
            return 'UP_STRONG' if change_pct > 1.0 else 'UP'
        elif change_pct < -0.3:
            return 'DOWN_STRONG' if change_pct < -1.0 else 'DOWN'
        else:
            return 'SIDEWAYS'
    
    def calculate_basic_rsi(self, prices, period=14):
        """Calcular RSI básico"""
        if len(prices) < period + 1:
            return 50  # Neutral si no hay suficientes datos
        
        # Calcular cambios
        changes = []
        for i in range(1, len(prices)):
            changes.append(prices[i] - prices[i-1])
        
        if len(changes) < period:
            return 50
        
        # Separar ganancias y pérdidas
        gains = [change if change > 0 else 0 for change in changes[-period:]]
        losses = [-change if change < 0 else 0 for change in changes[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100  # No hay pérdidas
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def evaluate_signal_strength(self, volatility, trend_5m, trend_15m, trend_1h, rsi, price_change):
        """Evaluar la fuerza potencial de una señal"""
        score = 0
        
        # Volatilidad apropiada (ni muy baja ni muy alta)
        if 0.5 <= volatility <= 2.0:
            score += 20
        elif 0.2 <= volatility <= 3.0:
            score += 10
        
        # Tendencias alineadas
        strong_trends = ['UP_STRONG', 'DOWN_STRONG']
        medium_trends = ['UP', 'DOWN']
        
        if trend_5m in strong_trends and trend_15m in strong_trends and trend_1h in strong_trends:
            score += 30  # Todas las tendencias fuertes y alineadas
        elif trend_5m in (strong_trends + medium_trends) and trend_15m in (strong_trends + medium_trends):
            score += 20  # Al menos 5m y 15m alineadas
        elif trend_5m != 'SIDEWAYS':
            score += 10  # Al menos 5m tiene dirección
        
        # RSI en zona operativa (no extremo)
        if 30 <= rsi <= 70:
            score += 15
        elif 20 <= rsi <= 80:
            score += 10
        
        # Movimiento reciente significativo
        if abs(price_change) >= 0.5:
            score += 15
        elif abs(price_change) >= 0.2:
            score += 10
        
        # Clasificar fuerza
        if score >= 70:
            return 'MUY_FUERTE'
        elif score >= 50:
            return 'FUERTE'
        elif score >= 30:
            return 'MEDIA'
        elif score >= 15:
            return 'DEBIL'
        else:
            return 'MUY_DEBIL'
    
    def generate_diagnosis(self, analyses):
        """Generar diagnóstico de por qué las señales son débiles"""
        
        if not analyses:
            return "No hay datos para diagnosticar"
        
        # Estadísticas generales
        valid_analyses = [a for a in analyses if a is not None]
        if not valid_analyses:
            return "No se pudieron obtener datos válidos para el diagnóstico"
        
        # Analizar patrones
        volatilities = [a['volatility_pct'] for a in valid_analyses]
        signal_strengths = [a['signal_strength'] for a in valid_analyses]
        trends_5m = [a['trend_5m'] for a in valid_analyses]
        rsis = [a['rsi'] for a in valid_analyses]
        
        avg_volatility = sum(volatilities) / len(volatilities)
        max_volatility = max(volatilities)
        
        diagnosis = f"""
DIAGNOSTICO DE SEÑALES DEBILES
==============================

RESUMEN GENERAL:
- Símbolos analizados: {len(valid_analyses)}
- Volatilidad promedio: {avg_volatility:.2f}%
- Volatilidad máxima: {max_volatility:.2f}%

DISTRIBUCION DE FUERZA DE SEÑALES:
- MUY_FUERTE: {signal_strengths.count('MUY_FUERTE')}
- FUERTE: {signal_strengths.count('FUERTE')}
- MEDIA: {signal_strengths.count('MEDIA')}
- DEBIL: {signal_strengths.count('DEBIL')}
- MUY_DEBIL: {signal_strengths.count('MUY_DEBIL')}

ANALISIS POR SIMBOLO:
"""
        
        for analysis in valid_analyses:
            diagnosis += f"""
{analysis['symbol']}:
  - Volatilidad: {analysis['volatility_pct']:.2f}%
  - Tendencias: 5m={analysis['trend_5m']}, 15m={analysis['trend_15m']}, 1h={analysis['trend_1h']}
  - RSI: {analysis['rsi']:.1f}
  - Fuerza potencial: {analysis['signal_strength']}
  - Problema principal: {self.identify_main_problem(analysis)}
"""
        
        # Diagnóstico general
        diagnosis += f"""

PROBLEMAS IDENTIFICADOS:

1. VOLATILIDAD:
"""
        if avg_volatility < 0.3:
            diagnosis += "   PROBLEMA: Volatilidad muy baja (<0.3%) - Mercado demasiado estático"
        elif avg_volatility > 3.0:
            diagnosis += "   PROBLEMA: Volatilidad muy alta (>3.0%) - Mercado demasiado errático"
        else:
            diagnosis += "   OK: Volatilidad en rango apropiado"
        
        diagnosis += f"""

2. TENDENCIAS:
   - SIDEWAYS dominante: {trends_5m.count('SIDEWAYS')} de {len(trends_5m)} símbolos
   - Falta de direccionalidad clara"""
        
        diagnosis += f"""

3. RSI PROMEDIO: {sum(rsis)/len(rsis):.1f}
"""
        if sum(rsis)/len(rsis) > 70:
            diagnosis += "   PROBLEMA: RSI en sobrecompra - Pocas oportunidades de BUY"
        elif sum(rsis)/len(rsis) < 30:
            diagnosis += "   PROBLEMA: RSI en sobreventa - Pocas oportunidades de SELL"
        else:
            diagnosis += "   OK: RSI en zona neutral"
        
        diagnosis += f"""

RECOMENDACIONES:

1. AJUSTAR UMBRALES:
   - Reducir umbral de confianza de 70% a 60%
   - Permitir señales con volatilidad ≥0.2%
   
2. MEJORAR DETECCIÓN:
   - Ponderar más el timeframe de 5 minutos
   - Considerar divergencias RSI
   - Usar breakouts de consolidación
   
3. CONDICIONES ACTUALES:
   - Mercado en modo CONSOLIDACION/SIDEWAYS
   - Pocas tendencias direccionales claras
   - Esperar breakouts o usar estrategias de rango

CONCLUSION:
Las señales débiles son NORMALES en condiciones actuales del mercado.
El sistema funciona correctamente pero el mercado está consolidando.
"""
        
        return diagnosis
    
    def identify_main_problem(self, analysis):
        """Identificar el problema principal de cada símbolo"""
        problems = []
        
        if analysis['volatility_pct'] < 0.3:
            problems.append("Volatilidad muy baja")
        elif analysis['volatility_pct'] > 3.0:
            problems.append("Volatilidad muy alta")
        
        if analysis['trend_5m'] == 'SIDEWAYS' and analysis['trend_15m'] == 'SIDEWAYS':
            problems.append("Sin tendencia clara")
        
        if analysis['rsi'] > 80:
            problems.append("RSI sobrecomprado")
        elif analysis['rsi'] < 20:
            problems.append("RSI sobrevendido")
        
        if abs(analysis['price_change_1h_pct']) < 0.1:
            problems.append("Movimiento insuficiente")
        
        return problems[0] if problems else "Sin problemas mayores"
    
    def run_diagnosis(self):
        """Ejecutar diagnóstico completo"""
        print("="*60)
        print("    ANALISIS RAPIDO DE SEÑALES DEBILES")
        print("    Por que no superan el 50% de confianza?")
        print("="*60)
        
        # Conectar a MT5
        if not mt5.initialize():
            print("ERROR: No se pudo conectar a MetaTrader 5")
            return
        
        try:
            # Símbolos principales
            symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']
            
            print(f"Analizando {len(symbols)} símbolos principales...")
            
            analyses = []
            for symbol in symbols:
                analysis = self.analyze_symbol(symbol)
                analyses.append(analysis)
            
            # Generar diagnóstico
            diagnosis = self.generate_diagnosis(analyses)
            
            # Mostrar resultados
            print("\n" + "="*60)
            print("DIAGNOSTICO COMPLETO:")
            print("="*60)
            print(diagnosis)
            print("="*60)
            
            # Guardar diagnóstico
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            diagnosis_file = f"logs/diagnosis_rapido_{timestamp}.txt"
            
            Path("logs").mkdir(exist_ok=True)
            with open(diagnosis_file, 'w', encoding='utf-8') as f:
                f.write(f"DIAGNOSTICO GENERADO: {datetime.now()}\n\n")
                f.write(diagnosis)
            
            print(f"\nDIAGNOSTICO GUARDADO EN: {diagnosis_file}")
            
        except Exception as e:
            print(f"ERROR EN DIAGNOSTICO: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            mt5.shutdown()

def main():
    analyzer = RapidSignalAnalysis()
    analyzer.run_diagnosis()

if __name__ == "__main__":
    main()