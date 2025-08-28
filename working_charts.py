"""
Working Charts - Gráficos de Velas, Barras y Lineales
=====================================================

Versión funcional que maneja correctamente los datos de TwelveData
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    import mplfinance as mpf
    from twelvedata import TDClient
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

load_dotenv()

class WorkingChartGenerator:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("API key no encontrada")
        
        self.client = TDClient(apikey=self.api_key)
        self.charts_dir = Path("advanced_charts")
        self.charts_dir.mkdir(exist_ok=True)
        
        print(f"Working Chart Generator iniciado")
        print(f"Directorio: {self.charts_dir.absolute()}")
    
    def get_market_data(self, symbol, interval="1h", outputsize=50):
        """Obtener datos de mercado correctamente formateados"""
        try:
            print(f"  Obteniendo datos de {symbol}...")
            
            # Obtener datos básicos
            ts = self.client.time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )
            
            df = ts.as_pandas()
            
            if df is None or df.empty:
                print(f"  Sin datos para {symbol}")
                return None
            
            # Renombrar columnas correctamente (sin volumen)
            df.columns = ['Open', 'High', 'Low', 'Close']
            
            # Agregar volumen sintético para mplfinance
            df['Volume'] = 1000  # Volumen constante sintético
            
            # Asegurar tipos numéricos
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Limpiar datos
            df = df.dropna()
            df = df[df['High'] >= df['Low']]
            df = df.sort_index()
            
            print(f"  Datos procesados: {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"  Error obteniendo datos: {e}")
            return None
    
    def create_candlestick_chart(self, symbol):
        """Crear gráfico de velas japonesas"""
        try:
            print(f"Creando velas japonesas para {symbol}...")
            
            df = self.get_market_data(symbol, "1h", 48)
            if df is None:
                return None
            
            # Configurar estilo
            mc = mpf.make_marketcolors(
                up='#26A69A', down='#EF5350',  # Verde y rojo moderno
                edge='black',
                wick={'up':'#26A69A', 'down':'#EF5350'},
                volume='#78909C'
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='lightgray',
                gridAlpha=0.5,
                facecolor='white'
            )
            
            # Crear y guardar gráfico
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"candlestick_{symbol.replace('/', '_')}_{timestamp}.png"
            
            mpf.plot(
                df,
                type='candle',
                style=s,
                title=f'{symbol} - Velas Japonesas (Candlesticks)',
                ylabel='Precio',
                figsize=(14, 8),
                savefig=str(filename)
            )
            
            print(f"  ✓ Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def create_ohlc_chart(self, symbol):
        """Crear gráfico OHLC (barras)"""
        try:
            print(f"Creando gráfico OHLC (barras) para {symbol}...")
            
            df = self.get_market_data(symbol, "2h", 36)
            if df is None:
                return None
            
            # Estilo OHLC
            mc = mpf.make_marketcolors(
                up='darkgreen', down='darkred',
                edge='black',
                wick='black'
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle=':',
                gridcolor='gray'
            )
            
            # Crear y guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"ohlc_{symbol.replace('/', '_')}_{timestamp}.png"
            
            mpf.plot(
                df,
                type='ohlc',
                style=s,
                title=f'{symbol} - Gráfico OHLC (Barras)',
                ylabel='Precio',
                figsize=(14, 8),
                savefig=str(filename)
            )
            
            print(f"  ✓ Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def create_line_chart(self, symbol):
        """Crear gráfico lineal con matplotlib"""
        try:
            print(f"Creando gráfico lineal para {symbol}...")
            
            df = self.get_market_data(symbol, "1h", 72)
            if df is None:
                return None
            
            # Crear figura con subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Gráfico principal - Línea de precio
            ax1.plot(df.index, df['Close'], linewidth=2.5, color='#2E86C1', label='Precio de Cierre')
            ax1.fill_between(df.index, df['Close'], alpha=0.3, color='#2E86C1')
            
            # Añadir medias móviles si hay suficientes datos
            if len(df) >= 20:
                ma20 = df['Close'].rolling(window=20).mean()
                ax1.plot(df.index, ma20, '--', linewidth=2, color='orange', 
                        label='Media Móvil 20', alpha=0.8)
            
            if len(df) >= 50:
                ma50 = df['Close'].rolling(window=50).mean()
                ax1.plot(df.index, ma50, '--', linewidth=2, color='red', 
                        label='Media Móvil 50', alpha=0.8)
            
            # Configurar primer subplot
            ax1.set_title(f'{symbol} - Gráfico Lineal', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Precio', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=10)
            
            # Segundo subplot - Indicador de volatilidad (rango High-Low)
            volatility = df['High'] - df['Low']
            ax2.bar(df.index, volatility, alpha=0.6, color='purple', 
                   label='Volatilidad (High-Low)')
            ax2.set_ylabel('Volatilidad', fontsize=12)
            ax2.set_xlabel('Tiempo', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.legend(fontsize=10)
            
            # Formato de fechas
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"line_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  ✓ Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def create_bar_analysis(self, symbol):
        """Crear análisis con gráficos de barras"""
        try:
            print(f"Creando análisis de barras para {symbol}...")
            
            df = self.get_market_data(symbol, "1day", 15)
            if df is None:
                return None
            
            # Crear figura con 4 subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. Barras de precio de cierre
            colors_close = ['#26A69A' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else '#EF5350' 
                           for i in range(len(df))]
            bars1 = ax1.bar(range(len(df)), df['Close'], color=colors_close, alpha=0.8)
            ax1.set_title('Precio de Cierre', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Precio')
            ax1.grid(True, alpha=0.3)
            
            # Añadir valores en las barras
            for i, bar in enumerate(bars1):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'${height:.0f}', ha='center', va='bottom', fontsize=8)
            
            # 2. Rango de precio (High - Low)
            price_range = df['High'] - df['Low']
            bars2 = ax2.bar(range(len(df)), price_range, color='purple', alpha=0.7)
            ax2.set_title('Rango de Precio (High - Low)', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Rango')
            ax2.grid(True, alpha=0.3)
            
            # 3. Variación porcentual diaria
            pct_change = ((df['Close'] - df['Open']) / df['Open'] * 100).fillna(0)
            colors_pct = ['#26A69A' if x >= 0 else '#EF5350' for x in pct_change]
            bars3 = ax3.bar(range(len(df)), pct_change, color=colors_pct, alpha=0.8)
            ax3.set_title('Variación % Diaria (Close vs Open)', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Variación %')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax3.grid(True, alpha=0.3)
            
            # 4. Análisis de momentum (Close vs High)
            momentum = (df['Close'] / df['High'] * 100).fillna(100)
            colors_momentum = ['#FFD700' if x >= 95 else '#FFA500' if x >= 90 else '#FF6347' 
                              for x in momentum]
            bars4 = ax4.bar(range(len(df)), momentum, color=colors_momentum, alpha=0.7)
            ax4.set_title('Momentum (Close/High %)', fontsize=14, fontweight='bold')
            ax4.set_ylabel('Momentum %')
            ax4.axhline(y=100, color='black', linestyle='--', alpha=0.5, label='Máximo')
            ax4.axhline(y=95, color='green', linestyle=':', alpha=0.7, label='Fuerte')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            # Configurar etiquetas del eje X para todos los subplots
            date_labels = [df.index[i].strftime('%m-%d') for i in range(len(df))]
            
            for ax in [ax1, ax2, ax3, ax4]:
                ax.set_xticks(range(len(df)))
                ax.set_xticklabels(date_labels, rotation=45)
                ax.set_xlabel('Fecha')
            
            plt.suptitle(f'{symbol} - Análisis Completo de Barras', fontsize=18, fontweight='bold')
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"bars_analysis_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  ✓ Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def generate_complete_set(self, symbol):
        """Generar conjunto completo de gráficos para un símbolo"""
        print(f"\n{'='*60}")
        print(f" GENERANDO GRÁFICOS COMPLETOS PARA {symbol}")
        print(f"{'='*60}")
        
        charts = []
        
        # 1. Velas japonesas
        candle = self.create_candlestick_chart(symbol)
        if candle:
            charts.append(candle)
        
        # 2. OHLC (barras)
        ohlc = self.create_ohlc_chart(symbol)
        if ohlc:
            charts.append(ohlc)
        
        # 3. Gráfico lineal
        line = self.create_line_chart(symbol)
        if line:
            charts.append(line)
        
        # 4. Análisis de barras
        bars = self.create_bar_analysis(symbol)
        if bars:
            charts.append(bars)
        
        print(f"Completado {symbol}: {len(charts)} gráficos creados")
        return charts
    
    def generate_portfolio(self):
        """Generar portfolio completo"""
        print("WORKING CHART GENERATOR")
        print("="*60)
        print("Tipos de gráficos:")
        print("  • Velas Japonesas (Candlesticks)")
        print("  • OHLC (Barras Open-High-Low-Close)")
        print("  • Lineales (con medias móviles)")
        print("  • Análisis de Barras (múltiples métricas)")
        print("="*60)
        
        symbols = ['BTC/USD', 'XAU/USD', 'EUR/USD']
        all_charts = []
        
        for symbol in symbols:
            symbol_charts = self.generate_complete_set(symbol)
            all_charts.extend(symbol_charts)
        
        return all_charts

def main():
    try:
        generator = WorkingChartGenerator()
        created_charts = generator.generate_portfolio()
        
        print(f"\n{'='*60}")
        print(" RESUMEN FINAL")
        print(f"{'='*60}")
        
        if created_charts:
            print(f"✅ Total de gráficos creados: {len(created_charts)}")
            print(f"📁 Ubicación: {generator.charts_dir}")
            
            # Contar por tipo
            chart_types = {}
            for chart_path in created_charts:
                filename = Path(chart_path).name
                chart_type = filename.split('_')[0]
                if chart_type not in chart_types:
                    chart_types[chart_type] = 0
                chart_types[chart_type] += 1
            
            print("\n📊 Gráficos por tipo:")
            type_names = {
                'candlestick': 'Velas Japonesas',
                'ohlc': 'Barras OHLC',
                'line': 'Lineales',
                'bars': 'Análisis de Barras'
            }
            
            for chart_type, count in chart_types.items():
                type_name = type_names.get(chart_type, chart_type)
                print(f"  • {type_name}: {count}")
            
            print("\n🔗 Integración:")
            print("  • Charts Dashboard (Puerto 8507)")
            print("  • AI Dashboard para análisis")
            print("  • Trade Validator para confirmación visual")
            
        else:
            print("❌ No se crearon gráficos")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()