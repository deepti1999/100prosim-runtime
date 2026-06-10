# 100prosim-Web — Stakeholder Implementation Plan

**Source of truth:** `260403_Portierung_Bestandsaufnahme.pdf` (ErnES, Schmidt-Kanefendt, 2026-04-03).
**Companion docs:** `260403_Bestandsaufnahme_DE.md` (German extract), `260403_Bestandsaufnahme_EN.md` (English translation), `NEXT_CHANGES.md` (P0–P4 digest).

This plan operationalises the stakeholder document. Every atomic ask in the PDF has a target ID (`T1`–`T63`) traced back to its source section. No target is skipped.

---

## 0. Principles (non-negotiable)

1. **Nothing in the PDF gets skipped.** Every atomic target T1–T63 has a verification checkbox. A phase is only "done" when all its targets pass verification.
2. **No calculation logic changes.** UI, UX, layout, translations, menus, buttons — all fair game. Math inside `calculation_engine/` and the `Formula` table is frozen. Exceptions are explicit and require Pascal's sign-off (currently: Phase 7 performance work only).
3. **No renaming domain cells.** LU_*, 9.3.1/9.3.4/10.x, sector names, Verbrauch codes, WS365 field names stay as-is. Translations are UI labels on top of the codes, not replacements for them.
4. **"Recalculate" means cascade propagation, not auto-Balance.** §2.4.4 of the PDF asks that user edits auto-propagate through interconnected cells (Verbrauch change → linked Erneuerbare cells refresh) — the existing `save_and_recalculate_*` path. Balance (§2.4.3) remains a manual button (two of them: Solar + Wind). Do not confuse the two.
5. **Commit per item, not per phase.** Small reversible commits. Never stack two behaviour changes in one commit.
6. **Verification is non-negotiable.** Every item must pass V2 (unit/contract tests), V3 (API smoke), V4 (Playwright against localhost), V5 (Playwright against live Heroku), V6 (docs). If any of the four fails, the item is not done. New tests may be added whenever coverage is weak. See §1 for the full ritual.
7. **Easiest first.** We front-load small, reversible, visible wins. Big structural work (acid test, handover) lives in later phases so the early sprints demonstrate progress and de-risk the tooling.
8. **Stakeholder-review gates between phases.** We stop after each phase, show Pascal + Schmidt-Kanefendt the result, and collect feedback before starting the next.

---

## 1. Verification template (used by every item)

Every item `X-N` follows this six-step ritual. Plan is **not** done until all six are green.

| Step | What | Where | Pass criterion |
|---|---|---|---|
| **V1 — Plan-internal** | Item's deliverable list in this doc | `IMPLEMENTATION_PLAN.md` | Every sub-target `T*` for this item has a ✅ box filled |
| **V2 — Unit / contract tests** | Targeted Django test module(s) | `simulator/test_*` | All relevant `test_bb_*` / `test_wb_*` / `test_e2e_*` pass locally. New tests added for any new code path. |
| **V3 — API smoke** | curl or pytest hitting HTTP endpoints | `scripts/smoke_<item>.sh` | Expected JSON / HTTP 200 / contract preserved |
| **V4 — Playwright localhost** | Regression scenario at `http://localhost:8001` | `regression/scenarios/` + `simulator/test_e2e_ui_*.py` | Scenario A + any item-specific scenario passes; screenshot diff clean |
| **V5 — Playwright Heroku** | Same scenario against live `prosim-100` | `bash scripts/heroku_up.sh` → run → `bash scripts/heroku_down.sh` | Scenario passes on live URL. Catches cross-process cache bugs that V2–V4 miss. |
| **V6 — Docs** | Update `CLAUDE.md` / per-item doc / memory if needed | `CLAUDE.md`, `docs/`, memory files | Any new invariant, gotcha, or decision is written down. |

**Cadence for V5:** batch by phase, not per item. Spin Heroku up once per phase, run the full Playwright suite against it, tear down. Keeps Heroku cost to ~$0.10/phase.

**Regression scenarios as checkpoints:** `compare.py A`, `compare.py C`, `compare.py D` must still pass after every item. Golden files regenerate **only** with explicit Pascal sign-off, never automatically.

---

## 2. Guardrails (what we will NOT touch)

| Off-limits | Why |
|---|---|
| `calculation_engine/*` formula logic | Math contract is frozen. |
| `Formula` table rows | Stakeholder contract. |
| Domain cell codes (LU_*, 9.3.x, 10.x, Verbrauch codes) | Stakeholder contract — external workflows depend on them. |
| Sector names (KLIK, Gebäudewärme, Prozesswärme, Mobile Anwendungen) | Four-sector model is load-bearing. |
| Iteration cuts from 2026-04-21 perf pass | Tuned for Heroku; reverting slows balance 2–3×. Revert recipe exists (`docs/CONVERGENCE_ITERATIONS_CHANGED.md`) but not used without ask. |
| `test_ws365_formulas` golden values | Math parity regression. |

Any item that requires touching the above is escalated to Pascal before starting.

---

## 3. Master target map (63 atomic targets from 16 PDF sections)

> This is the completeness ledger. Every PDF section is decomposed into atomic targets. Every target maps to exactly one item. The plan is done when every ✅ is checked.

**Fidelity notes:**
- **"explicit"** = PDF states it directly in words.
- **"implied"** = follows necessarily from PDF context (e.g. PDF mentions the login-loss incident in §2.1 → recovery procedure is implied as a handover deliverable).
- **"conditional"** = PDF phrases the ask as "if X, then do Y" — we must verify X first.
- **"extrapolated"** = reasonable extension of explicit asks to related UI surfaces PDF didn't individually enumerate.

| ID | PDF § | Target | Fidelity | Item |
|---|---|---|---|---|
| **T1** | §2.1 | ErnES compute platform provisioned (external gate) | explicit | 7-A |
| **T2** | §2.1 | Runnable installation on ErnES platform | explicit | 7-A |
| **T3** | §2.1 | ≥2 ErnES admins trained on hosting runbook | explicit | 7-A |
| **T4** | §2.1 | Login-credential loss recovery procedure documented | implied (PDF reports the incident) | 7-A |
| **T5** | §2.2 | Run acid test: onshore 2.0→2.3 %, offshore 70→60 GW, measure reconciliation time | explicit | 7-B |
| **T6** | §2.2 | Acid-test benchmark script (reproducible, tracked cycle-over-cycle) | implied | 0-C |
| **T7** | §2.2 | If acid test fails on ErnES platform: trigger architecture review | explicit | 7-B |
| **T8** | §2.3.1 | Parameter source (Quellbezug) surfaced in UI | explicit (proposal) | **DEFERRED** |
| **T9** | §2.3.1 | Parameter assumption (Annahme) surfaced in UI | explicit (proposal) | **DEFERRED** |
| **T10** | §2.3.1 | Admin can update parameters without code changes | explicit (proposal) | **DEFERRED** |
| **T11** | §2.3.2 | Scenario switcher between regions (DE + Bundesländer) | explicit (proposal) | **DEFERRED** |
| **T12** | §2.3.2 | Data model loaded from external file (Excel interface) | explicit (proposal) | **DEFERRED** |
| **T13** | §2.3.2 | Region-specific data models editable by non-developer admins | explicit (proposal) | **DEFERRED** |
| **T14** | §2.4.1 | Clearing user-input modification → original base value reappears | explicit (Verbrauch target) | 4-A |
| **T15** | §2.4.1 | T14 applies to Verbrauch targets, Renewable user inputs, LandUse user percents | extrapolated to all 3 mod surfaces | 4-A |
| **T16** | §2.4.2 | Remove "Create baseline" button | explicit | 4-B |
| **T17** | §2.4.2 | "Reset to baseline" loads admin-configured base | explicit | 4-B |
| **T18** | §2.4.2 | Shared baseline across users (not per-user) | explicit | 4-B |
| **T19** | §2.4.3 | Remove "Goal Seek" button | conditional (if already auto-runs, else add auto-run first) | 1-B |
| **T20** | §2.4.3 | Remove "Refresh / Aktualisieren" button | conditional (same) | 1-B |
| **T21** | §2.4.3 | Merge WS Balance Solar + Sector+WS Solar → single "Balance Solar" | explicit | 4-C |
| **T22** | §2.4.3 | Merge WS Balance Wind + Sector+WS Wind → single "Balance Wind" | explicit | 4-C |
| **T23** | §2.4.3 | Fix: buttons non-functional after scenario changes, no busy indicator | explicit (bug report) | 4-D |
| **T24** | §2.4.4 | Auto-**cascade** on any Verbrauch user change (change → linked Erneuerbare cells refresh; not auto-Balance) | explicit | 4-E |
| **T25** | §2.4.4 | Auto-cascade on any Erneuerbare user change | explicit | 4-E |
| **T26** | §2.4.4 | Auto-cascade on any Flächen user change | explicit | 4-E |
| **T27** | §2.4.4 | Never leave the user in an undefined-state window (clear visual feedback) | implied | 4-E |
| **T28** | §2.4.5 | Remove "Save All Values" button from Flächen page | conditional (if Scenarios→Save covers the intent) | 1-A |
| **T29** | §2.5.1 | Translate all page headings to German | explicit | 2-A |
| **T30** | §2.5.1 | Translate all column labels to German | explicit | 2-A |
| **T31** | §2.5.1 | Translate all button labels to German | explicit | 2-A |
| **T32** | §2.5.1 | Translate user manual to German | explicit | 2-B |
| **T33** | §2.5.1 | Native-German text (not Google-translate artifacts) | explicit | 2-A, 2-B |
| **T34** | §2.5.2 | German number format (dot thousands, comma decimal) on all pages | explicit (display) | 2-C |
| **T35** | §2.5.2 | German input parsing: `1.234,5` accepted | implied (parsing must match the format) | 2-C |
| **T36** | §2.5.2 | JS-rendered numbers use `toLocaleString('de-DE')` | implied (how T34 is achieved for JS) | 2-C |
| **T37** | §2.5.3 | Side-menu present on Verbrauch | explicit | 3-A |
| **T38** | §2.5.3 | Side-menu present on Jahresstrom | explicit | 3-A |
| **T39** | §2.5.3 | Side-menu present on Benutzerhandbuch | explicit | 3-A |
| **T40** | §2.5.3 | Side-menu uniformly formatted on Cockpit | explicit | 3-A |
| **T41** | §2.5.3 | Remove duplicate entries from top bar | conditional (only after T37–T40 make side-menu universal) | 3-B |
| **T42** | §2.5.3 | Move "100prosim" branding into side-menu header | explicit | 3-B |
| **T43** | §2.5.4 | Status + Target side-by-side view | explicit (Excel-pattern proposal) | 5-A |
| **T44** | §2.5.4 | Per-sector contribution breakdown | explicit | 5-A |
| **T45** | §2.5.4 | Left column "Wieviel werden wir noch brauchen?" (demand by sector) | extrapolated from Excel AH.Cockpit1 screenshot | 5-A |
| **T46** | §2.5.4 | Right column "Wo soll es herkommen?" (supply by source) | extrapolated from same screenshot | 5-A |
| **T47** | §2.5.4 | Percentage-delta annotations (e.g. -27 %, ×5.2) | extrapolated from same screenshot | 5-A |
| **T48** | §2.5.5 | Chart: Nachfrage-Einflüsse auf Endenergieverbrauch (Variantenvergleich) | explicit (Excel AH.Cockpit2) | 6-B |
| **T49** | §2.5.5 | Chart: Effizienz-Einflüsse auf Endenergieverbrauch (Variantenvergleich) | explicit | 6-B |
| **T50** | §2.5.5 | Chart: Endenergie-Verbrauch nach Anwendungsbereichen inkl. Grundstoffe | explicit | 6-B |
| **T51** | §2.5.5 | Chart: Primärenergie-Beiträge nach Quellen | explicit | 6-B |
| **T52** | §2.5.5 | Chart: Ausbau der Erneuerbaren Energiequellen | explicit | 6-B |
| **T53** | §2.5.6 | Audit current Flussdiagramm vs. Excel reference node-by-node | implied (precondition to fix) | 5-C |
| **T54** | §2.5.6 | Correct value→node assignments | explicit ("Werte falsch zugeordnet") | 5-C |
| **T55** | §2.5.6 | Increase font size / allow zoom | explicit ("kleine Schriftart") | 5-C |
| **T56** | §2.5.6 | Match Excel structure (Bedarfs-KW, PV, Wind, Laufwasser+Geoth → Elektrolyse → Stromspeicher → Rückverstromung; branches: Abregelung, Gasspeicher Direktverbr, Gasspeicher Strom) | explicit (Excel template shown) | 5-C |
| **T57** | §2.5.7 | Rescale y-axis: either Min=0 or annotate Min/Max/Capacity directly | explicit | 5-B |
| **T58** | §2.5.7 | Daily surplus / deficit stacked bars (solar + wind, separately) | explicit (Excel layout) | 5-B |
| **T59** | §2.5.7 | Mangelausgleich overlay bar | explicit | 5-B |
| **T60** | §2.5.7 | Unit switch GWh → Tagesladung | explicit | 5-B |
| **T61** | §2.5.8 | Persist each modification step (before/after, who, what, when) | explicit | 6-A |
| **T62** | §2.5.8 | UI showing snapshots as columns (per Excel layout) | explicit | 6-A |
| **T63** | §2.5.8 | Inspectable history (tracking of measure + effect — **not** undo/restore) | explicit (PDF says "Nachverfolgung", not "Rückgängig") | 6-A |

**T8–T13 are deferred** (data model rework) — Pascal has the Excel files but this needs its own discovery/scoping session before being pulled into the main plan. See §12 for details.

---

## 4. Phase sequencing (easiest → hardest)

| Phase | Name | Items | Risk | ETA (calendar, rough) |
|---|---|---|---|---|
| **0** | Scaffolding | 0-A, 0-B, 0-C | Low | 0.5 day |
| **1** | Surface removals | 1-A, 1-B | Very low | 0.5 day |
| **2** | Localization | 2-A, 2-B, 2-C | Low | 2 days |
| **3** | Menu consistency | 3-A, 3-B | Low | 1 day |
| **4** | Behaviour fixes | 4-A, 4-B, 4-C, 4-D, 4-E | Medium | 4 days |
| **5** | Chart rework | 5-A, 5-B, 5-C | Medium | 4 days |
| **6** | History + details | 6-A, 6-B | High | 5 days |
| **7** | Acid test + handover | 7-A, 7-B | External-gated | dependent on ErnES |
| **DEFERRED** | Data model (T8–T13) | — | — | separate scoping session with Pascal |

Phases 0–6 are what we drive end-to-end. Phase 7 is blocked on ErnES's platform choice. The data-model work (§2.3 of the PDF) is deferred to a separate effort — Pascal has the Excel files but we need a dedicated scoping session before pulling this into the main plan.

---

## 5. Phase 0 — Scaffolding

Before touching any stakeholder item, set up the infrastructure so phases 1–8 can run consistently.

### 0-A. Progress tracker file

**Deliverable:** `docs/stakeholder/PROGRESS.md` — the live checkbox grid. One box per target T1–T63. Updated at every commit.
**Verification:** file exists; commits reference target IDs (`docs(progress): T28 ✅`).
**Files:** new file.

### 0-B. Playwright regression scenarios for each phase

**Deliverable:** new regression scenarios covering the specific user journeys stakeholders test:
- `scenarios/E-verbrauch-edit.yml` — edit Verbrauch target, save, verify auto-recalc (for Phase 4)
- `scenarios/F-acid-test.yml` — onshore 2.0→2.3 %, offshore 70→60 GW, measure time (for Phase 8)
- `scenarios/G-modification-history.yml` — N edits, verify history log (for Phase 6)
**Verification:** each scenario produces a golden JSON on clean main, `compare.py <id>` exits 0.
**Files:** `regression/scenarios/*.yml`, `regression/golden/*.json`.

### 0-C. Acid-test benchmark harness

**Deliverable:** `scripts/bench_acid_test.sh` — reproducible 100prosim-Excel-vs-Web response-time comparison per §2.2 (T6).
- Creates clean workspace state, applies the two changes, triggers Balance Solar, times end-to-end.
- Runs against any `BASE_URL` (localhost or Heroku).
- Output: JSON with `{timestamp, url, host_platform, elapsed_s, commit_sha}`.
**Verification:** script runs locally and against Heroku, produces sane JSON.
**Files:** `scripts/bench_acid_test.sh`, `docs/stakeholder/BENCHMARK_LOG.md` (rolling log).

---

## 6. Phase 1 — Surface removals

Items are 30-minute fixes each. Removing unused buttons. No behaviour change.

### 1-A. Remove "Save All Values" button — `T28`

**Source:** §2.4.5 — button is redundant with `Scenarios → Save current Scenario`, only covers LandUse (not Renewables/Verbrauch), confusing.
**Files:** `simulator/templates/simulator/landuse_list.html` (or equivalent), any JS that wires it up.
**Approach:** delete the button + its JS handler. Leave the underlying endpoint for now (in case other callers exist); mark deprecation in code comment.
**V1:** T28 unchecked → checked.
**V2:** `test_bb_e2e` still passes (no breakage), no new test needed (pure removal).
**V3:** POST to the old endpoint still works (idempotence).
**V4:** Playwright `/landuse/` → verify button absent.
**V5:** Same, live Heroku.
**V6:** `CLAUDE.md` entry in Phase 1 change log.

### 1-B. Remove "Goal Seek" + "Refresh (Aktualisieren)" buttons — `T19`, `T20`

**Source:** §2.4.3 — Stakeholder states these are redundant because the functions run automatically on window open and after Balance.
**Files:** `simulator/templates/simulator/ws_template_balance_ui.html` (or wherever the Szenario-Abgleich modal is rendered), related JS.
**Approach:**
1. First verify the claim: do Goal Seek / Aktualisieren actually run automatically already? If yes, delete both buttons. If no, the underlying auto-trigger must be added **before** removing them.
2. Remove buttons only when auto-behaviour is confirmed.
**V1:** T19, T20.
**V2:** `test_bb_bal`, `test_e2e_ui_D_full_flow` still pass.
**V3:** Balance-all API still produces identical output pre/post removal.
**V4:** Playwright — open Szenario-Abgleich modal, buttons not present, balance still completes.
**V5:** Same, Heroku.
**V6:** `CLAUDE.md` — note the Goal Seek / Refresh redundancy finding.

---

## 7. Phase 2 — Localization

Translation work. Mechanical. Can run in parallel with Phase 3.

### 2-A. Translate all UI labels to German — `T29`, `T30`, `T31`, `T33`

**Source:** §2.5.1 — page headings, columns, buttons still English despite menu bar saying "Erneuerbare Energien". Inconsistency = user confusion.
**Files:** every file under `simulator/templates/`; audit with `grep -rni "Renewable Energy\|Land Use\|Status Value\|Target Value\|User Input\|Save All\|Recalculate" simulator/templates/`.
**Approach:**
1. Build a translation mapping file: `docs/stakeholder/TRANSLATION_GLOSSARY.md` — every English term Pascal would accept as German. Review with Pascal before mass-edit.
2. Apply term-by-term across all templates. Keep English text only inside Python / JS identifiers (code contract), never in user-facing output.
3. Must be **native German** (T33) — Pascal / Schmidt-Kanefendt review required, no Google Translate.
**V1:** T29, T30, T31, T33.
**V2:** all pages render without template errors.
**V3:** HTML bodies contain no untranslated English domain terms. Automated check: `grep -E "Renewable|Land Use|Save All|Target Value" docs/e2e_snapshots/` must be empty after run.
**V4:** Playwright visits every page, captures text content, diff against expected German strings.
**V5:** Same, Heroku.
**V6:** `docs/stakeholder/TRANSLATION_GLOSSARY.md` committed. `CLAUDE.md` note about "translate UI, not codes".

### 2-B. Translate user manual to German — `T32`, `T33`

**Source:** §2.5.1 — manual is entirely English, inconsistent with partially-German menus.
**Files:** `simulator/templates/simulator/user_manual.html` (or similar).
**Approach:** Native German rewrite, not translation of English. Consider splitting into sections that map to pages. Pascal reviews.
**V1:** T32, T33.
**V2:** manual page renders.
**V3:** page body contains German text (automated: ratio of German indicator words vs. English).
**V4:** Playwright navigate to manual, content check.
**V5:** Same, Heroku.
**V6:** Update `docs/README.md` to point at the German manual.

### 2-C. German number format end-to-end — `T34`, `T35`, `T36`

**Source:** §2.5.2 — currently only Szenario-Abgleich uses German format; everywhere else is English `1,234.5`.
**Files:** `landuse_project/settings.py` (`LANGUAGE_CODE`, `USE_L10N`), `simulator/templatetags/` (possibly new filters), any JS number formatter (Chart.js options, hand-rolled).
**Approach:**
1. Confirm Django locale settings. If `LANGUAGE_CODE = 'de'` isn't already set, set it. Add `USE_THOUSAND_SEPARATOR = True`.
2. Audit every template for `|floatformat` without `|intcomma`; replace with locale-aware filters.
3. Audit every JS file for `.toFixed(N)` / manual `.replace(',', '.')`; replace with `.toLocaleString('de-DE', { ... })`.
4. Input parsing: accept `1.234,5` in forms → convert to Python float on save. New utility function `parse_de_decimal`.
**V1:** T34, T35, T36.
**V2:** new unit tests for `parse_de_decimal` edge cases.
**V3:** API round-trips a value posted as `1.234,5` and returns the same format on GET.
**V4:** Playwright — visit every numeric page, screenshot, check for presence of comma-decimal and dot-thousands.
**V5:** Same, Heroku.
**V6:** `CLAUDE.md` note: German locale + `toLocaleString('de-DE')` are the contract.

---

## 8. Phase 3 — Menu consistency

### 3-A. Universal side-menu — `T37`, `T38`, `T39`, `T40`

**Source:** §2.5.3 — side-menu missing on Verbrauch, Jahresstrom, Benutzerhandbuch; differently formatted on Cockpit.
**Files:** extract shared side-menu into `simulator/templates/simulator/_sidebar.html`; include in `base.html` or every page template.
**Approach:**
1. Diff current side-menu markup across pages; extract the canonical form.
2. Create `_sidebar.html` partial.
3. Add `{% include '_sidebar.html' %}` to the three missing pages.
4. Normalize Cockpit's custom formatting.
**V1:** T37–T40.
**V2:** all templates render.
**V3:** n/a (pure template).
**V4:** Playwright visits all pages, asserts side-menu DOM element is present + same CSS class set.
**V5:** Same, Heroku.
**V6:** `CLAUDE.md` — template partial pattern.

### 3-B. Top-bar dedup — `T41`, `T42`

**Source:** §2.5.3 — left entries in top bar duplicate what's in the side-menu; 100prosim branding should move into side-menu header.
**Files:** `base.html` or the top-nav partial; `_sidebar.html` (for the branding header).
**Approach:** Remove duplicate top-bar links (Flächennutzung, Erneuerbare Energien, etc.); keep only the right-side account dropdown (Baseline, Scenarios, user). Add "100prosim" brand to side-menu top.
**V1:** T41, T42.
**V2:** templates render.
**V3:** n/a.
**V4:** Playwright — top bar has ≤ the set {brand-in-sidebar, account-dropdown}; no leftover page links.
**V5:** Same, Heroku.
**V6:** —

---

## 9. Phase 4 — Behaviour fixes

Biggest UX bundle. Each item has real backend touches.

### 4-A. Base-value restoration on clear — `T14`, `T15`

**Source:** §2.4.1 — deleting user input field should restore the base value.
**Files:** Verbrauch / Renewable / LandUse form templates + JS handlers.
**Approach:** treat the user input field as an **overlay** on base value.
- Show base value as placeholder / greyed-out background text.
- When user types → shows user value, clear "override" badge.
- When user clears (empty) → shows base value, no override badge.
- Backend: submitting empty user value persists `user_value=NULL`, which the existing logic already treats as "use base".
**V1:** T14, T15.
**V2:** new `test_bb_input_clear_restores_base` across three models.
**V3:** POST empty → GET returns base value.
**V4:** Playwright — set LandUse user_percent to 5, save, clear it, save, verify base percent reappears.
**V5:** Same, Heroku.
**V6:** —

### 4-B. Baseline = admin-provided — `T16`, `T17`, `T18`

**Source:** §2.4.2 — remove "Create baseline"; "Reset to baseline" loads admin baseline; shared across users.
**Files:** `simulator/models.py` (or baseline model file), `simulator/views_recalc.py` / `baseline_api.py`, baseline dropdown template.
**Approach:**
1. Introduce `AdminBaseline` singleton (per data model, not per user) seeded at data import.
2. `restore_baseline` uses `AdminBaseline` as source, not user's last capture.
3. Remove "Create baseline" UI. "Save as Scenario" remains (that's the user-facing save/restore, §2.4.5 explicitly endorses it).
**V1:** T16, T17, T18.
**V2:** new `test_bb_admin_baseline_shared_across_users`; old tests for `create_baseline` endpoint become obsolete (remove or mark xfail).
**V3:** API: POST `/api/baseline/restore/` resets all user data to admin baseline; verify two users see the same baseline.
**V4:** Playwright — user A modifies, user B modifies, both `Reset to baseline`, both converge to same state.
**V5:** Same, Heroku (two browser sessions).
**V6:** `CLAUDE.md` — note shared baseline contract.

### 4-C. Consolidate Balance buttons — `T21`, `T22`

**Source:** §2.4.3 — 4 buttons (WS Solar, Sector+WS Solar, WS Wind, Sector+WS Wind) → 2 ("Balance Solar", "Balance Wind").
**Files:** Szenario-Abgleich template, `simulator/views_ws.py`, `simulator/views_balance.py`.
**Approach:**
- Keep the 4 underlying API endpoints (they're separately useful).
- New "Balance Solar" button calls `apply_full_balance` (which already runs both WS and Sector+WS internally per §2.4.3 reading).
- Same for "Balance Wind" → `apply_full_balance_wind`.
- If `apply_full_balance` doesn't currently do the full pipeline, extend it to do so. **This is orchestration, not math** — confirmed within guardrails.
**V1:** T21, T22.
**V2:** `test_bb_bal` updated for new single-call flow.
**V3:** API contract stable for old endpoints; new unified endpoint produces same final state as old two-step.
**V4:** Playwright — click "Balance Solar" → state matches old two-step result.
**V5:** Same, Heroku (this is the class of bug we hit before — cross-process cache coherency).
**V6:** `CLAUDE.md` — balance-button consolidation recorded.

### 4-D. Fix: buttons non-functional after scenario changes — `T23`

**Source:** §2.4.3 — "during tests, buttons were mostly non-functional after scenario changes, no reconciliation and no busy indicator".
**Files:** investigate first; likely `balance_jobs.py`, frontend job-poll code, middleware.
**Approach:**
1. Reproduce on Heroku (this matches the class of bug we hit in 2026-04-21 — cross-process cache staleness).
2. Confirm whether `54d4567` (cache invalidation at worker entry) fully fixed it or if there's a remaining case.
3. Add busy indicator UX: disable button on click, show spinner, poll job status, re-enable on success.
**V1:** T23.
**V2:** new `test_bb_balance_after_edit` — modify Verbrauch, trigger balance, verify job runs to completion.
**V3:** `/api/ws/balance-job/<id>/` returns progress; status advances.
**V4:** Playwright — edit Verbrauch, click Balance Solar, verify spinner appears + job completes.
**V5:** Same, Heroku. **This is the primary acceptance gate** — the original report was on the deployed app.
**V6:** `CLAUDE.md` if new invariant discovered.

### 4-E. Auto-cascade (Excel-style propagation) on every change — `T24`, `T25`, `T26`, `T27`

**Source:** §2.4.4. PDF complaint: users are forced to switch to the Erneuerbare page and press "Recalculate Renewables" after every Verbrauch edit; Excel does this cascade automatically on every change.

**Crucial distinction:** this is **cascade propagation** (change in cell A → dependent cells refresh), **not** auto-Balance. Balance (§2.4.3) stays manual with two buttons (Solar / Wind). 4-E only removes the manual "Recalculate Renewables" step; it never triggers a Balance job.

**Files:** Verbrauch / Renewable / LandUse save handlers (`save_and_recalculate_verbrauch` already does this for one surface); frontend JS for the three input pages.

**Approach:**
- Extend the existing `save_and_recalculate_*` pattern to fire on every user save across all three surfaces.
- **Debounce** on the frontend so rapid typing doesn't spam the backend (200 ms typical).
- The cascade is cheap (milliseconds — formula-evaluator walk, not a Balance run). No async worker required.
- Remove the manual "Recalculate Renewables" button (or gate behind an admin-only "force refresh" toggle).
- UI feedback (T27): briefly show "Aktualisiert" after each save so the user sees the cascade ran.

**Non-goal (explicitly):** do NOT auto-trigger Balance on edits. Balance runs only when the user clicks Balance Solar or Balance Wind.

**V1:** T24, T25, T26, T27.
**V2:** `test_bb_e2e_auto_cascade` — edit every input field type, verify downstream computed cells update without any explicit button click, and without a Balance job firing.
**V3:** API trace confirms one cascade call per user save; `BalanceJob` table is untouched.
**V4:** Playwright — edit Verbrauch target, navigate to Erneuerbare, confirm the linked cells reflect the change with no intermediate button press.
**V5:** Same, Heroku.
**V6:** `CLAUDE.md` — document the cascade-vs-Balance distinction.

---

## 10. Phase 5 — Chart rework

### 5-A. Rich results overview — `T43`, `T44`, `T45`, `T46`, `T47`

**Source:** §2.5.4 — Status + Target side-by-side with per-sector breakdown, left/right columns per Excel AH.Cockpit1.
**Files:** new `simulator/templates/simulator/cockpit.html` (redesign) + JS; backend may need a new API returning Status+Target pairs per sector.
**Approach:**
1. Spec the exact chart from the Excel reference (PDF page 8).
2. Chart.js with horizontal stacked bars; left pane demand, right pane supply.
3. % delta annotations as data labels.
**V1:** T43–T47.
**V2:** API returns expected shape; unit test for data serializer.
**V3:** Shape compared to spec.
**V4:** Playwright screenshot diff vs. committed reference.
**V5:** Same, Heroku.
**V6:** `docs/stakeholder/` — sub-spec for cockpit redesign.

### 5-B. Improve annual H₂ storage chart — `T57`, `T58`, `T59`, `T60`

**Source:** §2.5.7 — show Min/Max/Capacity, daily surplus/deficit stacked, Mangelausgleich, Tagesladung unit.
**Files:** `simulator/templates/simulator/jahresstrom.html` (or wherever Jahresgang is rendered), JS chart config.
**Approach:**
1. Y-axis annotation of Min/Max/Kapazität = Max − Min.
2. Secondary stacked bar series: daily solar surplus, wind surplus, solar deficit, wind deficit, Mangelausgleich.
3. Unit switch: compute `Tagesladung = annual_consumption / 365`, show as TL/day.
**V1:** T57–T60.
**V2:** `test_ws365_formulas` still passes (golden values unchanged, only display logic differs).
**V3:** API returns daily deltas (new field maybe).
**V4:** Playwright — screenshot diff vs. reference.
**V5:** Same, Heroku.
**V6:** —

### 5-C. Fix electricity/H₂ flow diagram — `T53`, `T54`, `T55`, `T56`

**Source:** §2.5.6 — wrong value assignments, small font, doesn't match Excel structure.
**Files:** current flow-diagram component (identify during audit), reference data on `/annual-electricity/`.
**Approach:**
1. Node-by-node audit (T53): list every node in Excel reference (PDF page 10) and every node in current implementation; map correspondence.
2. File a bug per mismatch. Fix in order of severity.
3. Font: CSS zoom or SVG viewBox rescaling.
**V1:** T53–T56.
**V2:** new `test_bb_flow_diagram_nodes` checking each expected node + value is present in the API response.
**V3:** API returns all expected flow edges.
**V4:** Playwright — screenshot diff + DOM assert of node labels.
**V5:** Same, Heroku.
**V6:** —

---

## 11. Phase 6 — History + details

### 6-A. Modification history — `T61`, `T62`, `T63`

**Source:** §2.5.8 — step-by-step log of modifications, currently entirely missing.
**Files:** new `simulator/models.py::ModificationHistoryEntry`, migration, new template + view.
**Approach:**
1. Model: `{scenario, timestamp, user, field_path, before_value, after_value, balance_triggered_by, balance_result_snapshot}`.
2. Signal or wrapper on every user-save writes a history row.
3. UI: new tab on Cockpit or dedicated `/historie/` page — table with parameter rows, snapshots as columns (matches Excel AH.Monitor layout, PDF page 12).
4. Inspectable, but not time-travel-restorable in this iteration (too risky; handle in later iteration if asked).
**V1:** T61–T63.
**V2:** new `test_bb_history_logging` — perform N edits, verify N rows exist.
**V3:** `/api/history/` returns expected shape.
**V4:** Playwright — edit 3 params in sequence, open history page, verify 3 rows with correct before/after.
**V5:** Same, Heroku.
**V6:** —

### 6-B. Modification-detail variant comparison charts — `T48`, `T49`, `T50`, `T51`, `T52`

**Source:** §2.5.5 — 5 distinct chart types from Excel AH.Cockpit2 (PDF page 9).
**Files:** new `/modifikationsdetails/` page; 5 chart components.
**Approach:**
1. Requires persisting **Vorzustand** snapshot (previous-state) in addition to current. Piggyback on 6-A's history infrastructure.
2. Each chart = grouped horizontal bars with 4 series (Status / Basisszenario / Vorzustand / Aktueller Zustand).
3. Build one, then clone pattern for the other four.
**V1:** T48–T52.
**V2:** API returns 4-series data per sector; unit test.
**V3:** —
**V4:** Playwright — screenshot diffs vs. references for each of 5 charts.
**V5:** Same, Heroku.
**V6:** —

---

## 12. Phase 7 — Acid test + handover

### 7-A. Hosting handover — `T1`, `T2`, `T3`, `T4`

**Source:** §2.1.
**External gate:** ErnES picks a compute platform. Until then we wait.
**Deliverables:**
1. Platform-agnostic deploy runbook in `docs/HEROKU.md` (already exists) + a generic `docs/DEPLOY.md` that works for any Docker-compose-capable platform.
2. 2× ErnES admin onboarding sessions (live handover, with video).
3. Credential recovery procedure documented (T4): how to reset a lost superuser, reset testsim, regenerate `DJANGO_SECRET_KEY`, etc.

### 7-B. Acid test on ErnES platform — `T5`, `T6`, `T7`

**Source:** §2.2.
**Deliverables:**
1. Run `scripts/bench_acid_test.sh` against ErnES's deployed URL.
2. Report: platform specs, response time (s), delta vs. Excel 5.8 s. The PDF uses the word **"praxistauglich"** (practically usable) as the success criterion — it does NOT fix a numeric target. Success threshold must be confirmed with Schmidt-Kanefendt before the run.
3. If the result is not "praxistauglich": trigger the architecture review §2.2 explicitly calls for → revisit `docs/PYPSA_MIGRATION_RESEARCH.md` integration plan.

---

## 13. Deferred — Data model (§2.3 of the PDF)

**Status:** not on the current plan. Pascal has the source Excel files but this needs its own scoping session before being pulled in.

**Targets (still tracked, still owed to the stakeholder):**

- **T8, T9, T10** (§2.3.1) — parameter traceability: each value in the UI links back to its source reference and underlying assumption (like Excel's hyperlinked cells). Admin can update without code.
- **T11, T12, T13** (§2.3.2) — alternative regions: Bundesländer scenarios, data loaded from Excel files (`D.xlsx` and variants), admin-uploadable without code changes.

**Why deferred:**

- The stakeholder phrased §2.3 as a **Vorschlag** (proposal), not a must-have. Reading tone: this is the ambitious long-term direction, not the near-term blocker.
- It is architecturally the largest change on the list — touches import pipeline, data model, formula engine access patterns, and scenario/region concepts. Sizing it honestly is 2+ weeks minimum.
- Before starting we need to:
  1. Confirm with Schmidt-Kanefendt which Excel files are current and authoritative.
  2. Decide between Options A (one-time import + source metadata), B (live Excel binding), C (hybrid — import + `source_excel_path` per row). `NEXT_CHANGES.md` §P4-1 has a first-pass analysis.
  3. Write a dedicated spec (`docs/stakeholder/DESIGN_DATA_MODEL.md`) and review it with Pascal before touching code.

**Re-entry:** when Pascal is ready, open the scoping session and promote T8–T13 back into the main plan as a new phase (likely 8 or 9 at that point). Until then, no code work on this.

---

## 14. Risk register

| Risk | Probability | Mitigation |
|---|---|---|
| Auto-cascade (4-E) fires too often or in a missing-save path, producing wrong displayed values | Low–Medium | Debounce on frontend; V2 test covers "one cascade per save, no Balance fired"; V5 catches Heroku-only regressions. |
| Translation breaks layout (long German words overflow columns / buttons) | Low | Playwright screenshot diff per page catches overflow; tweak CSS widths as needed. |
| History model (6-A) explodes DB size on Heroku `essential-0` plan | Medium | Cap history at N rows per scenario (e.g. 500), auto-purge oldest on overflow, purge on baseline reset. |
| Cross-process cache bug re-emerges with auto-cascade (4-E) or button consolidation (4-C) | Medium | V5 (Heroku Playwright) per phase is mandatory. Pre-existing fix `54d4567` should hold but re-verify. |
| "Balance buttons currently already auto-run Goal Seek / Refresh" assumption is wrong — removing 1-B buttons breaks Balance | Medium | 1-B precondition is explicit verification: trace the code path first; if auto-run is NOT in place, either add it before removing buttons, or leave 1-B until 4-C (Balance consolidation) adds the orchestration. |
| "Save All Values" (T28) is actually doing something that `Scenarios → Save` does NOT cover | Low | Read both code paths side-by-side before deletion. If unique semantics exist, don't delete — ask Pascal. |
| Acid test on ErnES platform fails and "praxistauglich" threshold is not agreed | Medium | Confirm target with Schmidt-Kanefendt BEFORE running — so "pass/fail" is unambiguous. |
| Deferred data-model work (§2.3) gets forgotten | Low | T8–T13 stay in the target map and `PROGRESS.md` with ⏸ status. Reviewed at every phase boundary. |

---

## 15. Progress tracking

Live checkbox grid lives in `PROGRESS.md` (Phase 0-A). This plan doc is the spec; `PROGRESS.md` is the burndown.

Commit convention: `<type>(stakeholder-<phase>-<item>): <summary>` — e.g. `fix(stakeholder-1-A): remove Save All Values button (T28)`.

---

## 16. What changes in our workflow (updates to CLAUDE.md)

After Pascal approves this plan, the following update lands in `CLAUDE.md`:

- New section "Stakeholder implementation plan" pointing at this file as source of truth.
- New rule: "Any commit that advances a target must reference `T*` in the subject line".
- New rule: "Phase V5 (Heroku Playwright) requires `bash scripts/heroku_up.sh` at phase start + `heroku_down.sh` at phase end. Don't spin up per item."
