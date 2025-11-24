#!/usr/bin/env python
"""
SISTEMA DE TRADING COMPLETO - TODOS LOS SIMBOLOS PRINCIPALES
Monitorea y ejecuta trades en: EURUSD, GBPUSD, XAUUSD, BTCUSD
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
    print("    SISTEMA DE TRADING COMPLETO - TODOS LOS SIMBOLOS")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configurar path del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    sys.path.insert(0, str(project_dir))
    
    try:
        # Importar componentes necesarios
        import MetaTrader5 as mt5
        from src.data.twelvedata_client import TwelveDataClient
        from AI_ATR_INTELLIGENT_RISK_CALCULATOR import AIATRIntelligentRiskCalculator
        
        # Solo BTCUSD - broker limitado a crypto trading
        symbols = ['BTCUSDm']
        
        print("Inicializando componentes...")
        
        # Inicializar MT5
        if not mt5.initialize():
            print("ERROR: No se pudo conectar a MT5")
            return 1
        
        # Crear cliente TwelveData
        data_client = TwelveDataClient()
        print("TwelveData conectado")
        
        # Inicializar calculadora inteligente de ATR
        atr_calculator = AIATRIntelligentRiskCalculator()
        print("🧠 AI ATR Calculator inicializado")
        
        # Informacion de cuenta
        account = mt5.account_info()
        if account:
            print(f"MT5 conectado: Cuenta {account.login}")
            print(f"Balance: ${account.balance:.2f}")
            print(f"Equity: ${account.equity:.2f}")
        
        # Funcion de analisis tecnico para cada simbolo
        def analyze_symbol_technical(symbol):
            """Analisis tecnico completo"""
            try:
                # Convertir simbolo MT5 a TwelveData
                td_symbol = symbol.replace('m', '').replace('XAU', 'XAU/').replace('BTC', 'BTC/')
                if td_symbol == 'EURUSD':
                    td_symbol = 'EUR/USD'
                elif td_symbol == 'GBPUSD':
                    td_symbol = 'GBP/USD'
                elif td_symbol == 'XAUUSD':
                    td_symbol = 'XAU/USD'
                elif td_symbol == 'BTCUSD':
                    td_symbol = 'BTC/USD'
                
                # Obtener datos historicos
                df = data_client.get_time_series(td_symbol, "5min", 100)
                if df is None or len(df) < 50:
                    return {'signal': 'NO_OPERAR', 'confidence': 0, 'symbol': symbol, 'error': 'Sin datos suficientes'}
                
                # Calcular indicadores tecnicos
                close_prices = df['close'].values
                high_prices = df['high'].values
                low_prices = df['low'].values
                
                # RSI (14 periodos)
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
                
                # Medias moviles
                ma_short = sum(close_prices[-10:]) / 10 if len(close_prices) >= 10 else close_prices[-1]
                ma_long = sum(close_prices[-20:]) / 20 if len(close_prices) >= 20 else close_prices[-1]
                
                # Bollinger Bands
                ma_bb = sum(close_prices[-20:]) / 20 if len(close_prices) >= 20 else close_prices[-1]
                std_dev = (sum([(x - ma_bb)**2 for x in close_prices[-20:]]) / 20)**0.5 if len(close_prices) >= 20 else 0
                bb_upper = ma_bb + (2 * std_dev)
                bb_lower = ma_bb - (2 * std_dev)
                
                current_price = close_prices[-1]
                
                # Sistema de scoring avanzado
                score = 0
                reasons = []
                
                # RSI (peso: 25%)
                if rsi < 30:
                    score += 25
                    reasons.append("RSI sobreventa (alcista)")
                elif rsi > 70:
                    score -= 25
                    reasons.append("RSI sobrecompra (bajista)")
                elif 45 <= rsi <= 55:
                    score += 10
                    reasons.append("RSI neutral")
                
                # Cruce de medias (peso: 20%)
                if ma_short > ma_long * 1.001:  # 0.1% diferencia minima
                    score += 20
                    reasons.append("MA alcista")
                elif ma_short < ma_long * 0.999:
                    score -= 20
                    reasons.append("MA bajista")
                
                # Bollinger Bands (peso: 20%)
                if current_price <= bb_lower:
                    score += 20
                    reasons.append("Precio en BB inferior (alcista)")
                elif current_price >= bb_upper:
                    score -= 20
                    reasons.append("Precio en BB superior (bajista)")
                
                # Momentum (peso: 15%)
                if len(close_prices) >= 5:
                    momentum = (close_prices[-1] / close_prices[-5] - 1) * 100
                    if momentum > 0.2:
                        score += 15
                        reasons.append("Momentum positivo fuerte")
                    elif momentum < -0.2:
                        score -= 15
                        reasons.append("Momentum negativo fuerte")
                    elif momentum > 0:
                        score += 5
                        reasons.append("Momentum positivo")
                
                # Patron de precios (peso: 10%)
                if len(close_prices) >= 3:
                    if close_prices[-1] > close_prices[-2] > close_prices[-3]:
                        score += 10
                        reasons.append("Tendencia alcista corto plazo")
                    elif close_prices[-1] < close_prices[-2] < close_prices[-3]:
                        score -= 10
                        reasons.append("Tendencia bajista corto plazo")
                
                # Volatilidad (peso: 10%)
                if len(high_prices) >= 10 and len(low_prices) >= 10:
                    volatility = sum([high_prices[i] - low_prices[i] for i in range(-10, 0)]) / 10
                    avg_price = sum(close_prices[-10:]) / 10
                    vol_ratio = volatility / avg_price * 100
                    
                    if 0.5 <= vol_ratio <= 2.0:  # Volatilidad optima
                        score += 10
                        reasons.append("Volatilidad optima")
                    elif vol_ratio > 3.0:
                        score -= 5
                        reasons.append("Volatilidad muy alta")
                
                # Calcular confianza (0-100%)
                confidence = min(max((score + 50), 0), 100)
                
                # Determinar senal
                if score >= 30:
                    signal = 'BUY'
                elif score <= -30:
                    signal = 'SELL'
                else:
                    signal = 'NO_OPERAR'
                
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'symbol': symbol,
                    'current_price': current_price,
                    'rsi': rsi,
                    'ma_short': ma_short,
                    'ma_long': ma_long,
                    'score': score,
                    'reasons': reasons,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                
            except Exception as e:
                return {'signal': 'NO_OPERAR', 'confidence': 0, 'symbol': symbol, 'error': str(e)}
        
        # Funcion para ejecutar trades
        def execute_trade_smart(signal_data):
            """Ejecutar trade con gestion de riesgo inteligente"""
            try:
                symbol = signal_data['symbol']
                signal = signal_data['signal']
                confidence = signal_data['confidence']
                price = signal_data['current_price']
                
                # Obtener info del simbolo primero
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is None:
                    print(f"  -> Error: No se pudo obtener info de {symbol}")
                    return False
                
                # Obtener precios actuales de mercado
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    print(f"  -> Error: No se pudo obtener tick de {symbol}")
                    return False
                
                # Usar precios actuales del mercado
                if signal == 'BUY':
                    price = tick.ask  # Comprar al ask
                    order_type = mt5.ORDER_TYPE_BUY
                else:
                    price = tick.bid  # Vender al bid
                    order_type = mt5.ORDER_TYPE_SELL
                
                # Calcular tamaño de posicion basado en confianza
                if confidence >= 80:
                    volume = 0.02  # Posicion mas grande para alta confianza
                elif confidence >= 70:
                    volume = 0.01  # Posicion media
                else:
                    volume = 0.01  # Posicion minima
                
                # Verificar volumen minimo y maximo
                volume = max(symbol_info.volume_min, min(volume, symbol_info.volume_max))
                
                point = symbol_info.point
                digits = symbol_info.digits
                
                # Obtener distancia minima de stops en puntos
                stops_level = symbol_info.trade_stops_level
                if stops_level == 0:
                    stops_level = 20  # Default si no hay nivel definido
                
                # Calcular spread actual
                spread = (tick.ask - tick.bid) / point
                
                # 🧠 CALCULO INTELIGENTE DE SL/TP CON ATR Y AI
                print(f"  -> 🧠 Calculando SL/TP inteligente con ATR para {symbol}...")
                
                # Preparar datos de la señal para el AI
                signal_strength_data = {
                    'strength_score': confidence / 100.0,  # Convertir confianza a score 0-1
                    'strength_class': 'VERY_STRONG' if confidence >= 85 else 
                                    'STRONG' if confidence >= 75 else 
                                    'MODERATE' if confidence >= 65 else 'WEAK'
                }
                
                # Calcular SL/TP con ATR inteligente
                atr_symbol = 'BTC/USD' if 'BTC' in symbol else symbol.replace('m', '')  # Ajustar para API
                
                try:
                    atr_calculation = atr_calculator.calculate_intelligent_sl_tp(
                        atr_symbol, signal, signal_strength_data, price
                    )
                    
                    sl = round(atr_calculation['sl_price'], digits)
                    tp = round(atr_calculation['tp_price'], digits)
                    
                    print(f"     🎯 ATR SL/TP calculado:")
                    print(f"     Volatilidad: {atr_calculation['calculation_info'].get('volatility_class', 'N/A')}")
                    print(f"     SL distancia: {atr_calculation['sl_distance']:.1f}")
                    print(f"     TP distancia: {atr_calculation['tp_distance']:.1f}")
                    
                except Exception as atr_error:
                    print(f"     ⚠️  Error en ATR, usando fallback: {atr_error}")
                    # Fallback mejorado basado en el análisis previo
                    if 'BTC' in symbol:
                        sl_distance = max(stops_level + 100, 1200) * point  # Más conservador
                        tp_distance = max(stops_level + 200, 2400) * point  # Ratio 1:2
                    elif 'XAU' in symbol:
                        sl_distance = max(stops_level + 20, 200) * point
                        tp_distance = max(stops_level + 40, 400) * point
                    else:
                        sl_distance = max(stops_level + 10, 50) * point
                        tp_distance = max(stops_level + 20, 100) * point
                    
                    if signal == 'BUY':
                        sl = round(price - sl_distance, digits)
                        tp = round(price + tp_distance, digits)
                    else:
                        sl = round(price + sl_distance, digits)
                        tp = round(price - tp_distance, digits)
                
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
                    "comment": f"AI-ATR-{signal}-{confidence:.0f}%",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # Enviar orden
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"  -> TRADE EJECUTADO: {symbol} {signal} #{result.order}")
                    print(f"     Vol: {volume}, Precio: {price:.5f}")
                    print(f"     SL: {sl:.5f}, TP: {tp:.5f}")
                    print(f"     Confianza: {confidence:.1f}%")
                    return True
                else:
                    print(f"  -> Error: {result.comment}")
                    return False
                
            except Exception as e:
                print(f"  -> Error ejecutando: {e}")
                return False
        
        print("\\nESTADO INICIAL:")
        print(f"Simbolos: {', '.join(symbols)}")
        print(f"Metodo: ANALISIS TECNICO AVANZADO - CRYPTO ESPECIALIZADO")
        print(f"Umbral minimo: 60% confianza (optimizado para BTCUSD)")
        print(f"Auto trading: ACTIVADO")
        
        print("\\n" + "=" * 60)
        print("INICIANDO SISTEMA DE TRADING COMPLETO...")
        print("=" * 60)
        print("Monitoreo activo de 4 simbolos principales:")
        print("- EURUSDm (EUR/USD)")
        print("- GBPUSDm (GBP/USD)")  
        print("- XAUUSDm (Oro/USD)")
        print("- BTCUSDm (Bitcoin/USD)")
        print("")
        print("Presiona Ctrl+C para detener")
        print("-" * 60)
        
        cycle_count = 0
        total_trades = 0
        
        while True:
            try:
                cycle_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                print(f"\\n[Ciclo {cycle_count:04d}] {current_time} - Analizando mercados...")
                
                valid_signals = []
                
                # Analizar cada simbolo
                for symbol in symbols:
                    print(f"  -> Analizando {symbol}")
                    result = analyze_symbol_technical(symbol)
                    
                    if 'error' in result:
                        print(f"     ERROR: {result['error']}")
                        continue
                    
                    signal = result['signal']
                    confidence = result['confidence']
                    score = result.get('score', 0)
                    
                    print(f"     {signal} ({confidence:.1f}%) - Score: {score}")
                    
                    # Mostrar razones principales
                    if result.get('reasons'):
                        top_reasons = result['reasons'][:2]  # Top 2 razones
                        print(f"     Razones: {', '.join(top_reasons)}")
                    
                    # Ejecutar si cumple criterios (optimizado para BTCUSD)
                    if signal in ['BUY', 'SELL'] and confidence >= 60:
                        print(f"     -> SEÑAL VALIDA: Ejecutando {signal}...")
                        
                        if execute_trade_smart(result):
                            total_trades += 1
                            valid_signals.append(result)
                        else:
                            print(f"     -> Trade fallido")
                    else:
                        print(f"     -> Señal descartada (confianza < 60%)")
                
                # Resumen del ciclo
                if valid_signals:
                    print(f"  -> {len(valid_signals)} trades ejecutados este ciclo")
                else:
                    print(f"  -> Sin trades ejecutados este ciclo")
                
                print(f"  -> Total trades ejecutados: {total_trades}")
                
                # Mostrar posiciones cada 5 ciclos
                if cycle_count % 5 == 0:
                    try:
                        positions = mt5.positions_get()
                        if positions:
                            print(f"\\n--- POSICIONES ABIERTAS ({len(positions)}) ---")
                            total_profit = 0
                            by_symbol = {}
                            
                            for pos in positions:
                                profit = pos.profit
                                total_profit += profit
                                symbol = pos.symbol
                                
                                if symbol not in by_symbol:
                                    by_symbol[symbol] = {'profit': 0, 'count': 0}
                                by_symbol[symbol]['profit'] += profit
                                by_symbol[symbol]['count'] += 1
                            
                            # Mostrar resumen por simbolo
                            for symbol, data in by_symbol.items():
                                print(f"  {symbol}: {data['count']} pos, P&L: ${data['profit']:.2f}")
                            
                            print(f"  TOTAL P&L: ${total_profit:.2f}")
                            
                            # Mostrar equity actual
                            account = mt5.account_info()
                            if account:
                                print(f"  Equity actual: ${account.equity:.2f}")
                        else:
                            print("\\n--- Sin posiciones abiertas ---")
                    except Exception as e:
                        print(f"Error obteniendo posiciones: {e}")
                
                # Esperar antes del siguiente ciclo
                print("Esperando 45 segundos...")
                time.sleep(45)
                
            except KeyboardInterrupt:
                print("\\n\\nSistema detenido por usuario")
                break
            except Exception as e:
                print(f"Error en ciclo: {e}")
                time.sleep(10)
        
        print("\\nCerrando conexiones...")
        mt5.shutdown()
        print("Sistema cerrado correctamente")
        print(f"Resumen final: {total_trades} trades ejecutados en {cycle_count} ciclos")
        
    except Exception as e:
        print(f"ERROR CRITICO: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())