"""
Dashboard Web Interactivo - AlgoTrader v3.0
Panel de control en tiempo real para monitorear el sistema de trading
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import time
import json
import os
from pathlib import Path
import asyncio

# Configuración de página
st.set_page_config(
    page_title="AlgoTrader Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f4e79 0%, #2e8b57 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
    .alert-success {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 0.25rem;
    }
    .alert-danger {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

class TradingDashboard:
    def __init__(self):
        self.symbol = "BTCUSD"
        self.logs_path = Path("logs")
        self.data_cache = {}
        
    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if not mt5.initialize():
                return False, "No se pudo inicializar MT5"
            return True, "Conectado exitosamente"
        except Exception as e:
            return False, f"Error: {e}"
    
    def get_account_info(self):
        """Obtener información de la cuenta"""
        try:
            account = mt5.account_info()
            if account:
                return {
                    'login': account.login,
                    'balance': account.balance,
                    'equity': account.equity,
                    'margin': account.margin,
                    'free_margin': account.margin_free,
                    'profit': account.profit,
                    'currency': account.currency,
                    'leverage': account.leverage,
                    'company': account.company
                }
        except Exception as e:
            st.error(f"Error obteniendo info de cuenta: {e}")
        return None
    
    def get_positions(self):
        """Obtener posiciones abiertas"""
        try:
            positions = mt5.positions_get()
            if positions:
                pos_data = []
                for pos in positions:
                    pos_data.append({
                        'ticket': pos.ticket,
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == 0 else 'SELL',
                        'volume': pos.volume,
                        'price_open': pos.price_open,
                        'price_current': pos.price_current,
                        'profit': pos.profit,
                        'magic': pos.magic,
                        'time': datetime.fromtimestamp(pos.time)
                    })
                return pd.DataFrame(pos_data)
        except Exception as e:
            st.error(f"Error obteniendo posiciones: {e}")
        return pd.DataFrame()
    
    def get_bot_status(self):
        """Verificar estado del bot leyendo logs"""
        try:
            log_file = self.logs_path / "pro_bot.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                if lines:
                    last_line = lines[-1].strip()
                    # Extraer timestamp de la última línea
                    if '|' in last_line:
                        time_part = last_line.split('|')[0].strip()
                        try:
                            last_time = datetime.strptime(time_part, '%H:%M:%S')
                            # Ajustar fecha a hoy
                            last_time = last_time.replace(
                                year=datetime.now().year,
                                month=datetime.now().month,
                                day=datetime.now().day
                            )
                            
                            # Si está dentro de los últimos 2 minutos, está activo
                            time_diff = datetime.now() - last_time
                            is_active = time_diff.total_seconds() < 120
                            
                            return {
                                'active': is_active,
                                'last_update': last_time,
                                'status': 'ONLINE' if is_active else 'OFFLINE',
                                'last_log': last_line
                            }
                        except:
                            pass
        except Exception as e:
            st.error(f"Error leyendo logs: {e}")
        
        return {
            'active': False,
            'last_update': None,
            'status': 'UNKNOWN',
            'last_log': 'No disponible'
        }
    
    def parse_log_signals(self):
        """Extraer señales de los logs"""
        signals = []
        try:
            log_file = self.logs_path / "pro_bot.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line in lines[-50:]:  # Últimas 50 líneas
                    if 'Señal:' in line and 'Precio:' in line:
                        try:
                            parts = line.strip().split('|')
                            time_str = parts[0].strip()
                            content = parts[-1].strip()
                            
                            # Extraer precio y señal
                            if 'Precio:' in content and 'Señal:' in content:
                                precio_part = content.split('Precio:')[1].split()[0]
                                senal_part = content.split('Señal:')[1].split()[0]
                                
                                signals.append({
                                    'time': time_str,
                                    'price': float(precio_part) if precio_part != '0.00' else None,
                                    'signal': senal_part,
                                    'raw_line': content
                                })
                        except:
                            continue
        
        except Exception as e:
            st.error(f"Error parseando logs: {e}")
        
        return signals[-10:]  # Últimas 10 señales
    
    def get_price_data(self):
        """Obtener datos de precio actuales"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                return {
                    'symbol': self.symbol,
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': tick.ask - tick.bid,
                    'time': datetime.fromtimestamp(tick.time)
                }
        except Exception as e:
            st.error(f"Error obteniendo precio: {e}")
        return None

def main():
    dashboard = TradingDashboard()
    
    # Header principal
    st.markdown('<h1 class="main-header">🚀 AlgoTrader Dashboard v3.0</h1>', unsafe_allow_html=True)
    
    # Sidebar para controles
    st.sidebar.header("⚙️ Panel de Control")
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=True)
    show_logs = st.sidebar.checkbox("📝 Mostrar logs detallados", value=False)
    
    if st.sidebar.button("🔄 Actualizar ahora"):
        st.rerun()
    
    # Verificar conexión MT5
    mt5_connected, mt5_msg = dashboard.connect_mt5()
    
    # Estado del sistema
    st.subheader("📊 Estado del Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if mt5_connected:
            st.markdown('<div class="alert-success">✅ MT5 Conectado</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-danger">❌ MT5 Desconectado</div>', unsafe_allow_html=True)
    
    with col2:
        bot_status = dashboard.get_bot_status()
        if bot_status['active']:
            st.markdown('<div class="alert-success">🤖 Bot Activo</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-danger">🤖 Bot Inactivo</div>', unsafe_allow_html=True)
    
    with col3:
        # Verificar Ollama
        import subprocess
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
            ollama_active = result.returncode == 0
        except:
            ollama_active = False
        
        if ollama_active:
            st.markdown('<div class="alert-success">🧠 Ollama IA Activo</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-danger">🧠 Ollama IA Inactivo</div>', unsafe_allow_html=True)
    
    with col4:
        # Estado de Telegram
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        if telegram_token:
            st.markdown('<div class="alert-success">📱 Telegram OK</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-danger">📱 Telegram No Config</div>', unsafe_allow_html=True)
    
    if not mt5_connected:
        st.error(f"⚠️ {mt5_msg}")
        st.stop()
    
    # Información de cuenta
    st.subheader("💰 Información de Cuenta")
    account_info = dashboard.get_account_info()
    
    if account_info:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("💳 Cuenta", f"{account_info['login']}")
            st.metric("🏢 Broker", account_info['company'])
        
        with col2:
            st.metric("💰 Balance", f"${account_info['balance']:,.2f}")
            st.metric("📈 Equity", f"${account_info['equity']:,.2f}")
        
        with col3:
            profit_delta = account_info['profit']
            st.metric("📊 P&L Diario", f"${profit_delta:,.2f}", delta=f"{profit_delta:+.2f}")
            st.metric("🔒 Margen", f"${account_info['margin']:,.2f}")
        
        with col4:
            st.metric("💸 Margen Libre", f"${account_info['free_margin']:,.2f}")
            st.metric("⚖️ Apalancamiento", f"1:{account_info['leverage']}")
        
        with col5:
            st.metric("💱 Moneda", account_info['currency'])
            margin_level = (account_info['equity'] / account_info['margin'] * 100) if account_info['margin'] > 0 else 0
            st.metric("📏 Nivel Margen", f"{margin_level:.1f}%")
    
    # Precio actual
    st.subheader("📈 Precio Actual")
    price_data = dashboard.get_price_data()
    
    if price_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Símbolo", price_data['symbol'])
        with col2:
            st.metric("📉 Bid", f"${price_data['bid']:,.2f}")
        with col3:
            st.metric("📈 Ask", f"${price_data['ask']:,.2f}")
        with col4:
            st.metric("📊 Spread", f"${price_data['spread']:,.2f}")
    
    # Posiciones abiertas
    st.subheader("📊 Posiciones Abiertas")
    positions_df = dashboard.get_positions()
    
    if not positions_df.empty:
        st.dataframe(
            positions_df,
            use_container_width=True,
            column_config={
                "profit": st.column_config.NumberColumn("P&L", format="$%.2f"),
                "price_open": st.column_config.NumberColumn("Precio Entrada", format="%.5f"),
                "price_current": st.column_config.NumberColumn("Precio Actual", format="%.5f"),
                "volume": st.column_config.NumberColumn("Volumen", format="%.2f"),
            }
        )
        
        # Gráfico P&L por posición
        fig = px.bar(
            positions_df, 
            x='ticket', 
            y='profit',
            color='type',
            title="P&L por Posición",
            labels={'profit': 'P&L ($)', 'ticket': 'Ticket'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 No hay posiciones abiertas actualmente")
    
    # Estado del bot
    st.subheader("🤖 Estado del Bot")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if bot_status['active']:
            st.success(f"✅ Bot ACTIVO")
            st.info(f"🕐 Última actualización: {bot_status['last_update']}")
        else:
            st.error(f"❌ Bot INACTIVO")
            if bot_status['last_update']:
                st.warning(f"🕐 Última actividad: {bot_status['last_update']}")
    
    with col2:
        st.text_area("📝 Último log:", value=bot_status['last_log'], height=100)
    
    # Señales recientes
    st.subheader("🎯 Señales Recientes")
    signals = dashboard.parse_log_signals()
    
    if signals:
        signals_df = pd.DataFrame(signals)
        
        # Crear gráfico de señales
        fig = go.Figure()
        
        for signal in signals:
            if signal['price']:
                color = 'green' if signal['signal'] == 'BUY' else 'red' if signal['signal'] == 'SELL' else 'gray'
                fig.add_trace(go.Scatter(
                    x=[signal['time']],
                    y=[signal['price']],
                    mode='markers',
                    marker=dict(color=color, size=10),
                    name=signal['signal'],
                    text=f"{signal['signal']} @ ${signal['price']:,.2f}",
                    hovertemplate="<b>%{text}</b><br>Tiempo: %{x}<extra></extra>"
                ))
        
        fig.update_layout(
            title="Señales de Trading en el Tiempo",
            xaxis_title="Tiempo",
            yaxis_title="Precio ($)",
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de señales
        st.dataframe(signals_df, use_container_width=True)
    else:
        st.info("📭 No hay señales recientes disponibles")
    
    # Logs detallados
    if show_logs:
        st.subheader("📋 Logs Detallados")
        try:
            log_file = dashboard.logs_path / "pro_bot.log"
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    logs = f.readlines()
                
                # Mostrar últimas 20 líneas
                recent_logs = ''.join(logs[-20:])
                st.text_area("📝 Logs recientes:", value=recent_logs, height=300)
        except Exception as e:
            st.error(f"Error leyendo logs: {e}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Pie de página
    st.markdown("---")
    st.markdown("🚀 **AlgoTrader v3.0** - Dashboard en tiempo real | Última actualización: " + datetime.now().strftime("%H:%M:%S"))

if __name__ == "__main__":
    main()