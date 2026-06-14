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

if (-not $env:GROQ_API_KEY) {
    $env:GROQ_API_KEY = Read-Host "Enter GROQ_API_KEY for this session"
}

if (-not $env:GROQ_MODEL) {
    $env:GROQ_MODEL = "llama-3.3-70b-versatile"
}

& $Python -m streamlit run dashboardd.py
