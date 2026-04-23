# T17 — Verdict: **PASS**

`AdminBaseline` singleton model (commit `d43ca7d`) is the source for `/api/baseline/restore/`. Test `test_bb_admin_baseline::test_restore_uses_admin_singleton` ✅ green. V5 prior verification confirmed POST `/api/baseline/restore/` returns 200 with `scope: workspace`, restores admin baseline into testsim's workspace.
