# Stakeholder implementation — progress tracker

**Plan of record:** `IMPLEMENTATION_PLAN.md`
**PDF:** `260403_Portierung_Bestandsaufnahme.pdf`

Box states: ☐ = not started · ◐ = in progress · ✅ = done + all 6 verifications pass · ⏸ = blocked / deferred

Commit convention: `<type>(stakeholder-<phase>-<item>): <summary> (T<id>)`

Mandatory per item (non-negotiable, see IMPLEMENTATION_PLAN.md §1):
- V2 unit / contract tests pass
- V3 API smoke passes
- V4 Playwright against localhost passes
- V5 Playwright against live Heroku passes
- V6 docs updated (CLAUDE.md / per-item / memory)

---

## Phase 0 — Scaffolding
- ✅ 0-A Progress tracker file (this file)
- ✅ 0-B Playwright regression scenarios (E/F/G) — YAML stubs committed; playbook scripts land when each phase arrives
- ✅ 0-C `scripts/bench_acid_test.sh` + rolling `BENCHMARK_LOG.md` — harness stub committed; full flow in Phase 7-B

## Phase 1 — Surface removals
- ✅ 1-A Remove "Save All Values" — T28 — condition verified (autoSaveValue debounce 1s), commit `455fa65`
- ✅ 1-B Remove "Goal Seek" + "Refresh" — T19, T20 — condition verified (refreshWsSummaryCards auto-fires + summary endpoint runs goal_seek=True), commit `5fd420e`
- ✅ Phase 1 V5 — Heroku Playwright: both removals verified on live at `prosim-100-2661cfdfdcde.herokuapp.com`. Solar card populated "Optimales Solar: 1.211.176 GWh" automatically on page load without Goal Seek button; Balance buttons enabled correctly.

## Phase 2 — Localization
- ✅ 2-A UI labels to German — T29, T30, T31, T33 — commit `6c82cce` + title/lang fix `10d2c01`
- ✅ 2-B User manual to German — T32, T33 — commit `b8e4a45` (shared with 2-C)
- ✅ 2-C German number format end-to-end — T34, T35, T36 — commits `b8e4a45` + bilanz/admin fix `4131cb2`
- ✅ Phase 2 V5 — Heroku Playwright: all 8 user-reachable pages (login, landuse, renewable, verbrauch, ws, cockpit, bilanz, annual-electricity, user-manual) verified on live at `prosim-100-9fa2a64bdb5f.herokuapp.com`. Titles, headings, columns, buttons, card labels, alert text all German. Numbers in German format everywhere including Bilanz (`329.346` not `329,346`), annual flow diagram (`1.211.176 GWh`), WS summary cards (`Speicherdrift: 0,0 GWh`), LandUse areas (`35.759.529 ha`). 0 English leakage on any page. User manual shows 11 German steps + native German prose.

## Phase 3 — Menu consistency
- ✅ 3-A Universal side-menu — T37, T38, T39, T40 — commit `3bc2976`
- ✅ 3-B Top-bar dedup + brand move — T41, T42 — commit `3bc2976`
- ✅ Phase 3 V5 — Heroku: all 9 pages report sidebar=1, top-nav-dup=0, brand-in-sidebar=1

## Phase 4 — Behaviour fixes
- ✅ 4-A Base-value restore on clear — T14, T15 — commit `cee9a25` (placeholder shows base value on all 3 editable surfaces)
- ✅ 4-B Baseline = admin-provided — T16, T17, T18 — commit `d43ca7d` (shared admin baseline, staff-only creation, 5 new contract tests)
- ✅ 4-C Consolidate Balance buttons (4→2) — T21, T22 — commit `cb62793` (Balance Solar + Balance Wind; underlying endpoints retained)
- ✅ 4-D Fix buttons non-functional after edits + busy indicator — T23 — commit `eb5a6ae` (persistent `#balanceProgressBanner` with real-time polling status)
- ✅ 4-E Auto-cascade — T24, T25, T26, T27 — commit `86e3ba2` (removed skip_cascade on Renewable save; manual Recalculate buttons admin-only)
- ✅ Phase 3+4 batched V5 Heroku: LandUse edit triggered save+cascade live (`Saved to database: Updated LU_2.1 to 1.5% - renewables auto-updated`); Balance Solar/Wind buttons only visible, progress banner DOM in place, base-value data-attrs render (19 on landuse, 44 on verbrauch).

## Phase 5 — Chart rework
- ☐ 5-A Rich Cockpit results overview — T43, T44, T45, T46, T47
- ☐ 5-B Improved annual H₂ chart — T57, T58, T59, T60
- ☐ 5-C Fix electricity/H₂ flow diagram — T53, T54, T55, T56

## Phase 6 — History + details
- ☐ 6-A Modification history model + UI (inspectable, not undo) — T61, T62, T63
- ☐ 6-B Modification-detail variant charts (5) — T48, T49, T50, T51, T52

## Phase 7 — Acid test + handover (external-gated)
- ⏸ 7-A Hosting handover to ErnES — T1, T2, T3, T4
- ⏸ 7-B Acid-test benchmark on ErnES platform — T5, T6, T7

## DEFERRED — Data model (§2.3 of the PDF)
Not on the current plan. Pascal has the Excel files, but this needs a dedicated scoping session before being pulled in. Targets remain tracked and owed to the stakeholder.

- ⏸ T8 Parameter source (Quellbezug) surfaced in UI
- ⏸ T9 Parameter assumption (Annahme) surfaced in UI
- ⏸ T10 Admin can update parameters without code changes
- ⏸ T11 Scenario switcher between regions (DE + Bundesländer)
- ⏸ T12 Data model loaded from external file (Excel interface)
- ⏸ T13 Region-specific data models editable by non-developer admins

---

## Target count

63 atomic targets. Each maps to exactly one item. No skips, no duplicates.

- Phase 0: 1 (T6; others are scaffolding, no T-IDs)
- Phase 1: 3 (T19, T20, T28)
- Phase 2: 8 (T29–T36)
- Phase 3: 6 (T37–T42)
- Phase 4: 12 (T14–T18, T21–T27)
- Phase 5: 13 (T43–T47, T53–T60)
- Phase 6: 8 (T48–T52, T61–T63)
- Phase 7: 6 (T1–T5, T7)
- DEFERRED: 6 (T8–T13)

**Total: 63 unique T-IDs. Range T1–T63.** Nothing skipped; T8–T13 are parked, not dropped.
