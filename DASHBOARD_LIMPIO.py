#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎯 TRADING DASHBOARD - SISTEMA PROFESIONAL
==========================================
Dashboard limpio y moderno con emojis para monitoreo de trading
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import time

# 🎨 Configuración de la página
st.set_page_config(
    page_title="🎯 Trading Pro Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar menú de despliegue
st.markdown("""
<style>
    .reportview-container .main .block-container {
        max-width: none;
    }
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 🎨 CSS minimalista moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variables de color */
    :root {
        --bg-primary: #fafbfc;
        --bg-secondary: #ffffff;
        --text-primary: #1a202c;
        --text-secondary: #718096;
        --text-muted: #a0aec0;
        --accent-blue: #4299e1;
        --accent-green: #38b2ac;
        --border-light: #e2e8f0;
        --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Fondo principal */
    .main {
        background: var(--bg-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 0;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Cards minimalistas */
    .metric-card {
        background: var(--bg-secondary);
        padding: 1.75rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-light);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: var(--accent-blue);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    /* Colores de estado modernos */
    .success {
        color: var(--accent-green) !important;
        font-weight: 600;
    }
    
    .warning {
        color: #ed8936 !important;
        font-weight: 600;
    }
    
    .error {
        color: #e53e3e !important;
        font-weight: 600;
    }
    
    .info {
        color: var(--accent-blue) !important;
        font-weight: 600;
    }
    
    /* Header minimalista */
    .header {
        background: var(--bg-secondary);
        padding: 3rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-sm);
    }
    
    .header h1 {
        color: var(--text-primary) !important;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    
    .header h3 {
        color: var(--text-secondary) !important;
        font-weight: 500;
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    
    .header p {
        color: var(--text-muted) !important;
        font-weight: 400;
        font-size: 1rem;
    }
    
    /* Métricas grandes */
    .big-metric {
        font-size: 2.5rem !important;
        font-weight: 700;
        text-align: center;
        margin: 0.75rem 0;
        letter-spacing: -0.025em;
    }
    
    .metric-label {
        font-size: 0.875rem;
        text-align: center;
        color: var(--text-secondary) !important;
        margin-bottom: 0.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Texto general */
    .metric-card p {
        color: var(--text-secondary) !important;
        font-weight: 400;
        line-height: 1.5;
        margin: 0.5rem 0;
    }
    
    .metric-card h4 {
        color: var(--text-primary) !important;
        font-weight: 600;
        font-size: 1.125rem;
        margin-bottom: 0.75rem;
    }
    
    /* Sidebar moderna */
    .css-1d391kg {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-light);
    }
    
    /* Iconos SVG inline */
    .icon-status { 
        width: 12px; 
        height: 12px; 
        display: inline-block; 
        margin-right: 8px; 
        vertical-align: middle;
    }
    
    .icon-green { fill: var(--accent-green); }
    .icon-blue { fill: var(--accent-blue); }
    .icon-orange { fill: #ed8936; }
    
    /* Animaciones suaves */
    * {
        transition: color 0.15s ease, background-color 0.15s ease, border-color 0.15s ease;
    }
    
    .activity-item:hover {
        transform: translateX(4px);
        border-color: var(--accent-blue);
        box-shadow: var(--shadow-sm);
    }
    
    /* Secciones con mejor espaciado */
    .section-title {
        color: var(--text-primary) !important;
        font-weight: 600;
        font-size: 1.5rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-light);
    }
    
    /* Grid responsivo */
    @media (max-width: 768px) {
        .metric-card {
            margin: 0.5rem 0;
            padding: 1.25rem;
        }
        
        .big-metric {
            font-size: 2rem !important;
        }
        
        .header h1 {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class TradingDashboard:
    """🎯 Dashboard profesional de trading"""
    
    def __init__(self):
        self.logs_dir = Path("logs/comprehensive")
        self.date_str = datetime.now().strftime('%Y%m%d')
        
    def load_json_logs(self, filename):
        """📁 Cargar logs JSON"""
        try:
            log_file = self.logs_dir / f"{filename}_{self.date_str}.json"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return pd.DataFrame(data) if data else pd.DataFrame()
            return pd.DataFrame()
        except Exception as e:
            st.error(f"❌ Error cargando {filename}: {e}")
            return pd.DataFrame()
    
    def show_header(self):
        """🎨 Header principal del dashboard"""
        st.markdown("""
        <div class="header">
            <h1>🎯 TRADING PRO DASHBOARD</h1>
            <h3>📈 Sistema de Trading Profesional con IA</h3>
            <p>🕒 Tiempo real • 📊 Análisis completo • 🤖 IA Integrada</p>
        </div>
        """, unsafe_allow_html=True)
    
    def show_status_cards(self):
        """💳 Cards de estado del sistema"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Cargar datos
        system_events = self.load_json_logs("system_events")
        market_data = self.load_json_logs("market_data")
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">
                    <svg class="icon-status icon-green" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    ESTADO SISTEMA
                </div>
                <div class="big-metric success">ACTIVO</div>
                <p>Sistema operacional y monitoreando</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            positions_count = len(market_data) if not market_data.empty else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    <svg class="icon-status icon-blue" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    POSICIONES
                </div>
                <div class="big-metric info">{positions_count}</div>
                <p>Monitoreando activamente</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            cycles = len(system_events[system_events.get('message', '').str.contains('ciclo', case=False, na=False)]) if not system_events.empty else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    <svg class="icon-status icon-blue" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
                    </svg>
                    CICLOS
                </div>
                <div class="big-metric info">{cycles}</div>
                <p>Análisis completados</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            uptime = "25+ min" if cycles > 20 else f"{cycles} min"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    <svg class="icon-status icon-green" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"/>
                    </svg>
                    TIEMPO ACTIVO
                </div>
                <div class="big-metric success">{uptime}</div>
                <p>Sistema en línea</p>
            </div>
            """, unsafe_allow_html=True)
    
    def show_positions_summary(self):
        """💼 Resumen de posiciones"""
        st.markdown("<h2 class='section-title'>💼 POSICIONES ACTIVAS</h2>", unsafe_allow_html=True)
        
        market_data = self.load_json_logs("market_data")
        
        if market_data.empty:
            st.warning("⚠️ No hay datos de posiciones disponibles")
            return
        
        # Obtener las posiciones más recientes
        if 'timestamp_readable' in market_data.columns:
            market_data['datetime'] = pd.to_datetime(market_data['timestamp_readable'])
            latest_data = market_data.groupby('message').tail(1).sort_values('datetime', ascending=False)
        else:
            latest_data = market_data.tail(10)
        
        # Mostrar posiciones en tarjetas
        cols = st.columns(2)
        for idx, (_, row) in enumerate(latest_data.iterrows()):
            if idx >= 6:  # Limitar a 6 posiciones
                break
                
            col = cols[idx % 2]
            
            with col:
                data = row.get('data', {})
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        data = {}
                
                market_info = data.get('market_data', {})
                symbol = market_info.get('symbol', row.get('message', 'N/A').replace('Datos de mercado: ', ''))
                profit_pips = market_info.get('profit_pips', 0)
                profit_usd = market_info.get('profit_usd', 0)
                position_type = market_info.get('position_type', 'N/A')
                
                # Color según ganancia/pérdida
                color_class = "success" if profit_pips > 0 else "error" if profit_pips < 0 else "info"
                emoji = "📈" if profit_pips > 0 else "📉" if profit_pips < 0 else "➡️"
                
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{emoji} {symbol}</h4>
                    <p><strong>Tipo:</strong> {position_type} {'🔵' if position_type == 'BUY' else '🔴'}</p>
                    <p><strong>P&L:</strong> <span class="{color_class}">{profit_pips:.1f} pips (${profit_usd:.2f})</span></p>
                </div>
                """, unsafe_allow_html=True)
    
    def show_risk_management(self):
        """⚖️ Gestión de riesgo"""
        st.markdown("<h2 class='section-title'>⚖️ GESTIÓN DE RIESGO</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>🎯 BREAKEVEN</h4>
                <p><strong>Modo:</strong> <span class="warning">MANUAL</span></p>
                <p><strong>Trigger:</strong> 15+ pips</p>
                <p><strong>Acción:</strong> Sugerencia por Telegram 📱</p>
                <p><strong>Estado:</strong> ⏳ Esperando ganancias</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>📈 TRAILING STOP</h4>
                <p><strong>Modo:</strong> <span class="success">AUTOMÁTICO</span></p>
                <p><strong>Trigger:</strong> 25+ pips</p>
                <p><strong>Distancia:</strong> 15 pips</p>
                <p><strong>Estado:</strong> ⏳ Esperando ganancias</p>
            </div>
            """, unsafe_allow_html=True)
    
    def show_system_activity(self):
        """📊 Actividad del sistema"""
        st.markdown("<h2 class='section-title'>📊 ACTIVIDAD DEL SISTEMA</h2>", unsafe_allow_html=True)
        
        system_events = self.load_json_logs("system_events")
        
        if system_events.empty:
            st.info("ℹ️ No hay eventos del sistema disponibles")
            return
        
        # Filtrar eventos recientes
        if 'timestamp_readable' in system_events.columns:
            system_events['datetime'] = pd.to_datetime(system_events['timestamp_readable'])
            recent_events = system_events.tail(10).sort_values('datetime', ascending=False)
        else:
            recent_events = system_events.tail(10)
        
        # Mostrar eventos con emojis
        for _, event in recent_events.iterrows():
            message = event.get('message', 'Sin mensaje')
            timestamp = event.get('timestamp_readable', 'N/A')
            level = event.get('level', 'INFO')
            
            # Emojis según tipo de evento
            if 'ciclo' in message.lower():
                emoji = "🔄"
                color = "info"
            elif 'escaneo' in message.lower():
                emoji = "🔍"
                color = "info"
            elif 'completado' in message.lower():
                emoji = "✅"
                color = "success"
            elif 'error' in message.lower():
                emoji = "❌"
                color = "error"
            else:
                emoji = "ℹ️"
                color = "info"
            
            st.markdown(f"""
            <div class="activity-item" style="padding: 1rem; margin: 0.5rem 0; background: var(--bg-secondary); border: 1px solid var(--border-light); border-radius: 8px; transition: all 0.2s ease;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.25rem;">{emoji}</span>
                    <div style="flex: 1;">
                        <span class="{color}" style="color: var(--text-primary) !important; font-weight: 500;">{message}</span>
                        <div style="color: var(--text-muted) !important; font-size: 0.875rem; margin-top: 0.25rem;">{timestamp}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def show_performance_chart(self):
        """📈 Gráfico de rendimiento"""
        st.markdown("<h2 class='section-title'>📈 RENDIMIENTO EN TIEMPO REAL</h2>", unsafe_allow_html=True)
        
        system_events = self.load_json_logs("system_events")
        
        if system_events.empty:
            st.info("ℹ️ No hay datos suficientes para mostrar gráficos")
            return
        
        # Crear gráfico de ciclos
        cycle_events = system_events[system_events.get('message', '').str.contains('ciclo', case=False, na=False)]
        
        if not cycle_events.empty and 'timestamp_readable' in cycle_events.columns:
            cycle_events['datetime'] = pd.to_datetime(cycle_events['timestamp_readable'])
            cycle_events = cycle_events.sort_values('datetime')
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=cycle_events['datetime'],
                y=list(range(1, len(cycle_events) + 1)),
                mode='lines+markers',
                name='Ciclos del Sistema',
                line=dict(color='#10b981', width=3),
                marker=dict(size=8, color='#10b981')
            ))
            
            fig.update_layout(
                title="🔄 Progreso de Ciclos del Sistema",
                xaxis_title="⏰ Tiempo",
                yaxis_title="🔢 Número de Ciclo",
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            
            st.plotly_chart(fig, use_container_width=True)

def main():
    """🚀 Función principal"""
    dashboard = TradingDashboard()
    
    # Header principal
    dashboard.show_header()
    
    # Sidebar con opciones
    with st.sidebar:
        st.markdown("## ⚙️ CONFIGURACIÓN")
        
        auto_refresh = st.checkbox("🔄 Auto Refresh", value=True)
        refresh_interval = st.selectbox(
            "⏱️ Intervalo de Actualización",
            [5, 10, 15, 30, 60],
            index=2,
            format_func=lambda x: f"{x} segundos"
        )
        
        st.markdown("---")
        st.markdown("## 📱 CONEXIONES")
        st.success("✅ MetaTrader 5")
        st.success("✅ Telegram Bot")
        st.success("✅ Sistema de Logs")
        
        st.markdown("---")
        st.markdown("## 🔗 ACCESOS RÁPIDOS")
        st.markdown("📊 [Dashboard Original](http://localhost:8501)")
        st.markdown("📱 Telegram: @XentrisAIForex_bot")
        
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.rerun()
    
    # Contenido principal
    dashboard.show_status_cards()
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        dashboard.show_positions_summary()
    
    with col2:
        dashboard.show_risk_management()
    
    st.markdown("---")
    
    dashboard.show_performance_chart()
    
    st.markdown("---")
    
    dashboard.show_system_activity()
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()