#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA COMPLETO CON DIRECTOR DE OPERACIONES
===========================================
Sistema con Director de Operaciones integrado que:
- Monitorea posiciones cada 30 segundos
- Analiza volumen institucional 
- Ajusta TP dinámicamente
- Registra TODO en logs específicos
"""

import time
import threading
import logging
from datetime import datetime
from pathlib import Path
import sys

# Configurar logging específico del Director
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Logger específico del Director
director_logger = logging.getLogger('director')
director_handler = logging.FileHandler(log_dir / 'director_operations.log', encoding='utf-8')
director_formatter = logging.Formatter('%(asctime)s - DIRECTOR - %(levelname)s - %(message)s')
director_handler.setFormatter(director_formatter)
director_logger.addHandler(director_handler)
director_logger.setLevel(logging.INFO)

def main():
    """Sistema completo con Director de Operaciones"""
    
    try:
        print("=" * 80)
        print("      ALGO TRADER V3 - SISTEMA COMPLETO CON DIRECTOR")
        print("=" * 80)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Importar dependencias
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.signals.advanced_signal_generator import SignalGenerator
        from src.director.operations_director import OperationsDirector
        from src.utils.trade_history_logger import trade_logger
        
        print("Configurando sistema...")
        print("Importando SignalGenerator...")
        print("Importando Director de Operaciones...")
        
        # Crear generador con trading automático
        generator = SignalGenerator(auto_execute=True)
        
        # Inicializar Director de Operaciones
        print("Inicializando Director de Operaciones...")
        director = OperationsDirector()
        
        if not generator.mt5_connection:
            print("ERROR: No se pudo conectar a MT5")
            return
            
        if not director:
            print("ERROR: No se pudo inicializar el Director")
            return
        
        # Estado inicial
        print()
        print("ESTADO INICIAL:")
        print(f"Simbolos configurados: {', '.join(generator.config['symbols'])}")
        print(f"Mercado Forex: {'ABIERTO' if generator.is_market_open() else 'CERRADO'}")
        
        active_symbols = [s for s in generator.config['symbols'] if generator.is_market_open()]
        print(f"Simbolos activos: {', '.join(active_symbols) if active_symbols else 'NINGUNO'}")
        print(f"Trading automatico: {'ACTIVADO' if generator.auto_execute else 'DESACTIVADO'}")
        print(f"Monitor SL/TP: PRIORITARIO")
        print(f"Director: ACTIVADO")
        print(f"Telegram: {'CONFIGURADO' if generator.telegram else 'NO DISPONIBLE'}")
        print()
        
        # Verificar conexión MT5
        if hasattr(generator, 'mt5_connection') and generator.mt5_connection:
            print("Conexion MT5 para trading: ACTIVA")
        else:
            print("Conexion MT5 para trading: NO DISPONIBLE")
        print()
        
        print("=" * 60)
        print("INICIANDO SISTEMA CON DIRECTOR INTEGRADO...")
        print("=" * 60)
        print("El sistema ejecutara:")
        print("1. Monitor SL/TP CADA 30 SEGUNDOS")
        print("2. DIRECTOR DE OPERACIONES cada 30 segundos")
        print("3. Analisis de mercados cada 60 segundos")
        print("4. Ejecucion automatica de trades")
        print("5. Notificaciones por Telegram")
        print("6. Registro completo en logs/director_operations.log")
        print()
        print("Presiona Ctrl+C para detener")
        print("-" * 60)
        
        # Variables de control
        cycle_count = 0
        director_count = 0
        
        # Función del monitor con Director integrado
        def enhanced_monitor_thread():
            """Monitor mejorado con Director de Operaciones"""
            nonlocal director_count
            monitor_count = 0
            
            print(f"[MONITOR+DIRECTOR] Hilo iniciado")
            director_logger.info("Director de Operaciones iniciado")
            
            while generator.is_running:
                try:
                    monitor_count += 1
                    director_count += 1
                    
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"\\n[Monitor #{monitor_count:03d}] {timestamp} - Monitor + Director...")
                    
                    # 1. Monitor SL/TP básico
                    if generator.mt5_connection and generator.mt5_connection.connected:
                        corrected = generator.monitor_and_correct_positions()
                        if corrected > 0:
                            print(f"  -> SL/TP corregidas: {corrected}")
                            director_logger.info(f"SL/TP corregidas: {corrected} posiciones")
                    
                    # 2. DIRECTOR DE OPERACIONES
                    print(f"  -> [DIRECTOR #{director_count:03d}] Analizando operaciones activas...")
                    director_logger.info(f"Ciclo #{director_count} - Iniciando análisis")
                    
                    try:
                        # Analizar todas las posiciones abiertas
                        results = director.monitor_active_trades()
                        
                        if results.get('total_positions', 0) > 0:
                            adjustments = results.get('tp_adjustments', 0)
                            
                            print(f"  -> Director: {results['total_positions']} posiciones analizadas")
                            
                            if adjustments > 0:
                                print(f"  -> 🎯 DIRECTOR: {adjustments} ajustes TP realizados!")
                                director_logger.info(f"TP ajustados: {adjustments}")
                                
                                # Log detallado de los ajustes
                                for adjustment in results.get('adjustments_details', []):
                                    ticket = adjustment.get('ticket', 'N/A')
                                    adj_type = adjustment.get('type', 'N/A')
                                    old_tp = adjustment.get('old_tp', 0)
                                    new_tp = adjustment.get('new_tp', 0)
                                    reason = adjustment.get('reason', 'N/A')
                                    
                                    director_logger.info(
                                        f"AJUSTE: Ticket {ticket} | {adj_type} | "
                                        f"TP: {old_tp:.5f} -> {new_tp:.5f} | "
                                        f"Razón: {reason}"
                                    )
                                    
                                    # Registrar en historial para backtesting
                                    trade_logger.log_tp_adjustment({
                                        'ticket': ticket,
                                        'symbol': adjustment.get('symbol', ''),
                                        'adjustment_type': adj_type,
                                        'old_tp': old_tp,
                                        'new_tp': new_tp,
                                        'reason': reason,
                                        'ai_analysis': adjustment.get('ai_analysis', ''),
                                        'market_analysis': adjustment.get('market_data', {}),
                                        'current_price': adjustment.get('current_price', 0)
                                    })
                            else:
                                print(f"  -> Director: Sin ajustes necesarios")
                                director_logger.debug("Sin ajustes TP necesarios")
                        else:
                            print(f"  -> Director: No hay posiciones activas")
                            director_logger.debug("No hay posiciones para analizar")
                            
                    except Exception as director_error:
                        print(f"  -> [ERROR] Director: {director_error}")
                        director_logger.error(f"Error en Director: {director_error}")
                    
                    # 3. Esperar siguiente ciclo
                    time.sleep(30)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"  -> [ERROR] Monitor: {e}")
                    director_logger.error(f"Error en monitor: {e}")
                    time.sleep(30)
            
            print("[MONITOR+DIRECTOR] Hilo terminado")
            director_logger.info("Director de Operaciones detenido")
        
        # Función principal de análisis (sin cambios)
        def analysis_cycle():
            """Ciclo principal de análisis de mercado"""
            nonlocal cycle_count
            
            while generator.is_running:
                try:
                    cycle_count += 1
                    print(f"\\n[Ciclo {cycle_count:04d}] {datetime.now().strftime('%H:%M:%S')} - Analizando mercados...")
                    
                    if not generator.is_market_open():
                        print("  -> Mercado cerrado - Saltando análisis")
                        time.sleep(60)
                        continue
                    
                    # Generar señales como siempre
                    signals = generator.generate_signals_batch()
                    
                    if signals:
                        print(f"  -> {len(signals)} señales generadas")
                        director_logger.info(f"Señales generadas: {len(signals)}")
                    else:
                        print("  -> No hay señales en este ciclo")
                    
                    print("Esperando 60 segundos...")
                    time.sleep(60)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"  -> [ERROR] Análisis: {e}")
                    time.sleep(60)
        
        # Iniciar hilos
        monitor_thread = threading.Thread(target=enhanced_monitor_thread, daemon=True)
        analysis_thread = threading.Thread(target=analysis_cycle, daemon=True)
        
        print("Monitor SL/TP iniciado en hilo separado")
        monitor_thread.start()
        
        print("Notificacion de inicio enviada por Telegram")
        if generator.telegram:
            generator.telegram.send_message(
                "🚀 *SISTEMA CON DIRECTOR ACTIVADO*\\n\\n"
                f"Simbolos: {', '.join(active_symbols)}\\n"
                f"Director: Monitoreo cada 30s\\n"
                f"Hora: {datetime.now().strftime('%H:%M:%S')}"
            )
        
        # Ejecutar análisis en hilo principal
        analysis_cycle()
        
    except KeyboardInterrupt:
        print("\\n\\n[DETENIENDO] Interrupción por usuario")
        director_logger.info("Sistema detenido por usuario")
        generator.is_running = False
        
    except Exception as e:
        print(f"\\n[ERROR CRÍTICO] {e}")
        director_logger.error(f"Error crítico: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\\n[FINALIZANDO] Cerrando sistema...")
        if 'generator' in locals():
            generator.is_running = False
        print("Sistema detenido")

if __name__ == "__main__":
    main()