#!/usr/bin/env python3
"""
Script de Prueba del Sistema Completo - AlgoTrader v3.0
Verifica todos los componentes del sistema de trading
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Cargar configuración
load_dotenv('.env')

def test_environment():
    """Verificar variables de entorno"""
    print("=== VERIFICACIÓN DE CONFIGURACIÓN ===")
    
    required_vars = [
        'TELEGRAM_TOKEN', 
        'TELEGRAM_CHAT_ID', 
        'TRADING_SYMBOL'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        print(f"  • {var}: {'OK Configurado' if value else 'ERROR Faltante'}")
    
    return all(os.getenv(var) for var in required_vars)

def test_mt5_connection():
    """Verificar conexión MT5"""
    print("\n=== VERIFICACIÓN MT5 ===")
    
    try:
        if not mt5.initialize():
            print("  ERROR No se pudo inicializar MT5")
            return False
        
        # Información de cuenta
        account = mt5.account_info()
        if account:
            print(f"  OK Cuenta conectada: {account.login}")
            print(f"  OK Balance: ${account.balance:,.2f}")
            print(f"  OK Equity: ${account.equity:,.2f}")
            print(f"  OK Broker: {account.company}")
        
        # Verificar símbolo
        symbol = os.getenv('TRADING_SYMBOL', 'BTCUSD')
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"  OK Símbolo {symbol} disponible - Precio: ${tick.bid:,.2f}")
        else:
            print(f"  ERROR Símbolo {symbol} no disponible")
            return False
        
        mt5.shutdown()
        return True
        
    except Exception as e:
        print(f"  ERROR MT5: {e}")
        return False

def test_telegram():
    """Verificar Telegram"""
    print("\n=== VERIFICACIÓN TELEGRAM ===")
    
    try:
        from notifiers.telegram_notifier import send_telegram_message
        
        message = f"Prueba sistema AlgoTrader v3.0 - {datetime.now().strftime('%H:%M:%S')}"
        result = send_telegram_message(message)
        
        if result:
            print("  OK Mensaje enviado exitosamente")
            return True
        else:
            print("  ERROR Error enviando mensaje")
            return False
            
    except Exception as e:
        print(f"  ERROR Telegram: {e}")
        return False

def test_ollama():
    """Verificar Ollama AI"""
    print("\n=== VERIFICACIÓN OLLAMA AI ===")
    
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            models = [line.split()[0] for line in result.stdout.split('\n')[1:] if line.strip()]
            print(f"  OK Ollama activo - {len(models)} modelos disponibles")
            
            # Verificar modelo específico
            target_model = 'deepseek-r1:14b'
            if any(target_model in model for model in models):
                print(f"  OK Modelo {target_model} disponible")
            else:
                print(f"  WARN Modelo {target_model} no encontrado")
                print(f"    Modelos disponibles: {', '.join(models[:3])}")
            
            return True
        else:
            print("  ERROR Ollama no responde")
            return False
            
    except Exception as e:
        print(f"  ERROR Ollama: {e}")
        return False

def test_signal_generation():
    """Verificar generación de señales"""
    print("\n=== VERIFICACIÓN SEÑALES ===")
    
    try:
        from signals.signal_generator import SignalGenerator
        
        generator = SignalGenerator()
        symbol = os.getenv('TRADING_SYMBOL', 'BTCUSD')
        
        # Generar señal de prueba con datos mock
        import pandas as pd
        mock_data = pd.DataFrame({
            'close': [100, 101, 102, 101, 100],
            'volume': [1000, 1100, 1200, 1150, 1050]
        })
        signal = generator.generate(mock_data)
        
        if signal:
            print(f"  OK Señal generada para {symbol}")
            print(f"    Dirección: {signal.get('direction', 'N/A')}")
            print(f"    Fuerza: {signal.get('strength', 0):.2f}")
            print(f"    Confianza: {signal.get('confidence', 0):.2%}")
            return True
        else:
            print("  ERROR No se pudo generar señal")
            return False
            
    except Exception as e:
        print(f"  ERROR generación señales: {e}")
        return False

def test_bot_health():
    """Verificar estado del bot"""
    print("\n=== VERIFICACIÓN BOT ===")
    
    try:
        from pathlib import Path
        log_file = Path("logs/pro_bot.log")
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if lines:
                last_line = lines[-1].strip()
                print(f"  OK Log encontrado - {len(lines)} líneas")
                print(f"    Última entrada: {last_line[:100]}...")
                
                # Verificar actividad reciente
                if '|' in last_line:
                    time_part = last_line.split('|')[0].strip()
                    try:
                        last_time = datetime.strptime(time_part, '%H:%M:%S')
                        last_time = last_time.replace(
                            year=datetime.now().year,
                            month=datetime.now().month,
                            day=datetime.now().day
                        )
                        
                        time_diff = datetime.now() - last_time
                        if time_diff.total_seconds() < 300:  # 5 minutos
                            print("  OK Bot activo (actividad reciente)")
                        else:
                            print(f"  WARN Bot inactivo - última actividad: {time_diff}")
                    except:
                        print("  WARN No se pudo verificar tiempo de actividad")
                
                return True
            else:
                print("  ERROR Log vacío")
                return False
        else:
            print("  ERROR Archivo de log no encontrado")
            return False
            
    except Exception as e:
        print(f"  ERROR verificación bot: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("PRUEBA COMPLETA DEL SISTEMA ALGOTRADER v3.0")
    print("=" * 60)
    
    tests = [
        ("Configuración", test_environment),
        ("MT5", test_mt5_connection),
        ("Telegram", test_telegram),
        ("Ollama AI", test_ollama),
        ("Señales", test_signal_generation),
        ("Bot", test_bot_health)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ERROR ejecutando prueba {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name:15} | {status}")
    
    print("-" * 60)
    print(f"RESULTADO: {passed}/{total} pruebas exitosas ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\nSISTEMA COMPLETAMENTE FUNCIONAL")
        print("El sistema está listo para trading en vivo")
    elif passed >= total * 0.8:
        print("\nSISTEMA MAYORMENTE FUNCIONAL")
        print("Revisar componentes fallidos antes de trading en vivo")
    else:
        print("\nSISTEMA REQUIERE ATENCIÓN")
        print("Resolver problemas críticos antes de continuar")
    
    return passed == total

if __name__ == "__main__":
    success = main()
# Comentamos input para evitar error en ejecución automatizada
    # input("\nPresiona Enter para salir...")
    sys.exit(0 if success else 1)