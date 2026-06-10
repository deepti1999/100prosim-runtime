# Acid-test bench — 2026-04-24T02:24:15.691896+00:00

- base_url: `http://localhost:8001`
- commit_sha: `unknown`
- user: `testsim`
- runs per scenario: 2
- overall status: **completed**

| Scenario | Description | Runs | Median (s) | p95 (s) | Min (s) | Max (s) | Status |
|---|---|---:|---:|---:|---:|---:|---|
| A | read-only nav (6 pages) | 2 | 0.9139 | 0.9485 | 0.8794 | 0.9485 | ✅ |
| C | WS solar balance trigger+poll | 2 | 0.8193 | 0.8855 | 0.7531 | 0.8855 | ✅ |
| D | verbrauch edit + multi-pass recalc | 2 | 4.1425 | 5.2042 | 3.0808 | 5.2042 | ✅ |
