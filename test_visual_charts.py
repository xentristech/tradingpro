"""
Test Visual Charts - Verificar que los gráficos se vean correctamente
===================================================================

Script de prueba para generar gráficos de ejemplo y verificar visualización
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

def create_sample_candlestick():
    """Crear gráfico candlestick de ejemplo"""
    print("Creando gráfico candlestick de ejemplo...")
    
    # Datos de ejemplo
    dates = pd.date_range(start=datetime.now() - timedelta(hours=48), 
                         end=datetime.now(), freq='H')
    
    # Generar datos OHLC simulados
    np.random.seed(42)
    close_prices = 50000 + np.cumsum(np.random.randn(len(dates)) * 100)
    
    data = []
    for i, (date, close) in enumerate(zip(dates, close_prices)):
        high = close + np.random.uniform(50, 500)
        low = close - np.random.uniform(50, 500)
        open_price = close_prices[i-1] if i > 0 else close
        
        data.append({
            'Date': date,
            'Open': open_price,
            'High': max(open_price, close, high),
            'Low': min(open_price, close, low),
            'Close': close
        })
    
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    
    # Crear gráfico
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for i, (idx, row) in enumerate(df.iterrows()):
        # Color de la vela
        color = '#26A69A' if row['Close'] >= row['Open'] else '#EF5350'
        
        # Línea de sombra (wick)
        ax.plot([i, i], [row['Low'], row['High']], 
               color='black', linewidth=1, alpha=0.7)
        
        # Cuerpo de la vela
        body_height = abs(row['Close'] - row['Open'])
        body_bottom = min(row['Open'], row['Close'])
        
        if body_height > 0:
            rect = plt.Rectangle((i-0.3, body_bottom), 0.6, body_height,
                               facecolor=color, alpha=0.8, edgecolor='black')
            ax.add_patch(rect)
        else:
            # Doji (precios iguales)
            ax.plot([i-0.3, i+0.3], [row['Close'], row['Close']], 
                   color='black', linewidth=2)
    
    # Configurar gráfico
    current_price = df['Close'].iloc[-1]
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    ax.set_title(f'BTC/USD - LIVE Candlesticks | ${current_price:,.0f} | {timestamp}', 
                fontsize=16, fontweight='bold')
    ax.set_ylabel('Precio ($)', fontsize=12)
    ax.set_xlabel('Tiempo', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Etiquetas del eje X (cada 8 períodos)
    step = max(1, len(df) // 8)
    indices = list(range(0, len(df), step))
    labels = [df.index[i].strftime('%m-%d %H:%M') for i in indices if i < len(df)]
    ax.set_xticks(indices[:len(labels)])
    ax.set_xticklabels(labels, rotation=45)
    
    plt.tight_layout()
    
    # Guardar
    charts_dir = Path("advanced_charts")
    charts_dir.mkdir(exist_ok=True)
    filename = charts_dir / "candlestick_BTC_USD_live.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Guardado: {filename}")
    return str(filename)

def create_sample_line_chart():
    """Crear gráfico lineal de ejemplo"""
    print("Creando gráfico lineal de ejemplo...")
    
    # Datos de ejemplo
    dates = pd.date_range(start=datetime.now() - timedelta(hours=72), 
                         end=datetime.now(), freq='H')
    
    # Generar precios simulados
    np.random.seed(123)
    prices = 2000 + np.cumsum(np.random.randn(len(dates)) * 10)
    
    df = pd.DataFrame({'Close': prices}, index=dates)
    
    # Crear figura con subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                  gridspec_kw={'height_ratios': [3, 1]})
    
    # Gráfico principal
    ax1.plot(df.index, df['Close'], linewidth=3, color='#2E86C1', label='Precio LIVE', alpha=0.8)
    ax1.fill_between(df.index, df['Close'], alpha=0.2, color='#2E86C1')
    
    # Destacar último punto
    last_price = df['Close'].iloc[-1]
    last_time = df.index[-1]
    ax1.scatter([last_time], [last_price], color='red', s=100, zorder=5, 
               label=f'Actual: ${last_price:.2f}')
    
    # Media móvil
    ma20 = df['Close'].rolling(window=20).mean()
    ax1.plot(df.index, ma20, '--', linewidth=2, color='orange', 
            label='MA20', alpha=0.7)
    
    current_time = datetime.now().strftime('%H:%M:%S')
    ax1.set_title(f'XAU/USD - LIVE Line Chart | Actualizado: {current_time}', 
                 fontsize=16, fontweight='bold')
    ax1.set_ylabel('Precio ($)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    
    # Volatilidad simulada
    volatility = np.random.uniform(10, 50, len(df))
    colors = ['green' if v < 30 else 'orange' if v < 40 else 'red' for v in volatility]
    ax2.bar(df.index, volatility, color=colors, alpha=0.6)
    ax2.set_ylabel('Volatilidad', fontsize=12)
    ax2.set_xlabel('Tiempo', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar
    charts_dir = Path("advanced_charts")
    charts_dir.mkdir(exist_ok=True)
    filename = charts_dir / "line_XAU_USD_live.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Guardado: {filename}")
    return str(filename)

def create_sample_bar_analysis():
    """Crear análisis de barras de ejemplo"""
    print("Creando análisis de barras de ejemplo...")
    
    # Datos de ejemplo (15 días)
    dates = pd.date_range(start=datetime.now() - timedelta(days=15), 
                         end=datetime.now(), freq='D')
    
    np.random.seed(456)
    close_prices = 1.1000 + np.cumsum(np.random.randn(len(dates)) * 0.01)
    
    data = []
    for i, (date, close) in enumerate(zip(dates, close_prices)):
        open_price = close_prices[i-1] if i > 0 else close
        high = max(open_price, close) + np.random.uniform(0.001, 0.01)
        low = min(open_price, close) - np.random.uniform(0.001, 0.01)
        
        data.append({
            'Date': date,
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close
        })
    
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    
    # Crear figura con 4 subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Precio de cierre
    colors_close = ['#26A69A' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else '#EF5350' 
                   for i in range(len(df))]
    bars1 = ax1.bar(range(len(df)), df['Close'], color=colors_close, alpha=0.8)
    ax1.set_title(f'Precio de Cierre LIVE | Actual: ${df["Close"].iloc[-1]:.4f}', 
                 fontsize=14, fontweight='bold')
    ax1.set_ylabel('Precio')
    ax1.grid(True, alpha=0.3)
    
    # 2. Volatilidad diaria
    volatility = df['High'] - df['Low']
    avg_vol = volatility.mean()
    colors_vol = ['purple' if v <= avg_vol else 'red' for v in volatility]
    ax2.bar(range(len(df)), volatility, color=colors_vol, alpha=0.7)
    ax2.set_title(f'Volatilidad Diaria | Promedio: {avg_vol:.4f}', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Rango')
    ax2.axhline(y=avg_vol, color='black', linestyle='--', alpha=0.5)
    ax2.grid(True, alpha=0.3)
    
    # 3. Cambio porcentual
    pct_change = ((df['Close'] - df['Open']) / df['Open'] * 100)
    colors_pct = ['#26A69A' if x >= 0 else '#EF5350' for x in pct_change]
    ax3.bar(range(len(df)), pct_change, color=colors_pct, alpha=0.8)
    ax3.set_title(f'Cambio % Diario | Hoy: {pct_change.iloc[-1]:.2f}%', 
                 fontsize=14, fontweight='bold')
    ax3.set_ylabel('Cambio %')
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax3.grid(True, alpha=0.3)
    
    # 4. Strength Index
    strength = (df['Close'] / df['High'] * 100)
    colors_strength = ['#FFD700' if x >= 95 else '#FFA500' if x >= 90 else '#FF6347' 
                      for x in strength]
    ax4.bar(range(len(df)), strength, color=colors_strength, alpha=0.7)
    ax4.set_title(f'Strength Index | Actual: {strength.iloc[-1]:.1f}%', 
                 fontsize=14, fontweight='bold')
    ax4.set_ylabel('Strength %')
    ax4.axhline(y=100, color='black', linestyle='--', alpha=0.5)
    ax4.grid(True, alpha=0.3)
    
    # Etiquetas
    date_labels = [df.index[i].strftime('%m-%d') for i in range(len(df))]
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(date_labels, rotation=45)
        ax.set_xlabel('Fecha')
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    plt.suptitle(f'EUR/USD - LIVE Bar Analysis | {timestamp}', fontsize=18, fontweight='bold')
    plt.tight_layout()
    
    # Guardar
    charts_dir = Path("advanced_charts")
    filename = charts_dir / "bars_EUR_USD_live.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Guardado: {filename}")
    return str(filename)

def main():
    print("TEST VISUAL CHARTS")
    print("=" * 40)
    print("Generando gráficos de ejemplo para verificar visualización...")
    
    charts_created = []
    
    # Crear gráficos de ejemplo
    try:
        candle = create_sample_candlestick()
        if candle:
            charts_created.append(candle)
        
        line = create_sample_line_chart()
        if line:
            charts_created.append(line)
        
        bars = create_sample_bar_analysis()
        if bars:
            charts_created.append(bars)
        
        print(f"\n[SUCCESS] {len(charts_created)} gráficos de ejemplo creados")
        print("Archivos creados:")
        for chart in charts_created:
            print(f"  - {Path(chart).name}")
        
        print(f"\nUbicación: {Path('advanced_charts').absolute()}")
        print("\nPara ver los gráficos:")
        print("1. python charts_dashboard.py")  
        print("2. Abrir: http://localhost:8507")
        print("3. Los gráficos deberían aparecer con indicador LIVE")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creando gráficos de ejemplo: {e}")
        return False

if __name__ == "__main__":
    main()