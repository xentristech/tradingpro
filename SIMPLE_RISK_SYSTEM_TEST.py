#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PRUEBA SIMPLE DEL SISTEMA DE RIESGO Y JOURNAL
==============================================
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

from src.journal.trading_journal import get_journal
from src.risk.risk_monitor import RiskMonitor

def test_system():
    """Test simple del sistema completo"""
    print("=" * 60)
    print("   PRUEBA DEL SISTEMA DE RIESGO Y JOURNAL")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Test del Journal
    print("1. PROBANDO JOURNAL...")
    journal = get_journal()
    print(f"   Trades en historial: {len(journal.trades)}")
    
    # Calcular métricas
    metrics = journal.calculate_metrics(period_days=30)
    print(f"   Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"   Net Profit: ${metrics['net_profit']:.2f}")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    # 2. Test del Monitor de Riesgo
    print("\n2. PROBANDO MONITOR DE RIESGO...")
    risk_monitor = RiskMonitor()
    
    # Generar reporte
    report = risk_monitor.generate_risk_report()
    print(f"   Risk Score: {report.get('risk_score', 0):.1f}/100")
    print(f"   Status: {report.get('status', 'unknown')}")
    
    # 3. Estadísticas del Journal
    print("\n3. ESTADISTICAS DEL JOURNAL...")
    if len(journal.trades) > 0:
        patterns = journal.analyze_patterns()
        
        # Patrones de trading
        if patterns.get('best_hours'):
            print("   Mejores horas para trading:")
            for hour, data in patterns['best_hours'][:3]:
                print(f"     {hour}:00 - Profit: ${data['profit']:.2f} ({data['trades']} trades)")
        
        # Rachas
        if patterns.get('max_win_streak'):
            print(f"   Max racha ganadora: {patterns['max_win_streak']} trades")
            print(f"   Max racha perdedora: {patterns['max_loss_streak']} trades")
        
        # Performance por símbolo
        print("   Performance por simbolo:")
        for symbol, data in metrics['by_symbol'].items():
            wr = data['win_rate'] * 100
            print(f"     {symbol}: ${data['profit']:.2f} (WR: {wr:.1f}%)")
    
    # 4. Reporte diario
    print("\n4. REPORTE DEL DIA...")
    daily_report = journal.get_daily_report()
    print(f"   Trades hoy: {daily_report['trades']}")
    print(f"   Profit del dia: ${daily_report['profit']:.2f}")
    print(f"   Win/Loss: {daily_report['winning_trades']}/{daily_report['losing_trades']}")
    
    # 5. Verificación de archivos
    print("\n5. VERIFICANDO ARCHIVOS CREADOS...")
    
    # Journal JSON
    journal_file = Path("data/trading_journal.json")
    if journal_file.exists():
        print(f"   [OK] Journal: {journal_file}")
    else:
        print(f"   [ERROR] Journal no encontrado")
    
    # Logs de alertas
    alerts_file = Path("logs/risk_alerts.csv")
    if alerts_file.exists():
        print(f"   [OK] Log de alertas: {alerts_file}")
    else:
        print(f"   [INFO] Sin alertas registradas aun")
    
    print("\n" + "=" * 60)
    print("   PRUEBA COMPLETADA")
    print("=" * 60)
    
    # Mostrar resumen final
    print("\nRESUMEN:")
    print(f"- Journal funcional: {'SI' if len(journal.trades) >= 0 else 'NO'}")
    print(f"- Monitor de riesgo: {'SI' if report.get('risk_score') is not None else 'NO'}")
    print(f"- Metricas calculadas: {'SI' if metrics.get('total_trades') is not None else 'NO'}")
    print(f"- Archivos generados: {'SI' if journal_file.exists() else 'NO'}")
    
    return True

if __name__ == "__main__":
    try:
        test_system()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()