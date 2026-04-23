# T16 — Verdict: **PASS**

Commit `d43ca7d` makes "Create baseline" staff-only (gated by `can_create` flag in `/api/baseline/info/`). For testsim (non-staff), the dropdown shows only "Auf Baseline zurücksetzen". `test_bb_admin_baseline::test_can_create_flag_false_for_non_staff` ✅ green. Live verified previously on Heroku per VERIFICATION_STATUS.md §3.

In this audit's screenshots the Baseline dropdown is collapsed (not opened); the gating logic is exercised in V2 tests, V5 already confirmed the dropdown contents at `prosim-100-687a5505e19f`.
