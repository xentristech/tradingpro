#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA COMPLETO: GENERADOR DE SEÑALES + RISK MANAGER AVANZADO
==============================================================
Combina la generación de señales IA con breakeven y trailing stop automático
"""

import os
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))
sys.path.insert(0, str(project_path / 'src'))

def main():
    """Función principal del sistema completo"""
    
    print("="*70)
    print("    ALGO TRADER V3 - SISTEMA COMPLETO")
    print("    Generador IA + Breakeven + Trailing Stop")
    print("="*70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Importar dependencias
        from src.signals.advanced_signal_generator import SignalGenerator
        from src.risk.advanced_risk_manager import AdvancedRiskManager
        from dotenv import load_dotenv
        
        # Cargar configuración
        load_dotenv('configs/.env')
        
        print("Configurando sistema...")
        print("1. Importando SignalGenerator...")
        print("2. Importando AdvancedRiskManager...")
        
        # Crear instancias
        symbols = ['XAUUSDm', 'EURUSDm', 'GBPUSDm', 'BTCUSDm']
        
        # SIGNAL GENERATOR
        print("3. Creando generador con trading automatico...")
        generator = SignalGenerator(symbols=symbols, auto_execute=False)
        generator.enable_auto_trading()
        
        # RISK MANAGER
        print("4. Creando Advanced Risk Manager...")
        risk_manager = AdvancedRiskManager()
        
        # Verificar estado del mercado
        forex_open = generator.is_forex_market_open()
        active_symbols = generator.get_active_symbols()
        
        print("\nESTADO INICIAL:")
        print(f"Simbolos configurados: {', '.join(symbols)}")
        print(f"Mercado Forex: {'ABIERTO' if forex_open else 'CERRADO'}")
        print(f"Simbolos activos: {', '.join(active_symbols) if active_symbols else 'Ninguno'}")
        print("Trading automatico: ACTIVADO")
        print("Breakeven: ACTIVADO (20 pips -> +2 pips)")
        print("Trailing Stop: ACTIVADO (30 pips -> 15 pips distancia)")
        print("Monitor SL/TP: CADA 30 SEGUNDOS")
        print("Telegram: CONFIGURADO")
        print()
        
        # Verificar conexión MT5
        if generator.mt5_connection and generator.mt5_connection.connected:
            print("Conexion MT5 para trading: ACTIVA")
        else:
            print("Conexion MT5 para trading: ERROR")
        
        print()
        print("="*70)
        print("INICIANDO SISTEMA COMPLETO...")
        print("="*70)
        print("El sistema ejecutara:")
        print("1. [HILO 1] Generador de señales IA cada 60 segundos")
        print("2. [HILO 2] Risk Manager (Breakeven/Trailing) cada 30 segundos")
        print("3. [HILO 3] Monitor SL/TP basico cada 30 segundos")
        print("4. Ejecucion automatica de trades en MT5")
        print("5. Notificaciones por Telegram")
        print()
        print("Presiona Ctrl+C para detener")
        print("-" * 70)
        
        # Variables de control
        system_running = True
        
        def signal_generator_thread():
            """Hilo del generador de señales"""
            cycle_count = 0
            print("[SIGNAL GEN] Hilo iniciado")
            
            while system_running:
                try:
                    cycle_count += 1
                    current_time = datetime.now().strftime('%H:%M:%S')
                    
                    print(f"\n[SG Ciclo {cycle_count:04d}] {current_time} - Analizando mercados...")
                    
                    # Verificar y reconectar MT5
                    mt5_status = generator.check_and_reconnect_mt5()
                    if not mt5_status:
                        print("  -> MT5: ERROR - Sin conexion")
                    
                    # Ejecutar análisis
                    try:
                        signals = generator.run_analysis_cycle()
                        
                        if signals:
                            print(f"  -> {len(signals)} señales generadas")
                            print(f"  -> Trades ejecutados: {generator.trades_executed}")
                        else:
                            print("  -> No hay señales en este ciclo")
                            
                    except Exception as e:
                        print(f"  -> [ERROR] Error en analisis: {e}")
                    
                    # Esperar 60 segundos
                    time.sleep(60)
                    
                except Exception as e:
                    print(f"[SIGNAL GEN] Error: {e}")
                    time.sleep(10)
            
            print("[SIGNAL GEN] Hilo terminado")
        
        def risk_manager_thread():
            """Hilo del Risk Manager avanzado"""
            print("[RISK MANAGER] Hilo iniciado")
            
            while system_running:
                try:
                    # El AdvancedRiskManager ya tiene su propio loop
                    # Solo llamamos a su función de gestión
                    if hasattr(risk_manager, 'verify_mt5_connection') and risk_manager.verify_mt5_connection():
                        # Obtener posiciones
                        import MetaTrader5 as mt5
                        positions = mt5.positions_get()
                        
                        if positions:
                            print(f"[RISK] Monitoreando {len(positions)} posiciones...")
                            
                            for position in positions:
                                try:
                                    risk_manager.manage_position(position)
                                except Exception as e:
                                    print(f"[RISK] Error gestionando posicion {position.ticket}: {e}")
                    
                    # Esperar 30 segundos
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"[RISK MANAGER] Error: {e}")
                    time.sleep(30)
            
            print("[RISK MANAGER] Hilo terminado")
        
        def basic_monitor_thread():
            """Hilo del monitor básico de SL/TP"""
            monitor_count = 0
            print("[MONITOR] Hilo iniciado")
            
            while system_running:
                try:
                    monitor_count += 1
                    
                    # Verificar conexión MT5
                    if not generator.mt5_connection or not generator.mt5_connection.connected:
                        print(f"[Monitor #{monitor_count:03d}] MT5 no conectado")
                        time.sleep(30)
                        continue
                    
                    # Monitorear y corregir posiciones sin SL/TP
                    corrected = generator.monitor_and_correct_positions()
                    
                    if corrected > 0:
                        print(f"[Monitor #{monitor_count:03d}] {corrected} posiciones corregidas (SL/TP básico)")
                    
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"[MONITOR] Error: {e}")
                    time.sleep(30)
            
            print("[MONITOR] Hilo terminado")
        
        # Inicializar sistema
        generator.is_running = True
        
        # Notificar inicio por Telegram
        if generator.telegram and hasattr(generator.telegram, 'is_active') and generator.telegram.is_active:
            try:
                startup_msg = (
                    "ALGO TRADER V3 - SISTEMA COMPLETO\\n\\n"
                    f"Simbolos: {', '.join(symbols)}\\n"
                    "Trading automatico: ACTIVADO\\n"
                    "Breakeven: ACTIVADO (20 pips)\\n"
                    "Trailing Stop: ACTIVADO (30 pips)\\n"
                    "Estrategias IA: 6 activas\\n"
                    "Monitor: Cada 30 segundos"
                )
                generator.telegram.send_message(startup_msg)
                print("Notificacion de inicio enviada por Telegram")
            except Exception as e:
                print(f"Error enviando notificacion inicial: {e}")
        
        # Crear e iniciar hilos
        threads = []
        
        # Hilo 1: Generador de señales
        signal_thread = threading.Thread(target=signal_generator_thread, daemon=True)
        signal_thread.start()
        threads.append(signal_thread)
        print("[OK] Generador de señales iniciado en hilo separado")
        
        # Hilo 2: Risk Manager avanzado
        risk_thread = threading.Thread(target=risk_manager_thread, daemon=True)
        risk_thread.start()
        threads.append(risk_thread)
        print("[OK] Risk Manager avanzado iniciado en hilo separado")
        
        # Hilo 3: Monitor básico
        monitor_thread = threading.Thread(target=basic_monitor_thread, daemon=True)
        monitor_thread.start()
        threads.append(monitor_thread)
        print("[OK] Monitor básico iniciado en hilo separado")
        
        print()
        print("="*70)
        print("SISTEMA COMPLETO EJECUTÁNDOSE")
        print("="*70)
        
        # Loop principal
        try:
            while True:
                # Mostrar estadísticas cada 5 minutos
                time.sleep(300)  # 5 minutos
                
                print(f"\n--- ESTADISTICAS SISTEMA [{datetime.now().strftime('%H:%M:%S')}] ---")
                print(f"Señales generadas: {generator.signals_generated}")
                print(f"Trades ejecutados: {generator.trades_executed}")
                print(f"Posiciones corregidas: {generator.positions_corrected}")
                
                # Estadísticas del Risk Manager
                if hasattr(risk_manager, 'statistics'):
                    stats = risk_manager.statistics
                    print(f"Breakeven aplicados: {stats.get('breakeven_applied', 0)}")
                    print(f"Trailing actualizados: {stats.get('trailing_updated', 0)}")
                    print(f"Total pips ahorrados: {stats.get('total_pips_saved', 0)}")
                
        except KeyboardInterrupt:
            print("\n\nDeteniendo sistema por solicitud del usuario...")
            system_running = False
            generator.is_running = False
            
            # Esperar a que terminen los hilos
            time.sleep(3)
            
            print("\n" + "=" * 70)
            print("SISTEMA COMPLETO DETENIDO CORRECTAMENTE")
            print("=" * 70)
        
    except Exception as e:
        print(f"Error critico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()