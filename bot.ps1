param([ValidateSet("start","stop","status","logs","setup")][string]$mode="start")
$ErrorActionPreference = "Stop"

$ROOT = (Get-Location).Path
$VENV = Join-Path $ROOT ".venv"
$PY   = Join-Path $VENV "Scripts\python.exe"
$ACT  = Join-Path $VENV "Scripts\Activate.ps1"
$LOGS = Join-Path $ROOT "logs"

function Setup {
  if (-not (Test-Path $VENV)) { python -m venv $VENV }
  & $ACT
  pip install -r requirements.txt
  if (-not (Test-Path $LOGS)) { New-Item -ItemType Directory -Path $LOGS | Out-Null }
  Write-Host "Setup OK" -ForegroundColor Green
}

function Start-Bot {
  & $ACT
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $lr_out = Join-Path $LOGS "run_${ts}.out.log"
  $lr_err = Join-Path $LOGS "run_${ts}.err.log"
  $lp_out = Join-Path $LOGS "positions_${ts}.out.log"
  $lp_err = Join-Path $LOGS "positions_${ts}.err.log"

  Start-Process -FilePath $PY `
    -ArgumentList @("-m","orchestrator.run") `
    -WorkingDirectory $ROOT `
    -RedirectStandardOutput $lr_out `
    -RedirectStandardError  $lr_err `
    -WindowStyle Minimized

  Start-Process -FilePath $PY `
    -ArgumentList @("-m","orchestrator.positions") `
    -WorkingDirectory $ROOT `
    -RedirectStandardOutput $lp_out `
    -RedirectStandardError  $lp_err `
    -WindowStyle Minimized

  Write-Host "Bot iniciado. Logs en $LOGS" -ForegroundColor Cyan
}

function Stop-Bot {
  Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
  Write-Host "Procesos detenidos." -ForegroundColor Yellow
}

function Status {
  Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,MainWindowTitle,StartTime | Format-Table -AutoSize
}

function Logs {
  $latestOut = Get-ChildItem -Path $LOGS -Filter *.out.log -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
  $latestErr = Get-ChildItem -Path $LOGS -Filter *.err.log -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($latestOut -and ((Get-Item $latestOut.FullName).Length -gt 0)) {
    Write-Host "Mostrando OUT: $($latestOut.Name)"; Get-Content $latestOut.FullName -Wait -Tail 120
  } elseif ($latestErr) {
    Write-Host "Mostrando ERR: $($latestErr.Name)"; Get-Content $latestErr.FullName -Wait -Tail 120
  } else {
    Write-Host "No logs found." -ForegroundColor Yellow
  }
}

switch ($mode) {
  'setup'  { Setup }
  'start'  { Setup; Start-Bot }
  'stop'   { Stop-Bot }
  'status' { Status }
  'logs'   { Logs }
  default  { Setup; Start-Bot }
}
