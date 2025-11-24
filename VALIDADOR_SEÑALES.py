#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VALIDADOR DE SEÑALES CON IA
============================
Analiza la efectividad de las señales generadas y sugiere mejoras
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5
import sys
import os

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.ai.ollama_client import OllamaClient
    from src.utils.signal_logger import SignalLogger
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)

class SignalValidator:
    """Validador inteligente de señales usando IA"""
    
    def __init__(self):
        self.signal_logger = SignalLogger()
        self.ollama = OllamaClient()
        self.results_dir = Path("logs/validation")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_signals(self, date=None):
        """Cargar señales de un día específico"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        json_file = Path(f"logs/signals/signals_{date}.json")
        
        if not json_file.exists():
            print(f"❌ No se encontraron señales para {date}")
            return []
        
        with open(json_file, 'r', encoding='utf-8') as f:
            signals = json.load(f)
        
        print(f"📊 Cargadas {len(signals)} señales de {date}")
        return signals
    
    def validate_signal_outcome(self, signal, hours_later=1):
        """
        Validar qué pasó con una señal después de X horas
        
        Returns:
            dict: Resultado del análisis
        """
        try:
            if not mt5.initialize():
                return {'error': 'No se pudo conectar a MT5'}
            
            symbol = signal['symbol']
            signal_time = datetime.fromisoformat(signal['timestamp'])
            check_time = signal_time + timedelta(hours=hours_later)
            signal_price = signal.get('price_at_signal', 0)
            
            # Obtener precio después de X horas
            if check_time > datetime.now():
                # Si es futuro, usar precio actual
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    later_price = tick.bid
                else:
                    return {'error': f'No se pudo obtener tick para {symbol}'}
            else:
                # Obtener datos históricos
                rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M1, check_time, 1)
                if rates is None or len(rates) == 0:
                    return {'error': f'No hay datos históricos para {symbol}'}
                later_price = rates[0]['close']
            
            # Calcular resultado
            if signal_price == 0:
                return {'error': 'Precio de señal no disponible'}
            
            # Determinar valor de pip
            if symbol.startswith(('EUR', 'GBP', 'AUD', 'NZD')):
                pip_value = 0.0001
            elif 'JPY' in symbol:
                pip_value = 0.01
            else:
                pip_value = 1.0
            
            price_change = later_price - signal_price
            pips_change = price_change / pip_value
            
            # Evaluar efectividad según el tipo de señal
            signal_type = signal.get('signal_type', 'NO_OPERAR')
            confidence = signal.get('confidence', 0)
            
            if signal_type == 'BUY':
                success = pips_change > 0
                profit_pips = pips_change if success else 0
                loss_pips = abs(pips_change) if not success else 0
            elif signal_type == 'SELL':
                success = pips_change < 0
                profit_pips = abs(pips_change) if success else 0
                loss_pips = pips_change if not success else 0
            else:
                # NO_OPERAR - evaluar si hubiera sido rentable operar
                success = abs(pips_change) < 10  # Correcto no operar si movimiento < 10 pips
                profit_pips = 0
                loss_pips = 0
            
            result = {
                'signal_id': signal.get('id', ''),
                'symbol': symbol,
                'signal_type': signal_type,
                'confidence': confidence,
                'signal_price': signal_price,
                f'price_after_{hours_later}h': later_price,
                'price_change': price_change,
                'pips_change': pips_change,
                'success': success,
                'profit_pips': profit_pips,
                'loss_pips': loss_pips,
                'hours_analyzed': hours_later,
                'analysis_time': datetime.now().isoformat()
            }
            
            mt5.shutdown()
            return result
            
        except Exception as e:
            return {'error': f'Error validando señal: {e}'}
    
    def analyze_signals_batch(self, signals, hours_later=1):
        """Analizar un lote de señales"""
        results = []
        
        print(f"🔍 Analizando efectividad de {len(signals)} señales después de {hours_later}h...")
        
        for i, signal in enumerate(signals, 1):
            print(f"  [{i}/{len(signals)}] Analizando {signal['symbol']}...", end=" ")
            
            result = self.validate_signal_outcome(signal, hours_later)
            
            if 'error' in result:
                print(f"❌ {result['error']}")
            else:
                success_icon = "✅" if result['success'] else "❌"
                print(f"{success_icon} {result['pips_change']:+.1f} pips")
            
            results.append(result)
        
        return results
    
    def generate_ai_analysis(self, results):
        """Generar análisis inteligente usando IA"""
        try:
            # Preparar estadísticas
            valid_results = [r for r in results if 'error' not in r]
            
            if not valid_results:
                return "No hay resultados válidos para analizar"
            
            total_signals = len(valid_results)
            successful = sum(1 for r in valid_results if r['success'])
            success_rate = (successful / total_signals) * 100 if total_signals > 0 else 0
            
            # Análisis por tipo de señal
            buy_signals = [r for r in valid_results if r['signal_type'] == 'BUY']
            sell_signals = [r for r in valid_results if r['signal_type'] == 'SELL']
            no_operate = [r for r in valid_results if r['signal_type'] == 'NO_OPERAR']
            
            # Análisis por confianza
            high_conf = [r for r in valid_results if r['confidence'] >= 70]
            mid_conf = [r for r in valid_results if 50 <= r['confidence'] < 70]
            low_conf = [r for r in valid_results if r['confidence'] < 50]
            
            stats_summary = f"""
ESTADÍSTICAS DE VALIDACIÓN:
===========================
Total señales: {total_signals}
Señales exitosas: {successful}
Tasa de éxito: {success_rate:.1f}%

Por tipo de señal:
- BUY: {len(buy_signals)} señales
- SELL: {len(sell_signals)} señales  
- NO_OPERAR: {len(no_operate)} señales

Por nivel de confianza:
- Alta (≥70%): {len(high_conf)} señales
- Media (50-69%): {len(mid_conf)} señales
- Baja (<50%): {len(low_conf)} señales

Detalle de resultados:
"""
            
            for result in valid_results[:10]:  # Mostrar primeros 10
                stats_summary += f"\n- {result['symbol']} {result['signal_type']}: {result['pips_change']:+.1f} pips (Conf: {result['confidence']:.1f}%)"
            
            # Enviar a IA para análisis
            ai_prompt = f"""
Analiza estos resultados de validación de señales de trading y proporciona:

1. DIAGNÓSTICO: ¿Qué está funcionando bien y qué no?
2. PROBLEMAS IDENTIFICADOS: ¿Por qué las señales no superan el 50% de confianza?
3. RECOMENDACIONES ESPECÍFICAS: ¿Qué ajustes hacer al sistema?
4. PRÓXIMOS PASOS: ¿Cómo mejorar la generación de señales?

Datos de validación:
{stats_summary}

Se específico y práctico en las recomendaciones. El objetivo es mejorar la calidad y confianza de las señales.
"""
            
            print("🤖 Generando análisis con IA...")
            ai_response = self.ollama.generate_response(ai_prompt)
            
            return ai_response
            
        except Exception as e:
            return f"Error generando análisis IA: {e}"
    
    def save_validation_report(self, results, ai_analysis):
        """Guardar reporte completo de validación"""
        try:
            timestamp = datetime.now()
            
            # Crear reporte completo
            report = {
                'validation_id': f"validation_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                'timestamp': timestamp.isoformat(),
                'timestamp_readable': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'total_signals_analyzed': len(results),
                'valid_results': len([r for r in results if 'error' not in r]),
                'ai_analysis': ai_analysis,
                'detailed_results': results
            }
            
            # Guardar JSON
            report_file = self.results_dir / f"validation_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # Crear reporte legible
            readable_report = f"""
REPORTE DE VALIDACIÓN DE SEÑALES
================================
Fecha: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Señales analizadas: {len(results)}
Resultados válidos: {len([r for r in results if 'error' not in r])}

ANÁLISIS IA:
{ai_analysis}

ARCHIVO COMPLETO: {report_file.name}
================================
"""
            
            # Guardar reporte legible
            readable_file = self.results_dir / f"validation_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(readable_file, 'w', encoding='utf-8') as f:
                f.write(readable_report)
            
            print(f"📋 Reporte guardado: {readable_file.name}")
            return readable_file
            
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")
            return None
    
    def run_daily_validation(self, hours_later=1):
        """Ejecutar validación completa del día"""
        print("="*60)
        print("    VALIDADOR DE SEÑALES CON IA")
        print("="*60)
        
        # Cargar señales del día
        signals = self.load_signals()
        
        if not signals:
            print("❌ No hay señales para validar")
            return
        
        # Analizar efectividad
        results = self.analyze_signals_batch(signals, hours_later)
        
        # Generar análisis IA
        ai_analysis = self.generate_ai_analysis(results)
        
        # Guardar reporte
        report_file = self.save_validation_report(results, ai_analysis)
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("ANÁLISIS IA:")
        print("="*60)
        print(ai_analysis)
        print("="*60)
        
        if report_file:
            print(f"\n📄 Reporte completo: {report_file}")
        
        return results, ai_analysis

def main():
    """Función principal"""
    validator = SignalValidator()
    
    try:
        # Validación por defecto: 1 hora después
        validator.run_daily_validation(hours_later=1)
        
        print("\n🎯 OPCIONES ADICIONALES:")
        print("- Cambiar hours_later para análisis a más largo plazo")
        print("- Usar fechas específicas: validator.load_signals('20250909')")
        print("- Análisis de múltiples días para tendencias")
        
    except KeyboardInterrupt:
        print("\n⏹️ Validación interrumpida")
    except Exception as e:
        print(f"\n❌ Error en validación: {e}")

if __name__ == "__main__":
    main()