#!/usr/bin/env python
"""
SISTEMA DE TRADING AUTOMATICO FIJO - ALGO TRADER V3
Version que usa analisis tecnico directo (no IA)
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
    print("    ALGO TRADER V3 - SISTEMA FIJO (ANALISIS TECNICO)")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    sys.path.insert(0, str(project_dir))
    
    try:
        # Importar el generador avanzado que funciona
        print("Importando AdvancedTechnicalSignalGenerator...")
        
        # Crear nueva clase que usa solo analisis tecnico
        from src.signals.advanced_signal_generator import SignalGenerator as BaseGenerator
        import MetaTrader5 as mt5
        
        class TechnicalOnlySignalGenerator(BaseGenerator):
            """Generador que usa SOLO analisis tecnico (no IA)"""
            
            def generate_signal_for_symbol(self, symbol):
                """Generar señal usando SOLO analisis tecnico"""
                try:
                    print(f"  -> Analizando {symbol} (TECNICO PURO)")
                    
                    # Usar el método de análisis técnico directo
                    result = self.analyze_symbol(symbol)
                    
                    if result.get('signal') in ['BUY', 'SELL'] and result.get('confidence', 0) >= 60:
                        print(f"  -> {symbol}: {result['signal']} ({result['confidence']:.1f}%)")
                        return [result]
                    else:
                        print(f"  -> {symbol}: {result.get('signal', 'NO_OPERAR')} ({result.get('confidence', 0):.1f}%) - Descartado")
                        return []
                        
                except Exception as e:
                    print(f"  -> Error analizando {symbol}: {e}")
                    return []
            
            def run_analysis_cycle(self):
                """Ciclo de analisis tecnico puro"""
                active_symbols = self.get_active_symbols()
                print(f"Analizando {len(active_symbols)} simbolos activos...")
                
                all_signals = []
                for symbol in active_symbols:
                    signals = self.generate_signal_for_symbol(symbol)
                    all_signals.extend(signals)
                
                # Ejecutar trades si hay señales válidas
                if all_signals:
                    print(f"  -> {len(all_signals)} senales validas encontradas")
                    for signal in all_signals:
                        if self.auto_execute:
                            print(f"  -> Ejecutando trade: {signal['symbol']} {signal['signal']}")
                            self.execute_trade(signal)
                        else:
                            print(f"  -> Senal generada (no ejecutada): {signal['symbol']} {signal['signal']}")
                else:
                    print("  -> No hay senales validas en este ciclo")
                
                return all_signals
        
        # Crear instancia del generador técnico
        symbols = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD']  # Símbolos que funcionan bien
        generator = TechnicalOnlySignalGenerator(symbols=symbols, auto_execute=False)
        
        # Habilitar trading automático
        if generator.enable_auto_trading():
            print("Conexion MT5 para trading: ACTIVA")
        else:
            print("Conexion MT5 para trading: ERROR")
        
        # Estado inicial
        forex_open = generator.is_forex_market_open()
        active_symbols = generator.get_active_symbols()
        
        print("\nESTADO INICIAL:")
        print(f"Simbolos configurados: {', '.join(symbols)}")
        print(f"Mercado Forex: {'ABIERTO' if forex_open else 'CERRADO'}")
        print(f"Simbolos activos: {', '.join(active_symbols)}")
        print(f"Metodo: ANALISIS TECNICO PURO (sin IA)")
        print(f"Trading automatico: ACTIVADO")
        
        print("\n" + "=" * 50)
        print("INICIANDO CICLO DE TRADING TECNICO...")
        print("=" * 50)
        print("El sistema ejecutara:")
        print("1. Analisis tecnico cada 30 segundos")
        print("2. Generacion de senales (RSI, MACD, BB, MA)")
        print("3. EJECUCION AUTOMATICA de trades >60% confianza")
        print("4. Monitoreo y correccion de SL/TP")
        print()
        print("Presiona Ctrl+C para detener")
        print("-" * 50)
        
        cycle_count = 0
        generator.is_running = True
        
        # Notificar inicio por Telegram
        if generator.telegram and hasattr(generator.telegram, 'is_active') and generator.telegram.is_active:
            try:
                startup_msg = (
                    "ALGO TRADER V3 FIJO INICIADO\n\n"
                    f"Simbolos: {', '.join(symbols)}\n"
                    "Metodo: ANALISIS TECNICO PURO\n"
                    "Trading automatico: ACTIVADO\n"
                    "Umbral minimo: 60% confianza"
                )
                generator.telegram.send_message(startup_msg)
                print("Notificacion enviada por Telegram")
            except Exception as e:
                print(f"Error enviando notificacion: {e}")
        
        while generator.is_running:
            try:
                cycle_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Ciclo {cycle_count:04d}] {current_time} - Analisis Tecnico")
                
                # Verificar MT5
                mt5_status = generator.check_and_reconnect_mt5()
                if not mt5_status:
                    print("  -> MT5: ERROR - Reconectando...")
                
                # Ejecutar análisis técnico
                signals = generator.run_analysis_cycle()
                
                # Monitorear posiciones
                corrected = generator.monitor_and_correct_positions()
                
                print(f"  -> Trades ejecutados hoy: {generator.trades_executed}")
                if corrected > 0:
                    print(f"  -> Posiciones corregidas: {corrected}")
                
                # Estadísticas cada 10 ciclos
                if cycle_count % 10 == 0:
                    print(f"\n--- ESTADISTICAS (Ciclo {cycle_count}) ---")
                    print(f"Senales generadas: {generator.signals_generated}")
                    print(f"Trades ejecutados: {generator.trades_executed}")
                    
                    # Mostrar posiciones actuales
                    if generator.mt5_connection and generator.mt5_connection.connected:
                        try:
                            positions = generator.mt5_connection.get_positions()
                            if positions:
                                print(f"Posiciones abiertas: {len(positions)}")
                                for pos in positions[:3]:  # Mostrar solo las primeras 3
                                    print(f"  -> {pos.symbol}: ${pos.profit:.2f}")
                            else:
                                print("Sin posiciones abiertas")
                        except Exception as e:
                            print(f"Error obteniendo posiciones: {e}")
                
                # Esperar 30 segundos (más rápido que el sistema original)
                print("Esperando 30 segundos...")
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n\nSistema detenido por usuario")
                break
            except Exception as e:
                logger.error(f"Error en ciclo: {e}")
                print(f"  -> Error en ciclo: {e}")
                time.sleep(5)  # Pausa corta antes de reintentar
        
        generator.is_running = False
        
        # Notificar cierre
        print("\nCerrando sistema...")
        if generator.telegram and hasattr(generator.telegram, 'is_active') and generator.telegram.is_active:
            try:
                generator.telegram.send_message("ALGO TRADER V3 FIJO DETENIDO")
            except:
                pass
        
        print("Sistema cerrado correctamente")
        
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        print(f"ERROR CRITICO: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())