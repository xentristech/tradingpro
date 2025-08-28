"""
Simple Visual Charts - Graficos Simples y Funcionales
=====================================================

Version simplificada que funciona en Windows sin problemas de encoding
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    from twelvedata import TDClient
except ImportError:
    print("ERROR: Instalar twelvedata con: pip install twelvedata")
    exit(1)

load_dotenv()

class SimpleVisualCharts:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("API key no encontrada")
        
        self.client = TDClient(apikey=self.api_key)
        self.charts_dir = Path("advanced_charts")
        self.charts_dir.mkdir(exist_ok=True)
        
        print("Simple Visual Charts iniciado")
        print(f"Directorio: {self.charts_dir}")
    
    def get_data(self, symbol, interval="1h", outputsize=50):
        """Obtener datos de mercado"""
        try:
            print(f"Obteniendo datos para {symbol}...")
            
            ts = self.client.time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )
            
            df = ts.as_pandas()
            
            if df is None or df.empty:
                print(f"Sin datos para {symbol}")
                return None
            
            # Asegurar nombres en mayúsculas
            df.columns = ['Open', 'High', 'Low', 'Close']
            
            # Convertir a numérico
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Limpiar datos
            df = df.dropna()
            df = df.sort_index()
            
            print(f"Datos obtenidos: {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_candlestick_manual(self, symbol):
        """Crear velas japonesas manualmente con matplotlib"""
        try:
            print(f"Creando velas japonesas para {symbol}...")
            
            df = self.get_data(symbol, "1h", 48)
            if df is None:
                return None
            
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Crear velas japonesas manualmente
            for i, (idx, row) in enumerate(df.iterrows()):
                # Color de la vela
                color = 'green' if row['Close'] >= row['Open'] else 'red'
                
                # Línea de sombra (wick)
                ax.plot([i, i], [row['Low'], row['High']], 
                       color='black', linewidth=1, alpha=0.7)
                
                # Cuerpo de la vela
                body_height = abs(row['Close'] - row['Open'])
                body_bottom = min(row['Open'], row['Close'])
                
                rect = plt.Rectangle((i-0.3, body_bottom), 0.6, body_height,
                                   facecolor=color, alpha=0.8, edgecolor='black')
                ax.add_patch(rect)
            
            # Configurar gráfico
            ax.set_title(f'{symbol} - Velas Japonesas', fontsize=16, fontweight='bold')
            ax.set_ylabel('Precio', fontsize=12)
            ax.set_xlabel('Periodo', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Etiquetas del eje X (cada 8 períodos)
            step = max(1, len(df) // 8)
            indices = list(range(0, len(df), step))
            labels = [df.index[i].strftime('%m-%d %H:%M') for i in indices if i < len(df)]
            ax.set_xticks(indices[:len(labels)])
            ax.set_xticklabels(labels, rotation=45)
            
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"candlestick_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_ohlc_bars(self, symbol):
        """Crear gráfico OHLC con barras manuales"""
        try:
            print(f"Creando OHLC para {symbol}...")
            
            df = self.get_data(symbol, "2h", 36)
            if df is None:
                return None
            
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Crear barras OHLC manualmente
            for i, (idx, row) in enumerate(df.iterrows()):
                # Color según dirección
                color = 'darkgreen' if row['Close'] >= row['Open'] else 'darkred'
                
                # Línea principal (High-Low)
                ax.plot([i, i], [row['Low'], row['High']], 
                       color=color, linewidth=2)
                
                # Marcas de Open y Close
                ax.plot([i-0.2, i], [row['Open'], row['Open']], 
                       color=color, linewidth=2)
                ax.plot([i, i+0.2], [row['Close'], row['Close']], 
                       color=color, linewidth=2)
            
            ax.set_title(f'{symbol} - Grafico OHLC (Barras)', fontsize=16, fontweight='bold')
            ax.set_ylabel('Precio', fontsize=12)
            ax.set_xlabel('Periodo', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Etiquetas X
            step = max(1, len(df) // 8)
            indices = list(range(0, len(df), step))
            labels = [df.index[i].strftime('%m-%d %H:%M') for i in indices if i < len(df)]
            ax.set_xticks(indices[:len(labels)])
            ax.set_xticklabels(labels, rotation=45)
            
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"ohlc_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_line_chart(self, symbol):
        """Crear gráfico lineal simple"""
        try:
            print(f"Creando grafico lineal para {symbol}...")
            
            df = self.get_data(symbol, "1h", 72)
            if df is None:
                return None
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Gráfico principal
            ax1.plot(df['Close'], linewidth=2.5, color='blue', label='Precio de Cierre')
            ax1.fill_between(df.index, df['Close'], alpha=0.3, color='blue')
            
            # Media móvil si hay datos suficientes
            if len(df) >= 20:
                ma20 = df['Close'].rolling(20).mean()
                ax1.plot(ma20, '--', linewidth=2, color='orange', label='MA20')
            
            ax1.set_title(f'{symbol} - Grafico Lineal', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Precio', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Gráfico de volatilidad (rango High-Low)
            volatility = df['High'] - df['Low']
            ax2.bar(range(len(df)), volatility, alpha=0.6, color='purple')
            ax2.set_ylabel('Volatilidad', fontsize=12)
            ax2.set_xlabel('Periodo', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Etiquetas X para ambos gráficos
            step = max(1, len(df) // 8)
            indices = list(range(0, len(df), step))
            labels = [df.index[i].strftime('%m-%d %H:%M') for i in indices if i < len(df)]
            
            for ax in [ax1, ax2]:
                ax.set_xticks(indices[:len(labels)])
                ax.set_xticklabels(labels, rotation=45)
            
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"line_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_bar_analysis(self, symbol):
        """Crear análisis con barras múltiples"""
        try:
            print(f"Creando analisis de barras para {symbol}...")
            
            df = self.get_data(symbol, "1day", 15)
            if df is None:
                return None
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. Precios de cierre
            colors1 = ['green' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else 'red' 
                      for i in range(len(df))]
            ax1.bar(range(len(df)), df['Close'], color=colors1, alpha=0.8)
            ax1.set_title('Precios de Cierre', fontweight='bold')
            ax1.set_ylabel('Precio')
            ax1.grid(True, alpha=0.3)
            
            # 2. Rangos de precio (High-Low)
            price_range = df['High'] - df['Low']
            ax2.bar(range(len(df)), price_range, color='purple', alpha=0.7)
            ax2.set_title('Rango de Precios (High-Low)', fontweight='bold')
            ax2.set_ylabel('Rango')
            ax2.grid(True, alpha=0.3)
            
            # 3. Variación porcentual
            pct_change = ((df['Close'] - df['Open']) / df['Open'] * 100).fillna(0)
            colors3 = ['green' if x >= 0 else 'red' for x in pct_change]
            ax3.bar(range(len(df)), pct_change, color=colors3, alpha=0.8)
            ax3.set_title('Variacion % (Close vs Open)', fontweight='bold')
            ax3.set_ylabel('Variacion %')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax3.grid(True, alpha=0.3)
            
            # 4. Momentum (Close/High ratio)
            momentum = (df['Close'] / df['High'] * 100).fillna(100)
            colors4 = ['gold' if x >= 95 else 'orange' if x >= 90 else 'red' for x in momentum]
            ax4.bar(range(len(df)), momentum, color=colors4, alpha=0.7)
            ax4.set_title('Momentum (Close/High %)', fontweight='bold')
            ax4.set_ylabel('Momentum %')
            ax4.axhline(y=100, color='black', linestyle='--', alpha=0.5)
            ax4.grid(True, alpha=0.3)
            
            # Etiquetas para todos
            date_labels = [df.index[i].strftime('%m-%d') for i in range(len(df))]
            for ax in [ax1, ax2, ax3, ax4]:
                ax.set_xticks(range(len(df)))
                ax.set_xticklabels(date_labels, rotation=45)
                ax.set_xlabel('Fecha')
            
            plt.suptitle(f'{symbol} - Analisis Completo de Barras', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"bars_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Guardado: {filename.name}")
            return str(filename)
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def generate_all_charts(self, symbol):
        """Generar todos los tipos de gráficos"""
        print(f"\n{'-'*50}")
        print(f" GENERANDO GRAFICOS PARA {symbol}")
        print(f"{'-'*50}")
        
        charts = []
        
        # 1. Velas japonesas
        candle = self.create_candlestick_manual(symbol)
        if candle:
            charts.append(candle)
        
        # 2. OHLC
        ohlc = self.create_ohlc_bars(symbol)
        if ohlc:
            charts.append(ohlc)
        
        # 3. Lineal
        line = self.create_line_chart(symbol)
        if line:
            charts.append(line)
        
        # 4. Barras
        bars = self.create_bar_analysis(symbol)
        if bars:
            charts.append(bars)
        
        print(f"Completado: {len(charts)} graficos para {symbol}")
        return charts
    
    def run_complete_generation(self):
        """Ejecutar generación completa"""
        print("SIMPLE VISUAL CHARTS")
        print("="*50)
        print("Tipos de graficos:")
        print("- Velas Japonesas (Candlesticks)")
        print("- OHLC (Barras)")
        print("- Lineales") 
        print("- Analisis de Barras")
        print("="*50)
        
        symbols = ['BTC/USD', 'XAU/USD', 'EUR/USD']
        all_charts = []
        
        for symbol in symbols:
            symbol_charts = self.generate_all_charts(symbol)
            all_charts.extend(symbol_charts)
        
        return all_charts

def main():
    try:
        generator = SimpleVisualCharts()
        created_charts = generator.run_complete_generation()
        
        print(f"\n{'='*50}")
        print(" RESULTADO FINAL")
        print(f"{'='*50}")
        
        if created_charts:
            print(f"Total graficos creados: {len(created_charts)}")
            print(f"Ubicacion: {generator.charts_dir}")
            
            # Contar por tipo
            types = {}
            for chart in created_charts:
                chart_type = Path(chart).name.split('_')[0]
                types[chart_type] = types.get(chart_type, 0) + 1
            
            print("\nPor tipo:")
            for chart_type, count in types.items():
                print(f"  {chart_type}: {count}")
            
            print("\nIntegracion:")
            print("- Charts Dashboard (Puerto 8507)")
            print("- Sistema AlgoTrader")
            
        else:
            print("No se crearon graficos")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()