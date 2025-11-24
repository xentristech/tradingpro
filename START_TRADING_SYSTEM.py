#!/usr/bin/env python
"""
SISTEMA DE TRADING AUTOMATICO - ALGO TRADER V3
Version final sin emojis para Windows
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Configurar encoding desde el inicio
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def setup_simple_logging():
    """Configurar logging simple sin caracteres especiales"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        encoding='utf-8',
        errors='replace'
    )

def main():
    setup_simple_logging()
    logger = logging.getLogger(__name__)
    
    print("=" * 70)
    print("         ALGO TRADER V3 - SISTEMA DE TRADING AUTOMATICO")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    sys.path.insert(0, str(project_dir))
    
    try:
        # Configurar componentes sin emojis
        print("Configurando sistema...")
        
        # Importar sin emojis problemáticos
        print("Importando SignalGenerator...")
        from src.signals.advanced_signal_generator import SignalGenerator
        
        # Crear instancia
        print("Creando generador con trading automatico...")
        symbols = ['XAUUSDm', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'BTCUSDm', 'ETHUSDm']
        
        # Crear generador SIN auto_execute primero para evitar problemas
        generator = SignalGenerator(symbols=symbols, auto_execute=False)
        
        # Habilitar trading automático usando el método apropriado
        if generator.enable_auto_trading():
            print("Conexion MT5 para trading: ACTIVA")
        else:
            print("Conexion MT5 para trading: ERROR")
        
        # Mostrar estado del mercado
        forex_open = generator.is_forex_market_open()
        active_symbols = generator.get_active_symbols()
        
        print("\nESTADO INICIAL:")
        print(f"Simbolos configurados: {', '.join(symbols)}")
        print(f"Mercado Forex: {'ABIERTO' if forex_open else 'CERRADO'}")
        print(f"Simbolos activos: {', '.join(active_symbols)}")
        print(f"Trading automatico: ACTIVADO")  
        print(f"Monitor SL/TP: ACTIVADO")
        print(f"Telegram: CONFIGURADO")
        
        print("\n" + "=" * 50)
        print("INICIANDO CICLO DE TRADING...")
        print("=" * 50)
        print("El sistema ejecutara:")
        print("1. Analisis de mercados cada 60 segundos")
        print("2. Generacion de senales con IA")
        print("3. EJECUCION AUTOMATICA de trades en MT5")
        print("4. Monitoreo y correccion de SL/TP")
        print("5. Notificaciones por Telegram")
        print()
        print("Presiona Ctrl+C para detener")
        print("-" * 50)
        
        # Variables de seguimiento
        cycle_count = 0
        
        # CICLO PRINCIPAL MANUAL (evitar el método start() que tiene emojis)
        generator.is_running = True
        
        # Notificar inicio por Telegram (si está disponible)
        if generator.telegram and hasattr(generator.telegram, 'is_active') and generator.telegram.is_active:
            try:
                startup_msg = (
                    "ALGO TRADER V3 INICIADO\n\n"
                    f"Simbolos: {', '.join(symbols)}\n"
                    "Trading automatico: ACTIVADO\n"
                    "Monitor SL/TP: ACTIVADO\n"
                    "Estrategias: 6 activas"
                )
                generator.telegram.send_message(startup_msg)
                print("Notificacion de inicio enviada por Telegram")
            except Exception as e:
                print(f"Error enviando notificacion inicial: {e}")
        
        while generator.is_running:
            try:
                cycle_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Ciclo {cycle_count:04d}] {current_time} - Analizando mercados...")
                
                # Verificar y reconectar MT5 cada ciclo para detección rápida
                mt5_status = generator.check_and_reconnect_mt5()
                if not mt5_status:
                    print("  -> MT5: ERROR - Sin conexion - Intentando reconectar...")
                elif cycle_count % 5 == 0:  # Solo mostrar estado OK cada 5 ciclos para reducir spam
                    print("  -> MT5: Conexion verificada")
                
                # Ejecutar análisis manualmente
                signals = generator.run_analysis_cycle()
                
                # Monitorear y corregir posiciones abiertas
                corrected_this_cycle = generator.monitor_and_correct_positions()
                
                if signals:
                    print(f"  -> {len(signals)} senales generadas")
                    print(f"  -> Senales ejecutadas: {generator.trades_executed}")
                    print(f"  -> Posiciones corregidas: {generator.positions_corrected}")
                else:
                    print("  -> No hay senales en este ciclo")
                
                # Mostrar estadísticas cada 10 ciclos
                if cycle_count % 10 == 0:
                    print(f"\n--- ESTADISTICAS (Ciclo {cycle_count}) ---")
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
                print("\nDeteniendo por solicitud del usuario...")
                break
            except Exception as e:
                print(f"Error en ciclo: {e}")
                time.sleep(5)
                continue
        
        # Detener sistema
        generator.is_running = False
        print("\n" + "=" * 50)
        print("SISTEMA DETENIDO")
        print("=" * 50)
        print(f"Resumen final:")
        print(f"- Ciclos ejecutados: {cycle_count}")
        print(f"- Senales generadas: {generator.signals_generated}")
        print(f"- Trades ejecutados: {generator.trades_executed}")
        print(f"- Posiciones corregidas: {generator.positions_corrected}")
        
        # Desconectar MT5
        if generator.mt5_connection:
            generator.mt5_connection.disconnect()
            print("- Conexion MT5 cerrada")
            
    except KeyboardInterrupt:
        print("\n\nSistema interrumpido por el usuario")
        
    except Exception as e:
        print(f"\nError ejecutando sistema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()