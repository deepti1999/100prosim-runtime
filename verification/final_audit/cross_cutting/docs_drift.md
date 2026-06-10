# Cross-cutting — documentation drift

**Goal:** does CLAUDE.md / REMAINING.md / PROGRESS.md still match actual behaviour observed in this audit?

## CLAUDE.md

Spot-checked sections vs. observed reality:

| CLAUDE.md claim | Audit observation | Status |
|---|---|---|
| "Two-process model: web + worker" | Confirmed via `docker compose ps` (db/web/worker all up) | ✅ |
| "Heroku app name: prosim-100, hostname recreated each cycle" | Confirmed: `prosim-100-e738babd7226.herokuapp.com` provisioned anew this run | ✅ |
| "Test user: testsim / TestSim!2026" | Confirmed: testsim was created by `heroku_up.sh` per log, login works | ✅ |
| "speicherdrift_gwh == '0,0'" hard invariant | Heroku /ws/ shows Speicherdrift = 0,0 ✓; localhost shows 0,1 (testsim workspace state, not regression) | ✅ |
| "Landing page mentions 9.3.1 (405047) but seeded values are 406,403.3" | Not re-checked in this audit — landing page (/) not visited; presumed unchanged | unchecked |
| "T6 — bench script harness shipped" | T6 verdict: PASS-WITH-CAVEAT — script is a stub, doesn't actually measure | ⚠️ stale |
| "57/63 atomic targets shipped + V5-verified + operationally complete" | Audit confirms 57 targets shipped; verdict mix: 38 PASS + 19 PASS-WITH-CAVEAT + 0 FAIL | mostly ✅ |

## REMAINING.md

| Claim | Audit observation | Status |
|---|---|---|
| "Headline: 57/63 shipped" | True — 6 ErnES gated remain (T1-T5, T7) | ✅ |
| "T11/T12/T13 operationally complete" | Confirmed via Phase C synthetic TEST region, V5-verified | ✅ |
| "Speicherdrift hard-invariant 0,0" | Confirmed on Heroku | ✅ |

## PROGRESS.md

Up-to-date as of 2026-04-23. This audit confirms the ✅ marks are accurate per per-target verdicts.

## Stakeholder docs cited but not re-verified

- `FLOW_DIAGRAM_AUDIT.md` — referenced by T53 verdict; document exists with 22-pass iteration history.
- `HARDCODED_VALUES_TRACE.md` §6 — referenced by T54 verdict; documents Gasspeicher Direktverbr 83 vs Excel 87 known discrepancy.
- `DATA_MODEL_IMPORT_AUDIT.md` §0a/§0b/§0c — referenced extensively; matches my findings.
- `260403_Section_2.3_decision.md` — locked D1-D8 decisions per Pascal; not deviated from.

## Identified drift — all 4 resolved 2026-04-24 fix-bundle

1. **T6 PROGRESS.md vs reality:** ✅ **RESOLVED** — real bench harness landed in commit `d7822c3` (`scripts/bench_acid_test.py` — A/C/D scenarios with `perf_counter` timing). PROGRESS.md line 22 now reads `✅ 0-C scripts/bench_acid_test.py (real measurement, commit d7822c3)` which matches reality. T6 verdict upgraded CAVEAT → PASS in index.md post-fix-bundle.

2. **CLAUDE.md "50/63 shipped" headline stale:** ✅ **RESOLVED** — CLAUDE.md §"Stakeholder implementation plan" updated 2026-04-24 to read **57/63 shipped as of 2026-04-23; post-audit 42 PASS / 15 PASS-WITH-CAVEAT / 0 FAIL**, pointing at `verification/final_audit/index.md` for the breakdown.

3. **CLAUDE.md does NOT mention /gebaeudewarme/ Save All Values:** ✅ **RESOLVED via Fix 2 — retained per PDF scope.** PDF §2.4.5 literally names the Flächen page and notes the button does not exist on Erneuerbare/Verbrauch. No PDF mention of Gebäudewärme; the analogous `/gebaeudewarme/` button is a separate UX element. Retention is the intentional decision, locked by V2 test `T28SaveAllScopeTests::test_gebaeudewaerme_retains_alle_werte_speichern`. T28 verdict upgraded CAVEAT → PASS.

4. **Cockpit charts blank not in docs:** ✅ **RESOLVED** — Bug #111 fixed in commit `f86aae9` (data-attribute payload pattern with `|unlocalize` filter). T43-T47 restored CAVEAT → PASS after V4 + V5 Heroku Playwright confirmation. No longer a known-issue needing CLAUDE.md mention; charts render correctly.

## Verdict

**PASS** — all 4 identified drift items resolved 2026-04-24. Items 1 and 4 were already fixed by post-audit commits landed earlier (`d7822c3` + `f86aae9`); item 2 corrected in this fix-bundle; item 3 handled in companion T28 scope-align commit.
