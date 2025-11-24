#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CICLO COMPLETO CADA 5 MINUTOS - TRADING PRO V3
==============================================
Ejecuta todos los programas y flujos cada 5 minutos de forma automática
"""

import time
import subprocess
import sys
import os
from datetime import datetime
import logging
import json
import threading
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CICLO_5MIN - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ciclo_5_minutos.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CicloCompleto5Minutos:
    def __init__(self):
        self.running = True
        self.cycle_count = 0
        self.start_time = datetime.now()

        # Lista de programas a ejecutar en cada ciclo
        self.programas_ciclo = [
            # 1. ANÁLISIS DE MERCADO
            'python src/data/twelvedata_client.py',

            # 2. GENERACIÓN DE SEÑALES IA
            'python AI_NEURAL_PRICE_PREDICTOR.py',
            'python AI_OPPORTUNITY_HUNTER.py',
            'python ADVANCED_SIGNAL_GENERATOR.py',

            # 3. ANÁLISIS TÉCNICO
            'python AI_CANDLE_MOMENTUM_DETECTOR.py',
            'python VELOCITY_ACCELERATION_DETECTOR.py',

            # 4. GESTIÓN DE RIESGO
            'python AI_ATR_INTELLIGENT_RISK_CALCULATOR.py',
            'python EMERGENCY_RISK_MANAGER.py',

            # 5. MONITOREO DE POSICIONES
            'python MONITOR_POSITIONS_MT5.py',
            'python CHECK_POSITIONS_NOW.py',

            # 6. TRAILING Y BREAKEVEN
            'python SMART_BREAKEVEN_TRAILING.py',
            'python AI_AUTO_BREAKEVEN_SYSTEM.py',

            # 7. EVALUACIÓN Y LOGS
            'python AI_TRADE_PERFORMANCE_EVALUATOR.py',
            'python SYSTEM_STATUS_CHECK.py'
        ]

        # Programas que deben ejecutarse en background
        self.programas_background = [
            'python MONITOR_CONTINUO_TELEGRAM.py',
            'python AI_REALTIME_VIGILANCE_SYSTEM.py',
            'python monitoring_dashboard.py',
            'python advanced_dashboard.py'
        ]

        # Log de actividades
        self.log_actividades = []

    def log_actividad(self, descripcion, cambio="", estado="PROCESANDO"):
        """Registra actividad con timestamp"""
        actividad = {
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'hora': datetime.now().strftime('%H:%M:%S'),
            'descripcion': descripcion,
            'cambio': cambio,
            'estado': estado,
            'ciclo': self.cycle_count
        }
        self.log_actividades.append(actividad)
        logger.info(f"[CICLO {self.cycle_count}] {descripcion} - {estado}")
        return actividad

    def ejecutar_programa(self, comando, timeout=60):
        """Ejecuta un programa con timeout"""
        try:
            logger.info(f"Ejecutando: {comando}")

            # Ejecutar comando
            process = subprocess.Popen(
                comando,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)

                if process.returncode == 0:
                    self.log_actividad(
                        f"Programa ejecutado: {comando.split()[-1]}",
                        f"Salida exitosa: {len(stdout)} chars",
                        "EXITOSO"
                    )
                    return True, stdout
                else:
                    self.log_actividad(
                        f"Error en programa: {comando.split()[-1]}",
                        f"Error code: {process.returncode}",
                        "ERROR"
                    )
                    return False, stderr

            except subprocess.TimeoutExpired:
                process.kill()
                self.log_actividad(
                    f"Timeout en programa: {comando.split()[-1]}",
                    f"Timeout después de {timeout}s",
                    "TIMEOUT"
                )
                return False, "Timeout"

        except Exception as e:
            self.log_actividad(
                f"Excepción en programa: {comando.split()[-1]}",
                f"Error: {str(e)}",
                "EXCEPCION"
            )
            return False, str(e)

    def iniciar_programas_background(self):
        """Inicia programas que deben correr en background"""
        logger.info("Iniciando programas en background...")

        for programa in self.programas_background:
            try:
                logger.info(f"Iniciando background: {programa}")
                subprocess.Popen(
                    programa,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.log_actividad(
                    f"Background iniciado: {programa.split()[-1]}",
                    "Proceso en background activo",
                    "BACKGROUND"
                )
            except Exception as e:
                logger.error(f"Error iniciando background {programa}: {e}")

    def ejecutar_analisis_mercado(self):
        """Ejecuta análisis completo del mercado"""
        logger.info("=== INICIANDO ANÁLISIS DE MERCADO ===")

        # Análisis con TwelveData
        analisis_cmd = '''python -c "
from src.data.twelvedata_client import TwelveDataClient
from datetime import datetime

print('CICLO ANALISIS - MERCADO')
print('=' * 40)

client = TwelveDataClient()
symbols = ['XAUUSDm', 'BTCUSDm', 'EURUSDm', 'GBPUSDm']

for symbol in symbols:
    print(f'\\nANALIZANDO {symbol}...')
    try:
        analysis = client.get_complete_analysis(symbol)
        if analysis['price']:
            print(f'  PRECIO: {analysis[\"price\"]:.6f}')
        if analysis['indicators']:
            rsi = analysis['indicators'].get('rsi', 0)
            macd = analysis['indicators'].get('macd', 0)
            print(f'  RSI: {rsi:.2f} | MACD: {macd:.4f}')
        print(f'  SENTIMIENTO: {analysis[\"sentiment\"].upper()}')
    except Exception as e:
        print(f'  ERROR: {e}')

print(f'\\nCompletado: {datetime.now().strftime(\"%H:%M:%S\")}')
"'''

        return self.ejecutar_programa(analisis_cmd, timeout=120)

    def ejecutar_ciclo_completo(self):
        """Ejecuta un ciclo completo de 5 minutos"""
        self.cycle_count += 1
        ciclo_start = datetime.now()

        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"INICIANDO CICLO #{self.cycle_count} - {ciclo_start.strftime('%H:%M:%S')}")
        logger.info(f"{'='*60}")

        self.log_actividad(
            f"Inicio de ciclo #{self.cycle_count}",
            f"Ciclo automático cada 5 minutos",
            "INICIADO"
        )

        # 1. ANÁLISIS DE MERCADO
        logger.info("1️⃣ EJECUTANDO ANÁLISIS DE MERCADO...")
        success, output = self.ejecutar_analisis_mercado()
        if success:
            logger.info("✅ Análisis de mercado completado")
        else:
            logger.error("❌ Error en análisis de mercado")

        # 2. EJECUTAR PROGRAMAS DEL CICLO
        logger.info("2️⃣ EJECUTANDO PROGRAMAS DEL CICLO...")
        exitosos = 0
        fallidos = 0

        for i, programa in enumerate(self.programas_ciclo, 1):
            logger.info(f"Ejecutando [{i}/{len(self.programas_ciclo)}]: {programa}")
            success, output = self.ejecutar_programa(programa, timeout=30)

            if success:
                exitosos += 1
            else:
                fallidos += 1

            # Pequeña pausa entre programas
            time.sleep(2)

        # 3. RESUMEN DEL CICLO
        ciclo_end = datetime.now()
        duracion = (ciclo_end - ciclo_start).total_seconds()

        self.log_actividad(
            f"Ciclo #{self.cycle_count} completado",
            f"Exitosos: {exitosos}, Fallidos: {fallidos}, Duración: {duracion:.1f}s",
            "COMPLETADO"
        )

        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"CICLO #{self.cycle_count} COMPLETADO")
        logger.info(f"✅ Exitosos: {exitosos} | ❌ Fallidos: {fallidos}")
        logger.info(f"⏱️ Duración: {duracion:.1f} segundos")
        logger.info(f"🕐 Próximo ciclo en 5 minutos...")
        logger.info(f"{'='*60}")

        # Guardar log de actividades
        self.guardar_log_actividades()

        return exitosos, fallidos, duracion

    def guardar_log_actividades(self):
        """Guarda el log de actividades en JSON"""
        try:
            log_file = f"log_actividades_ciclo_{datetime.now().strftime('%Y%m%d')}.json"

            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_actividades, f, indent=2, ensure_ascii=False)

            logger.info(f"Log de actividades guardado en: {log_file}")

        except Exception as e:
            logger.error(f"Error guardando log de actividades: {e}")

    def mostrar_estadisticas(self):
        """Muestra estadísticas del sistema"""
        tiempo_total = (datetime.now() - self.start_time).total_seconds()
        horas = int(tiempo_total // 3600)
        minutos = int((tiempo_total % 3600) // 60)

        logger.info(f"")
        logger.info(f"📊 ESTADÍSTICAS DEL SISTEMA")
        logger.info(f"⏰ Tiempo ejecutándose: {horas}h {minutos}m")
        logger.info(f"🔄 Ciclos completados: {self.cycle_count}")
        logger.info(f"📋 Actividades registradas: {len(self.log_actividades)}")
        logger.info(f"")

    def run(self):
        """Ejecuta el ciclo principal"""
        logger.info(f"")
        logger.info(f"🚀 INICIANDO SISTEMA DE CICLO COMPLETO CADA 5 MINUTOS")
        logger.info(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"🕐 Hora inicio: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"")

        # Iniciar programas en background
        self.iniciar_programas_background()

        try:
            while self.running:
                # Ejecutar ciclo completo
                exitosos, fallidos, duracion = self.ejecutar_ciclo_completo()

                # Mostrar estadísticas cada 10 ciclos
                if self.cycle_count % 10 == 0:
                    self.mostrar_estadisticas()

                # Esperar 5 minutos (300 segundos)
                logger.info("⏳ Esperando 5 minutos para el próximo ciclo...")

                for i in range(300, 0, -30):
                    if not self.running:
                        break
                    if i % 60 == 0:
                        logger.info(f"⏱️ {i//60} minutos restantes...")
                    time.sleep(30)

        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo sistema por interrupción del usuario...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}")
            self.running = False
        finally:
            logger.info("🏁 Sistema de ciclo completo detenido")
            self.guardar_log_actividades()
            self.mostrar_estadisticas()

def main():
    """Función principal"""
    print("""
╔════════════════════════════════════════════════════════════╗
║           CICLO COMPLETO CADA 5 MINUTOS - V3             ║
║              TRADING PRO AUTOMATIZADO                     ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Crear y ejecutar el sistema de ciclos
    sistema = CicloCompleto5Minutos()
    sistema.run()

if __name__ == "__main__":
    main()