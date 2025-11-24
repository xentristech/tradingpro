#!/usr/bin/env python
"""
SISTEMA DE TRADING TÉCNICO PURO - ALGO TRADER V3
Version que usa SOLO el generador técnico que funciona
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    print("=" * 70)
    print("    ALGO TRADER V3 - SISTEMA TECNICO PURO")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configurar path del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    sys.path.insert(0, str(project_dir))
    
    try:
        # Importar solo el sistema técnico que funciona
        print("Importando sistema tecnico directo...")
        
        # Importar directamente el método que funciona
        sys.path.insert(0, str(project_dir))
        import MetaTrader5 as mt5
        from src.data.twelvedata_client import TwelveDataClient
        from src.broker.mt5_connection import MT5Connection
        
        # Símbolos con mejor rendimiento según los datos
        symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
        
        print("Inicializando componentes...")
        
        # Inicializar MT5
        if not mt5.initialize():
            print("ERROR: No se pudo conectar a MT5")
            return 1
        
        # Crear conexión MT5 para trading
        mt5_conn = MT5Connection()
        if not mt5_conn.connect():
            print("ERROR: No se pudo conectar MT5 Connection")
            return 1
        
        print(f"MT5 conectado: Cuenta {mt5_conn.account_info.login}")
        print(f"Balance: ${mt5_conn.account_info.balance:.2f}")
        
        # Crear cliente TwelveData
        data_client = TwelveDataClient()
        print("TwelveData conectado")
        
        # Función técnica directa (copiada del generador que funciona)
        def analyze_symbol_technical(symbol):
            """Análisis técnico directo sin IA"""
            try:
                # Obtener datos de mercado
                df = data_client.get_historical_data(symbol, "1min", 100)
                if df is None or len(df) < 50:
                    return {'signal': 'NO_OPERAR', 'confidence': 0, 'symbol': symbol, 'error': 'Sin datos suficientes'}
                
                # Calcular indicadores técnicos básicos
                close_prices = df['close'].values
                
                # RSI simple
                delta = [close_prices[i] - close_prices[i-1] for i in range(1, len(close_prices))]
                gains = [d if d > 0 else 0 for d in delta]
                losses = [-d if d < 0 else 0 for d in delta]
                
                avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 0
                avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 0
                
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                # Media móvil simple
                ma_short = sum(close_prices[-10:]) / 10 if len(close_prices) >= 10 else close_prices[-1]
                ma_long = sum(close_prices[-20:]) / 20 if len(close_prices) >= 20 else close_prices[-1]
                
                current_price = close_prices[-1]
                
                # Lógica de señal técnica
                score = 0
                reasons = []
                
                # RSI
                if rsi < 30:
                    score += 20
                    reasons.append("RSI sobreventa")
                elif rsi > 70:
                    score -= 20
                    reasons.append("RSI sobrecompra")
                else:
                    score += 5
                    reasons.append("RSI neutral")
                
                # Cruce de medias
                if ma_short > ma_long:
                    score += 15
                    reasons.append("MA alcista")
                else:
                    score -= 15
                    reasons.append("MA bajista")
                
                # Precio vs MA
                price_vs_ma = (current_price / ma_short - 1) * 100
                if abs(price_vs_ma) < 0.5:
                    score += 10
                    reasons.append("Precio cerca de MA")
                
                # Momentum básico
                if len(close_prices) >= 5:
                    momentum = (close_prices[-1] / close_prices[-5] - 1) * 100
                    if momentum > 0.1:
                        score += 10
                        reasons.append("Momentum positivo")
                    elif momentum < -0.1:
                        score -= 10
                        reasons.append("Momentum negativo")
                
                # Calcular confianza
                confidence = min(max((score + 50), 0), 100)
                
                # Determinar señal
                if score > 25:
                    signal = 'BUY'
                elif score < -25:
                    signal = 'SELL'
                else:
                    signal = 'NO_OPERAR'
                
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'symbol': symbol,
                    'current_price': current_price,
                    'rsi': rsi,
                    'score': score,
                    'reasons': reasons,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                
            except Exception as e:
                return {'signal': 'NO_OPERAR', 'confidence': 0, 'symbol': symbol, 'error': str(e)}
        
        # Función para ejecutar trade
        def execute_trade_direct(signal_data):
            """Ejecutar trade directamente"""
            try:
                symbol = signal_data['symbol']
                signal = signal_data['signal']
                price = signal_data['current_price']
                
                # Calcular tamaño de posición (0.01 lotes)
                volume = 0.01
                
                # Calcular SL y TP básicos
                if signal == 'BUY':
                    sl = price * 0.995  # 0.5% SL
                    tp = price * 1.01   # 1% TP
                    order_type = mt5.ORDER_TYPE_BUY
                elif signal == 'SELL':
                    sl = price * 1.005  # 0.5% SL  
                    tp = price * 0.99   # 1% TP
                    order_type = mt5.ORDER_TYPE_SELL
                else:
                    return False
                
                # Preparar orden
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": volume,
                    "type": order_type,
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": 20,
                    "magic": 123456,
                    "comment": f"AlgoTrader-{signal}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # Enviar orden
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"  -> TRADE EJECUTADO: {symbol} {signal} #{result.order}")
                    print(f"     Precio: {price:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")
                    return True
                else:
                    print(f"  -> Error ejecutando trade: {result.comment}")
                    return False
                
            except Exception as e:
                print(f"  -> Error en execute_trade: {e}")
                return False
        
        print("\nESTADO INICIAL:")
        print(f"Simbolos: {', '.join(symbols)}")
        print(f"Metodo: ANALISIS TECNICO PURO")
        print(f"Auto trading: ACTIVADO")
        print(f"Umbral minimo: 60% confianza")
        
        print("\n" + "=" * 50)
        print("INICIANDO CICLO DE TRADING TÉCNICO...")
        print("=" * 50)
        print("Presiona Ctrl+C para detener")
        print("-" * 50)
        
        cycle_count = 0
        trades_executed = 0
        
        while True:
            try:
                cycle_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[Ciclo {cycle_count:04d}] {current_time} - Análisis Técnico")
                
                signals = []
                
                # Analizar cada símbolo
                for symbol in symbols:
                    print(f"  -> Analizando {symbol}")
                    result = analyze_symbol_technical(symbol)
                    
                    if 'error' in result:
                        print(f"     ERROR: {result['error']}")
                        continue
                    
                    signal = result['signal']
                    confidence = result['confidence']
                    
                    print(f"     {signal} ({confidence:.1f}%) - Score: {result.get('score', 0)}")
                    
                    # Ejecutar si es señal válida
                    if signal in ['BUY', 'SELL'] and confidence >= 60:
                        print(f"     -> SEÑAL VÁLIDA: {signal} {confidence:.1f}%")
                        
                        # Ejecutar trade
                        if execute_trade_direct(result):
                            trades_executed += 1
                            signals.append(result)
                    else:
                        print(f"     -> Señal descartada (confianza < 60%)")
                
                # Resumen del ciclo
                if signals:
                    print(f"  -> {len(signals)} trades ejecutados en este ciclo")
                else:
                    print(f"  -> Sin trades en este ciclo")
                
                print(f"  -> Total trades hoy: {trades_executed}")
                
                # Mostrar posiciones actuales cada 5 ciclos
                if cycle_count % 5 == 0:
                    try:
                        positions = mt5.positions_get()
                        if positions:
                            print(f"\n--- POSICIONES ABIERTAS ({len(positions)}) ---")
                            total_profit = 0
                            for pos in positions:
                                total_profit += pos.profit
                                print(f"  {pos.symbol}: ${pos.profit:.2f} ({pos.volume} lots)")
                            print(f"  Total P&L: ${total_profit:.2f}")
                        else:
                            print("\n--- Sin posiciones abiertas ---")
                    except Exception as e:
                        print(f"Error obteniendo posiciones: {e}")
                
                # Esperar 30 segundos
                print("Esperando 30 segundos...")
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n\nSistema detenido por usuario")
                break
            except Exception as e:
                print(f"Error en ciclo: {e}")
                time.sleep(5)
        
        print("\nCerrando conexiones...")
        mt5.shutdown()
        print("Sistema cerrado correctamente")
        
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())