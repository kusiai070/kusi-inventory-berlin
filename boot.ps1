# Enterprise System Boot Script
# Checks for processes blocking port 8000 and kills them before starting the API

$port = 8000
$ErrorActionPreference = "SilentlyContinue"

Write-Host "Verificando puerto $port..." -ForegroundColor Cyan

# Find process on port 8000
$tcpConnection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($tcpConnection) {
    $pid_to_kill = $tcpConnection.OwningProcess
    Write-Host "DETECTADO: Proceso $pid_to_kill ocupando puerto $port." -ForegroundColor Yellow
    
    # Kill the process
    try {
        Stop-Process -Id $pid_to_kill -Force
        Write-Host "Proceso $pid_to_kill terminado exitosamente." -ForegroundColor Green
        Start-Sleep -Seconds 1
    }
    catch {
        Write-Host "ERROR: No se pudo terminar el proceso. Puede requerir permisos de administrador." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Puerto $port libre." -ForegroundColor Green
}

Write-Host "Iniciando Backend Enterprise..." -ForegroundColor Cyan
$env:PYTHONPATH = "$PWD"
python backend/api/main.py
