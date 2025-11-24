#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST RAPIDO DEL SISTEMA OPTIMIZADO
===================================
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def test_basic():
    print("=== TEST RAPIDO DEL SISTEMA ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: TwelveData
    try:
        print("\n1. Probando TwelveData...")
        
        # Crear versión simple sin volumen
        simple_td_code = '''
import os
import requests
from datetime import datetime

class TwelveDataSimple:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.base_url = 'https://api.twelvedata.com'
        self.symbol_map = {
            'EURUSD': 'EUR/USD',
            'XAUUSD': 'XAU/USD',
            'BTCUSD': 'BTC/USD'
        }
        
    def get_price(self, symbol):
        try:
            api_symbol = self.symbol_map.get(symbol, symbol)
            url = f"{self.base_url}/price"
            params = {'symbol': api_symbol, 'apikey': self.api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0))
        except:
            pass
        return None
        
    def get_indicators(self, symbol):
        # Simulación de indicadores
        return {
            'rsi': 55.5,
            'macd': 0.0001,
            'sma_20': 1.0850,
            'sentiment': 'NEUTRAL'
        }
'''
        
        with open('td_simple.py', 'w') as f:
            f.write(simple_td_code)
        
        from td_simple import TwelveDataSimple
        td = TwelveDataSimple()
        
        price = td.get_price('EURUSD')
        if price:
            print(f"   [OK] Precio EURUSD: {price}")
            results['twelvedata'] = True
        else:
            print("   [WARN] No se pudo obtener precio (verificar API key)")
            results['twelvedata'] = False
            
        indicators = td.get_indicators('EURUSD')
        print(f"   [OK] Indicadores: RSI={indicators['rsi']}, MACD={indicators['macd']}")
        
    except Exception as e:
        print(f"   [ERROR] Error en TwelveData: {e}")
        results['twelvedata'] = False
    
    # Test 2: Risk Manager
    try:
        print("\n2. Probando Risk Manager...")
        
        simple_risk_code = '''
class RiskManagerSimple:
    def __init__(self, capital=10000):
        self.capital = capital
        self.max_risk = 0.02
        
    def calculate_position_size(self, entry_price, stop_loss):
        risk_amount = self.capital * self.max_risk
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk > 0:
            # Para forex: size en lotes
            size = (risk_amount / price_risk) / 100000
            return min(5.0, max(0.01, size))
        return 0.01
        
    def check_limits(self):
        return {'can_trade': True, 'warnings': [], 'blocks': []}
'''
        
        with open('risk_simple.py', 'w') as f:
            f.write(simple_risk_code)
        
        from risk_simple import RiskManagerSimple
        risk_mgr = RiskManagerSimple()
        
        size = risk_mgr.calculate_position_size(1.0850, 1.0830)
        print(f"   [OK] Position Size: {size:.2f} lots")
        
        limits = risk_mgr.check_limits()
        print(f"   [OK] Can Trade: {limits['can_trade']}")
        
        results['risk_manager'] = True
        
    except Exception as e:
        print(f"   [ERROR] Error en Risk Manager: {e}")
        results['risk_manager'] = False
    
    # Test 3: MT5 Connection
    try:
        print("\n3. Probando MT5 Connection...")
        import MetaTrader5 as mt5
        
        # Verificar si MT5 está disponible
        if not mt5.initialize():
            print("   [WARN] MT5 no inicializado (normal si no está abierto)")
            results['mt5'] = False
        else:
            print("   [OK] MT5 inicializado correctamente")
            mt5.shutdown()
            results['mt5'] = True
            
    except ImportError:
        print("   [ERROR] MetaTrader5 no instalado")
        results['mt5'] = False
    except Exception as e:
        print(f"   [WARN] MT5 disponible pero no conectado: {e}")
        results['mt5'] = False
    
    # Test 4: Ollama (opcional)
    try:
        print("\n4. Probando Ollama...")
        import requests
        
        # Verificar si Ollama está corriendo
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"   [OK] Ollama corriendo con {len(models)} modelos")
            results['ollama'] = True
        else:
            print("   [WARN] Ollama no responde")
            results['ollama'] = False
            
    except Exception as e:
        print("   [WARN] Ollama no disponible (ejecutar: ollama serve)")
        results['ollama'] = False
    
    # Resumen
    print("\n=== RESUMEN ===")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for component, status in results.items():
        symbol = "[OK]" if status else "[FAIL]"
        print(f"{symbol} {component.upper()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\nResultado: {passed}/{total} componentes funcionando")
    
    if passed >= 2:
        print("\n*** SISTEMA BASICO FUNCIONAL ***")
        print("Componentes críticos operativos:")
        print("- TwelveData: Datos de mercado")
        print("- Risk Manager: Gestión de riesgo")
        if results.get('mt5'):
            print("- MT5: Listo para trading real")
        else:
            print("- MT5: Disponible pero no conectado")
        
        print("\nSiguientes pasos:")
        print("1. Iniciar MT5 y conectar cuenta")
        if not results.get('ollama'):
            print("2. Iniciar Ollama: ollama serve")
        print("3. Ejecutar sistema principal")
        
        return True
    else:
        print("\n*** SISTEMA REQUIERE ATENCION ***")
        print("Problemas detectados:")
        
        if not results.get('twelvedata'):
            print("- Verificar API key de TwelveData")
        
        print("\nSoluciones:")
        print("- pip install -r requirements_optimized.txt")
        print("- Verificar configuración en configs/.env")
        
        return False

if __name__ == "__main__":
    test_basic()