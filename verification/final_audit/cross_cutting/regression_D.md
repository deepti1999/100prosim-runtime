# Cross-cutting — regression scenario D

**Status:** NOT RE-RUN in this audit. Same reason as C — golden pre-dates Phase 2 translation drift.

See `regression_C.md` for the full reasoning. Scenario D ("full flow with Verbrauch edit + Solar/Wind balance") would require ~3-5 minutes of mutation + polling and would also exit 1 due to stale golden.

**Coverage by other means:**
- `test_e2e_current_scenario_flow` ✅ green
- `test_e2e_ui_D_full_flow` env-skipped (Postgres-Playwright requires `requirements-dev.txt` install — see `cross_cutting/e2e_ui_full.md`)

## Verdict

**CANNOT-VERIFY-LOCALLY** for Scenario D in this run. Same recommendation as C: re-capture goldens with Pascal sign-off when next a stakeholder review needs the regression harness.
