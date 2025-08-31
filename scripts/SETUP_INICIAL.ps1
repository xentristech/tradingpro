# ================================================
# SCRIPT DE CONFIGURACIÓN INICIAL - ALGO TRADER BOT
# ================================================
Write-Host "
╔══════════════════════════════════════════════════════════════╗
║           CONFIGURACIÓN INICIAL - ALGO TRADER BOT           ║
╚══════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Función para verificar instalación
function Test-Installation {
    param($Name, $Command)
    Write-Host "Verificando $Name... " -NoNewline
    try {
        $result = & $Command 2>&1
        Write-Host "✓ OK" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ NO ENCONTRADO" -ForegroundColor Red
        return $false
    }
}

# 1. VERIFICAR PYTHON
Write-Host "`n1. VERIFICANDO PYTHON" -ForegroundColor Yellow
Write-Host "═══════════════════════" -ForegroundColor Yellow

$pythonInstalled = $false
$pythonPaths = @(
    "python",
    "python3",
    "C:\Python310\python.exe",
    "C:\Python311\python.exe",
    "C:\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
)

foreach ($pyPath in $pythonPaths) {
    try {
        $version = & $pyPath --version 2>&1
        if ($version -match "Python 3\.(10|11|12)") {
            Write-Host "✓ Python encontrado: $version" -ForegroundColor Green
            Write-Host "  Ruta: $pyPath" -ForegroundColor Gray
            $PYTHON = $pyPath
            $pythonInstalled = $true
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonInstalled) {
    Write-Host @"
✗ Python 3.10+ NO está instalado

INSTRUCCIONES DE INSTALACIÓN:
1. Descargar Python desde: https://www.python.org/downloads/
2. Durante la instalación, MARCAR la opción 'Add Python to PATH'
3. Reiniciar PowerShell después de instalar
4. Ejecutar este script nuevamente
"@ -ForegroundColor Red
    exit 1
}

# 2. VERIFICAR OLLAMA
Write-Host "`n2. VERIFICANDO OLLAMA (IA Local)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════" -ForegroundColor Yellow

$ollamaInstalled = $false
try {
    $ollamaVersion = ollama --version 2>&1
    if ($ollamaVersion) {
        Write-Host "✓ Ollama instalado: $ollamaVersion" -ForegroundColor Green
        
        # Verificar si Ollama está ejecutándose
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction SilentlyContinue
            Write-Host "✓ Ollama está ejecutándose" -ForegroundColor Green
            
            # Listar modelos disponibles
            Write-Host "`n  Modelos disponibles:" -ForegroundColor Cyan
            ollama list
            
        } catch {
            Write-Host "⚠ Ollama instalado pero NO está ejecutándose" -ForegroundColor Yellow
            Write-Host "  Iniciando Ollama..." -ForegroundColor Gray
            Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 3
        }
        
        $ollamaInstalled = $true
    }
} catch {
    Write-Host @"
✗ Ollama NO está instalado

INSTRUCCIONES DE INSTALACIÓN:
1. Descargar desde: https://ollama.ai/download
2. Instalar Ollama
3. Abrir terminal y ejecutar: ollama pull deepseek-r1:14b
4. Dejar Ollama ejecutándose en segundo plano
"@ -ForegroundColor Red
}

# 3. VERIFICAR METATRADER 5
Write-Host "`n3. VERIFICANDO METATRADER 5" -ForegroundColor Yellow
Write-Host "══════════════════════════════" -ForegroundColor Yellow

$mt5Paths = @(
    "C:\Program Files\MetaTrader 5\terminal64.exe",
    "C:\Program Files\MetaTrader 5 Exness\terminal64.exe",
    "C:\Program Files\Exness MT5\terminal64.exe",
    "C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
)

$mt5Found = $false
foreach ($mt5Path in $mt5Paths) {
    if (Test-Path $mt5Path) {
        Write-Host "✓ MetaTrader 5 encontrado en: $mt5Path" -ForegroundColor Green
        $MT5_PATH = $mt5Path
        $mt5Found = $true
        break
    }
}

if (-not $mt5Found) {
    Write-Host @"
✗ MetaTrader 5 NO encontrado

INSTRUCCIONES:
1. Descargar MT5 desde tu broker (Exness, IC Markets, etc)
2. Instalar en la ruta por defecto
3. Crear una cuenta DEMO para pruebas
"@ -ForegroundColor Yellow
}

# 4. CREAR ENTORNO VIRTUAL
Write-Host "`n4. CONFIGURANDO ENTORNO VIRTUAL" -ForegroundColor Yellow
Write-Host "══════════════════════════════════" -ForegroundColor Yellow

$venvPath = ".\.venv"
if (Test-Path $venvPath) {
    Write-Host "✓ Entorno virtual ya existe" -ForegroundColor Green
} else {
    Write-Host "Creando entorno virtual..." -ForegroundColor Gray
    & $PYTHON -m venv $venvPath
    Write-Host "✓ Entorno virtual creado" -ForegroundColor Green
}

# Activar entorno virtual
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activando entorno virtual..." -ForegroundColor Gray
    & $activateScript
    Write-Host "✓ Entorno activado" -ForegroundColor Green
}

# 5. INSTALAR DEPENDENCIAS
Write-Host "`n5. INSTALANDO DEPENDENCIAS" -ForegroundColor Yellow
Write-Host "═══════════════════════════" -ForegroundColor Yellow

$pipPath = "$venvPath\Scripts\pip.exe"
$pythonVenv = "$venvPath\Scripts\python.exe"

if (Test-Path "requirements.txt") {
    Write-Host "Instalando paquetes Python..." -ForegroundColor Gray
    & $pipPath install --upgrade pip setuptools wheel 2>&1 | Out-Null
    & $pipPath install -r requirements.txt 2>&1 | ForEach-Object {
        if ($_ -match "Successfully installed") {
            Write-Host $_ -ForegroundColor Green
        } elseif ($_ -match "Requirement already satisfied") {
            # Ignorar mensajes de paquetes ya instalados
        } elseif ($_ -match "ERROR|Failed") {
            Write-Host $_ -ForegroundColor Red
        }
    }
    Write-Host "✓ Dependencias instaladas" -ForegroundColor Green
} else {
    Write-Host "✗ No se encontró requirements.txt" -ForegroundColor Red
}

# 6. VERIFICAR CONFIGURACIÓN
Write-Host "`n6. VERIFICANDO ARCHIVO DE CONFIGURACIÓN" -ForegroundColor Yellow
Write-Host "══════════════════════════════════════════" -ForegroundColor Yellow

$envFile = "configs\.env"
$envExample = "configs\.env.example"

if (Test-Path $envFile) {
    Write-Host "✓ Archivo .env encontrado" -ForegroundColor Green
    Write-Host "  Verificando variables críticas..." -ForegroundColor Gray
    
    $envContent = Get-Content $envFile -Raw
    $criticalVars = @(
        "TWELVEDATA_API_KEY",
        "MT5_LOGIN",
        "MT5_PASSWORD",
        "MT5_SERVER"
    )
    
    foreach ($var in $criticalVars) {
        if ($envContent -match "$var=(.+)") {
            $value = $matches[1].Trim()
            if ($value -eq "your_.*_here" -or $value -eq "") {
                Write-Host "  ⚠ $var NO configurado" -ForegroundColor Yellow
            } else {
                Write-Host "  ✓ $var configurado" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "⚠ Archivo .env NO encontrado" -ForegroundColor Yellow
    if (Test-Path $envExample) {
        Write-Host "Copiando archivo de ejemplo..." -ForegroundColor Gray
        Copy-Item $envExample $envFile
        Write-Host "✓ Archivo .env creado desde ejemplo" -ForegroundColor Green
        Write-Host @"

IMPORTANTE: Editar el archivo configs\.env con tus datos:
- TWELVEDATA_API_KEY: Obtener en https://twelvedata.com/
- MT5_LOGIN: Tu número de cuenta demo
- MT5_PASSWORD: Tu contraseña
- MT5_SERVER: Servidor de tu broker
- TELEGRAM_TOKEN: Crear bot con @BotFather (opcional)
"@ -ForegroundColor Yellow
    }
}

# 7. CREAR DIRECTORIOS NECESARIOS
Write-Host "`n7. CREANDO ESTRUCTURA DE DIRECTORIOS" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow

$directories = @("logs", "data", "backups", "storage")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Directorio '$dir' creado" -ForegroundColor Green
    } else {
        Write-Host "✓ Directorio '$dir' ya existe" -ForegroundColor Green
    }
}

# RESUMEN FINAL
Write-Host "`n" -NoNewline
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    RESUMEN DE CONFIGURACIÓN                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$ready = $true

if ($pythonInstalled) {
    Write-Host "✓ Python:        INSTALADO" -ForegroundColor Green
} else {
    Write-Host "✗ Python:        NO INSTALADO" -ForegroundColor Red
    $ready = $false
}

if ($ollamaInstalled) {
    Write-Host "✓ Ollama:        INSTALADO" -ForegroundColor Green
} else {
    Write-Host "⚠ Ollama:        NO INSTALADO (opcional)" -ForegroundColor Yellow
}

if ($mt5Found) {
    Write-Host "✓ MetaTrader 5:  ENCONTRADO" -ForegroundColor Green
} else {
    Write-Host "⚠ MetaTrader 5:  NO ENCONTRADO" -ForegroundColor Yellow
}

if (Test-Path $envFile) {
    Write-Host "✓ Configuración: ARCHIVO .env EXISTE" -ForegroundColor Green
} else {
    Write-Host "✗ Configuración: FALTA .env" -ForegroundColor Red
    $ready = $false
}

Write-Host "`n" -NoNewline

if ($ready) {
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║       ✓ SISTEMA LISTO PARA EJECUTAR EL BOT                  ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    
    Write-Host @"

PRÓXIMOS PASOS:
═══════════════
1. Editar configs\.env con tus credenciales
2. Ejecutar prueba de conexión MT5:
   .\bot.ps1 setup
   .\.venv\Scripts\python.exe test_mt5_simple.py

3. Iniciar el bot en modo DEMO:
   .\bot.ps1 start

4. Ver logs en tiempo real:
   .\bot.ps1 logs
   
5. Detener el bot:
   .\bot.ps1 stop
"@ -ForegroundColor Cyan
} else {
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║       ⚠ FALTAN COMPONENTES POR CONFIGURAR                   ║" -ForegroundColor Yellow
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    
    Write-Host @"

Por favor:
1. Instala los componentes faltantes
2. Ejecuta este script nuevamente
3. Configura el archivo .env
"@ -ForegroundColor Yellow
}

Write-Host "`nPresiona cualquier tecla para continuar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
