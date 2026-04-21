#!/usr/bin/env bash
# Spin up the prosim-100 Heroku app from scratch: create, addons, config, deploy, seed.
# Idempotent — safe to re-run if a step failed midway.
set -euo pipefail

APP="${HEROKU_APP:-prosim-100}"
REGION="${HEROKU_REGION:-eu}"

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

command -v heroku >/dev/null || { echo "heroku CLI not installed" >&2; exit 1; }
heroku whoami >/dev/null || { echo "not logged in — run: heroku login" >&2; exit 1; }

say "Creating app $APP (region=$REGION)"
if heroku apps:info -a "$APP" >/dev/null 2>&1; then
  echo "app already exists, skipping create"
else
  heroku create "$APP" --region "$REGION" --stack heroku-24
fi

say "Ensuring git remote 'heroku' points to $APP"
if git remote | grep -qx heroku; then
  git remote set-url heroku "https://git.heroku.com/$APP.git"
else
  heroku git:remote -a "$APP"
fi

say "Provisioning addons (Postgres + Redis)"
if ! heroku addons -a "$APP" | grep -q heroku-postgresql; then
  # Don't use --wait: Heroku CLI times out at 5 min even though provisioning continues.
  heroku addons:create heroku-postgresql:essential-0 -a "$APP" || true
fi
# Poll until Postgres reports created state
until heroku addons -a "$APP" 2>/dev/null | grep -q "heroku-postgresql.*created"; do
  echo "  waiting for Postgres to finish provisioning..."
  sleep 15
done
if ! heroku addons -a "$APP" | grep -q heroku-redis; then
  heroku addons:create heroku-redis:mini -a "$APP" --wait
fi

say "Setting config vars"
SECRET="${DJANGO_SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_urlsafe(64))')}"
HOSTNAME="$(heroku apps:info -a "$APP" --json | python -c 'import sys,json; print(json.load(sys.stdin)["app"]["web_url"].rstrip("/").removeprefix("https://"))')"
heroku config:set -a "$APP" \
  DJANGO_SECRET_KEY="$SECRET" \
  DJANGO_DEBUG=false \
  DJANGO_ALLOWED_HOSTS="$HOSTNAME,$APP.herokuapp.com" \
  DJANGO_CSRF_TRUSTED_ORIGINS="https://$HOSTNAME,https://$APP.herokuapp.com" \
  DB_USE_PGBOUNCER=true \
  DB_CONN_MAX_AGE=600 \
  PYTHONUNBUFFERED=1 >/dev/null

say "Deploying (git push heroku main)"
git push heroku main

say "Seeding data"
heroku run -a "$APP" "DISABLE_SIMULATOR_SIGNALS=true python manage.py loaddata seed/sqlite_seed.json" || echo "seed load skipped (already present?)"

say "Creating testsim user"
heroku run -a "$APP" "python manage.py shell -c \"
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(username='testsim', defaults={'email':'testsim@prosim-100.local','is_active':True})
u.set_password('TestSim!2026')
u.is_active = True
u.save()
print(f'testsim {\\\"created\\\" if created else \\\"updated\\\"}: id={u.id}')
\""

say "Smoke test"
sleep 3
curl -fsS -o /dev/null -w "readyz: %{http_code}\n"  "https://$HOSTNAME/readyz"  || true
curl -fsS -o /dev/null -w "healthz: %{http_code}\n" "https://$HOSTNAME/healthz" || true

say "Done — app live at: https://$HOSTNAME"
echo "Login: testsim / TestSim!2026"
echo "Tear down when finished: bash scripts/heroku_down.sh"
