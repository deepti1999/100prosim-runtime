# Stakeholder implementation — progress tracker

**Plan of record:** `IMPLEMENTATION_PLAN.md`
**PDF:** `260403_Portierung_Bestandsaufnahme.pdf`

Box states: ☐ = not started · ◐ = in progress · ✅ = done + all 6 verifications pass · ⏸ = blocked

Commit convention: `<type>(stakeholder-<phase>-<item>): <summary> (T<id>)`

---

## Phase 0 — Scaffolding
- ☐ 0-A Progress tracker file (this file)
- ☐ 0-B Playwright regression scenarios (E/F/G)
- ☐ 0-C `scripts/bench_acid_test.sh` + rolling `BENCHMARK_LOG.md`

## Phase 1 — Surface removals
- ☐ 1-A Remove "Save All Values" — T28
- ☐ 1-B Remove "Goal Seek" + "Refresh" — T19, T20

## Phase 2 — Localization
- ☐ 2-A UI labels to German — T29, T30, T31, T33
- ☐ 2-B User manual to German — T32, T33
- ☐ 2-C German number format end-to-end — T34, T35, T36

## Phase 3 — Menu consistency
- ☐ 3-A Universal side-menu — T37, T38, T39, T40
- ☐ 3-B Top-bar dedup + brand move — T41, T42

## Phase 4 — Behaviour fixes
- ☐ 4-A Base-value restore on clear — T14, T15
- ☐ 4-B Baseline = admin-provided — T16, T17, T18
- ☐ 4-C Consolidate Balance buttons (4→2) — T21, T22
- ☐ 4-D Fix buttons non-functional after edits + busy indicator — T23
- ☐ 4-E Auto-recalc on every change — T24, T25, T26, T27

## Phase 5 — Chart rework
- ☐ 5-A Rich Cockpit results overview — T43, T44, T45, T46, T47
- ☐ 5-B Improved annual H₂ chart — T57, T58, T59, T60
- ☐ 5-C Fix electricity/H₂ flow diagram — T53, T54, T55, T56

## Phase 6 — History + details
- ☐ 6-A Modification history model + UI — T61, T62, T63
- ☐ 6-B Modification-detail variant charts (5) — T48, T49, T50, T51, T52

## Phase 7 — Data model
- ☐ 7-A Parameter traceability — T8, T9, T10
- ☐ 7-B Alternative-region data models — T11, T12, T13

## Phase 8 — Acid test + handover (external-gated)
- ⏸ 8-A Hosting handover to ErnES — T1, T2, T3, T4
- ⏸ 8-B Acid-test benchmark on ErnES platform — T5, T6, T7

---

## Target count

63 atomic targets. Each maps to exactly one item.

- Phase 0: 1 (T6; others are scaffolding, no T-IDs)
- Phase 1: 3 (T19, T20, T28)
- Phase 2: 9 (T29–T36 + reused T33)
- Phase 3: 6 (T37–T42)
- Phase 4: 13 (T14–T18, T21–T27)
- Phase 5: 13 (T43–T47, T53–T60)
- Phase 6: 8 (T48–T52, T61–T63)
- Phase 7: 6 (T8–T13)
- Phase 8: 7 (T1–T5, T7; T6 ships in Phase 0)

Total with reuse-adjustment: **63 unique T-IDs**. No skips.
