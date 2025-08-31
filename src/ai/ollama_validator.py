#!/usr/bin/env python3
"""
OLLAMA AI VALIDATOR - Validación de señales de trading con IA
Utiliza DeepSeek-R1 para análisis inteligente de señales
"""
import requests
import json
import os
import logging
from typing import Dict, Optional, Any

# Configurar logging
logger = logging.getLogger(__name__)

class OllamaValidator:
    def __init__(self):
        self.host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'deepseek-r1:14b')
        
    def validate_signal(self, snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validar señal de trading usando IA Ollama
        
        Args:
            snapshot: Datos del mercado y análisis técnico
            
        Returns:
            Dict con signal, confidence, reason o None si error
        """
        try:
            # Preparar prompt para IA
            prompt = self._create_analysis_prompt(snapshot)
            
            # Enviar a Ollama
            response = self._call_ollama(prompt)
            
            if response:
                # Parsear respuesta de IA
                return self._parse_ai_response(response)
            else:
                logger.error("No hay respuesta de Ollama")
                return None
                
        except Exception as e:
            logger.error(f"Error en validación IA: {e}")
            return None
    
    def _create_analysis_prompt(self, snapshot: Dict[str, Any]) -> str:
        """Crear prompt estructurado para análisis de IA"""
        
        symbol = snapshot.get('symbol', 'UNKNOWN')
        price = snapshot.get('price', 0)
        rsi = snapshot.get('rsi', 50)
        macd = snapshot.get('macd', 0)
        trend = snapshot.get('trend', 'neutral')
        analysis = snapshot.get('analysis', 'Sin análisis')
        
        prompt = f"""Eres un experto analista de trading con 20 años de experiencia. Analiza esta situación del mercado y dame tu opinión profesional:

DATOS DEL MERCADO:
- Símbolo: {symbol}
- Precio actual: {price}
- RSI: {rsi}
- MACD: {macd}
- Tendencia: {trend}
- Análisis técnico: {analysis}

Por favor analiza estos datos y dame:
1. Tu recomendación: BUY, SELL, o HOLD
2. Tu nivel de confianza (0-100%)  
3. Tu razonamiento principal (máximo 2 líneas)

IMPORTANTE: 
- Solo recomienda BUY/SELL si hay una señal FUERTE (confianza >70%)
- Para señales débiles, recomienda HOLD
- Sé conservador con el riesgo
- Considera que esto es dinero real

Responde EXACTAMENTE en este formato JSON:
{{"signal": "BUY/SELL/HOLD", "confidence": 85, "reason": "Tu explicación aquí"}}"""

        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Llamar a la API de Ollama"""
        try:
            url = f"{self.host}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Más conservador
                    "top_p": 0.9,
                    "num_predict": 200   # Respuesta concisa
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Error Ollama API: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.error("No se pudo conectar a Ollama. ¿Está corriendo 'ollama serve'?")
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout en llamada a Ollama")
            return None
        except Exception as e:
            logger.error(f"Error llamando Ollama: {e}")
            return None
    
    def _parse_ai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parsear respuesta JSON de la IA"""
        try:
            # Buscar JSON en la respuesta
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validar estructura
                if 'signal' in result and 'confidence' in result and 'reason' in result:
                    # Normalizar signal
                    signal = result['signal'].upper()
                    if signal not in ['BUY', 'SELL', 'HOLD']:
                        signal = 'HOLD'
                    
                    # Normalizar confidence
                    confidence = float(result['confidence'])
                    confidence = max(0, min(100, confidence)) / 100  # 0-1 range
                    
                    return {
                        'signal': signal,
                        'confidence': confidence,
                        'reason': str(result['reason'])[:200]  # Limitar longitud
                    }
                else:
                    logger.warning("Respuesta IA no tiene estructura correcta")
                    return None
            else:
                logger.warning("No se encontró JSON válido en respuesta IA")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de IA: {e}")
            # Intentar parseo básico por palabras clave
            return self._parse_fallback(response)
        except Exception as e:
            logger.error(f"Error procesando respuesta IA: {e}")
            return None
    
    def _parse_fallback(self, response: str) -> Optional[Dict[str, Any]]:
        """Parseo básico si falla el JSON"""
        try:
            response_upper = response.upper()
            
            # Detectar señal
            if 'BUY' in response_upper and 'SELL' not in response_upper:
                signal = 'BUY'
            elif 'SELL' in response_upper and 'BUY' not in response_upper:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            # Confianza conservadora por defecto
            confidence = 0.5
            
            # Buscar números que puedan ser confianza
            import re
            numbers = re.findall(r'\b(\d{1,2}|\d{1,3})\b', response)
            for num in numbers:
                n = int(num)
                if 50 <= n <= 100:  # Rango razonable para confianza
                    confidence = n / 100
                    break
            
            return {
                'signal': signal,
                'confidence': confidence,
                'reason': response[:100] + "..." if len(response) > 100 else response
            }
            
        except Exception as e:
            logger.error(f"Error en parseo fallback: {e}")
            return None

# Instancia global del validador
_validator = OllamaValidator()

def validate_signal(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Función pública para validar señales
    
    Args:
        snapshot: Diccionario con datos del mercado
        
    Returns:
        Dict con signal, confidence, reason o None si error
        
    Example:
        result = validate_signal({
            'symbol': 'XAUUSD',
            'price': 2650.50,
            'rsi': 35.2,
            'macd': 0.15,
            'trend': 'alcista'
        })
    """
    return _validator.validate_signal(snapshot)

def test_ollama_connection() -> bool:
    """Probar conexión con Ollama"""
    try:
        host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        response = requests.get(f"{host}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # Test básico
    print("Probando validador Ollama...")
    
    if not test_ollama_connection():
        print("❌ Ollama no está conectado")
        exit(1)
    
    # Datos de prueba
    test_data = {
        'symbol': 'XAUUSD',
        'price': 2650.50,
        'rsi': 35.2,
        'macd': 0.15,
        'trend': 'alcista',
        'analysis': 'RSI en sobreventa recuperándose, MACD positivo, precio sobre medias móviles'
    }
    
    print("Enviando datos de prueba...")
    result = validate_signal(test_data)
    
    if result:
        print(f"✅ IA respondió:")
        print(f"   Señal: {result['signal']}")
        print(f"   Confianza: {result['confidence']:.1%}")
        print(f"   Razón: {result['reason']}")
    else:
        print("❌ No hay respuesta de IA")