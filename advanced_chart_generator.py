"""
Advanced Chart Generator - Gráficos Avanzados de Trading
========================================================

Sistema avanzado para crear gráficos de:
- Velas Japonesas (Candlesticks)
- Gráficos Lineales
- Gráficos de Barras
- Gráficos OHLC

Usando mplfinance + matplotlib + TwelveData API
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Importar bibliotecas especializadas
try:
    import mplfinance as mpf
    from twelvedata import TDClient
except ImportError as e:
    print(f"ERROR: Dependencias faltantes - {e}")
    print("Instalar con: pip install mplfinance twelvedata[pandas,matplotlib]")
    sys.exit(1)

# Cargar configuración
load_dotenv()

class AdvancedChartGenerator:
    def __init__(self):
        """Inicializar generador de gráficos avanzados"""
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY no encontrada")
        
        self.client = TDClient(apikey=self.api_key)
        self.charts_dir = Path("advanced_charts")
        self.charts_dir.mkdir(exist_ok=True)
        
        # Símbolos disponibles
        self.symbols = {
            'BTC/USD': 'Bitcoin',
            'XAU/USD': 'Gold',
            'EUR/USD': 'Euro Dollar',
            'GBP/USD': 'British Pound',
            'USD/JPY': 'Dollar Yen',
            'ETH/USD': 'Ethereum'
        }
        
        print(f"Advanced Chart Generator iniciado - API Key: OK")
        print(f"Directorio: {self.charts_dir.absolute()}")
    
    def get_market_data(self, symbol, interval="1h", outputsize=100):
        """Obtener datos de mercado formateados para mplfinance"""
        try:
            # Obtener datos
            ts = self.client.time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize,
                timezone="America/New_York"
            )
            
            df = ts.as_pandas()
            
            if df.empty:
                print(f"Sin datos para {symbol}")
                return None
            
            # Formatear para mplfinance (requiere columnas específicas)
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()  # Ordenar cronológicamente
            
            # Limpiar datos
            df = df.dropna()
            df = df[df['Volume'] >= 0]  # Filtrar volúmenes negativos
            
            return df
            
        except Exception as e:
            print(f"Error obteniendo datos para {symbol}: {e}")
            return None
    
    def create_candlestick_chart(self, symbol, interval="1h", periods=50, style='yahoo'):
        """Crear gráfico de velas japonesas profesional"""
        try:
            name = self.symbols.get(symbol, symbol)
            print(f"Creando gráfico de velas japonesas para {name}...")
            
            # Obtener datos
            df = self.get_market_data(symbol, interval, periods)
            if df is None:
                return None
            
            # Configurar estilo
            mc = mpf.make_marketcolors(
                up='g', down='r',           # Verde para subida, rojo para bajada
                edge='inherit',
                wick={'up':'green', 'down':'red'},
                volume='in'
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='gray',
                gridalpha=0.3,
                facecolor='white',
                figcolor='white'
            )
            
            # Crear gráfico
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"candlestick_{symbol.replace('/', '_')}_{timestamp}.png"
            
            mpf.plot(
                df,
                type='candle',
                style=s,
                volume=True,
                title=f'{name} ({symbol}) - Velas Japonesas',
                ylabel='Precio',
                ylabel_lower='Volumen',
                figsize=(14, 10),
                savefig=str(filename)
            )
            
            print(f"Velas japonesas guardadas: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error creando velas japonesas para {symbol}: {e}")
            return None
    
    def create_ohlc_chart(self, symbol, interval="4h", periods=30):
        """Crear gráfico OHLC (Open-High-Low-Close) estilo barras"""
        try:
            name = self.symbols.get(symbol, symbol)
            print(f"Creando gráfico OHLC para {name}...")
            
            # Obtener datos
            df = self.get_market_data(symbol, interval, periods)
            if df is None:
                return None
            
            # Estilo profesional
            mc = mpf.make_marketcolors(
                up='blue', down='red',
                edge='black',
                wick={'up':'blue', 'down':'red'}
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle=':',
                gridcolor='lightgray',
                facecolor='white'
            )
            
            # Crear gráfico OHLC
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"ohlc_{symbol.replace('/', '_')}_{timestamp}.png"
            
            mpf.plot(
                df,
                type='ohlc',  # Tipo barras OHLC
                style=s,
                volume=True,
                title=f'{name} ({symbol}) - Gráfico OHLC',
                ylabel='Precio',
                ylabel_lower='Volumen',
                figsize=(14, 10),
                savefig=str(filename)
            )
            
            print(f"Gráfico OHLC guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error creando OHLC para {symbol}: {e}")
            return None
    
    def create_line_chart(self, symbol, interval="1h", periods=72, price_type='close'):
        """Crear gráfico lineal simple"""
        try:
            name = self.symbols.get(symbol, symbol)
            print(f"Creando gráfico lineal para {name}...")
            
            # Obtener datos
            df = self.get_market_data(symbol, interval, periods)
            if df is None:
                return None
            
            # Crear figura
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Gráfico principal - Línea de precio
            price_data = df[price_type.capitalize()]
            ax1.plot(df.index, price_data, linewidth=2, color='#2E86C1', alpha=0.8)
            ax1.fill_between(df.index, price_data, alpha=0.3, color='#2E86C1')
            
            # Añadir media móvil
            if len(df) >= 20:
                ma20 = price_data.rolling(window=20).mean()
                ax1.plot(df.index, ma20, '--', linewidth=1, color='orange', label='MA20', alpha=0.8)
            
            if len(df) >= 50:
                ma50 = price_data.rolling(window=50).mean()
                ax1.plot(df.index, ma50, '--', linewidth=1, color='red', label='MA50', alpha=0.8)
            
            # Configurar precio
            ax1.set_title(f'{name} ({symbol}) - Gráfico Lineal ({price_type.upper()})', 
                         fontsize=16, fontweight='bold')
            ax1.set_ylabel('Precio', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Gráfico de volumen
            colors = ['green' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else 'red' 
                     for i in range(len(df))]
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.7, width=0.8)
            ax2.set_ylabel('Volumen', fontsize=12)
            ax2.set_xlabel('Tiempo', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Formato de fechas
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"line_{symbol.replace('/', '_')}_{price_type}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Gráfico lineal guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error creando gráfico lineal para {symbol}: {e}")
            return None
    
    def create_bar_chart(self, symbol, interval="1d", periods=30):
        """Crear gráfico de barras de volumen y precio"""
        try:
            name = self.symbols.get(symbol, symbol)
            print(f"Creando gráfico de barras para {name}...")
            
            # Obtener datos
            df = self.get_market_data(symbol, interval, periods)
            if df is None:
                return None
            
            # Crear figura con múltiples subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. Barras de precio de cierre
            colors1 = ['green' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else 'red' 
                      for i in range(len(df))]
            ax1.bar(range(len(df)), df['Close'], color=colors1, alpha=0.7)
            ax1.set_title('Precio de Cierre', fontweight='bold')
            ax1.set_ylabel('Precio')
            ax1.grid(True, alpha=0.3)
            
            # 2. Barras de volumen
            ax2.bar(range(len(df)), df['Volume'], color='blue', alpha=0.6)
            ax2.set_title('Volumen de Transacciones', fontweight='bold')
            ax2.set_ylabel('Volumen')
            ax2.grid(True, alpha=0.3)
            
            # 3. Rango (High - Low)
            price_range = df['High'] - df['Low']
            ax3.bar(range(len(df)), price_range, color='purple', alpha=0.6)
            ax3.set_title('Rango de Precio (High - Low)', fontweight='bold')
            ax3.set_ylabel('Rango')
            ax3.grid(True, alpha=0.3)
            
            # 4. Variación porcentual
            pct_change = ((df['Close'] - df['Open']) / df['Open'] * 100).fillna(0)
            colors4 = ['green' if x >= 0 else 'red' for x in pct_change]
            ax4.bar(range(len(df)), pct_change, color=colors4, alpha=0.7)
            ax4.set_title('Variación % (Close vs Open)', fontweight='bold')
            ax4.set_ylabel('Variación %')
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax4.grid(True, alpha=0.3)
            
            # Configurar etiquetas del eje X para todos los subplots
            for ax in [ax1, ax2, ax3, ax4]:
                ax.set_xlabel('Períodos')
                # Mostrar fechas cada cierto intervalo
                if len(df) <= 30:
                    step = max(1, len(df) // 10)
                    indices = range(0, len(df), step)
                    labels = [df.index[i].strftime('%m-%d') for i in indices]
                    ax.set_xticks(indices)
                    ax.set_xticklabels(labels, rotation=45)
            
            plt.suptitle(f'{name} ({symbol}) - Análisis de Barras', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"bars_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Gráfico de barras guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error creando gráfico de barras para {symbol}: {e}")
            return None
    
    def create_combined_chart(self, symbol, interval="1h", periods=48):
        """Crear gráfico combinado con velas + indicadores"""
        try:
            name = self.symbols.get(symbol, symbol)
            print(f"Creando gráfico combinado para {name}...")
            
            # Obtener datos
            df = self.get_market_data(symbol, interval, periods)
            if df is None:
                return None
            
            # Calcular indicadores
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['RSI'] = self.calculate_rsi(df['Close'])
            
            # Configurar adicionales para mplfinance
            apdict = [
                mpf.make_addplot(df['SMA_20'], color='orange', width=1.5),
                mpf.make_addplot(df['SMA_50'], color='red', width=1.5),
                mpf.make_addplot(df['RSI'], panel=2, color='purple', secondary_y=False)
            ]
            
            # Estilo profesional
            mc = mpf.make_marketcolors(
                up='#26A69A', down='#EF5350',
                edge='black',
                wick={'up':'#26A69A', 'down':'#EF5350'},
                volume='#78909C'
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='gray',
                gridwidth=0.5,
                gridAlpha=0.3,
                facecolor='white'
            )
            
            # Crear gráfico combinado
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"combined_{symbol.replace('/', '_')}_{timestamp}.png"
            
            mpf.plot(
                df,
                type='candle',
                style=s,
                addplot=apdict,
                volume=True,
                panel_ratios=(3, 1, 1),  # Ratios para precio, volumen, RSI
                title=f'{name} ({symbol}) - Análisis Combinado',
                ylabel='Precio',
                ylabel_lower='Volumen | RSI',
                figsize=(16, 12),
                savefig=str(filename)
            )
            
            print(f"Gráfico combinado guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error creando gráfico combinado para {symbol}: {e}")
            return None
    
    def calculate_rsi(self, prices, period=14):
        """Calcular RSI (Relative Strength Index)"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.fillna(50)  # Llenar NaN con 50 (neutral)
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def generate_all_charts(self, symbol='BTC/USD'):
        """Generar todos los tipos de gráficos para un símbolo"""
        print(f"\n{'='*60}")
        print(f" GENERANDO TODOS LOS TIPOS DE GRÁFICOS PARA {symbol}")
        print(f"{'='*60}")
        
        created_charts = []
        
        # 1. Velas japonesas
        candlestick = self.create_candlestick_chart(symbol, "1h", 50)
        if candlestick:
            created_charts.append(candlestick)
        
        # 2. Gráfico OHLC
        ohlc = self.create_ohlc_chart(symbol, "4h", 30)
        if ohlc:
            created_charts.append(ohlc)
        
        # 3. Gráfico lineal
        line_close = self.create_line_chart(symbol, "1h", 72, 'close')
        if line_close:
            created_charts.append(line_close)
        
        # 4. Gráfico de barras
        bars = self.create_bar_chart(symbol, "1d", 20)
        if bars:
            created_charts.append(bars)
        
        # 5. Gráfico combinado
        combined = self.create_combined_chart(symbol, "2h", 36)
        if combined:
            created_charts.append(combined)
        
        return created_charts
    
    def generate_portfolio_charts(self):
        """Generar gráficos para todos los símbolos principales"""
        print(f"\n{'='*70}")
        print(" GENERANDO PORTFOLIO COMPLETO DE GRÁFICOS")
        print(f"{'='*70}")
        
        all_charts = []
        main_symbols = ['BTC/USD', 'XAU/USD', 'EUR/USD']
        
        for symbol in main_symbols:
            symbol_charts = self.generate_all_charts(symbol)
            all_charts.extend(symbol_charts)
        
        return all_charts

def main():
    """Función principal"""
    try:
        generator = AdvancedChartGenerator()
        
        print("ADVANCED CHART GENERATOR")
        print("="*50)
        print("Tipos disponibles:")
        print("1. Velas Japonesas (Candlesticks)")
        print("2. Gráficos OHLC (Barras)")
        print("3. Gráficos Lineales") 
        print("4. Gráficos de Barras")
        print("5. Gráficos Combinados")
        print("6. Portfolio Completo")
        print()
        
        # Generar portfolio completo
        created_charts = generator.generate_portfolio_charts()
        
        print(f"\n{'='*50}")
        print(" RESUMEN DE GRÁFICOS CREADOS")
        print(f"{'='*50}")
        
        if created_charts:
            print(f"Total de gráficos: {len(created_charts)}")
            print(f"Directorio: {generator.charts_dir.absolute()}")
            print("\nArchivos creados:")
            
            chart_types = {}
            for chart_path in created_charts:
                filename = Path(chart_path).name
                chart_type = filename.split('_')[0]
                if chart_type not in chart_types:
                    chart_types[chart_type] = []
                chart_types[chart_type].append(filename)
            
            for chart_type, files in chart_types.items():
                print(f"\n{chart_type.upper()}:")
                for file in files:
                    print(f"  - {file}")
            
            print(f"\n{'='*50}")
            print("INTEGRACIÓN CON ALGOTRADER:")
            print("- Usar en Charts Dashboard (Puerto 8507)")
            print("- Análisis técnico avanzado")
            print("- Validación visual de señales")
            print("- Reportes de trading")
            
        else:
            print("No se pudieron crear gráficos")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()