"""
Chart Scheduler - Programador de Gráficos Dinámicos
==================================================

Sistema de programación que mantiene los gráficos actualizándose automáticamente
"""

import os
import time
import signal
import sys
from datetime import datetime
from pathlib import Path
import threading
import json
from dynamic_charts import DynamicChartGenerator

class ChartScheduler:
    def __init__(self, config_file="chart_config.json"):
        self.config_file = Path(config_file)
        self.generator = None
        self.is_running = False
        self.scheduler_thread = None
        
        # Configuración por defecto
        self.default_config = {
            "update_interval": 30,  # segundos
            "symbols": ["BTC/USD", "XAU/USD", "EUR/USD"],
            "chart_types": ["candlestick", "line", "ohlc", "bars"],
            "auto_start": True,
            "max_retries": 3,
            "retry_delay": 10
        }
        
        self.load_config()
        self.setup_signal_handlers()
        
    def load_config(self):
        """Cargar configuración desde archivo JSON"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Fusionar con configuración por defecto
                self.config = {**self.default_config, **config}
                print(f"Configuración cargada desde {self.config_file}")
            else:
                self.config = self.default_config
                self.save_config()
                print("Usando configuración por defecto")
                
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            self.config = self.default_config
    
    def save_config(self):
        """Guardar configuración actual"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"Configuración guardada en {self.config_file}")
        except Exception as e:
            print(f"Error guardando configuración: {e}")
    
    def setup_signal_handlers(self):
        """Configurar manejadores de señales para cierre limpio"""
        def signal_handler(signum, frame):
            print(f"\nSeñal {signum} recibida. Cerrando sistema...")
            self.stop_scheduler()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)  # Terminación del sistema
    
    def initialize_generator(self):
        """Inicializar generador de gráficos dinámicos"""
        try:
            self.generator = DynamicChartGenerator(
                update_interval=self.config['update_interval']
            )
            
            # Configurar símbolos
            self.generator.symbols = self.config['symbols']
            
            print("Generador de gráficos dinámicos inicializado")
            return True
            
        except Exception as e:
            print(f"Error inicializando generador: {e}")
            return False
    
    def start_scheduler(self):
        """Iniciar el programador"""
        if self.is_running:
            print("Scheduler ya está ejecutándose")
            return False
        
        print("CHART SCHEDULER")
        print("=" * 50)
        print("Configuración:")
        print(f"  • Intervalo de actualización: {self.config['update_interval']} segundos")
        print(f"  • Símbolos: {', '.join(self.config['symbols'])}")
        print(f"  • Tipos de gráfico: {', '.join(self.config['chart_types'])}")
        print(f"  • Reintentos máximos: {self.config['max_retries']}")
        print("=" * 50)
        
        # Inicializar generador
        if not self.initialize_generator():
            print("Error: No se pudo inicializar el generador")
            return False
        
        self.is_running = True
        
        def scheduler_loop():
            retry_count = 0
            
            while self.is_running:
                try:
                    # Actualizar gráficos
                    self.generator.update_all_charts()
                    retry_count = 0  # Reset contador de reintentos
                    
                    # Esperar el intervalo configurado
                    sleep_time = 0
                    while sleep_time < self.config['update_interval'] and self.is_running:
                        time.sleep(1)
                        sleep_time += 1
                    
                except Exception as e:
                    retry_count += 1
                    print(f"Error en scheduler (intento {retry_count}/{self.config['max_retries']}): {e}")
                    
                    if retry_count >= self.config['max_retries']:
                        print("Máximo número de reintentos alcanzado. Deteniendo scheduler...")
                        self.is_running = False
                        break
                    
                    # Esperar antes de reintentar
                    time.sleep(self.config['retry_delay'])
        
        # Ejecutar en hilo separado
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        print("Scheduler iniciado correctamente")
        print("Presiona Ctrl+C para detener")
        
        return True
    
    def stop_scheduler(self):
        """Detener el programador"""
        if not self.is_running:
            print("Scheduler no está ejecutándose")
            return
        
        print("Deteniendo scheduler...")
        self.is_running = False
        
        if self.generator:
            self.generator.stop_dynamic_updates()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        print("Scheduler detenido")
    
    def get_status(self):
        """Obtener estado actual del scheduler"""
        status = {
            'scheduler_running': self.is_running,
            'config': self.config,
            'generator_status': None
        }
        
        if self.generator:
            status['generator_status'] = self.generator.get_system_status()
        
        return status
    
    def update_config(self, new_config):
        """Actualizar configuración y reiniciar si es necesario"""
        old_interval = self.config.get('update_interval', 30)
        old_symbols = self.config.get('symbols', [])
        
        # Actualizar configuración
        self.config.update(new_config)
        self.save_config()
        
        # Reiniciar si hay cambios significativos
        if (self.config['update_interval'] != old_interval or 
            self.config['symbols'] != old_symbols):
            
            if self.is_running:
                print("Reiniciando scheduler con nueva configuración...")
                self.stop_scheduler()
                time.sleep(2)
                self.start_scheduler()
        
        print("Configuración actualizada")
    
    def run_once(self):
        """Ejecutar actualización una sola vez (para testing)"""
        if not self.generator:
            if not self.initialize_generator():
                print("Error: No se pudo inicializar el generador")
                return False
        
        print("Ejecutando actualización única...")
        self.generator.update_all_charts()
        print("Actualización completada")
        return True
    
    def run_interactive(self):
        """Modo interactivo para control manual"""
        print("MODO INTERACTIVO")
        print("Comandos disponibles:")
        print("  start    - Iniciar scheduler automático")
        print("  stop     - Detener scheduler")
        print("  once     - Ejecutar actualización una vez")
        print("  status   - Mostrar estado")
        print("  config   - Mostrar configuración")
        print("  exit     - Salir")
        print()
        
        while True:
            try:
                cmd = input("chart_scheduler> ").strip().lower()
                
                if cmd == 'start':
                    self.start_scheduler()
                    
                elif cmd == 'stop':
                    self.stop_scheduler()
                    
                elif cmd == 'once':
                    self.run_once()
                    
                elif cmd == 'status':
                    status = self.get_status()
                    print(json.dumps(status, indent=2, default=str))
                    
                elif cmd == 'config':
                    print(json.dumps(self.config, indent=2))
                    
                elif cmd in ['exit', 'quit']:
                    if self.is_running:
                        self.stop_scheduler()
                    break
                    
                else:
                    print("Comando no reconocido")
                    
            except KeyboardInterrupt:
                print("\nSaliendo...")
                if self.is_running:
                    self.stop_scheduler()
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Chart Scheduler - Sistema de gráficos dinámicos')
    parser.add_argument('--config', default='chart_config.json', 
                       help='Archivo de configuración (default: chart_config.json)')
    parser.add_argument('--once', action='store_true', 
                       help='Ejecutar actualización una sola vez')
    parser.add_argument('--interactive', action='store_true',
                       help='Modo interactivo')
    parser.add_argument('--interval', type=int, default=30,
                       help='Intervalo de actualización en segundos (default: 30)')
    
    args = parser.parse_args()
    
    try:
        # Crear scheduler
        scheduler = ChartScheduler(args.config)
        
        # Actualizar intervalo si se especificó
        if args.interval != 30:
            scheduler.update_config({'update_interval': args.interval})
        
        if args.once:
            # Ejecutar una sola vez
            scheduler.run_once()
            
        elif args.interactive:
            # Modo interactivo
            scheduler.run_interactive()
            
        else:
            # Modo automático continuo
            if scheduler.start_scheduler():
                try:
                    # Mantener ejecutándose
                    while scheduler.is_running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nDeteniendo...")
                finally:
                    scheduler.stop_scheduler()
            
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()