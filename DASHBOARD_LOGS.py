#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DASHBOARD DE LOGS - SISTEMA DE TRADING
======================================
Dashboard web interactivo para visualizar y analizar logs
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuración de la página
st.set_page_config(
    page_title="Trading Logs Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .stAlert {
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-text {
        color: #00cc44;
        font-weight: bold;
    }
    .error-text {
        color: #ff4444;
        font-weight: bold;
    }
    .warning-text {
        color: #ffaa00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class LogsDashboard:
    """Dashboard para visualización de logs de trading"""
    
    def __init__(self):
        self.log_dir = Path("logs/comprehensive")
        self.date_str = datetime.now().strftime('%Y%m%d')
        
        # Archivos de log
        self.log_files = {
            '📈 Señales': f"signals_{self.date_str}.json",
            '💰 Trades': f"trades_{self.date_str}.json",
            '🛡️ Risk Management': f"risk_management_{self.date_str}.json",
            '⚙️ Sistema': f"system_events_{self.date_str}.json",
            '❌ Errores': f"errors_{self.date_str}.json",
            '📱 Telegram': f"telegram_{self.date_str}.json",
            '📊 Mercado': f"market_data_{self.date_str}.json",
            '📈 Performance': f"performance_{self.date_str}.json"
        }
        
        # CSV files
        self.csv_files = {
            'daily_summary': self.log_dir / f"daily_summary_{self.date_str}.csv",
            'trades_summary': self.log_dir / f"trades_summary_{self.date_str}.csv",
            'risk_actions': self.log_dir / f"risk_actions_{self.date_str}.csv"
        }
    
    def load_json_log(self, log_type):
        """Cargar archivo JSON de log"""
        try:
            file_path = self.log_dir / self.log_files[log_type]
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return pd.DataFrame(data) if data else pd.DataFrame()
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error cargando {log_type}: {e}")
            return pd.DataFrame()
    
    def load_csv_data(self, csv_type):
        """Cargar archivo CSV"""
        try:
            file_path = self.csv_files[csv_type]
            if file_path.exists():
                return pd.read_csv(file_path)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error cargando CSV {csv_type}: {e}")
            return pd.DataFrame()
    
    def display_metrics_cards(self):
        """Mostrar tarjetas de métricas principales"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Cargar datos para métricas
        signals_df = self.load_json_log('📈 Señales')
        trades_df = self.load_json_log('💰 Trades')
        risk_df = self.load_json_log('🛡️ Risk Management')
        errors_df = self.load_json_log('❌ Errores')
        telegram_df = self.load_json_log('📱 Telegram')
        
        with col1:
            st.metric(
                label="📈 Señales Generadas",
                value=len(signals_df),
                delta=f"Últimas 24h"
            )
        
        with col2:
            st.metric(
                label="💰 Trades Ejecutados",
                value=len(trades_df),
                delta=None
            )
        
        with col3:
            breakeven_count = len(risk_df[risk_df['data'].apply(lambda x: 'BREAKEVEN' in str(x))]) if not risk_df.empty else 0
            st.metric(
                label="🛡️ Breakeven Aplicados",
                value=breakeven_count,
                delta=None
            )
        
        with col4:
            trailing_count = len(risk_df[risk_df['data'].apply(lambda x: 'TRAILING' in str(x))]) if not risk_df.empty else 0
            st.metric(
                label="🎯 Trailing Aplicados",
                value=trailing_count,
                delta=None
            )
        
        with col5:
            st.metric(
                label="❌ Errores",
                value=len(errors_df),
                delta="⚠️" if len(errors_df) > 0 else "✅"
            )
    
    def display_signals_analysis(self, df):
        """Análisis de señales"""
        if df.empty:
            st.info("No hay señales registradas")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución de tipos de señal
            if 'data' in df.columns:
                signal_types = df['data'].apply(lambda x: x.get('signal_type', 'UNKNOWN') if isinstance(x, dict) else 'UNKNOWN')
                fig = px.pie(
                    values=signal_types.value_counts().values,
                    names=signal_types.value_counts().index,
                    title="Distribución de Tipos de Señal",
                    color_discrete_map={'BUY': '#00cc44', 'SELL': '#ff4444', 'NO_OPERAR': '#888888'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Confianza promedio por hora
            if 'timestamp_readable' in df.columns and 'data' in df.columns:
                df['hour'] = pd.to_datetime(df['timestamp_readable']).dt.hour
                df['confidence'] = df['data'].apply(lambda x: x.get('confidence', 0) if isinstance(x, dict) else 0)
                
                hourly_confidence = df.groupby('hour')['confidence'].mean()
                
                fig = px.bar(
                    x=hourly_confidence.index,
                    y=hourly_confidence.values,
                    title="Confianza Promedio por Hora",
                    labels={'x': 'Hora', 'y': 'Confianza (%)'}
                )
                fig.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="Umbral 70%")
                st.plotly_chart(fig, use_container_width=True)
    
    def display_risk_timeline(self, df):
        """Timeline de acciones de risk management"""
        if df.empty:
            st.info("No hay acciones de risk management registradas")
            return
        
        # Preparar datos para timeline
        timeline_data = []
        for _, row in df.iterrows():
            if isinstance(row.get('data'), dict):
                action_type = row['data'].get('action_type', 'UNKNOWN')
                pos_data = row['data'].get('position_data', {})
                
                timeline_data.append({
                    'Time': row.get('timestamp_readable', ''),
                    'Action': action_type,
                    'Symbol': pos_data.get('symbol', 'N/A'),
                    'Ticket': pos_data.get('ticket', 'N/A'),
                    'Success': row['data'].get('success', False)
                })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            
            # Crear gráfico de timeline
            fig = go.Figure()
            
            colors = {'BREAKEVEN_APPLIED': 'green', 'TRAILING_APPLIED': 'blue', 
                     'BREAKEVEN_FAILED': 'red', 'TRAILING_FAILED': 'orange'}
            
            for action in timeline_df['Action'].unique():
                action_data = timeline_df[timeline_df['Action'] == action]
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(action_data['Time']),
                    y=[action] * len(action_data),
                    mode='markers',
                    name=action,
                    marker=dict(size=10, color=colors.get(action, 'gray')),
                    text=action_data['Symbol'] + ' #' + action_data['Ticket'].astype(str),
                    hovertemplate='%{text}<br>%{x}<extra></extra>'
                ))
            
            fig.update_layout(
                title="Timeline de Risk Management",
                xaxis_title="Tiempo",
                yaxis_title="Tipo de Acción",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def display_error_analysis(self, df):
        """Análisis de errores"""
        if df.empty:
            st.success("✅ No hay errores registrados")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Tipos de error más comunes
            if 'data' in df.columns:
                error_types = df['data'].apply(lambda x: x.get('error_type', 'UNKNOWN') if isinstance(x, dict) else 'UNKNOWN')
                
                fig = px.bar(
                    x=error_types.value_counts().values,
                    y=error_types.value_counts().index,
                    orientation='h',
                    title="Tipos de Error Más Comunes",
                    labels={'x': 'Cantidad', 'y': 'Tipo de Error'},
                    color_discrete_sequence=['#ff4444']
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Errores por hora
            if 'timestamp_readable' in df.columns:
                df['hour'] = pd.to_datetime(df['timestamp_readable']).dt.hour
                hourly_errors = df.groupby('hour').size()
                
                fig = px.line(
                    x=hourly_errors.index,
                    y=hourly_errors.values,
                    title="Errores por Hora del Día",
                    labels={'x': 'Hora', 'y': 'Cantidad de Errores'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def display_log_viewer(self, log_type):
        """Visor de logs con filtros"""
        df = self.load_json_log(log_type)
        
        if df.empty:
            st.info(f"No hay logs de {log_type}")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por rango de tiempo
            if 'timestamp_readable' in df.columns and len(df) > 0:
                df['datetime'] = pd.to_datetime(df['timestamp_readable'])
                
                min_time = df['datetime'].min()
                max_time = df['datetime'].max()
                
                # Asegurar que min_time y max_time sean diferentes
                if min_time == max_time:
                    # Agregar 1 minuto al tiempo máximo para evitar error
                    max_time = max_time + pd.Timedelta(minutes=1)
                
                time_range = st.slider(
                    "Rango de tiempo",
                    min_value=min_time.to_pydatetime(),
                    max_value=max_time.to_pydatetime(),
                    value=(min_time.to_pydatetime(), max_time.to_pydatetime()),
                    format="HH:mm:ss"
                )
                
                df = df[(df['datetime'] >= time_range[0]) & (df['datetime'] <= time_range[1])]
        
        with col2:
            # Filtro por nivel
            if 'level' in df.columns:
                levels = df['level'].unique()
                selected_levels = st.multiselect("Niveles", levels, default=levels)
                df = df[df['level'].isin(selected_levels)]
        
        with col3:
            # Búsqueda de texto
            search_text = st.text_input("Buscar en mensajes", "")
            if search_text and 'message' in df.columns:
                df = df[df['message'].str.contains(search_text, case=False, na=False)]
        
        # Mostrar tabla de logs
        st.subheader(f"Logs de {log_type} ({len(df)} entradas)")
        
        # Configurar columnas a mostrar
        columns_to_show = ['timestamp_readable', 'level', 'component', 'message']
        available_columns = [col for col in columns_to_show if col in df.columns]
        
        if available_columns:
            # Paginación
            rows_per_page = st.selectbox("Filas por página", [10, 25, 50, 100], index=1)
            
            total_pages = len(df) // rows_per_page + (1 if len(df) % rows_per_page > 0 else 0)
            page = st.number_input("Página", min_value=1, max_value=max(1, total_pages), value=1)
            
            start_idx = (page - 1) * rows_per_page
            end_idx = min(start_idx + rows_per_page, len(df))
            
            # Mostrar tabla
            display_df = df[available_columns].iloc[start_idx:end_idx]
            
            # Aplicar estilos condicionales
            def highlight_levels(row):
                if 'level' in row:
                    if row['level'] == 'ERROR':
                        return ['background-color: #ffcccc'] * len(row)
                    elif row['level'] == 'WARNING':
                        return ['background-color: #fff3cd'] * len(row)
                    elif row['level'] == 'SUCCESS':
                        return ['background-color: #d4edda'] * len(row)
                return [''] * len(row)
            
            styled_df = display_df.style.apply(highlight_levels, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Botón para exportar
            csv = df.to_csv(index=False)
            st.download_button(
                label=f"📥 Descargar {log_type} como CSV",
                data=csv,
                file_name=f"{log_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Mostrar detalles expandibles
        if st.checkbox("Mostrar detalles de datos", key=f"details_{log_type}"):
            if 'data' in df.columns:
                st.subheader("Detalles de Datos")
                for idx, row in df.iloc[start_idx:end_idx].iterrows():
                    with st.expander(f"{row.get('timestamp_readable', 'N/A')} - {row.get('message', 'N/A')}"):
                        if isinstance(row.get('data'), dict):
                            st.json(row['data'])
                        else:
                            st.text(str(row.get('data', 'No data')))
    
    def display_live_monitor(self):
        """Monitor en vivo de logs"""
        st.subheader("🔴 Monitor en Vivo")
        
        # Placeholder para actualizaciones
        placeholder = st.empty()
        
        # Control de actualización
        col1, col2, col3 = st.columns(3)
        with col1:
            auto_refresh = st.checkbox("Auto-actualizar", value=True)
        with col2:
            refresh_interval = st.selectbox("Intervalo (segundos)", [1, 5, 10, 30], index=1)
        with col3:
            if st.button("🔄 Actualizar Ahora"):
                st.rerun()
        
        if auto_refresh:
            # Obtener últimas entradas de cada tipo
            latest_entries = []
            
            for log_type in self.log_files.keys():
                df = self.load_json_log(log_type)
                if not df.empty and 'timestamp_readable' in df.columns:
                    # Obtener últimas 5 entradas
                    latest = df.tail(5)
                    for _, row in latest.iterrows():
                        entry = {
                            'Time': row.get('timestamp_readable', ''),
                            'Type': log_type,
                            'Level': row.get('level', 'INFO'),
                            'Message': row.get('message', 'No message')[:100]  # Limitar longitud
                        }
                        latest_entries.append(entry)
            
            # Ordenar por tiempo
            latest_entries.sort(key=lambda x: x['Time'], reverse=True)
            
            # Mostrar tabla de últimas entradas
            with placeholder.container():
                st.dataframe(
                    pd.DataFrame(latest_entries[:20]),  # Mostrar últimas 20
                    use_container_width=True,
                    height=400
                )
            
            # Auto-refresh
            time.sleep(refresh_interval)
            st.rerun()
    
    def display_performance_dashboard(self):
        """Dashboard de rendimiento"""
        st.subheader("📊 Dashboard de Rendimiento")
        
        # Cargar datos de trades
        trades_csv = self.load_csv_data('trades_summary')
        
        if not trades_csv.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Profit/Loss por símbolo
                if 'symbol' in trades_csv.columns and 'profit_usd' in trades_csv.columns:
                    # Convertir profit_usd a numérico
                    trades_csv['profit_usd'] = pd.to_numeric(trades_csv['profit_usd'], errors='coerce')
                    
                    profit_by_symbol = trades_csv.groupby('symbol')['profit_usd'].sum()
                    
                    fig = px.bar(
                        x=profit_by_symbol.index,
                        y=profit_by_symbol.values,
                        title="Profit/Loss por Símbolo",
                        labels={'x': 'Símbolo', 'y': 'Profit (USD)'},
                        color=profit_by_symbol.values,
                        color_continuous_scale=['red', 'yellow', 'green']
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Win rate por estrategia
                if 'strategy' in trades_csv.columns and 'profit_usd' in trades_csv.columns:
                    trades_csv['is_win'] = trades_csv['profit_usd'] > 0
                    win_rate = trades_csv.groupby('strategy')['is_win'].mean() * 100
                    
                    fig = px.bar(
                        x=win_rate.index,
                        y=win_rate.values,
                        title="Win Rate por Estrategia",
                        labels={'x': 'Estrategia', 'y': 'Win Rate (%)'},
                        color=win_rate.values,
                        color_continuous_scale=['red', 'yellow', 'green']
                    )
                    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50%")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Cargar datos de risk actions
        risk_csv = self.load_csv_data('risk_actions')
        
        if not risk_csv.empty:
            # Success rate de risk management
            if 'success' in risk_csv.columns and 'action_type' in risk_csv.columns:
                success_rate = risk_csv.groupby('action_type')['success'].mean() * 100
                
                fig = px.pie(
                    values=success_rate.values,
                    names=success_rate.index,
                    title="Tasa de Éxito de Risk Management",
                    color_discrete_map={'BREAKEVEN_APPLIED': '#00cc44', 'TRAILING_APPLIED': '#0088ff'}
                )
                st.plotly_chart(fig, use_container_width=True)

def main():
    """Función principal del dashboard"""
    
    # Título principal
    st.title("📊 Dashboard de Logs - Sistema de Trading")
    st.markdown("---")
    
    # Inicializar dashboard
    dashboard = LogsDashboard()
    
    # Sidebar para navegación
    st.sidebar.title("🔧 Navegación")
    
    page = st.sidebar.radio(
        "Selecciona una vista:",
        ["📈 Resumen General", "🔍 Explorador de Logs", "🔴 Monitor en Vivo", 
         "📊 Análisis de Performance", "❌ Análisis de Errores"]
    )
    
    # Filtro de fecha en sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Filtros Globales")
    
    # Selector de fecha
    selected_date = st.sidebar.date_input(
        "Fecha de logs",
        value=datetime.now().date(),
        max_value=datetime.now().date()
    )
    
    # Actualizar fecha en dashboard
    dashboard.date_str = selected_date.strftime('%Y%m%d')
    
    # Actualizar archivos de log con nueva fecha
    for key in dashboard.log_files.keys():
        file_name = dashboard.log_files[key].split('_')[0]
        dashboard.log_files[key] = f"{file_name}_{dashboard.date_str}.json"
    
    # Mostrar página seleccionada
    if page == "📈 Resumen General":
        st.header("📈 Resumen General")
        
        # Métricas principales
        dashboard.display_metrics_cards()
        
        st.markdown("---")
        
        # Análisis de señales
        st.subheader("📊 Análisis de Señales")
        signals_df = dashboard.load_json_log('📈 Señales')
        dashboard.display_signals_analysis(signals_df)
        
        st.markdown("---")
        
        # Timeline de risk management
        st.subheader("🛡️ Timeline de Risk Management")
        risk_df = dashboard.load_json_log('🛡️ Risk Management')
        dashboard.display_risk_timeline(risk_df)
    
    elif page == "🔍 Explorador de Logs":
        st.header("🔍 Explorador de Logs")
        
        # Selector de tipo de log
        selected_log = st.selectbox(
            "Selecciona el tipo de log:",
            list(dashboard.log_files.keys())
        )
        
        # Mostrar visor de logs
        dashboard.display_log_viewer(selected_log)
    
    elif page == "🔴 Monitor en Vivo":
        st.header("🔴 Monitor en Vivo")
        dashboard.display_live_monitor()
    
    elif page == "📊 Análisis de Performance":
        st.header("📊 Análisis de Performance")
        dashboard.display_performance_dashboard()
    
    elif page == "❌ Análisis de Errores":
        st.header("❌ Análisis de Errores")
        errors_df = dashboard.load_json_log('❌ Errores')
        dashboard.display_error_analysis(errors_df)
        
        # Tabla detallada de errores
        if not errors_df.empty:
            st.markdown("---")
            st.subheader("📋 Detalle de Errores Recientes")
            dashboard.display_log_viewer('❌ Errores')
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        """
        **Sistema de Logging v1.0**
        
        📁 Logs en: `logs/comprehensive/`
        
        🔄 Auto-actualización disponible
        
        📥 Exportación a CSV disponible
        """
    )
    
    # Información de última actualización
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()