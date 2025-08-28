"""
MT5 Advanced Scraper - Web scraping avanzado de documentación MT5
==============================================================

Sistema que extrae información completa de la documentación oficial de MT5
y implementa funciones avanzadas para análisis de ticks y trading
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from pathlib import Path
import re

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class MT5AdvancedScraper:
    def __init__(self):
        self.base_url = "https://www.mql5.com/en/docs/python_metatrader5"
        self.scraped_data = {}
        self.mt5_functions = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        print("MT5 Advanced Scraper inicializado")
    
    def scrape_mt5_documentation(self):
        """Extraer documentación completa de MT5"""
        try:
            print("[SCRAPING] Extrayendo documentación MT5...")
            
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer funciones principales
                functions = self.extract_functions_from_page(soup)
                self.mt5_functions.update(functions)
                
                # Buscar enlaces a páginas de funciones específicas
                function_links = self.find_function_links(soup)
                
                # Scrape páginas individuales de funciones
                for func_name, link in function_links.items():
                    time.sleep(1)  # Rate limiting
                    self.scrape_function_details(func_name, link)
                
                print(f"[SUCCESS] {len(self.mt5_functions)} funciones extraídas")
                return True
                
            else:
                print(f"[ERROR] Error accediendo documentación: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error scraping: {e}")
            return False
    
    def extract_functions_from_page(self, soup):
        """Extraer funciones de la página principal"""
        functions = {}
        
        # Buscar secciones de funciones
        function_sections = soup.find_all(['h2', 'h3', 'h4'])
        
        for section in function_sections:
            # Buscar nombres de funciones
            func_matches = re.findall(r'(\w+\(\))', section.get_text())
            
            for match in func_matches:
                func_name = match.replace('()', '')
                
                # Obtener descripción desde el párrafo siguiente
                next_p = section.find_next('p')
                description = next_p.get_text() if next_p else "Sin descripción"
                
                functions[func_name] = {
                    'description': description,
                    'category': section.get_text().split('-')[0].strip() if '-' in section.get_text() else 'General',
                    'syntax': match,
                    'scraped_from': 'main_page'
                }
        
        return functions
    
    def find_function_links(self, soup):
        """Encontrar enlaces a páginas de funciones específicas"""
        links = {}
        
        # Buscar todos los enlaces dentro de la documentación
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Enlaces que parecen ser de funciones MT5
            if '/python_metatrader5/' in href and href != self.base_url:
                func_name = href.split('/')[-1] if '/' in href else href
                links[func_name] = href if href.startswith('http') else f"https://www.mql5.com{href}"
        
        return links
    
    def scrape_function_details(self, func_name, url):
        """Extraer detalles específicos de una función"""
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer sintaxis
                syntax = self.extract_syntax(soup)
                
                # Extraer parámetros
                parameters = self.extract_parameters(soup)
                
                # Extraer ejemplos
                examples = self.extract_examples(soup)
                
                # Extraer valores de retorno
                returns = self.extract_return_values(soup)
                
                if func_name not in self.mt5_functions:
                    self.mt5_functions[func_name] = {}
                
                self.mt5_functions[func_name].update({
                    'syntax': syntax,
                    'parameters': parameters,
                    'examples': examples,
                    'returns': returns,
                    'url': url,
                    'detailed_scrape': True
                })
                
        except Exception as e:
            print(f"[WARNING] Error scraping {func_name}: {e}")
    
    def extract_syntax(self, soup):
        """Extraer sintaxis de la función"""
        syntax_elements = soup.find_all(['code', 'pre'], class_=re.compile(r'syntax|code'))
        
        syntax_list = []
        for element in syntax_elements:
            text = element.get_text().strip()
            if '(' in text and ')' in text:  # Parece una sintaxis de función
                syntax_list.append(text)
        
        return syntax_list
    
    def extract_parameters(self, soup):
        """Extraer parámetros de la función"""
        parameters = []
        
        # Buscar tablas de parámetros
        param_tables = soup.find_all('table')
        
        for table in param_tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Saltar header
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    param_name = cells[0].get_text().strip()
                    param_desc = cells[1].get_text().strip()
                    
                    if param_name and not param_name.lower() in ['parameter', 'name']:
                        parameters.append({
                            'name': param_name,
                            'description': param_desc,
                            'type': cells[2].get_text().strip() if len(cells) > 2 else 'Unknown'
                        })
        
        return parameters
    
    def extract_examples(self, soup):
        """Extraer ejemplos de código"""
        examples = []
        
        # Buscar bloques de código de ejemplo
        code_blocks = soup.find_all(['pre', 'code'], class_=re.compile(r'example|code'))
        
        for block in code_blocks:
            code_text = block.get_text().strip()
            
            # Filtrar solo ejemplos que parecen código Python
            if 'import' in code_text or 'mt5.' in code_text or 'def ' in code_text:
                examples.append(code_text)
        
        return examples
    
    def extract_return_values(self, soup):
        """Extraer información sobre valores de retorno"""
        returns = []
        
        # Buscar secciones que hablen de valores de retorno
        return_sections = soup.find_all(text=re.compile(r'return|Return'))
        
        for section in return_sections:
            parent = section.parent
            if parent:
                return_text = parent.get_text().strip()
                if len(return_text) > 10:  # Filtrar textos muy cortos
                    returns.append(return_text)
        
        return returns
    
    def implement_advanced_tick_functions(self):
        """Implementar funciones avanzadas basadas en documentación scrapeada"""
        if not MT5_AVAILABLE:
            print("[WARNING] MT5 no disponible, generando funciones de ejemplo")
            return self.generate_example_functions()
        
        advanced_functions = {
            'get_advanced_tick_data': self.get_advanced_tick_data,
            'analyze_market_depth': self.analyze_market_depth,
            'get_symbol_statistics': self.get_symbol_statistics,
            'calculate_spread_statistics': self.calculate_spread_statistics,
            'monitor_price_changes': self.monitor_price_changes
        }
        
        return advanced_functions
    
    def get_advanced_tick_data(self, symbol, count=1000):
        """Obtener datos tick avanzados con análisis"""
        try:
            if not mt5.initialize():
                return None
            
            # Obtener ticks usando funciones scrapeadas
            ticks = mt5.copy_ticks_from_pos(symbol, 0, count)
            
            if ticks is None or len(ticks) == 0:
                return None
            
            # Análisis avanzado de los ticks
            analysis = {
                'symbol': symbol,
                'total_ticks': len(ticks),
                'time_range': {
                    'start': datetime.fromtimestamp(ticks[0]['time']),
                    'end': datetime.fromtimestamp(ticks[-1]['time'])
                },
                'price_analysis': {
                    'bid_range': [min(tick['bid'] for tick in ticks), max(tick['bid'] for tick in ticks)],
                    'ask_range': [min(tick['ask'] for tick in ticks), max(tick['ask'] for tick in ticks)],
                    'spread_stats': {
                        'min': min(tick['ask'] - tick['bid'] for tick in ticks),
                        'max': max(tick['ask'] - tick['bid'] for tick in ticks),
                        'avg': sum(tick['ask'] - tick['bid'] for tick in ticks) / len(ticks)
                    }
                },
                'volume_analysis': {
                    'total_volume': sum(tick.get('volume', 0) for tick in ticks),
                    'avg_volume': sum(tick.get('volume', 0) for tick in ticks) / len(ticks) if ticks else 0
                },
                'tick_movements': self.analyze_tick_movements(ticks),
                'raw_ticks': ticks
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error en get_advanced_tick_data: {e}")
            return None
    
    def analyze_tick_movements(self, ticks):
        """Analizar movimientos entre ticks"""
        movements = {
            'up_moves': 0,
            'down_moves': 0,
            'no_change': 0,
            'movement_sizes': []
        }
        
        for i in range(1, len(ticks)):
            prev_price = (ticks[i-1]['bid'] + ticks[i-1]['ask']) / 2
            curr_price = (ticks[i]['bid'] + ticks[i]['ask']) / 2
            
            diff = curr_price - prev_price
            
            if diff > 0:
                movements['up_moves'] += 1
            elif diff < 0:
                movements['down_moves'] += 1
            else:
                movements['no_change'] += 1
            
            movements['movement_sizes'].append(abs(diff))
        
        movements['avg_movement'] = sum(movements['movement_sizes']) / len(movements['movement_sizes']) if movements['movement_sizes'] else 0
        movements['momentum'] = movements['up_moves'] - movements['down_moves']
        
        return movements
    
    def analyze_market_depth(self, symbol):
        """Analizar profundidad de mercado usando funciones scrapeadas"""
        try:
            if not mt5.initialize():
                return None
            
            # Suscribirse a market book
            if mt5.market_book_add(symbol):
                # Obtener datos de profundidad
                book = mt5.market_book_get(symbol)
                
                if book is not None:
                    analysis = {
                        'symbol': symbol,
                        'timestamp': datetime.now(),
                        'buy_orders': [order for order in book if order.type == mt5.BOOK_TYPE_BUY],
                        'sell_orders': [order for order in book if order.type == mt5.BOOK_TYPE_SELL],
                        'spread': None,
                        'liquidity': {
                            'buy_volume': sum(order.volume for order in book if order.type == mt5.BOOK_TYPE_BUY),
                            'sell_volume': sum(order.volume for order in book if order.type == mt5.BOOK_TYPE_SELL)
                        }
                    }
                    
                    # Calcular spread del book
                    if analysis['buy_orders'] and analysis['sell_orders']:
                        best_bid = max(order.price for order in analysis['buy_orders'])
                        best_ask = min(order.price for order in analysis['sell_orders'])
                        analysis['spread'] = best_ask - best_bid
                    
                    # Limpiar suscripción
                    mt5.market_book_release(symbol)
                    
                    return analysis
                
                mt5.market_book_release(symbol)
            
            return None
            
        except Exception as e:
            print(f"Error en analyze_market_depth: {e}")
            return None
    
    def get_symbol_statistics(self, symbol):
        """Obtener estadísticas completas del símbolo"""
        try:
            if not mt5.initialize():
                return None
            
            # Información básica del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
            
            # Último tick
            tick = mt5.symbol_info_tick(symbol)
            
            # Estadísticas del día
            stats = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'symbol_info': {
                    'point': symbol_info.point,
                    'digits': symbol_info.digits,
                    'spread': symbol_info.spread,
                    'trade_mode': symbol_info.trade_mode,
                    'min_volume': symbol_info.volume_min,
                    'max_volume': symbol_info.volume_max,
                    'contract_size': symbol_info.trade_contract_size
                },
                'current_tick': {
                    'bid': tick.bid if tick else None,
                    'ask': tick.ask if tick else None,
                    'spread': tick.ask - tick.bid if tick else None,
                    'volume': tick.volume if tick else None,
                    'time': datetime.fromtimestamp(tick.time) if tick else None
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"Error en get_symbol_statistics: {e}")
            return None
    
    def save_scraped_data(self):
        """Guardar datos scrapeados en JSON"""
        try:
            output_data = {
                'scraped_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_functions': len(self.mt5_functions),
                'functions': self.mt5_functions,
                'scraping_stats': {
                    'base_url': self.base_url,
                    'functions_with_examples': len([f for f in self.mt5_functions.values() if f.get('examples')]),
                    'functions_with_parameters': len([f for f in self.mt5_functions.values() if f.get('parameters')])
                }
            }
            
            filename = Path("mt5_scraped_documentation.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[SAVED] Datos guardados en: {filename}")
            return str(filename)
            
        except Exception as e:
            print(f"[ERROR] Error guardando: {e}")
            return None
    
    def generate_function_reference(self):
        """Generar guía de referencia de funciones MT5"""
        try:
            reference = []
            reference.append("# REFERENCIA DE FUNCIONES MT5 - Scrapeado de MQL5.com")
            reference.append("=" * 60)
            reference.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            reference.append(f"Total funciones: {len(self.mt5_functions)}")
            reference.append("")
            
            # Agrupar por categorías
            categories = {}
            for func_name, func_data in self.mt5_functions.items():
                category = func_data.get('category', 'Sin categoría')
                if category not in categories:
                    categories[category] = []
                categories[category].append((func_name, func_data))
            
            # Generar documentación por categoría
            for category, functions in categories.items():
                reference.append(f"## {category}")
                reference.append("-" * 40)
                
                for func_name, func_data in functions:
                    reference.append(f"\n### {func_name}")
                    reference.append(f"**Descripción:** {func_data.get('description', 'Sin descripción')}")
                    
                    if func_data.get('syntax'):
                        reference.append("**Sintaxis:**")
                        for syntax in func_data['syntax']:
                            reference.append(f"```python\n{syntax}\n```")
                    
                    if func_data.get('parameters'):
                        reference.append("**Parámetros:**")
                        for param in func_data['parameters']:
                            reference.append(f"- `{param['name']}`: {param['description']}")
                    
                    if func_data.get('examples'):
                        reference.append("**Ejemplos:**")
                        for example in func_data['examples']:
                            reference.append(f"```python\n{example}\n```")
                    
                    reference.append("")
            
            # Guardar referencia
            filename = Path("MT5_Function_Reference.md")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(reference))
            
            print(f"[SAVED] Referencia guardada en: {filename}")
            return str(filename)
            
        except Exception as e:
            print(f"[ERROR] Error generando referencia: {e}")
            return None

def main():
    try:
        scraper = MT5AdvancedScraper()
        
        print("MT5 ADVANCED SCRAPER")
        print("=" * 50)
        print("Extrayendo documentación completa de MQL5.com...")
        print("Este proceso puede tomar varios minutos")
        print("=" * 50)
        
        # Scrape documentación
        if scraper.scrape_mt5_documentation():
            print(f"\n[SUCCESS] Documentación extraída exitosamente")
            
            # Guardar datos
            json_file = scraper.save_scraped_data()
            reference_file = scraper.generate_function_reference()
            
            # Implementar funciones avanzadas
            advanced_funcs = scraper.implement_advanced_tick_functions()
            
            print(f"\n[SUMMARY] Archivos generados:")
            if json_file:
                print(f"  - {json_file}")
            if reference_file:
                print(f"  - {reference_file}")
            
            print(f"\n[FUNCTIONS] {len(advanced_funcs)} funciones avanzadas implementadas")
            
            # Ejemplo de uso de función avanzada
            if MT5_AVAILABLE:
                print(f"\n[EXAMPLE] Probando función avanzada...")
                example_data = scraper.get_advanced_tick_data('EURUSD', 100)
                if example_data:
                    print(f"  Símbolo: {example_data['symbol']}")
                    print(f"  Total ticks: {example_data['total_ticks']}")
                    print(f"  Spread promedio: {example_data['price_analysis']['spread_stats']['avg']:.5f}")
                    print(f"  Momentum: {example_data['tick_movements']['momentum']}")
            
        else:
            print("[ERROR] Error extrayendo documentación")
        
    except Exception as e:
        print(f"[FATAL] Error: {e}")

if __name__ == "__main__":
    main()