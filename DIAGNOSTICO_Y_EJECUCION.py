#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 DIAGNÓSTICO Y EJECUCIÓN DE SEÑALES
=====================================
Sistema completo para verificar, diagnosticar y ejecutar señales de trading
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('diagnostico_ejecucion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingDiagnosticSystem:
    """Sistema de diagnóstico y ejecución de trading"""
    
    def __init__(self):
        self.issues = []
        self.solutions = []
        self.status = {
            'mt5_connected': False,
            'api_working': False,
            'config_valid': False,
            'signals_generated': False,
            'execution_enabled': False,
            'positions_open': 0
        }
        
        print("\n" + "="*80)
        print("🔧 SISTEMA DE DIAGNÓSTICO Y EJECUCIÓN DE SEÑALES")
        print("="*80)
        print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def check_environment(self):
        """Verifica el entorno y configuración"""
        print("📋 VERIFICANDO ENTORNO...")
        print("-"*40)
        
        # Verificar archivo .env
        env_file = Path('.env')
        if not env_file.exists():
            self.issues.append("❌ Archivo .env no encontrado")
            self.solutions.append("Crear archivo .env desde .env.example")
            
            # Crear .env automáticamente
            print("⚠️ Creando archivo .env de configuración...")
            self.create_env_file()
        else:
            print("✅ Archivo .env encontrado")
            self.status['config_valid'] = True
        
        # Verificar Python y librerías
        self.check_dependencies()
        
        return self.status['config_valid']
    
    def create_env_file(self):
        """Crea archivo .env con configuración básica"""
        env_content = """# CONFIGURACIÓN DE TRADING - GENERADO AUTOMÁTICAMENTE
# =====================================================

# MODO DE TRADING
TRADING_MODE=DEMO
LIVE_TRADING=false

# MT5 CONFIGURACIÓN (COMPLETAR)
MT5_LOGIN=YOUR_LOGIN_HERE
MT5_PASSWORD=YOUR_PASSWORD_HERE
MT5_SERVER=Exness-MT5Real

# SÍMBOLOS
SYMBOL=BTCUSDm
TWELVEDATA_SYMBOL=BTC/USD

# API KEYS
TWELVEDATA_API_KEY=915b2ea02f7d49b986c1ae27d2711c73

# GESTIÓN DE RIESGO
RISK_PER_TRADE=0.01
MAX_CONCURRENT_TRADES=3
DEF_SL_USD=50
DEF_TP_USD=100

# NOTIFICACIONES (OPCIONAL)
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=

# MACHINE LEARNING
ML_ENABLED=false
"""
        
        try:
            with open('.env', 'w') as f:
                f.write(env_content)
            print("✅ Archivo .env creado con configuración básica")
            self.status['config_valid'] = True
        except Exception as e:
            self.issues.append(f"❌ Error creando .env: {e}")
    
    def check_dependencies(self):
        """Verifica las dependencias necesarias"""
        print("\n📦 VERIFICANDO DEPENDENCIAS...")
        print("-"*40)
        
        required_libs = {
            'MetaTrader5': 'MetaTrader5',
            'requests': 'requests',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'python-dotenv': 'dotenv'
        }
        
        missing = []
        for package, import_name in required_libs.items():
            try:
                __import__(import_name)
                print(f"✅ {package} instalado")
            except ImportError:
                print(f"❌ {package} NO instalado")
                missing.append(package)
        
        if missing:
            self.issues.append(f"❌ Librerías faltantes: {', '.join(missing)}")
            self.solutions.append(f"Ejecutar: pip install {' '.join(missing)}")
            
            # Intentar instalar automáticamente
            print("\n⚠️ Instalando dependencias faltantes...")
            self.install_dependencies(missing)
    
    def install_dependencies(self, packages):
        """Instala dependencias faltantes"""
        import subprocess
        
        for package in packages:
            try:
                print(f"📥 Instalando {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
                print(f"✅ {package} instalado correctamente")
            except:
                print(f"❌ Error instalando {package}")
    
    def check_mt5_connection(self):
        """Verifica conexión con MT5"""
        print("\n🔌 VERIFICANDO CONEXIÓN MT5...")
        print("-"*40)
        
        try:
            import MetaTrader5 as mt5
            from dotenv import load_dotenv
            load_dotenv()
            
            # Obtener credenciales
            login = os.getenv('MT5_LOGIN', '')
            password = os.getenv('MT5_PASSWORD', '')
            server = os.getenv('MT5_SERVER', 'Exness-MT5Real')
            
            if login == 'YOUR_LOGIN_HERE' or not login:
                self.issues.append("❌ MT5_LOGIN no configurado en .env")
                self.solutions.append("Editar .env y agregar tu número de cuenta MT5")
                print("❌ Credenciales MT5 no configuradas")
                return False
            
            # Intentar conectar
            if not mt5.initialize():
                self.issues.append("❌ No se pudo inicializar MT5")
                self.solutions.append("Verificar que MetaTrader 5 esté instalado")
                print("❌ MT5 no se pudo inicializar")
                return False
            
            # Intentar login
            authorized = mt5.login(int(login), password=password, server=server)
            
            if authorized:
                account_info = mt5.account_info()
                print(f"✅ Conectado a MT5")
                print(f"   Cuenta: {account_info.login}")
                print(f"   Balance: ${account_info.balance:.2f}")
                print(f"   Servidor: {account_info.server}")
                self.status['mt5_connected'] = True
                
                # Verificar posiciones abiertas
                positions = mt5.positions_get()
                if positions:
                    self.status['positions_open'] = len(positions)
                    print(f"   Posiciones abiertas: {len(positions)}")
                
                return True
            else:
                error = mt5.last_error()
                self.issues.append(f"❌ Login MT5 falló: {error}")
                self.solutions.append("Verificar credenciales en .env")
                print(f"❌ Error de autenticación: {error}")
                return False
                
        except Exception as e:
            self.issues.append(f"❌ Error MT5: {e}")
            self.solutions.append("Verificar instalación de MetaTrader5")
            print(f"❌ Error: {e}")
            return False
    
    def check_api_connection(self):
        """Verifica conexión con API de datos"""
        print("\n🌐 VERIFICANDO API DE DATOS...")
        print("-"*40)
        
        try:
            import requests
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('TWELVEDATA_API_KEY', '915b2ea02f7d49b986c1ae27d2711c73')
            
            # Test API
            url = f"https://api.twelvedata.com/quote"
            params = {
                'symbol': 'BTC/USD',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'code' not in data:  # No error
                    price = data.get('close', 'N/A')
                    print(f"✅ API TwelveData funcionando")
                    print(f"   BTC/USD: ${price}")
                    self.status['api_working'] = True
                    return True
                else:
                    self.issues.append(f"❌ API Error: {data.get('message', 'Unknown')}")
                    self.solutions.append("Verificar API key en .env")
                    print(f"❌ API Error: {data.get('message', 'Unknown')}")
            else:
                self.issues.append(f"❌ API HTTP Error: {response.status_code}")
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            self.issues.append(f"❌ Error conectando API: {e}")
            self.solutions.append("Verificar conexión a internet")
            print(f"❌ Error: {e}")
            
        return False
    
    def check_signals(self):
        """Verifica si hay señales generadas"""
        print("\n📊 VERIFICANDO SEÑALES...")
        print("-"*40)
        
        # Buscar archivos de señales
        signal_files = list(Path('.').glob('signals_*.json'))
        
        if signal_files:
            latest_file = max(signal_files, key=os.path.getctime)
            print(f"✅ Archivo de señales encontrado: {latest_file}")
            
            # Leer señales
            try:
                with open(latest_file, 'r') as f:
                    signals = json.load(f)
                
                print(f"   Total señales: {len(signals)}")
                
                # Mostrar señales de compra/venta
                buy_signals = [s for s in signals if 'BUY' in s.get('action', '')]
                sell_signals = [s for s in signals if 'SELL' in s.get('action', '')]
                
                if buy_signals:
                    print(f"   📈 Señales de COMPRA: {len(buy_signals)}")
                    for s in buy_signals:
                        print(f"      • {s['symbol']}: {s['action']}")
                
                if sell_signals:
                    print(f"   📉 Señales de VENTA: {len(sell_signals)}")
                    for s in sell_signals:
                        print(f"      • {s['symbol']}: {s['action']}")
                
                self.status['signals_generated'] = True
                return signals
                
            except Exception as e:
                self.issues.append(f"❌ Error leyendo señales: {e}")
                print(f"❌ Error: {e}")
        else:
            print("⚠️ No hay archivos de señales generados")
            self.solutions.append("Ejecutar: python SIGNAL_GENERATOR_LIVE.py")
            
            # Generar señales ahora
            print("\n🔄 Generando señales nuevas...")
            self.generate_signals_now()
        
        return []
    
    def generate_signals_now(self):
        """Genera señales inmediatamente"""
        try:
            from simple_signals import analyze_all
            print("Generando análisis...")
            analyze_all()
            self.status['signals_generated'] = True
        except Exception as e:
            print(f"❌ Error generando señales: {e}")
            self.issues.append(f"Error generando señales: {e}")
    
    def check_execution_system(self):
        """Verifica si el sistema de ejecución está activo"""
        print("\n⚙️ VERIFICANDO SISTEMA DE EJECUCIÓN...")
        print("-"*40)
        
        # Verificar si hay procesos de trading activos
        try:
            # Verificar archivo de estado
            state_file = Path('trading_state.json')
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                if state.get('active', False):
                    print("✅ Sistema de trading ACTIVO")
                    print(f"   Última actualización: {state.get('last_update', 'Unknown')}")
                    self.status['execution_enabled'] = True
                else:
                    print("⚠️ Sistema de trading INACTIVO")
                    self.solutions.append("Ejecutar: python main.py start")
            else:
                print("⚠️ Sistema de trading no inicializado")
                self.solutions.append("Ejecutar: python main.py start --mode demo")
                
        except Exception as e:
            print(f"❌ Error verificando sistema: {e}")
    
    def fix_issues(self):
        """Intenta solucionar los problemas encontrados"""
        print("\n🔧 APLICANDO SOLUCIONES...")
        print("-"*40)
        
        if not self.issues:
            print("✅ No hay problemas que solucionar")
            return True
        
        print(f"Se encontraron {len(self.issues)} problemas:")
        
        for i, (issue, solution) in enumerate(zip(self.issues, self.solutions), 1):
            print(f"\n{i}. {issue}")
            print(f"   Solución: {solution}")
            
            # Intentar aplicar solución automática
            if "pip install" in solution:
                print("   🔄 Aplicando solución automática...")
                packages = solution.split("pip install")[1].strip()
                self.install_dependencies(packages.split())
            
            elif "Crear archivo .env" in solution:
                if not Path('.env').exists():
                    print("   🔄 Creando archivo .env...")
                    self.create_env_file()
            
            elif "python" in solution:
                print(f"   ⚠️ Ejecutar manualmente: {solution}")
        
        return False
    
    def execute_signals(self, signals):
        """Ejecuta las señales de trading"""
        print("\n🚀 EJECUTANDO SEÑALES...")
        print("-"*40)
        
        if not self.status['mt5_connected']:
            print("❌ No se puede ejecutar: MT5 no conectado")
            return False
        
        try:
            import MetaTrader5 as mt5
            from dotenv import load_dotenv
            load_dotenv()
            
            # Filtrar señales fuertes
            strong_signals = [s for s in signals if 'STRONG' in s.get('action', '')]
            
            if not strong_signals:
                print("⚠️ No hay señales fuertes para ejecutar")
                return False
            
            for signal in strong_signals:
                symbol = signal['symbol']
                action = signal['action']
                
                print(f"\n📍 Procesando: {symbol} - {action}")
                
                # Verificar si el símbolo existe en MT5
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is None:
                    print(f"   ❌ Símbolo {symbol} no encontrado en MT5")
                    # Intentar variaciones
                    alternatives = [f"{symbol}m", symbol.replace('/', '')]
                    for alt in alternatives:
                        symbol_info = mt5.symbol_info(alt)
                        if symbol_info:
                            symbol = alt
                            print(f"   ✅ Usando símbolo alternativo: {symbol}")
                            break
                
                if symbol_info and symbol_info.visible:
                    # Preparar orden
                    lot = 0.01  # Lote mínimo
                    
                    if 'BUY' in action:
                        order_type = mt5.ORDER_TYPE_BUY
                        price = mt5.symbol_info_tick(symbol).ask
                        sl = price - (price * 0.01)  # -1%
                        tp = price + (price * 0.02)  # +2%
                    else:
                        order_type = mt5.ORDER_TYPE_SELL
                        price = mt5.symbol_info_tick(symbol).bid
                        sl = price + (price * 0.01)  # +1%
                        tp = price - (price * 0.02)  # -2%
                    
                    # Crear request
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": lot,
                        "type": order_type,
                        "price": price,
                        "sl": sl,
                        "tp": tp,
                        "deviation": 20,
                        "magic": 234000,
                        "comment": f"Signal: {action}",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    
                    # Verificar modo
                    if os.getenv('LIVE_TRADING', 'false').lower() == 'true':
                        print("   ⚠️ MODO LIVE - Ejecutando orden real...")
                        result = mt5.order_send(request)
                        
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            print(f"   ✅ Orden ejecutada: Ticket #{result.order}")
                        else:
                            print(f"   ❌ Error: {result.comment}")
                    else:
                        print("   📝 MODO DEMO - Orden simulada")
                        print(f"      Tipo: {action}")
                        print(f"      Precio: {price:.5f}")
                        print(f"      SL: {sl:.5f}")
                        print(f"      TP: {tp:.5f}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error ejecutando señales: {e}")
            self.issues.append(f"Error en ejecución: {e}")
            return False
    
    def generate_report(self):
        """Genera reporte completo del diagnóstico"""
        print("\n" + "="*80)
        print("📋 REPORTE DE DIAGNÓSTICO")
        print("="*80)
        
        # Estado general
        print("\n🔍 ESTADO DEL SISTEMA:")
        for key, value in self.status.items():
            icon = "✅" if value else "❌"
            if key == 'positions_open':
                print(f"   {icon} {key}: {value}")
            else:
                print(f"   {icon} {key}: {'Activo' if value else 'Inactivo'}")
        
        # Problemas encontrados
        if self.issues:
            print(f"\n⚠️ PROBLEMAS ENCONTRADOS ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   • {issue}")
        else:
            print("\n✅ No se encontraron problemas")
        
        # Soluciones recomendadas
        if self.solutions:
            print(f"\n💡 SOLUCIONES RECOMENDADAS:")
            for i, solution in enumerate(self.solutions, 1):
                print(f"   {i}. {solution}")
        
        # Recomendaciones finales
        print("\n📌 PRÓXIMOS PASOS:")
        
        if not self.status['mt5_connected']:
            print("   1. Configurar credenciales MT5 en archivo .env")
            print("   2. Asegurarse que MetaTrader 5 esté instalado")
        
        if not self.status['signals_generated']:
            print("   3. Generar señales: python SIGNAL_GENERATOR_LIVE.py")
        
        if not self.status['execution_enabled']:
            print("   4. Iniciar sistema: python main.py start --mode demo")
        
        if all(self.status.values()):
            print("   ✨ Sistema completamente operativo!")
            print("   Monitorear con: python MONITOR_SISTEMA.py")
        
        print("\n" + "="*80)
        print(f"Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        # Guardar reporte
        self.save_report()
    
    def save_report(self):
        """Guarda el reporte en archivo"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': self.status,
            'issues': self.issues,
            'solutions': self.solutions
        }
        
        filename = f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Reporte guardado en: {filename}")
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")
    
    def run_full_diagnostic(self):
        """Ejecuta diagnóstico completo"""
        print("🔄 Iniciando diagnóstico completo del sistema...\n")
        
        # 1. Verificar entorno
        self.check_environment()
        
        # 2. Verificar MT5
        self.check_mt5_connection()
        
        # 3. Verificar API
        self.check_api_connection()
        
        # 4. Verificar señales
        signals = self.check_signals()
        
        # 5. Verificar sistema de ejecución
        self.check_execution_system()
        
        # 6. Intentar solucionar problemas
        if self.issues:
            self.fix_issues()
        
        # 7. Ejecutar señales si todo está OK
        if self.status['mt5_connected'] and signals:
            print("\n¿Deseas ejecutar las señales encontradas? (s/n): ", end='')
            response = input().lower()
            if response == 's':
                self.execute_signals(signals)
        
        # 8. Generar reporte
        self.generate_report()
        
        return all([
            self.status['mt5_connected'],
            self.status['api_working'],
            self.status['config_valid']
        ])


def main():
    """Función principal"""
    try:
        # Crear sistema de diagnóstico
        diagnostic = TradingDiagnosticSystem()
        
        # Ejecutar diagnóstico completo
        success = diagnostic.run_full_diagnostic()
        
        if success:
            print("\n✅ SISTEMA LISTO PARA OPERAR")
            print("\nOpciones disponibles:")
            print("1. Generar señales: python SIGNAL_GENERATOR_LIVE.py")
            print("2. Iniciar trading: python main.py start")
            print("3. Monitorear: python MONITOR_SISTEMA.py")
        else:
            print("\n⚠️ SISTEMA REQUIERE CONFIGURACIÓN")
            print("Revisa el reporte generado para más detalles")
        
    except KeyboardInterrupt:
        print("\n\n⛔ Diagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
