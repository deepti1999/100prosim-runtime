# §2.3 Data-Model Audit (revised) — provenance + region, not value import

**Status:** **Phase A SHIPPED 2026-04-23 (T64) + Phase B SHIPPED 2026-04-23 (T65) + Phase C SHIPPED 2026-04-23 (T66)** — all V5-verified on Heroku. §2.3 operationally closed end-to-end (DE + non-DE region proven).
**Date:** 2026-04-23 (revised; v1 from earlier same day preserved in git history at commit `f5c738b` and back).
**Author:** Claude (Opus 4.7) under Pascal's direction.
**Scope:** Stakeholder PDF §2.3 "Datenmodell" (Schmidt-Kanefendt 2026-04-03).
**Purpose:** Re-frame the §2.3 work after the v1 audit got the framing wrong (treated §2.3 as value import; it is a **provenance + region + admin-edit** ask). Decompose §2.3 into atomic stakeholder requirements aligned with the literal text, audit current architecture against each, plan implementation phases that are independently shippable, and end with the decision points that are actually blocking.

---

## 0. What changed since v1

The v1 audit (preserved in git: `git show f5c738b -- docs/stakeholder/DATA_MODEL_IMPORT_AUDIT.md`) framed §2.3 as: "the 420 parameters are hardcoded in seed; we need to import them from D.xlsx, every value editable per-scenario but traceable back to D.xlsx row + URL + comment". Pascal pushed back on three counts:

1. There are **multiple workbooks** (D.xlsx, _S.xlsx, WS.xlsm, AH.xlsm, C.xlsx, MH.xlsx, `_100prosim.xlsm`, plus dev trace logs); v1 only looked at D.
2. The **math is already ported** into our `calculation_engine/` + `simulator/ws365_*` (~3 200 LOC) + 760-row `Formula` table.
3. The **values are already in the DB** (with provenance partially populated); §2.3 is asking us to **add the missing provenance + region + admin-update layer**, not re-import what's already there.

Steps A / B / C of this audit (committed `d2a4c28` / `55cf302` / `58a1b90`) verified Pascal's reading:

- **Step A** (`260403_Section_2.3_literal.md`): the literal PDF text bundles 11 distinct asks (L1–L11). The proposal is "Schnittstelle" (interface) — the implementation mechanism is left open.
- **Step B** (`WORKBOOK_CATALOG.md`): of 9 workbooks in the bundle, only **D.xlsx and _S.xlsx are first-class data substrate**. WS.xlsm is the calculation workbook (already ported). AH / C / MH / launcher / trace logs are out of scope.
- **Step C** (`scripts/audit_s_xlsx_mapping.py` + `scripts/audit_out/s_xlsx_map_*.csv`): mapping our 420 DB rows against `_S.xlsx` (whose sheets are 1:1 with our app pages) yields **78 % HIGH-confidence + 14 % MED + 6 % LABEL_ONLY + 1 % NONE**. The values exist in the DB and align with the stakeholder's view file.

The v1 audit's headline ("Algorithmic mapping from our DB → D.xlsx is NOT clean enough to automate, 35–75 % match") was a side-effect of mapping against the wrong file. Mapping against _S.xlsx (the right file) gives 92.8 % at MED-or-better with no hand curation.

This document fully supersedes v1. The decision record sits in `260403_Section_2.3_decision.md` (Step D); this file is the implementation-facing audit.

---

## 0a. Phase A SHIPPED 2026-04-23 (T64)

Phase A landed on `main` across 9 commits (`bb62a49` … `9da1a22`).

| Deliverable | Status | Evidence |
|---|---|---|
| Schema migration: source_url + notes_assumption + origin on 4 models | ✅ Shipped | `simulator/migrations/0051_phase_a_provenance_fields.py`; 11/11 V2 tests in `test_wb_provenance_schema.py` |
| `manage.py import_excel_provenance D.xlsx --apply` (idempotent, fail-loud, manifest + orphan CSV) | ✅ Shipped | `simulator/management/commands/import_excel_provenance.py`; 13/13 V2 tests in `test_wb_excel_provenance_import.py` |
| Provenance import run on real D.xlsx | ✅ Done | 265 / 420 rows changed (63.1 % overall, **80.5 % of 329 HIGH-confidence** rows). Zero numerical diff (pre/post value-column SHA256 identical across all 4 models). `data/import/d_xlsx.manifest.json` + `data/import/orphan_classification.csv` committed. |
| UI info-icon click popover on /landuse/ /renewable/ /verbrauch/ /gebaeudewarme/ | ✅ Shipped | `simulator/templates/simulator/_provenance_icon.html` partial + popover initializer in `base.html`; 4 templates updated; verbrauch + gebaeudewaerme + renewable views extended to pass provenance fields |
| /gebaeudewarme/ URL wired up | ✅ Shipped | `simulator/urls.py` — view existed but was dead code prior to Phase A |
| User-workspace propagation | ✅ Shipped | `_propagate_to_workspace_rows()` in import command (247 user-workspace rows) + `_clone_landuse_for_user` updated to carry provenance for fresh users (Heroku-verified) |
| V2 unit tests | ✅ 24/24 green | `test_wb_provenance_schema` (11) + `test_wb_excel_provenance_import` (13) |
| V4 Playwright localhost — popovers render on all 4 pages with substantive German content | ✅ Verified | `verification/phase_a/landuse_popover_open.png`, `renewable_popover_open.png`, `verbrauch_popover_open.png`, `gebaeudewarme_popover_open.png` (gitignored per project convention) |
| V5 Playwright Heroku — same 4 pages on `prosim-100-2c767e32f236.herokuapp.com` | ✅ Verified | `verification/phase_a/heroku_*_popover.png`; Jahresstrom diagram regression check (no movement of Track 1 D1–D4c values) `heroku_jahresstrom_no_regression.png` |
| V6 docs | ✅ Done | This section + `REMAINING.md` §2 marked SHIPPED |

What remains for §2.3:

- ~~**Phase B** (Region first-class + Bundesländer import + admin UI) — closes T11 + T12 + T13 + unblocks T54 D4a/D4b.~~ ✅ SHIPPED 2026-04-23 — see §0b below.

The 8 D1–D8 decisions in §9 are all in **LOCKED** state from 2026-04-23 (Pascal approved on the recommendation defaults plus D4 = click popover).

---

## 0b. Phase B SHIPPED 2026-04-23 (T65)

Phase B landed on `main` across 9 commits (`4fc6faf` … `a7174ea`).
Closes SR-004 (Region first-class), SR-011 (admin re-import — partial,
shell-driven for now), SR-012 (multi-region import path), and the
last two T54 backend-data items (D4a / D4b — installed-power constants
become region-scoped).

| Deliverable | Status | Evidence |
|---|---|---|
| Region model + DE seed (code unique, display_name, active, datenmodell_excel_hash, installed_pmax_ely_gw, installed_pmax_rv_gw, created_at) | ✅ Shipped | `simulator/migrations/0052_region_model_and_de_seed.py`; 12/12 V2 tests in `test_wb_region_model.py` |
| region FK on 4 parameter models (PROTECT, default DE) + backfill all 814 dev-DB rows + tightened owner-scoped unique constraints to include region | ✅ Shipped | `simulator/migrations/0053_region_fk_on_parameter_models.py` (AddField nullable → RunPython backfill → AlterField non-null pattern); 14/14 V2 tests in `test_wb_region_fk.py` |
| Workspace per (owner, region) — `region_scope` thread-local + OwnerScopedManager filter + `ensure_user_workspace_data(user, region_code)` + per-region clone helpers | ✅ Shipped | `simulator/region_scope.py`, `simulator/owner_scope.py`, `simulator/workspace_service.py`; 11/11 V2 tests in `test_wb_workspace_region.py` |
| Active-region session middleware — reads `active_region_code` from session, defaults DE, sets thread-local, plumbs region into `ensure_user_workspace_data`; `workspace_signals` reads same on login | ✅ Shipped | `simulator/middleware.py` + `simulator/workspace_signals.py`; 6/6 V2 tests in `test_wb_region_middleware.py` |
| Region switcher dropdown in nav — POST endpoint validates against `Region.active=True`, persists to session, redirects to referer; context processor exposes `active_regions` + `active_region_code` to all templates | ✅ Shipped | `simulator/views_region.py`, `simulator/context_processors.py`, `simulator/urls.py`, `simulator/templates/simulator/base.html`; 12/12 V2 tests in `test_wb_region_switcher.py` |
| `manage.py import_excel_provenance --region=<code>` + per-region paths (data/import/<region>/D.xlsx + manifest + orphan CSV); base-row + workspace-propagation filter by region | ✅ Shipped | `simulator/management/commands/import_excel_provenance.py`; 6/6 V2 tests in `test_wb_excel_import_region.py`; existing 13/13 Phase A import tests re-pointed at `data/import/DE/` |
| T54 D4a/D4b — Pmax-Ely (194 GW) + Pmax-RV (261 GW) sourced from `Region.installed_pmax_*`; `compute_ws_diagram_reference` returns them; template uses `id="pmax_ely_value"` + `id="pmax_rv_value"` with JS overwrite at DOMContentLoaded (Track 1 D1-D4c convention) | ✅ Shipped | `simulator/signals.py`, `simulator/page_renewable.py`, `simulator/templates/simulator/annual_electricity.html`; 8/11 V2 tests in `test_wb_pmax_dynamic.py` (3 skip — compute fn needs Formula rows test DB lacks; smoke verified on dev DB and Heroku) |
| Regression fix: scenario serializer + seed Region row | ✅ Shipped | `simulator/baseline_api.py` excludes `region` FK from per-row serialized payload (was 500-ing on `/api/scenario/create/`); `seed/sqlite_seed.json` gains a `simulator.region` row at index 0 so TransactionTestCase tests re-seed DE on each test setup |
| V2 unit tests | ✅ 71/71 new green + 11 existing updated | Phase B added 9 test modules (test_wb_region_*, test_wb_workspace_region, test_wb_pmax_dynamic, test_wb_excel_import_region); existing test_wb_queue_jobs_middleware + test_wb_excel_provenance_import each had a single intentional spec-drift assertion update (region_code='DE' kwarg + per-region manifest path) |
| Full thesis test suite | ✅ 183/183 green | (7 unrelated skips for Postgres-only e2e on SQLite) |
| V5 Playwright Heroku — region dropdown + DE active + D4a/D4b render correctly + popovers + parameter pages | ✅ Verified | `verification/phase_b/01_simulation_with_region_dropdown.png`, `02_annual_electricity_d4a_d4b.png`, `03_landuse_with_dropdown_and_popovers.png`, `04_region_dropdown_open.png`. Live URL was `prosim-100-7b2fe54360e6.herokuapp.com` (now destroyed, billing stopped). DOM-confirmed values: pmax_ely_value="194 GW", pmax_rv_value="261 GW (elekt.)", region_dropdown_label="DE" |
| Zero numerical drift on the existing DE region | ✅ Verified | All 420 base rows + per-user workspace rows backfilled to DE via 0053 RunPython; re-running `import_excel_provenance --apply` reports 0 changed (idempotent — same 178 d_xlsx + 87 derived = 265 total = identical to Phase A baseline) |
| V6 docs | ✅ Done | This §0b section + REMAINING.md headline 54→57/63 + T54 D4a/D4b marked SHIPPED in REMAINING.md §3 |

What remains for §2.3:

- ~~Phase 2 follow-ups documented as TODOs in code~~ — **all 4 closed by Phase C** (T66) — see §0c below.

---

## 0c. Phase C SHIPPED 2026-04-23 (T66)

Pascal opened Phase C in response to the §2.3 region-scope check
(`260403_Section_2.3_region_scope_check.md`) that flagged Phase B
as architecturally-only complete: the literal §2.3.2 ¶2 ask
"Erstellung und Zugriff auf Datenmodelle verschiedener Alternativ-
Regionen wird nicht unterstützt" + "regionsspezifische Anwendung …
nicht verfügbar" required at least one non-DE region to actually
work end-to-end, plus the 4 deferred TODOs to flip.

Phase C landed on `main` across 8 commits (`e23653b` … this commit).

| Deliverable | Status | Evidence |
|---|---|---|
| GebaeudewaermeData unique = (region, code) — drop global unique=True | ✅ Shipped `e23653b` | Migration 0054; 4/4 V2 tests in `test_wb_geb_region_uniq.py` |
| Scenario / baseline snapshot payload carries top-level `region_code` | ✅ Shipped `ae2809f` | `simulator/baseline_api.py` updated; legacy snapshots without region_code default DE for back-compat; 4/4 V2 tests in `test_wb_snapshot_region.py` |
| BalanceJob.payload.region_code + worker `region_scope` wrap | ✅ Shipped `cb746eb` | All 4 ws_api_apply_* endpoints stamp region from session via `_stamp_region(payload, request)`; `run_balance_job` reads payload + wraps dispatch in `region_scope(payload_region_code)` AROUND existing `owner_scope`; 4/4 V2 tests in `test_wb_balance_region_routing.py` |
| WSData per-(owner, region) — region FK + scoped clone helper | ✅ Shipped `fb5f2c8` | Migration 0055 (AddField nullable → backfill 736 rows → AlterField non-null); `_clone_simple_model_no_region` removed; 8/8 V2 tests in `test_wb_wsdata_region.py`. Decision rationale in commit message (rejected per-user-only and per-region-only; chose per-(owner, region) for symmetry with parameter models + cross-process cache coherency). |
| Row-creating import mode — `import_excel_provenance` on empty region clones DE structure + overlays new region's xlsx W values | ✅ Shipped `e7b8c19` | `_create_region_rows_from_de_template` helper in `simulator/management/commands/import_excel_provenance.py`; LandUse parent FK re-linked by code post-bulk_create; failure modes preserved; 3/3 V2 tests in `test_wb_import_create_region.py` (CREATE mode populates new region, DE rows untouched, UPDATE mode for DE preserved) |
| Cross-region isolation full smoke (4 models in one test) | ✅ Shipped `6dfc2ed` | `FullCrossRegionIsolationSmokeTests` in `test_wb_import_create_region.py`; GebaeudewaermeData switched to `OwnerScopedManager` so region thread-local actually filters its queries |
| Cosmetic migration 0056 — index rename | ✅ Shipped `51f50cd` | Auto-generated by Django; cosmetic only |
| Heroku V5 helper — clones DE rows × 1.05 into TEST region | ✅ Shipped `bbff38c` + `373e94c` | `scripts/heroku_seed_test_region.py` (throwaway; not used by app or tests). Needed because D.xlsx is gitignored so `import_excel_provenance` cannot run on Heroku without the source file. |
| V2 unit tests | ✅ 27/27 new green | Phase C added 5 test modules (test_wb_geb_region_uniq, test_wb_snapshot_region, test_wb_balance_region_routing, test_wb_wsdata_region, test_wb_import_create_region). 1 spec drift in test_wb_queue_jobs_middleware (region_code='DE' kwarg in ensure_workspace assertion). |
| Full thesis test suite | ✅ 207/207 green | (7 unrelated SQLite skips for Postgres-only e2e tests) |
| V5 Heroku — TEST region cloned via shell, switched in UI, values visibly differ from DE, switching back yields zero drift | ✅ Verified | `verification/phase_c/01_DE_jahresstrom_baseline.png`, `02_TEST_landuse.png`, `03_TEST_jahresstrom.png`, `04_DE_jahresstrom_after_switchback.png`. Live URL was `prosim-100-ce34bbba8419.herokuapp.com` (now destroyed; billing stopped). DOM-confirmed: TEST `pmax_ely_value="200 GW"` (TEST region constant), `pmax_rv_value="270 GW (elekt.)"`; DE round-trip values byte-identical to baseline (pv=1.211.176, wind=706.236, pmax_ely=194 GW, pmax_rv=261 GW, abgleichdifferenz=157). |
| Zero numerical drift on the existing DE region | ✅ Verified | DE Jahresstrom values pre/post Phase C identical via Heroku DOM check. Test DB: 207/207 green. Migrations preserve all DE row values; no value-write code path was touched. |

What §2.3 still needs (post-Phase-C):

- Per-region target / ziel column ingest. Phase C row-create
  reads only column W (status) from the new region's xlsx; target
  / ziel mirror status on row create. When stakeholders deliver
  Bundesländer Excel files with their own target columns, extend
  the create-mode value extraction. Until then, regions arrive
  with `target_* = status_*` which is acceptable for visual proof
  but means per-region target editing requires an admin update
  pass.
- Real Bundesländer data ingest. Pascal/Schmidt-Kanefendt drop
  `BB.xlsx` (etc.) at `data/import/BB/D.xlsx`, run
  `Region.objects.create(code='BB', display_name='Brandenburg',
  active=True, installed_pmax_ely_gw=..., installed_pmax_rv_gw=...)`
  in shell, then `python manage.py import_excel_provenance
  --region=BB --apply`. Region appears in dropdown immediately;
  switching surfaces BB data; provenance overlay applies; balance,
  scenarios, snapshots all region-isolated. **End-to-end proven on
  Heroku V5 with a synthetic TEST region.**
- Admin GUI for the import flow. Currently CLI-only (`manage.py
  shell` + `manage.py import_excel_provenance`). The literal §2.3
  ask "spezielle Admin-Rechte sind nicht erforderlich" maps to a
  /admin/data-import/ form; deferred to Phase D when there's
  actually a non-developer admin in the loop.

---

## 1. Executive summary

**Stakeholder ask (§2.3):** make every parameter's source URL and assumption note visible to users + admins; support per-region data models; let admins update the base scenario from an updated Excel file without a code change. (Literal asks L1–L11; see `260403_Section_2.3_literal.md`.)

**Current state:** the 420 parameters across LandUse / RenewableData / VerbrauchData / GebaeudewaermeData are fully populated, with values matching `_S.xlsx` (the scenario master) at 78 % HIGH and 92.8 % MED-or-better. **Provenance is the gap** — 0 / 420 rows have an assumption note, source URL coverage is partial (LandUse `quelle` codes only), and there is no `Region` model or admin parameter-update UI.

**Recommendation:** split §2.3 into a **2-phase incremental ship** (Phase A: provenance + tooltip + admin import for DE; Phase B: region first-class + Bundesländer-ready import). Each phase independently shippable, V2–V6 verifiable, and additive — does not touch the 51 shipped targets' numerical behaviour because Phase A is provenance-only and Phase B touches new (per-region) rows only.

**Hard rule this audit enforces:** no cell / code / label rename (CLAUDE.md "Stakeholder requirements" #1). Every `LU_*`, `9.3.*`, Verbrauch code, sector name, WS365 field name, and `Formula.name` stays frozen. Import only adds provenance metadata + region tagging; it does not rename anything. (Maps to SR-007 below.)

---

## 2. §2.3 decomposed into atomic stakeholder requirements (revised)

Each SR maps to one or more of the 11 literal asks in `260403_Section_2.3_literal.md` (L1–L11). The numbering is preserved from v1 but several requirements have been re-defined to match what §2.3 actually says.

### SR-001 — §2.3 is a provenance + region + admin-edit ask, not a value import (revised)
> §2.3 asks for an interface (Schnittstelle) that makes Excel data-model files usable in lieu of the integrated data model. Implementation mechanism is left open by the PDF (no requirement for live binding). The substantive asks are: source visibility, assumption visibility, region modularity, admin update capability — not bulk value re-import.

**Maps to:** L1, L2.

**Acceptance:** the implementation work is scoped per SR-002 … SR-012; SR-001 is the framing constraint.

### SR-002 — Each parameter carries its data source URL (was SR-002, refined)
> Each parameter row MUST carry the source URL from `D.xlsx!9.Quellen` (86 hyperlinks today) when one exists for that row.

**Maps to:** L3.

**Acceptance:** new column `source_url` (string, nullable) on the 4 parameter models; populated by the import command for every row whose label is matched in D.xlsx and whose source-cell carries a hyperlink. Coverage target: ≥ 80 % of HIGH-confidence rows.

### SR-003 — Each parameter carries its assumption note (was SR-003, refined)
> Each parameter row MUST carry the assumption text from the corresponding `D.xlsx!1.` cell comment (747 comments today).

**Maps to:** L4.

**Acceptance:** new column `notes_assumption` (text, nullable) on the 4 parameter models; populated by the import command for every row whose label is matched and whose D.xlsx counterpart has a `hsk: |` comment. Coverage target: ≥ 80 % of HIGH-confidence rows.

### SR-004 — Region is a first-class concept (NEW)
> The data model MUST support multiple regions (Germany + Bundesländer) via a `Region` model. The active region is selectable; per-region rows are isolated; default region is `DE` so existing single-region behaviour is preserved.

**Maps to:** L7, L9, L10, L11.

**Acceptance:** `Region` model with `(code, display_name, active, datenmodell_excel_hash)`. The 4 parameter models gain a region FK. Default fixture seeds one row `DE`. UI gets a region switcher (Phase B).

### SR-005 — Per-user / per-scenario overrides are preserved (unchanged)
> The existing per-user workspace override behaviour MUST NOT break. If a user changed `LU_2.1` in their workspace, their override still wins over the imported default; the import supplies the base, not the overlay.

**Maps to:** constraint (no literal ask; CLAUDE.md invariant).

**Acceptance:** `workspace_service.ensure_user_workspace_data()` behaviour unchanged; regression scenarios A / C / D pass with `compare.py` exit 0.

### SR-006 — Import is idempotent and diff-on-rerun (was SR-006, refined)
> Re-running the import against an unchanged file MUST be a no-op. Running it against a changed file MUST emit a per-row diff before any write, gated behind `--apply`.

**Maps to:** L6 (admin update workflow).

**Acceptance:** `python manage.py import_excel_provenance D.xlsx` on an unchanged file emits "0 changed"; on a changed file emits diff + requires explicit `--apply`. Test: `test_wb_excel_import_idempotent`.

### SR-007 — Import never renames any cell / code / label (unchanged — hard rule)
> All codes (`LU_*`, `9.3.*`, sector names, WS365 field names, `Formula` rows) stay frozen. The import ADDS provenance / region metadata; it MUST NOT rename anything.

**Maps to:** CLAUDE.md "Stakeholder requirements" #1; not a literal §2.3 ask but a hard project invariant.

**Acceptance:** `test_wb_code_freeze.py` (new) asserts no rename happens on import; the import command rejects any operation that would touch a `code` field.

### SR-008 — Import does not break the 51 shipped targets (unchanged — hard rule)
> All 51 shipped + Heroku-verified targets stay green. Golden regression scenarios A / C / D pass. All `test_bb_*` / `test_wb_*` / `test_e2e_*` modules pass.

**Maps to:** CLAUDE.md "Per-item verification" rule; not a literal §2.3 ask.

**Acceptance:** full thesis test suite green pre-import and post-import on the same seed. A / C / D goldens unchanged unless intentionally re-captured with Pascal sign-off.

### SR-009 — Provenance is visible in the UI (unchanged)
> A user viewing a parameter on `/landuse/`, `/renewable/`, `/verbrauch/`, `/gebaeudewarme/` MUST be able to see its source URL and assumption note from the row.

**Maps to:** L5 (epistemic engagement) + L8 (admin can update without code).

**Acceptance:** Playwright test hovers / clicks an info-icon on a row and asserts the popover contains the source URL and assumption text.

### SR-010 — Orphan parameters exposed via `origin` enum (unchanged)
> Parameters we have that D.xlsx does not (UI-only fields, derived outputs, scenario-policy assumptions, deeper-hierarchy splits) MUST be flagged as `origin='internal'` with a documented rationale, not silently treated as missing.

**Maps to:** Step C evidence (5 NONE + 25 LABEL_ONLY rows total are unmatched at value level).

**Acceptance:** `origin` enum on each parameter model with values `{ d_xlsx, derived, internal }`; orphan-classification report shipped with the import command; `origin='orphan'` count = 0 in production.

### SR-011 — Admin can update the base scenario without code changes (NEW)
> An admin (Django staff user) MUST be able to update the base scenario by uploading an updated `D.xlsx` (or per-region equivalent), reviewing the diff, and applying it — without a code change or redeploy.

**Maps to:** L6, L8.

**Acceptance:** admin form at `/admin/data-import/` accepts an `.xlsx` upload, runs `manage.py import_excel_*` in a guarded mode, presents the diff in the browser, lets the admin click "Apply" or "Cancel". Test: `test_e2e_ui_admin_data_import` (new).

### SR-012 — Multi-region import accepts per-region `.xlsx` files (NEW)
> The import command MUST accept either D.xlsx (Germany) or any per-region equivalent that follows the D.xlsx shape (e.g. `BB.xlsx`, `NW.xlsx`). Per-region rows are isolated by FK to the `Region` model; switching the active region in the UI changes the read scope.

**Maps to:** L9, L10, L11.

**Acceptance:** `manage.py import_excel_datenmodell <region_code> <file.xlsx>` populates per-region rows; UI region switcher shows all regions where `Region.active=True`. Test: `test_bb_region_switcher`.

---

## 3. Current architecture audit

### 3.1 Parameter-bearing models

(Unchanged from v1; numbers re-counted directly from `seed/sqlite_seed.json`.)

| Model                | Table                         | Rows | Key cols                                            | Source cols today          |
|----------------------|-------------------------------|-----:|-----------------------------------------------------|----------------------------|
| `LandUse`            | `simulator_landuse`           |   20 | `code`, `name`, `status_ha`, `target_ha`            | `quelle` (D-codes)         |
| `RenewableData`      | `simulator_renewabledata`     |  223 | `code`, `category`, `subcategory`, `status_value`, `target_value`, `unit` | `source` (CSV filename), `description` |
| `VerbrauchData`      | `simulator_verbrauchdata`     |  151 | `code`, `category`, `status`, `ziel`, `unit`        | (none — `notes` empty)     |
| `GebaeudewaermeData` | `simulator_gebaeudewaermedata`|   26 | `code`, `category`, `status`, `ziel`, `unit`        | (none — `notes` empty)     |
| **Total**            |                               |  **420** |                                                 |                            |

Additional structural models that will be touched: `Formula` (760 rows — frozen text), `WSData` (365-day time series — derived). Per-user workspace overlay models — out of scope per SR-005. New: `Region` (Phase B, SR-004).

### 3.2 Seed state — what provenance is actually present

Re-counted from `seed/sqlite_seed.json` (sample by Python script, 2026-04-23):

- `source` / `quelle` non-null: **74 / 420 (≈ 18 %)** — mostly LandUse `quelle="D.1.<n>"` (a D-style code, not a row number); RenewableData `source="solar_energy.csv"` etc.; the value content is a placeholder, not a hyperlink.
- `notes` non-null: **0 / 420 (0 %)** — no assumption text anywhere.
- `description` non-null: **103 / 420 (≈ 25 %)** — present on RenewableData; contains category narrative, not source citations.

Conclusion: the schema partially supports provenance (existing columns present) but the seed has not been populated with the actual D.xlsx content. **This is precisely what §2.3 asks us to fix** (SR-002, SR-003).

### 3.3 Parameter consumers (unchanged from v1)

`simulator/*.py` files that import or query parameter models: **28 files** (grep-counted). Heaviest consumers:

- `recalc_service.py`, `workspace_service.py` — persistence orchestration
- `page_landuse.py`, `page_renewable.py`, `views_pages.py` — rendering
- `balance_jobs.py`, `ws_365_service.py` — WS balance flow
- `goal_seek.py`, `percentage_rebalancer.py` — numerical solvers
- 15 test modules

A non-breaking additive column (e.g. `source_url`, `notes_assumption`, `origin`, region FK with default) touches **zero of these at read time** — the safe corridor.

### 3.4 Cache & signal surface (unchanged from v1)

Four process-local caches invalidated at `BalanceJob` entry today:

- `recalc_cache._cache`
- `_AUTO_TOKENS_CACHE`, `_LOOKUPS_CACHE` (in `formula_service.py`)
- `_WS365_COMPUTE_CACHE` (in `ws365_orchestrator.py`)

The import is a management command — runs outside a request / worker process. Cache coherency is not an issue at import time. RISK-04 still applies if an import races with `ensure_user_workspace_data()` for a live user; mitigation is a maintenance-mode flag.

### 3.5 Test surface (unchanged)

15 of 19 `simulator/test_*.py` modules query at least one parameter model. Goldens A / C / D probe parameter values downstream. `test_ws365_formulas.py` pins 760 formula outputs — unaffected by provenance changes.

---

## 4. Workbook substrate (replaces v1 §4 single-file deep-map)

Detailed coverage in `WORKBOOK_CATALOG.md`. The §2.3-relevant facts:

### 4.1 D.xlsx — primary substrate

- 17 sheets, 2.93 MB, file header `D. 250517.1733 hsk`.
- Sheet `1.` (2 133 × 157) — the **monolithic per-parameter dump**, carries all 747 cell comments (assumption text). Source URL hyperlinks count = 0 here.
- Sheet `9.Quellen` (264 × 33) — **86 hyperlinks** to AGEB, BMUV, BMEL, Ariadne, DLR, BfEE, etc. This is the canonical sources list.
- Sheet `O_` (211 × 16) — output mirror; the machine-readable extract that _S.xlsx and other workbooks consume via external link `[4]O_!*`.
- Sheet `I_Region` (199 × 19) — region-specific definitions (already structured for region split).
- Sheet `I_Basisdaten` (192 × 15) — installed capacities, areas, base data per region. **D4a (194 GW) and D4b (261 GW)** from the Jahresstrom diagram likely live here.

### 4.2 _S.xlsx — scenario master, sheets 1:1 with our app pages

- 17 sheets, 0.50 MB, file header `_S. 250517.1803 hsk`.
- Sheet names match our app pages exactly: `1. Flächen`, `2. Erneuerbare`, `3. Bedarfsniveau`, `4. Verbrauch`, `5. Bilanz`, `6. Fossile`, `7. Verbrauch Status`, `8. Kennzahlen`.
- Per-sheet column convention (verified):
  - col E = parameter label (German text)
  - col L (or col I in `1. Flächen`) = STATUS value
  - col M (or col L in `1. Flächen`) = ZIEL value
- Cells are mostly INDIRECT formulas resolving via the internal `I_` sheet to D.xlsx `O_` (the `[4]O_!*` external link).
- External link map decoded: `[1]=C.xlsx`, `[2]=WS.xlsm`, `[3]=BS.xlsx (NOT in bundle)`, `[4]=D.xlsx`.
- **§2.3 status: this is the operational view substrate.** Step C maps our DB rows to _S sheets at 78 % HIGH confidence; Phase A label-matching against D.xlsx for source/assumption pull uses _S as the disambiguating index.

### 4.3 BS.xlsx — Bedarfsstatus (referenced but missing from bundle)

- _S.xlsx sheet `7. Verbrauch Status` and `8. Kennzahlen` reference `[3]BS.xlsx` heavily (302 + 366 external-ref formulas).
- BS.xlsx is not in Pascal's local copy. For Phase A this means: rows derived from BS-only refs cannot be value-validated against the substrate. They will be classified `origin='internal'` if their _S row has no D.xlsx-derived backup, or `origin='derived'` if a parent D.xlsx row exists.
- Implication: the Phase A import command should not fail loud on a BS-derived row missing from D; it should classify and continue.

### 4.4 What stays out of scope

- `WS.xlsm` — calculation workbook, already ported to `calculation_engine/`. Useful only as a formula-reference oracle (as Track 1 used it). Not imported.
- `AH.xlsm` — Auswertungs-Historie, not Datenmodell. Out.
- `C.xlsx`, `MH.xlsx`, `_100prosim.xlsm` — config / stub / launcher. Out.
- `trace2.xlsx`, `tracelog.xlsx` — developer artefacts. Out.

(See `WORKBOOK_CATALOG.md` for per-file detail.)

---

## 5. Mapping evidence (replaces v1 §5)

Source: `scripts/audit_s_xlsx_mapping.py` + `scripts/audit_out/s_xlsx_map_*.csv` + `s_xlsx_map_summary.json` (Step C, committed `58a1b90`).

### 5.1 Coverage per model — DB rows mapped to _S.xlsx

| Model              | Rows | HIGH (label + status + ziel) | MED (one of) | LABEL_ONLY | NONE |
|--------------------|-----:|-----------------------------:|-------------:|-----------:|-----:|
| LandUse            |   20 |                  18 (90 %)  |       2      |       0    |   0 |
| RenewableData      |  223 |                 157 (70 %)  |      40      |      21    |   5 |
| VerbrauchData      |  151 |                 129 (85 %)  |      18      |       4    |   0 |
| GebaeudewaermeData |   26 |                  25 (96 %)  |       1      |       0    |   0 |
| **Total**          |  **420** |             **329 (78.3 %)** |     **61**  |    **25**  |  **5** |

Comparison vs v1 audit's D.xlsx-only mapping:

| Bucket     | v1 (D.xlsx only) | this audit (_S.xlsx) |
|------------|-----------------:|---------------------:|
| HIGH       |             19 % |               78.3 % |
| MED        |             22 % |               14.5 % |
| (effective coverage) |    41 %    |               92.8 % |

The 4× improvement in HIGH coverage comes entirely from picking the right substrate (Step B catalog identified _S as app-page-shaped; v1 missed it).

### 5.2 What the LABEL_ONLY + NONE buckets are

- **21 RenewableData LABEL_ONLY:** mostly category headers (`Solarenergie`, `Solarthermie`, `Solarstrom`, `Onshore-Windstrom`, `Laufwasser`, `Energieholz`, etc.) — rows that exist in our DB as parents in the hierarchy but carry no numeric value (their value is the sum of children).
- **4 VerbrauchData LABEL_ONLY:** `Mobile Anwendungen (MA)`, `Grundstoff-Synthetisierung`, plus 2 `Alternativ zur Verbrennungsmotoren` rows. Aggregation rows.
- **5 RenewableData NONE:** deeper-hierarchy rows (`10.4.3 davon Strom`, `10.5 Prozesswärme`, `10.6.2 davon Strom`, `7.1.4 Biogene Kraftstoffe (Wärme)`, `5 (empty label)`) where _S.xlsx has a different scenario value or doesn't split that deep.

**Implication for SR-010 origin classification:** all 30 unmatched rows fit naturally into `origin='internal'` (category headers and deeper splits ours-only). Pascal/stakeholder do not need to extend D.xlsx; the import tool just records why we don't have a counterpart.

### 5.3 Provenance chain (D substrate → _S view → DB row)

Verified on Step C:

```
D.xlsx O_  (output mirror)
   ↑ external ref [4]O_!<col><row>
_S.xlsx I_ (internal substrate sheet)
   ↑ INDIRECT($AC$1 & AE$1 & $AC<row>)  where $AC$1='I_!', AE$1='L', $AC<row>=row index
_S.xlsx <app-page> (e.g. '2. Erneuerbare')
   ↑ "=AE<row>" or "=AK<row>" helper column
DB row (matched by label + value, status + ziel)
```

For source URL + assumption note, the chain is shorter:

```
D.xlsx 9.Quellen (86 hyperlinks)
   ↑ key by '9.<n>' code referenced in D.xlsx 1. cell comments
D.xlsx 1.  (per-parameter dump, 747 'hsk: |' comments)
   ↑ row label match against our DB labels (Step C s_xlsx_map evidence)
DB row
```

The Phase A import command walks the second chain to populate `source_url` + `notes_assumption`.

---

## 6. Impact on the 51 shipped targets

(v1 numbers were 50/63 + 1 added since; current count is 51/63 + 12 outstanding per `REMAINING.md`.)

### 6.1 Per-phase risk matrix (revised)

| Phase           | Targets | Parameter sensitivity        | Risk if Phase A or B runs |
|-----------------|--------:|------------------------------|---------------------------|
| Phase 1 (UI)    |   T1–T12 | Low — UI shell only         | Cosmetic only             |
| Phase 2 (l10n)  |  T13–T36 | Low — translation/format    | Cosmetic                  |
| Phase 3 (menu)  |  T37–T42 | Low                         | Cosmetic                  |
| Phase 4 (cockpit)| T14–T28 | **Medium** — reads parameters; provenance is purely additive so behaviour unchanged | **Phase A: zero risk.** Phase B (region) doesn't touch existing DE rows. |
| Phase 5 (charts)| T43–T60 | **Medium** — same           | Same as Phase 4           |
| Phase 6 (history+detail)| T48–T63 | Low                | Same                      |
| T54 D1–D4c      |       4 | **Medium** — D3 % / D4c uses D-derived values | **Phase A: zero risk** (provenance only). **Phase B: zero risk for DE.** D4a/D4b (pending) get unblocked when `Region.installed_pmax_*` lands. |

### 6.2 Specific targets at risk after Phase A or Phase B

- **T25 auto-cascade:** Phase A doesn't change values, so cascade outputs don't move. Scenario C fingerprint stable.
- **T37 Gebäudewärme Bilanz / T41 Verbrauch Bilanz:** same as T25 — Phase A is provenance-only.
- **T49 / T50 Jahresstrom diagram (Track 1):** same — values held constant by Phase A.
- **D4a / D4b (currently hardcoded 194 GW / 261 GW):** unblocked when Phase B Region model adds installed-power fields. This is a positive impact (closes 2 of the 12 outstanding T54 sub-items).

### 6.3 Safe corridor

**Phase A is essentially zero-risk for the 51 shipped targets** because it adds metadata columns and populates them; no value column changes. **Phase B is low-risk for DE** because new region rows ship with the new region; existing DE rows stay put (the import command refuses to overwrite an existing region row unless `--apply` is passed AND the diff is reviewed).

---

## 7. Risk register (10 risks, revised severities)

The 10 v1 risks are preserved; severities re-evaluated against the corrected (provenance + region) framing.

| ID      | Risk                                                                             | v1 sev | Revised sev | Mitigation |
|---------|----------------------------------------------------------------------------------|------:|--------:|------------|
| RISK-01 | An import operation drifts a scenario golden                                     |  H/H  |   **L/L**   | Phase A is provenance-only; Phase B touches new-region rows only. DE re-sync (B4 in decision doc) is opt-in admin operation gated on `--apply` + diff review. |
| RISK-02 | Ambiguous one-to-many label mappings auto-picked wrong                           |  H/H  |   **M/M**   | Step C s_xlsx_map shows 78 % HIGH; only the 22 % MED-or-below need hand review (~30 min for Pascal); LOW classified as `origin='internal'` automatically. |
| RISK-03 | A code / cell / label gets renamed during import (violates CLAUDE.md contract)   | C/L  |   **C/L**   | Linter test `test_wb_code_freeze`; import command rejects any operation that would touch a `code` field. SR-007 enforces. |
| RISK-04 | Import collides with `ensure_user_workspace_data()` for a live user               |  M/M  |   **M/M**   | Maintenance-mode flag (`MAINTENANCE_MODE=1` env) blocks per-user workspace fires while the import runs; documented runbook for staging vs live. |
| RISK-05 | Per-user overrides silently overwritten by base row re-import                    |  C/L  |   **C/L**   | SR-005: import touches only `owner=NULL` base rows; per-user workspace tables (`owner=<user>`) are read-only to the import. Test `test_bb_user_override_preserved`. |
| RISK-06 | D.xlsx column layout changes between stakeholder revisions                       |  M/M  |   **M/M**   | Pinned manifest at `data/import/d_xlsx.manifest.json` records column layout fingerprint; import asserts header match; fails loud on drift. |
| RISK-07 | Orphan parameters mis-classified                                                 |  L/L  |   **L/L**   | SR-010 explicit `origin` enum (`d_xlsx` / `derived` / `internal`); orphan-classification report shipped with import; review report once per import. |
| RISK-08 | Idempotency broken — second import run produces a diff                           |  M/M  |   **M/M**   | Content-hash per row; skip unchanged; test `test_wb_excel_import_idempotent`. SR-006 enforces. |
| RISK-09 | Track-1 Jahresstrom values move after import                                     |  M/M  |   **L/L**   | Phase A provenance-only — no movement. Phase B for DE only touches new-region rows. D4a / D4b will move (positive: they become correct), goldens re-captured deliberately at that moment. |
| RISK-10 | Provenance column names collide with stakeholder-frozen `source` / `quelle`       |  L/M  |   **L/L**   | New columns are `source_url`, `notes_assumption`, `origin` — all clearly additive; existing `source` / `quelle` / `notes` keep their semantics. SR-007 protects names. |

**Net:** the highest-impact risk (RISK-01) drops from H/H to L/L because the corrected framing avoids bulk value re-import. RISK-09 drops similarly. Other risks essentially unchanged.

---

## 8. Verification / validation plan (V2–V6 per phase, revised)

CLAUDE.md V2–V6 ritual applied to each phase. The three-phase v1 plan
(A schema-only, B value sync, C overrides, D UI provenance) collapses to
**two phases** in the corrected framing; v1's Phase D (UI provenance) is
folded into Phase A; v1's Phase B (value sync) is replaced by the import
command (idempotent, opt-in). Phase C from v1 (override wiring) is now
satisfied by SR-005 — no new code needed.

### Phase A — Provenance + tooltip + DE admin import

- **V2 tests:**
  - `test_wb_parameter_models_schema` — asserts `source_url`, `notes_assumption`, `origin` columns exist + nullable.
  - `test_wb_excel_import_idempotent` — second run = no-op.
  - `test_wb_excel_import_no_rename` — refuses any code-field change.
  - `test_wb_origin_classification` — every row gets a non-null `origin` value.
  - `test_bb_provenance_in_api` — `/landuse/`, `/renewable/`, `/verbrauch/`, `/gebaeudewarme/` JSON includes `source_url` + `notes_assumption` when present.
  - `test_bb_user_override_preserved` — provenance import doesn't touch a user's workspace row.
- **V3 API smoke:** all 4 parameter pages return 200; JSON shape gains 3 nullable fields; existing fields untouched.
- **V4 Playwright localhost:** scenarios A / C / D pass unchanged. New `E-provenance-tooltip` scenario asserts info-icon click + popover content on each parameter page.
- **V5 Playwright Heroku:** `bash scripts/heroku_up.sh` → run E-provenance-tooltip + A/C/D → screenshot tooltip → `heroku_down.sh`. Cost ~$0.10.
- **V6 docs:** this audit gets a "Phase A SHIPPED" marker; `REMAINING.md` §2 rewritten; per-phase change log appended.

### Phase B — Region first-class + Bundesländer-ready import + D4a/D4b unblocked

- **V2 tests:**
  - `test_wb_region_model_schema` — `Region` table + parameter FK present.
  - `test_bb_region_isolation` — DE rows and a sample BB region row don't bleed into each other.
  - `test_bb_region_switcher_persistence` — region selection persists across reloads.
  - `test_bb_d4a_d4b_dynamic` — installed-power fields read from `Region`, not hardcoded.
  - `test_e2e_ui_admin_data_import` — admin upload form accepts a sample .xlsx, presents diff, applies on confirm.
- **V3 API smoke:** `/admin/data-import/` returns 200 for staff; non-staff get 403.
- **V4 Playwright localhost:** A / C / D scenarios pass for DE; new scenario `F-region-switch` validates the region switcher.
- **V5 Playwright Heroku:** spin up, do the region switch + D4a/D4b dynamic check + admin import + tear down.
- **V6 docs:** this audit gets "Phase B SHIPPED"; `REMAINING.md` §3 (T54 D4a/D4b) closes; `HARDCODED_VALUES_TRACE.md` §6 D4a/D4b row marked SHIPPED.

### Gate between phases

Pascal explicitly signs off before Phase B opens a PR. No phase starts while the previous one has red tests or ungraded golden drift. V5 Heroku batched per phase (one cycle each, ~$0.20 total).

---

## 9. Decision points (D1–D8) — LOCKED 2026-04-23 by Pascal

Status: **APPROVED.** Pascal: *"Approve D1–D8 as recommended, D4 = click popover. Open Phase A."*

These are the binding answers. Phase A implementation uses these without further re-litigation. To override later, edit this section + bump the migration / refactor accordingly.

| # | Question | LOCKED answer | Why |
|---|---|---|---|
| **D1** | Provenance schema — extend existing `source` / `quelle` / `notes` OR add new columns? | **Add new** `source_url` + `notes_assumption` + `origin`. Existing `quelle` / `source` / `notes` retain their current semantics. | Existing columns have incompatible content (`LandUse.quelle="D.1.<n>"` is a paragraph code, not a URL). Mixing semantics on the same column would corrupt audit history. |
| **D2** | Region model — first-class table OR settings constant? | **First-class table** `(code, display_name, active, datenmodell_excel_hash)`. Phase A still ships single-region (Germany implicit); the table lands in Phase B. | SR-004 + SR-012 require multi-region semantics; ~20-LOC migration cost; avoids rewrite when ErnES sends `BB.xlsx`. |
| **D3** | Import command behaviour on missing / malformed Excel? | **Fail loud, no silent fallback.** Refuse to write if file missing, hash-mismatch, or sheet schema unrecognised. | RISK-06 mitigation + CLAUDE.md "investigate root causes, don't bypass safety checks". |
| **D4** | Source-URL UI surface? | **Info-icon (`i`) per row, click → popover** showing `source_url` (link) + `notes_assumption` (text). | Pascal's choice. Click is keyboard- + screen-reader-friendly; reliably Playwright-testable; works on touch devices. |
| **D5** | Commit a D.xlsx hash manifest? | **Yes** — `data/import/d_xlsx.manifest.json` with `{import_tool_version, import_date, files: [{path, file_hash, sheet_hashes, region_code, rows_*}]}`. The .xlsx itself stays gitignored. | Audit trail; idempotency baseline; "what changed since last import" answer without reaching for the file. |
| **D6** | LOW-confidence DB rows (5 NONE + 25 LABEL_ONLY)? | **`origin='internal'`** with one-line per-row rationale comment in `data/import/orphan_classification.csv`. | Mostly category headers + deeper splits ours-only; pragmatic; promote later if stakeholder asks. |
| **D7** | Phase-A scope — schema + import + tooltip in one phase, OR split tooltip out? | **All three in one phase** (~3 days, single V5 Heroku cycle). | Tightly coupled — schema without import is dead, import without UI is invisible; saves V5 cycle (~$0.10). |
| **D8** | Region first-class — Phase A or Phase B? | **Phase B.** Phase A keeps single-region (Germany implicit; no `Region` model yet). Region + import + Bundesländer UI ships together in Phase B. | Smaller blast radius for Phase A (provenance-only is essentially zero-risk); Region migration wants its own V5 cycle and golden review. |

Companion: `260403_Section_2.3_recommendations.md` (Step G, commit `f04598d`) — original per-decision rationale before approval.

---

## 10. Open questions for Schmidt-Kanefendt (3, trimmed from v1's 4)

Not blocking the audit; worth raising before Phase B:

- **Q1:** Does the stakeholder have per-Bundesland Excel files in the same shape as D.xlsx? If yes, can he share a representative sample (e.g. BB.xlsx) to validate Phase B against?
- **Q2:** Are the 747 `hsk: |` comments on `D.xlsx!1.` considered authoritative documentation we should surface as-is, or working notes that we should curate before exposing?
- **Q3:** Is D.xlsx versioned / tagged on the stakeholder side (e.g. `D.250517.1733_hsk` in the file's `Stempel` sheet)? If yes, the import-tool manifest can record the version directly.

(v1 Q1 — canonical column for status/ziel — was resolved by switching to _S.xlsx; D-column convention no longer needed.)

---

## 11. Artefacts attached to this audit

Committed alongside this document (or by Steps A / B / C / D):

- `260403_Section_2.3_literal.md` — Step A literal paraphrase (commit `d2a4c28`).
- `WORKBOOK_CATALOG.md` — Step B per-file catalog (commit `55cf302`).
- `scripts/catalog_workbooks.py`, `scripts/probe_s_xlsx_formulas.py`, `scripts/probe_s_xlsx_values.py` — Step B extractors.
- `scripts/audit_out/{workbook_catalog,s_xlsx_probe,s_xlsx_values_probe}.txt` — Step B raw outputs.
- `scripts/audit_s_xlsx_mapping.py` — Step C mapping extractor (commit `58a1b90`).
- `scripts/audit_out/s_xlsx_map_<model>.csv` (4 files) + `s_xlsx_map_summary.json` — Step C per-model mapping evidence.
- `260403_Section_2.3_decision.md` — Step D binding decision record (commit `4c78f61`).
- `DATA_MODEL_AUDIT.md` — companion doc; `HARDCODED_VALUES_TRACE.md` — separate trace for the Jahresstrom flow diagram annotations.

Intentionally **not** produced by this audit (belongs to Phase A / B when approved):

- Schema migrations for `source_url`, `notes_assumption`, `origin`, `Region` FK.
- `Region` model + admin editor.
- `simulator/management/commands/import_excel_provenance.py` (Phase A).
- `simulator/management/commands/import_excel_datenmodell.py` (Phase B).
- `data/import/d_xlsx.manifest.json` (manifest pin).

The previous v1 produced a `data/mapping/d_xlsx_to_db.csv` placeholder. With Step C's mapping CSVs in place, that file is no longer needed — the s_xlsx_map_*.csv files ARE the curated mapping (78 % HIGH automatic + the 92 rows MED that benefit from a quick Pascal eyeball).

---

## 12. What this audit concludes (revised summary)

- §2.3 is a **provenance + region + admin-edit** ask. Not a value import.
- Our DB already holds the 420 parameter values; 78 % map at HIGH confidence to _S.xlsx, the stakeholder's scenario-master view file.
- The gap is **source URLs** (86 on D.xlsx), **assumption notes** (747 on D.xlsx), **first-class Region**, and **admin re-import without code change**.
- 12 atomic stakeholder requirements (SR-001 … SR-012); 10 risks (one drops H/H to L/L); 8 actually-blocking decisions for Pascal; 3 open questions for Schmidt-Kanefendt.
- Two-phase implementation: **Phase A** (provenance + tooltip + DE admin import, ~3 days, V2–V6) and **Phase B** (region first-class + Bundesländer-ready import + D4a/D4b unblocked, ~3 days, V2–V6).
- Cell / code / label freeze (CLAUDE.md rule #1) preserved by design — additive columns only.
- 51 shipped targets stay green; T54 D4a/D4b unblocks as a positive side-effect of Phase B.

**This audit makes no code changes and proposes none yet.** Next step is Pascal's decision on the 8 actually-blocking decisions in §9; coding starts in Phase A once those are resolved.
