"""
MT5 Tick Analyzer - Análisis de datos tick desde MetaTrader 5
==========================================================

Sistema que obtiene datos tick reales del broker via MT5 y los compara con TwelveData
"""

import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    print("AVISO: MetaTrader5 no instalado. Installar con: pip install MetaTrader5")
    MT5_AVAILABLE = False

try:
    from twelvedata import TDClient
    TWELVEDATA_AVAILABLE = True
except ImportError:
    print("AVISO: TwelveData no instalado. Installar con: pip install twelvedata")
    TWELVEDATA_AVAILABLE = False

load_dotenv()

class MT5TickAnalyzer:
    def __init__(self):
        self.mt5_connected = False
        self.twelvedata_client = None
        
        # Configuración
        self.symbols_mt5 = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
        self.symbols_td = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'XAU/USD', 'BTC/USD']
        
        # Datos
        self.mt5_data = {}
        self.twelvedata_data = {}
        self.comparison_data = {}
        
        self.initialize_connections()
    
    def initialize_connections(self):
        """Inicializar conexiones MT5 y TwelveData"""
        print("INICIALIZANDO CONEXIONES...")
        
        # Inicializar MT5
        if MT5_AVAILABLE:
            try:
                if mt5.initialize():
                    self.mt5_connected = True
                    account_info = mt5.account_info()
                    if account_info:
                        print(f"✅ MT5 conectado - Cuenta: {account_info.login}")
                        print(f"   Broker: {account_info.company}")
                        print(f"   Balance: ${account_info.balance:.2f}")
                    else:
                        print("⚠️  MT5 conectado pero sin info de cuenta")
                else:
                    print("❌ Error conectando MT5")
            except Exception as e:
                print(f"❌ Error MT5: {e}")
        else:
            print("❌ MT5 no disponible")
        
        # Inicializar TwelveData
        if TWELVEDATA_AVAILABLE:
            try:
                api_key = os.getenv('TWELVEDATA_API_KEY')
                if api_key:
                    self.twelvedata_client = TDClient(apikey=api_key)
                    print("✅ TwelveData conectado")
                else:
                    print("❌ TwelveData: API key no encontrada")
            except Exception as e:
                print(f"❌ Error TwelveData: {e}")
        else:
            print("❌ TwelveData no disponible")
    
    def get_mt5_tick_data(self, symbol, count=100):
        """Obtener datos tick de MT5"""
        if not self.mt5_connected:
            return None
        
        try:
            # Obtener ticks recientes
            ticks = mt5.copy_ticks_from_pos(symbol, 0, count)
            
            if ticks is None or len(ticks) == 0:
                print(f"No hay datos tick para {symbol}")
                return None
            
            # Convertir a DataFrame
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calcular spreads y movimientos
            df['spread'] = df['ask'] - df['bid']
            df['mid_price'] = (df['ask'] + df['bid']) / 2
            df['tick_change'] = df['mid_price'].diff()
            df['tick_direction'] = np.where(df['tick_change'] > 0, 'UP', 
                                          np.where(df['tick_change'] < 0, 'DOWN', 'FLAT'))
            
            return df
            
        except Exception as e:
            print(f"Error obteniendo ticks MT5 para {symbol}: {e}")
            return None
    
    def get_mt5_current_price(self, symbol):
        """Obtener precio actual de MT5"""
        if not self.mt5_connected:
            return None
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return {
                    'symbol': symbol,
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': tick.ask - tick.bid,
                    'mid_price': (tick.ask + tick.bid) / 2,
                    'timestamp': datetime.fromtimestamp(tick.time)
                }
            return None
        except Exception as e:
            print(f"Error obteniendo precio MT5 para {symbol}: {e}")
            return None
    
    def get_twelvedata_price(self, symbol):
        """Obtener precio de TwelveData"""
        if not self.twelvedata_client:
            return None
        
        try:
            quote = self.twelvedata_client.quote(symbol=symbol)
            data = quote.as_json()
            
            if data and 'close' in data:
                price = float(data['close'])
                # Simular bid/ask (spread aproximado)
                spread_pct = 0.0001  # 0.01%
                spread = price * spread_pct
                
                return {
                    'symbol': symbol,
                    'price': price,
                    'bid': price - spread/2,
                    'ask': price + spread/2,
                    'spread': spread,
                    'timestamp': datetime.now()
                }
            return None
        except Exception as e:
            print(f"Error obteniendo precio TwelveData para {symbol}: {e}")
            return None
    
    def compare_sources(self):
        """Comparar datos entre MT5 y TwelveData"""
        print("\n" + "="*80)
        print(f" COMPARACIÓN MT5 vs TWELVEDATA - {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
        
        comparison_results = {}
        
        for i, mt5_symbol in enumerate(self.symbols_mt5):
            if i < len(self.symbols_td):
                td_symbol = self.symbols_td[i]
                
                # Obtener datos de ambas fuentes
                mt5_data = self.get_mt5_current_price(mt5_symbol)
                td_data = self.get_twelvedata_price(td_symbol)
                
                if mt5_data and td_data:
                    # Calcular diferencias
                    price_diff = mt5_data['mid_price'] - td_data['price']
                    price_diff_pct = (price_diff / td_data['price']) * 100
                    spread_diff = mt5_data['spread'] - td_data['spread']
                    
                    comparison = {
                        'symbol_mt5': mt5_symbol,
                        'symbol_td': td_symbol,
                        'mt5_bid': mt5_data['bid'],
                        'mt5_ask': mt5_data['ask'],
                        'mt5_mid': mt5_data['mid_price'],
                        'mt5_spread': mt5_data['spread'],
                        'td_price': td_data['price'],
                        'td_bid': td_data['bid'],
                        'td_ask': td_data['ask'],
                        'td_spread': td_data['spread'],
                        'price_difference': price_diff,
                        'price_diff_pct': price_diff_pct,
                        'spread_difference': spread_diff,
                        'timestamp': datetime.now()
                    }
                    
                    comparison_results[mt5_symbol] = comparison
                    
                    # Mostrar comparación
                    print(f"\n{mt5_symbol:<8} (MT5) vs {td_symbol:<8} (TD)")
                    print(f"  MT5: Bid {mt5_data['bid']:.5f} | Ask {mt5_data['ask']:.5f} | "
                          f"Mid {mt5_data['mid_price']:.5f} | Spread {mt5_data['spread']:.5f}")
                    print(f"  TD:  Price {td_data['price']:.5f} | Bid {td_data['bid']:.5f} | "
                          f"Ask {td_data['ask']:.5f} | Spread {td_data['spread']:.5f}")
                    print(f"  DIFF: Price {price_diff:+.5f} ({price_diff_pct:+.3f}%) | "
                          f"Spread {spread_diff:+.5f}")
                    
                    # Análisis de la diferencia
                    if abs(price_diff_pct) > 0.1:
                        print(f"  ⚠️  DIFERENCIA SIGNIFICATIVA: {price_diff_pct:+.3f}%")
                    else:
                        print(f"  ✅ Diferencia normal: {price_diff_pct:+.3f}%")
                
                elif mt5_data:
                    print(f"\n{mt5_symbol:<8} (MT5) - Solo MT5 disponible")
                    print(f"  MT5: Bid {mt5_data['bid']:.5f} | Ask {mt5_data['ask']:.5f} | "
                          f"Spread {mt5_data['spread']:.5f}")
                    
                elif td_data:
                    print(f"\n{td_symbol:<8} (TD) - Solo TwelveData disponible")
                    print(f"  TD: Price {td_data['price']:.5f} | Spread {td_data['spread']:.5f}")
                
                else:
                    print(f"\n{mt5_symbol} - Sin datos disponibles")
        
        return comparison_results
    
    def analyze_mt5_tick_patterns(self, symbol, minutes=5):
        """Analizar patrones de tick de MT5"""
        if not self.mt5_connected:
            return None
        
        try:
            # Obtener ticks de los últimos N minutos
            tick_count = minutes * 60  # Aproximadamente 1 tick por segundo
            df = self.get_mt5_tick_data(symbol, tick_count)
            
            if df is None or len(df) == 0:
                return None
            
            # Filtrar últimos N minutos
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            df = df[df['time'] >= cutoff_time]
            
            if len(df) == 0:
                return None
            
            # Calcular estadísticas
            analysis = {
                'symbol': symbol,
                'period_minutes': minutes,
                'total_ticks': len(df),
                'current_bid': df['bid'].iloc[-1],
                'current_ask': df['ask'].iloc[-1],
                'current_spread': df['spread'].iloc[-1],
                'avg_spread': df['spread'].mean(),
                'min_spread': df['spread'].min(),
                'max_spread': df['spread'].max(),
                'price_high': df['mid_price'].max(),
                'price_low': df['mid_price'].min(),
                'price_range': df['mid_price'].max() - df['mid_price'].min(),
                'up_ticks': len(df[df['tick_direction'] == 'UP']),
                'down_ticks': len(df[df['tick_direction'] == 'DOWN']),
                'flat_ticks': len(df[df['tick_direction'] == 'FLAT']),
                'volatility': df['tick_change'].std(),
                'avg_tick_size': df['tick_change'].abs().mean()
            }
            
            analysis['tick_momentum'] = analysis['up_ticks'] - analysis['down_ticks']
            analysis['tick_bias'] = analysis['tick_momentum'] / analysis['total_ticks'] if analysis['total_ticks'] > 0 else 0
            
            return analysis
            
        except Exception as e:
            print(f"Error analizando ticks MT5 para {symbol}: {e}")
            return None
    
    def save_comparison_data(self):
        """Guardar datos de comparación"""
        try:
            output_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mt5_connected': self.mt5_connected,
                'twelvedata_available': self.twelvedata_client is not None,
                'comparisons': {},
                'mt5_analysis': {}
            }
            
            # Datos de comparación
            comparison_results = self.compare_sources()
            for symbol, data in comparison_results.items():
                output_data['comparisons'][symbol] = {
                    k: v for k, v in data.items() 
                    if k != 'timestamp'
                }
                output_data['comparisons'][symbol]['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Análisis de ticks MT5
            for symbol in self.symbols_mt5:
                analysis = self.analyze_mt5_tick_patterns(symbol, 5)
                if analysis:
                    output_data['mt5_analysis'][symbol] = analysis
            
            # Guardar archivo
            filename = Path("mt5_twelvedata_comparison.json")
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            print(f"\n[GUARDADO] Datos guardados en: {filename}")
            return str(filename)
            
        except Exception as e:
            print(f"Error guardando datos: {e}")
            return None
    
    def create_live_candlesticks_from_ticks(self, symbol, period_seconds=60):
        """Crear velas en tiempo real desde ticks MT5"""
        if not self.mt5_connected:
            return None
        
        try:
            # Obtener ticks del período
            tick_count = period_seconds * 2  # 2 ticks por segundo aproximadamente
            df = self.get_mt5_tick_data(symbol, tick_count)
            
            if df is None or len(df) == 0:
                return None
            
            # Agrupar por períodos de tiempo
            df.set_index('time', inplace=True)
            
            # Crear velas desde ticks
            candles = df['mid_price'].resample(f'{period_seconds}S').agg({
                'Open': 'first',
                'High': 'max', 
                'Low': 'min',
                'Close': 'last'
            }).dropna()
            
            # Agregar datos de spread
            spreads = df['spread'].resample(f'{period_seconds}S').agg({
                'avg_spread': 'mean',
                'min_spread': 'min',
                'max_spread': 'max'
            })
            
            # Combinar datos
            result = pd.concat([candles, spreads], axis=1)
            result['symbol'] = symbol
            result['period_seconds'] = period_seconds
            
            return result
            
        except Exception as e:
            print(f"Error creando velas desde ticks para {symbol}: {e}")
            return None
    
    def disconnect(self):
        """Desconectar servicios"""
        if self.mt5_connected:
            mt5.shutdown()
            print("MT5 desconectado")

def main():
    try:
        analyzer = MT5TickAnalyzer()
        
        print("MT5 TICK ANALYZER")
        print("="*50)
        print("Funcionalidades:")
        print("  • Datos tick reales desde MetaTrader 5")
        print("  • Comparación con TwelveData")
        print("  • Análisis de spreads y movimientos")
        print("  • Creación de velas desde ticks")
        print("  • Detección de diferencias entre fuentes")
        print("="*50)
        
        if not analyzer.mt5_connected and not analyzer.twelvedata_client:
            print("❌ No hay fuentes de datos disponibles")
            return
        
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Analizando datos...")
                
                # Comparar fuentes
                analyzer.save_comparison_data()
                
                # Mostrar análisis de ticks MT5
                if analyzer.mt5_connected:
                    print("\nANÁLISIS DE TICKS MT5 (5 minutos):")
                    print("-" * 50)
                    for symbol in analyzer.symbols_mt5[:3]:  # Primeros 3 símbolos
                        analysis = analyzer.analyze_mt5_tick_patterns(symbol, 5)
                        if analysis:
                            print(f"\n{symbol}:")
                            print(f"  Ticks totales: {analysis['total_ticks']}")
                            print(f"  Spread actual: {analysis['current_spread']:.5f} "
                                  f"(Avg: {analysis['avg_spread']:.5f})")
                            print(f"  Rango precio: {analysis['price_range']:.5f}")
                            print(f"  Ticks: ↑{analysis['up_ticks']} ↓{analysis['down_ticks']} "
                                  f"→{analysis['flat_ticks']}")
                            print(f"  Momentum: {analysis['tick_momentum']:+d} "
                                  f"(Bias: {analysis['tick_bias']:+.3f})")
                
                print(f"\n[ESPERA] Próxima actualización en 30 segundos...")
                print("Presiona Ctrl+C para detener")
                print("="*80)
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n[DETENIDO] Sistema detenido por usuario")
            
    except Exception as e:
        print(f"Error fatal: {e}")
        
    finally:
        if 'analyzer' in locals():
            analyzer.disconnect()

if __name__ == "__main__":
    main()