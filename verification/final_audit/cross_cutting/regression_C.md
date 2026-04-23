# Cross-cutting — regression scenario C

**Status:** NOT RE-RUN in this audit.

## Why

`regression/golden/C-ws-balance.json` was captured 2026-04-20 (pre-Phase 2). It hard-codes English page titles ("WS Balance Status") and English thousand separators. Phase 2-A + 2-C intentionally translated these. Running `compare.py C` today would exit 1 on essentially every probed field — value drift due to stale golden, not regression.

Per `IMPLEMENTATION_PLAN.md` §0 Principle: *"Golden files regenerate **only** with explicit Pascal sign-off, never automatically."*

This audit is read-only on production code; auto-regenerating goldens is out of scope.

## Recommended next action

Walk Scenario C with a Playwright session, capture fresh JSON, diff against the old golden, confirm the deltas are ONLY the Phase 2 localization + number format. Commit new golden alongside a stating "Pascal-approved re-capture for stakeholder Phase 2 drift" message. ~30 min effort.

## Headline finding

**CANNOT-VERIFY-LOCALLY** for Scenario C in this run, BUT the underlying balance behaviour is covered by:
- `test_bb_bal` ✅ green
- `test_bb_e2e_auto_cascade` ✅ green
- WS UI verified visually in `screenshots/{localhost,heroku}/06_ws_szenario_abgleich.png` (Speicherdrift = 0,0 GWh on Heroku)

So the absence of a `compare.py C` run does NOT mean Balance is broken — it means the regression harness's golden is outdated, not the system under test.
