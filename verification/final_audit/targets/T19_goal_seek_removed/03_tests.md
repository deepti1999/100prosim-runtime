# T19 — Tests

**Test module:** `simulator.test_bb_current_app` (6/6 passing per `cross_cutting/test_suite_full.md`).

**Most relevant assertion:** the test asserts that `/ws/` HTML body contains exactly the consolidated `Balance Solar` + `Balance Wind` buttons and does NOT contain `Goal Seek` / `Goal Seek ausführen` / `Sector + WS` strings.

**Backing test for auto-run behaviour:** `simulator.test_bb_bal::test_balance_solar_runs_without_explicit_goal_seek_call` confirms running `apply-full-balance` produces the same final state regardless of whether `goal_seek=True` was explicitly invoked first — i.e. the consolidated path orchestrates the goal-seek internally.

**Result:** ✅ green in 2026-04-24 full run.
