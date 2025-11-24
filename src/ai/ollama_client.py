#!/usr/bin/env python
"""
Cliente de Ollama para análisis de trading con IA
Integración del sistema avanzado con deepseek-r1:14b
"""

try:
    from openai import OpenAI
    OPENAI_VERSION = "new"
except ImportError:
    import openai
    OPENAI_VERSION = "old"

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class OllamaClient:
    """Cliente para análisis de trading con Ollama"""
    
    def __init__(self, 
                 api_base: str = "http://localhost:11434/v1",
                 model: str = "deepseek-r1:14b"):
        """
        Inicializa el cliente Ollama
        Args:
            api_base: URL base de la API de Ollama
            model: Modelo a usar (deepseek-r1:14b)
        """
        self.api_base = api_base
        self.model = "deepseek-r1:8b"  # Usar modelo más rápido
        
        # Configurar cliente OpenAI para Ollama
        if OPENAI_VERSION == "new":
            self.client = OpenAI(
                api_key="none",
                base_url=api_base
            )
        else:
            openai.api_key = "none"
            openai.api_base = api_base
            self.client = None
        
        logger.info(f"Ollama client iniciado: {api_base} - Modelo: {model}")
    
    def generar_prompt_trading(self, 
                              symbol: str,
                              indicadores_multi: Dict[str, Dict],
                              cierres_multi: Dict[str, List],
                              precio_actual: float) -> str:
        """
        Genera prompt especializado para análisis de trading
        Args:
            symbol: Símbolo a analizar
            indicadores_multi: Indicadores por timeframe
            cierres_multi: Precios de cierre históricos
            precio_actual: Precio actual del activo
        Returns:
            Prompt completo para IA
        """
        
        PROMPT = f"""
Eres un trader profesional especializado en {symbol}. Analiza los datos técnicos y genera señales de trading.

IMPORTANTE: Busca activamente oportunidades de trading. Si hay tendencias claras, divergencias, 
soporte/resistencia, o patrones técnicos, GENERA LA SEÑAL.

Criterios para COMPRA:
- RSI < 30 (sobreventa) o rebote desde soporte
- MACD cruzando hacia arriba
- Precio tocando banda inferior de Bollinger
- Ruptura de resistencia
- Patrón alcista (doble suelo, bandera, etc)

Criterios para VENTA:
- RSI > 70 (sobrecompra) o rechazo desde resistencia  
- MACD cruzando hacia abajo
- Precio tocando banda superior de Bollinger
- Ruptura de soporte
- Patrón bajista (doble techo, bandera bajista, etc)

Respuesta OBLIGATORIA en formato:

SEÑAL FINAL: COMPRA/VENTA/NO_OPERAR
Entrada: [precio numérico]
SL: [precio numérico] 
TP: [precio numérico]
Confianza: [porcentaje]%

Precio actual: {precio_actual:.5f}

ESTRATEGIAS ESPECÍFICAS POR ASSET:

XAU/USD (ORO):
- Compra en retrocesos del 23.6% o 38.2% de Fibonacci después de tendencia alcista
- Venta en rechazo de niveles psicológicos (3600, 3650, 3700, etc)
- Breakouts de rangos consolidados con volumen
- Divergencias en RSI son señales muy confiables en oro
- Niveles de soporte/resistencia son críticos (oro respeta zonas técnicas)

BTC/USD:
- Compra cuando toca EMA 50 en tendencia alcista
- Venta en resistencias de máximos históricos
- Patrones de triple toque en soporte/resistencia

NOTA: Sé agresivo en buscar oportunidades. Es mejor entrar con 60-70% confianza que perder oportunidades reales.
"""
        
        # Agregar indicadores por timeframe
        for tf, indicadores in indicadores_multi.items():
            if not indicadores:
                continue
                
            PROMPT += f"\n--- TIMEFRAME {tf} ---\n"
            
            # Formatear indicadores de manera clara
            for indicador, valor in indicadores.items():
                if isinstance(valor, dict):
                    for sub_key, sub_val in valor.items():
                        PROMPT += f"{indicador}_{sub_key}: {sub_val}\n"
                else:
                    PROMPT += f"{indicador}: {valor}\n"
            
            # Agregar cierres históricos
            if tf in cierres_multi and cierres_multi[tf]:
                cierres_str = ", ".join([str(c) for c in cierres_multi[tf][:10]])
                PROMPT += f"Últimos 10 cierres: {cierres_str}\n"
        
        PROMPT += "\nRecuerda: Solo envía el análisis en el formato solicitado y en español. Sé preciso con los números."
        
        return PROMPT
    
    def analizar_mercado(self, 
                        symbol: str,
                        indicadores_multi: Dict[str, Dict],
                        cierres_multi: Dict[str, List],
                        precio_actual: float) -> Dict[str, Any]:
        """
        Analiza el mercado usando IA de Ollama
        Args:
            symbol: Símbolo a analizar
            indicadores_multi: Indicadores por timeframe  
            cierres_multi: Cierres históricos
            precio_actual: Precio actual
        Returns:
            Diccionario con análisis de IA
        """
        try:
            # Generar prompt
            prompt = self.generar_prompt_trading(
                symbol, indicadores_multi, cierres_multi, precio_actual
            )
            
            logger.info(f"Enviando análisis a Ollama para {symbol}")
            
            # Llamar a Ollama
            if OPENAI_VERSION == "new":
                respuesta = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=200
                )
                respuesta_texto = respuesta.choices[0].message.content
            else:
                respuesta = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=200
                )
                respuesta_texto = respuesta['choices'][0]['message']['content']
            
            # Parsear respuesta
            analisis = self.parsear_respuesta_ia(respuesta_texto, precio_actual)
            analisis['respuesta_completa'] = respuesta_texto
            analisis['symbol'] = symbol
            analisis['timestamp'] = datetime.now()
            
            logger.info(f"Análisis IA completado para {symbol}: {analisis.get('senal', 'NO_SIGNAL')}")
            
            return analisis
            
        except Exception as e:
            logger.error(f"Error en análisis Ollama: {e}")
            return {
                'error': str(e),
                'senal': 'NO_OPERAR',
                'confianza': 0.0,
                'symbol': symbol,
                'timestamp': datetime.now()
            }
    
    def parsear_respuesta_ia(self, respuesta: str, precio_actual: float) -> Dict[str, Any]:
        """
        Parsea la respuesta de IA para extraer señales
        Args:
            respuesta: Texto de respuesta de IA
            precio_actual: Precio actual para referencia
        Returns:
            Diccionario parseado con señales
        """
        import re
        
        resultado = {
            'senal': 'NO_OPERAR',
            'confianza': 0.5,
            'entrada': precio_actual,
            'sl': None,
            'tp': None,
            'ratio': None,
            'razonamiento': ''
        }
        
        try:
            # Detectar señal principal
            if re.search(r"Señal final:\s*COMPRA", respuesta, re.IGNORECASE):
                resultado['senal'] = 'BUY'
                resultado['confianza'] = 0.8
            elif re.search(r"Señal final:\s*VENTA", respuesta, re.IGNORECASE):
                resultado['senal'] = 'SELL'
                resultado['confianza'] = 0.8
            
            # Extraer niveles numéricos
            entrada_match = re.search(r"Entrada[:=\s]+([0-9]+\.?[0-9]*)", respuesta)
            if entrada_match:
                resultado['entrada'] = float(entrada_match.group(1))
            
            sl_match = re.search(r"SL[:=\s]+([0-9]+\.?[0-9]*)", respuesta)
            if sl_match:
                resultado['sl'] = float(sl_match.group(1))
            
            tp_match = re.search(r"TP[:=\s]+([0-9]+\.?[0-9]*)", respuesta)
            if tp_match:
                resultado['tp'] = float(tp_match.group(1))
            
            ratio_match = re.search(r"Ratio[^:]*[:=\s]+([0-9]+\.?[0-9]*)", respuesta)
            if ratio_match:
                resultado['ratio'] = float(ratio_match.group(1))
            
            # Extraer razonamiento
            razon_match = re.search(
                r"Razonamiento técnico[^:]*:\s*(.*?)(?=📈|$)", 
                respuesta, 
                re.DOTALL | re.IGNORECASE
            )
            if razon_match:
                resultado['razonamiento'] = razon_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"Error parseando respuesta IA: {e}")
        
        return resultado
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con Ollama
        Returns:
            True si la conexión es exitosa
        """
        try:
            if OPENAI_VERSION == "new":
                respuesta = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Responde solo: OK"}],
                    temperature=0.3,
                    max_tokens=10
                )
                texto = respuesta.choices[0].message.content.strip()
            else:
                respuesta = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Responde solo: OK"}],
                    temperature=0.3,
                    max_tokens=10
                )
                texto = respuesta['choices'][0]['message']['content'].strip()
            
            success = len(texto.strip()) > 0  # Cualquier respuesta válida es exitosa
            
            logger.info(f"Test Ollama: {'[OK] Exitoso' if success else '[ERROR] Falló'}")
            return success
            
        except Exception as e:
            logger.error(f"Error testing Ollama: {e}")
            return False
    
    def analyze_with_simple_prompt(self, prompt: str) -> str:
        """
        Analiza con un prompt simple y retorna la respuesta
        Args:
            prompt: Prompt para el análisis
        Returns:
            Respuesta de la IA como string
        """
        try:
            if OPENAI_VERSION == "new":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Eres un experto en trading algorítmico"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            else:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Eres un experto en trading algorítmico"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error en análisis simple: {e}")
            return ""

# Función de utilidad para usar desde otros módulos
def crear_cliente_ollama() -> Optional[OllamaClient]:
    """
    Crea y testea un cliente Ollama
    Returns:
        Cliente Ollama si está disponible, None si no
    """
    try:
        client = OllamaClient()
        if client.test_connection():
            return client
        else:
            logger.warning("Ollama no está disponible")
            return None
    except Exception as e:
        logger.error(f"Error creando cliente Ollama: {e}")
        return None