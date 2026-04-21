#!/usr/bin/env bash
# Destroy the prosim-100 Heroku app and all its addons. Stops billing immediately.
set -euo pipefail

APP="${HEROKU_APP:-prosim-100}"

command -v heroku >/dev/null || { echo "heroku CLI not installed" >&2; exit 1; }

if ! heroku apps:info -a "$APP" >/dev/null 2>&1; then
  echo "app $APP does not exist — nothing to do"
  exit 0
fi

echo "About to destroy Heroku app: $APP"
echo "  - web + worker dynos will stop"
echo "  - Postgres database will be deleted (data lost)"
echo "  - Redis cache will be deleted"
echo "  - all billing stops"
echo
read -rp "Type the app name ($APP) to confirm: " CONFIRM
if [ "$CONFIRM" != "$APP" ]; then
  echo "aborted"
  exit 1
fi

# Heroku CLI's internal git-remote cleanup may fail on Windows with a harmless
# error even after the app is destroyed — tolerate non-zero exit, then verify.
heroku apps:destroy "$APP" --confirm "$APP" || true

if heroku apps:info -a "$APP" >/dev/null 2>&1; then
  echo "ERROR: app $APP still exists — destroy failed" >&2
  exit 1
fi

if git remote | grep -qx heroku; then
  git remote remove heroku || true
fi

echo
echo "Destroyed. Billing stopped."
echo "Recreate anytime with: bash scripts/heroku_up.sh"
