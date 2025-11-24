#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test del journal con datos de ejemplo"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Añadir path
sys.path.insert(0, str(Path(__file__).parent))

from src.journal.trading_journal import get_journal

def test_journal():
    """Test completo del journal con trades de ejemplo"""
    print("=" * 60)
    print("TEST DEL JOURNAL DE TRADING")
    print("=" * 60)
    
    journal = get_journal()
    
    # Trades de ejemplo
    sample_trades = [
        {
            'ticket': 123001,
            'symbol': 'XAUUSD',
            'type': 'BUY',
            'volume': 0.01,
            'entry_price': 2650.50,
            'exit_price': 2655.00,
            'sl_price': 2648.00,
            'tp_price': 2655.00,
            'entry_time': (datetime.now() - timedelta(hours=2)).isoformat(),
            'exit_time': (datetime.now() - timedelta(hours=1)).isoformat(),
            'profit_usd': 45.0,
            'profit_pips': 45,
            'profit_percent': 0.17,
            'strategy': 'AI_Hybrid',
            'confidence': 0.85,
            'indicators': {'RSI': 65, 'MACD': 0.5, 'ATR': 2.5}
        },
        {
            'ticket': 123002,
            'symbol': 'EURUSD',
            'type': 'SELL',
            'volume': 0.02,
            'entry_price': 1.1050,
            'exit_price': 1.1030,
            'sl_price': 1.1070,
            'tp_price': 1.1030,
            'entry_time': (datetime.now() - timedelta(hours=4)).isoformat(),
            'exit_time': (datetime.now() - timedelta(hours=3)).isoformat(),
            'profit_usd': 40.0,
            'profit_pips': 20,
            'profit_percent': 0.15,
            'strategy': 'Multi_TF',
            'confidence': 0.72,
            'indicators': {'RSI': 35, 'MACD': -0.3, 'ATR': 1.8}
        },
        {
            'ticket': 123003,
            'symbol': 'BTCUSD',
            'type': 'BUY',
            'volume': 0.01,
            'entry_price': 65000.00,
            'exit_price': 64800.00,
            'sl_price': 64500.00,
            'tp_price': 65500.00,
            'entry_time': (datetime.now() - timedelta(hours=6)).isoformat(),
            'exit_time': (datetime.now() - timedelta(hours=5)).isoformat(),
            'profit_usd': -20.0,
            'profit_pips': -200,
            'profit_percent': -0.31,
            'strategy': 'AI_Hybrid',
            'confidence': 0.60,
            'indicators': {'RSI': 45, 'MACD': 0.1, 'ATR': 500.0}
        },
        {
            'ticket': 123004,
            'symbol': 'GBPUSD',
            'type': 'BUY',
            'volume': 0.015,
            'entry_price': 1.2750,
            'exit_price': 1.2780,
            'sl_price': 1.2720,
            'tp_price': 1.2780,
            'entry_time': (datetime.now() - timedelta(hours=8)).isoformat(),
            'exit_time': (datetime.now() - timedelta(hours=7)).isoformat(),
            'profit_usd': 45.0,
            'profit_pips': 30,
            'profit_percent': 0.24,
            'strategy': 'Breakout',
            'confidence': 0.78,
            'indicators': {'RSI': 58, 'MACD': 0.2, 'ATR': 1.2}
        },
        {
            'ticket': 123005,
            'symbol': 'XAUUSD',
            'type': 'SELL',
            'volume': 0.01,
            'entry_price': 2648.00,
            'exit_price': 2650.00,
            'sl_price': 2653.00,
            'tp_price': 2645.00,
            'entry_time': (datetime.now() - timedelta(hours=10)).isoformat(),
            'exit_time': (datetime.now() - timedelta(hours=9)).isoformat(),
            'profit_usd': -20.0,
            'profit_pips': -20,
            'profit_percent': -0.08,
            'strategy': 'Mean_Reversion',
            'confidence': 0.55,
            'indicators': {'RSI': 75, 'MACD': -0.1, 'ATR': 2.8}
        }
    ]
    
    # Añadir trades
    print("Añadiendo trades de ejemplo...")
    for trade_data in sample_trades:
        trade = journal.add_trade(trade_data)
        print(f"  [OK] {trade.symbol} {trade.trade_type} #{trade.ticket}")
    
    # Añadir snapshots de balance
    initial_balance = 10000.0
    for i, trade_data in enumerate(sample_trades):
        balance = initial_balance + sum(t['profit_usd'] for t in sample_trades[:i+1])
        journal.add_balance_snapshot(initial_balance, balance)
    
    print(f"\nTotal trades en journal: {len(journal.trades)}")
    
    # Calcular métricas
    print("\n" + "=" * 40)
    print("CALCULANDO MÉTRICAS...")
    print("=" * 40)
    
    metrics = journal.calculate_metrics(period_days=1)
    
    print(f"METRICAS DE RENDIMIENTO:")
    print(f"   Total trades: {metrics['total_trades']}")
    print(f"   Win rate: {metrics['win_rate']*100:.1f}%")
    print(f"   Profit factor: {metrics['profit_factor']:.2f}")
    print(f"   Net profit: ${metrics['net_profit']:.2f}")
    print(f"   Expectancy: ${metrics['expectancy']:.2f}")
    
    print(f"\nMETRICAS DE RIESGO:")
    print(f"   Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Sortino ratio: {metrics['sortino_ratio']:.2f}")
    print(f"   Max drawdown: ${metrics['max_drawdown']:.2f} ({metrics['max_drawdown_percent']:.2f}%)")
    print(f"   VaR 95%: ${metrics['var_95']:.2f}")
    print(f"   Recovery factor: {metrics['recovery_factor']:.2f}")
    
    print(f"\nPOR SIMBOLO:")
    for symbol, data in metrics['by_symbol'].items():
        print(f"   {symbol}: ${data['profit']:.2f} ({data['trades']} trades, WR: {data['win_rate']*100:.1f}%)")
    
    print(f"\nPOR ESTRATEGIA:")
    for strategy, data in metrics['by_strategy'].items():
        print(f"   {strategy}: ${data['profit']:.2f} ({data['trades']} trades, WR: {data['win_rate']*100:.1f}%)")
    
    # Análisis de patrones
    print("\n" + "=" * 40)
    print("ANÁLISIS DE PATRONES")
    print("=" * 40)
    
    patterns = journal.analyze_patterns()
    
    if patterns.get('best_hours'):
        print("MEJORES HORAS:")
        for hour, data in patterns['best_hours'][:3]:
            print(f"   {hour}:00 → ${data['profit']:.2f} ({data['trades']} trades)")
    
    if patterns.get('max_win_streak'):
        print(f"\nRACHAS:")
        print(f"   Max racha ganadora: {patterns['max_win_streak']}")
        print(f"   Max racha perdedora: {patterns['max_loss_streak']}")
        current = patterns.get('current_streak', 0)
        if current > 0:
            print(f"   Racha actual: +{current} wins")
        elif current < 0:
            print(f"   Racha actual: {current} losses")
    
    # Reporte diario
    print("\n" + "=" * 40)
    print("REPORTE DEL DÍA")
    print("=" * 40)
    
    daily = journal.get_daily_report()
    print(f"Fecha: {daily['date']}")
    print(f"Trades: {daily['trades']}")
    print(f"Profit: ${daily['profit']:.2f}")
    print(f"Win/Loss: {daily['winning_trades']}/{daily['losing_trades']}")
    print(f"Mejor trade: ${daily['best_trade']:.2f}")
    print(f"Peor trade: ${daily['worst_trade']:.2f}")
    print(f"Simbolos: {', '.join(daily['symbols_traded'])}")
    
    # Exportar CSV
    print("\n" + "=" * 40)
    print("EXPORTACIÓN")
    print("=" * 40)
    
    csv_file = f"data/test_journal_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    journal.export_to_csv(csv_file)
    print(f"[OK] Journal exportado a: {csv_file}")
    
    print("\n" + "=" * 60)
    print("[OK] TEST DEL JOURNAL COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    test_journal()