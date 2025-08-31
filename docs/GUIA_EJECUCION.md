# 🚀 GUÍA DE EJECUCIÓN RÁPIDA - ALGO TRADER V3

## ⚡ INICIO RÁPIDO (3 PASOS)

### PASO 1: Verificar Estado
```batch
VERIFICAR_ESTADO.bat
```
Esto verificará que todo esté listo para ejecutar.

### PASO 2: Ejecutar Sistema
```batch
EJECUTAR_TODO.bat
```
Esto iniciará todos los servicios automáticamente.

### PASO 3: Acceder a los Dashboards
Los dashboards se abrirán automáticamente en tu navegador:
- **Dashboard Principal**: http://localhost:8512
- **Gráficos en Vivo**: http://localhost:8516
- **TradingView Pro**: http://localhost:8517

---

## 📁 ARCHIVOS DE EJECUCIÓN CREADOS

| Archivo | Función | Descripción |
|---------|---------|-------------|
| **EJECUTAR_TODO.bat** | 🚀 **PRINCIPAL** | Inicia todo el sistema con un clic |
| **execute_all.py** | 🐍 Script Python | Sistema completo con menú interactivo |
| **START_ALL_SERVICES.bat** | 🔧 Alternativo | Inicio detallado con opciones |
| **VERIFICAR_ESTADO.bat** | 🔍 Verificador | Comprueba el estado del sistema |
| **check_system_status.py** | 📊 Diagnóstico | Análisis completo del sistema |

---

## 🎯 MÉTODOS DE EJECUCIÓN

### Método 1: AUTOMÁTICO (Recomendado)
```batch
EJECUTAR_TODO.bat
```
- ✅ Un solo clic
- ✅ Inicia todo automáticamente
- ✅ Abre navegadores
- ✅ Menú interactivo

### Método 2: MANUAL CON PYTHON
```python
python execute_all.py
```
- Control total
- Opciones avanzadas
- Monitoreo en tiempo real

### Método 3: SERVICIOS INDIVIDUALES
```python
# Sistema de ticks
python src/data/TICK_SYSTEM_FINAL.py

# Dashboard principal
python src/ui/dashboards/revolutionary_dashboard_final.py

# Gráficos
python src/ui/charts/chart_simulation_reviewed.py

# TradingView
python src/ui/charts/tradingview_professional_chart.py
```

---

## 🖥️ SERVICIOS DEL SISTEMA

### Servicios Core
| Servicio | Puerto | Estado | URL |
|----------|--------|--------|-----|
| Sistema de Ticks MT5 | 8508 | Core | - |
| Revolutionary Dashboard | 8512 | UI | http://localhost:8512 |
| Chart Simulation | 8516 | UI | http://localhost:8516 |
| TradingView Professional | 8517 | UI | http://localhost:8517 |

### Servicios Opcionales
| Servicio | Puerto | Estado | URL |
|----------|--------|--------|-----|
| Modern Dashboard | 8508 | UI | http://localhost:8508 |
| Signal Dashboard | 8510 | UI | http://localhost:8510 |
| Trading Bot | - | Trading | Modo DEMO/PAPER/LIVE |

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "Python no detectado"
**Solución:**
1. Instala Python 3.10+ desde https://python.org
2. Durante la instalación, marca ✅ "Add Python to PATH"
3. Reinicia el terminal

### Error: "Módulo no encontrado"
**Solución:**
```bash
pip install MetaTrader5 pandas numpy requests beautifulsoup4 plotly
```

### Error: "Puerto ya en uso"
**Solución:**
1. El servicio ya está ejecutándose (está bien)
2. O cierra el proceso anterior:
```batch
taskkill /F /IM python.exe
```

### Error: "MT5 no conectado"
**Solución:**
1. Abre MetaTrader 5
2. Inicia sesión en tu cuenta
3. Permite el trading algorítmico en Herramientas > Opciones > Expert Advisors

---

## 📊 VERIFICAR ESTADO DEL SISTEMA

Para ver un diagnóstico completo:
```batch
VERIFICAR_ESTADO.bat
```

Esto mostrará:
- ✅ Dependencias instaladas
- ✅ Archivos necesarios
- ✅ Servicios activos
- ✅ Conexión MT5
- ✅ URLs disponibles

---

## 🎮 MENÚ INTERACTIVO

Cuando ejecutes `EJECUTAR_TODO.bat`, verás un menú con opciones:

```
[1] Ver estado del sistema
[2] Iniciar Trading Bot (DEMO)
[3] Iniciar Trading Bot (PAPER)
[4] Abrir dashboards en navegador
[5] Reiniciar servicios
[6] Ver logs
[0] Salir
```

---

## 🛑 DETENER EL SISTEMA

### Opción 1: Desde el menú
- Presiona `0` y luego `s` para detener todo

### Opción 2: Cerrar ventana
- Los servicios continuarán en segundo plano
- Para detenerlos completamente:
```batch
taskkill /F /IM python.exe
```

---

## 📝 LOGS Y MONITOREO

Los logs se guardan en:
- `logs/algo_trader.log` - Log principal
- `logs/trading.log` - Log de trading
- `system_status_report.json` - Último estado del sistema

---

## ✅ CHECKLIST DE EJECUCIÓN

- [ ] Python 3.10+ instalado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] MetaTrader 5 instalado y abierto
- [ ] Archivo `.env` configurado con credenciales
- [ ] Ejecutar `VERIFICAR_ESTADO.bat` para confirmar
- [ ] Ejecutar `EJECUTAR_TODO.bat` para iniciar
- [ ] Dashboards abiertos en navegador
- [ ] Trading Bot iniciado (opcional)

---

## 🎉 ¡SISTEMA LISTO!

Una vez que ejecutes `EJECUTAR_TODO.bat`:

1. **Sistema de Ticks**: Analiza datos en tiempo real
2. **Dashboards**: Visualización profesional
3. **Trading Bot**: Ejecuta estrategias (cuando lo actives)
4. **Monitoreo**: Todo se supervisa automáticamente

---

## 💡 TIPS PROFESIONALES

1. **Siempre empieza en modo DEMO** hasta estar seguro
2. **Revisa los logs** regularmente en `logs/`
3. **Monitorea el drawdown** en el dashboard
4. **Usa stop loss** siempre
5. **No operes en noticias** importantes

---

## 🆘 SOPORTE

Si tienes problemas:
1. Ejecuta `VERIFICAR_ESTADO.bat`
2. Revisa el archivo `system_status_report.json`
3. Verifica los logs en `logs/`
4. Asegúrate de que MT5 esté abierto

---

**¡TODO ESTÁ LISTO! Solo ejecuta `EJECUTAR_TODO.bat` y el sistema iniciará automáticamente.**

---
*Desarrollado por XentrisTech - Trading Algorítmico Profesional*