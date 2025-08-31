#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de Trading con Monitor SL/TP Prioritario
El monitor SL/TP se ejecuta independientemente de la IA
"""
import time
import threading
from datetime import datetime

def main():
    """Función principal del sistema de trading con monitor prioritario"""
    
    try:
        print("======================================================================")
        print("         ALGO TRADER V3 - MONITOR PRIORITARIO")
        print("======================================================================")
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("Configurando sistema...")
        print("Importando SignalGenerator...")
        
        # Importar dependencias
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.signals.advanced_signal_generator import SignalGenerator
        
        # Crear instancia
        print("Creando generador con trading automatico...")
        symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'BTCUSDm']
        
        # Crear generador SIN auto_execute primero para evitar problemas
        generator = SignalGenerator(symbols=symbols, auto_execute=False)
        
        # Habilitar trading automático después de la inicialización
        generator.enable_auto_trading()
        
        # Mostrar estado del mercado
        forex_open = generator.is_forex_market_open()
        active_symbols = generator.get_active_symbols()
        
        print("\\nESTADO INICIAL:")
        print(f"Simbolos configurados: {', '.join(symbols)}")
        print(f"Mercado Forex: {'ABIERTO' if forex_open else 'CERRADO'}")
        print(f"Simbolos activos: {', '.join(active_symbols) if active_symbols else 'Ninguno'}")
        print("Trading automatico: ACTIVADO")
        print("Monitor SL/TP: PRIORITARIO")
        print("Telegram: CONFIGURADO")
        print()
        
        # Verificar conexión MT5
        if generator.mt5_connection and generator.mt5_connection.connected:
            print("Conexion MT5 para trading: ACTIVA")
        else:
            print("Conexion MT5 para trading: ERROR")
        
        print()
        print("==================================================")
        print("INICIANDO SISTEMA CON MONITOR PRIORITARIO...")
        print("==================================================")
        print("El sistema ejecutara:")
        print("1. Monitor SL/TP CADA 30 SEGUNDOS (hilo separado)")
        print("2. Analisis de mercados cada 60 segundos")  
        print("3. Generacion de senales con IA (con timeout)")
        print("4. EJECUCION AUTOMATICA de trades en MT5")
        print("5. Notificaciones por Telegram")
        print()
        print("Presiona Ctrl+C para detener")
        print("-" * 50)
        
        # Variables de seguimiento
        cycle_count = 0
        
        # Función para el monitor SL/TP en hilo separado
        def monitor_thread():
            """Monitor SL/TP independiente cada 30 segundos"""
            monitor_count = 0
            print(f"[MONITOR] Hilo iniciado - is_running: {generator.is_running}")
            
            while generator.is_running:
                try:
                    monitor_count += 1
                    print(f"\\n[Monitor #{monitor_count:03d}] {datetime.now().strftime('%H:%M:%S')} - Revisando posiciones...")
                    
                    # Verificar conexión MT5 antes del monitor
                    if not generator.mt5_connection or not generator.mt5_connection.connected:
                        print(f"  -> [WARNING] MT5 no conectado, saltando monitor")
                        time.sleep(30)
                        continue
                    
                    # Monitorear y corregir posiciones abiertas
                    corrected = generator.monitor_and_correct_positions()
                    
                    if corrected > 0:
                        print(f"  -> [OK] {corrected} posiciones corregidas")
                    else:
                        print(f"  -> [OK] Todas las posiciones protegidas")
                        
                    # Esperar 30 segundos antes del próximo check
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"  -> [ERROR] Error en monitor: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(30)
            
            print("[MONITOR] Hilo terminado")
        
        # Iniciar monitor SL/TP en hilo separado
        generator.is_running = True
        monitor_thread_obj = threading.Thread(target=monitor_thread, daemon=True)
        monitor_thread_obj.start()
        print("Monitor SL/TP iniciado en hilo separado")
        
        # Notificar inicio por Telegram (si está disponible)
        if generator.telegram and hasattr(generator.telegram, 'is_active') and generator.telegram.is_active:
            try:
                startup_msg = (
                    "ALGO TRADER V3 - MONITOR PRIORITARIO\\n\\n"
                    f"Simbolos: {', '.join(symbols)}\\n"
                    "Trading automatico: ACTIVADO\\n"
                    "Monitor SL/TP: PRIORITARIO (30s)\\n"
                    "Estrategias: 6 activas"
                )
                generator.telegram.send_message(startup_msg)
                print("Notificacion de inicio enviada por Telegram")
            except Exception as e:
                print(f"Error enviando notificacion inicial: {e}")
        
        # CICLO PRINCIPAL - Solo análisis IA y señales
        while generator.is_running:
            try:
                cycle_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\\n[Ciclo {cycle_count:04d}] {current_time} - Analizando mercados...")
                
                # Verificar y reconectar MT5
                mt5_status = generator.check_and_reconnect_mt5()
                if not mt5_status:
                    print("  -> MT5: ERROR - Sin conexion - Intentando reconectar...")
                elif cycle_count % 5 == 0:
                    print("  -> MT5: Conexion verificada")
                
                # Ejecutar análisis CON TIMEOUT
                try:
                    # Usar threading para timeout del análisis IA
                    def run_analysis_with_timeout():
                        return generator.run_analysis_cycle()
                    
                    analysis_thread = threading.Thread(target=lambda: setattr(run_analysis_with_timeout, 'result', run_analysis_with_timeout()))
                    analysis_thread.start()
                    analysis_thread.join(timeout=120)  # Timeout de 2 minutos
                    
                    if analysis_thread.is_alive():
                        print("  -> [WARNING] Analisis IA timeout (>2min) - Saltando al siguiente ciclo")
                        signals = []
                    else:
                        signals = getattr(run_analysis_with_timeout, 'result', [])
                        
                except Exception as e:
                    print(f"  -> [ERROR] Error en analisis: {e}")
                    signals = []
                
                if signals:
                    print(f"  -> {len(signals)} senales generadas")
                    print(f"  -> Senales ejecutadas: {generator.trades_executed}")
                    print(f"  -> Posiciones corregidas: {generator.positions_corrected}")
                else:
                    print("  -> No hay senales en este ciclo")
                
                # Mostrar estadísticas cada 10 ciclos
                if cycle_count % 10 == 0:
                    print(f"\\n--- ESTADISTICAS (Ciclo {cycle_count}) ---")
                    print(f"Senales generadas: {generator.signals_generated}")
                    print(f"Trades ejecutados: {generator.trades_executed}")
                    print(f"Posiciones corregidas: {generator.positions_corrected}")
                    
                    # Mostrar posiciones actuales
                    if generator.mt5_connection and generator.mt5_connection.connected:
                        try:
                            positions = generator.mt5_connection.get_positions()
                            if positions:
                                print(f"Posiciones abiertas: {len(positions)}")
                                for pos in positions:
                                    pos_type = "BUY" if pos.type == 0 else "SELL"
                                    sl_ok = "SI" if pos.sl != 0.0 else "NO"
                                    tp_ok = "SI" if pos.tp != 0.0 else "NO"
                                    print(f"  - {pos.symbol}: {pos_type} {pos.volume} (SL:{sl_ok} TP:{tp_ok}) P&L:{pos.profit:.2f}")
                            else:
                                print("No hay posiciones abiertas")
                        except Exception as e:
                            print(f"Error obteniendo posiciones: {e}")
                
                print(f"Esperando 60 segundos...")
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\\nDeteniendo por solicitud del usuario...")
                break
            except Exception as e:
                print(f"Error en ciclo: {e}")
                time.sleep(5)
                continue
        
        # Detener sistema
        generator.is_running = False
        print("\\n" + "=" * 50)
        print("Sistema detenido.")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\\nSistema interrumpido por el usuario")
    except Exception as e:
        print(f"Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()