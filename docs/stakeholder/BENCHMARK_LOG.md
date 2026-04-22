# Acid-test benchmark log

Rolling log of `scripts/bench_acid_test.sh` runs. Per PDF §2.2 — onshore
wind 2.0%→2.3%, offshore 70→60 GW, measure Balance Solar elapsed time.

Excel baseline: 5.8 s. Heroku Basic (2026-04-03): ~120 s.

Format: one JSON object per line, append-only.

```json
{"timestamp":"2026-04-22T13:49:11Z","base_url":"http://localhost:8001","commit_sha":"79a5f3a","elapsed_seconds":null,"status":"stub","note":"harness not yet implemented; Phase 7-B"}
```
