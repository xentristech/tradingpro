# 🚀 GUÍA RÁPIDA DE IMPLEMENTACIÓN

## 📋 CONFIGURACIÓN INICIAL

### 1. Instalación de Dependencias
```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows)
.venv\Scripts\activate

# Activar entorno (Linux/Mac)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración de Variables de Entorno
```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus credenciales
```

### 3. Configuración Mínima Requerida (.env)
```env
# === CONFIGURACIÓN ESENCIAL ===

# MetaTrader 5
MT5_LOGIN=tu_numero_de_cuenta
MT5_PASSWORD=tu_password
MT5_SERVER=Exness-MT5Real  # o tu servidor

# TwelveData API
TWELVEDATA_API_KEY=915b2ea02f7d49b986c1ae27d2711c73

# Trading
SYMBOL=BTCUSDm
RISK_PER_TRADE=0.01
MAX_CONCURRENT_TRADES=1

# Modo (IMPORTANTE: false para demo)
LIVE_TRADING=false

# Opcional: Telegram
TELEGRAM_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
```

## 🎯 CASOS DE USO COMUNES

### CASO 1: Análisis de NAS100
```python
# analizar_nas100.py
import asyncio
from src.data.twelvedata_client import TwelveDataClient
from src.signals.signal_generator import SignalGenerator

async def analizar_nas100():
    # Inicializar cliente
    client = TwelveDataClient()
    
    # Obtener datos
    data = await client.get_time_series('NAS100', '5min', 100)
    
    # Generar señal
    generator = SignalGenerator()
    signal = generator.generate(data)
    
    print(f"Señal NAS100: {signal['direction']}")
    print(f"Fuerza: {signal['strength']}")
    print(f"Confianza: {signal['confidence']}")
    
    return signal

# Ejecutar
if __name__ == "__main__":
    signal = asyncio.run(analizar_nas100())
```

### CASO 2: Trading Automatizado Simple
```python
# trading_simple.py
import os
import time
from src.core.bot_manager import BotManager

def trading_automatico():
    # Configurar modo demo
    os.environ['LIVE_TRADING'] = 'false'
    
    # Crear bot
    bot = BotManager()
    
    # Configurar parámetros
    bot.config['symbol'] = 'BTCUSDm'
    bot.config['risk_per_trade'] = 0.01
    
    # Iniciar trading
    bot.start()
    
    try:
        # Mantener ejecutando
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bot.stop()
        print("Bot detenido")

if __name__ == "__main__":
    trading_automatico()
```

### CASO 3: Monitor de Posiciones
```python
# monitor_posiciones.py
import MetaTrader5 as mt5
import time
from datetime import datetime

def monitorear_posiciones():
    # Conectar a MT5
    if not mt5.initialize():
        print("Error conectando a MT5")
        return
    
    while True:
        # Obtener posiciones
        positions = mt5.positions_get()
        
        if positions:
            print(f"\n=== POSICIONES ACTIVAS ({datetime.now()}) ===")
            for pos in positions:
                profit = pos.profit
                symbol = pos.symbol
                volume = pos.volume
                
                # Color según profit
                color = "🟢" if profit > 0 else "🔴"
                
                print(f"{color} {symbol}: {volume} lotes | P&L: ${profit:.2f}")
        else:
            print("No hay posiciones abiertas")
        
        time.sleep(5)  # Actualizar cada 5 segundos

if __name__ == "__main__":
    monitorear_posiciones()
```

### CASO 4: Detector de Oportunidades
```python
# detector_oportunidades.py
import asyncio
from src.ai.opportunity_hunter import AIOpportunityHunter

async def buscar_oportunidades():
    # Símbolos a analizar
    symbols = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'NAS100', 'EURUSD']
    
    # Crear hunter
    hunter = AIOpportunityHunter()
    
    # Buscar oportunidades
    opportunities = await hunter.scan_markets(symbols)
    
    # Mostrar resultados
    print("\n🎯 OPORTUNIDADES DETECTADAS:")
    print("="*50)
    
    for opp in opportunities[:5]:  # Top 5
        print(f"""
        Símbolo: {opp['symbol']}
        Tipo: {opp['type']}
        Probabilidad: {opp['probability']*100:.1f}%
        R:R Ratio: {opp['risk_reward']:.2f}
        Entrada: ${opp['entry_point']:.2f}
        """)
    
    return opportunities

if __name__ == "__main__":
    asyncio.run(buscar_oportunidades())
```

## 🔧 SCRIPTS ÚTILES

### 1. Verificación Completa del Sistema
```python
# verificar_sistema.py
import sys
import os

def verificar_sistema():
    print("🔍 VERIFICANDO SISTEMA...")
    print("="*50)
    
    checks = {
        'Python Version': sys.version,
        'MT5 Config': os.getenv('MT5_LOGIN', 'NO CONFIGURADO'),
        'API Key': 'OK' if os.getenv('TWELVEDATA_API_KEY') else 'FALTA',
        'Live Mode': os.getenv('LIVE_TRADING', 'false'),
        'Symbol': os.getenv('SYMBOL', 'NO CONFIGURADO')
    }
    
    for key, value in checks.items():
        status = "✅" if value != 'NO CONFIGURADO' and value != 'FALTA' else "❌"
        print(f"{status} {key}: {value}")
    
    # Test MT5
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            print("✅ MT5: Conectado")
            mt5.shutdown()
        else:
            print("❌ MT5: No se puede conectar")
    except:
        print("❌ MT5: No instalado")
    
    # Test TwelveData
    try:
        import requests
        api_key = os.getenv('TWELVEDATA_API_KEY')
        if api_key:
            r = requests.get(f'https://api.twelvedata.com/quote?symbol=BTC/USD&apikey={api_key}')
            if r.status_code == 200:
                print("✅ TwelveData: API funcionando")
            else:
                print("❌ TwelveData: Error en API")
    except:
        print("❌ TwelveData: Error de conexión")

if __name__ == "__main__":
    verificar_sistema()
```

### 2. Gestión de Riesgo en Tiempo Real
```python
# gestion_riesgo_live.py
from src.risk.risk_manager import RiskManager
import MetaTrader5 as mt5

def gestionar_riesgo():
    # Inicializar
    rm = RiskManager()
    mt5.initialize()
    
    # Obtener info de cuenta
    account = mt5.account_info()
    
    # Calcular métricas
    metrics = {
        'balance': account.balance,
        'equity': account.equity,
        'margin': account.margin,
        'free_margin': account.margin_free,
        'margin_level': account.margin_level,
        'drawdown': (account.balance - account.equity) / account.balance * 100
    }
    
    print("\n💰 ESTADO DE CUENTA:")
    print(f"Balance: ${metrics['balance']:.2f}")
    print(f"Equity: ${metrics['equity']:.2f}")
    print(f"Drawdown: {metrics['drawdown']:.2f}%")
    
    # Verificar límites
    if metrics['drawdown'] > 5:
        print("⚠️ ALERTA: Drawdown alto!")
    
    if metrics['margin_level'] < 200:
        print("⚠️ ALERTA: Nivel de margen bajo!")
    
    # Recomendaciones
    max_risk = rm.calculate_position_size(
        metrics['balance'],
        0.01,  # 1% risk
        50     # 50 pips SL
    )
    
    print(f"\n📊 Tamaño máximo recomendado: {max_risk:.2f} lotes")

if __name__ == "__main__":
    gestionar_riesgo()
```

## 📊 COMANDOS RÁPIDOS

### Windows (Archivos .bat)
```bash
# Iniciar sistema completo
EJECUTAR_SISTEMA_COMPLETO.bat

# Solo señales
EJECUTAR_SOLO_SENALES.bat

# Verificar todo
VERIFICAR_TODO.bat

# Monitor de posiciones
VER_POSICIONES.bat

# Diagnóstico
EJECUTAR_DIAGNOSTICO.bat
```

### Python Directo
```bash
# Sistema principal
python main.py start --mode demo

# Ver estado
python main.py status

# Ejecutar tests
python main.py test

# Monitor continuo
python MONITOR_SISTEMA.py

# Dashboard tiempo real
python DASHBOARD_TIEMPO_REAL.py

# Señales avanzadas
python ADVANCED_SIGNAL_GENERATOR.py
```

## 🎮 MODOS DE OPERACIÓN

### MODO 1: Solo Señales (Sin Trading)
```python
# config para solo señales
os.environ['LIVE_TRADING'] = 'false'
os.environ['SIGNALS_ONLY'] = 'true'

# Ejecutar
python ADVANCED_SIGNAL_GENERATOR.py
```

### MODO 2: Paper Trading (Simulado)
```python
# config para paper trading
os.environ['LIVE_TRADING'] = 'false'
os.environ['PAPER_TRADING'] = 'true'

# Ejecutar
python main.py start --mode paper
```

### MODO 3: Trading Real (Con Confirmación)
```python
# config para trading real
os.environ['LIVE_TRADING'] = 'true'

# Ejecutar (pedirá confirmación)
python main.py start --mode live
```

## 🛠️ SOLUCIÓN DE PROBLEMAS COMUNES

### Error: "No se puede conectar a MT5"
```python
# Verificar conexión MT5
import MetaTrader5 as mt5

# Intentar conectar con parámetros específicos
if not mt5.initialize(
    login=int(os.getenv('MT5_LOGIN')),
    password=os.getenv('MT5_PASSWORD'),
    server=os.getenv('MT5_SERVER')
):
    print(f"Error: {mt5.last_error()}")
```

### Error: "API Key inválida"
```python
# Verificar API key
import requests

api_key = os.getenv('TWELVEDATA_API_KEY')
response = requests.get(
    f'https://api.twelvedata.com/api_usage?apikey={api_key}'
)
print(response.json())  # Ver uso y límites
```

### Error: "Sin datos de mercado"
```python
# Verificar símbolo
from src.data.data_manager import DataManager

dm = DataManager({'symbol': 'BTCUSDm'})
symbols = dm.get_available_symbols()
print(f"Símbolos disponibles: {symbols}")
```

## 📈 OPTIMIZACIÓN DE RENDIMIENTO

### 1. Caché de Datos
```python
# Habilitar caché
os.environ['ENABLE_CACHE'] = 'true'
os.environ['CACHE_DURATION'] = '300'  # 5 minutos
```

### 2. Reducir Frecuencia de Análisis
```python
# En config
ANALYSIS_INTERVAL = 60  # segundos
SIGNAL_CHECK_INTERVAL = 30  # segundos
```

### 3. Limitar Indicadores
```python
# Solo indicadores esenciales
ESSENTIAL_INDICATORS = ['rsi', 'macd', 'ema20', 'ema50']
```

## 🔒 SEGURIDAD

### 1. Nunca Compartir
- API Keys
- Contraseñas MT5
- Tokens de Telegram
- Archivos .env

### 2. Usar Variables de Entorno
```python
# BIEN ✅
api_key = os.getenv('TWELVEDATA_API_KEY')

# MAL ❌
api_key = '915b2ea02f7d49b986c1ae27d2711c73'
```

### 3. Límites de Seguridad
```python
# Configurar límites estrictos
MAX_LOSS_PER_DAY = 100  # USD
MAX_TRADES_PER_DAY = 10
MAX_LOT_SIZE = 0.1
```

## 📱 NOTIFICACIONES

### Configurar Telegram
1. Crear bot con @BotFather
2. Obtener token
3. Obtener chat_id
4. Configurar en .env

### Tipos de Notificaciones
```python
# Configurar qué notificar
NOTIFY_SIGNALS = true      # Nuevas señales
NOTIFY_TRADES = true       # Trades ejecutados
NOTIFY_ERRORS = true       # Errores del sistema
NOTIFY_PERFORMANCE = true  # Resumen diario
```

## 🎯 MEJORES PRÁCTICAS

### 1. Siempre Empezar en Demo
```bash
# Verificar modo antes de ejecutar
python -c "import os; print('MODO:', 'LIVE' if os.getenv('LIVE_TRADING')=='true' else 'DEMO')"
```

### 2. Logs Detallados
```python
# Habilitar logs debug
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. Backups Regulares
```bash
# Backup de configuración
copy .env .env.backup

# Backup de datos
xcopy /E /I storage storage_backup
```

### 4. Monitoreo Constante
```python
# Script de monitoreo
while True:
    check_system_health()
    check_positions()
    check_performance()
    time.sleep(60)
```

## 📞 SOPORTE RÁPIDO

### Comandos de Diagnóstico
```bash
# Estado completo
python DIAGNOSTICO_COMPLETO.py

# Verificar señales
python VERIFICAR_SEÑALES.py

# Ver logs
python VISOR_LOGS_TIEMPO_REAL.py
```

### Archivos de Log
- `logs/trading_bot.log` - Log principal
- `logs/signals.log` - Señales generadas
- `logs/trades.log` - Trades ejecutados
- `logs/errors.log` - Errores del sistema

---

**⚡ INICIO RÁPIDO**
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env
copy .env.example .env
# (editar con tus credenciales)

# 3. Verificar sistema
python verificar_sistema.py

# 4. Ejecutar en demo
python main.py start --mode demo

# 5. Monitorear
python MONITOR_SISTEMA.py
```

---
**Versión**: 3.0.0  
**Última actualización**: 2024
