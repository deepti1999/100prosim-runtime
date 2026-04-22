#!/usr/bin/env bash
# Acid-test benchmark per PDF §2.2 (T5, T6).
#
# Test case: in the baseline scenario, set onshore wind area 2.0% -> 2.3%
# (LandUse LU_6) and offshore capacity 70 GW -> 60 GW (Renewable 9.3.4), then
# trigger Balance Solar and measure end-to-end elapsed time.
#
# Excel reference: 5.8 s
# Current Heroku Basic: ~120 s (20x slower) as of 2026-04-03
#
# Usage:
#   BASE_URL=http://localhost:8001 bash scripts/bench_acid_test.sh
#   BASE_URL=https://prosim-100-xxxxx.herokuapp.com bash scripts/bench_acid_test.sh
#
# Result is appended to docs/stakeholder/BENCHMARK_LOG.md as JSON.

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8001}"
USERNAME="${BENCH_USER:-testsim}"
PASSWORD="${BENCH_PASS:-TestSim!2026}"
LOG="docs/stakeholder/BENCHMARK_LOG.md"
COMMIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

say "Acid-test benchmark against $BASE_URL (commit $COMMIT_SHA)"

# TODO(T6 full implementation): this script is a stub that captures the intent
# and shape. The actual Playwright-driven flow (login -> reset testsim ->
# edit LU_6 to 2.3% -> edit 9.3.4 to 60 GW -> trigger Balance Solar ->
# poll balance job -> capture elapsed) gets implemented when Phase 7-B lands.
# We keep the stub now so the rolling log and calling pattern are fixed.

cat >&2 <<EOF
[stub] Full benchmark harness will be implemented in Phase 7-B.

Intended flow:
  1. Playwright login as $USERNAME
  2. POST /api/testsim-reset  (bring workspace to clean baseline)
  3. Edit LandUse LU_6 user_percent = 2.3
  4. Edit Renewable 9.3.4 user_value = 60 GW
  5. Navigate to /ws/
  6. Click Balance Solar, start timer
  7. Poll /api/ws/balance-job/<id>/ until status='succeeded'
  8. Stop timer, record elapsed
  9. Capture final speicherdrift, annual_electricity, LU_2.1

For now, this script emits a placeholder entry to $LOG so the log format is
locked in.
EOF

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$(dirname "$LOG")"
if [ ! -f "$LOG" ]; then
  cat > "$LOG" <<'HEADER'
# Acid-test benchmark log

Rolling log of `scripts/bench_acid_test.sh` runs. Per PDF §2.2 — onshore
wind 2.0%→2.3%, offshore 70→60 GW, measure Balance Solar elapsed time.

Excel baseline: 5.8 s. Heroku Basic (2026-04-03): ~120 s.

Format: one JSON object per line, append-only.

HEADER
fi

cat >>"$LOG" <<EOF
\`\`\`json
{"timestamp":"$TIMESTAMP","base_url":"$BASE_URL","commit_sha":"$COMMIT_SHA","elapsed_seconds":null,"status":"stub","note":"harness not yet implemented; Phase 7-B"}
\`\`\`
EOF

say "Logged stub entry to $LOG"
