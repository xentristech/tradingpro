"""
Chart Generator for AlgoTrader System
====================================

Sistema integrado de generación de gráficas para el AlgoTrader MVP v3
Utiliza TwelveData API para crear visualizaciones de trading
"""

import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()

# Importar TwelveData
try:
    from twelvedata import TDClient
except ImportError:
    print("ERROR: twelvedata no instalado")
    print("Instalar con: pip install twelvedata[pandas,matplotlib]")
    sys.exit(1)

class AlgoTraderChartGenerator:
    def __init__(self):
        """Inicializar generador de gráficas"""
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY no encontrada en variables de entorno")
        
        self.client = TDClient(apikey=self.api_key)
        self.charts_dir = Path("charts")
        self.charts_dir.mkdir(exist_ok=True)
        
        # Símbolos del sistema AlgoTrader
        self.symbols = {
            'BTC/USD': 'Bitcoin',
            'XAU/USD': 'Gold', 
            'EUR/USD': 'Euro Dollar',
            'GBP/USD': 'British Pound',
            'USD/JPY': 'Dollar Yen'
        }
        
        print(f"Chart Generator iniciado - API Key: {self.api_key[:8]}...")
    
    def create_trading_chart(self, symbol, hours=48, include_indicators=True):
        """Crear gráfica de trading con análisis técnico"""
        try:
            name = self.symbols.get(symbol, symbol)
            print(f"Creando gráfica de trading para {name}...")
            
            # Obtener datos de precio
            ts = self.client.time_series(
                symbol=symbol,
                interval="1h",
                outputsize=hours
            )
            
            df = ts.as_pandas()
            if df.empty:
                print(f"Sin datos para {symbol}")
                return None
            
            # Configurar figura
            if include_indicators:
                fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), 
                                                   gridspec_kw={'height_ratios': [3, 1, 1]})
            else:
                fig, ax1 = plt.subplots(figsize=(14, 8))
            
            # Gráfica principal de precios
            ax1.plot(df.index, df['close'], linewidth=2, label='Close', color='blue')
            ax1.fill_between(df.index, df['low'], df['high'], alpha=0.2, color='gray')
            
            # Líneas de soporte/resistencia básicas
            recent_high = df['high'].tail(24).max()
            recent_low = df['low'].tail(24).min()
            ax1.axhline(y=recent_high, color='red', linestyle='--', alpha=0.7, label='24h High')
            ax1.axhline(y=recent_low, color='green', linestyle='--', alpha=0.7, label='24h Low')
            
            ax1.set_title(f'{name} ({symbol}) - Trading Analysis', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Price', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            if include_indicators:
                try:
                    # RSI
                    rsi_data = self.client.technical_indicator(
                        symbol=symbol,
                        indicator="RSI",
                        interval="1h",
                        outputsize=hours//2
                    )
                    rsi_df = rsi_data.as_pandas()
                    
                    if not rsi_df.empty:
                        ax2.plot(rsi_df.index, rsi_df['rsi'], color='purple', linewidth=2)
                        ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                        ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                        ax2.fill_between(rsi_df.index, 30, 70, alpha=0.1, color='gray')
                        ax2.set_ylabel('RSI', fontsize=10)
                        ax2.set_title('RSI (14)', fontsize=12)
                        ax2.grid(True, alpha=0.3)
                        ax2.set_ylim(0, 100)
                    
                    # MACD
                    macd_data = self.client.technical_indicator(
                        symbol=symbol,
                        indicator="MACD",
                        interval="1h",
                        outputsize=hours//2
                    )
                    macd_df = macd_data.as_pandas()
                    
                    if not macd_df.empty:
                        ax3.plot(macd_df.index, macd_df['macd'], label='MACD', linewidth=2)
                        ax3.plot(macd_df.index, macd_df['macd_signal'], label='Signal', linewidth=2)
                        ax3.bar(macd_df.index, macd_df['macd_hist'], label='Histogram', alpha=0.6)
                        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                        ax3.set_ylabel('MACD', fontsize=10)
                        ax3.set_xlabel('Time', fontsize=10)
                        ax3.set_title('MACD', fontsize=12)
                        ax3.legend(fontsize=8)
                        ax3.grid(True, alpha=0.3)
                
                except Exception as e:
                    print(f"Error obteniendo indicadores: {e}")
            
            # Ajustar fechas
            if include_indicators:
                plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            else:
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Guardar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"trading_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Gráfica guardada: {filename}")
            return str(filename)
            
        except Exception as e:
            print(f"Error creando gráfica para {symbol}: {e}")
            return None
    
    def create_dashboard_chart(self, symbol, timeframe="1h", periods=24):
        """Crear gráfica optimizada para dashboards"""
        try:
            name = self.symbols.get(symbol, symbol)
            
            # Obtener datos
            ts = self.client.time_series(
                symbol=symbol,
                interval=timeframe,
                outputsize=periods
            )
            
            df = ts.as_pandas()
            if df.empty:
                return None
            
            # Crear gráfica compacta
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Línea de precio principal
            ax.plot(df.index, df['close'], linewidth=3, color='#2E86C1', label='Price')
            
            # Área de precio
            ax.fill_between(df.index, df['close'], alpha=0.3, color='#2E86C1')
            
            # Información de precio actual
            current_price = df['close'].iloc[0]
            price_change = df['close'].iloc[0] - df['close'].iloc[-1]
            pct_change = (price_change / df['close'].iloc[-1]) * 100
            
            # Color según cambio
            color = '#27AE60' if price_change >= 0 else '#E74C3C'
            
            # Título con información actual
            title = f'{name}\n${current_price:,.2f} ({pct_change:+.2f}%)'
            ax.set_title(title, fontsize=14, fontweight='bold', color=color)
            
            # Configuración mínima
            ax.set_ylabel('Price', fontsize=10)
            ax.grid(True, alpha=0.2)
            ax.tick_params(axis='x', rotation=45, labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            
            # Remover bordes innecesarios
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            # Guardar para dashboard
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.charts_dir / f"dashboard_{symbol.replace('/', '_')}_{timestamp}.png"
            plt.savefig(filename, dpi=100, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return str(filename)
            
        except Exception as e:
            print(f"Error creando gráfica dashboard para {symbol}: {e}")
            return None
    
    def generate_system_charts(self):
        """Generar todas las gráficas del sistema"""
        print("Generando gráficas del sistema AlgoTrader...")
        
        created_charts = {
            'trading': [],
            'dashboard': []
        }
        
        # Gráficas principales (BTC y Gold)
        main_symbols = ['BTC/USD', 'XAU/USD']
        
        for symbol in main_symbols:
            # Gráfica de trading completa
            trading_chart = self.create_trading_chart(symbol, hours=48, include_indicators=True)
            if trading_chart:
                created_charts['trading'].append(trading_chart)
            
            # Gráfica para dashboard
            dashboard_chart = self.create_dashboard_chart(symbol, timeframe="1h", periods=24)
            if dashboard_chart:
                created_charts['dashboard'].append(dashboard_chart)
        
        # Gráficas adicionales (Forex)
        forex_symbols = ['EUR/USD', 'GBP/USD']
        
        for symbol in forex_symbols:
            dashboard_chart = self.create_dashboard_chart(symbol, timeframe="4h", periods=12)
            if dashboard_chart:
                created_charts['dashboard'].append(dashboard_chart)
        
        return created_charts
    
    def get_latest_charts(self):
        """Obtener las gráficas más recientes"""
        chart_files = list(self.charts_dir.glob("*.png"))
        chart_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return {
            'total': len(chart_files),
            'latest': chart_files[:5],  # 5 más recientes
            'directory': str(self.charts_dir.absolute())
        }

def main():
    """Función principal para pruebas"""
    try:
        generator = AlgoTraderChartGenerator()
        
        print("="*50)
        print(" ALGOTRADER CHART GENERATOR")
        print("="*50)
        
        # Generar gráficas del sistema
        charts = generator.generate_system_charts()
        
        print("\nGráficas creadas:")
        print(f"Trading charts: {len(charts['trading'])}")
        for chart in charts['trading']:
            print(f"  - {Path(chart).name}")
        
        print(f"Dashboard charts: {len(charts['dashboard'])}")
        for chart in charts['dashboard']:
            print(f"  - {Path(chart).name}")
        
        # Información de gráficas
        latest = generator.get_latest_charts()
        print(f"\nTotal de gráficas: {latest['total']}")
        print(f"Directorio: {latest['directory']}")
        
        print("\nIntegración con AlgoTrader:")
        print("- Usar en Signals Dashboard (Puerto 8506)")
        print("- Integrar con AI Dashboard (Puerto 8505)")
        print("- Análisis visual para Trade Validator")
        
        print("\nGeneración completada exitosamente!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()