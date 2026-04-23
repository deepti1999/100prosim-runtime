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

## Identified drift

1. **T6 PROGRESS.md vs reality:** PROGRESS.md says T6 ✅ Shipped. T6 audit: bench script is a stub. Recommend updating PROGRESS.md to ✅ "Harness shape" + ⚠️ "Measurement TBD in Phase 7-B" or similar nuance.

2. **CLAUDE.md "57/63 shipped":** technically accurate at the literal ✅/⏸ ledger level, but 19 of those 57 are PASS-WITH-CAVEAT in this audit. Headline ratio more like "38 PASS + 19 PASS-WITH-CAVEAT + 0 FAIL = 57 functionally shipped, most polish-ready, some open follow-ups". See `EXECUTIVE_SUMMARY.md` for the full breakdown.

3. **CLAUDE.md does NOT mention:** the "Save All Values" button still exists on /gebaeudewarme/ (analogous UX issue per T28 caveat). Not a documentation gap per se (T28's literal scope was /landuse/ only) but worth a follow-up note.

4. **Cockpit charts blank** is not in any current docs. T43-T47 PASS-WITH-CAVEAT documents this — should propagate to a follow-up entry or known-issue note in CLAUDE.md.

## Verdict

**PASS-WITH-CAVEAT** — docs are mostly accurate; identified 4 specific drift items above for follow-up. Audit findings can be folded into CLAUDE.md / REMAINING.md in a separate documentation cleanup pass.
