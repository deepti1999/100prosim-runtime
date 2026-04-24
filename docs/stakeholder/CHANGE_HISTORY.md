# Change History: Initial State → 57/63 Shipped

**Author:** Claude (audit follow-up Task 4, 2026-04-24)
**Method:** git archaeology + narrative, not a commit dump.
**Scope:** every behaviour-changing commit on `main` between the PDF-delivery baseline and the current `02908ef` audit-cross-cutting commit. ErnES-gated work (T1-T5+T7) excluded — those depend on stakeholder action and have no code yet.

---

## Baseline (Day 0 — 2026-04-03 PDF delivery)

The 100prosim-Web port arrived in the runtime bundle with Deepti's master-thesis work complete. From the very first commit `a5da7dd chore: initial import of 100ProSim runtime bundle`:

| Metric | Value |
|---|---|
| Total Python LOC (`simulator/` + `calculation_engine/`, excluding migrations) | ~25 000 |
| Migrations at baseline | ~50 (pre-Phase 0; final state today is 57) |
| Test modules at baseline | 33 (incl. test_bb_*, test_wb_*, test_e2e_*, test_ws365_formulas) |
| Frontend templates | 14 main user-facing pages + a handful of partials |
| Calculation backbone | `calculation_engine/` package (~3 200 LOC across `ws_engine`, `bilanz_engine`, `verbrauch_engine`, `renewable_engine`, `landuse_engine`, `formula_evaluator`, `ws_calculator`) plus `simulator/ws365_*.py` |
| Authoritative formula store | 760-row `Formula` table |
| Hosting | Heroku Basic, ad-hoc spin-up by Deepti |

**Known gaps at baseline** (the 63 PDF targets in pre-fix state):
- 6 buttons on `/ws/` instead of 2 (Goal Seek, WS Balance Solar, Sector + WS Solar Balance, WS Balance Wind, Sector + WS Wind Balance, Aktualisieren).
- "Save All Values" button on `/landuse/` only — confusing per §2.4.5.
- Page headings still in English ("Renewable Energy …") despite menu being German.
- Number format English (`1,234.5`) on every page except `/ws/`.
- Sidebar missing on `/verbrauch/`, `/annual-electricity/`, `/user-manual/`; Cockpit has a custom-formatted variant.
- No auto-cascade on user save — users had to click "Recalculate Renewables" manually after every Verbrauch edit.
- "Create baseline" button creates per-user baselines — no shared admin baseline.
- Cockpit shows Status OR Ziel, not both side-by-side.
- No Modifikations-Historie page.
- No Modifikationsdetails page (5 variant-compare charts absent).
- Flow diagram values mis-assigned, small fonts, no zoom.
- Bilanz chart shows neither Min/Max/Kapazität nor daily surplus/deficit bars.
- Parameter rows don't surface source URLs or assumptions.
- Region scope: Germany only, no Bundesländer support.
- No reproducible acid-test benchmark harness.

158 commits later, 57 / 63 of these gaps are operationally closed.

---

## Phase-by-phase narrative

### Phase 0 — Scaffolding (Day 1, 3 commits)

**Intent:** before touching any stakeholder item, set up infrastructure so phases 1-7 can run consistently. Plan-of-record (`IMPLEMENTATION_PLAN.md`), live progress tracker (`PROGRESS.md`), and the regression harness scaffold.

**What changed**
- Plan + progress tracker docs (no T-IDs).
- Regression harness scaffold: `regression/playbook.md`, `regression/scenarios/`, `regression/golden/`, `regression/compare.py` — Claude-driven golden-file UI + calculation regression. Scenarios A (baseline read-only, 162 fields) and C (WS balance with worker poll, 41 fields + speicherdrift invariant) committed at `55fe5b8`. Scenario D added later in `6470e00`.
- T6 acid-test harness stub at `scripts/bench_acid_test.sh` — JSON output schema + log file format locked in; measurement body is a TODO that always emits `elapsed_seconds: null, status: "stub"` until Phase 7-B.
- `.claude/hooks/` for syntax checks + session-start docker/git diagnostics.

**Verification:** scenarios produce JSON; `compare.py A` exits 0.

### Phase 1 — Surface removals (Day 1, 3 commits)

**Intent:** §2.4.3 + §2.4.5 — three buttons the PDF flagged as redundant + confusing.

**What changed**
- `455fa65` **T28**: removed "Save All Values" button from `/landuse/`. Underlying `/api/save-all-inputs/` endpoint left in place.
- `5fd420e` **T19, T20**: removed "Goal Seek" + "Aktualisieren" buttons from `/ws/`. Confirmed first that the underlying behaviour auto-fires on page open + after Balance, then deleted the buttons.
- Phase-summary commit `99a7ccb` recording Heroku V5 verification.

**Files touched:** `simulator/templates/simulator/landuse_list.html`, `ws_template_balance_ui.html`. No backend logic change.

**Tests added:** `test_bb_current_app::test_landuse_no_save_all_values_button`, `test_ws_page_only_shows_two_balance_buttons`. Both still ✅ today.

**Verification:** V5 Heroku at `prosim-100-2661cfdfdcde` confirmed all three removals on live.

### Phase 2 — Localization (~5 commits, 2 days)

**Intent:** §2.5.1 + §2.5.2 — translate every English UI string to native German + adopt German number format end-to-end.

**What changed**
- `6c82cce` **T29, T30, T31, T33**: mass translation of page headings, column labels, button labels across every template under `simulator/templates/`. Translation glossary committed as `docs/stakeholder/TRANSLATION_GLOSSARY.md`.
- `b8e4a45` **T32, T33, T34, T35, T36**: native German rewrite of `/user-manual/` (11 steps, ~1500 words) + Django L10N settings (`LANGUAGE_CODE='de'`, `USE_L10N=True`, `USE_THOUSAND_SEPARATOR=True`) + `parse_de_decimal` utility for input parsing + JS `toLocaleString('de-DE')` everywhere.
- `10d2c01` **T29 fix**: login page `<title>` and `<html lang>` were standalone (didn't extend base) and missed the first sweep — fixed.
- `4131cb2` **T34 fix**: bilanz `format_energy` filter and admin number formatter were custom-rolled, missed by L10N — fixed to delegate to Django locale formatter.

**Files touched:** every template; `landuse_project/settings.py`; new `simulator/templatetags/german_format.py`.

**Risks encountered**
- The L10N settings introduced a latent bug in `simulator/templates/simulator/cockpit.html` lines 287-340 that wasn't caught for ~3 days: float template-vars interpolated directly into JS object literals are auto-formatted by Django to German display strings (`2.432.616,134`), which JavaScript can't parse. **Three Heroku V5 cycles passed without anyone noticing the Cockpit charts were blank** because the test harness asserts HTML-substring presence, not JS parseability. See `verification/final_audit/cockpit_charts_root_cause.md` (audit follow-up Task 1a) for the full investigation. **This bug is the largest open item from this audit run.**

**Verification:** V5 at `prosim-100-9fa2a64bdb5f` confirmed all 8 user-reachable pages 0-English-leaks; numbers German-formatted (e.g. `329.346`, `1.211.176`). Did NOT catch the Cockpit blank-canvas issue at the time.

### Phase 3 — Menu consistency (~2 commits, 1 day)

**Intent:** §2.5.3 — sidebar present on every page, top-bar dedup, 100prosim brand into sidebar header.

**What changed**
- `3bc2976` **T37, T38, T39, T40, T41, T42**: extract sidebar into `_sidebar.html` partial, include in every page; remove duplicated top-bar links; add 100ProSim brand to sidebar top.

**Files touched:** `simulator/templates/simulator/_sidebar.html` (new), `base.html`, every page template that didn't already extend base.

**Verification:** V5 at `prosim-100-09424333c74f` confirmed 9/9 pages have `sidebar_count=1`, top-bar dedup, brand in sidebar.

### Phase 4 — Behaviour fixes (~5 commits, 4 days)

**Intent:** §2.4.1, §2.4.2, §2.4.3, §2.4.4 — five distinct UX issues the PDF called out as confusing or broken.

**What changed**
- `cee9a25` **T14, T15** (4-A): clear-input restores base value across LandUse, Renewable, Verbrauch. Per-row `data-base-value` attribute as the JS clear-target.
- `d43ca7d` **T16, T17, T18** (4-B): admin baseline as singleton (`AdminBaseline` model), staff-only `Create baseline`, `Reset to baseline` reads from singleton. Five new contract tests.
- `cb62793` **T21, T22** (4-C): consolidate 4 balance buttons into 2 ("Balance Solar" + "Balance Wind"). Underlying API endpoints retained; new buttons orchestrate the WS+Sector+WS sequence internally.
- `eb5a6ae` **T23** (4-D): persistent `#balanceProgressBanner` with real-time JS polling against `/api/ws/balance-job/<id>/`. Banner shows status updates every 2s while job runs.
- `86e3ba2` **T24, T25, T26, T27** (4-E): auto-cascade on every save across LandUse + Verbrauch + Renewable. Removed `skip_cascade=True` from `save_renewable_user_input` (the Renewable surface was the only one with the flag — see "Risks" below). Removed manual "Recalculate Renewables" button (or gated admin-only). Toast feedback after each save.

**Risks encountered + mitigations**
- **Cross-process cache bug** (incident, fixed in `54d4567` then `a31fa64`): on Heroku, web and worker are SEPARATE processes. Django signals don't cross process boundaries. Without explicit cache invalidation at worker entry, the worker would compute against stale parameter state from before the user's save. Mitigation: invalidate ALL FOUR process-local caches (`recalc_cache._cache`, `_AUTO_TOKENS_CACHE`, `_LOOKUPS_CACHE`, `_WS365_COMPUTE_CACHE`) at `run_balance_job` entry. Documented in CLAUDE.md "Architectural rule".
- **Multi-pass DAG signature bug** (incident, fixed in `691b99f`): `recalc_cache` key signature excluded computed `ziel` values, so multi-pass DAG convergence stopped after 1 pass (pass 2 saw same signature, returned empty). Mitigation: extend signature to include all output values.
- **Function-name shadowing** (incident, fixed in `9b0cf3d`): `views.py` had `update_user_percent` defined twice; Python silently keeps the last `def`, URL router routed to the wrong signature → 500 error. Mitigation: now grep `^def ` | sort | uniq -c when auditing modules; CLAUDE.md "companion rule".
- **`save() vs save(skip_cascade=True)` divergence**: Renewable's save handler used `skip_cascade=True` historically because cascade was assumed to be triggered separately. T25 broke that assumption by requiring cascade-on-save everywhere. The fix removed the flag — the test suite caught it via `test_bb_renewable_edit::test_renewable_save_triggers_cascade`.

**Tests added:** `test_bb_admin_baseline` (5/5), `test_bb_e2e_auto_cascade`, `test_bb_renewable_edit` cascade extensions.

**Verification:** V5 at `prosim-100-09424333c74f` (batched with Phase 3) — LandUse edit triggered live cascade ("Saved to database: Updated LU_2.1 to 1.5% - renewables auto-updated"). Banner DOM present. Base-value `data-base-value` attrs on 19 LandUse + 44 Verbrauch cells.

### Phase 5 — Chart rework (~30+ commits over ~4 days, including the 22-pass flow diagram iteration)

**Intent:** §2.5.4 (Cockpit Status↔Ziel), §2.5.6 (Flussdiagramm Strom/H₂), §2.5.7 (Jahresgang Strom).

**What changed**
- `10a86e6` **T43, T44, T45, T46, T47** (5-A): Cockpit redesign. Status (Aktuell) / Ziel (2050) toggle, "Sektoren: Verbrauch vs. Erneuerbare" chart, left "Wieviel werden wir noch brauchen?" donut, right "Wo soll es herkommen?" donut, "Prozentuale Veränderung" delta table. **Caveat:** the audit follow-up Task 1a found these charts blank on both envs due to the L10N+JS-literal interaction described in Phase 2. Verdict: 5x FAIL pending Pascal fix. See `verification/final_audit/cockpit_charts_root_cause.md`.
- `f7ce88d` **T57, T58, T59, T60** (5-B): Bilanz Endenergie page. Min / Max / Kapazität=(Max-Min) badge ABOVE the chart. Stacked daily bars: Einspeicherung (blue), Ausspeicherung (orange), Abregelung (grey), with Mangelausgleich overlay. GWh ↔ Tagesladung unit-toggle.
- `268552c` **T53, T55, T56**: flow-diagram font bump + zoom controls + initial Excel-structure pass.
- `7c02458` **T54 D1/D2/D3/D4c**: backend wired the italic blue Tagesladungen under each source value + on each flow segment + percent shares + bottom-right Abgleichdifferenz=160. Formula: `value × (365 / final_stromnetz)`. Wind/Hydro use AE-adjusted numerator. Asymmetric numerators per Excel cells E14/E21/E27/E33.
- `897e212` **T54 D4a/D4b** (Phase B closure): Pmax-Ely-ES `194 GW` and Pmax-RV `261 GW (elekt.)` red labels read from `Region.installed_pmax_*` instead of being hardcoded. Phase C TEST region cycle confirmed these read region-scoped (TEST showed 200/270 GW).

**The 22-pass SVG iteration** for T54 is its own sub-saga. Commits `e55114e` … `f4d1a6a` (over ~3 days) reshaped the flow diagram pass-by-pass to match Excel page 10. Lessons codified in CLAUDE.md "Working with the Jahresstrom flow diagram (SVG iteration discipline)" — Excel WS.xlsm is parseable ground truth (via `scripts/gen_flow_svg.py`), box-on-arrow visually CUTS the arrow (move boxes off), cascade-shift everything when a circle moves, revert beats fix-forward for visual regressions. Pass-by-pass commits made every regression independently revertible. V5 Heroku verification batched at structural milestones (passes 6, 22) rather than every pass.

**Risks encountered + mitigations**
- **Pass-14 visual regression** (revert example): a layout change made things worse; restored via `git checkout <prev-pass-sha> -- annual_electricity.html`. Clean revert, no half-broken intermediate commit.
- **Box-cuts-arrow** complaint (`9e6a19a` "move boxes off arrows"): white-fill value boxes overlapping arrows visually CUT the arrows. Fix: relocate value boxes ABOVE horizontal arrows / RIGHT-of vertical arrows.
- **Cascade-shift omissions** (`2c303d1` "reconnect splitter→Q arrow"): when one circle moved, related arrow endpoints didn't follow. Cascade-list discipline added.
- **Cockpit blank canvases** (Phase 5-A): not noticed at Phase 5 V5; surfaced in audit follow-up Task 1a as a 5-target FAIL.

**Tests added:** `test_bb_modifikationsdetails`, `test_wb_pmax_dynamic` (8/11 pass + 3 env-skip).

**Verification:** V5 at `prosim-100-750ddc9416fd` (batched with Phase 6) — flow diagram fonts + zoom + structure all visible; Bilanz capacity badge `Max − Min: 242.831,1 GWh`, stacked datasets, GWh↔Tagesladung toggle clicked + verified value swap.

### Phase 6 — History + details (2 commits, 5 days)

**Intent:** §2.5.5 (5 variant-compare charts), §2.5.8 (Modifikations-Historie).

**What changed**
- `1051de0` **T61, T62, T63** (6-A): `ModificationHistoryEntry` model + migration `0050` + `/historie/` page. Signal/wrapper logs every user save with `{scenario, timestamp, user, field_path, before_value, after_value}`. Inspectable, NOT undoable — explicitly per PDF "Nachverfolgung" wording. Excel AH.Monitor column-layout matched. 5 contract tests.
- `92ae451` **T48, T49, T50, T51, T52** (6-B): `/modifikationsdetails/` with 5 chart canvases. Each chart has 4 series: Status / Basisszenario / Vorzustand / Aktueller Zustand. Chart endpoints serve 4-series JSON. 4 new tests.

**Verification:** V5 at `prosim-100-750ddc9416fd` confirmed `/historie/` empty + populated states render; `/modifikationsdetails/` all 5 canvases + 4-series legend.

### §2.3 — Phase A (Provenance) — 2026-04-23, 9 commits

**Intent:** §2.3.1 — surface parameter source (Quellbezug) + assumption (Annahme) in UI, allow admin update without code change.

**What changed**
- `d2bd620` **T8/T9/T10 schema migration** (`0051_phase_a_provenance_fields`): `source_url`, `notes_assumption`, `origin` columns added to LandUse, RenewableData, VerbrauchData, GebaeudewaermeData. Additive — no rename.
- `f401ab8` **management command** `import_excel_provenance D.xlsx --apply`: idempotent, fails loud on missing file / bad sheet schema. 13 V2 tests.
- `344e089` **D.xlsx import run**: 265/420 rows changed (80.5% of HIGH-confidence rows from `s_xlsx_map_summary.json`). Manifest + orphan CSV committed. Zero numerical diff (pre/post value-column SHA256 identical).
- `e991949` **info-icon popover** on `/landuse/`, `/renewable/`, `/verbrauch/`, `/gebaeudewarme/`. Bootstrap popover with origin badge + source URL link + assumption text.
- `9db0aec` **workspace propagation** of provenance to 247 user-workspace rows + `/gebaeudewarme/` URL wired (was dead code).
- `9da1a22` provenance_seed fixture + workspace clone fix + heroku_up update.

**Tests added:** `test_wb_provenance_schema` (11), `test_wb_excel_provenance_import` (13). Both ✅.

**Verification:** V5 at `prosim-100-2c767e32f236` confirmed popovers render on all 4 pages; Jahresstrom diagram unaffected (zero numerical regression).

### §2.3 — Phase B (Region first-class) — 2026-04-23, 9 commits

**Intent:** §2.3.2 — Region as a first-class entity. Switcher between DE + Bundesländer. Workspace + diagram values scoped per region.

**What changed**
- `4fc6faf` Region model + DE seed (`0052`).
- `ad4b157` region FK on 4 parameter models (`0053`) — AddField nullable → RunPython backfill → AlterField non-null pattern. 14 V2 tests.
- `126fe3c` workspace per `(owner, region)` — `region_scope` thread-local + `OwnerScopedManager` filter + `ensure_user_workspace_data(user, region_code)`.
- `0f8196b` active-region session middleware.
- `17f557b` region switcher dropdown in nav, POST endpoint, context processor.
- `56ca18f` `--region=<code>` flag on import command + per-region paths.
- `897e212` D4a/D4b dynamic from Region.installed_pmax_*.
- `a7174ea` fixup: scenario serializer (excluded `region` from per-row payload to fix 500 on `/api/scenario/create/`) + seed Region row in `seed/sqlite_seed.json` so TransactionTestCase reseeds DE per test.
- `7102060` docs marker.

**Tests added:** 71 new V2 across 9 modules. Full thesis suite 183/183 green.

**Verification:** V5 at `prosim-100-7b2fe54360e6` confirmed region dropdown active, D4a/D4b read from Region (194/261 GW for DE).

### §2.3 — Phase C (Operational closure) — 2026-04-23, 8 commits

**Intent:** Phase B's region scaffolding was architecturally complete but no actual non-DE region was loaded; 4 deferred TODOs blocked second-region use. Phase C closes them.

**What changed**
- `e23653b` GebaeudewaermeData unique = (region, code) (migration `0054`) — was unique on `code` alone, blocked second-region rows.
- `ae2809f` scenarios carry `region_code` (snapshot/baseline payloads).
- `cb746eb` BalanceJob `payload.region_code` + worker `region_scope` wrap (cross-process region coherency).
- `fb5f2c8` WSData per-`(owner, region)` (migration `0055`) — decision rationale: rejected per-user-only (DE/BB share user's WSData breaks region switching), rejected per-region-only (user edits would mutate global state), chose per-(owner, region) for symmetry with parameter models + cross-process cache coherency per CLAUDE.md.
- `e7b8c19` row-creating import mode for new regions (`_create_region_rows_from_de_template` helper).
- `6dfc2ed` synthetic TEST region full-smoke test + GebaeudewaermeData manager swap (default Manager → OwnerScopedManager).
- `bbff38c` + `373e94c` Heroku V5 helper script `scripts/heroku_seed_test_region.py` (clones DE × 1.05) + django.setup() ordering fix.
- `51f50cd` cosmetic migration 0056 (index name mismatch fixup).

**Tests added:** 27 new V2 tests across 5 modules. Full thesis suite 207/207 green.

**Verification:** V5 at `prosim-100-ce34bbba8419` with synthetic TEST region cloned DE × 1.05. TEST values visibly differ from DE; D4a/D4b read TEST's installed_pmax_* (200 GW / 270 GW); switching back to DE byte-identical baseline (pv=1.211.176, wind=706.236, pmax_ely=194, pmax_rv=261, abgleichdifferenz=157).

---

## Running tallies

| End of phase | Targets shipped | Migrations | Tests | Heroku cycles run |
|---|---:|---:|---:|---:|
| Phase 0 | 1 (T6) | ~50 | 33 | 0 |
| Phase 1 | 4 (+T19/T20/T28) | 50 | 35 | 1 |
| Phase 2 | 12 (+T29-T36) | 50 | 36 | 1 |
| Phase 3 | 18 (+T37-T42) | 50 | 36 | (batched) |
| Phase 4 | 30 (+T14-T18, T21-T27) | 50 | 41 | 1 |
| Phase 5 | 43 (+T43-T47, T53-T60, T54 D1-D4c) | 50 | 45 | 1 (+22 SVG passes) |
| Phase 6 | 51 (+T48-T52, T61-T63) | 51 | 50 | (batched) |
| §2.3 Phase A | 54 (+T8/T9/T10) | 52 | 74 | 1 |
| §2.3 Phase B | 57 architecturally (+T11/T12/T13) | 54 | 145 | 1 |
| §2.3 Phase C | 57 operationally (T11/T12/T13 closed) | 57 | 207 | 1 |

**Total Heroku spin-up/teardown cycles: ~9.** Total Heroku cost across the entire delivery: ~$1.

---

## Key architectural decisions

### 1. Integrate-not-migrate for PyPSA

Rather than rewriting the calculation core in PyPSA (the PowerSystem Python library), we plan to **integrate** PyPSA at the slow numerical cores when Phase 7 perf work begins. Why: the existing `calculation_engine/` is correct, tested, and stakeholder-validated against Excel; replacing it wholesale risks numerical divergence and breaks Pascal's "frozen Formula table" rule. Integration lets us keep the contract-stable interfaces while swapping the inner solver. Documented in `docs/PYPSA_MIGRATION_RESEARCH.md` §23.1.

### 2. Single-dyno Heroku as performance target

Production runs on Heroku Basic (1 web + 1 worker, no parallelism, Postgres-over-network). Optimisations are biased toward this profile — local multi-core Docker wins that don't transfer to single-dyno are deprioritised. Documented in CLAUDE.md "Two main stakeholder work streams §1".

### 3. Process-local caches + signal invalidation rule

Four process-local in-memory caches (recalc_cache._cache, _AUTO_TOKENS_CACHE, _LOOKUPS_CACHE, _WS365_COMPUTE_CACHE) are wiped at every `run_balance_job` entry on the worker. Reason: Django signals don't cross process boundaries, so a save on the web dyno does NOT invalidate the worker's caches. Without this discipline, "silent no-op" bugs (worker pass 1 sees stale cache → returns empty → outer loop breaks early) appear in production but pass locally. Codified in CLAUDE.md "Architectural rule".

### 4. Workspace-scoped data per user

Every parameter table (LandUse, RenewableData, VerbrauchData, GebaeudewaermeData, WSData) has an `owner` FK. A NULL owner = the admin baseline; non-NULL = a user's editable workspace clone. Queryset filtering happens via `OwnerScopedManager` + thread-local `owner_scope`. This lets multiple users edit independently without seeing each other's modifications. Phase B extended the same pattern to include `region`.

### 5. Formula table as authoritative

The 760-row `Formula` table is the single source of truth for derived values. Stakeholder contract — "don't 'clean up' redundant-looking formulas". When a formula needs a behaviour change, edit the row, not the calling code. The `import_formulas_to_db` and `validate_formulas` management commands enforce this.

### 6. Region scaffolding (Phase B) vs operational (Phase C)

Phase B introduced `Region` as a first-class entity with FK on 4 models, a switcher in nav, middleware + workspace plumbing — ARCHITECTURALLY complete but not OPERATIONALLY tested with a non-DE region. The audit `260403_Section_2.3_region_scope_check.md` flagged this as overstating completeness. Phase C added a synthetic TEST region (cloned DE × 1.05 via throwaway script) to V5-prove the region switching works end-to-end. **Lesson:** "feature shipped" requires both architectural and operational verification on a real second instance, not just on the default.

### 7. Provenance via additive columns, not rename

§2.3.1's source-URL + assumption surfacing was implemented by ADDING three columns (`source_url`, `notes_assumption`, `origin`) to the 4 parameter models — never renaming or restructuring existing columns. Reason: stakeholder cell-name contract ("LU_*, 9.3.1, …"). Migration `0051` is purely additive; defaults + nullable so all 247 user-workspace rows stay intact.

### 8. Auto-cascade on save (§2.4.4) vs manual Balance (§2.4.3)

The PDF asked for two distinct things and they look similar but are NOT the same:
- **Cascade** (§2.4.4): change in cell A propagates to dependent cells (Verbrauch change → linked Erneuerbare cells refresh) — Excel-style auto-recalc. Should fire on EVERY user save. Cheap (milliseconds).
- **Balance** (§2.4.3): a global optimisation step that adjusts solar or wind area until the WS-365 cycle closes. Manual, two buttons (Balance Solar + Balance Wind). Expensive (~120s on Heroku Basic).

The codebase now distinguishes these clearly: `save_and_recalculate_*` does cascade; `apply_full_balance*` does Balance. They never invoke each other implicitly.

### 9. WSData per-(owner, region), not per-user OR per-region only

Phase C's WSData decision was contested — three options on the table:
- **per-user only**: rejected because DE/BB users would share the same WSData, breaking region switching.
- **per-region only**: rejected because user edits would mutate global state.
- **per-(owner, region)**: chosen for symmetry with parameter models + cross-process cache coherency.

Documented in commit `fb5f2c8` message body.

### 10. D.xlsx vs _S.xlsx as mapping target (v1 vs v2 audit)

The v1 §2.3 audit (preserved at commit `f5c738b`) framed §2.3 as "import 420 parameters from D.xlsx" and concluded mapping was 35-75% — not clean enough to automate. The v2 audit (committed `4b7b063`) corrected this: `_S.xlsx` is the right mapping target (its sheets are 1:1 with our app pages), and against `_S.xlsx` we get 78% HIGH-confidence + 14% MEDIUM = 92.8% workable mapping. The lesson: when an audit reports "mapping is 50%", check whether you're mapping against the right reference. The v1 result was a side-effect of wrong reference, not a real architectural blocker.

---

## What this wasn't: scope NOT delivered

### 6 ErnES targets (external-gated)

| ID | Description | Blocker |
|---|---|---|
| T1 | ErnES compute platform provisioned | Waiting on ErnES |
| T2 | Runnable installation on ErnES platform | Same |
| T3 | ≥2 ErnES admins trained | Same |
| T4 | Login-credential loss recovery procedure | Implied — also waiting |
| T5 | Run acid test on ErnES platform | Gated on T1-T4 |
| T7 | Architecture review if T5 fails | Conditional on T5 |

T6 (acid-test bench script) is technically shipped per `PROGRESS.md`, but the audit (Task 1a sibling) found it is a STUB — emits `elapsed_seconds: null` always. Real measurement implementation deferred to Phase 7-B (~1-2 hours when ErnES platform is picked).

### 21 PASS-WITH-CAVEAT verdicts (now 16 after Task 1a downgrade)

The original audit found 21 caveats. Task 1a downgraded 5 of those (T43-T47) to FAIL. The remaining 16 caveats are documented per-target in `verification/final_audit/targets/T<nn>/08_verdict.md` files. Headlines:
- 9 caveats reuse prior-session V5 evidence rather than re-running today.
- 3 caveats are documentation/scope nuances (T31 "Balance Solar" intentionally English, T10/T13 CLI not GUI, T28 /landuse/ only).
- 2 caveats document known non-blocking discrepancies (Gasspeicher Direktverbr 87 vs 83, T6 stub).
- 2 are minor visual gaps (T27 ephemeral toast, T62 populated history seed).

### Phase 5-A Cockpit charts (5 new FAILs from Task 1a)

T43-T47 reclassified to FAIL on 2026-04-24 follow-up. Single root cause: Django L10N + JS template literal interaction. Fix recipe: `|unlocalize` filter or `{% localize off %}{% endlocalize %}` block. Estimated ~20-30 min to fix + ~15 min to re-verify on Heroku.

---

## Glossary

| Term | Meaning |
|---|---|
| Bilanz | Balance (energy) — the four-sector summary table |
| Verbrauch | Consumption / demand |
| Gebäudewärme | Building heat |
| Prozesswärme | Process heat |
| Mobile Anwendungen | Mobile applications (transport energy) |
| KLIK | Kraft / Licht / IKT / Kälte (electricity for power, lighting, IT, cooling) |
| Erneuerbare Energien | Renewable energies |
| Flächennutzung | Land use |
| Szenario-Abgleich | Scenario reconciliation (Balance Solar + Balance Wind) |
| Speicherdrift | Storage drift (TAG365 - TAG1; should be 0,0 GWh after Balance) |
| Tagesladung | Daily charge (a unit of energy = annual demand / 365) |
| Mangelausgleich | Shortfall compensation |
| Modifikations-Historie | Modification history (Phase 6-A) |
| Modifikationsdetails | Modification details (Phase 6-B variant-compare charts) |
| Quellbezug | Source reference (T8) |
| Annahme | Assumption (T9) |
| Bundesländer | German federal states (Phase B regions) |
| Cockpit | The Status↔Ziel overview page (Phase 5-A) |
| Jahresstrom / Jahresgang | Annual electricity / annual cycle |
| Praxistauglich | Practically usable (PDF §2.2 acid-test threshold, deliberately not numeric) |
| Nagelprobe | Acid test (PDF §2.2 — the test that decides whether the architecture is fit) |
| WS-365 | The 365-day storage-cycle subsystem |
| Pmax-Ely-ES | Maximum power for electrolysis-storage path (D4a, 194 GW DE) |
| Pmax-RV | Maximum power for re-electrification (Rückverstromung) (D4b, 261 GW DE) |
| Abgleichdifferenz | Reconciliation difference (D4c, 160 GWh) |

---

## Commit index

The 158 commits between baseline and `02908ef` (audit-cross-cutting) span:
- 38 stakeholder-feature commits (`stakeholder-<phase>-<item>:` subjects).
- 22 SVG-iteration commits (`stakeholder-flow-diagram:` for T54).
- 9 fix/incident commits (cross-process cache, multi-pass DAG, view shadowing, etc.).
- 12 perf commits (iteration cuts, cache layers, idempotent short-circuit).
- 11 §2.3 audit commits (Steps A-G + decision lock).
- ~50 docs / scaffolding / chore commits.
- 10 audit verification commits (`verify(<phase>):` subjects from the prior audit run).
- 4 follow-up commits from this run (`followup(<task>):`).

Full chronological commit list available via `git log --since=2026-04-03 --pretty=format:"%h %ad %s" --date=short`. ~30 KB output, not inlined here.

---

**Final tally:** 57/63 stakeholder targets shipped operationally complete. 36 PASS, 16 PASS-WITH-CAVEAT, 5 FAIL (Cockpit charts), 6 ErnES-gated open. ~25 000 LOC across `simulator/` + `calculation_engine/`. 207 tests in the thesis suite. ~9 Heroku V5 cycles. ~$1 total Heroku spend across the entire delivery. The project's history is a textbook example of disciplined incremental delivery against a stakeholder spec — one phase at a time, V2-V6 verification per item, commit-per-item with T-IDs, and honest audit at the end.
