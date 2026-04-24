# Caveat closure — 2026-04-24 fix-bundle summary

**Scope:** close low-risk caveats from `verification/final_audit/index.md`.
**Constraint:** UI / templates / docs / CLI-gap only. Zero backend-math
touches (verified: `git diff 0ef6d22..HEAD -- calculation_engine/
simulator/signals.py simulator/recalc_service.py simulator/ws365_*.py
seed/` is empty).

**Heroku cycles:** 1 (app `prosim-100-a2eca0df3011`, provisioned +
destroyed). Total run cost ~$0.10.

## 7 commits shipped

| # | Commit | Scope |
|---:|---|---|
| 1 | `689fb62` | Fix 3 — docs drift (CLAUDE.md headline, docs_drift.md closure) |
| 2 | `4b5aef0` | Fix 5 — 11 caveats accepted (docs/stakeholder/CAVEATS_ACCEPTED.md) |
| 3 | `fb43411` | Fix 4 — T54 Gasspeicher 83 vs 87 investigation (report only) |
| 4 | `e340cbc` | Fix 1 — T33 German residues (3 strings + 5 siblings) |
| 5 | `b790e64` | Fix 2 — T28 scope align (retain /gebaeudewarme/ per PDF §2.4.5 literal) |
| 6 | `8b06b12` | Fix 1 follow-up — persistence-pill German (found on V5) |
| 7 | `b885333` | V5 Heroku evidence + T33 verdict closure |

## Caveats closed (CAVEAT → PASS) — 3

- **T28** — PDF §2.4.5 re-read: literally Flächen-scoped. Retain
  /gebaeudewarme/ "Alle Werte speichern" button. V2 test locks retention.
- **T33** — 3 documented English residues (Renewable empty-state, login
  flash, Cockpit "Ziel (2050)") + 7 sibling residues (auth flashes +
  persistence pill) now all German. V2 test suite `test_bb_german_ui`
  (8 tests) locks German state.
- **docs_drift.md** — 4 drift items resolved (T6/f86aae9 already
  resolved upstream; CLAUDE.md headline updated; T28 handled by Fix 2;
  Cockpit charts already resolved).

## Caveats accepted (non-breaking, not scheduled for fix) — 11

- **T10, T13** — CLI works; GUI deferred to Phase D per Pascal.
- **T18** — Singleton model + V2 green + prior V5 evidence sufficient.
- **T23** — DOM + prior V5 banner streaming evidence sufficient.
- **T27** — Persistent "Letzte Änderungen" panel IS the durable feedback.
- **T31** — "Balance Solar/Wind" intentional per TRANSLATION_GLOSSARY.
- **T62** — Empty-state + prior V5 populated-layout evidence sufficient.
- **cross_process_cache.md** — Invariant verified by code + Phase C.
- **provenance_audit.md** — V2 covers import; 10-row sweep nice-to-have.
- **heroku_cold_boot.md** — PDF "praxistauglich" has no gating threshold.
- **security_sweep.md** — Django + V2 sufficient; pen-test out of charter.

Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md` with per-entry
rationale + escalation policy.

## Escalated to Pascal — 1

- **T54 (Gasspeicher Tages 83 vs Excel 87)** — full investigation in
  `verification/final_audit/gasspeicher_83_vs_87.md`. Finding: Excel is
  authoritative (L37/Q37 ARE formulas, not hardcoded as
  HARDCODED_VALUES_TRACE.md §6 wrongly claimed). Our simulator's
  `flow_gasspeicher_direkt_tages` uses scenario-target basis (→ 83),
  producing an 83/87/87 split across the three Gasspeicher diagram
  positions; Excel labels all three "87" from the same
  solver-simulated basis. One-line fix proposed
  (`simulator/signals.py:175` — use `gas_storage * tl_factor` instead
  of `(ely_branch_value * ETA_STROM_GAS) * tl_factor`). Filed as
  TaskCreate #8; T54 verdict REMAINS PASS-WITH-CAVEAT until Pascal
  approves the backend math change.

## Verdict tally — delta

**Before:** 42 PASS / 15 CAVEAT / 0 FAIL.
**After:**  44 PASS / 7 CAVEAT-ACCEPTED + 1 CAVEAT-open + 5 cross-cutting (4 ACCEPTED + 1 PASS) / 0 FAIL.
No regressions; full thesis suite 260/260 green (+7 env-skipped).

## What's next for Pascal

- Review `TaskCreate #8` (T54 math fix proposal) — decide whether to
  ship the one-line change in signals.py line 175.
- Everything else in this fix-bundle is final and self-contained.
