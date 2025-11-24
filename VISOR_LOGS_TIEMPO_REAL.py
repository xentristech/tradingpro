#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VISOR DE LOGS EN TIEMPO REAL
============================
Herramienta para ver y analizar logs del sistema en tiempo real
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
import sys

# Agregar path del proyecto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path / 'src'))

try:
    from src.utils.comprehensive_logger import comprehensive_logger
except ImportError:
    comprehensive_logger = None

class RealTimeLogViewer:
    """Visor de logs en tiempo real"""
    
    def __init__(self):
        self.log_dir = Path("logs/comprehensive")
        self.date_str = datetime.now().strftime('%Y%m%d')
        
        # Archivos a monitorear
        self.log_files = {
            'signals': self.log_dir / f"signals_{self.date_str}.json",
            'trades': self.log_dir / f"trades_{self.date_str}.json",
            'risk_management': self.log_dir / f"risk_management_{self.date_str}.json",
            'system_events': self.log_dir / f"system_events_{self.date_str}.json",
            'errors': self.log_dir / f"errors_{self.date_str}.json",
            'telegram_notifications': self.log_dir / f"telegram_{self.date_str}.json"
        }
        
        # Contadores para tracking
        self.last_counts = {}
        for log_type in self.log_files.keys():
            self.last_counts[log_type] = 0
    
    def get_log_entries(self, log_type: str, limit: int = 10) -> list:
        """Obtener últimas entradas de un tipo de log"""
        try:
            log_file = self.log_files[log_type]
            
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            
            # Retornar últimas entradas
            return entries[-limit:] if entries else []
            
        except Exception as e:
            print(f"Error leyendo {log_type}: {e}")
            return []
    
    def get_new_entries(self, log_type: str) -> list:
        """Obtener solo las nuevas entradas desde la última verificación"""
        try:
            log_file = self.log_files[log_type]
            
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            
            current_count = len(entries)
            last_count = self.last_counts[log_type]
            
            if current_count > last_count:
                new_entries = entries[last_count:]
                self.last_counts[log_type] = current_count
                return new_entries
            
            return []
            
        except Exception as e:
            print(f"Error obteniendo nuevas entradas {log_type}: {e}")
            return []
    
    def format_log_entry(self, entry: dict) -> str:
        """Formatear entrada de log para visualización"""
        timestamp = entry.get('timestamp_readable', 'N/A')
        log_type = entry.get('log_type', 'UNKNOWN')
        level = entry.get('level', 'INFO')
        component = entry.get('component', 'Unknown')
        message = entry.get('message', 'No message')
        
        # Color coding (básico)
        if level == 'ERROR':
            prefix = "[ERROR]"
        elif level == 'WARNING':
            prefix = "[WARN]"
        elif log_type == 'SIGNAL':
            prefix = "[SIGNAL]"
        elif log_type == 'TRADE_EXECUTION':
            prefix = "[TRADE]"
        elif log_type == 'RISK_MANAGEMENT':
            prefix = "[RISK]"
        elif log_type == 'TELEGRAM_NOTIFICATION':
            prefix = "[TELEGRAM]"
        else:
            prefix = "[INFO]"
        
        formatted = f"{timestamp} {prefix} {component}: {message}"
        
        # Agregar datos adicionales si son importantes
        data = entry.get('data', {})
        if data:
            if log_type == 'SIGNAL':
                symbol = data.get('symbol', '')
                signal_type = data.get('signal_type', '')
                confidence = data.get('confidence', 0)
                formatted += f" [{symbol} {signal_type} {confidence:.1f}%]"
            
            elif log_type == 'RISK_MANAGEMENT':
                action_type = data.get('action_type', '')
                pos_data = data.get('position_data', {})
                symbol = pos_data.get('symbol', '')
                ticket = pos_data.get('ticket', '')
                formatted += f" [{action_type} {symbol} #{ticket}]"
            
            elif log_type == 'TRADE_EXECUTION':
                symbol = data.get('symbol', '')
                ticket = data.get('ticket', '')
                trade_type = data.get('type', '')
                formatted += f" [{symbol} #{ticket} {trade_type}]"
        
        return formatted
    
    def show_current_stats(self):
        """Mostrar estadísticas actuales"""
        try:
            if comprehensive_logger:
                stats = comprehensive_logger.get_current_stats()
                
                print("\n" + "="*60)
                print("    ESTADÍSTICAS EN TIEMPO REAL")
                print("="*60)
                print(f"Tiempo activo: {stats.get('uptime_readable', 'N/A')}")
                print(f"Señales generadas: {stats.get('signals_generated', 0)}")
                print(f"Trades ejecutados: {stats.get('trades_executed', 0)}")
                print(f"Breakeven aplicados: {stats.get('breakeven_applied', 0)}")
                print(f"Trailing aplicados: {stats.get('trailing_applied', 0)}")
                print(f"Errores registrados: {stats.get('errors_count', 0)}")
                print(f"Notificaciones enviadas: {stats.get('notifications_sent', 0)}")
                print("="*60)
            else:
                print("Sistema de logging no disponible para estadísticas")
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
    
    def monitor_real_time(self, refresh_seconds=5):
        """Monitorear logs en tiempo real"""
        print("="*70)
        print("    MONITOR DE LOGS EN TIEMPO REAL")
        print("="*70)
        print(f"Refrescando cada {refresh_seconds} segundos")
        print("Presiona Ctrl+C para detener")
        print("="*70)
        
        try:
            while True:
                # Limpiar pantalla (básico)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print(f"MONITOR DE LOGS - {datetime.now().strftime('%H:%M:%S')}")
                print("="*70)
                
                # Mostrar estadísticas
                self.show_current_stats()
                
                # Mostrar nuevas entradas de cada tipo
                total_new_entries = 0
                
                for log_type in ['signals', 'trades', 'risk_management', 'errors', 'telegram_notifications']:
                    new_entries = self.get_new_entries(log_type)
                    
                    if new_entries:
                        total_new_entries += len(new_entries)
                        print(f"\n[NUEVAS ENTRADAS - {log_type.upper()}]")
                        print("-" * 50)
                        
                        for entry in new_entries:
                            print(self.format_log_entry(entry))
                
                if total_new_entries == 0:
                    print("\nSin nuevas entradas...")
                else:
                    print(f"\nTotal nuevas entradas: {total_new_entries}")
                
                print(f"\nPróxima actualización en {refresh_seconds} segundos...")
                time.sleep(refresh_seconds)
                
        except KeyboardInterrupt:
            print("\n\nMonitor detenido")
    
    def show_log_summary(self, log_type: str, limit: int = 20):
        """Mostrar resumen de un tipo de log específico"""
        print(f"\n=== RESUMEN DE {log_type.upper()} (Últimas {limit} entradas) ===")
        
        entries = self.get_log_entries(log_type, limit)
        
        if not entries:
            print(f"No hay entradas de {log_type}")
            return
        
        for entry in entries:
            print(self.format_log_entry(entry))
        
        print(f"\nTotal entradas mostradas: {len(entries)}")
    
    def analyze_performance(self):
        """Analizar rendimiento del sistema"""
        print("\n" + "="*60)
        print("    ANÁLISIS DE RENDIMIENTO")
        print("="*60)
        
        # Analizar señales
        signals = self.get_log_entries('signals', 100)  # Últimas 100
        if signals:
            signal_types = {}
            confidence_levels = []
            
            for signal in signals:
                data = signal.get('data', {})
                sig_type = data.get('signal_type', 'UNKNOWN')
                confidence = data.get('confidence', 0)
                
                signal_types[sig_type] = signal_types.get(sig_type, 0) + 1
                if confidence > 0:
                    confidence_levels.append(confidence)
            
            print(f"\nSEÑALES (últimas {len(signals)}):")
            for sig_type, count in signal_types.items():
                print(f"  {sig_type}: {count}")
            
            if confidence_levels:
                avg_confidence = sum(confidence_levels) / len(confidence_levels)
                print(f"  Confianza promedio: {avg_confidence:.1f}%")
        
        # Analizar risk management
        risk_actions = self.get_log_entries('risk_management', 100)
        if risk_actions:
            action_types = {}
            success_count = 0
            
            for action in risk_actions:
                data = action.get('data', {})
                action_type = data.get('action_type', 'UNKNOWN')
                success = data.get('success', False)
                
                action_types[action_type] = action_types.get(action_type, 0) + 1
                if success:
                    success_count += 1
            
            print(f"\nRISK MANAGEMENT (últimas {len(risk_actions)}):")
            for action_type, count in action_types.items():
                print(f"  {action_type}: {count}")
            
            success_rate = (success_count / len(risk_actions)) * 100 if risk_actions else 0
            print(f"  Tasa de éxito: {success_rate:.1f}%")
        
        # Analizar errores
        errors = self.get_log_entries('errors', 50)
        if errors:
            error_types = {}
            
            for error in errors:
                data = error.get('data', {})
                error_type = data.get('error_type', 'UNKNOWN')
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            print(f"\nERRORES (últimos {len(errors)}):")
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count}")
        
        print("="*60)

def main():
    """Función principal"""
    viewer = RealTimeLogViewer()
    
    print("VISOR DE LOGS DEL SISTEMA DE TRADING")
    print("====================================")
    print()
    print("Opciones:")
    print("1. Monitor en tiempo real")
    print("2. Ver resumen de señales")
    print("3. Ver resumen de trades")
    print("4. Ver resumen de risk management")
    print("5. Ver errores")
    print("6. Análisis de rendimiento")
    print("7. Ver estadísticas actuales")
    print()
    
    try:
        opcion = input("Selecciona una opción (1-7): ").strip()
        
        if opcion == '1':
            refresh = input("Segundos de refresco (default 5): ").strip()
            refresh = int(refresh) if refresh.isdigit() else 5
            viewer.monitor_real_time(refresh)
            
        elif opcion == '2':
            limit = input("Número de entradas (default 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            viewer.show_log_summary('signals', limit)
            
        elif opcion == '3':
            limit = input("Número de entradas (default 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            viewer.show_log_summary('trades', limit)
            
        elif opcion == '4':
            limit = input("Número de entradas (default 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            viewer.show_log_summary('risk_management', limit)
            
        elif opcion == '5':
            limit = input("Número de entradas (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            viewer.show_log_summary('errors', limit)
            
        elif opcion == '6':
            viewer.analyze_performance()
            
        elif opcion == '7':
            viewer.show_current_stats()
            
        else:
            print("Opción no válida")
    
    except KeyboardInterrupt:
        print("\nPrograma interrumpido")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()