#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RISK MANAGER DASHBOARD
======================
Panel de control web para monitorear el sistema de gestión de riesgo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import json
import os
from pathlib import Path
import time

# Configuración de página
st.set_page_config(
    page_title="Risk Manager Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .stMetric {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .success-box {
        background-color: #1e3a1e;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #4caf50;
    }
    .warning-box {
        background-color: #3a2e1e;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
    }
    .info-box {
        background-color: #1e2a3a;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

class RiskManagerDashboard:
    def __init__(self):
        # Cargar configuración
        self.load_config()
        
        # Estado
        if 'positions_history' not in st.session_state:
            st.session_state.positions_history = []
        if 'statistics' not in st.session_state:
            st.session_state.statistics = {
                'breakeven_applied': 0,
                'trailing_updated': 0,
                'total_pips_saved': 0,
                'positions_protected': 0
            }
            
    def load_config(self):
        """Cargar configuración desde .env"""
        from dotenv import load_dotenv
        env_path = Path('configs/.env')
        if env_path.exists():
            load_dotenv(env_path)
            
        self.config = {
            'breakeven_enabled': os.getenv('ENABLE_BREAKEVEN', 'true').lower() == 'true',
            'trailing_enabled': os.getenv('ENABLE_TRAILING_STOP', 'true').lower() == 'true',
            'ai_enabled': os.getenv('USE_AI_RISK_OPTIMIZATION', 'true').lower() == 'true',
            'breakeven_trigger': float(os.getenv('BREAKEVEN_TRIGGER_PIPS', '20')),
            'trailing_activation': float(os.getenv('TRAILING_ACTIVATION_PIPS', '30')),
            'trailing_distance': float(os.getenv('TRAILING_DISTANCE_PIPS', '15')),
            'check_interval': int(os.getenv('RISK_CHECK_INTERVAL', '30'))
        }
        
    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                return False
            return True
        except:
            return False
            
    def render(self):
        """Renderizar el dashboard"""
        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.title("🛡️ Risk Manager Dashboard")
            st.caption("Sistema Avanzado de Gestión de Riesgo - Breakeven & Trailing Stop")
            
        with col2:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
                
        with col3:
            status = "🟢 Activo" if self.connect_mt5() else "🔴 Desconectado"
            st.metric("Estado MT5", status)
            
        # Separador
        st.divider()
        
        # Configuración actual
        with st.expander("⚙️ Configuración Actual", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**Breakeven**")
                status = "✅ Activado" if self.config['breakeven_enabled'] else "❌ Desactivado"
                st.write(f"Estado: {status}")
                st.write(f"Trigger: {self.config['breakeven_trigger']} pips")
                
            with col2:
                st.markdown("**Trailing Stop**")
                status = "✅ Activado" if self.config['trailing_enabled'] else "❌ Desactivado"
                st.write(f"Estado: {status}")
                st.write(f"Activación: {self.config['trailing_activation']} pips")
                st.write(f"Distancia: {self.config['trailing_distance']} pips")
                
            with col3:
                st.markdown("**IA Optimization**")
                status = "✅ Activado" if self.config['ai_enabled'] else "❌ Desactivado"
                st.write(f"Estado: {status}")
                st.write(f"Modelo: deepseek-r1:14b")
                
            with col4:
                st.markdown("**Sistema**")
                st.write(f"Intervalo: {self.config['check_interval']}s")
                st.write(f"Modo: {'Conservador' if os.getenv('CONSERVATIVE_MODE') == 'true' else 'Normal'}")
                
        # Métricas principales
        st.markdown("### 📊 Estadísticas Generales")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Breakeven Aplicados",
                st.session_state.statistics['breakeven_applied'],
                delta=None if st.session_state.statistics['breakeven_applied'] == 0 else "+BE"
            )
            
        with col2:
            st.metric(
                "Trailing Actualizados",
                st.session_state.statistics['trailing_updated'],
                delta=None if st.session_state.statistics['trailing_updated'] == 0 else "+TS"
            )
            
        with col3:
            st.metric(
                "Pips Protegidos",
                f"{st.session_state.statistics['total_pips_saved']:.1f}",
                delta=None if st.session_state.statistics['total_pips_saved'] == 0 else f"+{st.session_state.statistics['total_pips_saved']:.1f}"
            )
            
        with col4:
            st.metric(
                "Posiciones Protegidas",
                st.session_state.statistics['positions_protected'],
                delta=None
            )
            
        # Posiciones actuales
        st.markdown("### 📈 Posiciones Abiertas")
        
        if self.connect_mt5():
            positions = mt5.positions_get()
            
            if positions:
                # Crear DataFrame
                data = []
                for pos in positions:
                    symbol_info = mt5.symbol_info(pos.symbol)
                    point = symbol_info.point if symbol_info else 0.00001
                    
                    # Calcular profit en pips
                    if pos.type == mt5.ORDER_TYPE_BUY:
                        current_price = symbol_info.bid if symbol_info else pos.price_current
                        profit_pips = (current_price - pos.price_open) / point
                    else:
                        current_price = symbol_info.ask if symbol_info else pos.price_current
                        profit_pips = (pos.price_open - current_price) / point
                        
                    # Estado de protección
                    protection = []
                    if pos.sl > 0:
                        if pos.type == mt5.ORDER_TYPE_BUY and pos.sl >= pos.price_open:
                            protection.append("🔒 BE")
                        elif pos.type == mt5.ORDER_TYPE_SELL and pos.sl <= pos.price_open:
                            protection.append("🔒 BE")
                        else:
                            protection.append("📊 SL")
                    else:
                        protection.append("⚠️ Sin SL")
                        
                    data.append({
                        'Ticket': pos.ticket,
                        'Símbolo': pos.symbol,
                        'Tipo': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                        'Volumen': pos.volume,
                        'Entrada': pos.price_open,
                        'Actual': current_price,
                        'SL': pos.sl if pos.sl > 0 else '-',
                        'TP': pos.tp if pos.tp > 0 else '-',
                        'Profit (pips)': f"{profit_pips:.1f}",
                        'Profit ($)': f"${pos.profit:.2f}",
                        'Protección': ' '.join(protection)
                    })
                    
                df = pd.DataFrame(data)
                
                # Mostrar tabla con colores
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Profit ($)': st.column_config.NumberColumn(
                            format="$%.2f",
                        ),
                        'Protección': st.column_config.TextColumn(
                            help="🔒 BE = Breakeven, 📊 SL = Stop Loss activo, ⚠️ = Sin protección"
                        )
                    }
                )
                
                # Análisis de riesgo
                st.markdown("### 🎯 Análisis de Riesgo")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de distribución de profit
                    profits = [float(p['Profit (pips)']) for p in data]
                    fig = go.Figure(data=[
                        go.Bar(
                            x=[p['Símbolo'] for p in data],
                            y=profits,
                            marker_color=['green' if p > 0 else 'red' for p in profits],
                            text=[f"{p:.1f}" for p in profits],
                            textposition='auto',
                        )
                    ])
                    fig.update_layout(
                        title="Profit por Posición (pips)",
                        xaxis_title="Símbolo",
                        yaxis_title="Profit (pips)",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col2:
                    # Estado de protección
                    protected = sum(1 for p in data if '🔒' in p['Protección'])
                    unprotected = len(data) - protected
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=['Protegidas', 'Sin Protección'],
                        values=[protected, unprotected],
                        hole=.3,
                        marker_colors=['#4caf50', '#ff9800']
                    )])
                    fig.update_layout(
                        title="Estado de Protección",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
            else:
                st.info("No hay posiciones abiertas")
                
        else:
            st.error("No se pudo conectar a MT5")
            
        # Recomendaciones
        st.markdown("### 💡 Recomendaciones Actuales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-box">
            <b>Configuración Sugerida para el Mercado Actual:</b><br>
            • Breakeven: 15-25 pips (según volatilidad)<br>
            • Trailing: Activar a 30 pips<br>
            • Distancia: 2x ATR o 15 pips mínimo<br>
            • Revisar cada 30 segundos
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            if self.config['ai_enabled']:
                st.markdown("""
                <div class="success-box">
                <b>IA Optimization Activa ✅</b><br>
                El sistema ajustará automáticamente los parámetros según:<br>
                • Volatilidad actual del mercado<br>
                • Tendencia y momentum<br>
                • Historial de performance
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="warning-box">
                <b>IA Optimization Desactivada ⚠️</b><br>
                Considera activar la optimización por IA para:<br>
                • Ajustes dinámicos de parámetros<br>
                • Mejor adaptación al mercado<br>
                • Maximizar protección de ganancias
                </div>
                """, unsafe_allow_html=True)
                
        # Log de eventos
        st.markdown("### 📜 Eventos Recientes")
        
        # Leer logs si existen
        log_file = Path('logs/risk_manager.log')
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-20:]  # Últimas 20 líneas
                
            # Filtrar eventos importantes
            events = []
            for line in lines:
                if 'BREAKEVEN' in line or 'TRAILING' in line or 'aplicado' in line:
                    events.append(line.strip())
                    
            if events:
                for event in events[-10:]:  # Mostrar últimos 10 eventos
                    if 'BREAKEVEN' in event:
                        st.success(event)
                    elif 'TRAILING' in event:
                        st.info(event)
                    else:
                        st.write(event)
            else:
                st.write("No hay eventos recientes")
        else:
            st.write("No se encontró archivo de log")
            
        # Footer con auto-refresh
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            if st.checkbox("Auto-actualizar cada 30 segundos"):
                time.sleep(30)
                st.rerun()

def main():
    dashboard = RiskManagerDashboard()
    dashboard.render()

if __name__ == "__main__":
    main()
