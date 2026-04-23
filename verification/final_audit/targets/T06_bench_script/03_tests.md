# T6 — Tests

## Existing test coverage
**None.** The bench script is a shell script in `scripts/`, not exercised by the Django suite.

## Manual smoke run

```
$ BASE_URL=http://localhost:8001 bash scripts/bench_acid_test.sh
==> Acid-test benchmark against http://localhost:8001 (commit 9f2fe3d)
[stub] Full benchmark harness will be implemented in Phase 7-B.

Intended flow:
  1. Playwright login as testsim
  2. POST /api/testsim-reset  (bring workspace to clean baseline)
  …
  9. Capture final speicherdrift, annual_electricity, LU_2.1

For now, this script emits a placeholder entry to docs/stakeholder/BENCHMARK_LOG.md so the log format is locked in.

==> Logged stub entry to docs/stakeholder/BENCHMARK_LOG.md
```

Result: script ran, exit 0, emitted a JSON line.

## Pass/fail

- Existence: ✅
- Runs without error: ✅
- Captures correct metadata fields (`timestamp`, `base_url`, `commit_sha`): ✅
- Captures `elapsed_seconds`: ❌ (always null in current implementation)
- Reproducible cycle-over-cycle: ⚠️ format yes, measurement no

## Test gap

A real test would invoke the script against a known endpoint and assert the resulting JSON line conforms. Not written because the script's measurement is a stub — testing that "stub returns null" is not productive.
