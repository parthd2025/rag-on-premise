$port = 8000
$ErrorActionPreference = "SilentlyContinue"
$tcp = Get-NetTCPConnection -LocalPort $port
if ($tcp) {
    Write-Host "Killing process on port $port..."
    Stop-Process -Id $tcp.OwningProcess -Force
} else {
    Write-Host "No process found on port $port."
}

$env:HF_HOME = "$PSScriptRoot\backend\models"
Set-Location "$PSScriptRoot\backend"
$python = "$PSScriptRoot\venv\Scripts\python.exe"

Write-Host "Starting backend using $python..."
$p = Start-Process -FilePath $python -ArgumentList "-m uvicorn api.main:app --host 0.0.0.0 --port 8000" -PassThru -RedirectStandardOutput "logs\backend.log" -RedirectStandardError "logs\backend_err.log"
Write-Host "Backend started with PID $($p.Id)"
