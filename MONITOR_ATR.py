#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor con cálculo de SL/TP basado en ATR real
"""

import MetaTrader5 as mt5
import time
import numpy as np
from datetime import datetime
import requests

class ATRMonitor:
    def __init__(self):
        self.check_interval = 10  # segundos
        self.atr_period = 14
        self.sl_multiplier = 2.0  # 2x ATR para SL
        self.tp_multiplier = 3.0  # 3x ATR para TP
        
    def connect(self):
        """Conecta a MT5"""
        if not mt5.initialize():
            print("[ERROR] No se pudo conectar a MT5")
            return False
            
        account_info = mt5.account_info()
        if account_info:
            print(f"[CUENTA] {account_info.login} | Balance: ${account_info.balance:.2f}")
            return True
        return False
    
    def calculate_atr(self, symbol, timeframe=mt5.TIMEFRAME_H1, periods=14):
        """Calcula ATR usando datos de MT5"""
        try:
            # Obtener datos OHLC
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, periods + 10)
            
            if rates is None or len(rates) < periods:
                print(f"    [ERROR] No se pudieron obtener datos para {symbol}")
                return None
            
            # Calcular True Range
            high = np.array([r['high'] for r in rates])
            low = np.array([r['low'] for r in rates])
            close = np.array([r['close'] for r in rates])
            
            # TR = max(H-L, |H-Cp|, |L-Cp|)
            tr_list = []
            for i in range(1, len(rates)):
                tr1 = high[i] - low[i]
                tr2 = abs(high[i] - close[i-1])
                tr3 = abs(low[i] - close[i-1])
                tr_list.append(max(tr1, tr2, tr3))
            
            if len(tr_list) < periods:
                return None
                
            # Calcular ATR (promedio de True Range)
            atr = np.mean(tr_list[-periods:])
            
            print(f"    [ATR] {symbol}: {atr:.5f} (TF: {timeframe})")
            return atr
            
        except Exception as e:
            print(f"    [ERROR ATR] {symbol}: {str(e)}")
            return None
    
    def get_atr_from_api(self, symbol):
        """Obtiene ATR desde TwelveData API como respaldo"""
        try:
            # Mapear simbolos MT5 a TwelveData
            symbol_map = {
                'XAUUSDm': 'XAUUSD',
                'BTCUSDm': 'BTCUSD',
                'EURUSD': 'EUR/USD',
                'GBPUSD': 'GBP/USD',
                'USDJPY': 'USD/JPY'
            }
            
            api_symbol = symbol_map.get(symbol, symbol)
            
            # API TwelveData (usar clave gratuita)
            url = f"https://api.twelvedata.com/atr?symbol={api_symbol}&interval=1h&apikey=demo"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    atr_value = float(data['values'][0]['atr'])
                    print(f"    [ATR API] {symbol}: {atr_value:.5f}")
                    return atr_value
            
        except Exception as e:
            print(f"    [ERROR API] {symbol}: {str(e)}")
        
        return None
    
    def calculate_sl_tp_with_atr(self, position):
        """Calcula SL y TP usando ATR"""
        symbol = position.symbol
        
        # Intentar obtener ATR de MT5 primero
        atr = self.calculate_atr(symbol)
        
        # Si falla, usar API
        if atr is None:
            atr = self.get_atr_from_api(symbol)
        
        # Si ambos fallan, usar valor estimado por símbolo
        if atr is None:
            if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
                atr = 25.0  # ATR estimado para oro
            elif "BTC" in symbol.upper():
                atr = 1000.0  # ATR estimado para BTC
            else:
                atr = 0.001   # ATR estimado para forex
            print(f"    [ATR ESTIMADO] {symbol}: {atr:.5f}")
        
        # Obtener info del símbolo
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return None, None
            
        price = position.price_current
        
        # Calcular distancias basadas en ATR
        sl_distance = atr * self.sl_multiplier
        tp_distance = atr * self.tp_multiplier
        
        # Calcular niveles
        if position.type == 0:  # BUY
            sl_price = price - sl_distance
            tp_price = price + tp_distance
        else:  # SELL
            sl_price = price + sl_distance
            tp_price = price - tp_distance
            
        # Redondear según los decimales del símbolo
        sl_price = round(sl_price, symbol_info.digits)
        tp_price = round(tp_price, symbol_info.digits)
        
        print(f"    [CALC] ATR: {atr:.5f} | SL: {sl_price:.5f} | TP: {tp_price:.5f}")
        
        return sl_price, tp_price
    
    def fix_position_atr(self, position):
        """Corrige posición usando ATR"""
        print(f"\n  [CORRIGIENDO] #{position.ticket} {position.symbol}")
        
        sl_price, tp_price = self.calculate_sl_tp_with_atr(position)
        
        if sl_price is None or tp_price is None:
            print(f"    [ERROR] No se pudo calcular SL/TP")
            return False
        
        # Solo configurar lo que falta
        if position.sl == 0:
            sl_to_set = sl_price
        else:
            sl_to_set = position.sl
            
        if position.tp == 0:
            tp_to_set = tp_price  
        else:
            tp_to_set = position.tp
        
        # Crear request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": sl_to_set,
            "tp": tp_to_set,
            "magic": 234000,
            "comment": "ATR Monitor"
        }
        
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"    [OK] SL/TP configurados con ATR")
            return True
        else:
            if result:
                print(f"    [ERROR] Código: {result.retcode}")
            return False
    
    def run(self):
        """Ejecuta el monitor ATR"""
        print("\n" + "="*60)
        print("     MONITOR ATR - STOP LOSS Y TAKE PROFIT")
        print("="*60)
        print(f"SL: {self.sl_multiplier}x ATR | TP: {self.tp_multiplier}x ATR")
        print(f"Verificación cada {self.check_interval} segundos")
        print("Presiona Ctrl+C para detener\n")
        
        if not self.connect():
            return
            
        cycle = 0
        total_fixed = 0
        
        try:
            while True:
                cycle += 1
                print(f"[Ciclo {cycle:04d}] {datetime.now().strftime('%H:%M:%S')}")
                
                # Verificar posiciones
                positions = mt5.positions_get()
                
                if not positions:
                    print("  [INFO] No hay posiciones abiertas")
                else:
                    print(f"  [SCAN] {len(positions)} posiciones encontradas")
                    
                    for pos in positions:
                        needs_sl = pos.sl == 0
                        needs_tp = pos.tp == 0
                        
                        if needs_sl or needs_tp:
                            status = []
                            if needs_sl: status.append("Sin SL")
                            if needs_tp: status.append("Sin TP")
                            
                            print(f"  [ALERTA] #{pos.ticket} {pos.symbol} - {' | '.join(status)}")
                            
                            if self.fix_position_atr(pos):
                                total_fixed += 1
                                print(f"  [SUCCESS] Posición protegida con ATR")
                            else:
                                print(f"  [FAILED] No se pudo corregir")
                        else:
                            print(f"  [OK] #{pos.ticket} {pos.symbol} ya protegida")
                
                print()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n[MONITOR DETENIDO]")
            print(f"Total corregidas: {total_fixed}")
        finally:
            mt5.shutdown()

def main():
    monitor = ATRMonitor()
    monitor.run()

if __name__ == "__main__":
    main()