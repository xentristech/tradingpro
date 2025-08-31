# ALGO TRADER V3 - Ejecutar como Servicio de Windows
# Ejecutar como Administrador

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    ALGO TRADER V3 - SERVICIO WINDOWS" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptPath "SISTEMA_PERMANENTE.py"

Write-Host "📂 Directorio: $scriptPath" -ForegroundColor Yellow
Write-Host "🐍 Script Python: $pythonScript" -ForegroundColor Yellow
Write-Host ""

if (Test-Path $pythonScript) {
    Write-Host "✅ Script encontrado. Iniciando..." -ForegroundColor Green
    Write-Host "🔄 El sistema se ejecutará permanentemente" -ForegroundColor Green
    Write-Host "⏹️  Presiona Ctrl+C para detener" -ForegroundColor Green
    Write-Host ""
    
    # Ejecutar el sistema permanente
    & python $pythonScript
} else {
    Write-Host "❌ No se encontró SISTEMA_PERMANENTE.py" -ForegroundColor Red
    Write-Host "📂 Verificar que esté en: $pythonScript" -ForegroundColor Red
}

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")