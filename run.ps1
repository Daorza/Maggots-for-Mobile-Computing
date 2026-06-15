$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Virtual environment not found. Create it first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

Write-Host "Starting FastAPI Backend..." -ForegroundColor Green
Start-Process -FilePath $Python -ArgumentList "-m uvicorn main:app --port 8000 --reload" -NoNewWindow

Write-Host "Starting React Frontend..." -ForegroundColor Green
Set-Location "$ProjectRoot\frontend"
Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -NoNewWindow

Write-Host "Services are running! Press Ctrl+C to terminate." -ForegroundColor Cyan
while ($true) { Start-Sleep -Seconds 1 }
