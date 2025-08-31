"""
Enhanced Tick System - Sistema mejorado con datos scrapeados de MT5
================================================================

Sistema avanzado que usa la documentación scrapeada para implementar
análisis de ticks más sofisticado y funciones profesionales
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class EnhancedTickSystem:
    def __init__(self):
        self.mt5_functions = self.load_scraped_functions()
        self.tick_data = {}
        self.analysis_cache = {}
        self.is_running = False
        
        # Símbolos principales para análisis
        self.main_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
        
        print("Enhanced Tick System inicializado")
        print(f"Funciones MT5 cargadas: {len(self.mt5_functions)}")
        
        if MT5_AVAILABLE:
            self.initialize_mt5_connection()
    
    def load_scraped_functions(self):
        """Cargar funciones scrapeadas de la documentación"""
        try:
            json_file = Path("mt5_scraped_documentation.json")
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('functions', {})
            else:
                print("[WARNING] Archivo de documentación scrapeada no encontrado")
                return {}
        except Exception as e:
            print(f"[ERROR] Error cargando funciones scrapeadas: {e}")
            return {}
    
    def initialize_mt5_connection(self):
        """Inicializar conexión MT5 usando conocimiento scrapeado"""
        try:
            if not mt5.initialize():
                print("[ERROR] No se pudo inicializar MT5")
                return False
            
            # Obtener información de cuenta usando funciones conocidas
            account_info = mt5.account_info()
            if account_info:
                print(f"[MT5] Cuenta conectada: {account_info.login}")
                print(f"[MT5] Broker: {account_info.company}")
                print(f"[MT5] Balance: ${account_info.balance:.2f}")
            
            # Obtener información del terminal
            terminal_info = mt5.terminal_info()
            if terminal_info:
                print(f"[MT5] Terminal: {terminal_info.name}")
                print(f"[MT5] Path: {terminal_info.path}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error inicializando MT5: {e}")
            return False
    
    def get_enhanced_tick_analysis(self, symbol, tick_count=500):
        """Análisis avanzado de ticks usando funciones scrapeadas"""
        try:
            if not MT5_AVAILABLE or not mt5.initialize():
                return self.generate_simulated_analysis(symbol, tick_count)
            
            print(f"[ANÁLISIS] Obteniendo {tick_count} ticks para {symbol}...")
            
            # Usar copy_ticks_from_pos (función scrapeada) - nombre correcto
            ticks = mt5.copy_ticks_from_pos(symbol, 0, tick_count)
            
            if ticks is None or len(ticks) == 0:
                print(f"[WARNING] No hay ticks para {symbol}")
                return None
            
            # Convertir a DataFrame para análisis
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df['mid_price'] = (df['bid'] + df['ask']) / 2
            df['spread'] = df['ask'] - df['bid']
            
            # Análisis exhaustivo
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'tick_count': len(ticks),
                'time_range': {
                    'start': df['time'].min(),
                    'end': df['time'].max(),
                    'duration_minutes': (df['time'].max() - df['time'].min()).total_seconds() / 60
                },
                'price_statistics': self.calculate_price_statistics(df),
                'spread_analysis': self.analyze_spread_patterns(df),
                'volume_analysis': self.analyze_volume_patterns(df),
                'tick_flow_analysis': self.analyze_tick_flow(df),
                'market_microstructure': self.analyze_microstructure(df),
                'liquidity_metrics': self.calculate_liquidity_metrics(df),
                'volatility_analysis': self.analyze_volatility_patterns(df)
            }
            
            # Guardar en caché
            self.analysis_cache[symbol] = analysis
            
            return analysis
            
        except Exception as e:
            print(f"[ERROR] Error en análisis de {symbol}: {e}")
            return None
    
    def calculate_price_statistics(self, df):
        """Calcular estadísticas detalladas de precios"""
        return {
            'bid_stats': {
                'min': float(df['bid'].min()),
                'max': float(df['bid'].max()),
                'mean': float(df['bid'].mean()),
                'std': float(df['bid'].std()),
                'range': float(df['bid'].max() - df['bid'].min())
            },
            'ask_stats': {
                'min': float(df['ask'].min()),
                'max': float(df['ask'].max()),
                'mean': float(df['ask'].mean()),
                'std': float(df['ask'].std()),
                'range': float(df['ask'].max() - df['ask'].min())
            },
            'mid_price_stats': {
                'min': float(df['mid_price'].min()),
                'max': float(df['mid_price'].max()),
                'mean': float(df['mid_price'].mean()),
                'std': float(df['mid_price'].std()),
                'range': float(df['mid_price'].max() - df['mid_price'].min())
            }
        }
    
    def analyze_spread_patterns(self, df):
        """Análisis detallado de patrones de spread"""
        spread_stats = {
            'min_spread': float(df['spread'].min()),
            'max_spread': float(df['spread'].max()),
            'mean_spread': float(df['spread'].mean()),
            'median_spread': float(df['spread'].median()),
            'std_spread': float(df['spread'].std()),
            'spread_stability': float(df['spread'].std() / df['spread'].mean()) if df['spread'].mean() > 0 else 0
        }
        
        # Análisis de distribución de spreads
        spread_percentiles = {
            '25th': float(df['spread'].quantile(0.25)),
            '75th': float(df['spread'].quantile(0.75)),
            '90th': float(df['spread'].quantile(0.90)),
            '95th': float(df['spread'].quantile(0.95))
        }
        
        # Contar spreads por rangos
        spread_ranges = {
            'tight_spreads': len(df[df['spread'] <= spread_stats['mean']]),
            'wide_spreads': len(df[df['spread'] > spread_stats['mean']]),
            'extreme_spreads': len(df[df['spread'] > spread_percentiles['95th']])
        }
        
        return {
            'statistics': spread_stats,
            'percentiles': spread_percentiles,
            'distribution': spread_ranges
        }
    
    def analyze_volume_patterns(self, df):
        """Análisis de patrones de volumen"""
        if 'volume' not in df.columns or df['volume'].isna().all():
            return {'note': 'Datos de volumen no disponibles'}
        
        return {
            'total_volume': float(df['volume'].sum()),
            'mean_volume': float(df['volume'].mean()),
            'volume_distribution': {
                'high_volume_ticks': len(df[df['volume'] > df['volume'].quantile(0.75)]),
                'low_volume_ticks': len(df[df['volume'] <= df['volume'].quantile(0.25)]),
                'zero_volume_ticks': len(df[df['volume'] == 0])
            }
        }
    
    def analyze_tick_flow(self, df):
        """Análisis del flujo de ticks"""
        # Calcular cambios de precio tick a tick
        df['price_change'] = df['mid_price'].diff()
        df['direction'] = np.where(df['price_change'] > 0, 1, 
                                 np.where(df['price_change'] < 0, -1, 0))
        
        flow_analysis = {
            'up_ticks': len(df[df['direction'] == 1]),
            'down_ticks': len(df[df['direction'] == -1]),
            'unchanged_ticks': len(df[df['direction'] == 0]),
            'net_tick_flow': len(df[df['direction'] == 1]) - len(df[df['direction'] == -1]),
            'tick_flow_ratio': len(df[df['direction'] == 1]) / len(df[df['direction'] == -1]) if len(df[df['direction'] == -1]) > 0 else float('inf')
        }
        
        # Análisis de persistencia (runs)
        runs = []
        current_run = 1
        for i in range(1, len(df)):
            if df['direction'].iloc[i] == df['direction'].iloc[i-1] and df['direction'].iloc[i] != 0:
                current_run += 1
            else:
                if current_run > 1:
                    runs.append(current_run)
                current_run = 1
        
        flow_analysis['persistence_analysis'] = {
            'average_run_length': np.mean(runs) if runs else 0,
            'max_run_length': max(runs) if runs else 0,
            'total_runs': len(runs)
        }
        
        return flow_analysis
    
    def analyze_microstructure(self, df):
        """Análisis de microestructura del mercado"""
        # Calcular intervalos entre ticks
        df['time_diff'] = df['time'].diff().dt.total_seconds()
        
        microstructure = {
            'tick_frequency': {
                'mean_interval_seconds': float(df['time_diff'].mean()),
                'median_interval_seconds': float(df['time_diff'].median()),
                'min_interval_seconds': float(df['time_diff'].min()),
                'max_interval_seconds': float(df['time_diff'].max())
            },
            'price_clustering': self.analyze_price_clustering(df),
            'spread_dynamics': self.analyze_spread_dynamics(df)
        }
        
        return microstructure
    
    def analyze_price_clustering(self, df):
        """Análisis de agrupación de precios"""
        # Analizar dígitos finales de precios
        bid_last_digits = df['bid'].apply(lambda x: int((x * 100000) % 10))
        ask_last_digits = df['ask'].apply(lambda x: int((x * 100000) % 10))
        
        return {
            'bid_digit_distribution': bid_last_digits.value_counts().to_dict(),
            'ask_digit_distribution': ask_last_digits.value_counts().to_dict(),
            'round_number_bias': {
                'bid_zeros': len(bid_last_digits[bid_last_digits == 0]) / len(bid_last_digits),
                'ask_zeros': len(ask_last_digits[ask_last_digits == 0]) / len(ask_last_digits)
            }
        }
    
    def analyze_spread_dynamics(self, df):
        """Análisis de dinámicas del spread"""
        df['spread_change'] = df['spread'].diff()
        
        return {
            'spread_volatility': float(df['spread'].std()),
            'spread_persistence': float(df['spread'].autocorr(lag=1)) if len(df) > 1 else 0,
            'spread_mean_reversion': {
                'expanding_spreads': len(df[df['spread_change'] > 0]),
                'contracting_spreads': len(df[df['spread_change'] < 0]),
                'stable_spreads': len(df[df['spread_change'] == 0])
            }
        }
    
    def calculate_liquidity_metrics(self, df):
        """Calcular métricas de liquidez"""
        # Métricas básicas de liquidez basadas en spreads y volumen
        liquidity = {
            'spread_based_liquidity': 1 / df['spread'].mean() if df['spread'].mean() > 0 else 0,
            'effective_spread': float(df['spread'].mean()),
            'quoted_spread': float(df['spread'].median()),
            'spread_impact': float(df['spread'].std())
        }
        
        if 'volume' in df.columns and not df['volume'].isna().all():
            liquidity['volume_weighted_spread'] = float(
                (df['spread'] * df['volume']).sum() / df['volume'].sum()
            ) if df['volume'].sum() > 0 else 0
        
        return liquidity
    
    def analyze_volatility_patterns(self, df):
        """Análisis de patrones de volatilidad"""
        # Volatilidad basada en returns
        df['returns'] = df['mid_price'].pct_change()
        
        volatility = {
            'realized_volatility': float(df['returns'].std()),
            'price_range_volatility': float((df['ask'].max() - df['bid'].min()) / df['mid_price'].mean()),
            'tick_volatility': float(df['mid_price'].diff().std()),
            'volatility_clustering': float(df['returns'].abs().autocorr(lag=1)) if len(df) > 1 else 0
        }
        
        return volatility
    
    def generate_simulated_analysis(self, symbol, tick_count):
        """Generar análisis simulado cuando MT5 no está disponible"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'tick_count': tick_count,
            'note': 'Análisis simulado - MT5 no disponible',
            'simulated_data': {
                'spread_range': [0.00015, 0.00025],
                'volatility_estimate': 0.0012,
                'liquidity_score': 0.85
            }
        }
    
    def run_comprehensive_analysis(self):
        """Ejecutar análisis completo de todos los símbolos"""
        print("\n" + "="*60)
        print(" ENHANCED TICK SYSTEM - ANÁLISIS COMPLETO")
        print("="*60)
        
        results = {}
        
        for symbol in self.main_symbols:
            print(f"\n[PROCESANDO] {symbol}...")
            analysis = self.get_enhanced_tick_analysis(symbol, 300)
            
            if analysis:
                results[symbol] = analysis
                
                # Mostrar resumen
                print(f"  Ticks analizados: {analysis['tick_count']}")
                
                if 'spread_analysis' in analysis:
                    spread_info = analysis['spread_analysis']['statistics']
                    print(f"  Spread promedio: {spread_info['mean_spread']:.5f}")
                    print(f"  Rango de spread: {spread_info['min_spread']:.5f} - {spread_info['max_spread']:.5f}")
                
                if 'tick_flow_analysis' in analysis:
                    flow_info = analysis['tick_flow_analysis']
                    print(f"  Flujo neto: {flow_info['net_tick_flow']:+d} ticks")
                    print(f"  Ratio up/down: {flow_info['tick_flow_ratio']:.2f}")
        
        return results
    
    def save_analysis_results(self, results):
        """Guardar resultados del análisis"""
        try:
            output_data = {
                'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'enhanced_analysis': results,
                'scraped_functions_used': len(self.mt5_functions),
                'symbols_analyzed': len(results)
            }
            
            filename = Path("enhanced_tick_analysis.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n[SAVED] Análisis guardado en: {filename}")
            return str(filename)
            
        except Exception as e:
            print(f"[ERROR] Error guardando: {e}")
            return None

def main():
    try:
        enhanced_system = EnhancedTickSystem()
        
        print("ENHANCED TICK SYSTEM")
        print("="*50)
        print("Sistema avanzado con documentación scrapeada de MQL5")
        print("Análisis profesional de microestructura de mercado")
        print("="*50)
        
        # Ejecutar análisis completo
        results = enhanced_system.run_comprehensive_analysis()
        
        # Guardar resultados
        if results:
            enhanced_system.save_analysis_results(results)
            
            print(f"\n" + "="*60)
            print(" RESUMEN DEL ANÁLISIS MEJORADO")
            print("="*60)
            print(f"Símbolos analizados: {len(results)}")
            print(f"Funciones MT5 utilizadas: {len(enhanced_system.mt5_functions)}")
            print(f"Análisis completado: {datetime.now().strftime('%H:%M:%S')}")
            
            # Mostrar insights principales
            for symbol, analysis in results.items():
                if isinstance(analysis, dict) and 'spread_analysis' in analysis:
                    spread = analysis['spread_analysis']['statistics']['mean_spread']
                    flow = analysis.get('tick_flow_analysis', {}).get('net_tick_flow', 0)
                    print(f"  {symbol}: Spread {spread:.5f}, Flujo {flow:+d}")
        else:
            print("[WARNING] No se pudieron obtener resultados")
        
    except Exception as e:
        print(f"[FATAL] Error: {e}")

if __name__ == "__main__":
    main()