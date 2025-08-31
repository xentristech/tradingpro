"""
🎯 Algo Trader Dashboard v3.0
Dashboard profesional para monitoreo del sistema de trading
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import os
from pathlib import Path

# Configurar página
st.set_page_config(
    page_title="Algo Trader Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #363742;
    }
    .success-text {
        color: #00ff41;
    }
    .danger-text {
        color: #ff4b4b;
    }
    .warning-text {
        color: #ffa726;
    }
    div[data-testid="metric-container"] {
        background-color: #262730;
        border: 1px solid #363742;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 5
if 'equity_history' not in st.session_state:
    st.session_state.equity_history = []  # list of (timestamp, equity)

# Importar componentes del sistema
@st.cache_resource
def load_components():
    """Carga los componentes del sistema"""
    try:
        from utils.state_manager import StateManager
        from utils.mt5_connection import MT5ConnectionManager
        from utils.rate_limiter import RateLimiter
        from dotenv import load_dotenv
        
        load_dotenv('configs/.env')
        
        return {
            'state_manager': StateManager(),
            'mt5_manager': MT5ConnectionManager(),
            'rate_limiter': RateLimiter()
        }
    except Exception as e:
        st.error(f"Error cargando componentes: {e}")
        return None

def get_system_status(components):
    """Obtiene el estado actual del sistema"""
    if not components:
        return None
    
    try:
        health = components['state_manager'].get_health_status()
        stats = components['state_manager'].get_session_stats()
        
        # Calcular métricas adicionales
        uptime_seconds = health.get('uptime', 0)
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        
        win_rate = 0
        if stats.get('trades_total', 0) > 0:
            win_rate = (stats.get('trades_won', 0) / stats['trades_total']) * 100
        
        return {
            'status': health.get('trading_state', 'UNKNOWN'),
            'uptime': uptime_str,
            'cycles': health.get('cycles', 0),
            'positions_open': health.get('positions_open', 0),
            'errors': health.get('errors', 0),
            'critical_errors': health.get('critical_errors', 0),
            'trades_total': stats.get('trades_total', 0),
            'trades_won': stats.get('trades_won', 0),
            'trades_lost': stats.get('trades_lost', 0),
            'profit_total': stats.get('profit_total', 0),
            'win_rate': win_rate,
            'max_drawdown': stats.get('max_drawdown', 0)
        }
    except Exception as e:
        st.error(f"Error obteniendo estado: {e}")
        return None

def get_mt5_data(components):
    """Obtiene datos de MT5"""
    if not components or not components['mt5_manager']:
        return None
    
    try:
        if not components['mt5_manager'].is_connected():
            components['mt5_manager'].connect()
        
        account = components['mt5_manager'].get_account_info()
        if account:
            return {
                'connected': True,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free,
                'margin_level': account.margin_level if account.margin > 0 else 0,
                'profit': account.profit
            }
        return {'connected': False}
    except:
        return {'connected': False}

def get_positions_data(components):
    """Obtiene datos de posiciones abiertas"""
    if not components:
        return []
    
    try:
        positions = components['state_manager'].get_positions()
        rows = []
        for pos in positions.values():
            entry = pos.get('entry_price')
            sl = pos.get('sl') or 0
            tp = pos.get('tp') or 0
            rr = 0.0
            try:
                dist_sl = abs(entry - sl) if entry and sl else 0
                dist_tp = abs(tp - entry) if entry and tp else 0
                rr = (dist_tp / dist_sl) if dist_sl else 0.0
            except Exception:
                rr = 0.0
            rows.append({
                'Ticket': pos.get('ticket'),
                'Symbol': pos.get('symbol'),
                'Type': pos.get('type'),
                'Volume': pos.get('volume'),
                'Entry': entry,
                'Current': pos.get('current_price'),
                'SL': sl,
                'TP': tp,
                'R:R': round(rr, 2),
                'Profit': pos.get('profit', 0)
            })
        return rows
    except:
        return []

def get_recent_signals(components):
    """Obtiene señales recientes"""
    if not components:
        return []
    
    try:
        signals = components['state_manager'].get_recent_signals(20)
        return signals
    except:
        return []

def get_rate_limits(components):
    """Obtiene estado de rate limits"""
    if not components or not components['rate_limiter']:
        return {}
    
    try:
        stats = {}
        for api in ['twelvedata', 'ollama', 'telegram']:
            api_stats = components['rate_limiter'].get_stats(api)
            remaining = components['rate_limiter'].get_remaining_calls(api)
            stats[api] = {
                'total_calls': api_stats.get('total_calls', 0),
                'blocked_calls': api_stats.get('blocked_calls', 0),
                'remaining_minute': remaining.get('per_minute', 0),
                'remaining_hour': remaining.get('per_hour', 0)
            }
        return stats
    except:
        return {}

# MAIN DASHBOARD
def main():
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🤖 Algo Trader Dashboard v3.0")
    
    with col2:
        if st.button("🔄 Refresh", type="primary"):
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
    
    # Auto refresh
    if st.session_state.auto_refresh:
        time.sleep(st.session_state.refresh_interval)
        st.rerun()
    
    # Cargar componentes
    components = load_components()
    
    if not components:
        st.error("⚠️ No se pudieron cargar los componentes del sistema")
        st.stop()
    
    # Obtener datos
    system_status = get_system_status(components)
    mt5_data = get_mt5_data(components)
    positions = get_positions_data(components)
    rate_limits = get_rate_limits(components)
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview", 
        "💼 Positions", 
        "📈 Performance",
        "🎯 Signals",
        "🔒 Rate Limits",
        "⚙️ Settings",
        "📜 Closed Trades"
    ])
    
    # TAB 1: OVERVIEW
    with tab1:
        # Métricas principales
        st.subheader("📊 System Status")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_color = "🟢" if system_status['status'] == 'running' else "🔴"
            st.metric(
                "Status",
                f"{status_color} {system_status['status'].upper()}",
                delta=f"Uptime: {system_status['uptime']}"
            )
        
        with col2:
            st.metric(
                "Cycles",
                f"{system_status['cycles']:,}",
                delta=f"Errors: {system_status['errors']}"
            )
        
        with col3:
            st.metric(
                "Open Positions",
                system_status['positions_open'],
                delta=f"Total: {system_status['trades_total']}"
            )
        
        with col4:
            profit_color = "🟢" if system_status['profit_total'] >= 0 else "🔴"
            st.metric(
                "Total P&L",
                f"{profit_color} ${system_status['profit_total']:.2f}",
                delta=f"Win Rate: {system_status['win_rate']:.1f}%"
            )
        
        # MT5 Status
        st.subheader("🏦 Account Status")
        
        if mt5_data and mt5_data.get('connected'):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Balance", f"${mt5_data['balance']:.2f}")
            
            with col2:
                equity_delta = mt5_data['equity'] - mt5_data['balance']
                st.metric(
                    "Equity",
                    f"${mt5_data['equity']:.2f}",
                    delta=f"${equity_delta:+.2f}"
                )
            
            with col3:
                st.metric("Margin", f"${mt5_data['margin']:.2f}")
            
            with col4:
                margin_level = mt5_data['margin_level']
                level_color = "🟢" if margin_level > 200 else "🟡" if margin_level > 100 else "🔴"
                st.metric(
                    "Margin Level",
                    f"{level_color} {margin_level:.1f}%"
                )
        else:
            st.warning("⚠️ MT5 no conectado")

        # Gráfico de P&L
        st.subheader("📈 Profit & Loss Chart")
        
        # Simular datos para el gráfico (en producción vendría de la base de datos)
        hours = list(range(24))
        pnl_data = np.cumsum(np.random.randn(24) * 10)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours,
            y=pnl_data,
            mode='lines+markers',
            name='P&L',
            line=dict(color='#00ff41' if pnl_data[-1] > 0 else '#ff4b4b', width=2),
            fill='tonexty',
            fillcolor='rgba(0, 255, 65, 0.1)' if pnl_data[-1] > 0 else 'rgba(255, 75, 75, 0.1)'
        ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="24-Hour P&L",
            xaxis_title="Hour",
            yaxis_title="Profit/Loss ($)",
            height=400,
            template="plotly_dark",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Equity Curve (Live)
        st.subheader("📉 Equity Curve (Live)")
        try:
            from pathlib import Path as _Path
            eq_val = None
            if mt5_data and mt5_data.get('equity'):
                eq_val = float(mt5_data['equity'])
            # Cargar historial previo de disco si no está en memoria
            try:
                if not st.session_state.equity_history:
                    eqp = _Path('logs/equity_history.csv')
                    if eqp.exists():
                        df_eq = pd.read_csv(eqp)
                        # parse
                        if 'timestamp' in df_eq.columns and 'equity' in df_eq.columns:
                            ts = pd.to_datetime(df_eq['timestamp'], errors='coerce')
                            vals = pd.to_numeric(df_eq['equity'], errors='coerce')
                            st.session_state.equity_history = list(zip(ts.tolist(), vals.fillna(0).tolist()))
            except Exception:
                pass
            if eq_val is not None:
                st.session_state.equity_history.append((datetime.now(), eq_val))
                # Mantener últimos 500 puntos
                st.session_state.equity_history = st.session_state.equity_history[-500:]
                times = [t for t, _ in st.session_state.equity_history]
                values = [v for _, v in st.session_state.equity_history]
                fig_eq = go.Figure(go.Scatter(x=times, y=values, mode='lines', line=dict(color='#ffaa00', width=2)))
                fig_eq.update_layout(template='plotly_dark', height=300, xaxis_title='Time', yaxis_title='Equity ($)')
                st.plotly_chart(fig_eq, use_container_width=True)
                # Guardar a disco
                try:
                    os.makedirs('logs', exist_ok=True)
                    pd.DataFrame({'timestamp': times, 'equity': values}).to_csv('logs/equity_history.csv', index=False)
                except Exception:
                    pass
            else:
                st.info("Equity no disponible aún (requiere MT5 conectado)")
        except Exception as e:
            st.warning(f"No se pudo generar curva de equity: {e}")

        # IA Alerts (señales recientes con alta confianza)
        st.subheader("🧠 IA Alerts")
        try:
            recent_signals = get_recent_signals(components) or []
            if recent_signals:
                try:
                    min_conf = float(os.getenv('MIN_CONFIDENCE', '0.75'))
                except Exception:
                    min_conf = 0.75
                high_conf = [s for s in recent_signals if float(s.get('confidence', 0)) >= min_conf]
                if high_conf:
                    s0 = high_conf[-1]
                    msg = f"{s0.get('symbol','')} — {s0.get('signal','')} — Conf: {float(s0.get('confidence',0))*100:.1f}%"
                    st.success(f"Señal IA: {msg}")
                else:
                    st.info("No hay señales IA por encima del umbral de confianza")
            else:
                st.info("Sin señales recientes")
        except Exception as e:
            st.warning(f"No se pudieron evaluar IA alerts: {e}")

        # Gating alerts (últimos mensajes 'Gating:' del estado)
        st.subheader("🚧 Gating Alerts")
        try:
            # Acceder al estado interno para leer últimos errores
            errors = getattr(components['state_manager'], '_state', {}).get('errors', [])
            gating = [e for e in errors if isinstance(e, dict) and str(e.get('message','')).startswith('Gating:')]
            gating = gating[-5:]
            if gating:
                for g in gating[::-1]:
                    st.warning(g.get('message','Gating'))
            else:
                st.info('Sin alertas de gating recientes')
        except Exception as e:
            st.info('No hay información de gating')

        # Última orden (desde logs/trades.csv)
        st.subheader("🧾 Última Orden")
        try:
            import pandas as _pd
            from pathlib import Path as _Path
            tpath = _Path('logs/trades.csv')
            if tpath.exists():
                dfo = _pd.read_csv(tpath)
                if not dfo.empty:
                    row = dfo.iloc[-1]
                    cols = st.columns(4)
                    with cols[0]:
                        st.metric("Side/Symbol", f"{row.get('side','')} {row.get('symbol','')}")
                        st.metric("Ticket", f"{int(row.get('ticket', 0)) if str(row.get('ticket','')).isdigit() else row.get('ticket','-')}")
                    with cols[1]:
                        st.metric("Entry", f"{float(row.get('entry',0)):.5f}")
                        st.metric("Volume", f"{float(row.get('volume',0)):.2f}")
                    with cols[2]:
                        st.metric("SL", f"{float(row.get('sl',0)):.5f}")
                        st.metric("TP", f"{float(row.get('tp',0)):.5f}")
                    with cols[3]:
                        st.metric("R:R", f"{float(row.get('rr',0)):.2f}")
                        st.metric("Conf.", f"{float(row.get('confidence',0))*100:.1f}%")
                    # Detalles adicionales
                    with st.expander("Detalles de la orden"):
                        st.write(f"Timestamp: {row.get('timestamp','-')}")
                        reason = row.get('reason','')
                        if isinstance(reason, str) and reason.strip():
                            st.write(f"Reason: {reason}")
                        st.json(row.to_dict())
            else:
                st.info("No hay registros de aperturas aún (logs/trades.csv)")
        except Exception as e:
            st.warning(f"No se pudo leer última orden: {e}")
    
    # TAB 2: POSITIONS
    with tab2:
        st.subheader("💼 Open Positions")
        
        if positions:
            df_positions = pd.DataFrame(positions)
            
            # Colorear filas según profit
            def color_profit(val):
                if isinstance(val, (int, float)):
                    color = 'green' if val > 0 else 'red' if val < 0 else 'white'
                    return f'color: {color}'
                return ''
            
            styled_df = df_positions.style.applymap(
                color_profit,
                subset=['Profit']
            )
            
            st.dataframe(styled_df, use_container_width=True, height=400)

            # Download positions CSV
            try:
                csv_pos = df_positions.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Descargar posiciones (CSV)", data=csv_pos, file_name='open_positions.csv', mime='text/csv')
            except Exception:
                pass
            
            # Resumen de posiciones
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_volume = df_positions['Volume'].sum() if 'Volume' in df_positions else 0
                st.metric("Total Volume", f"{total_volume:.2f}")
            
            with col2:
                total_profit = df_positions['Profit'].sum() if 'Profit' in df_positions else 0
                st.metric("Total Profit", f"${total_profit:.2f}")
            
            with col3:
                avg_profit = df_positions['Profit'].mean() if 'Profit' in df_positions else 0
                st.metric("Avg Profit", f"${avg_profit:.2f}")
        else:
            st.info("📭 No hay posiciones abiertas")
    
    # TAB 3: PERFORMANCE
    with tab3:
        st.subheader("📈 Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Win/Loss Distribution
            fig = go.Figure(data=[
                go.Bar(name='Wins', x=['Trades'], y=[system_status['trades_won']], marker_color='#00ff41'),
                go.Bar(name='Losses', x=['Trades'], y=[system_status['trades_lost']], marker_color='#ff4b4b')
            ])
            
            fig.update_layout(
                title="Win/Loss Distribution",
                template="plotly_dark",
                height=300,
                barmode='stack'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Performance Metrics
            metrics_data = {
                'Metric': ['Win Rate', 'Total Trades', 'Max Drawdown', 'Profit Factor'],
                'Value': [
                    f"{system_status['win_rate']:.1f}%",
                    str(system_status['trades_total']),
                    f"${system_status['max_drawdown']:.2f}",
                    f"{(system_status['trades_won'] / max(system_status['trades_lost'], 1)):.2f}"
                ]
            }
            
            df_metrics = pd.DataFrame(metrics_data)
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("💹 Cumulative PnL (from closed trades)")
        try:
            import pandas as _pd
            from pathlib import Path as _Path
            cpath = _Path('logs/trades_closed.csv')
            if cpath.exists():
                dfc = _pd.read_csv(cpath)
                if not dfc.empty and 'pnl' in dfc.columns:
                    # Parse timestamp and sort
                    if 'timestamp' in dfc.columns:
                        dfc['timestamp'] = _pd.to_datetime(dfc['timestamp'], errors='coerce')
                        dfc = dfc.sort_values('timestamp')
                    # Selector de símbolo para PnL acumulado
                    sym_options = ['(Todos)']
                    if 'symbol' in dfc.columns:
                        sym_options += sorted([s for s in dfc['symbol'].dropna().unique().tolist()])
                    sel_sym = st.selectbox('Símbolo para PnL acumulado', options=sym_options, index=0)
                    dfc_plot = dfc.copy()
                    if sel_sym != '(Todos)' and 'symbol' in dfc_plot.columns:
                        dfc_plot = dfc_plot[dfc_plot['symbol'] == sel_sym]
                    # Ejes
                    if 'timestamp' in dfc_plot.columns and not dfc_plot['timestamp'].isna().all():
                        x = dfc_plot['timestamp']
                    else:
                        x = list(range(len(dfc_plot)))
                    y = _pd.to_numeric(dfc_plot['pnl'], errors='coerce').fillna(0).cumsum()
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(color='#00ccff', width=2)))
                    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
                    title_suffix = '' if sel_sym == '(Todos)' else f' — {sel_sym}'
                    fig2.update_layout(template='plotly_dark', height=350, xaxis_title='Time', yaxis_title='Cumulative PnL ($)', title=f"Cumulative PnL{title_suffix}")
                    st.plotly_chart(fig2, use_container_width=True)
                    # PnL por símbolo (barra) y Heatmap de R:R promedio por símbolo
                    st.markdown("### 📊 PnL por símbolo y R:R promedio")
                    try:
                        col_a, col_b = st.columns(2)
                        # PnL por símbolo
                        if 'symbol' in dfc.columns and 'pnl' in dfc.columns:
                            pnl_by_sym = dfc.groupby('symbol', dropna=True)['pnl'].sum().sort_values(ascending=False)
                            with col_a:
                                fig_bar = go.Figure(go.Bar(x=pnl_by_sym.index.tolist(), y=pnl_by_sym.values.tolist(), marker_color='#00cc88'))
                                fig_bar.update_layout(template='plotly_dark', height=320, xaxis_title='Symbol', yaxis_title='PnL Total ($)')
                                st.plotly_chart(fig_bar, use_container_width=True)
                        # Heatmap de R:R promedio por símbolo
                        if 'symbol' in dfc.columns and 'rr' in dfc.columns:
                            rr_avg = dfc.groupby('symbol', dropna=True)['rr'].mean()
                            # Convertir a matriz 2D simbólica (símbolos como filas, una columna RR)
                            z = [[float(rr_avg.get(sym, 0.0))] for sym in rr_avg.index.tolist()]
                            with col_b:
                                fig_hm = go.Figure(data=go.Heatmap(
                                    z=z,
                                    x=['R:R'],
                                    y=rr_avg.index.tolist(),
                                    colorscale='Viridis'))
                                fig_hm.update_layout(template='plotly_dark', height=320)
                                st.plotly_chart(fig_hm, use_container_width=True)

                        # Distribución de cierres (TP/SL/MANUAL)
                        if 'hit' in dfc.columns:
                            st.markdown("### 🥧 Distribución de cierres (TP/SL/MANUAL)")
                            counts = dfc['hit'].fillna('MANUAL').value_counts()
                            if not counts.empty:
                                import plotly.express as px
                                fig_pie = px.pie(values=counts.values.tolist(), names=counts.index.tolist(), hole=0.3, color_discrete_sequence=px.colors.sequential.Blues)
                                fig_pie.update_layout(template='plotly_dark', height=320)
                                st.plotly_chart(fig_pie, use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pudieron generar gráficos por símbolo: {e}")
            else:
                st.info("No hay trades cerrados aún (logs/trades_closed.csv)")
        except Exception as e:
            st.error(f"Error generando gráfico de PnL: {e}")
    
    # TAB 4: SIGNALS
    with tab4:
        st.subheader("🎯 Recent Signals")
        
        signals = get_recent_signals(components)
        
        if signals:
            # Selector de timeframe para Entry estimado
            tfs_list = os.getenv('TIMEFRAMES', '5min,15min,1h').split(',')
            tfs_list = [tf.strip() for tf in tfs_list if tf.strip()]
            sel_tf = st.selectbox('Timeframe para Entry estimado', options=tfs_list, index=0)
            for signal in signals[:10]:  # Mostrar últimas 10 señales
                timestamp = signal.get('timestamp', 'N/A')
                symbol = signal.get('symbol', 'N/A')
                signal_type = signal.get('signal', 'N/A')
                confidence = signal.get('confidence', 0)
                
                # Color según tipo de señal
                if signal_type == 'BUY':
                    color = "🟢"
                elif signal_type == 'SELL':
                    color = "🔴"
                else:
                    color = "⚪"
                
                with st.expander(f"{color} {timestamp} - {symbol} - {signal_type}"):
                    st.write(f"**Confidence:** {confidence:.1%}")
                    setup = signal.get('setup', {}) or {}
                    if setup:
                        sl = setup.get('sl') or 0
                        tp = setup.get('tp') or 0
                        # Precio estimado: si hay market_data en estado
                        entry = None
                        try:
                            md = components['state_manager'].get_market_data(symbol) or {}
                            feats = (md.get('features') or {})
                            p = feats.get(sel_tf, {}).get('price', 0)
                            entry = p
                        except Exception:
                            entry = None
                        dist_sl = abs((entry or 0) - sl) if sl and entry else 0
                        dist_tp = abs(tp - (entry or 0)) if tp and entry else 0
                        rr = (dist_tp / dist_sl) if dist_sl else 0
                        cols = st.columns(4)
                        cols[0].metric("SL", f"{sl:.5f}" if sl else "-", delta=(f"Δ {dist_sl:.5f}" if dist_sl else None))
                        cols[1].metric("TP", f"{tp:.5f}" if tp else "-", delta=(f"Δ {dist_tp:.5f}" if dist_tp else None))
                        cols[2].metric("R:R", f"{rr:.2f}")
                        cols[3].metric("Entry", f"{(entry or 0):.5f}")
                    else:
                        st.write("Sin setup de SL/TP")
            # Download openings CSV if available
            import pandas as _pd
            from pathlib import Path as _Path
            o_path = _Path('logs/trades.csv')
            if o_path.exists():
                try:
                    df_open = _pd.read_csv(o_path)
                    csv_open = df_open.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Descargar aperturas (CSV)", data=csv_open, file_name='trades_open.csv', mime='text/csv')
                except Exception:
                    pass
        else:
            st.info("📭 No hay señales recientes")
    
    # TAB 5: RATE LIMITS
    with tab5:
        st.subheader("🔒 API Rate Limits")
        
        if rate_limits:
            for api_name, limits in rate_limits.items():
                with st.expander(f"📡 {api_name.upper()}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Calls", limits['total_calls'])
                    
                    with col2:
                        st.metric("Blocked", limits['blocked_calls'])
                    
                    with col3:
                        st.metric("Remaining/Min", limits['remaining_minute'])
                    
                    with col4:
                        st.metric("Remaining/Hr", limits['remaining_hour'])
                    
                    # Progress bar para límite por minuto
                    if limits['remaining_minute'] > 0:
                        progress = limits['remaining_minute'] / 10  # Asumiendo 10 calls/min max
                        st.progress(min(progress, 1.0))
        else:
            st.info("No hay información de rate limits disponible")
    
    # TAB 6: SETTINGS
    with tab6:
        st.subheader("⚙️ Dashboard Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Auto Refresh")
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=1,
                max_value=60,
                value=st.session_state.refresh_interval
            )
            st.session_state.refresh_interval = refresh_interval
            
            st.markdown("### Display Options")
            show_charts = st.checkbox("Show Charts", value=True)
            show_metrics = st.checkbox("Show Metrics", value=True)
            dark_mode = st.checkbox("Dark Mode", value=True)
        
        with col2:
            st.markdown("### System Actions")
            
            if st.button("🔍 Run Health Check", type="secondary"):
                with st.spinner("Running health check..."):
                    os.system("python health_check.py")
                st.success("Health check completed")

        st.markdown("---")
        st.subheader("🧾 Export Trade Journal")
        try:
            import pandas as _pd
            from io import BytesIO as _BytesIO
            from pathlib import Path as _Path
            # Load data
            pos_rows = get_positions_data(components) or []
            df_pos = _pd.DataFrame(pos_rows)
            df_open = _pd.read_csv(_Path('logs/trades.csv')) if _Path('logs/trades.csv').exists() else _pd.DataFrame()
            df_closed = _pd.read_csv(_Path('logs/trades_closed.csv')) if _Path('logs/trades_closed.csv').exists() else _pd.DataFrame()

            # Build XLSX in-memory
            buf = _BytesIO()
            with _pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                if not df_pos.empty:
                    df_pos.to_excel(writer, index=False, sheet_name='OpenPositions')
                if not df_open.empty:
                    df_open.to_excel(writer, index=False, sheet_name='Openings')
                if not df_closed.empty:
                    df_closed.to_excel(writer, index=False, sheet_name='ClosedTrades')
                # Summary sheet
                try:
                    summary = []
                    if not df_closed.empty:
                        pnl_total = float(_pd.to_numeric(df_closed.get('pnl', 0), errors='coerce').fillna(0).sum())
                        rr_avg = float(_pd.to_numeric(df_closed.get('rr', 0), errors='coerce').fillna(0).mean())
                        summary.append({'metric': 'PnL Total', 'value': pnl_total})
                        summary.append({'metric': 'R:R Promedio', 'value': rr_avg})
                    if not df_open.empty:
                        conf_avg = float(_pd.to_numeric(df_open.get('confidence', 0), errors='coerce').fillna(0).mean())
                        summary.append({'metric': 'Confianza media (aperturas)', 'value': conf_avg})
                    if not df_pos.empty:
                        summary.append({'metric': 'Posiciones abiertas', 'value': int(len(df_pos))})
                    if summary:
                        _pd.DataFrame(summary).to_excel(writer, index=False, sheet_name='Summary')
                except Exception:
                    pass
            buf.seek(0)
            st.download_button(
                "⬇️ Exportar Trade Journal (XLSX)",
                data=buf,
                file_name='trade_journal.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            # JSONL export
            try:
                import json as _json
                jsonl_lines = []
                if not df_open.empty:
                    for r in df_open.to_dict(orient='records'):
                        r['_type'] = 'opening'
                        jsonl_lines.append(_json.dumps(r, ensure_ascii=False))
                if not df_closed.empty:
                    for r in df_closed.to_dict(orient='records'):
                        r['_type'] = 'closed'
                        jsonl_lines.append(_json.dumps(r, ensure_ascii=False))
                if not df_pos.empty:
                    for r in df_pos.to_dict(orient='records'):
                        r['_type'] = 'open_position'
                        jsonl_lines.append(_json.dumps(r, ensure_ascii=False))
                if jsonl_lines:
                    st.download_button(
                        "⬇️ Exportar Journal (JSONL)",
                        data=("\n".join(jsonl_lines)).encode('utf-8'),
                        file_name='trade_journal.jsonl',
                        mime='application/json'
                    )
            except Exception:
                pass
        except Exception as e:
            st.error(f"Error generando export: {e}")

    # TAB 7: CLOSED TRADES (from CSV)
    with tab7:
        st.subheader("📜 Closed Trades Log")
        import pandas as _pd
        from pathlib import Path as _Path
        csv_path = _Path('logs/trades_closed.csv')
        if not csv_path.exists():
            st.info("No hay registros aún (logs/trades_closed.csv)")
        else:
            try:
                df = _pd.read_csv(csv_path)
                # Parse timestamp to datetime
                if 'timestamp' in df.columns:
                    df['timestamp'] = _pd.to_datetime(df['timestamp'], errors='coerce')
                # Filters
                cols = st.columns(4)
                with cols[0]:
                    symbols = sorted(df['symbol'].dropna().unique().tolist()) if 'symbol' in df.columns else []
                    sel_symbol = st.selectbox("Símbolo", options=["(Todos)"] + symbols, index=0)
                with cols[1]:
                    min_date = df['timestamp'].min() if 'timestamp' in df.columns else None
                    max_date = df['timestamp'].max() if 'timestamp' in df.columns else None
                    date_range = st.date_input("Rango de fechas", value=(min_date.date() if min_date else None, max_date.date() if max_date else None)) if min_date is not None else None
                with cols[2]:
                    side_opt = st.selectbox("Lado", options=["(Ambos)", "BUY", "SELL"], index=0)
                with cols[3]:
                    hit_opt = st.selectbox("Cierre por", options=["(Todos)", "TP", "SL", "MANUAL"], index=0)

                # Apply filters
                fdf = df.copy()
                if sel_symbol != "(Todos)" and 'symbol' in fdf.columns:
                    fdf = fdf[fdf['symbol'] == sel_symbol]
                if side_opt != "(Ambos)" and 'side' in fdf.columns:
                    fdf = fdf[fdf['side'] == side_opt]
                if hit_opt != "(Todos)" and 'hit' in fdf.columns:
                    fdf = fdf[fdf['hit'] == hit_opt]
                if date_range and 'timestamp' in fdf.columns and not fdf['timestamp'].isna().all():
                    try:
                        start, end = date_range
                        if start and end:
                            fdf = fdf[(fdf['timestamp'] >= _pd.Timestamp(start)) & (fdf['timestamp'] <= _pd.Timestamp(end) + _pd.Timedelta(days=1))]
                    except Exception:
                        pass

                # Summary metrics
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Trades", f"{len(fdf):,}")
                with c2:
                    pnl = fdf['pnl'].sum() if 'pnl' in fdf.columns else 0
                    st.metric("PnL Total", f"${pnl:.2f}")
                with c3:
                    rr_avg = fdf['rr'].replace([_pd.NA, _pd.NaT], 0).astype(float).mean() if 'rr' in fdf.columns else 0
                    st.metric("R:R Promedio", f"{rr_avg:.2f}")
                with c4:
                    dur = fdf['duration_min'].replace([_pd.NA, _pd.NaT], 0).astype(float).mean() if 'duration_min' in fdf.columns else 0
                    st.metric("Duración Promedio (min)", f"{dur:.1f}")

                st.dataframe(fdf, use_container_width=True, height=420)

                # Download buttons
                st.markdown("### Download")
                try:
                    csv_all = df.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Descargar CSV (completo)", data=csv_all, file_name='trades_closed.csv', mime='text/csv')
                except Exception:
                    pass
                try:
                    csv_filtered = fdf.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Descargar CSV (filtrado)", data=csv_filtered, file_name='trades_closed_filtered.csv', mime='text/csv')
                except Exception:
                    pass
            except Exception as e:
                st.error(f"Error leyendo CSV: {e}")
            
            if st.button("📊 Export Data", type="secondary"):
                # Exportar datos a CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_data = {
                    'system_status': system_status,
                    'mt5_data': mt5_data,
                    'positions': positions,
                    'rate_limits': rate_limits
                }
                
                export_file = f"exports/dashboard_export_{timestamp}.json"
                os.makedirs("exports", exist_ok=True)
                
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                st.success(f"Data exported to {export_file}")
            
            if st.button("🔄 Restart System", type="secondary"):
                st.warning("System restart requested")
                # Aquí iría la lógica para reiniciar el sistema
    
    # Footer
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🤖 Algo Trader v3.0")
    
    with col2:
        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    
    with col3:
        mode = os.getenv('LIVE_TRADING', 'false')
        mode_text = "🔴 LIVE" if mode == 'true' else "🟢 DEMO"
        st.caption(f"Mode: {mode_text}")

if __name__ == "__main__":
    main()
