#!/usr/bin/env python
"""
BTCUSD INSTITUTIONAL VOLUME DETECTOR - DETECTOR DE VOLUMENES INSTITUCIONALES
============================================================================
Sistema especializado en detectar movimientos de volumen institucional en BTCUSD
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
import numpy as np
import json

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class BTCUSDInstitutionalVolumeDetector:
    """Detector de volumen institucional para BTCUSD"""
    
    def __init__(self):
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'
        self.base_url = 'https://api.twelvedata.com'
        self.symbol = 'BTC/USD'
        
        # Configuracion para deteccion de whales
        self.whale_config = {
            'large_volume_threshold': 1000000,  # $1M USD en volumen
            'price_impact_threshold': 0.5,      # 0.5% cambio de precio
            'time_window_minutes': 5,           # Ventana de 5 minutos
            'volume_spike_ratio': 3.0,          # 3x el volumen promedio
            'institutional_confidence': 70      # 70% confianza minima
        }
        
        # Historial de volumenes para analisis
        self.volume_history = []
        self.price_history = []
        self.whale_alerts = []
        
        print("BTCUSD Institutional Volume Detector inicializado")
        print("- Detección de ballenas (whales)")
        print("- Análisis de volumen institucional")
        print("- Alertas de movimientos sospechosos")
    
    def get_realtime_data(self, interval='1min', outputsize=50):
        """Obtener datos en tiempo real de BTCUSD"""
        try:
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': self.symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    return data['values']
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo datos en tiempo real: {e}")
            return None
    
    def calculate_volume_proxy(self, candle_data):
        """Calcular volumen proxy basado en rango y precio"""
        try:
            high = float(candle_data['high'])
            low = float(candle_data['low'])
            close = float(candle_data['close'])
            
            # Volumen estimado = (high-low) * close * factor_multiplicador
            volume_proxy = (high - low) * close * 10
            return volume_proxy
            
        except Exception as e:
            print(f"Error calculando volumen proxy: {e}")
            return 0
    
    def detect_volume_spikes(self, current_volume, volume_history):
        """Detectar picos de volumen anómalos"""
        try:
            if len(volume_history) < 10:
                return False, 0, "Historial insuficiente"
            
            # Calcular volumen promedio de los últimos 20 períodos
            recent_volumes = volume_history[-20:]
            avg_volume = np.mean(recent_volumes)
            std_volume = np.std(recent_volumes)
            
            # Calcular ratio de spike
            spike_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Detectar spike si está por encima del threshold
            is_spike = spike_ratio >= self.whale_config['volume_spike_ratio']
            
            # Calcular score de institucionalidad
            institutional_score = min(spike_ratio * 20, 100)
            
            reason = f"Volumen {spike_ratio:.1f}x mayor que promedio"
            
            return is_spike, institutional_score, reason
            
        except Exception as e:
            print(f"Error detectando spikes: {e}")
            return False, 0, "Error en análisis"
    
    def detect_price_impact(self, price_data):
        """Detectar impacto en precio que sugiere actividad institucional"""
        try:
            if len(price_data) < 5:
                return False, 0, "Datos insuficientes"
            
            # Analizar cambio de precio en últimos 5 períodos
            current_price = price_data[0]
            prices_5_ago = price_data[4] if len(price_data) > 4 else price_data[-1]
            
            price_change_pct = ((current_price - prices_5_ago) / prices_5_ago) * 100
            
            # Detectar impacto significativo
            has_impact = abs(price_change_pct) >= self.whale_config['price_impact_threshold']
            
            # Score basado en magnitud del cambio
            impact_score = min(abs(price_change_pct) * 40, 100)
            
            direction = "ALCISTA" if price_change_pct > 0 else "BAJISTA"
            reason = f"Cambio {direction} de {price_change_pct:+.2f}%"
            
            return has_impact, impact_score, reason
            
        except Exception as e:
            print(f"Error detectando impacto de precio: {e}")
            return False, 0, "Error en análisis"
    
    def analyze_whale_patterns(self, volume_data, price_data):
        """Analizar patrones que indican actividad de ballenas"""
        try:
            patterns = []
            whale_score = 0
            
            if not volume_data or not price_data or len(price_data) < 3:
                return patterns, 0
            
            # 1. Patrón: Volumen alto + precio estable = Acumulación
            current_volume = volume_data[0] if volume_data else 0
            recent_prices = [float(p) for p in price_data[:3]]
            
            price_stability = np.std(recent_prices) / np.mean(recent_prices)
            
            if current_volume > self.whale_config['large_volume_threshold'] and price_stability < 0.01:
                patterns.append("ACUMULACION_INSTITUCIONAL")
                whale_score += 30
            
            # 2. Patrón: Volumen extremo + movimiento direccional = Distribución
            if len(price_data) >= 5:
                price_trend = (float(price_data[0]) - float(price_data[4])) / float(price_data[4])
                
                if current_volume > self.whale_config['large_volume_threshold'] * 2 and abs(price_trend) > 0.02:
                    if price_trend > 0:
                        patterns.append("COMPRA_INSTITUCIONAL_AGRESIVA")
                    else:
                        patterns.append("VENTA_INSTITUCIONAL_AGRESIVA")
                    whale_score += 40
            
            # 3. Patrón: Múltiples spikes de volumen = Actividad sostenida
            volume_spikes = 0
            for i, vol in enumerate(volume_data[:5]):
                if i < len(self.volume_history) - 10:
                    avg_vol = np.mean(self.volume_history[-(10+i):-(i) if i > 0 else None])
                    if vol > avg_vol * 2:
                        volume_spikes += 1
            
            if volume_spikes >= 3:
                patterns.append("ACTIVIDAD_INSTITUCIONAL_SOSTENIDA")
                whale_score += 25
            
            return patterns, whale_score
            
        except Exception as e:
            print(f"Error analizando patrones de ballenas: {e}")
            return [], 0
    
    def generate_whale_alert(self, analysis_data):
        """Generar alerta de actividad institucional"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'symbol': 'BTCUSD',
            'alert_type': 'INSTITUTIONAL_ACTIVITY',
            'confidence': analysis_data.get('institutional_confidence', 0),
            'volume_score': analysis_data.get('volume_score', 0),
            'price_impact_score': analysis_data.get('price_impact_score', 0),
            'whale_patterns': analysis_data.get('whale_patterns', []),
            'current_price': analysis_data.get('current_price', 0),
            'volume_spike_ratio': analysis_data.get('volume_spike_ratio', 0),
            'recommendation': analysis_data.get('recommendation', 'MONITOR'),
            'details': analysis_data.get('details', '')
        }
        
        self.whale_alerts.append(alert)
        
        # Mantener solo las últimas 50 alertas
        if len(self.whale_alerts) > 50:
            self.whale_alerts.pop(0)
        
        return alert
    
    def run_institutional_analysis(self):
        """Ejecutar análisis completo de volumen institucional"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ANALIZANDO VOLUMEN INSTITUCIONAL BTCUSD...")
        print("=" * 60)
        
        # Obtener datos en tiempo real
        realtime_data = self.get_realtime_data('1min', 30)
        if not realtime_data:
            print("❌ No se pudieron obtener datos en tiempo real")
            return None
        
        # Procesar datos
        current_candle = realtime_data[0]
        current_price = float(current_candle['close'])
        current_volume = self.calculate_volume_proxy(current_candle)
        
        # Actualizar historiales
        self.volume_history.append(current_volume)
        self.price_history.append(current_price)
        
        # Mantener solo los últimos 100 registros
        if len(self.volume_history) > 100:
            self.volume_history.pop(0)
        if len(self.price_history) > 100:
            self.price_history.pop(0)
        
        # Análisis de spikes de volumen
        volume_spike, volume_score, volume_reason = self.detect_volume_spikes(
            current_volume, self.volume_history[:-1])
        
        # Análisis de impacto de precio
        price_impact, price_score, price_reason = self.detect_price_impact(self.price_history)
        
        # Análisis de patrones de ballenas
        volume_data_for_analysis = [current_volume] + self.volume_history[-10:]
        whale_patterns, whale_score = self.analyze_whale_patterns(
            volume_data_for_analysis, [str(p) for p in self.price_history[-10:]])
        
        # Calcular confianza institucional
        institutional_confidence = (volume_score * 0.4 + price_score * 0.3 + whale_score * 0.3)
        
        # Mostrar resultados
        print(f"💰 Precio actual: ${current_price:,.2f}")
        print(f"📊 Volumen estimado: ${current_volume:,.0f}")
        print(f"🐋 Score institucional: {institutional_confidence:.1f}%")
        
        print(f"\n📈 ANÁLISIS DE VOLUMEN:")
        print(f"   Spike detectado: {'SÍ' if volume_spike else 'NO'}")
        print(f"   Score volumen: {volume_score:.1f}/100")
        print(f"   Razón: {volume_reason}")
        
        print(f"\n💥 ANÁLISIS DE IMPACTO:")
        print(f"   Impacto significativo: {'SÍ' if price_impact else 'NO'}")
        print(f"   Score impacto: {price_score:.1f}/100")
        print(f"   Razón: {price_reason}")
        
        if whale_patterns:
            print(f"\n🐋 PATRONES DETECTADOS:")
            for pattern in whale_patterns:
                print(f"   - {pattern}")
        
        # Generar recomendación
        if institutional_confidence >= self.whale_config['institutional_confidence']:
            recommendation = "ALERTA_INSTITUCIONAL"
            details = "Actividad institucional detectada - MONITOREAR CERCANAMENTE"
        elif institutional_confidence >= 50:
            recommendation = "ACTIVIDAD_MODERADA"
            details = "Posible actividad institucional - Mantener vigilancia"
        elif volume_spike or price_impact:
            recommendation = "ACTIVIDAD_DETECTADA"
            details = "Actividad de mercado inusual detectada"
        else:
            recommendation = "ACTIVIDAD_NORMAL"
            details = "Sin señales institucionales significativas"
        
        # Preparar datos de análisis
        analysis_data = {
            'institutional_confidence': institutional_confidence,
            'volume_score': volume_score,
            'price_impact_score': price_score,
            'whale_patterns': whale_patterns,
            'current_price': current_price,
            'volume_spike_ratio': current_volume / np.mean(self.volume_history[-20:]) if len(self.volume_history) >= 20 else 1,
            'recommendation': recommendation,
            'details': details
        }
        
        # Generar alerta si es necesario
        alert = None
        if institutional_confidence >= 60:
            alert = self.generate_whale_alert(analysis_data)
        
        print(f"\n🎯 RECOMENDACIÓN: {recommendation}")
        print(f"📝 Detalles: {details}")
        
        if alert:
            print(f"\n🚨 ALERTA GENERADA - Confianza: {institutional_confidence:.1f}%")
        
        print("=" * 60)
        
        return analysis_data

def main():
    print("=" * 70)
    print("    BTCUSD INSTITUTIONAL VOLUME DETECTOR")
    print("=" * 70)
    print("Sistema de detección de volumen institucional y actividad de ballenas")
    print("- Análisis de spikes de volumen")
    print("- Detección de impacto en precios") 
    print("- Identificación de patrones institucionales")
    print()
    
    detector = BTCUSDInstitutionalVolumeDetector()
    
    try:
        while True:
            # Ejecutar análisis
            analysis = detector.run_institutional_analysis()
            
            if analysis and analysis['institutional_confidence'] >= 70:
                print(f"\n🚨 ALTA ACTIVIDAD INSTITUCIONAL DETECTADA!")
                print(f"Confianza: {analysis['institutional_confidence']:.1f}%")
            
            print(f"\n⏰ Próximo análisis en 60 segundos...")
            print("Presiona Ctrl+C para detener")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Detector de volumen institucional detenido por usuario")
    except Exception as e:
        print(f"❌ Error en detector: {e}")
    finally:
        print("BTCUSD Institutional Volume Detector finalizado")

if __name__ == "__main__":
    main()