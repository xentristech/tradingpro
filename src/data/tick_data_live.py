"""
Tick Data Live - Sistema de datos tick bid/ask en tiempo real
===========================================================

Calcula y muestra los movimientos de precio tick por tick con bid/ask spread
"""

import os
import time
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv

try:
    from twelvedata import TDClient
except ImportError:
    print("ERROR: Instalar twelvedata con: pip install twelvedata")
    exit(1)

load_dotenv()

class LiveTickData:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("API key no encontrada")
        
        self.client = TDClient(apikey=self.api_key)
        self.tick_data = {}
        self.is_running = False
        
        # Símbolos para monitorear
        self.symbols = ['BTC/USD', 'XAU/USD', 'EUR/USD', 'GBP/USD', 'USD/JPY']
        
        # Configuración de tick
        self.tick_interval = 5  # segundos entre actualizaciones
        self.max_ticks = 100    # máximo de ticks a mantener
        
        print("Live Tick Data System iniciado")
        print(f"Símbolos: {', '.join(self.symbols)}")
        print(f"Intervalo: {self.tick_interval} segundos")
    
    def calculate_bid_ask_from_price(self, price, symbol):
        """Calcular bid/ask aproximado desde el precio"""
        # Spreads típicos por instrumento (en pips/puntos)
        spreads = {
            'EUR/USD': 0.00015,  # 1.5 pips
            'GBP/USD': 0.00020,  # 2.0 pips
            'USD/JPY': 0.015,    # 1.5 pips
            'XAU/USD': 0.50,     # 50 centavos
            'BTC/USD': 25.0      # 25 dólares
        }
        
        spread = spreads.get(symbol, price * 0.0001)  # 0.01% por defecto
        
        bid = price - (spread / 2)
        ask = price + (spread / 2)
        
        return bid, ask
    
    def get_current_price(self, symbol):
        """Obtener precio actual de un símbolo"""
        try:
            # Usar quote endpoint para datos más frecuentes
            quote = self.client.quote(symbol=symbol)
            price_data = quote.as_json()
            
            if price_data and 'close' in price_data:
                price = float(price_data['close'])
                return price
            else:
                return None
                
        except Exception as e:
            print(f"Error obteniendo precio de {symbol}: {e}")
            return None
    
    def calculate_tick_movement(self, symbol, current_price):
        """Calcular movimiento del tick"""
        if symbol not in self.tick_data:
            return 0, 0, "INICIAL"
        
        previous_ticks = self.tick_data[symbol]
        if not previous_ticks:
            return 0, 0, "INICIAL"
        
        last_tick = previous_ticks[-1]
        last_price = last_tick['price']
        
        # Calcular movimiento
        tick_change = current_price - last_price
        tick_change_pct = (tick_change / last_price * 100) if last_price != 0 else 0
        
        # Determinar dirección
        if tick_change > 0:
            direction = "UP"
        elif tick_change < 0:
            direction = "DOWN"
        else:
            direction = "FLAT"
        
        return tick_change, tick_change_pct, direction
    
    def update_tick_data(self, symbol):
        """Actualizar datos tick para un símbolo"""
        try:
            current_price = self.get_current_price(symbol)
            if current_price is None:
                return False
            
            # Calcular bid/ask
            bid, ask = self.calculate_bid_ask_from_price(current_price, symbol)
            spread = ask - bid
            
            # Calcular movimiento del tick
            tick_change, tick_change_pct, direction = self.calculate_tick_movement(symbol, current_price)
            
            # Crear registro de tick
            tick_record = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'price': current_price,
                'bid': bid,
                'ask': ask,
                'spread': spread,
                'tick_change': tick_change,
                'tick_change_pct': tick_change_pct,
                'direction': direction
            }
            
            # Guardar en histórico
            if symbol not in self.tick_data:
                self.tick_data[symbol] = []
            
            self.tick_data[symbol].append(tick_record)
            
            # Mantener solo los últimos N ticks
            if len(self.tick_data[symbol]) > self.max_ticks:
                self.tick_data[symbol] = self.tick_data[symbol][-self.max_ticks:]
            
            return True
            
        except Exception as e:
            print(f"Error actualizando tick de {symbol}: {e}")
            return False
    
    def get_tick_summary(self, symbol, period_minutes=5):
        """Obtener resumen de ticks en un período"""
        if symbol not in self.tick_data or not self.tick_data[symbol]:
            return None
        
        # Filtrar ticks del período
        cutoff_time = datetime.now() - timedelta(minutes=period_minutes)
        recent_ticks = [tick for tick in self.tick_data[symbol] 
                       if tick['timestamp'] >= cutoff_time]
        
        if not recent_ticks:
            return None
        
        # Calcular estadísticas
        prices = [tick['price'] for tick in recent_ticks]
        spreads = [tick['spread'] for tick in recent_ticks]
        changes = [tick['tick_change'] for tick in recent_ticks if tick['direction'] != 'INICIAL']
        
        up_ticks = len([t for t in recent_ticks if t['direction'] == 'UP'])
        down_ticks = len([t for t in recent_ticks if t['direction'] == 'DOWN'])
        flat_ticks = len([t for t in recent_ticks if t['direction'] == 'FLAT'])
        
        summary = {
            'symbol': symbol,
            'period_minutes': period_minutes,
            'total_ticks': len(recent_ticks),
            'current_price': recent_ticks[-1]['price'],
            'current_bid': recent_ticks[-1]['bid'],
            'current_ask': recent_ticks[-1]['ask'],
            'current_spread': recent_ticks[-1]['spread'],
            'high_price': max(prices),
            'low_price': min(prices),
            'price_range': max(prices) - min(prices),
            'avg_spread': np.mean(spreads),
            'up_ticks': up_ticks,
            'down_ticks': down_ticks,
            'flat_ticks': flat_ticks,
            'tick_momentum': up_ticks - down_ticks,
            'last_direction': recent_ticks[-1]['direction'],
            'last_change': recent_ticks[-1]['tick_change'],
            'last_change_pct': recent_ticks[-1]['tick_change_pct'],
            'volatility': np.std(changes) if changes else 0
        }
        
        return summary
    
    def display_live_ticks(self):
        """Mostrar ticks en tiempo real"""
        print("\n" + "="*80)
        print(f" LIVE TICK DATA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        for symbol in self.symbols:
            summary = self.get_tick_summary(symbol)
            if summary:
                direction_symbol = {"UP": "↑", "DOWN": "↓", "FLAT": "→"}.get(summary['last_direction'], "•")
                color_code = {"UP": "[UP]", "DOWN": "[DN]", "FLAT": "[--]"}.get(summary['last_direction'], "[??]")
                
                print(f"\n{symbol:<8} | {summary['current_price']:<12.4f} | "
                      f"Bid: {summary['current_bid']:<10.4f} | Ask: {summary['current_ask']:<10.4f} | "
                      f"Spread: {summary['current_spread']:<8.4f}")
                
                print(f"         | Tick: {color_code} {direction_symbol} {summary['last_change']:+.4f} "
                      f"({summary['last_change_pct']:+.2f}%) | "
                      f"Ticks 5min: ↑{summary['up_ticks']} ↓{summary['down_ticks']} →{summary['flat_ticks']}")
                
                print(f"         | Range 5min: {summary['low_price']:.4f} - {summary['high_price']:.4f} | "
                      f"Momentum: {summary['tick_momentum']:+d} | Vol: {summary['volatility']:.4f}")
    
    def save_tick_data_json(self):
        """Guardar datos tick en JSON"""
        try:
            output_data = {}
            
            for symbol in self.symbols:
                if symbol in self.tick_data:
                    # Convertir últimos 20 ticks a formato JSON
                    recent_ticks = self.tick_data[symbol][-20:]
                    
                    output_data[symbol] = {
                        'summary': self.get_tick_summary(symbol),
                        'recent_ticks': []
                    }
                    
                    for tick in recent_ticks:
                        tick_json = {
                            'timestamp': tick['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            'price': tick['price'],
                            'bid': tick['bid'],
                            'ask': tick['ask'],
                            'spread': tick['spread'],
                            'tick_change': tick['tick_change'],
                            'tick_change_pct': tick['tick_change_pct'],
                            'direction': tick['direction']
                        }
                        output_data[symbol]['recent_ticks'].append(tick_json)
            
            # Guardar archivo
            filename = Path("tick_data_live.json")
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            return str(filename)
            
        except Exception as e:
            print(f"Error guardando tick data: {e}")
            return None
    
    def start_live_monitoring(self):
        """Iniciar monitoreo en tiempo real"""
        if self.is_running:
            print("Sistema ya está ejecutándose")
            return
        
        self.is_running = True
        
        def monitoring_loop():
            cycle = 1
            
            while self.is_running:
                try:
                    print(f"\n[CICLO {cycle}] Actualizando tick data...")
                    
                    # Actualizar todos los símbolos
                    success_count = 0
                    for symbol in self.symbols:
                        if self.update_tick_data(symbol):
                            success_count += 1
                        time.sleep(0.5)  # Pausa entre símbolos
                    
                    print(f"[INFO] {success_count}/{len(self.symbols)} símbolos actualizados")
                    
                    # Mostrar datos actuales
                    self.display_live_ticks()
                    
                    # Guardar datos
                    json_file = self.save_tick_data_json()
                    if json_file:
                        print(f"\n[GUARDADO] Datos tick guardados en: {json_file}")
                    
                    print(f"\n[ESPERA] Próxima actualización en {self.tick_interval} segundos...")
                    print("="*80)
                    
                    cycle += 1
                    
                    # Esperar intervalo
                    sleep_time = 0
                    while sleep_time < self.tick_interval and self.is_running:
                        time.sleep(1)
                        sleep_time += 1
                    
                except Exception as e:
                    print(f"Error en loop de monitoreo: {e}")
                    time.sleep(5)
        
        # Ejecutar en hilo separado
        self.monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        print("Sistema de tick data en tiempo real iniciado")
        return True
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.is_running = False
        print("Sistema de tick data detenido")

def main():
    try:
        tick_system = LiveTickData()
        
        print("LIVE TICK DATA SYSTEM")
        print("="*40)
        print("Características:")
        print("  • Precios bid/ask calculados en tiempo real")
        print("  • Movimientos tick por tick")
        print("  • Análisis de momentum y volatilidad")
        print("  • Datos guardados en JSON")
        print("  • 5 pares principales de forex y commodities")
        print("="*40)
        
        # Iniciar sistema
        tick_system.start_live_monitoring()
        
        print("\nPresiona Ctrl+C para detener el sistema")
        
        try:
            # Mantener ejecutándose
            while tick_system.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[DETENIENDO] Sistema detenido por usuario")
            
        finally:
            tick_system.stop_monitoring()
            
    except Exception as e:
        print(f"Error fatal: {e}")

if __name__ == "__main__":
    main()