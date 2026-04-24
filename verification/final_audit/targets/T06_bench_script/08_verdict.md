# T6 — Verdict: **PASS** (upgraded from PASS-WITH-CAVEAT 2026-04-24)

## Headline

The harness now actually measures. Replaces the prior `scripts/bench_acid_test.sh` stub (which always emitted `elapsed_seconds: null, status: "stub"`) with a real Python harness `scripts/bench_acid_test.py` that drives 3 user flows over HTTP and records `time.perf_counter()` deltas.

Fix landed in commit `d7822c3` (2026-04-24).

## What changed

`scripts/bench_acid_test.py` (343 LOC, NEW):
- CLI: `--scenario A|C|D|all`, `--runs N`, `--user`, `--base-url`
- Pre-flight: `/healthz` + `/readyz` HTTP 200 or hard-exit
- Scenario A: login → 6 GETs (cockpit/landuse/renewable/verbrauch/bilanz/annual-electricity)
- Scenario C: login → POST /api/ws/apply-balance/ → poll BalanceJob → capture speicherdrift_gwh
- Scenario D: login → POST verbrauch save → POST save-recalc-verbrauch → poll multi-pass recalc job → capture annual_electricity_gwh
- Per-scenario aggregate: median, p95, min, max + per-run elapsed
- Best-effort workspace reset between D runs (gracefully reports caveat when docker CLI unavailable)
- JSON to stdout (back-compat top-level `elapsed_seconds` + `status`) + markdown table to `verification/final_audit/bench_acid_test_<date>.md`

`simulator/test_bb_bench_acid.py` (V2): subprocess-runs the bench with `--scenario A --runs 1` against the live local stack; asserts JSON shape contract (status, elapsed_seconds_median, markdown_summary_path). Skips when `/healthz` unreachable.

## V4 evidence (run on local stack 2026-04-24)

| Scenario | Description | Median (s) | p95 (s) | Min (s) | Max (s) |
|---|---|---:|---:|---:|---:|
| A | read-only nav (6 pages) | 0.9139 | 0.9485 | 0.8794 | 0.9485 |
| C | WS solar balance trigger+poll | 0.8193 | 0.8855 | 0.7531 | 0.8855 |
| D | verbrauch edit + multi-pass recalc | 4.1425 | 5.2042 | 3.0808 | 5.2042 |

Full markdown summary: `verification/final_audit/bench_acid_test_2026-04-24.md`.

## Audit checklist

- [x] Script exists at `scripts/bench_acid_test.py`.
- [x] Reads `--base-url` flag + `BENCH_BASE_URL` env var.
- [x] Captures `commit_sha` from `git rev-parse --short HEAD`.
- [x] Emits structured JSON to stdout.
- [x] Writes markdown summary to `verification/final_audit/bench_acid_test_<date>.md`.
- [x] **Actually measures elapsed time** (3 scenarios, configurable runs).
- [x] Pre-flight `/healthz` + `/readyz` 200 check.
- [x] V2 contract test: `simulator/test_bb_bench_acid.py` (1 test, green).
- [x] V4 manual run with output captured (table above).
- [x] Old `scripts/bench_acid_test.sh` retained for backward compat (also functional with stub schema).

## Notes

- Scenario D's reset path needs the host's `docker` CLI; from inside the docker `web` container the reset is gracefully skipped with a documented caveat. Run from the host shell for full inter-run reset.
- `scripts/bench_acid_test.sh` is NOT removed — it remains the previous stub for any caller still wired to the bash interface. The new `.py` script is the real measurement tool.
- Phase 7-B (acid-test ON ErnES platform) remains future work — this run delivers only the **harness**, not the production-platform measurement.

**Bug task closed:** the T6 stub gap is no longer outstanding.
