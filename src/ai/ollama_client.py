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
        self.model = model
        
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
Actúa como un analista técnico profesional con enfoque institucional. SOLO responde en español.
Usando datos en tiempo real, realiza un análisis completo y riguroso sobre el activo {symbol}.

Tu objetivo es:
1. Consultar los indicadores técnicos clave en cada timeframe disponible
2. Detectar si existe una señal fuerte de compra, venta, o si no es recomendable operar
3. Basar la conclusión SOLO en los datos frescos proporcionados

Formato de respuesta OBLIGATORIO:

📊 **Análisis Técnico**
✅ **Señal final: COMPRA** o **Señal final: VENTA** o **Señal final: NO OPERAR**
🧠 **Razonamiento técnico claro y breve**
📈 **Setup operativo sugerido**:
- Entrada: {precio_actual:.5f} (precio actual de referencia)
- SL: [precio numérico stop loss]
- TP: [precio numérico take profit]  
- Ratio TP/SL: [ratio numérico, ej: 2.0]

DATOS ACTUALES:
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
                    temperature=0.2,
                    max_tokens=1500
                )
                respuesta_texto = respuesta.choices[0].message.content
            else:
                respuesta = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1500
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
                    temperature=0.1,
                    max_tokens=10
                )
                texto = respuesta.choices[0].message.content.strip()
            else:
                respuesta = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Responde solo: OK"}],
                    temperature=0.1,
                    max_tokens=10
                )
                texto = respuesta['choices'][0]['message']['content'].strip()
            
            success = "OK" in texto.upper()
            
            logger.info(f"Test Ollama: {'[OK] Exitoso' if success else '[ERROR] Falló'}")
            return success
            
        except Exception as e:
            logger.error(f"Error testing Ollama: {e}")
            return False

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