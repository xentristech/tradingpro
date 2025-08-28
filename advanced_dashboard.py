"""
Advanced Trading Dashboard - Panel de Control Avanzado
Dashboard completo para múltiples cuentas con análisis en tiempo real
Version: 3.0.0
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import MetaTrader5 as mt5
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configurar path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv('configs/.env')

# Configurar página
st.set_page_config(
    page_title="AlgoTrader Advanced Dashboard",
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
        color: #1f77b4;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .account-header {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        margin: 1rem 0;
    }
    .position-card {
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        background: #f8f9fa;
    }
    .danger-alert {
        background: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: bold;
    }
    .success-alert {
        background: #44ff44;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

class AdvancedDashboard:
    """Dashboard avanzado para trading multi-cuenta"""
    
    def __init__(self):
        self.accounts_config = {
            'Ava Real': {'login': 89390972, 'server': 'Ava-Real 1-MT5'},
            'Exness Trial': {'login': 197678662, 'server': 'Exness-MT5Trial11'}
        }
        self.refresh_interval = 30  # segundos
        
    def run(self):
        """Ejecuta el dashboard principal"""
        # Header principal
        st.markdown('<div class="main-header">🚀 AlgoTrader Advanced Dashboard v3.0</div>', 
                   unsafe_allow_html=True)
        
        # Sidebar
        self._render_sidebar()
        
        # Auto-refresh
        if st.session_state.get('auto_refresh', True):
            st.rerun()
        
        # Contenido principal
        self._render_main_content()
    
    def _render_sidebar(self):
        """Renderiza la barra lateral"""
        with st.sidebar:
            st.markdown("## ⚙️ Control Panel")
            
            # Controles de actualización
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            with col2:
                auto_refresh = st.checkbox("🔁 Auto", value=True)
                st.session_state.auto_refresh = auto_refresh
            
            st.markdown("---")
            
            # Estado del sistema
            st.markdown("### [SYSTEM] Status")
            
            # Verificar conexiones MT5
            mt5_status = self._check_mt5_status()
            if mt5_status['connected']:
                st.success(f"[OK] MT5 Connected")
                st.info(f"Account: {mt5_status['account']}")
                st.info(f"Balance: ${mt5_status['balance']:.2f}")
            else:
                st.error("[ERROR] MT5 Disconnected")
            
            st.markdown("---")
            
            # Configuraciones
            st.markdown("### ⚙️ Settings")
            
            show_charts = st.checkbox("Show Charts", value=True)
            show_history = st.checkbox("📋 Show History", value=True)
            show_analysis = st.checkbox("🔍 Show Analysis", value=True)
            
            # Filtros
            st.markdown("### 🎛️ Filters")
            time_filter = st.selectbox("Time Range", 
                                     ["Last Hour", "Last 4 Hours", "Today", "Last 7 Days"])
            
            symbols_filter = st.multiselect("Symbols", 
                                          ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "XAUUSD"],
                                          default=["BTCUSD", "EURUSD"])
            
            st.session_state.update({
                'show_charts': show_charts,
                'show_history': show_history,
                'show_analysis': show_analysis,
                'time_filter': time_filter,
                'symbols_filter': symbols_filter
            })
    
    def _check_mt5_status(self):
        """Verifica el estado de MT5"""
        try:
            if mt5.initialize():
                account = mt5.account_info()
                if account:
                    return {
                        'connected': True,
                        'account': account.login,
                        'balance': account.balance,
                        'equity': account.equity,
                        'server': account.server
                    }
                else:
                    mt5.shutdown()
                    return {'connected': False}
            else:
                return {'connected': False}
        except:
            return {'connected': False}
    
    def _render_main_content(self):
        """Renderiza el contenido principal"""
        # Obtener datos
        accounts_data = self._get_accounts_data()
        
        # KPIs principales
        self._render_kpis(accounts_data)
        
        # Alertas de riesgo
        self._render_risk_alerts(accounts_data)
        
        # Análisis por cuenta
        for account_name, data in accounts_data.items():
            self._render_account_section(account_name, data)
        
        # Análisis consolidado
        if st.session_state.get('show_analysis', True):
            self._render_consolidated_analysis(accounts_data)
        
        # Gráficos avanzados
        if st.session_state.get('show_charts', True):
            self._render_advanced_charts(accounts_data)
        
        # Historial de operaciones
        if st.session_state.get('show_history', True):
            self._render_trading_history()
    
    def _get_accounts_data(self):
        """Obtiene datos de todas las cuentas"""
        accounts_data = {}
        
        for account_name, config in self.accounts_config.items():
            try:
                # Conectar a MT5
                if not mt5.initialize():
                    continue
                
                account_info = mt5.account_info()
                positions = mt5.positions_get()
                
                if account_info:
                    # Calcular métricas
                    total_profit = sum(pos.profit for pos in positions) if positions else 0
                    positions_without_sl = sum(1 for pos in positions if pos.sl == 0) if positions else 0
                    positions_without_tp = sum(1 for pos in positions if pos.tp == 0) if positions else 0
                    
                    accounts_data[account_name] = {
                        'info': account_info,
                        'positions': positions if positions else [],
                        'total_positions': len(positions) if positions else 0,
                        'total_profit': total_profit,
                        'positions_without_sl': positions_without_sl,
                        'positions_without_tp': positions_without_tp,
                        'risk_level': self._calculate_risk_level(positions, account_info),
                        'status': 'Connected'
                    }
                else:
                    accounts_data[account_name] = {
                        'status': 'Disconnected',
                        'total_positions': 0,
                        'total_profit': 0,
                        'positions_without_sl': 0,
                        'positions_without_tp': 0,
                        'risk_level': 0
                    }
                
            except Exception as e:
                accounts_data[account_name] = {
                    'status': f'Error: {str(e)}',
                    'total_positions': 0,
                    'total_profit': 0,
                    'positions_without_sl': 0,
                    'positions_without_tp': 0,
                    'risk_level': 0
                }
        
        return accounts_data
    
    def _calculate_risk_level(self, positions, account_info):
        """Calcula el nivel de riesgo de la cuenta"""
        if not positions or not account_info:
            return 0
        
        total_risk = 0
        for pos in positions:
            if pos.sl != 0:
                # Calcular riesgo basado en SL
                risk = abs(pos.price_open - pos.sl) * pos.volume * 100000
                total_risk += risk
            else:
                # Sin SL = riesgo alto (estimado)
                total_risk += pos.volume * 100000 * 0.02  # 2% del nominal
        
        risk_percentage = (total_risk / account_info.equity) * 100 if account_info.equity > 0 else 0
        return min(risk_percentage, 100)
    
    def _render_kpis(self, accounts_data):
        """Renderiza KPIs principales"""
        st.markdown("## Key Performance Indicators")
        
        # Calcular métricas consolidadas
        total_balance = 0
        total_equity = 0
        total_positions = 0
        total_profit = 0
        total_risk_positions = 0
        
        for data in accounts_data.values():
            # Siempre es un diccionario según _get_accounts_data()
            if isinstance(data, dict):
                info = data.get('info')
                if info and hasattr(info, 'balance'):
                    total_balance += info.balance
                    total_equity += info.equity
                total_positions += data.get('total_positions', 0)
                total_profit += data.get('total_profit', 0)
                total_risk_positions += data.get('positions_without_sl', 0) + data.get('positions_without_tp', 0)
        
        # Mostrar KPIs
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total Balance",
                value=f"${total_balance:.2f}",
                delta=f"${total_equity - total_balance:.2f}"
            )
        
        with col2:
            st.metric(
                label="Total Equity",
                value=f"${total_equity:.2f}",
                delta=f"{((total_equity/total_balance - 1)*100) if total_balance > 0 else 0:.2f}%"
            )
        
        with col3:
            st.metric(
                label="Open Positions",
                value=str(total_positions),
                delta=f"{len(accounts_data)} accounts"
            )
        
        with col4:
            profit_color = "normal" if total_profit >= 0 else "inverse"
            st.metric(
                label="💹 Total P&L",
                value=f"${total_profit:.2f}",
                delta=f"{'▲' if total_profit >= 0 else '▼'} {abs(total_profit):.2f}",
                delta_color=profit_color
            )
        
        with col5:
            risk_color = "inverse" if total_risk_positions > 0 else "normal"
            st.metric(
                label="Risk Positions",
                value=str(total_risk_positions),
                delta="No SL/TP" if total_risk_positions > 0 else "Protected",
                delta_color=risk_color
            )
    
    def _render_risk_alerts(self, accounts_data):
        """Renderiza alertas de riesgo"""
        st.markdown("## Risk Alerts")
        
        alerts = []
        
        for account_name, data in accounts_data.items():
            if data.get('positions_without_sl', 0) > 0:
                alerts.append({
                    'type': 'danger',
                    'message': f"[ALERT] {account_name}: {data['positions_without_sl']} positions without Stop Loss"
                })
            
            if data.get('positions_without_tp', 0) > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f"[WARNING] {account_name}: {data['positions_without_tp']} positions without Take Profit"
                })
            
            if data.get('risk_level', 0) > 10:
                alerts.append({
                    'type': 'danger',
                    'message': f"[DANGER] {account_name}: High risk level {data['risk_level']:.1f}%"
                })
        
        if alerts:
            for alert in alerts:
                if alert['type'] == 'danger':
                    st.error(alert['message'])
                else:
                    st.warning(alert['message'])
        else:
            st.success("[OK] No critical risk alerts")
    
    def _render_account_section(self, account_name, data):
        """Renderiza sección de cuenta específica"""
        st.markdown(f"## [{account_name.upper()}] Account Details")
        
        if data.get('status') != 'Connected':
            st.error(f"[ERROR] {account_name}: {data.get('status', 'Unknown')}")
            return
        
        account_info = data.get('info')
        positions = data.get('positions', [])
        
        # Información de cuenta
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Account", str(account_info.login))
        with col2:
            st.metric("Balance", f"${account_info.balance:.2f}")
        with col3:
            st.metric("Equity", f"${account_info.equity:.2f}")
        with col4:
            st.metric("Free Margin", f"${account_info.margin_free:.2f}")
        
        # Posiciones
        if positions:
            st.markdown("### Open Positions")
            
            positions_df = []
            for pos in positions:
                sl_status = "OK" if pos.sl != 0 else "NO"
                tp_status = "OK" if pos.tp != 0 else "NO"
                
                positions_df.append({
                    'Ticket': pos.ticket,
                    'Symbol': pos.symbol,
                    'Type': 'BUY' if pos.type == 0 else 'SELL',
                    'Volume': pos.volume,
                    'Open Price': f"{pos.price_open:.5f}",
                    'Current Price': f"{pos.price_current:.5f}",
                    'P&L': f"${pos.profit:.2f}",
                    'SL': f"{pos.sl:.5f}" if pos.sl != 0 else "None",
                    'TP': f"{pos.tp:.5f}" if pos.tp != 0 else "None",
                    'SL Status': sl_status,
                    'TP Status': tp_status,
                    'Time': datetime.fromtimestamp(pos.time).strftime('%H:%M:%S')
                })
            
            df = pd.DataFrame(positions_df)
            st.dataframe(df, use_container_width=True)
            
            # Gráfico de P&L por posición
            fig = px.bar(df, x='Ticket', y='P&L', color='Type',
                        title=f"{account_name} - P&L by Position",
                        color_discrete_map={'BUY': '#2ecc71', 'SELL': '#e74c3c'})
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("No open positions")
    
    def _render_consolidated_analysis(self, accounts_data):
        """Renderiza análisis consolidado"""
        st.markdown("## 🔍 Consolidated Analysis")
        
        # Crear tabs para diferentes análisis
        tab1, tab2, tab3, tab4 = st.tabs(["Portfolio", "Risk", "Performance", "Exposure"])
        
        with tab1:
            self._render_portfolio_analysis(accounts_data)
        
        with tab2:
            self._render_risk_analysis(accounts_data)
        
        with tab3:
            self._render_performance_analysis(accounts_data)
        
        with tab4:
            self._render_exposure_analysis(accounts_data)
    
    def _render_portfolio_analysis(self, accounts_data):
        """Análisis de portfolio"""
        st.markdown("### Portfolio Distribution")
        
        # Distribución por cuenta
        balances = []
        for account_name, data in accounts_data.items():
            if data.get('status') == 'Connected':
                balances.append({
                    'Account': account_name,
                    'Balance': data.get('info', {}).get('balance', 0),
                    'Equity': data.get('info', {}).get('equity', 0)
                })
        
        if balances:
            df = pd.DataFrame(balances)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(df, values='Balance', names='Account', title="Balance Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(df, x='Account', y=['Balance', 'Equity'], 
                           title="Balance vs Equity", barmode='group')
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_risk_analysis(self, accounts_data):
        """Análisis de riesgo"""
        st.markdown("### Risk Assessment")
        
        risk_data = []
        for account_name, data in accounts_data.items():
            if data.get('status') == 'Connected':
                risk_data.append({
                    'Account': account_name,
                    'Risk Level': data.get('risk_level', 0),
                    'Positions w/o SL': data.get('positions_without_sl', 0),
                    'Positions w/o TP': data.get('positions_without_tp', 0),
                    'Total Positions': data.get('total_positions', 0)
                })
        
        if risk_data:
            df = pd.DataFrame(risk_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(df, x='Account', y='Risk Level', 
                           title="Risk Level by Account (%)",
                           color='Risk Level',
                           color_continuous_scale='Reds')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(df, x='Account', 
                           y=['Positions w/o SL', 'Positions w/o TP'],
                           title="Unprotected Positions",
                           barmode='group',
                           color_discrete_map={
                               'Positions w/o SL': '#e74c3c',
                               'Positions w/o TP': '#f39c12'
                           })
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_performance_analysis(self, accounts_data):
        """Análisis de rendimiento"""
        st.markdown("### Performance Analysis")
        
        performance_data = []
        for account_name, data in accounts_data.items():
            if data.get('status') == 'Connected':
                info = data.get('info', {})
                balance = info.get('balance', 0)
                equity = info.get('equity', 0)
                profit = data.get('total_profit', 0)
                
                performance_data.append({
                    'Account': account_name,
                    'Total P&L': profit,
                    'P&L %': (profit / balance * 100) if balance > 0 else 0,
                    'Equity %': ((equity - balance) / balance * 100) if balance > 0 else 0
                })
        
        if performance_data:
            df = pd.DataFrame(performance_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(df, x='Account', y='Total P&L',
                           title="Absolute P&L by Account",
                           color='Total P&L',
                           color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(df, x='P&L %', y='Equity %', 
                               size='Total P&L', color='Account',
                               title="P&L vs Equity Performance (%)")
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_exposure_analysis(self, accounts_data):
        """Análisis de exposición"""
        st.markdown("### Market Exposure")
        
        exposure_data = {}
        
        for account_name, data in accounts_data.items():
            if data.get('status') == 'Connected':
                positions = data.get('positions', [])
                for pos in positions:
                    symbol = pos.symbol
                    volume = pos.volume
                    
                    if symbol not in exposure_data:
                        exposure_data[symbol] = {'Total Volume': 0, 'Positions': 0, 'Accounts': set()}
                    
                    exposure_data[symbol]['Total Volume'] += volume
                    exposure_data[symbol]['Positions'] += 1
                    exposure_data[symbol]['Accounts'].add(account_name)
        
        if exposure_data:
            df = pd.DataFrame([
                {
                    'Symbol': symbol,
                    'Total Volume': data['Total Volume'],
                    'Positions': data['Positions'],
                    'Accounts': len(data['Accounts'])
                }
                for symbol, data in exposure_data.items()
            ])
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(df, values='Total Volume', names='Symbol', 
                           title="Volume Distribution by Symbol")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(df, x='Symbol', y='Positions',
                           title="Number of Positions by Symbol")
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_advanced_charts(self, accounts_data):
        """Renderiza gráficos avanzados"""
        st.markdown("## Advanced Charts")
        
        # Aquí se pueden agregar gráficos de precios en tiempo real
        st.info("[INFO] Real-time price charts will be implemented with live data feeds")
    
    def _render_trading_history(self):
        """Renderiza historial de trading"""
        st.markdown("## 📋 Trading History")
        
        try:
            # Obtener historial de deals
            deals = mt5.history_deals_get(datetime.now() - timedelta(days=7), datetime.now())
            
            if deals:
                deals_df = []
                for deal in deals:
                    deals_df.append({
                        'Ticket': deal.ticket,
                        'Time': datetime.fromtimestamp(deal.time),
                        'Symbol': deal.symbol,
                        'Type': 'BUY' if deal.type == 0 else 'SELL',
                        'Volume': deal.volume,
                        'Price': deal.price,
                        'Profit': deal.profit,
                        'Comment': deal.comment
                    })
                
                df = pd.DataFrame(deals_df)
                st.dataframe(df, use_container_width=True)
                
                # Gráfico de profit over time
                if not df.empty:
                    fig = px.line(df, x='Time', y='Profit', 
                                title="Profit Over Time",
                                markers=True)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trading history available")
                
        except Exception as e:
            st.error(f"Error loading trading history: {str(e)}")

# Función principal
def main():
    """Función principal del dashboard"""
    dashboard = AdvancedDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()