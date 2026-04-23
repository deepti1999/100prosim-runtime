# T6 — Edge cases

## Edge case 1: `BASE_URL` unset

Default kicks in (`BASE_URL=http://localhost:8001`). Script runs. ✅

## Edge case 2: `BENCHMARK_LOG.md` missing

Script writes a header on first run (lines 55–67). ✅

## Edge case 3: Run from outside a git repo

`git rev-parse --short HEAD` fails; the `||` fallback substitutes `'unknown'`. Script still completes. ✅

## Edge case 4: `BASE_URL` is unreachable

Currently the script does NOT make any HTTP calls (stub), so unreachable URLs do not affect anything. **In the real implementation this would be the most important edge case** — the harness should fail loud if it cannot log in / reach the API, NOT silently emit `elapsed_seconds=null`.

## Edge case 5: Multiple concurrent runs

`>>` append is atomic per line on POSIX, so two concurrent script runs append two JSON lines without interleaving. ✅

## Edge case 6: Heroku spin-up still mid-flight

Same as case 4 — stub doesn't reach out, so no effect. The real implementation should retry-with-backoff or fail loud after N failed attempts.
