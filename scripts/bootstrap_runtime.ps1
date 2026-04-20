$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ROOT_DIR

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: docker is not installed."
    exit 1
}

$composeCheck = docker compose version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: docker compose is not available."
    exit 1
}

$infoCheck = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Docker is not running. Start Docker Desktop and retry."
    exit 1
}

docker compose down --remove-orphans 2>$null

$APP_PORT = if ($env:APP_PORT) { [int]$env:APP_PORT } else { 8001 }
while ($true) {
    $listener = netstat -ano 2>$null | Select-String "LISTENING" | Select-String ":$APP_PORT "
    if (-not $listener) { break }
    $APP_PORT++
}
$env:APP_PORT = $APP_PORT

Write-Host "[1/5] Starting PostgreSQL"
docker compose up -d --force-recreate db

Write-Host "[2/5] Waiting for PostgreSQL readiness"
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    docker compose exec -T db pg_isready -U postgres -d finalthesis3 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $ready) {
    Write-Error "ERROR: PostgreSQL did not become ready in time."
    exit 1
}

Write-Host "[3/5] Running migrations"
docker compose run --rm --no-deps web python manage.py migrate --noinput

Write-Host "[4/5] Loading seed data if database is empty"
docker compose run --rm --no-deps web python manage.py shell -c "from simulator.models import LandUse; import sys; sys.exit(0 if LandUse.objects.exists() else 1)"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Database already contains project data. Skipping seed import."
} else {
    docker compose run --rm --no-deps -e DISABLE_SIMULATOR_SIGNALS=true web python manage.py loaddata seed/sqlite_seed.json
}

Write-Host "[5/5] Starting web and worker processes"
docker compose up -d web worker

Write-Host ""
Write-Host "Bundle is ready."
Write-Host "Web URL: http://localhost:$APP_PORT"
Write-Host "Health URL: http://localhost:$APP_PORT/readyz"
Write-Host "Logs: docker compose logs -f web worker"
