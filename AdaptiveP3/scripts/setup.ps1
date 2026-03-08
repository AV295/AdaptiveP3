# AP3 one-click setup (Windows PowerShell)
# Assumes PostgreSQL is installed and psql is available in PATH.
# Also assumes you already installed Python dependencies.

$ErrorActionPreference = "Stop"

Write-Host "[AP3] Checking psql..." -ForegroundColor Cyan
$psql = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psql) {
    Write-Host "psql not found. Please install PostgreSQL and add psql to PATH." -ForegroundColor Red
    Write-Host "Download: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit 1
}

$projectRoot = "C:\Users\aadha\Documents\VSCode\AdaptiveP3"
$sqlCreate = Join-Path $projectRoot "scripts\01-create-db.sql"
$sqlSeed = Join-Path $projectRoot "scripts\02-seed.sql"

Write-Host "[AP3] Creating database and role..." -ForegroundColor Cyan
# Run against default 'postgres' database as superuser
psql -U postgres -d postgres -f $sqlCreate

Write-Host "[AP3] Seeding data..." -ForegroundColor Cyan
psql -U ap3_user -d ap3_db -f $sqlSeed

Write-Host "[AP3] Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow

# Start the server (assumes virtualenv already active or global packages installed)
uvicorn main:app --reload --port 8000

powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
