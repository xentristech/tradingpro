#!/usr/bin/env python
"""
ALGO TRADER AI v3.0 - Sistema Principal
Sistema profesional de trading algorítmico con IA
Author: XentrisTech
Version: 3.0.0
"""
import os
import sys
import argparse
import asyncio
import signal
from pathlib import Path
from datetime import datetime
import json

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Configurar encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.bot_manager import BotManager
from utils.logger_config import setup_logging, TradingLogger, PerformanceLogger
from notifiers.telegram_notifier import TelegramNotifier

# Variable global para el bot
bot_instance = None
logger = None

def print_banner():
    """Muestra banner del sistema"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                    🤖 ALGO TRADER AI v3.0                 ║
    ║              Professional Algorithmic Trading Bot          ║
    ║                      by XentrisTech                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def signal_handler(signum, frame):
    """Manejador de señales del sistema"""
    global bot_instance
    print("\n⚠️  Señal de interrupción recibida...")
    
    if bot_instance and bot_instance.is_running:
        print("Deteniendo bot de forma segura...")
        asyncio.create_task(bot_instance.stop())
    
    sys.exit(0)

async def start_trading(args):
    """
    Inicia el bot de trading
    Args:
        args: Argumentos de línea de comandos
    """
    global bot_instance, logger
    
    try:
        # Crear bot manager
        bot_instance = BotManager(config_path=args.config)
        
        # Configurar modo
        if args.mode == 'live':
            os.environ['LIVE_TRADING'] = 'true'
            logger.warning("⚠️  MODO LIVE ACTIVADO - Operaciones reales")
        elif args.mode == 'paper':
            os.environ['PAPER_TRADING'] = 'true'
            logger.info("📝 Modo Paper Trading activado")
        else:
            os.environ['LIVE_TRADING'] = 'false'
            logger.info("🎮 Modo DEMO activado")
        
        # Iniciar bot
        success = await bot_instance.start()
        
        if not success:
            logger.error("❌ Error al iniciar el bot")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("⚠️  Interrupción por usuario")
        if bot_instance:
            await bot_instance.stop()
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        return 1

async def stop_trading():
    """Detiene el bot de trading"""
    global bot_instance, logger
    
    if bot_instance and bot_instance.is_running:
        logger.info("Deteniendo bot...")
        await bot_instance.stop()
        logger.info("✅ Bot detenido correctamente")
    else:
        logger.info("El bot no está en ejecución")

async def show_status():
    """Muestra el estado del sistema"""
    global bot_instance, logger
    
    print("\n" + "="*60)
    print(" ESTADO DEL SISTEMA")
    print("="*60)
    
    if bot_instance:
        status = bot_instance.get_status()
        
        print(f"\n🤖 Bot Status: {'🟢 RUNNING' if status['running'] else '🔴 STOPPED'}")
        print(f"📊 Modo: {status['mode']}")
        print(f"💱 Símbolo: {status['symbol']}")
        
        print("\n📦 Componentes:")
        for component, active in status['components'].items():
            icon = "✅" if active else "❌"
            print(f"  {icon} {component.capitalize()}")
        
        print("\n📈 Estadísticas:")
        stats = status['stats']
        print(f"  • Trades totales: {stats.get('trades_total', 0)}")
        print(f"  • Trades ganados: {stats.get('trades_won', 0)}")
        print(f"  • Trades perdidos: {stats.get('trades_lost', 0)}")
        print(f"  • Profit total: ${stats.get('profit_total', 0):.2f}")
        
    else:
        print("❌ Bot no inicializado")
    
    # Mostrar performance
    perf_logger = PerformanceLogger()
    summary = perf_logger.get_summary()
    
    if 'total_trades' in summary and summary['total_trades'] > 0:
        print("\n📊 Performance General:")
        print(f"  • Win Rate: {summary['win_rate']:.1f}%")
        print(f"  • P&L Total: ${summary['total_pnl']:.2f}")
        print(f"  • Promedio/Trade: ${summary['avg_trade']:.2f}")
        print(f"  • Mejor trade: ${summary['best_trade']:.2f}")
        print(f"  • Peor trade: ${summary['worst_trade']:.2f}")
    
    print("\n" + "="*60)

async def run_test():
    """Ejecuta pruebas del sistema"""
    global logger
    
    print("\n🧪 EJECUTANDO PRUEBAS DEL SISTEMA...")
    print("="*60)
    
    results = {
        'mt5_connection': False,
        'data_api': False,
        'telegram': False,
        'ml_models': False,
        'risk_manager': False
    }
    
    # Test MT5
    try:
        from broker.mt5_connection import MT5Connection
        mt5 = MT5Connection()
        if mt5.connect():
            results['mt5_connection'] = True
            account = mt5.get_account_info()
            if account:
                print(f"✅ MT5: Conectado - Balance: ${account.balance:.2f}")
            mt5.disconnect()
        else:
            print("❌ MT5: No se pudo conectar")
    except Exception as e:
        print(f"❌ MT5: Error - {e}")
    
    # Test Data API
    try:
        from data.data_manager import DataManager
        dm = DataManager({'symbol': 'BTCUSD'})
        data = await dm.get_data('BTC/USD', '1h', 1)
        if data is not None:
            results['data_api'] = True
            print(f"✅ Data API: OK - Último precio: ${data['close'].iloc[-1]:.2f}")
        else:
            print("❌ Data API: Sin datos")
    except Exception as e:
        print(f"❌ Data API: Error - {e}")
    
    # Test Telegram
    try:
        notifier = TelegramNotifier()
        if notifier.enabled:
            success = await notifier.send_message("🧪 Test de conexión - AlgoTrader v3.0")
            if success:
                results['telegram'] = True
                print("✅ Telegram: Mensaje enviado")
            else:
                print("❌ Telegram: Error enviando mensaje")
        else:
            print("⚠️  Telegram: No configurado")
    except Exception as e:
        print(f"❌ Telegram: Error - {e}")
    
    # Test ML
    try:
        from ml.ml_predictor import MLPredictor
        predictor = MLPredictor()
        results['ml_models'] = True
        print(f"✅ ML: {len(predictor.models)} modelos disponibles")
    except Exception as e:
        print(f"⚠️  ML: {e}")
    
    # Test Risk Manager
    try:
        from risk.risk_manager import RiskManager
        rm = RiskManager()
        assessment = rm.evaluate_trade('BTCUSD', 'buy', 0, 3)
        results['risk_manager'] = True
        print(f"✅ Risk Manager: OK - Trade allowed: {assessment['trade_allowed']}")
    except Exception as e:
        print(f"❌ Risk Manager: Error - {e}")
    
    # Resumen
    print("\n" + "="*60)
    print(" RESUMEN DE PRUEBAS")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component.replace('_', ' ').title()}")
    
    print(f"\n📊 Resultado: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("✨ Sistema completamente operativo!")
    elif passed >= total * 0.6:
        print("⚠️  Sistema parcialmente operativo")
    else:
        print("❌ Sistema requiere configuración")

async def run_backtest(args):
    """Ejecuta backtest del sistema"""
    print("\n📊 MODO BACKTEST")
    print("="*60)
    
    # Implementación de backtest
    print("⚠️  Backtest no implementado aún")
    print("   Use: python backtester.py para backtesting")

async def optimize_strategy(args):
    """Optimiza parámetros de estrategia"""
    print("\n🔧 OPTIMIZACIÓN DE ESTRATEGIA")
    print("="*60)
    
    # Implementación de optimización
    print("⚠️  Optimización no implementada aún")

def main():
    """Función principal con argumentos CLI"""
    global logger
    
    parser = argparse.ArgumentParser(
        description='Algo Trader AI v3.0 - Professional Trading Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py start              # Iniciar en modo demo
  python main.py start --mode live  # Iniciar en modo real
  python main.py status             # Ver estado del sistema
  python main.py test               # Ejecutar pruebas
  python main.py stop               # Detener el bot
        """
    )
    
    # Comandos principales
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status', 'test', 'backtest', 'optimize'],
        help='Comando a ejecutar'
    )
    
    # Opciones
    parser.add_argument(
        '--mode',
        choices=['demo', 'live', 'paper'],
        default='demo',
        help='Modo de trading (default: demo)'
    )
    
    parser.add_argument(
        '--symbol',
        default=None,
        help='Símbolo a operar (default: desde .env)'
    )
    
    parser.add_argument(
        '--config',
        default='configs/.env',
        help='Archivo de configuración (default: configs/.env)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug'
    )
    
    parser.add_argument(
        '--no-telegram',
        action='store_true',
        help='Desactivar notificaciones de Telegram'
    )
    
    # Opciones de backtest
    parser.add_argument(
        '--start-date',
        help='Fecha inicio backtest (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        help='Fecha fin backtest (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--initial-capital',
        type=float,
        default=10000,
        help='Capital inicial para backtest'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(level=log_level)
    
    # Mostrar banner
    print_banner()
    
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Cargar configuración
    from dotenv import load_dotenv
    config_path = PROJECT_ROOT / args.config
    
    if not config_path.exists():
        logger.error(f"❌ Archivo de configuración no encontrado: {config_path}")
        return 1
    
    load_dotenv(config_path)
    
    # Sobrescribir con argumentos CLI
    if args.symbol:
        os.environ['SYMBOL'] = args.symbol
    if args.no_telegram:
        os.environ['TELEGRAM_ENABLED'] = 'false'
    
    # Ejecutar comando
    try:
        if args.command == 'start':
            if args.mode == 'live':
                response = input("⚠️  MODO LIVE - ¿Estás seguro? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Operación cancelada por usuario")
                    return 0
            
            return asyncio.run(start_trading(args))
        
        elif args.command == 'stop':
            return asyncio.run(stop_trading())
        
        elif args.command == 'status':
            return asyncio.run(show_status())
        
        elif args.command == 'test':
            return asyncio.run(run_test())
        
        elif args.command == 'backtest':
            return asyncio.run(run_backtest(args))
        
        elif args.command == 'optimize':
            return asyncio.run(optimize_strategy(args))
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando comando: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import logging
    sys.exit(main())
