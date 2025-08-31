"""
Dynamic Charts - Gráficos Dinámicos en Tiempo Real
================================================

Sistema de gráficos que se actualizan automáticamente en tiempo real
"""

import os
import sys
import threading
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

try:
    import mplfinance as mpf
    from twelvedata import TDClient
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

load_dotenv()

class DynamicChartGenerator:
    def __init__(self, update_interval=30):  # Actualizar cada 30 segundos
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("API key no encontrada")
        
        self.client = TDClient(apikey=self.api_key)
        self.charts_dir = Path("advanced_charts")
        self.charts_dir.mkdir(exist_ok=True)
        
        self.update_interval = update_interval
        self.is_running = False
        self.update_thread = None
        
        # Símbolos a monitorear
        self.symbols = ['BTC/USD', 'XAU/USD', 'EUR/USD']
        
        # Estado de los datos
        self.chart_data = {}
        self.last_update = {}
        
        print("Dynamic Chart Generator iniciado")
        print(f"Intervalo de actualización: {update_interval} segundos")
        print(f"Símbolos: {', '.join(self.symbols)}")
    
    def get_realtime_data(self, symbol, interval="1h", outputsize=50):
        """Obtener datos en tiempo real"""
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Actualizando {symbol}...")
            
            ts = self.client.time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )
            
            df = ts.as_pandas()
            
            if df is None or df.empty:
                print(f"  Sin datos para {symbol}")
                return None
            
            # Formatear datos correctamente
            df.columns = ['Open', 'High', 'Low', 'Close']
            df['Volume'] = 1000  # Volumen sintético
            
            # Convertir a numérico
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Limpiar datos
            df = df.dropna()
            df = df[df['High'] >= df['Low']]
            df = df.sort_index()
            
            print(f"  Datos actualizados: {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def create_dynamic_candlestick(self, symbol, df):
        """Crear velas japonesas dinámicas"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"candlestick_{symbol.replace('/', '_')}_live.png"
            
            # Configurar colores dinámicos
            mc = mpf.make_marketcolors(
                up='#00C851', down='#FF4444',
                edge='black',
                wick={'up':'#00C851', 'down':'#FF4444'},
                volume='#33B5E5'
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='lightgray',
                gridAlpha=0.5,
                facecolor='white'
            )
            
            # Título con timestamp
            current_price = df['Close'].iloc[-1]
            price_change = df['Close'].iloc[-1] - df['Close'].iloc[-2] if len(df) > 1 else 0
            change_pct = (price_change / df['Close'].iloc[-2] * 100) if len(df) > 1 and df['Close'].iloc[-2] != 0 else 0
            
            title = f'{symbol} - LIVE Candlesticks | ${current_price:.4f} ({change_pct:+.2f}%) | {timestamp}'
            
            # Crear gráfico
            mpf.plot(
                df.tail(48),  # Últimas 48 velas
                type='candle',
                style=s,
                title=title,
                ylabel='Precio',
                figsize=(14, 8),
                savefig=str(filename)
            )
            
            return str(filename)
            
        except Exception as e:
            print(f"  Error creando candlestick: {e}")
            return None
    
    def create_dynamic_line(self, symbol, df):
        """Crear gráfico lineal dinámico"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"line_{symbol.replace('/', '_')}_live.png"
            
            # Usar datos recientes
            df_recent = df.tail(72)
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Gráfico principal con precio actual destacado
            ax1.plot(df_recent.index, df_recent['Close'], 
                    linewidth=3, color='#2E86C1', label='Precio LIVE', alpha=0.8)
            ax1.fill_between(df_recent.index, df_recent['Close'], alpha=0.2, color='#2E86C1')
            
            # Destacar último punto
            last_price = df_recent['Close'].iloc[-1]
            last_time = df_recent.index[-1]
            ax1.scatter([last_time], [last_price], color='red', s=100, zorder=5, label=f'Actual: ${last_price:.4f}')
            
            # Media móvil dinámica
            if len(df_recent) >= 20:
                ma20 = df_recent['Close'].rolling(window=20).mean()
                ax1.plot(df_recent.index, ma20, '--', linewidth=2, color='orange', 
                        label='MA20', alpha=0.7)
            
            # Título dinámico
            current_time = datetime.now().strftime('%H:%M:%S')
            ax1.set_title(f'{symbol} - LIVE Line Chart | Actualizado: {current_time}', 
                         fontsize=16, fontweight='bold')
            ax1.set_ylabel('Precio', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=10)
            
            # Volatilidad en tiempo real
            volatility = df_recent['High'] - df_recent['Low']
            colors = ['green' if v < volatility.median() else 'orange' if v < volatility.quantile(0.75) else 'red' 
                     for v in volatility]
            ax2.bar(df_recent.index, volatility, color=colors, alpha=0.6)
            ax2.set_ylabel('Volatilidad', fontsize=12)
            ax2.set_xlabel('Tiempo', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Formato de fechas
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(filename)
            
        except Exception as e:
            print(f"  Error creando line chart: {e}")
            return None
    
    def create_dynamic_ohlc(self, symbol, df):
        """Crear gráfico OHLC dinámico"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"ohlc_{symbol.replace('/', '_')}_live.png"
            
            # Configurar estilo OHLC
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
            
            # Título con datos en tiempo real
            current_price = df['Close'].iloc[-1]
            high_24h = df['High'].tail(24).max()
            low_24h = df['Low'].tail(24).min()
            
            title = f'{symbol} - LIVE OHLC Bars | ${current_price:.4f} | H:${high_24h:.4f} L:${low_24h:.4f} | {timestamp}'
            
            mpf.plot(
                df.tail(36),
                type='ohlc',
                style=s,
                title=title,
                ylabel='Precio',
                figsize=(14, 8),
                savefig=str(filename)
            )
            
            return str(filename)
            
        except Exception as e:
            print(f"  Error creando OHLC: {e}")
            return None
    
    def create_dynamic_bars(self, symbol, df):
        """Crear análisis de barras dinámico"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"bars_{symbol.replace('/', '_')}_live.png"
            
            # Usar datos diarios recientes
            df_daily = df.resample('D').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna().tail(15)
            
            if len(df_daily) < 3:
                return None
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. Precio de cierre con tendencia
            colors_close = ['#26A69A' if df_daily.iloc[i]['Close'] >= df_daily.iloc[i]['Open'] else '#EF5350' 
                           for i in range(len(df_daily))]
            bars1 = ax1.bar(range(len(df_daily)), df_daily['Close'], color=colors_close, alpha=0.8)
            ax1.set_title(f'Precio de Cierre LIVE | Actual: ${df_daily["Close"].iloc[-1]:.2f}', 
                         fontsize=14, fontweight='bold')
            ax1.set_ylabel('Precio')
            ax1.grid(True, alpha=0.3)
            
            # 2. Volatilidad diaria
            volatility_daily = df_daily['High'] - df_daily['Low']
            avg_volatility = volatility_daily.mean()
            colors_vol = ['purple' if v <= avg_volatility else 'red' for v in volatility_daily]
            bars2 = ax2.bar(range(len(df_daily)), volatility_daily, color=colors_vol, alpha=0.7)
            ax2.set_title(f'Volatilidad Diaria | Promedio: ${avg_volatility:.2f}', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Rango')
            ax2.axhline(y=avg_volatility, color='black', linestyle='--', alpha=0.5, label='Promedio')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # 3. Cambio porcentual con momentum
            pct_change = ((df_daily['Close'] - df_daily['Open']) / df_daily['Open'] * 100).fillna(0)
            colors_pct = ['#26A69A' if x >= 0 else '#EF5350' for x in pct_change]
            bars3 = ax3.bar(range(len(df_daily)), pct_change, color=colors_pct, alpha=0.8)
            ax3.set_title(f'Cambio % Diario | Hoy: {pct_change.iloc[-1]:.2f}%', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Cambio %')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax3.grid(True, alpha=0.3)
            
            # 4. Strength Index (Close vs High ratio)
            strength = (df_daily['Close'] / df_daily['High'] * 100).fillna(100)
            colors_strength = ['#FFD700' if x >= 95 else '#FFA500' if x >= 90 else '#FF6347' for x in strength]
            bars4 = ax4.bar(range(len(df_daily)), strength, color=colors_strength, alpha=0.7)
            ax4.set_title(f'Strength Index | Actual: {strength.iloc[-1]:.1f}%', fontsize=14, fontweight='bold')
            ax4.set_ylabel('Strength %')
            ax4.axhline(y=100, color='black', linestyle='--', alpha=0.5, label='Máximo')
            ax4.axhline(y=95, color='green', linestyle=':', alpha=0.7, label='Fuerte')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
            
            # Etiquetas de fecha
            date_labels = [df_daily.index[i].strftime('%m-%d') for i in range(len(df_daily))]
            for ax in [ax1, ax2, ax3, ax4]:
                ax.set_xticks(range(len(df_daily)))
                ax.set_xticklabels(date_labels, rotation=45)
                ax.set_xlabel('Fecha')
            
            plt.suptitle(f'{symbol} - LIVE Bar Analysis | {timestamp}', fontsize=18, fontweight='bold')
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(filename)
            
        except Exception as e:
            print(f"  Error creando bars: {e}")
            return None
    
    def update_all_charts(self):
        """Actualizar todos los gráficos dinámicamente"""
        print(f"\n{'='*60}")
        print(f" ACTUALIZACION DINAMICA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        for symbol in self.symbols:
            try:
                # Obtener datos frescos
                df = self.get_realtime_data(symbol, "1h", 100)
                if df is None:
                    continue
                
                # Guardar datos en caché
                self.chart_data[symbol] = df
                self.last_update[symbol] = datetime.now()
                
                # Generar todos los tipos de gráfico
                charts_created = []
                
                # 1. Candlestick
                candle = self.create_dynamic_candlestick(symbol, df)
                if candle:
                    charts_created.append("candlestick")
                
                # 2. Line chart
                line = self.create_dynamic_line(symbol, df)
                if line:
                    charts_created.append("line")
                
                # 3. OHLC
                ohlc = self.create_dynamic_ohlc(symbol, df)
                if ohlc:
                    charts_created.append("ohlc")
                
                # 4. Bar analysis
                bars = self.create_dynamic_bars(symbol, df)
                if bars:
                    charts_created.append("bars")
                
                print(f"  {symbol}: {len(charts_created)} gráficos actualizados ({', '.join(charts_created)})")
                
            except Exception as e:
                print(f"  Error actualizando {symbol}: {e}")
        
        print(f"Próxima actualización en {self.update_interval} segundos...")
    
    def start_dynamic_updates(self):
        """Iniciar actualizaciones dinámicas en hilo separado"""
        if self.is_running:
            print("Sistema ya está ejecutándose")
            return
        
        self.is_running = True
        
        def update_loop():
            while self.is_running:
                try:
                    self.update_all_charts()
                    time.sleep(self.update_interval)
                except Exception as e:
                    print(f"Error en loop de actualización: {e}")
                    time.sleep(5)  # Esperar antes de reintentar
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        
        print(f"Sistema de gráficos dinámicos iniciado")
        print(f"Actualizando cada {self.update_interval} segundos")
        print("Presiona Ctrl+C para detener")
    
    def stop_dynamic_updates(self):
        """Detener actualizaciones dinámicas"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        print("Sistema de gráficos dinámicos detenido")
    
    def get_system_status(self):
        """Obtener estado del sistema"""
        status = {
            'running': self.is_running,
            'update_interval': self.update_interval,
            'symbols': self.symbols,
            'last_updates': {},
            'charts_directory': str(self.charts_dir.absolute())
        }
        
        for symbol in self.symbols:
            if symbol in self.last_update:
                status['last_updates'][symbol] = self.last_update[symbol].strftime('%Y-%m-%d %H:%M:%S')
            else:
                status['last_updates'][symbol] = "Nunca"
        
        return status

def main():
    try:
        # Crear generador dinámico
        generator = DynamicChartGenerator(update_interval=30)  # 30 segundos
        
        print("DYNAMIC CHART GENERATOR")
        print("="*60)
        print("Características:")
        print("  • Actualización automática cada 30 segundos")
        print("  • Gráficos en tiempo real con datos LIVE")
        print("  • 4 tipos: Candlestick, Line, OHLC, Bar Analysis")
        print("  • Integración con Charts Dashboard")
        print("="*60)
        
        # Hacer actualización inicial
        generator.update_all_charts()
        
        # Iniciar sistema dinámico
        generator.start_dynamic_updates()
        
        # Mantener funcionando
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDeteniendo sistema...")
            generator.stop_dynamic_updates()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()