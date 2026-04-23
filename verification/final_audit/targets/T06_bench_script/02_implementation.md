# T6 — Implementation

## Files

| File | Status |
|---|---|
| `scripts/bench_acid_test.sh` | Exists (76 LOC). |
| `docs/stakeholder/BENCHMARK_LOG.md` | Exists (12 lines). |

## Commits referencing T6

`PROGRESS.md` Phase 0-C credits T6 to the scaffolding push that introduced `scripts/bench_acid_test.sh` + `BENCHMARK_LOG.md` together. Direct grep:

```
$ git log --oneline --all | grep -i 'T6\b\|bench'
```
yields no commit explicitly tagged T6 (it landed in the broader `c403c7d Phase 0 scaffolding` commit per `REMAINING.md` "Commits of record").

## Code shape (current state)

`scripts/bench_acid_test.sh` (read above):
- ✅ Reads `BASE_URL`, `BENCH_USER`, `BENCH_PASS` env vars.
- ✅ Captures `commit_sha` via `git rev-parse --short HEAD`.
- ✅ Appends one JSON line per run to `BENCHMARK_LOG.md`.
- ✅ Initialises `BENCHMARK_LOG.md` with a header on first run.
- ❌ The actual benchmark steps (login → reset → edit → click Balance → poll → measure) are **NOT implemented** — lines 29–34 are a TODO comment, lines 35–51 print "[stub] Full benchmark harness will be implemented in Phase 7-B" to stderr, and line 71 emits a placeholder `"elapsed_seconds": null, "status": "stub"`.

## Coverage by tests

No automated test exercises this shell script. It is intentionally not part of the Django suite (it lives in `scripts/`).

## What the harness *does* lock down today

- The CALLING PATTERN (`BASE_URL=… bash scripts/bench_acid_test.sh`).
- The OUTPUT SHAPE (one JSON object per run, the 5 acceptance fields).
- The LOG FILE PATH.

What it does NOT do today is actually measure anything. The single existing log line in `BENCHMARK_LOG.md` (`elapsed_seconds: null`, `status: stub`) is from the 2026-04-22 stub run.
