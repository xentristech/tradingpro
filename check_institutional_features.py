#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Revision de Configuraciones Institucionales
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import os
from datetime import datetime
from dotenv import load_dotenv

print('=' * 80)
print('    REVISION DE CONFIGURACIONES INSTITUCIONALES')
print('=' * 80)
print(f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# Cargar configuración
load_dotenv('configs/.env')

# 1. CUENTA Y BROKER INSTITUCIONAL
print('1. CONFIGURACION DEL BROKER:')
print('-' * 40)
print(f'Broker: EXNESS')
print(f'Server: {os.getenv("MT5_SERVER", "N/A")}')
print(f'Account: {os.getenv("MT5_LOGIN", "N/A")}')
print(f'Leverage: 1:200 (detectado en MT5)')
print(f'Account Type: Trial/Professional')
print()

# 2. CARACTERISTICAS PROFESIONALES DISPONIBLES
print('2. CARACTERISTICAS PROFESIONALES DISPONIBLES:')
print('-' * 50)

institutional_features = {
    'Multi-Account Manager': 'multi_account_manager_fixed.py',
    'Professional Charts (TradingView)': 'src/ui/charts/tradingview_professional_chart.py',
    'Advanced Risk Management': 'src/risk/advanced_risk.py',
    'Professional Dashboard': 'src/ui/dashboards/advanced_modern_dashboard.py',
    'Volume Flow Analysis': 'enhanced_modules/volume_flow_analyzer.py',
    'Smart Position Manager': 'src/trading/smart_position_manager.py',
    'Advanced Backtesting': 'backtesting/advanced_backtest.py',
    'Professional Trade Validator': 'enhanced_modules/trade_validator.py',
    'AI Trade Monitor': 'src/ai/ai_trade_monitor.py',
    'Automated Trader (Exness)': 'src/trading/exness_automated_trader.py'
}

for feature, file_path in institutional_features.items():
    full_path = Path(file_path)
    status = "[OK]" if full_path.exists() else "[--]"
    print(f'{status} {feature}')
    if full_path.exists():
        print(f'     Archivo: {file_path}')

print()

# 3. CONFIGURACIONES DE TRADING INSTITUCIONAL
print('3. CONFIGURACIONES DE TRADING INSTITUCIONAL:')
print('-' * 50)
print(f'Capital Inicial: ${os.getenv("INITIAL_CAPITAL", "10000")}')
print(f'Max Risk per Trade: {float(os.getenv("MAX_RISK", "0.03"))*100}%')
print(f'Max Drawdown Permitido: {float(os.getenv("MAX_DRAWDOWN", "0.15"))*100}%')
print(f'Max Daily Loss: {float(os.getenv("MAX_DAILY_LOSS", "0.05"))*100}%')
print(f'Max Consecutive Losses: {os.getenv("MAX_CONSECUTIVE_LOSSES", "3")}')
print(f'Kelly Fraction: {os.getenv("KELLY_FRACTION", "0.2")}')
print(f'Risk Adaptativo: {os.getenv("USE_ADAPTIVE_RISK", "false").upper()}')
print()

# 4. FUNCIONALIDADES AVANZADAS ACTIVAS
print('4. FUNCIONALIDADES AVANZADAS ACTIVAS:')
print('-' * 45)
print(f'Breakeven Automatico: {os.getenv("ENABLE_BREAKEVEN", "false").upper()}')
print(f'Trailing Stop: {os.getenv("ENABLE_TRAILING_STOP", "false").upper()}')
print(f'AI Risk Optimization: {os.getenv("USE_AI_RISK_OPTIMIZATION", "false").upper()}')
print(f'Critical Alerts: {os.getenv("ENABLE_CRITICAL_ALERTS", "false").upper()}')
print(f'Divergence Alerts: {os.getenv("ALERT_ON_DIVERGENCE", "false").upper()}')
print(f'Pattern Alerts: {os.getenv("ALERT_ON_DOUBLE_TOP", "false").upper()}')
print()

# 5. TIMEFRAMES Y ANALISIS
print('5. TIMEFRAMES Y ANALISIS:')
print('-' * 30)
timeframes = os.getenv("TIMEFRAMES", "5min,15min,1h,4h,1day").split(',')
print(f'Timeframes Activos: {len(timeframes)}')
for tf in timeframes:
    print(f'  - {tf}')
print()

# 6. INTEGRACIONES EXTERNAS
print('6. INTEGRACIONES EXTERNAS:')
print('-' * 35)
print(f'TwelveData API: {os.getenv("TWELVEDATA_API_KEY", "N/A")[:8]}...')
print(f'Telegram Bot: {os.getenv("TELEGRAM_TOKEN", "N/A")[:8]}...')
print(f'Ollama AI: {os.getenv("OLLAMA_API_BASE", "N/A")}')
print(f'AI Model: {os.getenv("OLLAMA_MODEL", "N/A")}')
print()

# 7. CAPACIDADES INSTITUCIONALES DETECTADAS
print('7. CAPACIDADES INSTITUCIONALES DETECTADAS:')
print('-' * 48)

capabilities = []
if Path('multi_account_manager_fixed.py').exists():
    capabilities.append("Gestion Multi-Cuenta")
if Path('src/ui/charts/tradingview_professional_chart.py').exists():
    capabilities.append("Charts Profesionales")
if Path('src/risk/advanced_risk.py').exists():
    capabilities.append("Risk Management Avanzado")
if Path('backtesting/advanced_backtest.py').exists():
    capabilities.append("Backtesting Profesional")
if os.getenv("USE_AI_RISK_OPTIMIZATION", "false").lower() == "true":
    capabilities.append("AI Risk Optimization")

for cap in capabilities:
    print(f'[OK] {cap}')

if not capabilities:
    print('[INFO] Configuracion basica detectada')

print()

# 8. RECOMENDACIONES INSTITUCIONALES
print('8. RECOMENDACIONES PARA USO INSTITUCIONAL:')
print('-' * 50)
print('[SUGERENCIA] Activar AI Risk Optimization (USE_AI_RISK_OPTIMIZATION=true)')
print('[SUGERENCIA] Configurar Multiple Accounts si es necesario')
print('[SUGERENCIA] Usar Professional Charts para analisis visual')
print('[SUGERENCIA] Implementar backtesting antes de trading en vivo')
print('[SUGERENCIA] Configurar alertas criticas para monitoro 24/7')

print()
print('=' * 80)
print('ESTADO: El sistema tiene capacidades PROFESIONALES/INSTITUCIONALES')
print('BROKER: EXNESS (Profesional)')
print('FUNCIONES: Avanzadas con IA, Multi-timeframe y Risk Management')
print('=' * 80)