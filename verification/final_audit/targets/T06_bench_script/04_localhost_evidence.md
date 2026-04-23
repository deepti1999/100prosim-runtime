# T6 — Localhost evidence

## What was run

```bash
BASE_URL=http://localhost:8001 bash scripts/bench_acid_test.sh
```

(Documented in `03_tests.md`.)

## Output captured

One JSON line appended to `docs/stakeholder/BENCHMARK_LOG.md`:

```json
{"timestamp":"<UTC>","base_url":"http://localhost:8001","commit_sha":"<sha>","elapsed_seconds":null,"status":"stub","note":"harness not yet implemented; Phase 7-B"}
```

## UI surfaces affected

**None.** T6 is a CLI-only deliverable — there is no UI to navigate or screenshot.

## Verification approach

T6 is the only target in this audit that has no browser surface, so V4 collapses to "the script runs locally and emits the right shape". That part passes.
