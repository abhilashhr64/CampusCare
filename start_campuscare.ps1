# CampusCare AI — Native Windows Startup Script
# Run this script to launch the full stack locally without Docker

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Launching CampusCare AI Advanced Working Stack     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot
$PgBin = "C:\Program Files\PostgreSQL\18\bin"
$PgData = "c:\Users\madha\campuscare_pgdata"

# 1. Start PostgreSQL 18 on port 5433 if not running
$pgListening = Get-NetTCPConnection -LocalPort 5433 -ErrorAction SilentlyContinue
if (-not $pgListening) {
    Write-Host "[1/3] Starting PostgreSQL 18 cluster (Port 5433)..." -ForegroundColor Yellow
    Start-Process -FilePath "$PgBin\postgres.exe" -ArgumentList "-D `"$PgData`"" -WindowStyle Hidden
    Start-Sleep -Seconds 3
} else {
    Write-Host "[1/3] PostgreSQL 18 is already active on Port 5433." -ForegroundColor Green
}

# 2. Run Migrations & Start FastAPI Backend
Write-Host "[2/3] Checking Alembic migrations and starting Backend (Port 8000)..." -ForegroundColor Yellow
$backendVenv = "$WorkspaceRoot\backend\.venv\Scripts"
Push-Location "$WorkspaceRoot\backend"
& "$backendVenv\alembic.exe" -c "$WorkspaceRoot\backend\alembic.ini" upgrade head
Pop-Location

$backendListening = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if (-not $backendListening) {
    Start-Process -FilePath "$backendVenv\uvicorn.exe" -ArgumentList "src.main:app --app-dir backend --host 127.0.0.1 --port 8000" -WorkingDirectory $WorkspaceRoot
    Start-Sleep -Seconds 2
} else {
    Write-Host "      Backend is already running on Port 8000." -ForegroundColor Green
}

# 3. Start Next.js Frontend
Write-Host "[3/3] Starting Next.js Frontend (Port 3000)..." -ForegroundColor Yellow
$frontendListening = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if (-not $frontendListening) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$WorkspaceRoot\frontend`"; npm run dev -- -p 3000"
    Start-Sleep -Seconds 3
} else {
    Write-Host "      Frontend is already running on Port 3000." -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " CampusCare AI is LIVE!" -ForegroundColor Green
Write-Host " - Web Portal: http://localhost:3000" -ForegroundColor White
Write-Host " - Interactive API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host " - Health Check: http://127.0.0.1:8000/api/v1/system/health" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green

# Open browser to the web portal
Start-Process "http://localhost:3000"
