"""
Unified Professional Trading Dashboard with Real-time Data
Author: Trading Pro System
Version: 3.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
import json

# Configure page
st.set_page_config(
    page_title="Trading Pro Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS for professional look
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0;
    }

    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }

    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }

    .alert-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }

    .trading-signal {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }

    .signal-buy {
        background-color: #d4edda;
        border-left-color: #28a745;
    }

    .signal-sell {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }

    .signal-neutral {
        background-color: #e2e3e5;
        border-left-color: #6c757d;
    }

    .position-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2C3E50 0%, #34495E 100%);
    }

    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-online {
        background-color: #28a745;
    }

    .status-offline {
        background-color: #dc3545;
    }

    .status-warning {
        background-color: #ffc107;
    }
</style>
""", unsafe_allow_html=True)

class DashboardData:
    """Mock data generator for dashboard demo"""

    def __init__(self):
        self.current_time = datetime.now()
        self.account_balance = 50000
        self.initial_balance = 50000

    def get_account_metrics(self) -> Dict:
        """Get account performance metrics"""
        # Simulate account performance
        pnl_today = np.random.uniform(-500, 1000)
        total_pnl = self.account_balance - self.initial_balance + pnl_today

        return {
            'account_balance': self.account_balance + pnl_today,
            'daily_pnl': pnl_today,
            'total_pnl': total_pnl,
            'daily_return': pnl_today / self.account_balance * 100,
            'total_return': total_pnl / self.initial_balance * 100,
            'open_positions': np.random.randint(2, 8),
            'pending_orders': np.random.randint(0, 5),
            'win_rate': np.random.uniform(55, 75),
            'sharpe_ratio': np.random.uniform(1.2, 2.8),
            'max_drawdown': np.random.uniform(5, 15),
            'profit_factor': np.random.uniform(1.1, 2.5)
        }

    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        symbols = ['EURUSD', 'GBPUSD', 'BTCUSD', 'XAUUSD', 'USDJPY']
        positions = []

        for i in range(np.random.randint(3, 7)):
            symbol = np.random.choice(symbols)
            side = np.random.choice(['BUY', 'SELL'])
            entry_price = np.random.uniform(1.0, 2000.0)
            current_price = entry_price * (1 + np.random.uniform(-0.02, 0.02))
            quantity = np.random.uniform(0.1, 2.0)

            if side == 'BUY':
                pnl = (current_price - entry_price) * quantity * 1000
            else:
                pnl = (entry_price - current_price) * quantity * 1000

            positions.append({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl / (entry_price * quantity * 1000) * 100,
                'duration': f"{np.random.randint(10, 1440)} min",
                'stop_loss': entry_price * (0.98 if side == 'BUY' else 1.02),
                'take_profit': entry_price * (1.03 if side == 'BUY' else 0.97)
            })

        return positions

    def get_signals(self) -> List[Dict]:
        """Get recent trading signals"""
        symbols = ['EURUSD', 'GBPUSD', 'BTCUSD', 'XAUUSD', 'USDJPY']
        signals = []

        for i in range(np.random.randint(3, 8)):
            symbol = np.random.choice(symbols)
            signal_type = np.random.choice(['BUY', 'SELL', 'NEUTRAL'])
            confidence = np.random.uniform(60, 95)

            signals.append({
                'symbol': symbol,
                'signal': signal_type,
                'confidence': confidence,
                'price': np.random.uniform(1.0, 2000.0),
                'timestamp': datetime.now() - timedelta(minutes=np.random.randint(1, 60)),
                'strategy': np.random.choice(['AI_Hybrid', 'MA_Cross', 'RSI_Divergence']),
                'timeframe': np.random.choice(['5m', '15m', '1h']),
                'risk_reward': np.random.uniform(1.5, 3.0)
            })

        return sorted(signals, key=lambda x: x['timestamp'], reverse=True)

    def get_price_data(self, symbol: str = 'BTCUSD', days: int = 30) -> pd.DataFrame:
        """Generate mock price data"""
        dates = pd.date_range(end=datetime.now(), periods=days*24, freq='H')

        # Generate realistic OHLCV data
        base_price = 67000 if symbol == 'BTCUSD' else 1.1

        prices = []
        current_price = base_price

        for _ in dates:
            # Random walk with some trend
            change = np.random.normal(0, 0.02)
            current_price *= (1 + change)

            # OHLC around current price
            open_price = current_price * (1 + np.random.normal(0, 0.001))
            high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.005)))
            close_price = current_price
            volume = np.random.exponential(100000)

            prices.append({
                'timestamp': dates[len(prices)],
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })

        return pd.DataFrame(prices).set_index('timestamp')

    def get_equity_curve(self, days: int = 30) -> pd.DataFrame:
        """Generate equity curve data"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        equity = []
        current_equity = self.initial_balance

        for date in dates:
            # Random daily return
            daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean with 2% volatility
            current_equity *= (1 + daily_return)

            equity.append({
                'date': date,
                'equity': current_equity,
                'benchmark': self.initial_balance * (1 + 0.0003) ** (len(equity))  # 3% annual benchmark
            })

        return pd.DataFrame(equity).set_index('date')

    def get_system_status(self) -> Dict:
        """Get system health status"""
        return {
            'mt5_connection': np.random.choice(['online', 'offline'], p=[0.95, 0.05]),
            'data_feed': np.random.choice(['online', 'delayed', 'offline'], p=[0.9, 0.08, 0.02]),
            'ai_system': np.random.choice(['online', 'warning', 'offline'], p=[0.85, 0.12, 0.03]),
            'risk_manager': np.random.choice(['online', 'warning'], p=[0.95, 0.05]),
            'telegram_bot': np.random.choice(['online', 'offline'], p=[0.9, 0.1]),
            'last_signal': datetime.now() - timedelta(minutes=np.random.randint(1, 15)),
            'last_trade': datetime.now() - timedelta(minutes=np.random.randint(5, 120)),
            'system_uptime': f"{np.random.randint(1, 30)} days"
        }

# Initialize data source
if 'data_source' not in st.session_state:
    st.session_state.data_source = DashboardData()

def create_price_chart(data: pd.DataFrame, symbol: str) -> go.Figure:
    """Create candlestick chart with volume"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=[f'{symbol} Price', 'Volume'],
        row_width=[0.2, 0.7]
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name="Price"
        ),
        row=1, col=1
    )

    # Volume bars
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['volume'],
            name="Volume",
            marker_color='rgba(158,202,225,0.8)'
        ),
        row=2, col=1
    )

    # Add moving averages
    ma_20 = data['close'].rolling(20).mean()
    ma_50 = data['close'].rolling(50).mean()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=ma_20,
            name="MA 20",
            line=dict(color='orange', width=1)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=ma_50,
            name="MA 50",
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )

    fig.update_layout(
        title=f"{symbol} Price Chart",
        xaxis_rangeslider_visible=False,
        height=500,
        showlegend=True
    )

    return fig

def create_equity_curve(data: pd.DataFrame) -> go.Figure:
    """Create equity curve chart"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['equity'],
            mode='lines',
            name='Portfolio',
            line=dict(color='#2E8B57', width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['benchmark'],
            mode='lines',
            name='Benchmark',
            line=dict(color='#B22222', width=1, dash='dash')
        )
    )

    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        height=300,
        showlegend=True
    )

    return fig

def create_performance_metrics_chart(metrics: Dict) -> go.Figure:
    """Create performance metrics radar chart"""
    categories = ['Win Rate', 'Sharpe Ratio', 'Profit Factor', 'Recovery Factor']
    values = [
        metrics['win_rate'],
        metrics['sharpe_ratio'] * 20,  # Scale for visualization
        metrics['profit_factor'] * 25,
        (100 - metrics['max_drawdown'])  # Invert drawdown
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Performance'
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="Performance Radar",
        height=300
    )

    return fig

def main():
    """Main dashboard function"""

    # Header
    st.title("🚀 Trading Pro Dashboard")
    st.markdown("---")

    # Auto-refresh
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()

    # Auto-refresh every 30 seconds
    if st.sidebar.checkbox("Auto Refresh (30s)", value=True):
        time.sleep(30)
        st.rerun()

    # Get data
    data_source = st.session_state.data_source
    metrics = data_source.get_account_metrics()
    positions = data_source.get_positions()
    signals = data_source.get_signals()
    system_status = data_source.get_system_status()

    # Sidebar - System Status
    st.sidebar.markdown("## 🔧 System Status")

    status_colors = {'online': '🟢', 'warning': '🟡', 'offline': '🔴', 'delayed': '🟡'}

    for service, status in system_status.items():
        if service not in ['last_signal', 'last_trade', 'system_uptime']:
            color = status_colors.get(status, '⚪')
            st.sidebar.markdown(f"{color} **{service.replace('_', ' ').title()}**: {status.title()}")

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Last Signal**: {system_status['last_signal'].strftime('%H:%M:%S')}")
    st.sidebar.markdown(f"**Last Trade**: {system_status['last_trade'].strftime('%H:%M:%S')}")
    st.sidebar.markdown(f"**Uptime**: {system_status['system_uptime']}")

    # Main Dashboard Layout

    # Row 1: Key Metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-value">${metrics['account_balance']:,.0f}</p>
                <p class="metric-label">Account Balance</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        pnl_color = "green" if metrics['daily_pnl'] >= 0 else "red"
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-value" style="color: {pnl_color}">${metrics['daily_pnl']:+,.0f}</p>
                <p class="metric-label">Daily P&L</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-value">{metrics['daily_return']:+.1f}%</p>
                <p class="metric-label">Daily Return</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-value">{metrics['open_positions']}</p>
                <p class="metric-label">Open Positions</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-value">{metrics['win_rate']:.1f}%</p>
                <p class="metric-label">Win Rate</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col6:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-value">{metrics['sharpe_ratio']:.2f}</p>
                <p class="metric-label">Sharpe Ratio</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Row 2: Charts
    col1, col2 = st.columns([2, 1])

    with col1:
        # Price Chart
        symbol = st.selectbox("Select Symbol", ['BTCUSD', 'EURUSD', 'XAUUSD', 'GBPUSD'])
        price_data = data_source.get_price_data(symbol)
        price_chart = create_price_chart(price_data, symbol)
        st.plotly_chart(price_chart, use_container_width=True)

    with col2:
        # Equity Curve
        equity_data = data_source.get_equity_curve()
        equity_chart = create_equity_curve(equity_data)
        st.plotly_chart(equity_chart, use_container_width=True)

        # Performance Radar
        perf_chart = create_performance_metrics_chart(metrics)
        st.plotly_chart(perf_chart, use_container_width=True)

    st.markdown("---")

    # Row 3: Positions and Signals
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Open Positions")

        if positions:
            for pos in positions:
                pnl_color = "success" if pos['pnl'] >= 0 else "danger"
                side_emoji = "🟢" if pos['side'] == 'BUY' else "🔴"

                st.markdown(
                    f"""
                    <div class="position-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{side_emoji} {pos['symbol']} {pos['side']}</strong><br>
                                <small>Qty: {pos['quantity']:.2f} | Entry: {pos['entry_price']:.4f}</small>
                            </div>
                            <div style="text-align: right;">
                                <div style="color: {'green' if pos['pnl'] >= 0 else 'red'}; font-weight: bold;">
                                    ${pos['pnl']:+.2f}
                                </div>
                                <small>({pos['pnl_pct']:+.1f}%)</small>
                            </div>
                        </div>
                        <div style="margin-top: 8px; font-size: 0.8em; color: #666;">
                            Current: {pos['current_price']:.4f} | SL: {pos['stop_loss']:.4f} | TP: {pos['take_profit']:.4f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No open positions")

    with col2:
        st.subheader("🎯 Recent Signals")

        for signal in signals[:8]:  # Show last 8 signals
            signal_class = f"signal-{signal['signal'].lower()}"
            confidence_color = "green" if signal['confidence'] > 80 else "orange" if signal['confidence'] > 70 else "red"

            st.markdown(
                f"""
                <div class="trading-signal {signal_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{signal['symbol']} - {signal['signal']}</strong><br>
                            <small>{signal['strategy']} | {signal['timeframe']}</small>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: {confidence_color}; font-weight: bold;">
                                {signal['confidence']:.1f}%
                            </div>
                            <small>{signal['timestamp'].strftime('%H:%M')}</small>
                        </div>
                    </div>
                    <div style="margin-top: 4px; font-size: 0.8em;">
                        Price: {signal['price']:.4f} | R:R {signal['risk_reward']:.1f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Row 4: Advanced Metrics
    st.markdown("---")
    st.subheader("📈 Advanced Analytics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Return",
            f"{metrics['total_return']:+.1f}%",
            f"{metrics['daily_return']:+.1f}% today"
        )

    with col2:
        st.metric(
            "Profit Factor",
            f"{metrics['profit_factor']:.2f}",
            "1.0 = Breakeven"
        )

    with col3:
        st.metric(
            "Max Drawdown",
            f"{metrics['max_drawdown']:.1f}%",
            "Lower is better"
        )

    with col4:
        st.metric(
            "Pending Orders",
            f"{metrics['pending_orders']}",
            "Awaiting execution"
        )

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666; font-size: 0.8em;">
            Trading Pro Dashboard v3.0 | Last updated: {timestamp}
        </div>
        """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()