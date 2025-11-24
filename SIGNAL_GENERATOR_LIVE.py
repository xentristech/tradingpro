#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GENERADOR DE SEÑALES DE TRADING EN TIEMPO REAL
==================================================
Sistema profesional de generación de señales con análisis multi-indicador
Versión: 4.0 - Optimizado para NAS100 y mercados principales
"""

import requests
import time
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from colorama import init, Fore, Back, Style
import os

# Inicializar colorama para Windows
init(autoreset=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('signals_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProfessionalSignalGenerator:
    """
    Generador profesional de señales de trading con análisis avanzado
    """
    
    def __init__(self):
        # API Configuration
        self.api_key = '915b2ea02f7d49b986c1ae27d2711c73'  # TwelveData API
        self.base_url = 'https://api.twelvedata.com'
        
        # Símbolos principales con mapeo correcto
        self.symbols = {
            'NAS100': 'NAS100',      # NASDAQ 100
            'BTCUSD': 'BTC/USD',     # Bitcoin
            'XAUUSD': 'XAU/USD',     # Oro
            'EURUSD': 'EUR/USD',     # Euro/Dólar
            'GBPUSD': 'GBP/USD',     # Libra/Dólar
            'US500': 'SPX',          # S&P 500
            'ETHUSD': 'ETH/USD',     # Ethereum
        }
        
        # Configuración de señales
        self.signal_thresholds = {
            'strong_buy': 70,
            'buy': 60,
            'neutral': 40,
            'sell': 30,
            'strong_sell': 20
        }
        
        logger.info("✅ Sistema de señales profesional inicializado")
        self.print_header()
    
    def print_header(self):
        """Imprime el header del sistema"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}🚀 GENERADOR PROFESIONAL DE SEÑALES DE TRADING v4.0")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.WHITE}Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.WHITE}API: TwelveData | Símbolos: {len(self.symbols)}")
        print(f"{Fore.CYAN}{'='*80}\n")
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Obtiene cotización actual"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            url = f"{self.base_url}/quote"
            params = {
                'symbol': mapped_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo quote {symbol}: {e}")
            return None
    
    def get_technical_indicators(self, symbol: str, interval: str = '5min') -> Dict:
        """Obtiene indicadores técnicos múltiples"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            indicators = {}
            
            # Configuración de indicadores clave
            indicator_list = [
                ('rsi', {'time_period': 14}),
                ('macd', {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}),
                ('bbands', {'time_period': 20, 'series_type': 'close', 'sd': 2}),
                ('ema', {'time_period': 20}),
                ('ema', {'time_period': 50}, 'ema_50'),
                ('atr', {'time_period': 14}),
                ('adx', {'time_period': 14}),
                ('stoch', {'k_period': 14, 'd_period': 3, 'smooth_k': 3}),
            ]
            
            for config in indicator_list:
                if len(config) == 2:
                    indicator_name, params = config
                    key = indicator_name
                else:
                    indicator_name, params, key = config
                
                try:
                    url = f"{self.base_url}/{indicator_name}"
                    request_params = {
                        'symbol': mapped_symbol,
                        'interval': interval,
                        'outputsize': 5,
                        'apikey': self.api_key,
                        **params
                    }
                    
                    response = requests.get(url, params=request_params, timeout=8)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'values' in data and data['values']:
                            indicators[key] = data['values'][0]  # Último valor
                    
                    time.sleep(0.15)  # Rate limiting
                    
                except Exception as e:
                    logger.debug(f"Error con {indicator_name}: {e}")
                    continue
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error obteniendo indicadores: {e}")
            return {}
    
    def calculate_signal_score(self, indicators: Dict, quote: Dict) -> Tuple[float, List[str]]:
        """
        Calcula el score de la señal basado en múltiples indicadores
        """
        score = 50  # Score neutral inicial
        signals = []
        
        # Análisis RSI
        if 'rsi' in indicators:
            try:
                rsi_value = float(indicators['rsi']['rsi'])
                if rsi_value < 30:
                    score += 20
                    signals.append(f"📈 RSI sobreventa: {rsi_value:.1f}")
                elif rsi_value > 70:
                    score -= 20
                    signals.append(f"📉 RSI sobrecompra: {rsi_value:.1f}")
                else:
                    signals.append(f"➖ RSI neutral: {rsi_value:.1f}")
            except:
                pass
        
        # Análisis MACD
        if 'macd' in indicators:
            try:
                macd_hist = float(indicators['macd'].get('macd_histogram', 0))
                if macd_hist > 0:
                    score += 15
                    signals.append(f"📈 MACD positivo: {macd_hist:.4f}")
                else:
                    score -= 15
                    signals.append(f"📉 MACD negativo: {macd_hist:.4f}")
            except:
                pass
        
        # Análisis Bollinger Bands
        if 'bbands' in indicators and quote:
            try:
                current_price = float(quote.get('close', 0))
                upper = float(indicators['bbands'].get('upper_band', 0))
                lower = float(indicators['bbands'].get('lower_band', 0))
                middle = float(indicators['bbands'].get('middle_band', 0))
                
                if current_price < lower:
                    score += 15
                    signals.append(f"📈 Precio bajo BB inferior")
                elif current_price > upper:
                    score -= 15
                    signals.append(f"📉 Precio sobre BB superior")
                else:
                    position = ((current_price - lower) / (upper - lower)) * 100
                    signals.append(f"➖ BB posición: {position:.1f}%")
            except:
                pass
        
        # Análisis ADX (fuerza de tendencia)
        if 'adx' in indicators:
            try:
                adx_value = float(indicators['adx']['adx'])
                if adx_value > 25:
                    signals.append(f"💪 Tendencia fuerte: ADX {adx_value:.1f}")
                    score += 5  # Bonus por tendencia fuerte
                else:
                    signals.append(f"😴 Tendencia débil: ADX {adx_value:.1f}")
            except:
                pass
        
        # Análisis Stochastic
        if 'stoch' in indicators:
            try:
                k_value = float(indicators['stoch']['slow_k'])
                d_value = float(indicators['stoch']['slow_d'])
                
                if k_value < 20:
                    score += 10
                    signals.append(f"📈 Stoch sobreventa: K={k_value:.1f}")
                elif k_value > 80:
                    score -= 10
                    signals.append(f"📉 Stoch sobrecompra: K={k_value:.1f}")
            except:
                pass
        
        # Normalizar score entre 0-100
        score = max(0, min(100, score))
        
        return score, signals
    
    def determine_action(self, score: float) -> Tuple[str, str]:
        """Determina la acción basada en el score"""
        if score >= self.signal_thresholds['strong_buy']:
            return 'STRONG BUY', Fore.GREEN + Back.BLACK
        elif score >= self.signal_thresholds['buy']:
            return 'BUY', Fore.GREEN
        elif score <= self.signal_thresholds['strong_sell']:
            return 'STRONG SELL', Fore.RED + Back.BLACK
        elif score <= self.signal_thresholds['sell']:
            return 'SELL', Fore.RED
        else:
            return 'NEUTRAL', Fore.YELLOW
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """Análisis completo de un símbolo"""
        print(f"\n{Fore.CYAN}📊 Analizando {symbol}...")
        
        # Obtener datos
        quote = self.get_quote(symbol)
        indicators = self.get_technical_indicators(symbol)
        
        if not quote:
            return {'symbol': symbol, 'status': 'error', 'message': 'No se pudo obtener cotización'}
        
        # Calcular señal
        score, signals = self.calculate_signal_score(indicators, quote)
        action, color = self.determine_action(score)
        
        # Preparar resultado
        result = {
            'symbol': symbol,
            'price': float(quote.get('close', 0)),
            'change': float(quote.get('percent_change', 0)),
            'score': score,
            'action': action,
            'signals': signals,
            'timestamp': datetime.now().isoformat()
        }
        
        # Imprimir resultado formateado
        self.print_analysis_result(result, color)
        
        return result
    
    def print_analysis_result(self, result: Dict, color: str):
        """Imprime el resultado del análisis de forma formateada"""
        print(f"\n{Fore.WHITE}{'='*60}")
        print(f"{Fore.CYAN}🎯 {result['symbol']}")
        print(f"{Fore.WHITE}{'='*60}")
        
        # Información de precio
        change_color = Fore.GREEN if result['change'] > 0 else Fore.RED
        print(f"{Fore.WHITE}💰 Precio: ${result['price']:,.2f}")
        print(f"{change_color}📊 Cambio: {result['change']:+.2f}%")
        
        # Score y acción
        print(f"\n{Fore.CYAN}📈 ANÁLISIS TÉCNICO:")
        print(f"{Fore.WHITE}Score: {result['score']:.1f}/100")
        print(f"{color}🎯 SEÑAL: {result['action']}{Style.RESET_ALL}")
        
        # Señales individuales
        if result['signals']:
            print(f"\n{Fore.CYAN}📝 INDICADORES:")
            for signal in result['signals']:
                print(f"  {signal}")
        
        # Recomendación
        self.print_recommendation(result)
    
    def print_recommendation(self, result: Dict):
        """Imprime recomendaciones basadas en la señal"""
        print(f"\n{Fore.CYAN}💡 RECOMENDACIÓN:")
        
        if result['action'] == 'STRONG BUY':
            print(f"{Fore.GREEN}✅ Señal fuerte de COMPRA")
            print(f"{Fore.GREEN}   • Considerar entrada inmediata")
            print(f"{Fore.GREEN}   • Stop Loss: -2% desde entrada")
            print(f"{Fore.GREEN}   • Take Profit: +3-5% desde entrada")
        
        elif result['action'] == 'BUY':
            print(f"{Fore.GREEN}✅ Señal de COMPRA moderada")
            print(f"{Fore.GREEN}   • Esperar confirmación adicional")
            print(f"{Fore.GREEN}   • Stop Loss: -1.5% desde entrada")
            print(f"{Fore.GREEN}   • Take Profit: +2-3% desde entrada")
        
        elif result['action'] == 'STRONG SELL':
            print(f"{Fore.RED}⛔ Señal fuerte de VENTA")
            print(f"{Fore.RED}   • Considerar salida o short")
            print(f"{Fore.RED}   • Stop Loss: +2% desde entrada")
            print(f"{Fore.RED}   • Take Profit: -3-5% desde entrada")
        
        elif result['action'] == 'SELL':
            print(f"{Fore.RED}⛔ Señal de VENTA moderada")
            print(f"{Fore.RED}   • Reducir posición o esperar")
            print(f"{Fore.RED}   • Stop Loss: +1.5% desde entrada")
            print(f"{Fore.RED}   • Take Profit: -2-3% desde entrada")
        
        else:
            print(f"{Fore.YELLOW}⚠️ Mercado en rango - No operar")
            print(f"{Fore.YELLOW}   • Esperar señal más clara")
            print(f"{Fore.YELLOW}   • Observar niveles clave")
    
    def run_continuous_analysis(self, interval_seconds: int = 300):
        """Ejecuta análisis continuo cada X segundos"""
        print(f"\n{Fore.CYAN}🔄 Iniciando análisis continuo cada {interval_seconds} segundos...")
        print(f"{Fore.YELLOW}Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                # Hora actual
                print(f"\n{Fore.CYAN}{'='*80}")
                print(f"{Fore.WHITE}⏰ Ciclo de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{Fore.CYAN}{'='*80}")
                
                # Analizar todos los símbolos
                all_results = []
                for symbol in self.symbols.keys():
                    try:
                        result = self.analyze_symbol(symbol)
                        all_results.append(result)
                        time.sleep(1)  # Pequeña pausa entre símbolos
                    except Exception as e:
                        logger.error(f"Error analizando {symbol}: {e}")
                        continue
                
                # Resumen de señales
                self.print_summary(all_results)
                
                # Guardar resultados
                self.save_results(all_results)
                
                # Esperar hasta el próximo ciclo
                print(f"\n{Fore.YELLOW}⏳ Esperando {interval_seconds} segundos hasta el próximo análisis...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}🛑 Análisis detenido por el usuario")
            return
    
    def print_summary(self, results: List[Dict]):
        """Imprime un resumen de todas las señales"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📊 RESUMEN DE SEÑALES")
        print(f"{Fore.CYAN}{'='*80}")
        
        # Clasificar por tipo de señal
        strong_buys = [r for r in results if r.get('action') == 'STRONG BUY']
        buys = [r for r in results if r.get('action') == 'BUY']
        sells = [r for r in results if r.get('action') == 'SELL']
        strong_sells = [r for r in results if r.get('action') == 'STRONG SELL']
        neutrals = [r for r in results if r.get('action') == 'NEUTRAL']
        
        # Imprimir resumen
        if strong_buys:
            print(f"\n{Fore.GREEN}🚀 STRONG BUY ({len(strong_buys)}):")
            for r in strong_buys:
                print(f"   • {r['symbol']}: Score {r['score']:.1f}")
        
        if buys:
            print(f"\n{Fore.GREEN}✅ BUY ({len(buys)}):")
            for r in buys:
                print(f"   • {r['symbol']}: Score {r['score']:.1f}")
        
        if sells:
            print(f"\n{Fore.RED}📉 SELL ({len(sells)}):")
            for r in sells:
                print(f"   • {r['symbol']}: Score {r['score']:.1f}")
        
        if strong_sells:
            print(f"\n{Fore.RED}⛔ STRONG SELL ({len(strong_sells)}):")
            for r in strong_sells:
                print(f"   • {r['symbol']}: Score {r['score']:.1f}")
        
        if neutrals:
            print(f"\n{Fore.YELLOW}➖ NEUTRAL ({len(neutrals)}):")
            for r in neutrals:
                print(f"   • {r['symbol']}: Score {r['score']:.1f}")
        
        # Mejor oportunidad
        if results:
            best = max(results, key=lambda x: abs(x['score'] - 50))
            print(f"\n{Fore.CYAN}🏆 MEJOR OPORTUNIDAD:")
            print(f"   {best['symbol']}: {best['action']} (Score: {best['score']:.1f})")
    
    def save_results(self, results: List[Dict]):
        """Guarda los resultados en un archivo JSON"""
        try:
            filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Resultados guardados en {filename}")
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
    
    def run_single_analysis(self):
        """Ejecuta un análisis único de todos los símbolos"""
        all_results = []
        
        for symbol in self.symbols.keys():
            try:
                result = self.analyze_symbol(symbol)
                all_results.append(result)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error analizando {symbol}: {e}")
                continue
        
        # Resumen
        self.print_summary(all_results)
        
        # Guardar
        self.save_results(all_results)
        
        return all_results


def main():
    """Función principal"""
    # Limpiar pantalla
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Crear generador de señales
    generator = ProfessionalSignalGenerator()
    
    # Menú de opciones
    print(f"\n{Fore.CYAN}📋 OPCIONES DE ANÁLISIS:")
    print(f"{Fore.WHITE}1. Análisis único de todos los símbolos")
    print(f"{Fore.WHITE}2. Análisis continuo (cada 5 minutos)")
    print(f"{Fore.WHITE}3. Análisis continuo (cada 1 minuto)")
    print(f"{Fore.WHITE}4. Análisis de símbolo específico")
    
    try:
        option = input(f"\n{Fore.YELLOW}Selecciona opción (1-4): {Fore.WHITE}")
        
        if option == '1':
            generator.run_single_analysis()
        
        elif option == '2':
            generator.run_continuous_analysis(300)  # 5 minutos
        
        elif option == '3':
            generator.run_continuous_analysis(60)   # 1 minuto
        
        elif option == '4':
            print(f"\n{Fore.CYAN}Símbolos disponibles:")
            for symbol in generator.symbols.keys():
                print(f"  • {symbol}")
            symbol = input(f"\n{Fore.YELLOW}Ingresa símbolo: {Fore.WHITE}").upper()
            if symbol in generator.symbols:
                generator.analyze_symbol(symbol)
            else:
                print(f"{Fore.RED}Símbolo no válido")
        
        else:
            print(f"{Fore.RED}Opción no válida")
    
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Programa terminado por el usuario")
    except Exception as e:
        logger.error(f"Error en programa principal: {e}")
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}Fin del análisis - AlgoTrader v4.0")
    print(f"{Fore.CYAN}{'='*80}\n")


if __name__ == "__main__":
    main()
