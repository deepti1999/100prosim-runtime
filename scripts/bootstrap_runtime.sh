#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose is not available." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running. Start Docker and retry." >&2
  exit 1
fi

docker compose down --remove-orphans >/dev/null 2>&1 || true

APP_PORT="${APP_PORT:-8001}"
while lsof -ti tcp:${APP_PORT} -sTCP:LISTEN >/dev/null 2>&1; do
  APP_PORT="$((APP_PORT + 1))"
done
export APP_PORT

POSTGRES_PORT="${POSTGRES_PORT:-5432}"
while lsof -ti tcp:${POSTGRES_PORT} -sTCP:LISTEN >/dev/null 2>&1; do
  POSTGRES_PORT="$((POSTGRES_PORT + 1))"
done
export POSTGRES_PORT

echo "[1/5] Starting PostgreSQL"
docker compose up -d --force-recreate db

echo "[2/5] Waiting for PostgreSQL readiness"
ready=false
for _ in {1..40}; do
  if docker compose exec -T db pg_isready -U postgres -d finalthesis3 >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done

if [[ "$ready" != "true" ]]; then
  echo "ERROR: PostgreSQL did not become ready in time." >&2
  exit 1
fi

echo "[3/5] Running migrations"
docker compose run --rm --no-deps web python manage.py migrate --noinput

echo "[4/5] Loading seed data if database is empty"
if docker compose run --rm --no-deps web python manage.py shell -c "from simulator.models import LandUse; import sys; sys.exit(0 if LandUse.objects.exists() else 1)"; then
  echo "Database already contains project data. Skipping seed import."
else
  docker compose run --rm --no-deps -e DISABLE_SIMULATOR_SIGNALS=true web python manage.py loaddata seed/sqlite_seed.json
fi

echo "[5/6] Collecting static files"
docker compose run --rm --no-deps web python manage.py collectstatic --noinput --verbosity 0

echo "[6/6] Starting web and worker processes"
docker compose up -d web worker

echo
echo "Bundle is ready."
echo "Web URL: http://localhost:${APP_PORT}"
echo "Health URL: http://localhost:${APP_PORT}/readyz"
echo "PostgreSQL host port: ${POSTGRES_PORT}"
echo "Logs: docker compose logs -f web worker"
