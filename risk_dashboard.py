#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DASHBOARD DE RIESGO EN TIEMPO REAL - ALGO TRADER V3
===================================================
Dashboard interactivo con Streamlit para monitoreo de riesgo
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
from pathlib import Path
import sys

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

# Importar módulos del proyecto
from src.journal.trading_journal import get_journal
from src.broker.mt5_connection import MT5Connection

# Configuración de la página
st.set_page_config(
    page_title="AlgoTrader V3 - Risk Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #1f77b4;
    }
    .metric-positive {
        color: #00cc00;
    }
    .metric-negative {
        color: #ff4444;
    }
    .alert-box {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
    }
    .alert-danger {
        background-color: #f8d7da;
        border: 1px solid #dc3545;
    }
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado de sesión
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 5

def load_bot_state():
    """Carga el estado del bot desde el archivo JSON"""
    state_file = Path("data/bot_state.json")
    if state_file.exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return {}

def get_mt5_data():
    """Obtiene datos de MT5"""
    try:
        mt5 = MT5Connection()
        if mt5.connect():
            account_info = mt5.account_info
            positions = mt5.get_positions()
            
            return {
                'connected': True,
                'balance': account_info.balance if account_info else 0,
                'equity': account_info.equity if account_info else 0,
                'margin': account_info.margin if account_info else 0,
                'free_margin': account_info.margin_free if account_info else 0,
                'positions': len(positions) if positions else 0,
                'positions_data': positions
            }
    except:
        pass
    
    return {
        'connected': False,
        'balance': 0,
        'equity': 0,
        'margin': 0,
        'free_margin': 0,
        'positions': 0,
        'positions_data': []
    }

def calculate_risk_metrics(journal, mt5_data):
    """Calcula métricas de riesgo en tiempo real"""
    metrics = journal.calculate_metrics(period_days=30)
    
    # Calcular exposición actual
    total_exposure = 0
    if mt5_data['positions_data']:
        for pos in mt5_data['positions_data']:
            total_exposure += pos.volume * pos.price_current
    
    # Calcular riesgo actual
    current_risk = 0
    if mt5_data['equity'] > 0:
        current_risk = (total_exposure / mt5_data['equity']) * 100
    
    # Drawdown actual
    current_dd = 0
    if mt5_data['balance'] > 0:
        current_dd = ((mt5_data['balance'] - mt5_data['equity']) / mt5_data['balance']) * 100
    
    return {
        **metrics,
        'total_exposure': total_exposure,
        'current_risk': current_risk,
        'current_drawdown': current_dd,
        'margin_level': (mt5_data['equity'] / mt5_data['margin'] * 100) if mt5_data['margin'] > 0 else 0
    }

def create_equity_chart(journal):
    """Crea gráfico de equity curve"""
    if not journal.equity_history:
        return None
    
    df = pd.DataFrame(journal.equity_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['value'],
        mode='lines',
        name='Equity',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Añadir línea de balance inicial si existe
    if journal.balance_history:
        initial_balance = journal.balance_history[0]['balance']
        fig.add_hline(y=initial_balance, line_dash="dash", 
                     line_color="gray", annotation_text="Balance Inicial")
    
    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Tiempo",
        yaxis_title="Equity ($)",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_pnl_distribution(journal):
    """Crea gráfico de distribución de PnL"""
    trades_df = pd.DataFrame([t.to_dict() for t in journal.trades if t.profit_usd])
    
    if trades_df.empty:
        return None
    
    fig = go.Figure()
    
    # Histograma de PnL
    fig.add_trace(go.Histogram(
        x=trades_df['profit_usd'],
        nbinsx=30,
        name='Distribución PnL',
        marker_color='#1f77b4',
        opacity=0.7
    ))
    
    # Añadir línea vertical en 0
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break Even")
    
    # Añadir media
    mean_pnl = trades_df['profit_usd'].mean()
    fig.add_vline(x=mean_pnl, line_dash="dash", line_color="green", 
                 annotation_text=f"Media: ${mean_pnl:.2f}")
    
    fig.update_layout(
        title="Distribución de Ganancias/Pérdidas",
        xaxis_title="PnL ($)",
        yaxis_title="Frecuencia",
        height=400,
        showlegend=False
    )
    
    return fig

def create_symbol_performance(journal):
    """Crea gráfico de rendimiento por símbolo"""
    trades_df = pd.DataFrame([t.to_dict() for t in journal.trades if t.profit_usd])
    
    if trades_df.empty:
        return None
    
    # Agrupar por símbolo
    symbol_stats = trades_df.groupby('symbol').agg({
        'profit_usd': 'sum',
        'ticket': 'count'
    }).reset_index()
    symbol_stats.columns = ['Symbol', 'Total Profit', 'Trades']
    
    # Crear gráfico de barras
    fig = px.bar(symbol_stats, x='Symbol', y='Total Profit',
                 color='Total Profit',
                 color_continuous_scale=['red', 'yellow', 'green'],
                 text='Trades',
                 title="Rendimiento por Símbolo")
    
    fig.update_traces(texttemplate='%{text} trades', textposition='outside')
    fig.update_layout(height=400)
    
    return fig

def create_drawdown_chart(journal):
    """Crea gráfico de drawdown"""
    if not journal.equity_history:
        return None
    
    df = pd.DataFrame(journal.equity_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['value'] = df['value'].astype(float)
    
    # Calcular drawdown
    df['peak'] = df['value'].cummax()
    df['drawdown'] = (df['value'] - df['peak']) / df['peak'] * 100
    
    fig = go.Figure()
    
    # Área de drawdown
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['drawdown'],
        fill='tozeroy',
        name='Drawdown %',
        line=dict(color='red', width=1),
        fillcolor='rgba(255, 0, 0, 0.2)'
    ))
    
    # Línea de advertencia
    fig.add_hline(y=-5, line_dash="dash", line_color="orange", 
                 annotation_text="Advertencia -5%")
    fig.add_hline(y=-10, line_dash="dash", line_color="red", 
                 annotation_text="Crítico -10%")
    
    fig.update_layout(
        title="Drawdown Histórico",
        xaxis_title="Tiempo",
        yaxis_title="Drawdown (%)",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def display_alerts(risk_metrics, mt5_data):
    """Muestra alertas de riesgo"""
    alerts = []
    
    # Verificar drawdown
    if risk_metrics['current_drawdown'] > 10:
        alerts.append(('danger', f"⚠️ DRAWDOWN CRÍTICO: {risk_metrics['current_drawdown']:.2f}%"))
    elif risk_metrics['current_drawdown'] > 5:
        alerts.append(('warning', f"⚠️ Drawdown elevado: {risk_metrics['current_drawdown']:.2f}%"))
    
    # Verificar exposición
    if risk_metrics['current_risk'] > 30:
        alerts.append(('danger', f"⚠️ EXPOSICIÓN ALTA: {risk_metrics['current_risk']:.2f}%"))
    elif risk_metrics['current_risk'] > 20:
        alerts.append(('warning', f"⚠️ Exposición moderada: {risk_metrics['current_risk']:.2f}%"))
    
    # Verificar margin level
    if mt5_data['margin'] > 0 and risk_metrics['margin_level'] < 200:
        alerts.append(('danger', f"⚠️ MARGIN LEVEL BAJO: {risk_metrics['margin_level']:.2f}%"))
    elif mt5_data['margin'] > 0 and risk_metrics['margin_level'] < 500:
        alerts.append(('warning', f"⚠️ Margin level: {risk_metrics['margin_level']:.2f}%"))
    
    # Verificar win rate
    if risk_metrics['win_rate'] < 0.4:
        alerts.append(('warning', f"⚠️ Win rate bajo: {risk_metrics['win_rate']*100:.1f}%"))
    
    # Mostrar alertas
    if alerts:
        st.subheader("🚨 Alertas de Riesgo")
        for alert_type, message in alerts:
            if alert_type == 'danger':
                st.error(message)
            elif alert_type == 'warning':
                st.warning(message)
            else:
                st.info(message)
    else:
        st.success("✅ Todos los parámetros de riesgo están dentro de límites normales")

def main():
    """Función principal del dashboard"""
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("📊 AlgoTrader V3 - Risk Dashboard")
    with col2:
        st.markdown(f"**Última actualización:** {st.session_state.last_update.strftime('%H:%M:%S')}")
    with col3:
        if st.button("🔄 Actualizar"):
            st.session_state.last_update = datetime.now()
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Auto-refresh
        st.session_state.auto_refresh = st.checkbox("Auto-actualizar", st.session_state.auto_refresh)
        if st.session_state.auto_refresh:
            st.session_state.refresh_interval = st.slider(
                "Intervalo (segundos)", 1, 60, st.session_state.refresh_interval
            )
        
        # Período de análisis
        period = st.selectbox(
            "Período de análisis",
            ["Hoy", "7 días", "30 días", "Todo"],
            index=2
        )
        
        # Filtros
        st.subheader("Filtros")
        show_closed = st.checkbox("Mostrar trades cerrados", True)
        show_open = st.checkbox("Mostrar posiciones abiertas", True)
        
        # Estado de servicios
        st.subheader("Estado de Servicios")
        bot_state = load_bot_state()
        mt5_data = get_mt5_data()
        
        # MT5
        if mt5_data['connected']:
            st.success("✅ MT5 Conectado")
        else:
            st.error("❌ MT5 Desconectado")
        
        # Telegram
        if bot_state.get('telegram_active'):
            st.success("✅ Telegram Activo")
        else:
            st.warning("⚠️ Telegram Inactivo")
        
        # IA
        if bot_state.get('ai_active'):
            st.success("✅ IA Activa")
        else:
            st.warning("⚠️ IA Inactiva")
    
    # Cargar datos
    journal = get_journal()
    mt5_data = get_mt5_data()
    risk_metrics = calculate_risk_metrics(journal, mt5_data)
    
    # Métricas principales
    st.subheader("📈 Métricas Principales")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "Balance",
            f"${mt5_data['balance']:.2f}",
            f"{mt5_data['balance'] - 10000:.2f}" if mt5_data['balance'] else None
        )
    
    with col2:
        st.metric(
            "Equity", 
            f"${mt5_data['equity']:.2f}",
            f"{mt5_data['equity'] - mt5_data['balance']:.2f}" if mt5_data['equity'] else None
        )
    
    with col3:
        dd_color = "🔴" if risk_metrics['current_drawdown'] > 5 else "🟢"
        st.metric(
            f"Drawdown {dd_color}",
            f"{risk_metrics['current_drawdown']:.2f}%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Win Rate",
            f"{risk_metrics['win_rate']*100:.1f}%",
            f"{(risk_metrics['win_rate']-0.5)*100:.1f}%" if risk_metrics['win_rate'] else None
        )
    
    with col5:
        st.metric(
            "Profit Factor",
            f"{risk_metrics['profit_factor']:.2f}",
            "Positivo" if risk_metrics['profit_factor'] > 1 else "Negativo"
        )
    
    with col6:
        st.metric(
            "Sharpe Ratio",
            f"{risk_metrics['sharpe_ratio']:.2f}",
            "Bueno" if risk_metrics['sharpe_ratio'] > 1 else "Mejorable"
        )
    
    # Alertas
    display_alerts(risk_metrics, mt5_data)
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Gráficos", "📋 Trades", "💹 Posiciones", "📈 Métricas", "🎯 Análisis"]
    )
    
    with tab1:
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            equity_chart = create_equity_chart(journal)
            if equity_chart:
                st.plotly_chart(equity_chart, use_container_width=True)
            else:
                st.info("No hay datos de equity disponibles")
        
        with col2:
            drawdown_chart = create_drawdown_chart(journal)
            if drawdown_chart:
                st.plotly_chart(drawdown_chart, use_container_width=True)
            else:
                st.info("No hay datos de drawdown disponibles")
        
        col3, col4 = st.columns(2)
        
        with col3:
            pnl_chart = create_pnl_distribution(journal)
            if pnl_chart:
                st.plotly_chart(pnl_chart, use_container_width=True)
            else:
                st.info("No hay trades para mostrar distribución")
        
        with col4:
            symbol_chart = create_symbol_performance(journal)
            if symbol_chart:
                st.plotly_chart(symbol_chart, use_container_width=True)
            else:
                st.info("No hay datos por símbolo")
    
    with tab2:
        # Tabla de trades
        st.subheader("📋 Historial de Trades")
        
        if journal.trades:
            trades_data = []
            for trade in journal.trades[-50:]:  # Últimos 50 trades
                trades_data.append({
                    'Ticket': trade.ticket,
                    'Símbolo': trade.symbol,
                    'Tipo': trade.trade_type,
                    'Volumen': trade.volume,
                    'Entrada': trade.entry_price,
                    'Salida': trade.exit_price or '-',
                    'PnL ($)': f"${trade.profit_usd:.2f}" if trade.profit_usd else '-',
                    'PnL (%)': f"{trade.profit_percent:.2f}%" if trade.profit_percent else '-',
                    'Estrategia': trade.strategy,
                    'Resultado': trade.result or 'ABIERTO'
                })
            
            df_trades = pd.DataFrame(trades_data)
            
            # Aplicar colores según resultado
            def color_result(val):
                if val == 'WIN':
                    return 'background-color: #90EE90'
                elif val == 'LOSS':
                    return 'background-color: #FFB6C1'
                return ''
            
            styled_df = df_trades.style.applymap(color_result, subset=['Resultado'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No hay trades en el historial")
    
    with tab3:
        # Posiciones abiertas
        st.subheader("💹 Posiciones Abiertas")
        
        if mt5_data['positions_data']:
            positions_data = []
            for pos in mt5_data['positions_data']:
                current_profit = pos.profit
                pip_value = 1 if 'JPY' in pos.symbol else 0.0001
                pips = (pos.price_current - pos.price_open) / pip_value
                if pos.type == 1:  # SELL
                    pips = -pips
                
                positions_data.append({
                    'Ticket': pos.ticket,
                    'Símbolo': pos.symbol,
                    'Tipo': 'BUY' if pos.type == 0 else 'SELL',
                    'Volumen': pos.volume,
                    'Entrada': pos.price_open,
                    'Actual': pos.price_current,
                    'SL': pos.sl or 'Sin SL ⚠️',
                    'TP': pos.tp or 'Sin TP',
                    'Pips': f"{pips:.1f}",
                    'PnL': f"${current_profit:.2f}"
                })
            
            df_positions = pd.DataFrame(positions_data)
            
            # Aplicar colores según PnL
            def color_pnl(val):
                if '$' in str(val):
                    value = float(val.replace('$', ''))
                    if value > 0:
                        return 'color: green'
                    elif value < 0:
                        return 'color: red'
                return ''
            
            styled_positions = df_positions.style.applymap(color_pnl, subset=['PnL'])
            st.dataframe(styled_positions, use_container_width=True)
            
            # Resumen de exposición
            total_volume = sum(pos.volume for pos in mt5_data['positions_data'])
            st.info(f"**Exposición total:** {total_volume:.2f} lotes | "
                   f"**Riesgo:** {risk_metrics['current_risk']:.2f}%")
        else:
            st.info("No hay posiciones abiertas")
    
    with tab4:
        # Métricas detalladas
        st.subheader("📈 Métricas Detalladas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Métricas de Rendimiento")
            metrics_display = {
                'Total Trades': risk_metrics['total_trades'],
                'Trades Ganadores': risk_metrics['winning_trades'],
                'Trades Perdedores': risk_metrics['losing_trades'],
                'Ganancia Bruta': f"${risk_metrics['gross_profit']:.2f}",
                'Pérdida Bruta': f"${risk_metrics['gross_loss']:.2f}",
                'Ganancia Neta': f"${risk_metrics['net_profit']:.2f}",
                'Ganancia Promedio': f"${risk_metrics['avg_win']:.2f}",
                'Pérdida Promedio': f"${risk_metrics['avg_loss']:.2f}",
                'Expectancy': f"${risk_metrics['expectancy']:.2f}"
            }
            
            for key, value in metrics_display.items():
                st.text(f"{key}: {value}")
        
        with col2:
            st.markdown("### Métricas de Riesgo")
            risk_display = {
                'Sharpe Ratio': f"{risk_metrics['sharpe_ratio']:.2f}",
                'Sortino Ratio': f"{risk_metrics['sortino_ratio']:.2f}",
                'Max Drawdown': f"${risk_metrics['max_drawdown']:.2f}",
                'Max Drawdown %': f"{risk_metrics['max_drawdown_percent']:.2f}%",
                'VaR 95%': f"${risk_metrics['var_95']:.2f}",
                'Calmar Ratio': f"{risk_metrics['calmar_ratio']:.2f}",
                'Recovery Factor': f"{risk_metrics['recovery_factor']:.2f}",
                'Avg R:R': f"{risk_metrics['avg_rr']:.2f}",
                'Margin Level': f"{risk_metrics['margin_level']:.2f}%"
            }
            
            for key, value in risk_display.items():
                st.text(f"{key}: {value}")
    
    with tab5:
        # Análisis y patrones
        st.subheader("🎯 Análisis de Patrones")
        
        patterns = journal.analyze_patterns()
        
        if patterns.get('message'):
            st.info(patterns['message'])
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### Mejores Horas")
                if patterns.get('best_hours'):
                    for hour, data in patterns['best_hours']:
                        st.text(f"{hour}:00 - ${data['profit']:.2f} ({data['trades']} trades)")
            
            with col2:
                st.markdown("### Mejores Días")
                if patterns.get('best_days'):
                    for day, data in patterns['best_days']:
                        st.text(f"{day}: ${data['profit']:.2f} ({data['trades']} trades)")
            
            with col3:
                st.markdown("### Rachas")
                st.text(f"Max racha ganadora: {patterns.get('max_win_streak', 0)}")
                st.text(f"Max racha perdedora: {patterns.get('max_loss_streak', 0)}")
                current = patterns.get('current_streak', 0)
                if current > 0:
                    st.success(f"Racha actual: +{current} wins")
                elif current < 0:
                    st.error(f"Racha actual: {current} losses")
                else:
                    st.info("Sin racha actual")
        
        # Recomendaciones
        st.markdown("### 💡 Recomendaciones")
        
        recommendations = []
        
        if risk_metrics['win_rate'] < 0.5:
            recommendations.append("⚠️ Win rate bajo - Revisar estrategias y condiciones de entrada")
        
        if risk_metrics['avg_rr'] < 1.5:
            recommendations.append("⚠️ Risk/Reward bajo - Considerar targets más amplios")
        
        if risk_metrics['max_drawdown_percent'] > 10:
            recommendations.append("🔴 Drawdown alto - Reducir tamaño de posiciones")
        
        if risk_metrics['sharpe_ratio'] < 1:
            recommendations.append("⚠️ Sharpe Ratio bajo - Mejorar consistencia de retornos")
        
        if recommendations:
            for rec in recommendations:
                st.warning(rec)
        else:
            st.success("✅ Todas las métricas están en rangos óptimos")
    
    # Auto-refresh
    if st.session_state.auto_refresh:
        time.sleep(st.session_state.refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()