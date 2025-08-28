"""
Fixed Advanced Charts - Gráficos Corregidos
===========================================

Versión corregida para gráficos de velas, barras y lineales
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

class FixedChartGenerator:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("API key no encontrada")
        
        self.client = TDClient(apikey=self.api_key)
        self.charts_dir = Path("advanced_charts")
        self.charts_dir.mkdir(exist_ok=True)
        
        print("Fixed Chart Generator iniciado")
    
    def get_clean_data(self, symbol, interval="1h", outputsize=50):
        """Obtener y limpiar datos correctamente"""
        try:
            print(f"  Obteniendo datos para {symbol}...")
            
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
            
            # Renombrar columnas para mplfinance
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # Asegurar tipos correctos
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)
            
            # Limpiar datos
            df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
            df = df[df['High'] >= df['Low']]  # Validación básica
            df = df.sort_index()
            
            print(f"  Datos obtenidos: {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"  Error obteniendo datos: {e}")
            return None
    
    def create_candlestick_simple(self, symbol):
        """Crear velas japonesas usando mplfinance"""
        try:
            print(f"Creando velas japonesas para {symbol}...")
            
            df = self.get_clean_data(symbol, "1h", 48)
            if df is None:
                return None
            
            # Configurar colores
            mc = mpf.make_marketcolors(
                up='green', down='red',
                edge='black',
                wick={'up':'green', 'down':'red'},
                volume='blue'
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='lightgray'
            )
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"candlestick_{symbol.replace('/', '_')}_{timestamp}.png"
            
            # Crear gráfico
            mpf.plot(
                df,
                type='candle',
                style=s,
                volume=True,
                title=f'{symbol} - Velas Japonesas',
                figsize=(12, 8),
                savefig=str(filename)
            )
            
            print(f"  Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def create_line_simple(self, symbol):
        """Crear gráfico lineal simple"""
        try:
            print(f"Creando gráfico lineal para {symbol}...")
            
            df = self.get_clean_data(symbol, "1h", 72)
            if df is None:
                return None
            
            # Crear figura
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Línea de precio
            ax1.plot(df.index, df['Close'], linewidth=2, color='blue', label='Precio')
            ax1.fill_between(df.index, df['Close'], alpha=0.3, color='blue')
            
            # Media móvil simple si hay suficientes datos
            if len(df) >= 20:
                ma20 = df['Close'].rolling(20).mean()
                ax1.plot(df.index, ma20, '--', color='orange', label='MA20')
            
            ax1.set_title(f'{symbol} - Gráfico Lineal', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Precio')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Volumen
            ax2.bar(df.index, df['Volume'], color='gray', alpha=0.6)
            ax2.set_ylabel('Volumen')
            ax2.set_xlabel('Tiempo')
            ax2.grid(True, alpha=0.3)
            
            # Formato fechas
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"line_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def create_ohlc_bars(self, symbol):
        """Crear gráfico OHLC con barras"""
        try:
            print(f"Creando gráfico OHLC para {symbol}...")
            
            df = self.get_clean_data(symbol, "4h", 36)
            if df is None:
                return None
            
            # Estilo OHLC
            mc = mpf.make_marketcolors(
                up='darkgreen', down='darkred',
                edge='black',
                wick='black'
            )
            
            s = mpf.make_mpf_style(marketcolors=mc)
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"ohlc_{symbol.replace('/', '_')}_{timestamp}.png"
            
            mpf.plot(
                df,
                type='ohlc',
                style=s,
                volume=True,
                title=f'{symbol} - Gráfico OHLC',
                figsize=(12, 8),
                savefig=str(filename)
            )
            
            print(f"  Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def create_bar_analysis(self, symbol):
        """Crear análisis con barras múltiples"""
        try:
            print(f"Creando gráfico de barras para {symbol}...")
            
            df = self.get_clean_data(symbol, "1day", 20)  # Usar 1day en lugar de 1d
            if df is None:
                return None
            
            # Crear figura
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            
            # 1. Precio de cierre
            colors_close = ['green' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else 'red' 
                           for i in range(len(df))]
            ax1.bar(range(len(df)), df['Close'], color=colors_close, alpha=0.7)
            ax1.set_title('Precio de Cierre')
            ax1.set_ylabel('Precio')
            ax1.grid(True, alpha=0.3)
            
            # 2. Volumen
            ax2.bar(range(len(df)), df['Volume'], color='blue', alpha=0.6)
            ax2.set_title('Volumen')
            ax2.set_ylabel('Volumen')
            ax2.grid(True, alpha=0.3)
            
            # 3. Rango (High-Low)
            price_range = df['High'] - df['Low']
            ax3.bar(range(len(df)), price_range, color='purple', alpha=0.6)
            ax3.set_title('Rango de Precio')
            ax3.set_ylabel('Rango')
            ax3.grid(True, alpha=0.3)
            
            # 4. Cambio porcentual
            pct_change = ((df['Close'] - df['Open']) / df['Open'] * 100).fillna(0)
            colors_pct = ['green' if x >= 0 else 'red' for x in pct_change]
            ax4.bar(range(len(df)), pct_change, color=colors_pct, alpha=0.7)
            ax4.set_title('Cambio % (Close vs Open)')
            ax4.set_ylabel('Cambio %')
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax4.grid(True, alpha=0.3)
            
            # Etiquetas del eje X
            for ax in [ax1, ax2, ax3, ax4]:
                if len(df) <= 20:
                    step = max(1, len(df) // 8)
                    indices = range(0, len(df), step)
                    labels = [df.index[i].strftime('%m-%d') for i in indices if i < len(df)]
                    ax.set_xticks(indices[:len(labels)])
                    ax.set_xticklabels(labels, rotation=45)
            
            plt.suptitle(f'{symbol} - Análisis de Barras', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"bars_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def generate_all_for_symbol(self, symbol):
        """Generar todos los tipos para un símbolo"""
        print(f"\n{'-'*50}")
        print(f" {symbol}")
        print(f"{'-'*50}")
        
        charts = []
        
        # 1. Velas japonesas
        candle = self.create_candlestick_simple(symbol)
        if candle:
            charts.append(candle)
        
        # 2. Gráfico lineal
        line = self.create_line_simple(symbol)
        if line:
            charts.append(line)
        
        # 3. OHLC
        ohlc = self.create_ohlc_bars(symbol)
        if ohlc:
            charts.append(ohlc)
        
        # 4. Barras de análisis
        bars = self.create_bar_analysis(symbol)
        if bars:
            charts.append(bars)
        
        return charts
    
    def generate_complete_portfolio(self):
        """Generar portfolio completo"""
        print("FIXED CHART GENERATOR")
        print("="*50)
        print("Generando gráficos avanzados...")
        
        symbols = ['BTC/USD', 'XAU/USD']
        all_charts = []
        
        for symbol in symbols:
            symbol_charts = self.generate_all_for_symbol(symbol)
            all_charts.extend(symbol_charts)
        
        return all_charts

def main():
    try:
        generator = FixedChartGenerator()
        created_charts = generator.generate_complete_portfolio()
        
        print(f"\n{'='*50}")
        print(" RESULTADOS")
        print(f"{'='*50}")
        
        if created_charts:
            print(f"Gráficos creados: {len(created_charts)}")
            print(f"Ubicación: {generator.charts_dir}")
            
            types = {}
            for chart in created_charts:
                chart_type = Path(chart).name.split('_')[0]
                if chart_type not in types:
                    types[chart_type] = 0
                types[chart_type] += 1
            
            print("\nPor tipo:")
            for chart_type, count in types.items():
                print(f"  {chart_type}: {count}")
            
            print("\nTipos implementados:")
            print("  • candlestick: Velas japonesas")
            print("  • line: Gráficos lineales")
            print("  • ohlc: Barras OHLC")
            print("  • bars: Análisis de barras")
        else:
            print("No se crearon gráficos")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()