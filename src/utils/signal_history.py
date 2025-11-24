#!/usr/bin/env python
"""
Utilidad para guardar historial de señales en CSV
"""

import os
import csv
import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SignalHistoryManager:
    """Gestor de historial de señales"""
    
    def __init__(self, csv_path: str = "data/historial_senales.csv"):
        """
        Inicializa el gestor de historial
        Args:
            csv_path: Ruta del archivo CSV
        """
        self.csv_path = csv_path
        self.ensure_csv_exists()
    
    def ensure_csv_exists(self):
        """Crear archivo CSV si no existe"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            
            # Crear archivo CSV con headers si no existe
            if not os.path.isfile(self.csv_path):
                with open(self.csv_path, "w", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", 
                        "symbol", 
                        "signal_type", 
                        "confidence", 
                        "entry_price", 
                        "stop_loss", 
                        "take_profit", 
                        "ratio", 
                        "reasoning", 
                        "strategy",
                        "timeframes",
                        "full_response"
                    ])
                logger.info(f"Archivo CSV creado: {self.csv_path}")
        except Exception as e:
            logger.error(f"Error creando CSV: {e}")
    
    def extract_signal_data(self, ia_response: str, symbol: str, strategy: str = "AI_Hybrid") -> Dict[str, Any]:
        """
        Extrae datos estructurados de la respuesta de IA
        Args:
            ia_response: Respuesta de la IA
            symbol: Símbolo analizado
            strategy: Estrategia utilizada
        Returns:
            Diccionario con datos extraídos
        """
        try:
            # Extraer señal
            # Buscar tanto en español como en inglés
            signal_match = re.search(r"SEÑAL FINAL:\s*(COMPRA|VENTA|NO_OPERAR|BUY|SELL|HOLD)", ia_response, re.IGNORECASE)
            if signal_match:
                signal_raw = signal_match.group(1).upper()
                # Normalizar a inglés
                if signal_raw in ['COMPRA', 'BUY']:
                    signal_type = "BUY"
                elif signal_raw in ['VENTA', 'SELL']:
                    signal_type = "SELL"
                else:
                    signal_type = "NO_OPERAR"
            else:
                signal_type = "NO_OPERAR"
            
            # Extraer confianza
            confidence_match = re.search(r"Confianza:\s*([0-9]+)%", ia_response)
            confidence = confidence_match.group(1) if confidence_match else "0"
            
            # Extraer precios
            entry_match = re.search(r"Entrada:\s*([0-9]+\.?[0-9]*)", ia_response)
            entry_price = entry_match.group(1) if entry_match else ""
            
            sl_match = re.search(r"SL:\s*([0-9]+\.?[0-9]*)", ia_response)
            stop_loss = sl_match.group(1) if sl_match else ""
            
            tp_match = re.search(r"TP:\s*([0-9]+\.?[0-9]*)", ia_response)
            take_profit = tp_match.group(1) if tp_match else ""
            
            # Extraer ratio
            ratio_match = re.search(r"Ratio:\s*([0-9]+\.?[0-9]*)", ia_response)
            ratio = ratio_match.group(1) if ratio_match else ""
            
            # Extraer razonamiento
            reasoning_match = re.search(r"RAZONAMIENTO\*\*\s*(.*?)(?:\n\*\*|$)", ia_response, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
            
            return {
                'signal_type': signal_type,
                'confidence': confidence,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'ratio': ratio,
                'reasoning': reasoning,
                'symbol': symbol,
                'strategy': strategy
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo datos de señal: {e}")
            return {
                'signal_type': 'ERROR',
                'confidence': '0',
                'entry_price': '',
                'stop_loss': '',
                'take_profit': '',
                'ratio': '',
                'reasoning': f'Error: {str(e)}',
                'symbol': symbol,
                'strategy': strategy
            }
    
    def save_signal(self, 
                   ia_response: str, 
                   symbol: str, 
                   strategy: str = "AI_Hybrid",
                   timeframes: str = "5min,15min,1h") -> bool:
        """
        Guarda una señal en el CSV
        Args:
            ia_response: Respuesta completa de IA
            symbol: Símbolo analizado
            strategy: Estrategia utilizada
            timeframes: Timeframes analizados
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Extraer datos estructurados
            data = self.extract_signal_data(ia_response, symbol, strategy)
            
            # Crear timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Guardar en CSV
            with open(self.csv_path, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    data['symbol'],
                    data['signal_type'],
                    data['confidence'],
                    data['entry_price'],
                    data['stop_loss'],
                    data['take_profit'],
                    data['ratio'],
                    data['reasoning'],
                    data['strategy'],
                    timeframes,
                    ia_response.replace("\n", " ")  # Texto completo en una línea
                ])
            
            logger.info(f"Señal guardada: {symbol} - {data['signal_type']} ({data['confidence']}%)")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando señal: {e}")
            return False

# Instancia global
signal_history = SignalHistoryManager()