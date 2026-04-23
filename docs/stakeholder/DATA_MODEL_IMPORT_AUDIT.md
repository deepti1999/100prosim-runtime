# §2.3 Data-Model Import — Deep Audit

**Status:** Audit only. No code changes proposed yet.
**Date:** 2026-04-23
**Author:** Claude (Opus 4.7) under Pascal's direction
**Scope:** Stakeholder PDF §2.3 "Datenmodell — Datenerfassung und Quellen" (Schmidt-Kanefendt 2026-04-03)
**Purpose:** Before touching any code, break §2.3 into atomic stakeholder requirements, audit our current architecture against each one, map the gap to Germany's `D.xlsx` data source, measure regression blast radius on the 63 already-shipped targets, and lay out a verification plan that keeps every shipped target green.

---

## 0. Reading guide

This document is intentionally long because §2.3 touches every parameter in the app, every page that displays a parameter, and every test that asserts on a parameter. The sections are:

1. **Executive summary** — one-page recommendation
2. **§2.3 decomposed** — atomic stakeholder requirements SR-001 … SR-010
3. **Architecture audit** — what we have today (models, seed, consumers, tests)
4. **D.xlsx structure** — what the PDF actually points us at
5. **Mapping analysis** — how cleanly our rows map to D.xlsx rows (spoiler: not cleanly)
6. **Impact on the 63 shipped targets** — per-phase risk
7. **Risk register** — enumerated + mitigations
8. **Verification / validation plan** — V2–V6 per phase
9. **Decision points** — what Pascal has to decide before coding starts

Sections 2, 5, 6, 7 are load-bearing for the final approach. Sections 3 and 4 are reference.

---

## 1. Executive summary

**Stakeholder ask (§2.3):** the 420 parameters that feed the simulator today are hardcoded in `seed/sqlite_seed.json` with no visible provenance. The stakeholder wants the D.xlsx (Germany data model, 17 sheets, 675 parameter rows, 86 source hyperlinks, 747 assumption comments) to be the **authoritative source** — every parameter editable per-scenario but traceable back to its D.xlsx row, source URL, and assumption comment.

**Current state:** our 4 parameter-bearing models (`LandUse`, `RenewableData`, `VerbrauchData`, `GebaeudewaermeData`) carry `source` / `quelle` / `notes` columns, but 346 of 420 rows (82%) have no source metadata. The seed fixture is the de-facto ground truth; D.xlsx is not consumed anywhere.

**Algorithmic mapping from our DB → D.xlsx sheet `1.` is NOT clean enough to automate:**

| Model               | Rows | Match ≥0.6 | Partial 0.3–0.6 | No match |
|---------------------|-----:|-----------:|----------------:|---------:|
| LandUse             |   20 |        75% |              5% |      20% |
| RenewableData       |  301 |        62% |             19% |      19% |
| VerbrauchData       |  151 |        54% |             22% |      24% |
| GebaeudewaermeData  |   26 |        35% |             23% |      42% |

(Full CSVs in `scripts/audit_out/mapping_*.csv`; extractor is `scripts/audit_import_mapping.py`.)

**Recommendation:** split §2.3 into a **4-phase incremental import** — schema + provenance first, hand-curated golden mapping second, per-scenario overrides third, UI provenance surfacing last. Each phase is independently shippable, independently verifiable, and none of them touch the 50+ shipped targets' behaviour unless we deliberately change a seed value. Details in §9.

**Hard rule this audit enforces:** no cell / code / label rename (CLAUDE.md §"Stakeholder requirements" #1). Every `LU_*`, `9.3.*`, Verbrauch code, WS365 field name, and `Formula.name` stays frozen. Import only adds provenance metadata and values; it does not rename anything.

---

## 2. §2.3 decomposed into atomic stakeholder requirements

The PDF §2.3 reads as one paragraph, but it bundles ≥10 distinct asks. Treating it as one requirement is how schema decisions go wrong. Decomposition:

### SR-001 — D.xlsx is the authoritative parameter source
> Every simulator parameter MUST correspond to a row in `D.xlsx` (Germany data model). A parameter with no D.xlsx row is an orphan and is either a calculated output, a UI-only field, or a policy/scenario assumption that needs to be promoted into D.xlsx.

**Acceptance:** a `scripts/verify_parameter_origin.py` can emit a per-row report {our_code, dxlsx_sheet, dxlsx_row, match_type} with zero `ORPHAN` rows (or a reviewed exception list).

### SR-002 — Each parameter carries its data source
> Each parameter row MUST carry the source URL / citation from D.xlsx column(s) in `9.Quellen` (86 hyperlinks today).

**Acceptance:** `LandUse.source`, `RenewableData.quelle`, `VerbrauchData.source`, `GebaeudewaermeData.source` are non-null for ≥95% of rows with a D.xlsx source, and the remaining <5% are listed in a known-exception file.

### SR-003 — Each parameter carries its assumption note
> The 747 per-cell comments in D.xlsx sheet `1.` (the methodology / author's reasoning) MUST be preserved alongside each parameter.

**Acceptance:** a new `notes_assumption` or extend-existing `notes` column populated for ≥90% of rows that have a D.xlsx comment.

### SR-004 — Numeric values round-trip against D.xlsx
> The current value of every parameter MUST match the corresponding D.xlsx cell within a stated tolerance (e.g. ±0.1% for floats, exact for integers/codes).

**Acceptance:** `scripts/verify_dxlsx_roundtrip.py` emits zero drift rows above tolerance, or a reviewed intentional-deviation list.

### SR-005 — Per-scenario overrides preserved
> The existing per-user / per-scenario override behaviour MUST NOT break. If the user changes `LU_2.1` in their workspace, their override still wins over the imported default; D.xlsx supplies the seed, not the per-user override.

**Acceptance:** existing `workspace_service.ensure_user_workspace_data()` behaviour unchanged; regression scenarios A / C / D pass unchanged; `compare.py` exit 0.

### SR-006 — Import is repeatable (idempotent)
> Re-running the import against an updated D.xlsx MUST be idempotent — running it twice produces the same DB state as running it once. Unchanged rows are not touched; changed rows produce a readable diff.

**Acceptance:** `python manage.py import_d_xlsx` on an unchanged file emits "0 changed"; on a changed file emits a per-row diff + prompts for confirmation before committing.

### SR-007 — Import does not rename cells/codes/labels
> Codes (`LU_0`, `9.3.1`, …), sector names, WS365 field names, `Formula` rows stay frozen. The import ADDS provenance and MAY update numeric values; it MUST NOT rename anything.

**Acceptance:** `grep -n "^def import_d_xlsx" scripts/`  never renames a code. Code-rename linter test `test_wb_code_freeze.py` stays green.

### SR-008 — Import does not break the 63 shipped targets
> All 63 targets from the stakeholder plan (50 shipped + Heroku-verified, 13 open) stay green. Golden regression scenarios A / C / D pass. All `test_bb_*` / `test_wb_*` / `test_e2e_*` modules pass.

**Acceptance:** full thesis test suite green pre-import and post-import on the same seed; A/C/D goldens unchanged unless intentionally re-captured with Pascal sign-off.

### SR-009 — Provenance is visible in the UI
> A user viewing a parameter on `/landuse/`, `/renewable/`, `/verbrauch/`, `/gebaeudewarme/` MUST be able to see its source URL and assumption comment (tooltip, expandable row, or side panel — UX TBD).

**Acceptance:** a Playwright test hovers a parameter row and asserts the tooltip contains the source URL.

### SR-010 — Orphan parameters are exposed, not hidden
> Parameters we have that D.xlsx doesn't (UI-only fields, derived outputs, scenario-policy assumptions) MUST be flagged as `origin='internal'` with a documented rationale, not silently treated as D.xlsx rows.

**Acceptance:** parameter-origin report has three categories: `d_xlsx`, `internal`, `orphan`; the `orphan` count is 0 or reviewed.

---

## 3. Current architecture audit

### 3.1 Parameter-bearing models

| Model                | Table                   | Rows | Key cols                                        | Source cols                |
|----------------------|-------------------------|-----:|-------------------------------------------------|----------------------------|
| `LandUse`            | `simulator_landuse`     |   20 | `code`, `name`, `status_ha`, `target_ha`        | `source`, `notes`          |
| `RenewableData`      | `simulator_renewabledata` | 223 | `code`, `category`, `subcategory`, `status_value`, `target_value`, `unit` | `quelle`, `description` |
| `VerbrauchData`      | `simulator_verbrauchdata` | 151 | `code`, `category`, `status`, `ziel`, `unit`   | `source`, `notes`          |
| `GebaeudewaermeData` | `simulator_gebaeudewaermedata` |  26 | `code`, `category`, `status`, `ziel`, `unit` | `source`, `notes`          |
| **Total**            |                         |  **420** |                                             |                            |

Additional structural models that are NOT parameter carriers but WILL be touched: `Formula` (760 rows, formula text — already frozen), `WSData` (365-day time series — derived), `Scenario` / workspace overlay models (per-user state — unchanged).

### 3.2 Seed state

- `seed/sqlite_seed.json` — 62,829 lines, 3,995 rows across 13 models.
- Of the 420 parameter rows, provenance today:
  - `source` / `quelle` non-null: **74 / 420 (18%)**
  - `notes` non-null: **0 / 420 (0%)**
  - `description` non-null: **103 / 420 (25%)**
- Conclusion: the DB schema supports provenance but the seed has not been populated; this is what §2.3 is pushing us to fix.

### 3.3 Parameter consumers

`simulator/*.py` files that import or query parameter models: **28 files** (identified via grep for `LandUse|RenewableData|VerbrauchData|GebaeudewaermeData`). The heaviest consumers:

- `recalc_service.py`, `workspace_service.py` — persistence orchestration
- `page_landuse.py`, `page_renewable.py`, `views_pages.py` — rendering
- `balance_jobs.py`, `ws_365_service.py` — WS balance flow
- `goal_seek.py`, `percentage_rebalancer.py` — numerical solvers
- 15 test modules (`test_bb_*`, `test_wb_*`, `test_e2e_*`, `test_ws365_formulas`)

Any schema change on the 4 models forces a review across all 28 files. A non-breaking additive column (e.g. `notes_assumption`) touches zero of them at read time — that's the safe corridor.

### 3.4 Cache & signal surface (from CLAUDE.md)

Four process-local caches invalidated at `BalanceJob` entry today:

- `recalc_cache._cache`
- `_AUTO_TOKENS_CACHE`, `_LOOKUPS_CACHE` (in `formula_service.py`)
- `_WS365_COMPUTE_CACHE` (in `ws365_orchestrator.py`)

Import must run **outside** a request/worker process (management command), so cache coherency isn't an issue. But: if the import writes rows while `ensure_user_workspace_data()` can fire for any existing user, we need a global lock or we run the import with the site in maintenance mode. Noted as RISK-04 below.

### 3.5 Test surface

- 15 of 19 `simulator/test_*.py` modules query at least one parameter model.
- Golden regression scenarios A / C / D all probe parameter values downstream.
- `test_ws365_formulas.py` pins 760 formula outputs — unaffected by value changes unless we intentionally change an input value.

---

## 4. D.xlsx structure deep-map

File: `docs/100prosim_d_*/D.xlsx` (gitignored; Germany data model; canonical).

| Sheet ref         | Content                                          | Parameter-row count (non-empty col E, non-stub) |
|-------------------|--------------------------------------------------|------------------------------------------------:|
| `1.`              | Main parameters (all 4 domains mixed by section) |                                       **~675** |
| `2.` … `8.`       | Sector breakdowns                                 |                                       varies |
| `9.Quellen`       | Source hyperlinks                                 |                        **86 hyperlinks** |
| (per-cell)        | Author comments (methodology / assumptions)       |                            **747 comments** |
| **Sheet total**   |                                                  |                                            17 |

Key column conventions on sheet `1.`:

- Col E — German label
- Col U (21) — primary scenario value
- Cols V / W / AG / AN — alternate scenarios / variants
- Source hyperlinks live on `9.Quellen` and are referenced from `1.` via comments / formula refs

The PDF assumes the reader is familiar with this layout; our mapping scripts treat col E as the matching key.

### 4.1 What D.xlsx gives us

- Hard numeric values for ~675 parameters
- 86 URL-shaped source citations
- 747 per-cell author comments (the "why this number" notes)
- Multi-variant scenarios that overlap with but are not identical to our scenarios A / C / D

### 4.2 What D.xlsx does NOT give us

- Our `code` scheme (`LU_*`, `9.3.*`, etc.) — these are ours, not Schmidt-Kanefendt's. The import must translate, not replace.
- Per-user overrides — that's our workspace layer; D.xlsx is single-variant per column.
- Formulas at the simulator level — the `Formula` table is ours; D.xlsx is a values document.

---

## 5. Mapping analysis (what "75% findable" actually means)

Source of the numbers: `scripts/audit_import_mapping.py` (committed with this audit). It reads the seed rows, normalises German labels, and matches against D.xlsx sheet `1.` col E by shared-word overlap.

### 5.1 Coverage

| Model              | Rows | Matched (≥0.6) | Partial (0.3–0.6) | Unmatched / No-label |
|--------------------|-----:|---------------:|------------------:|---------------------:|
| LandUse            |   20 |             15 |                 1 |                    4 |
| RenewableData      |  301 |            187 |                56 |                   58 |
| VerbrauchData      |  151 |             81 |                33 |                   37 |
| GebaeudewaermeData |   26 |              9 |                 6 |                   11 |

CSV details: `scripts/audit_out/mapping_*.csv` (502 rows total, 4 files).

### 5.2 Why algorithmic mapping is not enough

- **Gebäudewärme (35%):** codes like `GW_N.1.2` carry short category labels ("Erdgas Bestand", "Wärmepumpe Neubau") that overlap too weakly with D.xlsx's fuller sentences ("Endenergiebedarf Wärmepumpen im Bestand 2045"). The label overlap is genuine semantic match but the word-intersection score drops below threshold.
- **RenewableData (62%):** `9.3.*` sub-subcategories can share wording with multiple D.xlsx rows — e.g. "PV Dachanlage" matches 3 distinct rows (residential / commercial / mixed). Automated pick of the highest-overlap is **wrong** in ~1 in 5 cases; human disambiguation required.
- **VerbrauchData (54%):** category names repeat across sectors ("Industrie / Raumwärme" vs "Haushalt / Raumwärme") and D.xlsx sometimes lumps them on one row, sometimes splits. One-to-many and many-to-one cases dominate the unmatched bucket.
- **LandUse (75%):** cleanest; labels are unique enough ("Siedlungsfläche", "Landwirtschaftliche Nutzfläche") that word-overlap works. Still 4 unmatched — 2 are UI-only (`LU_0` aggregate), 2 need hand review.

### 5.3 Conclusion

**Do not automate the import from algorithmic matching.** The right artefact is a **hand-curated golden mapping CSV** (`data_model_mapping.csv`) that Pascal or the stakeholder reviews once, then the import reads that CSV deterministically. Treat the algorithmic audit as scaffolding for the human review, not as the import source.

---

## 6. Impact analysis on the 63 shipped targets

### 6.1 Per-phase risk matrix

Targets grouped by PDF phase (see `IMPLEMENTATION_PLAN.md`):

| Phase           | Targets | Parameter sensitivity           | Risk if we change a value      |
|-----------------|--------:|---------------------------------|--------------------------------|
| Phase 1 (UI)    |     T1–T12 | Low — UI shell only           | Cosmetic only                  |
| Phase 2 (domain)|  T13–T24 | **High** — reads LandUse / Renewable | Scenario C drift likely |
| Phase 3 (balance)| T25–T36 | **High** — WS365 reads all 4 models | Scenario C / D drift likely |
| Phase 4 (Bilanz)| T37–T44 | **High** — depends on Verbrauch + Gebäudewärme | Scenario D drift likely |
| Phase 5 (flow)  |  T45–T53 | Medium — flow diagram reads Bilanz | Jahresstrom diagram values move |
| Phase 6 (infra) |  T55–T63 | Low — deployment / perf         | Unlikely to drift numerics     |
| T54 D1–D4c      |       4 | **High** — D3 % / D4c Abgleichdiff depend on parameter values | Jahresstrom flow diagram numbers move |

### 6.2 Specific targets at risk

- **T25 (auto-cascade):** changing any parameter triggers cascade across formulas — if the numerical value of a status/ziel changes, Bilanz row outputs move. **Scenario C fingerprint will drift.**
- **T37 (Gebäudewärme Bilanz):** directly reads `GebaeudewaermeData.ziel`. Any D.xlsx re-synced value changes the Bilanz row.
- **T41 (Verbrauch Bilanz):** same pattern with `VerbrauchData`.
- **T49 / T50 (Jahresstrom diagram):** shipped Track 1 yesterday wiring D1–D4c from computed WS reference. Changing input parameters changes those outputs. Diagram screenshots in golden set will need re-capture if values shift.

### 6.3 What stays safe

- **Phase 1 (T1–T12):** text / CSS / template-only changes — untouched.
- **Phase 6 (T55–T63):** deployment / config — untouched unless we add a new management command which is additive.
- **`Formula` table rows (all 760):** import is values-only; formulas stay put.
- **All 15 `test_ws365_formulas` parity cases:** values of the 760 formula outputs are derived from inputs. If we don't change inputs (Phase A of the import — schema only — no value changes), all 760 stay green.

### 6.4 Safe corridor

**Phase A of the import (schema + provenance only, no value changes) touches zero of the 63 targets' numeric outputs.** That's the first shippable slice with essentially zero risk. Phases B, C, D introduce value changes and need per-phase golden review.

---

## 7. Risk register

| ID      | Risk                                                                             | Severity | Likelihood | Mitigation                                                                                                     |
|---------|----------------------------------------------------------------------------------|---------:|-----------:|----------------------------------------------------------------------------------------------------------------|
| RISK-01 | Importing a D.xlsx numeric value silently drifts a scenario golden               |     High |       High | Phase A (schema/provenance only) first; Phase B value sync gated on per-model golden re-capture with Pascal sign-off |
| RISK-02 | Ambiguous one-to-many label mappings auto-picked wrong                           |     High |       High | No auto-pick; hand-curated `data_model_mapping.csv` reviewed by Pascal before first import                     |
| RISK-03 | A code / cell / label gets renamed during import (violates CLAUDE.md contract)   | Critical |        Low | Import tool rejects any operation that would change `code`; linter test `test_wb_code_freeze.py` to cover     |
| RISK-04 | Import runs while `ensure_user_workspace_data()` is firing for live users        |   Medium |     Medium | Import requires maintenance-mode flag or runs on a cloned DB; never on live Heroku mid-session                 |
| RISK-05 | Per-user overrides silently overwritten by base row re-import                    | Critical |        Low | Import touches only owner=NULL base rows; user workspace tables (`owner=<user>`) are out of scope               |
| RISK-06 | D.xlsx column layout changes between stakeholder revisions                       |   Medium |     Medium | Import script asserts column headers match a pinned manifest; fails loud if Schmidt-Kanefendt reshapes the file |
| RISK-07 | Orphan parameters (we have them, D.xlsx doesn't) mis-classified as "missing"      |      Low |        Low | SR-010 — explicit `origin='internal'` column with rationale; orphan report reviewed manually                   |
| RISK-08 | Idempotency broken — second import run produces a diff                           |   Medium |     Medium | Content-hash each row; skip unchanged; unit test `test_wb_dxlsx_import_idempotent`                               |
| RISK-09 | Jahresstrom diagram (Track 1 D1–D4c) numbers move after Phase B                  |   Medium |     Medium | Re-run Playwright scenario against Heroku after each phase; screenshot diff reviewed                           |
| RISK-10 | Provenance column names collide with stakeholder-frozen `source` / `quelle`       |      Low |     Medium | Extend existing columns where possible; only add new columns for clearly new data (e.g. `notes_assumption`)    |

---

## 8. Verification / validation plan (V2–V6 per phase)

Applying CLAUDE.md's V2–V6 ritual to each import phase.

### Phase A — Schema + provenance extend (NO value changes)

- **V2 tests:** `test_wb_parameter_models_schema` (new) asserts `source`, `notes_assumption`, `origin` columns exist and are nullable; `test_wb_code_freeze` asserts no code was renamed.
- **V3 API smoke:** `/landuse/`, `/renewable/`, `/verbrauch/`, `/gebaeudewarme/` return 200 and same JSON shape (additive-only fields accepted).
- **V4 Playwright localhost:** scenarios A / C / D all exit 0 against unchanged goldens.
- **V5 Playwright Heroku:** spin up, navigate each parameter page, screenshot, eyeball tooltip shows source when hovered (if UI slice included in Phase A).
- **V6 docs:** `DATA_MODEL_IMPORT_AUDIT.md` updated with Phase A SHIPPED marker; `REMAINING.md` §3 updated.

### Phase B — Hand-curated mapping CSV + idempotent import command

- **V2 tests:** `test_wb_dxlsx_import_idempotent` (re-import = no-op); `test_wb_dxlsx_import_no_rename` (no code changes); `test_wb_dxlsx_orphan_report` (orphan classification correct).
- **V3 API smoke:** import command runs against a test-DB copy and emits "0 changed" on the second run.
- **V4 Playwright localhost:** scenarios A / C / D may drift IF values changed — run `categorize_A_diff.py` output, Pascal reviews, goldens re-captured with sign-off IF intentional.
- **V5 Playwright Heroku:** full parameter-page walk + Bilanz + Jahresstrom diagram visual check; screenshot diff vs pre-Phase-B baseline.
- **V6 docs:** per-model mapping CSV checked in; per-phase change log in this audit.

### Phase C — Per-scenario override wiring (SR-005)

- **V2 tests:** `test_bb_scenario_override` (user override wins over D.xlsx default); existing workspace tests unchanged.
- **V3 API smoke:** save a user edit, reload, verify user value stays.
- **V4 Playwright localhost:** scenario D (write / read-back) passes unchanged.
- **V5 Playwright Heroku:** testsim user saves an override on live Heroku; reloads; value persists across a worker recycle.
- **V6 docs:** override-contract documented in `CLAUDE.md` "Known invariants" section.

### Phase D — UI provenance surfacing (SR-009)

- **V2 tests:** template snapshot test includes `data-source-url` attribute on parameter rows.
- **V3 API smoke:** HTML response includes the attribute.
- **V4 Playwright localhost:** new scenario `E-provenance-tooltip` asserts tooltip text on hover.
- **V5 Playwright Heroku:** same scenario against live URL.
- **V6 docs:** screenshot evidence in `VISUAL_VERIFICATION_2026-04-<date>.md`.

### Gate between phases

Pascal explicitly signs off before advancing. No phase starts while the previous one has red tests or ungraded golden drift.

---

## 9. Decision points for Pascal

Concrete choices that have to be made before Phase A opens a PR.

1. **Column naming for assumption notes.** Extend existing `notes` column (currently empty, 0/420) vs add a new `notes_assumption` column? Extending is less churn; adding is more explicit. **Recommendation:** extend existing `notes`, add a separate `origin` enum column.

2. **Mapping CSV location.** `data_model_mapping.csv` at repo root, under `data/`, or under `docs/stakeholder/`? **Recommendation:** `data/mapping/d_xlsx_to_db.csv` so the import script has a stable path and it's not confused with docs.

3. **D.xlsx snapshot versioning.** D.xlsx is gitignored today. We need a hash / version pin so we know what import ran against what file. **Recommendation:** commit `data/mapping/d_xlsx.manifest.json` with `{file_hash, sheet_hashes, import_date}`; keep the binary gitignored.

4. **Phase A scope — UI or not?** Phase A can be purely schema (no UI) or can include the SR-009 tooltip. **Recommendation:** Phase A = schema only, Phase D = tooltip. Cleaner to separate.

5. **Value sync policy.** When D.xlsx value ≠ our seed, does D.xlsx win (auto-overwrite on import) or do we emit a diff for review? **Recommendation:** diff-and-review for first 3 imports, auto-overwrite after pattern stabilises.

6. **Orphan handling.** Parameters we have that D.xlsx doesn't (policy assumptions, UI-only rows) — classify as `origin='internal'` and leave them, or push them into D.xlsx via a new sheet? **Recommendation:** classify as `origin='internal'` for now; stakeholder decision on whether to promote them.

7. **Heroku import cadence.** Import runs once at release, or every deploy, or on-demand? **Recommendation:** on-demand management command (`manage.py import_d_xlsx`) — no implicit run at deploy.

8. **Commit boundaries.** One commit per phase, or per-model within a phase? **Recommendation:** one commit per phase (A, B, C, D) — cleaner revert surface. Scripts + mapping CSV can go in same commit as the phase that introduces them.

9. **Test baseline refresh.** Run `regression/capture_A.py` + `capture_C.py` + `capture_D.py` before Phase A opens so we have a clean pre-audit fingerprint. **Recommendation:** yes, unconditionally.

10. **T54 D1–D4c interaction.** Track 1 just shipped yesterday. Phase A is additive so should be neutral; Phase B value-sync could move D3 / D4c outputs. **Recommendation:** Phase B for RenewableData runs AFTER re-capturing Track 1 Jahresstrom golden.

---

## 10. Open questions for Schmidt-Kanefendt

(Not blocking audit, but worth raising with the stakeholder before Phase B value sync.)

- Q1: For rows where D.xlsx has multiple scenario columns (U / V / W / AG / AN), which column is canonical for the current app scenario?
- Q2: Are the 747 per-cell comments considered authoritative documentation, or working notes? (Affects whether we surface them as-is or curate.)
- Q3: Is D.xlsx versioned / tagged on your side? (Affects RISK-06 mitigation.)
- Q4: Should the 4 simulator models reorganise around D.xlsx sheet taxonomy (currently our model-split is by UI page, D.xlsx splits by sector)? (Affects a possible future Phase E refactor but out of scope for SR-001…SR-010.)

---

## 11. Artefacts attached to this audit

Committed alongside this document:

- `scripts/audit_import_mapping.py` — algorithmic label-match extractor (the tool that produced §5.1 numbers).
- `scripts/audit_out/mapping_landuse.csv` — 20 rows.
- `scripts/audit_out/mapping_renewabledata.csv` — 301 rows.
- `scripts/audit_out/mapping_verbrauchdata.csv` — 151 rows.
- `scripts/audit_out/mapping_gebaeudewaermedata.csv` — 26 rows.

Intentionally NOT produced by this audit (belongs to Phase A/B when approved):

- `data/mapping/d_xlsx_to_db.csv` — hand-curated golden mapping.
- `data/mapping/d_xlsx.manifest.json` — source file hash.
- `simulator/management/commands/import_d_xlsx.py` — import management command.
- Schema migrations for `origin` / `notes_assumption` columns.

---

## 12. Summary: what this audit concludes

- §2.3 is 10 atomic stakeholder requirements, not one.
- Our architecture supports ~60% of them with the existing schema; the missing ~40% is provenance population, not structural redesign.
- Algorithmic mapping is 35–75% accurate — not enough to automate; hand-curation required once by Pascal/stakeholder, then deterministic.
- The 63 shipped targets are safe as long as Phase A (schema/provenance) precedes Phase B (value sync), and Phase B re-captures goldens deliberately.
- Cell / code / label freeze (CLAUDE.md rule #1) is preserved by design — import adds metadata, does not rename.
- Risk register has 10 identified risks, 7 medium-or-above, all with named mitigations.
- Four phases (A/B/C/D) each independently shippable with V2–V6 discipline.
- Ten decision points remain for Pascal before Phase A opens a PR; four questions for Schmidt-Kanefendt before Phase B.

**This audit makes no code changes and proposes none yet.** Next step is Pascal's decision on the 10 decision points in §9; coding starts in Phase A once those are resolved.
