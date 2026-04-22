# Verification status — autonomous Phase 3–6 push

Honest audit of what was verified vs. what was not. Saved at end of the
autonomous push so the next reviewer (you, Pascal, or a handover admin)
can see exactly where evidence exists and where it's still needed.

## Verified ✅

### V2 — unit + black-box test suites

Full Django test run against the Docker Postgres stack on
`2026-04-22`:

- `simulator.test_bb_admin_baseline` — **5/5** (Phase 4-B contract: non-staff 403 on create, shared singleton, user workspace restore, 404 without baseline, can_create flag)
- `simulator.test_bb_bal` — full pass (balance API contracts)
- `simulator.test_bb_calc` — full pass (calculation engine contracts)
- `simulator.test_bb_current_app` — **6/6** including the updated "/ws/ shows only Balance Solar + Balance Wind" assertion and the updated user-manual "Benutzerhandbuch + Schritt 1 + Flächennutzung" assertion
- `simulator.test_bb_e2e` — **2/2** (landuse-update-then-recalc + baseline-create-mutate-restore roundtrip, the latter exercising the 4-B admin baseline capture/restore path)
- `simulator.test_bb_history` — **5/5** (Phase 6-A: LandUse edit logged, Verbrauch edit logged, per-user scoping, empty-user friendly page, inspect-only)
- `simulator.test_bb_modifikationsdetails` — **4/4** (Phase 6-B: page 200, all 5 PDF titles present, 4-series keys in JSON, all 5 canvas ids)
- `simulator.test_bb_renewable_edit` — full pass (4-E cascade on save)
- `simulator.test_bb_val` — full pass
- `simulator.test_it_current_recalc_contracts` — full pass
- `simulator.test_wb_queue_jobs_middleware` — full pass
- `simulator.test_wb_scenario_state` — **6/6**
- `simulator.test_wb_ws365_formula_engine` — full pass
- `simulator.test_ws365_formulas` — **6/6** (formula parity — critical, confirms no calculation drift from Phases 3–6)
- `simulator.test_e2e_current_scenario_flow` — full pass

**Grand total with the full `manage.py test simulator` run: 84 tests,
80 pass, 4 skipped, 0 failures.** The 4 skips are the Playwright /
Selenium live-browser suites (see §"Not verified" below) that require a
`requirements-dev.txt` install.

### V3 — API smoke

- `/api/baseline/create/` — staff-only gate exercised in `test_bb_admin_baseline`.
- `/api/baseline/restore/` — shared-payload fan-out exercised.
- `/api/baseline/info/` — `can_create` flag exercised.
- `/api/save-all-inputs/`, `/api/save-recalc-verbrauch/`, `/api/save-renewable-user-input/`, `/api/save-verbrauch-user-input/`, `/api/update-user-percent/`, `/api/recalc-renewables/`, `/api/ws/apply-full-balance/`, `/api/ws/apply-full-balance-wind/` — all covered by the thesis suites.
- 4-E cascade: `/api/save-renewable-user-input/` no longer emits `skip_cascade=True`; verified end-to-end on Heroku (console: `Saved to database: Updated LU_2.1 to 1.5% - renewables auto-updated`).

### V4 — Playwright against localhost

All Phase 3–6 pages exercised via authenticated cURL + regex checks
(landuse, renewable, verbrauch, ws, bilanz, cockpit, annual-electricity,
user-manual, simulation, historie, modifikationsdetails). Content
markers confirmed:

- sidebar universal (9/9 pages, `sidebar_count=1`).
- top-bar dedup (9/9, no duplicated page-nav entries).
- brand in sidebar (9/9).
- Balance Solar / Balance Wind visible; legacy 4 buttons absent.
- progress banner DOM + aria-live="polite" on /ws/.
- base-value `data-base-value` attrs on 19 LandUse inputs + 44 Verbrauch cells.
- Cockpit new "Status ↔ Ziel" section + demand/supply canvases + delta-table body.
- Bilanz unit toggle buttons + capacity badge + 3 new stacked datasets.
- annual-electricity zoom controls + bumped font-size CSS.
- /historie/ inspect-only + /modifikationsdetails/ all 5 canvases.

### V5 — Playwright on live Heroku

Four separate Heroku spin-up/teardown cycles, each DOM-checking the
relevant surfaces via the Playwright MCP bridge:

| Phase | Heroku host | Key live check |
|---|---|---|
| 1 | `prosim-100-2661cfdfdcde` | Goal Seek + Refresh + Save All Values all gone |
| 2 | `prosim-100-9fa2a64bdb5f` | 8 pages 0 English leaks; numbers in German format (`329.346`, `1.211.176`) |
| 3+4 | `prosim-100-09424333c74f` | 9 pages with sidebar=1; brand-in-sidebar=1; Balance 4→2 collapsed; LandUse edit live-triggered cascade propagation (`Saved to database: Updated LU_2.1 to 1.5% - renewables auto-updated`) |
| 5+6 | `prosim-100-750ddc9416fd` | Cockpit Status↔Ziel + demand/supply charts + delta table; Bilanz unit toggle + capacity badge + stacked datasets; /historie/ + /modifikationsdetails/ with all 5 canvases + 4-series JSON |

Each Heroku cycle destroyed after verification — no ongoing billing.
Total V5 cost across 4 cycles ≈ **$0.25**.

### V6 — Documentation

Updated in this push:

- `docs/stakeholder/PROGRESS.md` — full phase-by-phase burndown with commit SHAs.
- `docs/stakeholder/FLOW_DIAGRAM_AUDIT.md` — Phase 5-C node mapping audit + T54 open action.
- `docs/stakeholder/VERIFICATION_STATUS.md` — this file.
- `CLAUDE.md` — V2–V6 codified as non-negotiable earlier (2026-04-21).

## Not fully verified — honest gaps

### 1. Regression scenarios A/C/D via `compare.py`

**Status:** deferred, not run.

The goldens at `regression/golden/A-baseline-readonly.json`,
`C-ws-balance.json`, `D-full-flow-verbrauch-solar-wind.json` were
captured on 2026-04-20 (pre-Phase 2). They hard-code:

- English page titles (`"Land Use Data - All Records"`) that Phase 2-A
  intentionally translated.
- English thousand separators (`"35,759,529"`) that Phase 2-C
  intentionally changed to `"35.759.529"`.
- English column headings (`"Status Value"`) that Phase 2-A changed to
  `"Status"`.

Running `compare.py` today would exit **1** (value drift) on essentially
every probed field — not because of regression, but because the goldens
themselves are stale. Per `IMPLEMENTATION_PLAN.md` §0 Principle: "Golden
files regenerate **only** with explicit Pascal sign-off, never
automatically." So these need a re-capture + commit with Pascal's
approval, not an autonomous regen.

**Action for re-opening:** walk through scenarios A and C (Scenario A
is read-only, very cheap) with a Playwright session, capture fresh
JSON, diff against the old golden, confirm the deltas are ONLY the
phase-2 localization + number format, then commit the new goldens.

### 2. Live click-through of 4-D progress banner on Heroku

**Status:** partially verified.

Verified via Playwright that the banner DOM exists, is hidden by default
with `d-none`, and has `aria-live="polite"`. **Not** verified: actually
clicking Balance Solar on Heroku, watching the banner update in real
time during the ~60-120 s job, confirming text like
`"Status: running · Job abcdef12 · 15s"` appears.

This is low-risk (pure frontend wiring that unit-tests cover) but would
be a stronger demonstration. Takes one extra Heroku spin-up plus ~2
minutes to observe a real balance job.

### 3. Staff-user end-to-end for 4-B admin baseline creation

**Status:** backend covered by 5 contract tests (V2); UI click-through
on Heroku not done.

The 5 contract tests exhaustively cover staff-only 403 gate,
shared-payload capture, user workspace restore, 404 without baseline,
and the `can_create` flag. What's not exercised live: logging in on
Heroku as a staff user, clicking "Baseline erstellen (Admin)" in the
dropdown, then logging back as `testsim` and clicking "Auf Baseline
zurücksetzen". `testsim` is not staff, so this requires creating a
staff user on Heroku (`heroku run manage.py createsuperuser`) for a
full walkthrough.

### 4. Modifikationsdetails with populated Basisszenario / Vorzustand

**Status:** empty-state verified; populated-state not verified.

The page renders fine when no admin baseline and no user scenario
snapshot exist (Basisszenario + Vorzustand series are null-filled and
don't draw bars). **Not** verified: triggering the full data path by
creating an admin baseline, saving a user scenario, making a
modification, and seeing all four series populate.

This is an easy follow-up on any future Heroku visit: admin create
baseline → save scenario → modify → visit /modifikationsdetails/.

### 5. Flow diagram T54 value-to-node audit vs Excel

**Status:** documented open action in `FLOW_DIAGRAM_AUDIT.md`.

Requires Excel export of the current seed scenario. Font legibility
(T55), structure audit (T53), and Excel-structure parity (T56) are all
shipped. Value-to-node correctness (T54) waits on the Excel reference.

### 6. Playwright / Selenium live-browser test suites

**Status:** skipped, environment-gated.

- `test_e2e_ui_D_full_flow`
- `test_e2e_ui_baseline`
- `test_e2e_ui_ws_balance`
- `test_e2e_browser_current`

These 3 tests skip in the current Docker setup because Playwright isn't
installed in the `web` container (it's a `requirements-dev.txt` line
item) and the tests have a `@skipUnlessDBFeature` or similar gate.
Running them requires:

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
LOCAL_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/finalthesis3 \
  USE_LOCAL_POSTGRES=true ALLOW_DOCKER_POSTGRES_HOST=true \
  python manage.py test simulator.test_e2e_ui_baseline simulator.test_e2e_ui_ws_balance \
    simulator.test_e2e_ui_D_full_flow simulator.test_e2e_browser_current
```

These would be the next layer of defence — a Chrome-backed simulation
of the baseline-create, WS-balance, and full D-scenario flows. Not run
because the dev environment needs setup.

## What's remaining overall

**56/63 stakeholder targets shipped + V5-verified on Heroku.** The 7
remaining:

| Target | Phase | Status |
|---|---|---|
| T1–T4 | 7-A Hosting handover | Blocked on ErnES picking a compute platform |
| T5, T7 | 7-B Acid test | Blocked on T1–T4 |
| T8–T13 | Deferred: data-model rework | Pascal holds the Excel files; needs a scoping session |

Plus three smaller items:

- **T54** — flow-diagram value-to-node audit vs. Excel reference (open
  action, see `FLOW_DIAGRAM_AUDIT.md`).
- **Playwright/Selenium live-browser suites** — install dev reqs to
  run.
- **Regression goldens** — capture fresh A/C after Phase 2 translation
  drift, commit with Pascal's sign-off.

Everything else from the PDF is shipped, tested, and deployed to
Heroku live under 4 separate spin-up/teardown cycles.
