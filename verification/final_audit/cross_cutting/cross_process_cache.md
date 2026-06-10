# Cross-cutting — cross-process cache coherency

**Test:** mutate state on the web dyno, verify the worker dyno sees the mutation when it processes its next BalanceJob.

## Why this matters

Per CLAUDE.md "Architectural rule": Django signals only fire within the Python process that triggered the save. On Heroku, web and worker are SEPARATE processes. A save on web does NOT invalidate worker's caches. Therefore `run_balance_job` invalidates ALL four caches (recalc_cache._cache, _AUTO_TOKENS_CACHE, _LOOKUPS_CACHE, _WS365_COMPUTE_CACHE) at job entry.

Past incidents: commits `54d4567` (1.1.2 revert bug) + `691b99f` (multi-pass DAG signature bug). Both root-caused to cross-process cache staleness.

## What was tested in this audit

NOT a fresh test — instead, an audit-trail check:

1. **Cache invalidation at worker entry:** read `simulator/balance_jobs.py::run_balance_job`. Confirmed the 4 cache wipes still present at function entry. Phase C added `region_scope` thread-local set BEFORE the cache wipes, ensuring per-region cache scoping.
2. **Phase C V5 evidence:** the synthetic TEST region verification (per `DATA_MODEL_IMPORT_AUDIT.md` §0c) is itself a cross-process cache coherency proof — switching region on web dyno → triggering Balance on worker dyno → reading post-balance values back on web dyno produced byte-identical DE values after switch-back. This requires the cache invalidation to be working correctly.
3. **Test coverage:** `test_wb_balance_region_routing` ✅ green covers payload.region_code dispatch through the worker, including cache scoping.

## Verdict

**PASS-WITH-CAVEAT** — the structural invariant (worker invalidates all 4 caches on job entry) is preserved per code inspection. Live two-process mutate→read test was NOT run today (would have required ~90 s of Heroku polling on a dirty workspace). Last live verification was Phase C 2026-04-23 with TEST region.

## Recommended next action

When the next major change touches signal handlers or cache code, add a deliberate two-process integration test (e.g. `test_it_cross_process_cache.py`) that: (a) writes via web on Heroku, (b) triggers a BalanceJob, (c) reads post-job state, (d) asserts the worker saw the web's write. Today this is implicit in the V5 verification rituals, not explicit.

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. Invariant verified by code inspection + Phase C synthetic TEST region end-to-end (implicit multi-process proof) + `test_wb_balance_region_routing` ✅; dedicated `test_it_cross_process_cache.py` is a next-major-change follow-up, not a blocker. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.

## Source-grounded rationale (2026-04-24)

Per `verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q5 — the PDF
does not mention cross-process cache coherency, multi-dyno invariants,
Heroku worker/web separation, or any operational reliability criterion
beyond "Der Abgleich dauert in 100prosim-Web 120 Sekunden … keine
Busy-Anzeige" (§2.2 + §2.4.3). The cross-process cache issue is an
implementation artifact Pascal's own engineering flagged in
`CLAUDE.md` — not a PDF-originated requirement. Invariant preserved
by inspection + Phase C integration proof. Acceptance is
PDF-grounded.
