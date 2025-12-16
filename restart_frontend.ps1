$port = 5173
$ErrorActionPreference = "SilentlyContinue"
$tcp = Get-NetTCPConnection -LocalPort $port
if ($tcp) {
    Write-Host "Killing process on port $port..."
    Stop-Process -Id $tcp.OwningProcess -Force
} else {
    Write-Host "No process found on port $port."
}

Set-Location "$PSScriptRoot\frontend"
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Force -Path "logs" }
Write-Host "Starting frontend..."
$p = Start-Process -FilePath "npx.cmd" -ArgumentList "vite --host" -PassThru -RedirectStandardOutput "logs\frontend.log" -RedirectStandardError "logs\frontend_err.log"
Write-Host "Frontend started with PID $($p.Id)"
