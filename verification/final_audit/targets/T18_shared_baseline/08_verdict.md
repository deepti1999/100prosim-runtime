# T18 — Verdict: **PASS-WITH-CAVEAT**

`AdminBaseline` is a singleton (per data model, not per user). Test `test_bb_admin_baseline::test_baseline_shared_across_users` ✅ green — two test users restore from the same source row. V5 two-user concurrency verified previously on `prosim-100-687a5505e19f` (admin_pascal created baseline, testsim restored it; verified same state). Documented in VERIFICATION_STATUS.md §3.

**Caveat:** in this audit run I did NOT execute the two-user roundtrip live (would have dirtied testsim workspace mid-audit and required spinning up admin_pascal). Reusing prior verification + green V2 tests.
