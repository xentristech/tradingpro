#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO COMPLETO DEL SISTEMA - ALGO TRADER V3
=================================================
Verifica que todos los componentes estén funcionando correctamente
"""

import os
import sys
import time
import json
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Back, Style
import importlib.util

# Inicializar colorama
init(autoreset=True)

class SystemDiagnostic:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
    def print_header(self):
        """Imprime el header del diagnóstico"""
        print(Fore.CYAN + "="*70)
        print(Fore.CYAN + " "*20 + "DIAGNÓSTICO COMPLETO DEL SISTEMA")
        print(Fore.CYAN + " "*25 + "ALGO TRADER V3")
        print(Fore.CYAN + "="*70)
        print()
        
    def check_environment(self):
        """Verifica las variables de entorno"""
        print(Fore.YELLOW + "\n[1/10] VERIFICANDO VARIABLES DE ENTORNO...")
        
        env_vars = {
            'TWELVEDATA_API_KEY': False,
            'TELEGRAM_TOKEN': False,
            'TELEGRAM_CHAT_ID': False,
            'MT5_LOGIN': False,
            'MT5_PASSWORD': False,
            'MT5_SERVER': False,
            'OPENAI_API_KEY': False
        }
        
        env_file = self.base_path / '.env'
        if env_file.exists():
            print(f"  ✅ Archivo .env encontrado")
            
            # Leer .env
            with open(env_file, 'r') as f:
                content = f.read()
                
            for var in env_vars:
                if var in content and f'{var}=' in content:
                    # Verificar que no sea el valor por defecto o vacío
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith(f'{var}='):
                            value = line.split('=', 1)[1].strip()
                            if value and value != 'YOUR_API_KEY_HERE' and value != '':
                                env_vars[var] = True
                                
                                # Verificación especial para TwelveData
                                if var == 'TWELVEDATA_API_KEY' and value == '23d17ce5b7044ad5aef9766770a6252b':
                                    print(f"  ⚠️ {var}: Usando API key hardcodeada (INSEGURO)")
                                    self.results['warnings'].append("API key de TwelveData hardcodeada")
                                else:
                                    print(f"  ✅ {var}: Configurado")
                            else:
                                print(f"  ❌ {var}: No configurado o vacío")
                else:
                    print(f"  ❌ {var}: No encontrado")
        else:
            print(f"  ❌ Archivo .env NO encontrado")
            self.results['errors'].append("Archivo .env no existe")
            
        self.results['components']['environment'] = env_vars
        return all(env_vars.values())
        
    def check_python_packages(self):
        """Verifica los paquetes Python necesarios"""
        print(Fore.YELLOW + "\n[2/10] VERIFICANDO PAQUETES PYTHON...")
        
        packages = {
            'MetaTrader5': {'import': 'MetaTrader5', 'critical': True},
            'pandas': {'import': 'pandas', 'critical': True},
            'numpy': {'import': 'numpy', 'critical': True},
            'requests': {'import': 'requests', 'critical': True},
            'telegram': {'import': 'telegram', 'critical': False},
            'plotly': {'import': 'plotly', 'critical': False},
            'dash': {'import': 'dash', 'critical': False},
            'redis': {'import': 'redis', 'critical': False},
            'sqlalchemy': {'import': 'sqlalchemy', 'critical': True},
            'colorama': {'import': 'colorama', 'critical': False},
            'psutil': {'import': 'psutil', 'critical': False}
        }
        
        installed = {}
        for package, info in packages.items():
            try:
                spec = importlib.util.find_spec(info['import'])
                if spec is not None:
                    installed[package] = True
                    print(f"  ✅ {package}: Instalado")
                else:
                    installed[package] = False
                    if info['critical']:
                        print(f"  ❌ {package}: NO instalado (CRÍTICO)")
                        self.results['errors'].append(f"Paquete crítico {package} no instalado")
                    else:
                        print(f"  ⚠️ {package}: NO instalado (opcional)")
                        self.results['warnings'].append(f"Paquete opcional {package} no instalado")
            except Exception as e:
                installed[package] = False
                print(f"  ❌ {package}: Error verificando - {e}")
                
        self.results['components']['packages'] = installed
        return all(installed[p] for p, info in packages.items() if info['critical'])
        
    def check_mt5_connection(self):
        """Verifica la conexión con MetaTrader 5"""
        print(Fore.YELLOW + "\n[3/10] VERIFICANDO CONEXIÓN MT5...")
        
        try:
            import MetaTrader5 as mt5
            
            # Inicializar MT5
            if mt5.initialize():
                print(f"  ✅ MT5 inicializado")
                
                # Obtener info de la cuenta
                account_info = mt5.account_info()
                if account_info:
                    print(f"  ✅ Cuenta conectada: {account_info.login}")
                    print(f"  💰 Balance: ${account_info.balance:.2f}")
                    print(f"  💳 Equity: ${account_info.equity:.2f}")
                    
                    self.results['components']['mt5'] = {
                        'connected': True,
                        'login': account_info.login,
                        'balance': account_info.balance,
                        'equity': account_info.equity
                    }
                else:
                    print(f"  ❌ No se pudo obtener información de la cuenta")
                    self.results['components']['mt5'] = {'connected': False}
                    
                mt5.shutdown()
                return True
            else:
                print(f"  ❌ No se pudo inicializar MT5")
                error = mt5.last_error()
                print(f"  Error: {error}")
                self.results['components']['mt5'] = {'connected': False, 'error': str(error)}
                return False
                
        except ImportError:
            print(f"  ❌ MetaTrader5 no está instalado")
            self.results['components']['mt5'] = {'connected': False, 'error': 'Not installed'}
            return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results['components']['mt5'] = {'connected': False, 'error': str(e)}
            return False
            
    def check_twelvedata(self):
        """Verifica la conexión con TwelveData API"""
        print(Fore.YELLOW + "\n[4/10] VERIFICANDO TWELVEDATA API...")
        
        try:
            # Intentar importar el cliente optimizado primero
            try:
                from src.data.twelvedata_client_optimized import TwelveDataClientOptimized
                client = TwelveDataClientOptimized()
                print(f"  ✅ Cliente optimizado disponible")
            except:
                # Fallback al cliente original
                from src.data.twelvedata_client import TwelveDataClient
                client = TwelveDataClient()
                print(f"  ⚠️ Usando cliente original (no optimizado)")
                self.results['warnings'].append("Cliente TwelveData no optimizado")
                
            # Verificar conexión
            if hasattr(client, 'verify_connection'):
                if client.verify_connection():
                    print(f"  ✅ API conectada")
                    
                    # Verificar llamadas restantes
                    if hasattr(client, 'get_remaining_calls'):
                        remaining = client.get_remaining_calls()
                        print(f"  📞 Llamadas restantes: {remaining}/800")
                        
                        if remaining < 100:
                            print(f"  ⚠️ Pocas llamadas API restantes")
                            self.results['warnings'].append(f"Solo {remaining} llamadas API restantes")
                    
                    self.results['components']['twelvedata'] = {'connected': True}
                    return True
                else:
                    print(f"  ❌ No se pudo conectar a TwelveData")
                    self.results['components']['twelvedata'] = {'connected': False}
                    return False
            else:
                print(f"  ⚠️ Cliente sin método de verificación")
                self.results['components']['twelvedata'] = {'connected': 'unknown'}
                return True
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results['components']['twelvedata'] = {'connected': False, 'error': str(e)}
            return False
            
    def check_telegram(self):
        """Verifica la conexión con Telegram"""
        print(Fore.YELLOW + "\n[5/10] VERIFICANDO TELEGRAM BOT...")
        
        try:
            from src.notifiers.telegram_notifier import TelegramNotifier
            
            notifier = TelegramNotifier()
            
            if notifier.is_active:
                print(f"  ✅ Bot Telegram activo")
                print(f"  🤖 Bot: @{notifier.bot_username if hasattr(notifier, 'bot_username') else 'XentrisAIForex_bot'}")
                
                # Intentar enviar mensaje de prueba
                try:
                    notifier.send_message("🔍 Diagnóstico del sistema - Verificación de conexión")
                    print(f"  ✅ Mensaje de prueba enviado")
                except:
                    print(f"  ⚠️ No se pudo enviar mensaje de prueba")
                    
                self.results['components']['telegram'] = {'connected': True}
                return True
            else:
                print(f"  ❌ Bot Telegram no activo")
                self.results['components']['telegram'] = {'connected': False}
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results['components']['telegram'] = {'connected': False, 'error': str(e)}
            return False
            
    def check_database(self):
        """Verifica la base de datos"""
        print(Fore.YELLOW + "\n[6/10] VERIFICANDO BASE DE DATOS...")
        
        db_path = self.base_path / 'storage' / 'trading.db'
        
        if db_path.exists():
            print(f"  ✅ Base de datos encontrada")
            
            # Verificar tamaño
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"  📊 Tamaño: {size_mb:.2f} MB")
            
            if size_mb > 100:
                print(f"  ⚠️ Base de datos muy grande, considerar limpieza")
                self.results['warnings'].append(f"Base de datos grande: {size_mb:.2f} MB")
                
            # Intentar conectar
            try:
                import sqlite3
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Verificar tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                print(f"  📋 Tablas encontradas: {len(tables)}")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"    - {table[0]}: {count} registros")
                    
                conn.close()
                
                self.results['components']['database'] = {
                    'exists': True,
                    'size_mb': size_mb,
                    'tables': len(tables)
                }
                return True
                
            except Exception as e:
                print(f"  ❌ Error conectando a la base de datos: {e}")
                self.results['components']['database'] = {'exists': True, 'error': str(e)}
                return False
        else:
            print(f"  ⚠️ Base de datos no encontrada (se creará automáticamente)")
            self.results['components']['database'] = {'exists': False}
            return True
            
    def check_processes(self):
        """Verifica qué procesos están ejecutándose"""
        print(Fore.YELLOW + "\n[7/10] VERIFICANDO PROCESOS ACTIVOS...")
        
        try:
            import psutil
            
            processes_to_check = {
                'telegram_notifier': False,
                'signal_generator': False,
                'realtime_signal': False,
                'dashboard': False,
                'mt5': False,
                'terminal64': False
            }
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    for process_key in processes_to_check:
                        if process_key in name or process_key in cmdline:
                            processes_to_check[process_key] = True
                            print(f"  ✅ {process_key}: Ejecutándose (PID: {proc.info['pid']})")
                except:
                    pass
                    
            for process, running in processes_to_check.items():
                if not running:
                    print(f"  ⚠️ {process}: No detectado")
                    
            self.results['components']['processes'] = processes_to_check
            return True
            
        except ImportError:
            print(f"  ❌ psutil no instalado, no se pueden verificar procesos")
            self.results['components']['processes'] = {'error': 'psutil not installed'}
            return False
            
    def check_ports(self):
        """Verifica los puertos utilizados"""
        print(Fore.YELLOW + "\n[8/10] VERIFICANDO PUERTOS...")
        
        ports_to_check = {
            8512: 'Dashboard Principal',
            8516: 'Chart Simulation',
            8517: 'TradingView Chart',
            8508: 'Tick System',
            6379: 'Redis Cache'
        }
        
        open_ports = {}
        
        for port, service in ports_to_check.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                open_ports[port] = True
                print(f"  ✅ Puerto {port} ({service}): Abierto")
            else:
                open_ports[port] = False
                print(f"  ⚠️ Puerto {port} ({service}): Cerrado")
                
        self.results['components']['ports'] = open_ports
        return True
        
    def check_logs(self):
        """Verifica el estado de los logs"""
        print(Fore.YELLOW + "\n[9/10] VERIFICANDO LOGS...")
        
        log_dir = self.base_path / 'logs'
        
        if log_dir.exists():
            log_files = list(log_dir.glob('*.log'))
            print(f"  📁 Directorio de logs encontrado")
            print(f"  📝 Archivos de log: {len(log_files)}")
            
            # Verificar logs recientes
            recent_logs = []
            for log_file in log_files:
                # Verificar si el log fue modificado en las últimas 24 horas
                if (time.time() - log_file.stat().st_mtime) < 86400:
                    recent_logs.append(log_file.name)
                    
            if recent_logs:
                print(f"  ✅ Logs activos (últimas 24h): {len(recent_logs)}")
                for log in recent_logs[:5]:  # Mostrar máximo 5
                    print(f"    - {log}")
            else:
                print(f"  ⚠️ No hay logs recientes")
                
            # Verificar tamaño total
            total_size = sum(f.stat().st_size for f in log_files) / (1024 * 1024)
            print(f"  💾 Tamaño total de logs: {total_size:.2f} MB")
            
            if total_size > 100:
                print(f"  ⚠️ Logs ocupan mucho espacio, considerar limpieza")
                self.results['warnings'].append(f"Logs ocupan {total_size:.2f} MB")
                
            self.results['components']['logs'] = {
                'total_files': len(log_files),
                'recent_files': len(recent_logs),
                'total_size_mb': total_size
            }
        else:
            print(f"  ⚠️ Directorio de logs no encontrado")
            log_dir.mkdir(exist_ok=True)
            print(f"  ✅ Directorio de logs creado")
            self.results['components']['logs'] = {'created': True}
            
        return True
        
    def check_system_files(self):
        """Verifica archivos críticos del sistema"""
        print(Fore.YELLOW + "\n[10/10] VERIFICANDO ARCHIVOS DEL SISTEMA...")
        
        critical_files = {
            'src/signals/realtime_signal_generator.py': 'Generador de señales',
            'src/data/twelvedata_client.py': 'Cliente TwelveData',
            'src/notifiers/telegram_notifier.py': 'Notificador Telegram',
            'src/broker/mt5_connection.py': 'Conexión MT5',
            'src/risk/advanced_risk_manager.py': 'Gestor de riesgo',
            'EJECUTAR_TODO_PRO.bat': 'Script principal'
        }
        
        missing_files = []
        
        for file_path, description in critical_files.items():
            full_path = self.base_path / file_path
            if full_path.exists():
                print(f"  ✅ {description}: Encontrado")
            else:
                print(f"  ❌ {description}: NO encontrado")
                missing_files.append(file_path)
                self.results['errors'].append(f"Archivo crítico no encontrado: {file_path}")
                
        # Verificar archivos optimizados
        optimized_files = {
            'src/data/twelvedata_client_optimized.py': 'Cliente optimizado',
            'SYSTEM_IMPROVEMENT.py': 'Sistema de mejoras',
            'MONITOR_SISTEMA.py': 'Monitor del sistema'
        }
        
        print(f"\n  📊 Archivos optimizados:")
        for file_path, description in optimized_files.items():
            full_path = self.base_path / file_path
            if full_path.exists():
                print(f"    ✅ {description}: Instalado")
            else:
                print(f"    ⚠️ {description}: No instalado")
                self.results['warnings'].append(f"Optimización no instalada: {file_path}")
                
        self.results['components']['critical_files'] = {
            'missing': missing_files,
            'total_checked': len(critical_files)
        }
        
        return len(missing_files) == 0
        
    def generate_report(self):
        """Genera el reporte final"""
        print(Fore.CYAN + "\n" + "="*70)
        print(Fore.CYAN + " "*25 + "REPORTE FINAL")
        print(Fore.CYAN + "="*70)
        
        # Contar componentes OK
        components_ok = sum(1 for comp in self.results['components'].values() 
                          if isinstance(comp, dict) and comp.get('connected', False))
        total_components = len(self.results['components'])
        
        # Estado general
        if self.results['errors']:
            status = "❌ SISTEMA CON ERRORES CRÍTICOS"
            color = Fore.RED
        elif self.results['warnings']:
            status = "⚠️ SISTEMA FUNCIONAL CON ADVERTENCIAS"
            color = Fore.YELLOW
        else:
            status = "✅ SISTEMA COMPLETAMENTE FUNCIONAL"
            color = Fore.GREEN
            
        print(color + f"\n{status}")
        print(f"\nComponentes funcionando: {components_ok}/{total_components}")
        
        # Errores críticos
        if self.results['errors']:
            print(Fore.RED + f"\n❌ ERRORES CRÍTICOS ({len(self.results['errors'])}):")
            for error in self.results['errors']:
                print(f"  • {error}")
                
        # Advertencias
        if self.results['warnings']:
            print(Fore.YELLOW + f"\n⚠️ ADVERTENCIAS ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
                
        # Recomendaciones
        print(Fore.CYAN + "\n📋 RECOMENDACIONES:")
        
        recommendations = []
        
        # Verificar API key de TwelveData
        if 'API key de TwelveData hardcodeada' in str(self.results['warnings']):
            recommendations.append("Ejecutar ACTUALIZAR_SEGURIDAD_URGENTE.bat para configurar API key segura")
            
        # Verificar cliente optimizado
        if 'Cliente TwelveData no optimizado' in str(self.results['warnings']):
            recommendations.append("Usar cliente optimizado para reducir consumo de API")
            
        # Verificar logs grandes
        if any('Logs ocupan' in w for w in self.results['warnings']):
            recommendations.append("Limpiar logs antiguos con CLEAN_AND_OPTIMIZE.py")
            
        # Verificar base de datos grande
        if any('Base de datos grande' in w for w in self.results['warnings']):
            recommendations.append("Optimizar base de datos")
            
        # Verificar procesos no activos
        processes = self.results['components'].get('processes', {})
        if isinstance(processes, dict) and not processes.get('signal_generator'):
            recommendations.append("Iniciar generador de señales con EJECUTAR_TODO_PRO.bat")
            
        if not recommendations:
            recommendations.append("Sistema funcionando correctamente, no hay acciones requeridas")
            
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
            
        # Guardar reporte en archivo
        report_file = self.base_path / 'DIAGNOSTICO_RESULTADO.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=4, ensure_ascii=False)
            
        print(Fore.WHITE + f"\n📄 Reporte completo guardado en: {report_file.name}")
        
        return status
        
    def run_diagnostic(self):
        """Ejecuta el diagnóstico completo"""
        self.print_header()
        
        print(Fore.WHITE + "Iniciando diagnóstico del sistema...\n")
        
        # Ejecutar todas las verificaciones
        checks = [
            self.check_environment,
            self.check_python_packages,
            self.check_mt5_connection,
            self.check_twelvedata,
            self.check_telegram,
            self.check_database,
            self.check_processes,
            self.check_ports,
            self.check_logs,
            self.check_system_files
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"  ❌ Error en verificación: {e}")
                self.results['errors'].append(f"Error en {check.__name__}: {str(e)}")
                
        # Generar reporte
        status = self.generate_report()
        
        return status

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║        DIAGNÓSTICO COMPLETO - ALGO TRADER V3                  ║
║                                                                ║
║  Este script verificará todos los componentes del sistema     ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    time.sleep(2)
    
    # Ejecutar diagnóstico
    diagnostic = SystemDiagnostic()
    status = diagnostic.run_diagnostic()
    
    print(Fore.WHITE + "\n" + "="*70)
    print("Diagnóstico completado")
    print("="*70)
    
    # Retornar código de salida apropiado
    if "ERRORES CRÍTICOS" in status:
        return 1
    elif "ADVERTENCIAS" in status:
        return 0
    else:
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nDiagnóstico cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
