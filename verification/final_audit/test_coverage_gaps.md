# Test coverage — per-module gap table + behaviour-vs-contract audit

**Date:** 2026-04-24 (audit follow-up Tasks 2b + 2c, combined)
**Methodology:** `coverage run --source=simulator,calculation_engine --branch manage.py test simulator -v 0`. Full `coverage report -m` in `coverage_report.txt`. HTML in `coverage_html/index.html`.

**Headline:** **48% line coverage, 11 694 statements, 5 653 missed, 2 740 branches with 263 partial.** Heavy concentration of misses in legacy / management commands / calculation orchestration code.

## Risk classification

Per the follow-up brief:
- **HIGH:** cache invalidation, cross-process signal, goal-seek, region scope, balance worker, workspace service, recalc service, ws365_*.
- **MEDIUM:** API contract, serialization, formula_service.
- **LOW:** templates, pure helpers, admin.

## Per-module gap table — by risk

### HIGH-RISK modules (sorted by line% ascending)

| File | Stmts | Line % | Branch % (Br/BrPart) | Risk note |
|---|---:|---:|---:|---|
| `simulator/ws365_sector_balance.py` | 291 | **2 %** | 0/80 (0/1) | Sector-balance orchestration. Almost no test reaches it. **Big gap — but this is invoked transitively when a real Balance Solar runs end-to-end**, and our suite only does unit-level Balance tests. Fix is an integration test, not a unit one. |
| `simulator/ws365_orchestrator.py` | 455 | **7 %** | 2/92 (0/2) | The 365-day pipeline. Same as above — invoked transitively, not directly. |
| `simulator/page_cockpit.py` | 93 | **8 %** | 0/4 | The page that we just FAILed in Task 1a. View code path is barely exercised — explains why the JS bug went unnoticed. |
| `simulator/percentage_rebalancer.py` | 80 | **15 %** | 2/32 (0/2) | LandUse percent rebalance helper. Used during Balance. |
| `simulator/renewable_recalc.py` | 26 | **24 %** | 1/8 | Renewable cascade helper. |
| `simulator/recalc_service.py` | 295 | **32 %** | 6/68 (0/6) | **Largest HIGH-risk gap in the suite.** Recalc orchestration including goal-seek delegation. |
| `simulator/signals.py` | 255 | **51 %** | 6/54 | Cross-process signal handlers + cache invalidation. CLAUDE.md "Architectural rule" lives or dies here. |
| `simulator/ws365_core.py` | 243 | **51 %** | 4/68 (0/4) | Core 365-day computation. Half-covered — could miss edge cases. |
| `simulator/balance_jobs.py` | 87 | **85 %** | 3/26 (0/3) | The four-cache wipe at job entry. Well-covered. |
| `simulator/recalc_cache.py` | 34 | **92 %** | 1/4 (0/1) | Process-local cache. Well-covered. |
| `simulator/workspace_service.py` | 60 | **92 %** | 3/30 (0/3) | Per-user / per-region clone helper. Well-covered. |
| `simulator/ws365_formula_engine.py` | 244 | **93 %** | 8/68 (0/8) | Formula evaluator. Excellent coverage. |
| `simulator/owner_scope.py` | 50 | **94 %** | 2/14 | OwnerScopedManager. Well-covered. |
| `simulator/region_scope.py` | 18 | **100 %** | 0/2 | Thread-local region scope. Full coverage. |

**HIGH-risk dead-code gaps:**
- `simulator/calculations.py` (512 stmts, 0%) — confirmed **dead code** (zero callers via grep). Legacy procedural calculator, superseded by `calculation_engine/`. Consider deleting in a future cleanup pass.
- `simulator/ws_formula_service.py` (78 stmts, 0%) — confirmed **dead code** (zero callers).
- `simulator/goal_seek.py` (55 stmts, 0%) — only callsite is `simulator/recalc_service.py`. Coverage gap is real (goal-seek convergence is a HIGH-risk path per audit prompt, and we have ZERO tests for it). New test below.
- `simulator/ws365_gw_direct_solve.py` (41 stmts, 0%) — likely invoked from orchestrator's gw-direct path. Coverage gap.

### MEDIUM-RISK modules

| File | Stmts | Line % | Risk |
|---|---:|---:|---|
| `simulator/recalc_api.py` | 93 | 39 % | API contract + 4 cascade endpoints. |
| `simulator/views.py` | 236 | 37 % | Legacy multi-purpose view file. |
| `simulator/balance_api.py` | 177 | 22 % | Balance API surface (4 endpoints). |
| `simulator/formula_service.py` | 555 | 26 % | Formula loading + evaluation. |
| `simulator/input_api.py` | 196 | 66 % | Input save endpoints. |
| `simulator/ws_queue_api.py` | 130 | 72 % | WS job queue endpoints. |
| `simulator/ws_api.py` | 136 | 77 % | WS view endpoints. |
| `simulator/baseline_api.py` | 280 | 78 % | Admin baseline endpoints. |

### LOW-RISK modules

`simulator/admin.py` (32 %), `simulator/page_smard.py` (3 %), `simulator/page_landuse.py` (48 %), various templatetags (44-79 %), management commands (mostly 0 % — they're admin tools, not user-facing). Acceptable.

## Modules under 50% line coverage AND HIGH-risk

5 modules:
1. `simulator/ws365_sector_balance.py` (2 %)
2. `simulator/ws365_orchestrator.py` (7 %)
3. `simulator/page_cockpit.py` (8 %)
4. `simulator/percentage_rebalancer.py` (15 %)
5. `simulator/recalc_service.py` (32 %)

(Plus the 0 %-line modules above where 3 are dead code, 1 is goal_seek.)

## Per-target behaviour-vs-contract classification

For each of the 57 shipped targets, classify the test module as:
- **BEHAVIOUR**: asserts end-state of a workflow including side-effects, signals, cascades, DB state, cache coherency.
- **CONTRACT**: asserts HTTP 200 + shape; doesn't exercise core logic.

| T | Test module(s) | Type | Notes |
|---|---|---|---|
| T6 | (none) | — | T6 is a CLI harness, no test. |
| T8/T9/T10 | `test_wb_provenance_schema`, `test_wb_excel_provenance_import` | BEHAVIOUR | DB rows + manifest hash + idempotency. |
| T11/T12/T13 | `test_wb_region_*` (6 modules), `test_wb_workspace_region`, `test_wb_balance_region_routing`, `test_wb_wsdata_region` | BEHAVIOUR | Region scoping end-to-end including thread-local. |
| T14/T15 | `test_bb_e2e`, implicit in `test_bb_renewable_edit` | CONTRACT (mostly) | Asserts HTTP 200 on save with empty value; doesn't simulate full clear→base round-trip with subsequent reload. **Gap.** |
| T16/T17/T18 | `test_bb_admin_baseline` (5/5) | BEHAVIOUR | Staff gate, shared singleton, restore round-trip. |
| T19/T20/T28 | `test_bb_current_app::test_*_no_*_button` | CONTRACT | Asserts HTML body lacks string. Doesn't verify auto-fire on page open (T19 underlying behaviour). **Gap.** |
| T21/T22 | `test_bb_current_app`, `test_bb_bal` | BEHAVIOUR | Full balance flow exercised. |
| T23 | `test_bb_bal` (banner state in HTML) | CONTRACT | Asserts banner DOM present. Does NOT verify banner UPDATES during job (the live-streaming evidence in `VERIFICATION_STATUS.md` §2 was Playwright, not unit). **Gap — but real-browser coverage.** |
| T24/T25/T26/T27 | `test_bb_e2e_auto_cascade`, `test_bb_renewable_edit` | BEHAVIOUR | Asserts cascade fires on save AND no BalanceJob fires. |
| T29-T36 | `test_bb_current_app` | CONTRACT | Asserts strings present. **By nature of UI translation, contract is appropriate here.** |
| T37-T42 | `test_bb_current_app::test_sidebar_*` | CONTRACT | Asserts sidebar element + count. Appropriate. |
| T43-T47 | `test_bb_modifikationsdetails` (closest) | CONTRACT | **Asserts canvas DOM presence; does NOT execute JS, so the L10N+JS bug went undetected.** This is THE gap that Task 1a found. **New test in 2d below.** |
| T48-T52 | `test_bb_modifikationsdetails` 4/4 + 3 added | BEHAVIOUR (data shape) + CONTRACT (DOM) | Tests verify 4-series JSON shape AND canvas DOM presence. |
| T53/T55/T56 | (no automated test for SVG correctness) | — | Visual-only. Verified through 22-pass Playwright iteration. **Gap — accepted, visual SVG layout is hard to assert in unit tests.** |
| T54 D1-D4c | `test_wb_pmax_dynamic` (8/11) | BEHAVIOUR | Asserts D4a/D4b read from Region. D1/D2/D3/D4c values not unit-tested (they live in template + JS — same pattern as T43-T47, but the JS *does* render them correctly because they go through different code paths). |
| T57-T60 | `test_ws365_formulas` 6/6 | BEHAVIOUR | Calculation parity locked. UI rendering of badge / toggle / stacked bars is CONTRACT-only via DOM grep. |
| T61/T62/T63 | `test_bb_history` 5/5 | BEHAVIOUR | DB row created on save, signal log, per-user scoping, inspect-only assertion. |

**Summary of behaviour-vs-contract gaps:**
- **Critical** — T43-T47: contract-only, missed the JS-bombs-on-numbers bug. Fixed in 2d below with a real-JS-rendering test.
- **Real but accepted** — T53/T55/T56 (visual SVG): no easy unit assertion; the 22-pass Playwright iteration is the verification.
- **Latent** — T14/T15 (clear→base round trip), T19/T20 (auto-fire on page open), T23 (banner streaming): contract-only assertions; real behaviour was verified via prior Playwright sessions (`VERIFICATION_STATUS.md`). Could benefit from real-browser e2e tests.

## What this audit will write (Task 2d)

Six new tests prioritised by impact-per-effort:

1. **`test_wb_cockpit_js_validity.py`** — would have caught the T43-T47 L10N+JS bug. HIGHEST priority.
2. **`test_wb_region_isolation_cross_user.py`** — owner-scope leak: user A in DE, user B in TEST, no cross-read.
3. **`test_wb_active_region_middleware_switch.py`** — switch active region mid-session, subsequent API calls carry new region.
4. **`test_wb_d4ab_region_isolation.py`** — change Region.installed_pmax_ely on a non-active region, active-region values unchanged.
5. **`test_wb_import_idempotent_apply.py`** — `manage.py import_excel_provenance --apply` run twice → "0 changed" the second time.
6. **`test_wb_save_default_cascade.py`** — regression test for the 2026-04 fix (`save()` default cascade behaviour after Renewable lost it). Asserts that `save()` without `skip_cascade` triggers cascade, AND that Renewable in particular does not silently skip.

Each test module:
- Docstring stating the invariant + target(s) covered.
- Golden path test.
- ≥2 edge cases.
- ≥1 regression (referencing the past commit).
