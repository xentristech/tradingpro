#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA DE TRADING CON DIARIO Y GESTIÓN DE RIESGO - ALGO TRADER V3
==================================================================
Sistema completo con journal inteligente y monitoreo de riesgo
"""

import sys
import time
import threading
from datetime import datetime
from pathlib import Path

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

# Importar componentes principales
from src.signals.advanced_signal_generator import SignalGenerator
from src.journal.trading_journal import get_journal
from src.journal.google_sheets_exporter import GoogleSheetsExporter
from src.risk.risk_monitor import RiskMonitor
from src.broker.mt5_connection import MT5Connection
from src.notifiers.telegram_notifier import TelegramNotifier

def update_journal_from_mt5(journal, mt5_connection):
    """Actualiza el journal con las posiciones de MT5"""
    try:
        if not mt5_connection.connect():
            return
            
        # Obtener posiciones cerradas recientes (historial)
        # Nota: MT5 no tiene un método directo, necesitaríamos implementar tracking
        
        # Obtener posiciones abiertas
        positions = mt5_connection.get_positions()
        
        if positions:
            for pos in positions:
                # Verificar si ya está en el journal
                existing = any(t.ticket == pos.ticket for t in journal.trades)
                
                if not existing:
                    # Añadir al journal
                    trade_data = {
                        'ticket': pos.ticket,
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == 0 else 'SELL',
                        'volume': pos.volume,
                        'entry_price': pos.price_open,
                        'sl_price': pos.sl if pos.sl != 0 else None,
                        'tp_price': pos.tp if pos.tp != 0 else None,
                        'entry_time': datetime.fromtimestamp(pos.time).isoformat(),
                        'magic': pos.magic,
                        'comment': pos.comment,
                        'strategy': 'AI_Hybrid' if 'AI' in pos.comment else 'Manual'
                    }
                    journal.add_trade(trade_data)
                else:
                    # Actualizar trade existente
                    journal.update_trade(pos.ticket, {
                        'profit_usd': pos.profit,
                        'profit_pips': (pos.price_current - pos.price_open) * 10000 if 'JPY' not in pos.symbol else (pos.price_current - pos.price_open) * 100
                    })
                    
        # Actualizar snapshot de balance/equity
        account_info = mt5_connection.account_info
        if account_info:
            journal.add_balance_snapshot(account_info.balance, account_info.equity)
            
    except Exception as e:
        print(f"Error actualizando journal: {e}")

def main():
    """Función principal del sistema con journal y riesgo"""
    
    print("=" * 70)
    print("   ALGO TRADER V3 - SISTEMA CON DIARIO Y GESTIÓN DE RIESGO")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Inicializar componentes
    print("Inicializando componentes...")
    
    # 1. Journal de trading
    print("→ Cargando journal de trading...")
    journal = get_journal()
    print(f"  ✓ {len(journal.trades)} trades en historial")
    
    # 2. Monitor de riesgo
    print("→ Inicializando monitor de riesgo...")
    risk_monitor = RiskMonitor()
    print("  ✓ Monitor configurado")
    
    # 3. Exportador Google Sheets (opcional)
    google_exporter = None
    try:
        print("→ Configurando Google Sheets...")
        google_exporter = GoogleSheetsExporter()
        if google_exporter.client:
            google_exporter.create_or_open_spreadsheet("AlgoTrader_Journal")
            print("  ✓ Google Sheets conectado")
        else:
            print("  ⚠ Google Sheets no configurado")
    except Exception as e:
        print(f"  ⚠ Google Sheets no disponible: {e}")
    
    # 4. Generador de señales
    print("→ Iniciando generador de señales...")
    symbols = ['XAUUSDm', 'EURUSDm', 'GBPUSDm', 'BTCUSDm']
    generator = SignalGenerator(symbols=symbols, auto_execute=False)
    generator.enable_auto_trading()
    print(f"  ✓ Trading automático activado para {len(symbols)} símbolos")
    
    # 5. Conexión MT5 para journal
    mt5_conn = MT5Connection()
    
    print()
    print("=" * 70)
    print("SISTEMA INICIADO - FUNCIONES ACTIVAS:")
    print("=" * 70)
    print("✓ Diario de trading con métricas avanzadas")
    print("✓ Monitor de riesgo en tiempo real")
    print("✓ Alertas por Telegram y sonido local")
    print("✓ Análisis de patrones y correlación")
    print("✓ Exportación a Google Sheets" if google_exporter and google_exporter.client else "⚠ Google Sheets no configurado")
    print()
    
    # Calcular y mostrar métricas iniciales
    print("MÉTRICAS ACTUALES:")
    print("-" * 40)
    metrics = journal.calculate_metrics(period_days=30)
    print(f"Total trades: {metrics['total_trades']}")
    print(f"Win rate: {metrics['win_rate']*100:.1f}%")
    print(f"Profit factor: {metrics['profit_factor']:.2f}")
    print(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max drawdown: {metrics['max_drawdown_percent']:.2f}%")
    print(f"Net profit (30d): ${metrics['net_profit']:.2f}")
    print()
    
    # Función para actualizar journal periódicamente
    def journal_updater():
        """Actualiza el journal cada 60 segundos"""
        while generator.is_running:
            try:
                # Actualizar desde MT5
                update_journal_from_mt5(journal, mt5_conn)
                
                # Calcular métricas
                metrics = journal.calculate_metrics(period_days=1)
                
                # Exportar a Google Sheets si está disponible
                if google_exporter and google_exporter.client:
                    try:
                        # Exportar trades
                        trades_dict = [t.to_dict() for t in journal.trades[-100:]]  # Últimos 100
                        google_exporter.export_trades(trades_dict)
                        
                        # Exportar métricas
                        google_exporter.export_metrics(metrics)
                        
                        # Exportar resumen diario
                        if mt5_conn.account_info:
                            daily_report = journal.get_daily_report()
                            google_exporter.export_daily_summary(
                                mt5_conn.account_info.balance,
                                mt5_conn.account_info.equity,
                                daily_report['trades'],
                                daily_report['profit']
                            )
                    except Exception as e:
                        print(f"Error exportando a Google Sheets: {e}")
                
                # Esperar
                time.sleep(60)
                
            except Exception as e:
                print(f"Error en journal updater: {e}")
                time.sleep(60)
    
    # Función para monitor de posiciones con journal
    def enhanced_monitor_thread():
        """Monitor mejorado que actualiza el journal"""
        monitor_count = 0
        
        while generator.is_running:
            try:
                monitor_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Monitor #{monitor_count:03d}] {current_time}")
                
                # Monitor estándar de posiciones
                if generator.mt5_connection and generator.mt5_connection.connected:
                    corrected = generator.monitor_and_correct_positions()
                    
                    if corrected > 0:
                        print(f"  → {corrected} posiciones corregidas")
                    
                    # Actualizar journal con posiciones actuales
                    update_journal_from_mt5(journal, generator.mt5_connection)
                    
                    # Generar reporte de riesgo
                    risk_report = risk_monitor.generate_risk_report()
                    risk_score = risk_report.get('risk_score', 0)
                    
                    # Mostrar estado de riesgo
                    if risk_score > 80:
                        print(f"  → ⚠️ RIESGO CRÍTICO: {risk_score:.1f}/100")
                    elif risk_score > 60:
                        print(f"  → ⚠️ Riesgo elevado: {risk_score:.1f}/100")
                    elif risk_score > 40:
                        print(f"  → ⚡ Riesgo moderado: {risk_score:.1f}/100")
                    else:
                        print(f"  → ✅ Riesgo normal: {risk_score:.1f}/100")
                
                # Esperar 30 segundos
                time.sleep(30)
                
            except Exception as e:
                print(f"  → Error en monitor: {e}")
                time.sleep(30)
    
    # Iniciar hilos de monitoreo
    generator.is_running = True
    
    # Hilo del journal
    journal_thread = threading.Thread(target=journal_updater, daemon=True)
    journal_thread.start()
    print("✓ Actualizador de journal iniciado")
    
    # Hilo del monitor de riesgo
    risk_monitor.start(background=True)
    print("✓ Monitor de riesgo iniciado")
    
    # Hilo del monitor de posiciones mejorado
    monitor_thread = threading.Thread(target=enhanced_monitor_thread, daemon=True)
    monitor_thread.start()
    print("✓ Monitor de posiciones iniciado")
    
    print()
    print("Sistema ejecutándose. Presiona Ctrl+C para detener")
    print("-" * 70)
    
    # Notificar inicio por Telegram
    if generator.telegram and generator.telegram.is_active:
        try:
            startup_msg = (
                "🚀 *ALGO TRADER V3 - SISTEMA COMPLETO*\n\n"
                "✅ Diario de trading activo\n"
                "✅ Monitor de riesgo activo\n"
                "✅ Alertas configuradas\n"
                f"📊 Símbolos: {', '.join(symbols)}\n"
                f"📈 Win Rate: {metrics['win_rate']*100:.1f}%\n"
                f"💰 Profit (30d): ${metrics['net_profit']:.2f}"
            )
            generator.telegram.send_message(startup_msg, parse_mode='Markdown')
        except Exception as e:
            print(f"Error enviando notificación inicial: {e}")
    
    # Ciclo principal de análisis
    cycle_count = 0
    
    try:
        while generator.is_running:
            cycle_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n[Ciclo {cycle_count:04d}] {current_time} - Analizando mercados...")
            
            # Verificar MT5
            mt5_status = generator.check_and_reconnect_mt5()
            if not mt5_status:
                print("  → MT5: Reconectando...")
            
            # Ejecutar análisis
            try:
                signals = generator.run_analysis_cycle()
                
                if signals:
                    print(f"  → {len(signals)} señales generadas")
                    
                    # Registrar señales en el journal
                    for signal in signals:
                        if 'executed' in signal and signal['executed']:
                            trade_data = {
                                'ticket': signal.get('ticket', 0),
                                'symbol': signal['symbol'],
                                'type': signal['type'],
                                'volume': signal.get('volume', 0.01),
                                'entry_price': signal.get('price', 0),
                                'sl_price': signal.get('sl'),
                                'tp_price': signal.get('tp'),
                                'strategy': signal.get('strategy', 'AI_Hybrid'),
                                'confidence': signal.get('strength', 0),
                                'indicators': signal.get('indicators', {}),
                                'ai_analysis': signal.get('reason', '')
                            }
                            journal.add_trade(trade_data)
                else:
                    print("  → No hay señales en este ciclo")
                
            except Exception as e:
                print(f"  → Error en análisis: {e}")
            
            # Mostrar estadísticas cada 10 ciclos
            if cycle_count % 10 == 0:
                print(f"\n--- ESTADÍSTICAS (Ciclo {cycle_count}) ---")
                
                # Métricas del día
                daily_report = journal.get_daily_report()
                print(f"Trades hoy: {daily_report['trades']}")
                print(f"PnL del día: ${daily_report['profit']:.2f}")
                
                # Métricas generales
                print(f"Señales generadas: {generator.signals_generated}")
                print(f"Trades ejecutados: {generator.trades_executed}")
                print(f"Posiciones corregidas: {generator.positions_corrected}")
                
                # Risk score actual
                risk_report = risk_monitor.generate_risk_report()
                print(f"Risk Score: {risk_report.get('risk_score', 0):.1f}/100")
                
                # Patrones detectados
                patterns = journal.analyze_patterns()
                if patterns.get('current_streak'):
                    streak = patterns['current_streak']
                    if streak > 0:
                        print(f"Racha actual: {streak} wins seguidas")
                    else:
                        print(f"Racha actual: {abs(streak)} losses seguidas")
            
            # Esperar 60 segundos
            print("Esperando 60 segundos...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\nDeteniendo sistema...")
        
    finally:
        # Detener componentes
        generator.is_running = False
        risk_monitor.stop()
        
        # Generar reporte final
        print("\n" + "=" * 70)
        print("REPORTE FINAL DE SESIÓN")
        print("=" * 70)
        
        # Métricas finales
        final_metrics = journal.calculate_metrics(period_days=1)
        print(f"Trades ejecutados hoy: {final_metrics['total_trades']}")
        print(f"Win rate de la sesión: {final_metrics['win_rate']*100:.1f}%")
        print(f"PnL de la sesión: ${final_metrics['net_profit']:.2f}")
        
        # Análisis de patrones
        patterns = journal.analyze_patterns()
        if patterns.get('best_hours'):
            print(f"Mejor hora: {patterns['best_hours'][0][0]}:00")
        
        # Exportar reporte final
        if google_exporter and google_exporter.client:
            try:
                journal.export_to_csv()
                print("✓ Datos exportados a CSV")
                
                # Crear dashboard final en Google Sheets
                google_exporter.create_dashboard_sheet()
                print(f"✓ Dashboard disponible en: {google_exporter.get_spreadsheet_url()}")
            except Exception as e:
                print(f"Error exportando datos finales: {e}")
        
        print("\n¡Sistema detenido correctamente!")


if __name__ == "__main__":
    main()