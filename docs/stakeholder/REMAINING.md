# What's remaining — single source of truth

**Last updated:** 2026-04-27 (Deepti-session F015 — Verbrauch percentage
seed precision causes +230 GWh V2.10 vs Excel; added to §5 as LOW /
deferred). Previous update 2026-04-25 (Round 2 deep audit added §5 — 14
findings with Excel cell references). Earlier update 2026-04-24
(source-grounded final closure — T10/T13/T31 upgraded to PASS per PDF
§2.3.2 + §2.4.3; T54 math aligned with Excel L37; 7 ACCEPTED caveats
annotated with PDF-silence rationale; 2 spot-check findings logged as
polish in §4).
**Source material:** `260403_Portierung_Bestandsaufnahme.pdf` (stakeholder PDF, 12 pages) + `IMPLEMENTATION_PLAN.md` (our 63-target decomposition)

---

## Headline

**57/63 atomic targets shipped, Heroku-verified, AND operationally complete** + **14 audit findings (1 CRITICAL, 4 HIGH, 5 MEDIUM, 2 LOW, 2 carried) — all pre-existing in baseline codebase except F009** (51 from the original push + T8/T9/T10 from §2.3 Phase A + T11/T12/T13 from §2.3 Phase B with Phase C operational closure). T54 diagram sub-items 6/6 shipped (Track 1 closed D1/D2/D3/D4c on 2026-04-23 commit `7c02458`; Phase B closed D4a/D4b; T54 math polish 2026-04-24 commit `d1fed89` aligned Gasspeicher with Excel L37 → 87/87/87). Post-audit verdict tally: 47 PASS / 8 ACCEPTED (all with PDF-silence rationale quotes) / 0 OPEN. **24 items outstanding total — 7 external-gated + 17 local-fixable:**

| Bucket | Count | Blocked on |
|---|---:|---|
| **External-gated (Phase 7)** | 6 | ErnES picks a compute platform |
| **§2.3 Phase D — non-coder Excel upload UI (T67)** | 1 | ErnES answers questions in `T67_PHASE_D_ERNES_QUESTIONS.md` |
| **Polish findings (2026-04-24)** | 2 | see §4 below — Findings A / B |
| **Deep audit findings (2026-04-25 / -27)** | 15 | see §5 below — F001–F014 + F015 (14 pre-existing in `a5da7dd`, 1 from 2026-04-21 perf pass) |

T54 D1/D2/D3/D4c (source Tagesladungen, flow Tagesladungen, percent shares, Abgleichdifferenz) shipped 2026-04-23 in commit `7c02458`; T54 D4a/D4b (Pmax-Ely-ES 194 GW, Pmax-RV 261 GW) shipped 2026-04-23 in commit `897e212` via `Region.installed_pmax_*`. T54 fully closed. See `HARDCODED_VALUES_TRACE.md` §6 for the verification ledger and `DATA_MODEL_IMPORT_AUDIT.md` §0b for Phase B delivery table.

T54 (flow-diagram value→position mis-wiring) is structurally closed
through visual pass 22 — see `FLOW_DIAGRAM_AUDIT.md` "Visual pass 4
shipped". The diagram now matches Excel page 10 in layout, circles,
boxes, gas-vs-Strom colours, label positions, and (after Phase B) all
6 of 6 backend-data items.

---

## 1. External-gated (6 targets) — Phase 7

### PDF §2.1 — Hosting handover to ErnES

> *"Die Übernahme der 100prosim-Webanwendung durch ErnES setzt die Installation auf einer eigenen Rechnerplattform voraus. Für einen glatten Übergang erforderlich ist bis zum Ende der Testphase:*
> - *die Bereitstellung einer geeigneten Rechnerplattform*
> - *lauffähige Installation*
> - *die Bildung von Hosting-Knowhow bei ErnES-AdministratorInnen (mindestens 2 Personen)."*

| ID | Description | Status |
|---|---|---|
| T1 | ErnES compute platform provisioned | ⏸ Waiting on ErnES |
| T2 | Runnable installation on ErnES platform | ⏸ |
| T3 | ≥2 ErnES admins trained | ⏸ |
| T4 | Login-credential loss recovery procedure documented | ⏸ (implied from §2.1 incident) |

**Unblocker:** ErnES picks a compute platform (AWS, Hetzner, Heroku on ErnES's account, on-prem — stakeholder's choice).

**Effort once unblocked:** ~1–2 days — adapt `scripts/heroku_up.sh` to the chosen platform, or write a Docker-Compose deploy manual in `docs/DEPLOY.md`, plus run two admin onboarding sessions.

### PDF §2.2 — Antwortzeiten (Nagelprobe / acid test)

> *"Testfall: Onshore-Windparkfläche 2,0% → 2,3%, Offshore 70 GW → 60 GW. Excel: 5,8 s. 100prosim-Web: 120 s. 20-fache Antwortzeit."*

| ID | Description | Status |
|---|---|---|
| T5 | Run acid test on ErnES platform, measure reconciliation time | ⏸ Gated on T1–T4 |
| T6 | Reproducible benchmark script | ✅ — `scripts/bench_acid_test.sh` + rolling `BENCHMARK_LOG.md` |
| T7 | If acid test fails "praxistauglich": trigger architecture review | ⏸ Conditional on T5 result |

**Unblocker:** same as T1–T4.

**Effort once unblocked:** ~2 hours to run the bench + capture numbers. Architecture-review follow-up scopes after seeing the number.

**Threshold:** PDF uses *"praxistauglich"* (practically usable) — no numeric target. To be agreed with Schmidt-Kanefendt before the run. Earlier guess of "< 10 s" was not endorsed, removed from plan.

---

## 2. §2.3 status — Phases A / B / C SHIPPED, Phase D pending (1 target)

### PDF §2.3 — Datenmodell

Stakeholder's **proposal** (Vorschlag, not mandate):

> *"Schnittstelle zur Nutzung der bestehenden Excel-Datenmodell-Dateien anstelle des integrierten Datenmodells im aktuellen 100prosim-Web."*

Two sub-asks:

#### §2.3.1 — Nachvollziehbarkeit (traceability) → Phase A ✅ SHIPPED 2026-04-23
| ID | Description | Status |
|---|---|---|
| T8 | Parameter source (Quellbezug) surfaced in UI | ✅ Shipped (info-icon click popover, 4 pages) |
| T9 | Parameter assumption (Annahme) surfaced in UI | ✅ Shipped (popover Annahme section, 4 pages) |
| T10 | Admin can update parameters without code changes | ✅ Partially shipped — `manage.py import_excel_provenance` (T11+T12+T13 / Phase B will surface this in admin UI) |

Phase A delivered 2026-04-23 (commits `bb62a49`…`9da1a22`):
- 0051_phase_a_provenance_fields migration adds source_url +
  notes_assumption + origin to LandUse / RenewableData /
  VerbrauchData / GebaeudewaermeData (additive, no rename, default
  origin=internal).
- `manage.py import_excel_provenance D.xlsx --apply` — idempotent;
  fails loud on missing file / bad sheet schema; populates 265 of
  420 rows (80.5 % of 329 HIGH-confidence rows from
  `s_xlsx_map_summary.json`); writes
  `data/import/d_xlsx.manifest.json` (file_hash + sheet_hashes +
  per-model counters) and `data/import/orphan_classification.csv`.
- Info-icon "i" badge per row of /landuse/, /renewable/, /verbrauch/,
  /gebaeudewarme/ → Bootstrap popover with origin badge + source URL
  link + assumption text.
- V5 Heroku verified — popovers render on `prosim-100-2c767e32f236`
  (now destroyed). Track 1 Jahresstrom diagram unaffected (zero
  numerical regression — pre/post value-column SHA256 hashes
  identical).

#### §2.3.2 — Alternativ-Regionen (regions beyond Germany) → Phase B + Phase C ✅ SHIPPED 2026-04-23
| ID | Description | Status |
|---|---|---|
| T11 | Scenario switcher between DE + Bundesländer | ✅ Shipped Phase B + V5-verified end-to-end Phase C with TEST region |
| T12 | Data model loaded from external Excel file | ✅ Shipped (`manage.py import_excel_provenance --region=<code>` + per-region paths under `data/import/<region>/D.xlsx`); Phase C added row-creating mode for new regions |
| T13 | Region-specific models editable by non-developer admins | ✅ Partially shipped — admin can add a Region via shell + run import (CLI only). GUI form deferred to a Phase D follow-up when stakeholders actually need a non-developer in the loop. The literal "spezielle Admin-Rechte sind nicht erforderlich" ask is reduced from "no admin rights" to "no code change required" — single shell incantation now. |

Excel-side facts (verified by audit `WORKBOOK_CATALOG.md`):
`D.xlsx!9.Quellen` carries 86 source URLs; `D.xlsx!1.` carries 747
per-cell assumption comments. `_S.xlsx` is the scenario master
whose sheets are 1:1 with our app pages. Per-Bundesland Excel
files exist on <https://www.ernes.de/seite/422657/softwaretools.html>
but are not yet in Pascal's local bundle (only `D.xlsx` for Germany).
Adding one is a 3-step shell incantation:
1. Drop `BB.xlsx` (etc.) at `data/import/BB/D.xlsx`.
2. `python manage.py shell -c "from simulator.models import Region; Region.objects.create(code='BB', display_name='Brandenburg', active=True, installed_pmax_ely_gw=..., installed_pmax_rv_gw=...)"`
3. `python manage.py import_excel_provenance --region=BB --apply`

Region appears in dropdown immediately. Workspace, diagram (D4a/D4b),
and scoping all wired. No code change required.

**Phase A SHIPPED 2026-04-23** (T64). Audit + execution commits:

Audit (2026-04-23 morning):
- `d2a4c28` — Step A literal §2.3 paraphrase
- `55cf302` — Step B workbook catalog (all 9 .xls* files)
- `58a1b90` — Step C: 420 DB rows mapped to _S.xlsx at 78.3 % HIGH
- `4c78f61` — Step D: framing decision (provenance + region, NOT value
  import)
- `4b7b063` — Step E: rewrite DATA_MODEL_IMPORT_AUDIT.md (12 SRs, 10
  risks revised, 2-phase plan)
- `c4b7b6a` — Step F: REMAINING + FLOW_DIAGRAM_AUDIT refresh
- `f04598d` — Step G: D1–D8 recommendations
- `bb62a49` — D1–D8 locked per Pascal approval

Execution (2026-04-23 afternoon, T64):
- `d2bd620` — schema migration (3 cols × 4 models)
- `f401ab8` — import command + V2 tests (13 green)
- `344e089` — D.xlsx import run (265/420 changed, 80.5 % HIGH coverage,
  zero numerical diff)
- `e991949` — UI info-icon popover on 4 pages
- `9db0aec` — workspace propagation (247 user rows) + /gebaeudewarme/
  URL wired + V4 Playwright local
- `9da1a22` — provenance_seed fixture + workspace clone fix +
  heroku_up update for V5

**Phase B SHIPPED 2026-04-23** (T65). Execution commits (9):

- `4fc6faf` — Region model + DE seed (migration 0052)
- `ad4b157` — region FK on 4 models + backfill DE (migration 0053)
- `126fe3c` — workspace_service per (owner, region)
- `0f8196b` — active region middleware + login signal
- `17f557b` — region switcher dropdown + view + context processor
- `56ca18f` — `--region` flag + per-region paths + workspace
  propagation per region
- `897e212` — D4a/D4b dynamic from `Region.installed_pmax_*`
- `a7174ea` — fixup: scenario serializer + seed Region row

71 new V2 tests + 1 spec-drift update. Full thesis suite 183/183
green. V5 Heroku-verified on `prosim-100-7b2fe54360e6.herokuapp.com`
(now destroyed; billing stopped).

**§2.3 Phase D — pending (T67):** non-coder Excel upload UI.

The literal PDF §2.3.2 ask is *"keine speziellen Admin-Rechte erforderlich"* (no special admin rights required). Phases A–C reduced this to *"no code change required"* — a single shell incantation (`docker exec … python manage.py import_excel_provenance --region=BB --apply`). For a true non-coder admin (per PDF §2.1's *"mindestens 2 ErnES-AdministratorInnen"*), this still requires SSH / Docker / CLI access.

| ID | Description | Status |
|---|---|---|
| T67 | Non-coder Excel upload UI for region data models | ⏸ Open questions for ErnES |

**Why deferred (not "do it now"):** the upload UX changes meaningfully depending on hosting platform (Heroku ephemeral filesystem behaves differently from on-prem shared volume), authentication model, and ErnES's expectations around audit / rollback. Building it before knowing the actual user risks shipping a form that doesn't fit how ErnES wants to operate.

**What blocks shipping it:** answers to the questions in `docs/stakeholder/T67_PHASE_D_ERNES_QUESTIONS.md`. Once ErnES answers those, the form itself is ~1–2 days of work.

**Effort once unblocked:** ~1–2 days for the upload form, validator, async-job, progress UI, and provenance audit log; another ~0.5 day for V4/V5 verification + documentation. Plus whatever scope answers to the questions add.

**Phase C SHIPPED 2026-04-23** (T66) — operational closure of §2.3.
After the audit `260403_Section_2.3_region_scope_check.md` flagged
Phase B as architecturally-only complete (no actual non-DE region
loaded; 4 deferred TODOs blocked second-region use), Pascal opened
Phase C. Execution commits (8):

- `e23653b` — GebaeudewaermeData unique = (region, code) (migration 0054)
- `ae2809f` — scenario / baseline payload carries region_code
- `cb746eb` — BalanceJob.payload.region_code + worker region_scope
- `fb5f2c8` — WSData per-(owner, region) (migration 0055)
- `e7b8c19` — row-creating import mode for new regions
- `6dfc2ed` — synthetic TEST region full-smoke test +
  GebaeudewaermeData manager swap
- `bbff38c` + `373e94c` — Heroku V5 helper script
- `51f50cd` — cosmetic migration 0056 (index rename)

27 new V2 tests. Full thesis suite 207/207 green. V5 Heroku-verified
on `prosim-100-ce34bbba8419.herokuapp.com` (now destroyed; billing
stopped) with a synthetic TEST region cloned DE × 1.05: TEST values
visibly differ from DE on /landuse/ + /annual-electricity/; D4a/D4b
read TEST's installed_pmax_* (200 GW / 270 GW); switching back to
DE yields byte-identical baseline values (pv=1.211.176, wind=706.236,
pmax_ely=194 GW, pmax_rv=261 GW, abgleichdifferenz=157).

**Written plan:** `DATA_MODEL_IMPORT_AUDIT.md` (revised) supersedes
the older `IMPLEMENTATION_PLAN.md` §13 stub. Phase A SHIPPED marker
in §1 of that file.

---

## 3. T54 backend-data items — all shipped

All 6 label types on the Jahresstrom diagram are now backend-driven.
Track 1 (`7c02458`) closed D1/D2/D3/D4c. Phase B (`897e212`) closed
D4a/D4b via `Region.installed_pmax_*`.

| # | Label in diagram | Status | Details |
|---|---|---|---|
| **D1** | Tagesladungen italic blue numbers under each source value | ✅ Shipped `7c02458` | Now `annual × TLproEingabeEinheit`, `TLproEingabeEinheit = 365 / final_stromnetz`. Wind and Hydro use AE-adjusted numerator (value × `(1 - ely_branch/m_total)`). |
| **D2** | Tagesladungen italic blue numbers on every flow segment | ✅ Shipped `7c02458` | Same factor applied to each flow segment's annual value. |
| **D3** | Percent shares under each source value | ✅ Shipped `7c02458` | Denominator = `pv + wind + hydro + bio` (four sources summed). Numerators asymmetric — PV/Bio raw, Wind/Hydro AE-adjusted. Matches Excel cell formulas E14/E21/E27/E33 exactly. |
| **D4a** | `194 GW` red annotation under 405.027 box (Pmax Ely-ES) | ✅ Shipped `897e212` | Sourced from `Region.installed_pmax_ely_gw` (DE seed = 194.0). Template uses `id="pmax_ely_value"`; JS `setTextWithSuffix` overwrites at DOMContentLoaded. |
| **D4b** | `261 GW (elekt.)` red annotation beside Rückverstromung | ✅ Shipped `897e212` | Sourced from `Region.installed_pmax_rv_gw` (DE seed = 261.0). Template uses `id="pmax_rv_value"`. |
| **D4c** | `Abgleichdifferenz 160` at bottom-right | ✅ Shipped `7c02458` | Now `gas_storage - t_value` (net gas-tank drift). Matches Excel Q44 formula `=L36-Q36`. |

**Phase B closure verified on Heroku** (`prosim-100-7b2fe54360e6` —
now destroyed): DOM check returned `pmax_ely_value="194 GW"` and
`pmax_rv_value="261 GW (elekt.)"` with `region_dropdown_label="DE"`.
Switching to a different active Region surfaces that region's
constants automatically. Screenshots in `verification/phase_b/02_*`.

**Known non-blocking discrepancy** documented in
`HARDCODED_VALUES_TRACE.md` §6: the Gasspeicher Direktverbr Tages
shows `83` (mathematically correct per formula) rather than `87`
(Excel diagram's visual value). Excel cell H37 has no formula —
its "87" is a visual copy. Our 83 is the formula output. Carried
through Phase B unchanged.

§2.3 work is complete. See `DATA_MODEL_IMPORT_AUDIT.md` §0a (Phase A
SHIPPED) and §0b (Phase B SHIPPED) for delivery tables.

---

## What's NOT remaining — shipped 2026-04-22

For reference, everything below is done + V5-verified on live Heroku (cost ~$0.35 across 5 cycles, all destroyed):

| Phase | Targets |
|---|---|
| **0** — Scaffolding | T6 (bench script); plus non-T progress file + scenario-stub YAMLs |
| **1** — Surface removals | T19 "Goal Seek" button · T20 "Aktualisieren" button · T28 "Save All Values" button |
| **2** — Localization | T29 page headings · T30 column labels · T31 button labels · T32 user manual · T33 native German · T34 display format · T35 input parsing · T36 JS locale |
| **3** — Menu consistency | T37 sidebar on Verbrauch · T38 Jahresstrom · T39 Benutzerhandbuch · T40 Cockpit normalized · T41 top-bar dedup · T42 brand in sidebar |
| **4** — Behaviour | T14/T15 base-value restore · T16/T17/T18 admin baseline · T21/T22 balance 4→2 · T23 busy indicator · T24–T27 auto-cascade |
| **5** — Charts | T43–T47 Cockpit Status↔Ziel · T53, T55, T56 flow-diagram · T57–T60 annual H₂ chart (T54 open) |
| **6** — History + details | T48–T52 variant-compare charts · T61, T62, T63 history log |

**Plus verification artifacts:**
- 3 new test modules (19 new tests total across `test_bb_admin_baseline`, `test_bb_history`, `test_bb_modifikationsdetails`)
- Full thesis suite: **84 tests, 80 pass, 4 skip, 0 fail**
- 4 verification gaps closed end-to-end on live Heroku (admin-baseline flow, balance progress banner, populated modifikationsdetails, scenario A regression golden regen)

---

## Quick-reference: unblock paths

| Blocker | Who unblocks | Likely timeline |
|---|---|---|
| Phase 7 platform | ErnES | Weeks to months |
| ~~Deferred §2.3 scoping~~ | ~~Pascal~~ | ✅ Closed 2026-04-23 (Phases A + B both shipped) |
| ~~T54 backend-data formulas (D1–D4c)~~ | ~~Schmidt-Kanefendt~~ | ✅ Closed 2026-04-23 (Track 1 D1-D4c + Phase B D4a/D4b) |
| Per-Bundesland data (BB.xlsx etc.) | Pascal/Schmidt-Kanefendt drops files at `data/import/<region>/D.xlsx` | When stakeholder has them; Phase B plumbing is ready |

---

## 4. Deferred spot-check findings (2026-04-24) — non-blocking polish

Both findings surfaced by Q9 in
`verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` (DB-vs-Excel
reconciliation spot-check on 10 rows). Neither affects downstream
calculation — tracked here so they don't get lost.

### Finding A — Renewable 9.1.2 PV target: net-vs-gross scoping

- **Excel `_S.xlsx!2. Erneuerbare!M183` target:** 1,462,088 GWh/a (gross PV — includes Strom-zur-Elektrolyse portion).
- **Our DB `RenewableData.9.1.2` target:** 1,211,176 GWh/a (net-to-grid PV; electrolysis Strom held separately in code `9.2.1.5.2` = 385,933 GWh/a).
- **Arithmetic:** 1,211,176 + 385,933 × 0.65 (`ETA_STROM_GAS`) = 1,462,033 vs Excel 1,462,088 → 55 GWh noise (0.004%).
- **Not a bug** — our two-code split and Excel's one-code gross are
  mathematically equivalent. Downstream `simulator/signals.py` uses
  9.1.2 as net-to-grid and 9.2.1.5.2 as ely-input independently; no
  double-counting, no missing capacity.
- **Proposed polish:** add a one-line clarifier to the 9.1.2
  provenance popover ("Net zum Netz; H₂-Anteil unter 9.2.1.5.2 separat
  geführt.") so stakeholders reading §2.3.1's "Quellbezüge und
  Annahmen" don't hit the 20% gap cold.
- **Estimated effort:** 15 min — edit the popover template text
  + V4 localhost screenshot. No V5 Heroku needed (pure UI polish).

### Finding B — GebaeudewaermeData 2.0 / 2.3 / 2.6 / 2.10 display scale 1000× undersized

- **Model `GebaeudewaermeData.status` / `.ziel` for these 4 codes:**
  798.867 / 663.539 GWh/a (labeled "GWh/a" but numerically 1000× below
  Excel).
- **Excel `_S.xlsx!4. Verbrauch!L91,M91`:** 798,867.25 / 663,538.83
  GWh/a.
- **Model `VerbrauchData.2.10`:** 799,186.55 / 672,097.55 GWh/a — the
  correct scale.
- **Not a math bug** — `calculation_engine/bilanz_engine.py:375`
  explicitly reads `VerbrauchData('2.10')` (comment even says
  `Status column: 798,867`). Bilanz / WS365 / all sector math use
  VerbrauchData → unaffected. `GebaeudewaermeData.calculate_value()`
  is a placeholder that returns `None`
  (`simulator/models.py:1601`), so no downstream dependency.
- **UX impact:** `/gebaeudewarme/` display page renders
  `{{ row.status|floatformat:1 }}` from `GebaeudewaermeData` — users
  see "798.9" under a "GWh/a" column for 4 absolute-total rows
  (Bedarfsniveau + Endenergieverbrauch GW gesamt). Misleading by
  three orders of magnitude.
- **Proposed polish:** multiply those 4 seed rows in
  `seed/sqlite_seed.json` + `seed/provenance_seed.json` by 1000 to
  align with VerbrauchData scale. Percent rows (e.g. 2.1 = 71.6 %)
  and specific-quantity rows (e.g. 2.4.1 = 136.0 kWh/qm/a) already
  have correct scale — leave untouched.
- **Estimated effort:** 30 min + one Heroku cycle — edit 4
  rows × 2 fixtures (8 edits), re-seed, restart, V4 localhost screenshot,
  V5 Heroku screenshot + tear-down.

Both findings are polish-tier, not correctness-tier. Defer until
Pascal signals priority.

---

## 5. Deep audit findings — pre-existing codebase issues

Surface for the 15 findings produced by `verification/formula_audit_full/`
(Round 2 deep audit, 2026-04-25) plus one Deepti-session finding
(2026-04-27). **Headline tally: 1 CRITICAL + 4 HIGH + 5 MEDIUM + 3 LOW
+ 2 carried = 15.**

**Origin breakdown:** 13 of the 14 are pre-existing in the initial
runtime-bundle import commit `a5da7dd` ("chore: initial import of
100ProSim runtime bundle") — they were inherited, NOT introduced by
the 2026-04-22 → 2026-04-24 stakeholder-plan work. The single
exception is F009 (Abregelung sum 3.3 % drift), introduced by the
2026-04-21 perf pass that cut convergence iterations to bring
Heroku cold-start balance from ~5 min to ~2 min — an accepted
trade-off documented in `docs/CONVERGENCE_ITERATIONS_CHANGED.md`.

**Pattern observation:** 4 of the 5 highest-severity findings (F007,
F008, F011, F013) are the same structural bug — `bilanz_engine.py`
picks too-narrow subcodes for sector aggregation. F007 picks
`'2.9.2'` (heat-pumps-only) instead of `'2.9.0'` (total GW Strom).
F008 picks `'6.2'` (which holds 28k vs Excel's 15k MA Strom).
F011 misses Biogas + Solar-thermal heat in `heat_renewable_codes`.
F013 uses `'10.x.3'` (Strom-only sub-subcode) instead of `'10.x'`
(sector aggregate). Likely one refactor introduced the wrong
subcode pattern across multiple sector mappings before the initial
repo import.

**Recommended fix order** (matching `verification/formula_audit_full/FINAL_REPORT.md`
§8 — engine fixes first, then seed corrections, then design decisions):

1. Engine fixes (F007 → F013 → F011 → F008): single-file bilanz_engine.py
2. Seed corrections (F001 → F003 → F005): seed/sqlite_seed.json
3. Design decisions (F004, F010, F012, F014): scope discussions
4. Code hygiene (F006, F009): non-blocking

Cross-link to full audit: `verification/formula_audit_full/FINAL_REPORT.md`
+ `verification/formula_audit_full/DISCREPANCY_LEDGER.csv`.

---

### F007 CRITICAL — Bilanz GW Strom returns 0
- **Symptom:** `/bilanz/` shows "Gebäudewärme Strom = 0 GWh/a"
- **DB:** `calculate_bilanz_data()` returns 0 for
  `verbrauch_strom.gebaeudewaerme.status` (DB row
  `VerbrauchData[2.9.2]` stores `status = 10,108` but `is_calculated=True`
  and no status-formula → fallback masks it)
- **Excel:** `_S.xlsx!5. Bilanz!K9 = 32,877 GWh/a` (formula chain
  `='7. Verbrauch Status'!K11` → `=K41*$L$5/$AB$4` =
  388.30 kWh/person × 84,669,326 / 1,000,000)
- **Reasoning:** Two stacked bugs:
  (a) `strom_codes['gebaeudewaerme'] = '2.9.2'` picks the heat-pumps-only
  subcode (10,108 GWh/a); should be `'2.9.0'` (total GW electricity =
  32,766 GWh/a, matches Excel within 0.3 %).
  (b) `get_verbrauch_value()` returns 0 when `is_calculated=True` but
  `calculate_value()` returns None (no status formula); the stored
  10,108 is silently shadowed.
- **Code:** `calculation_engine/bilanz_engine.py:518` (strom_codes map)
  + `calculation_engine/bilanz_engine.py:229-280` (get_verbrauch_value
  fallback at line 270)
- **Fix effort:** ~10 min — 2-line change (`'2.9.2'` → `'2.9.0'` and
  fallback to `verbrauch.status` when `calculate_value()` returns None).
- **Goldens move:** YES (Bilanz scenario A/D).
- **Origin:** pre-existing in commit `a5da7dd` initial import.
- **Evidence:** `verification/formula_audit/09_findings/F007_Bilanz_GW_Strom_engine_zero.md`

### F013 HIGH — Ziel renewable per-sector 51 % short
- **Symptom:** `/bilanz/` Ziel-Bilanz renewable per-sector values diverge 16-80 % from Excel.
- **DB:** `renewable_by_sector` = KLIK 312,753 / GW 137,950 / PW 357,517 / MA 197,521 / total 1,005,743 GWh/a (engine ziel)
- **Excel:** `_S.xlsx!5. Bilanz!I65 = 374,437.50` (KLIK), `L65 = 699,077.14` (GW), `O65 = 560,767.10` (PW), `R65 = 427,711.43` (MA), `U65 = 2,061,993.18` (total)
- **Reasoning:** Engine `renewable_by_sector` reads `10.3.1` / `10.4.3` /
  `10.5.3` / `10.6.2` (these are Strom-only sub-subcodes). Excel
  `L65 = M239` (full GW renewable across gas + liquid + solid + heat +
  Strom). Should use `10.3` / `10.4` / `10.5` / `10.6` (sector aggregate
  parents). With the parent codes, GW renewable would jump from 17,211
  to ~172,290 (10× increase, matches Excel L239).
- **Code:** `calculation_engine/bilanz_engine.py:407-419`
- **Fix effort:** ~5 min — 4-line change in the `renewable_by_sector` dict.
- **Goldens move:** YES.
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit_full/08_findings/F013_ziel_renewable_per_sector_drift.md`

### F011 HIGH — verbrauch_heat_renewable returns 0
- **Symptom:** Bilanz Wärme renewable row shows 0 across all sectors when Excel scenario has 32,783 GWh/a (Biogas Wärmenutzung + Solar thermal).
- **DB:** `calculate_bilanz_data()['verbrauch_heat_renewable']['status']['gebaeudewaerme'] = 0`
- **Excel:** `_S.xlsx!5. Bilanz!L22 = 32,782.79` (formula `=L10+L91+L137+L153+L159` summing solar thermal + biogas heat + wood heat + 2 more renewable heat sources)
- **Reasoning:** Engine's `heat_renewable_codes` map doesn't aggregate
  the Renewable subcodes that Excel sums in `L22`. The `v_heat_status_ren`
  dict evaluates to `{kraft_licht: 0, gebaeudewaerme: 0, ...}` because
  no contributing codes are wired in.
- **Code:** `calculation_engine/bilanz_engine.py:660-661`
  (verbrauch_heat_renewable assembly) + the `heat_renewable_codes` map
  defined nearby that needs Biogas/Solar-thermal codes added.
- **Fix effort:** ~30 min — cross-reference Excel `L22 = L10+L91+L137+L153+L159`
  to the matching DB Renewable codes (likely under `10.4.2` family);
  expand the heat_renewable_codes map.
- **Goldens move:** YES.
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit_full/08_findings/F011_verbrauch_heat_renewable_zero.md`

### F001 HIGH — LU_2.1 user_percent seed drift 3.856 vs 5
- **Symptom:** Solare Freiflächen target_ha is 23 % short of scenario.
- **DB:** `LandUse[LU_2.1].user_percent = 3.856 %`, `target_ha = 684,640.80 ha`
- **Excel:** `_S.xlsx!1. Flächen!R13 = 5` (Ziel-Modifikation, literal),
  `_S.xlsx!1. Flächen!L13 = 887,749.85 ha`
- **Reasoning:** Excel L13 formula
  `=IF(R13="",AF13,IF(T13="",INDIRECT("L"&AB13)*R13/100,R13))` with
  R13=5 and AB13=12 → L12 × 5 / 100 = 17,754,997 × 0.05 = 887,749.85.
  DB seed has `user_percent = 3.856 %` instead of 5 % → recomputes
  ziel as 17,754,997 × 0.03856 ≈ 684,641. Formula shape is identical;
  the **seed value** for `user_percent` diverges.
- **Code:** seed row — `seed/sqlite_seed.json` `LandUse[code='LU_2.1']` (`user_percent` field, owner=None canonical)
- **Fix effort:** ~5 min — single seed-value change + `percentage_rebalancer` cascade.
- **Goldens move:** YES (LandUse + Bilanz Flächen totals).
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit/09_findings/F001_LU_2_1_user_percent_drift.md`

### F003 HIGH — Verbrauch 3.2.2 Zieleinfluss Prozess-Effizienz drifts 89 vs 95
- **Symptom:** PW efficiency multiplier ziel is 6 percentage points
  below scenario; affects PW total (related F004).
- **DB:** `VerbrauchData[3.2.2].ziel = 89.00004`, `status = 100.0` (matches),
  `is_calculated = False`
- **Excel:** `_S.xlsx!4. Verbrauch!M32 = 95` (literal hand-set scenario
  parameter, not a formula); `L32 = 100` (matches DB status)
- **Reasoning:** Hand-set scenario parameter at literal 95. DB seeds at
  89.00004. Sibling row 1.1.2 (KLIK Endanwendungs-Effizienz) seed
  matches Excel at 95 — so this drift is isolated to 3.2.2, not a
  systemic miss across all Zieleinfluss rows.
- **Code:** seed row — `seed/sqlite_seed.json` `VerbrauchData[code='3.2.2']` (`ziel` field, owner=None canonical)
- **Fix effort:** ~5 min — single seed correction.
- **Goldens move:** YES (PW sector ziel ~6 % lift).
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit/09_findings/F003_Verbrauch_3_2_2_ziel_drift.md`

### F008 HIGH (carried) — Bilanz MA Strom subcode mismatch (28,136 vs 15,300)
- **Symptom:** `/bilanz/` MA Strom is 84 % too high.
- **DB:** `calculate_bilanz_data()['verbrauch_strom']['status']['mobile'] = 28,136`
  (from DB row `VerbrauchData[6.2].status = 28,135.997474`, category "davon Strom")
- **Excel:** `_S.xlsx!5. Bilanz!Q9 = 15,300.01 GWh/a` (formula
  `='7. Verbrauch Status'!Q11` → `=Q41*$L$5/$AB$4` =
  180.70 kWh/person × 84,669,326 / 1,000,000)
- **Reasoning:** `strom_codes['mobile'] = '6.2'` selects a DB value
  ~13k GWh/a above Excel's `Q9`. Either DB 6.2 includes electric-traction
  rail that Excel tracks separately, OR DB 6.2 status is back-cast from
  ziel state. Same class as F007 — subcode mapping error in
  `bilanz_engine.py`.
- **Code:** `calculation_engine/bilanz_engine.py:521` (strom_codes mobile entry)
- **Fix effort:** ~30-60 min — enumerate VerbrauchData rows under
  6.x; identify which one corresponds to Excel `Q9`; or correct seed
  if 6.2 status is wrong.
- **Goldens move:** YES.
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit/09_findings/F008_Bilanz_MA_Strom_code_mismatch.md`

### F005 HIGH (carried) — Biogas Nutzungsgrad seed drift 12-23 pp
- **Symptom:** Biogas power-plant + KWK efficiency factors diverge
  12-23 percentage points from Excel; cascades into Biogas-Verstromung
  GWh/a totals.
- **DB:** `RenewableData[5.4.2.1] (Biogas Nutzungsgrad Kraftwerk).status = 37.5`,
  `.target = 45`. `RenewableData[5.4.2.3] (Biogas Nutzungsgrad
  KWK-Abwärme effektiv).status = 21.9`, `.target = 25`.
- **Excel:** `_S.xlsx!2. Erneuerbare!L84 = 25`, `M84 = 35` (Biogas
  Nutzungsgrad Kraftwerk). `_S.xlsx!2. Erneuerbare!L86 = 45`, `M86 = 45`
  (Biogas Nutzungsgrad KWK-Abwärme effektiv).
- **Reasoning:** Round 2's curated section-aware mapping placed the
  Biogas + Biodiesel "Nutzungsgrad KWK-Abwärme effektiv" rows in
  separate Excel sections (84/86 for Biogas vs 136 for Biodiesel).
  Biodiesel row `6.1.3.2.3` matches Excel L136 EXACTLY at 50/50, so
  the Biogas drift is isolated and confirmed real. Carried because
  it's one specific instance of F014's Renewable-yield-cluster
  pattern.
- **Code:** seed rows — `seed/sqlite_seed.json` `RenewableData[code='5.4.2.1']`
  + `RenewableData[code='5.4.2.3']`
- **Fix effort:** ~10 min — 4 seed values (status + ziel for both rows)
  pending stakeholder confirmation.
- **Goldens move:** YES.
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit/09_findings/F005_Renewable_biogas_nutzungsgrad.md`
  + closure `verification/formula_audit_full/04_renewable_section_aware/f005_resolution.md`

### F002 MEDIUM — LU_2.4 (sonstige Nutzung) residual drift 12.8 %
- **Symptom:** "(sonstige Nutzung)" target_ha is 12.8 % above scenario; **derived consequence of F001**.
- **DB:** `LandUse[LU_2.4].target_ha = 1,883,157`
- **Excel:** `_S.xlsx!1. Flächen!L25 = 1,670,097.38`
  (formula `=L12-L14-L22-L13` = LF target − Ackerland − Dauergrünland − LU_2.1)
- **Reasoning:** LU_2.4 is a residual. With LU_2.1 wrong (684,641 instead
  of 887,750 — F001), the residual absorbs the 203 kha gap →
  17,754,997 − 10,826,000 − 4,371,150 − 684,641 ≈ 1,873,206 (DB shows
  1,883,157, small rounding). Fixing F001 cascades and self-corrects F002.
- **Code:** none — derived
- **Fix effort:** 0 min — auto-corrects when F001 is fixed.
- **Goldens move:** YES (along with F001).
- **Origin:** pre-existing in commit `a5da7dd` (consequence of F001's seed).
- **Evidence:** `verification/formula_audit/09_findings/F002_LU_2_4_residual_drift.md`

### F004 MEDIUM — Verbrauch 3.7 PW status 0.9 % short
- **Symptom:** PW sector total status is 0.9 % below Excel; ziel matches.
- **DB:** `VerbrauchData[3.7].status = 550,370.90 GWh/a`
  (`is_calculated=True` — sum of PW children 3.3 / 3.4 / 3.5 / 3.6)
- **Excel:** `_S.xlsx!4. Verbrauch!L120 = 555,394.57 GWh/a`
- **Reasoning:** 0.9 % drift on a calculated sum suggests one PW child
  status seed is slightly off. Ziel is identical (drift < 1 ppm) →
  bug is status-side only.
- **Code:** seed row — one of `seed/sqlite_seed.json`
  `VerbrauchData[code in {3.3.0, 3.4.0, 3.5.0, 3.6.0}]` (`status` field)
- **Fix effort:** ~30-60 min — drill-down to identify the single child;
  correct the seed.
- **Goldens move:** YES.
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit/09_findings/F004_Verbrauch_3_7_status_drift.md`

### F010 MEDIUM — 10.x_ziel residual-vs-sum formula divergence
- **Symptom:** Sector-total renewable Formulas (10.4_ziel / 10.5_ziel /
  10.6_ziel) compute via sum-of-children in DB, residual in Excel.
  Default-scenario identical; unbalanced-scenario may diverge.
- **DB:** `Formula[10.5_ziel_target].expression =
  'Renewable_10_5_1 + Renewable_10_5_3 + Renewable_10_5_2'`
- **Excel:** `_S.xlsx!2. Erneuerbare!M62 = =100-M62-M64-M65` (residual form)
- **Reasoning:** Sum-form: total = changed_value + other_siblings.
  Residual-form: total = 100 − other_siblings (changed sibling
  ignored). The two diverge when one sibling is moved without
  rebalancing the others. Behavioural design question — Excel's
  scenario state has the children sum to 100, so both forms agree
  at default.
- **Code:** Formula table rows `10.4_ziel_target`, `10.5_ziel_target`,
  `10.6_ziel_target` — backed by `seed/sqlite_seed.json` Formula entries
- **Fix effort:** ~30-45 min — Formula expression refactor + scenario
  test under unbalanced edits.
- **Goldens move:** NO at default scenario; YES if user-mutated workspaces are tested.
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit_full/08_findings/F010_residual_vs_sum_divergence.md`

### F012 MEDIUM — verbrauch_fuels aggregates 3 carriers
- **Symptom:** Engine `verbrauch_fuels` is a single aggregate for gas +
  liquid + solid; Excel has 3 separate Bilanz rows.
- **DB:** Single dict key `verbrauch_fuels.gebaeudewaerme = 632,956`
  (sum of gas + liquid + solid)
- **Excel:** `_S.xlsx!5. Bilanz!K12 = 346,430` (gas), `K15 = 136,478`
  (liquid), `K18 = 149,501` (solid). Sum K12+K15+K18 = 632,410
  (matches engine within 0.09 %, PASS_COSMETIC).
- **Reasoning:** Engine model coarser than Excel. Aggregate math is
  right; per-carrier display is missing. Stakeholder PDF §2.3 may
  require per-carrier reporting; if not, accept as-is.
- **Code:** `calculation_engine/bilanz_engine.py:642-653`
  (verbrauch_fuels assembly)
- **Fix effort:** ~60-90 min to split into 3 carriers; or 0 min if
  accepted as out-of-scope.
- **Goldens move:** NO at aggregate level; YES if per-carrier rows are added.
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit_full/08_findings/F012_verbrauch_fuels_no_carrier_breakdown.md`

### F014 MEDIUM — Renewable yield / Nutzungsgrad cluster drift 5-30 %
- **Symptom:** ~50 Renewable seed values diverge 5-30 % from Excel —
  Solarthermie yield, Biomethan split, Biomasse Nutzungsgrad,
  Biogas-Biomasse yields, etc.
- **DB:** Examples: Solarthermie Energieertrag DB = 3,878 vs Excel 5,250
  (26 % drift); Biomethan für MA DB = 1.2 % vs Excel 1.25 % (3.9 %).
  Total: 68 status + 65 ziel rows >1 % drift after section-aware mapping.
- **Excel:** `_S.xlsx!2. Erneuerbare` — Solarthermie yield row L9 = 5,250
  (Excel cached); Biomethan-für-MA row `L114 = 1.249887...`; full list
  in `verification/formula_audit_full/04_renewable_section_aware/per_row_parity.csv`
  (rows with `verdict_status=DRIFT` or `verdict_ziel=DRIFT`).
- **Reasoning:** Cluster pattern, not a single bug. DB Renewable seed
  was captured at one point in time; Excel scenario parameters were
  later refined. Drift is consistent with a seed-refresh lag of
  ~2-3 months.
- **Code:** seed rows — `seed/sqlite_seed.json` ~50 RenewableData rows
  (those flagged DRIFT in `04_renewable_section_aware/per_row_parity.csv`)
- **Fix effort:** ~2-4 hours — re-import Renewable seed values from
  `_S.xlsx!2. Erneuerbare` using the curated mapping; produce a diff;
  await stakeholder sign-off before committing seed change.
- **Goldens move:** YES (Renewable + Bilanz renewable rows).
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit_full/08_findings/F014_renewable_yield_cluster_drift.md`

### F006 LOW — WS_ABREGELUNG_THRESHOLD = 0.65 dead code
- **Symptom:** Constant looks load-bearing but is unused; if rewired,
  would produce 35 %-short Einspeich on max-excess days.
- **DB:** `Formula[key='WS_ABREGELUNG_THRESHOLD', category='ws_constant'].expression = '0.65'`
- **Excel:** Named range `Abregelung` →
  `WS.xlsm!1.Jahresbilanz_Strom!N32 = 1` (cached value, formula
  `=IF(O32="",D79,O32)/100` with D79 = 100).
- **Reasoning:** `calculation_engine/ws_engine.py:40` loads the
  constant and uses it as both threshold AND multiplier in
  Einspeich/Abregelung branching; with 0.65 it would diverge from
  Excel (which uses 1 for both). Grep confirms `ws_engine.py` has
  zero importers in `simulator/` — production WS365 path uses
  `WS365Formula[einspeich]` (migration 0044) which correctly uses
  threshold = 1. Constant has no production effect today; documented
  hygiene risk.
- **Code:** `calculation_engine/ws_engine.py:40` (loader; entire file
  is dead code) + Formula seed row in `seed/sqlite_seed.json`
- **Fix effort:** ~5 min — either delete `ws_engine.py` + the seed
  row, OR change the seed expression to `'1.0'` to match Excel if
  someone re-wires it.
- **Goldens move:** NO (no production effect).
- **Origin:** pre-existing in commit `a5da7dd`.
- **Evidence:** `verification/formula_audit/09_findings/F006_WS_ABREGELUNG_THRESHOLD_dead_code.md`

### F015 LOW (deferred) — Verbrauch percentage seed precision causes +230 GWh V2.10 vs Excel
- **Symptom:** V2.10 (`Endenergieverbrauch GW gesamt`) reads 663,768.68 GWh/a in default scenario where Excel reads 663,538.83 — permanent +230 GWh offset that propagates into V2.6, V2.10, the GW supply target (R10.4), and the GW gap consumed by the balance optimiser. The drift is constant at ~+230 GWh regardless of V2.4.1 user input (verified by editing V2.4.1 75→80 in both stacks; main app gives 672,097.55 vs Excel-precise 671,867.20).
- **DB:** `VerbrauchData[2.1].ziel = 71.64`, `VerbrauchData[2.2].ziel = 28.4`, `VerbrauchData[2.4].ziel = 85.9`, `VerbrauchData[2.5].ziel = 14.1` (all rounded to ≤2 decimals at seed-import time).
- **Excel:** `_S.xlsx!4. Verbrauch!L46 = 71.64093767867352` (V2.1), `L52 = 28.35906232132647` (V2.2), `L58 = 85.92911239479102` (V2.4), `L70 = 14.07088760520898` (V2.5) — full precision, sums to exactly 100.
- **Reasoning:** App seed truncates four percentage shares to ≤2 decimals. Excel's V2.1+V2.2 sums to exactly 100; ours sums to 71.64+28.4 = 100.04 → V2.3 inflates by 0.04 % (= +319 GWh) → cascades to V2.4.0 (+42 GWh) and V2.5.2 (+194 GWh) → V2.6 = V2.10 ends up +230 GWh. V2.4 + V2.5 = 100 in both seed and Excel (lucky cancellation), so the GW share split itself isn't the leak — only V2.1/V2.2 is. Math fully reproducible: with Excel-precise values plugged into the existing app formula chain, V2.10 lands at 671,867.20 vs the app's 672,097.55 — delta 230.56 GWh, matches the user's observation exactly.
- **Code:** seed rows — `seed/sqlite_seed.json` `VerbrauchData[code in {2.1, 2.2, 2.4, 2.5}]` (`ziel` field; `user_percent` field if it shadows ziel for any of them).
- **Fix effort:** ~30 min for the seed edit itself, **but** non-trivial in cascade: every regression golden (scenarios A / C / D) shifts because V2.3, V2.4.0, V2.4.9, V2.5.0, V2.5.2, V2.6, V2.10 all move ~230 GWh, downstream R10.4 supply target moves to compensate, the Bilanz GW row moves, and the GW gap can swing into / out of the balance optimiser's ±100 GWh tolerance window — so balance-button behaviour changes too. Effectively a baseline-regen sprint, not a one-line fix.
- **Goldens move:** YES — every scenario A / C / D affected; downstream Bilanz, WS365 storage drift, and balance convergence path all change.
- **Origin:** pre-existing in commit `a5da7dd` initial import (seed was captured at low precision before the runtime bundle was packaged).
- **Priority:** **deferred / not important.** The math is internally consistent (V2.10 is reproducible from the seed values shown to the user), only the absolute level differs from Excel. Stakeholder hasn't flagged. Fits naturally into a future "Excel parity sweep" alongside F014 (Renewable yield cluster) and the Verbrauch / GW seed corrections in F003 / F004 / F005 — all share the pattern "seed captured at one point in time, Excel scenario refined later". Don't ship in isolation; bundle.
- **Evidence:** session investigation 2026-04-27 (no audit folder yet — math reproduced live in `prosim_main` testsim workspace by parsing `_S.xlsx!4. Verbrauch` rows 46/52/57/58/68/70/73/75/91 and back-solving the formula chain).

### F009 LOW — Jahresstrom Abregelung sum 3.3 % drift (accepted perf trade-off)
- **Symptom:** `n_input_branch` (Abregelung input) drifts 3.3 % from
  Excel; flow_q_abregelung_tages drifts 3.25 %; abgleichdifferenz
  drifts 1.66 %.
- **DB:** `compute_ws_diagram_reference()`: `n_input_branch = 195,890.29`,
  `flow_q_abregelung_tages = 64.55`, `abgleichdifferenz = 156.63`
- **Excel:** `WS.xlsm!1.Jahresbilanz_Strom!L23 = 189,627.90` (named
  range `AbregCopy` → `Zeitreihen Kalkulation!Q152` annual sum);
  `L24 = 62.46` (Abregelung tages); `Q44 = 159.27` (Abgleichdifferenz)
- **Reasoning:** 2026-04-21 perf pass intentionally cut convergence
  iteration counts (Heroku cold-start balance ~5 min → ~2 min). Within
  scenario D tolerance ±5 ha / ±1 GWh. Daily Einspeich + Abregelung
  formulas in `WS365Formula` exactly match Excel; the 3.3 % drift is
  the goal-seek solver's residual mis-balance from the iteration cut.
- **Code:** convergence iteration counts — see `docs/CONVERGENCE_ITERATIONS_CHANGED.md`
  for the exact revert recipe per file/line.
- **Fix effort:** 0 min if accepted (current state); ~60 min if reverted
  for bit-identical math.
- **Goldens move:** NO (within tolerance; goldens already accept
  current values).
- **Origin:** **introduced** by 2026-04-21 perf pass (the only one of
  the 14 NOT pre-existing in `a5da7dd`).
- **Evidence:** `verification/formula_audit/09_findings/F009_Abregelung_sum_drift_from_perf_cuts.md`

---

## Commits of record

```
9d18bb5  gap #1 (scenario A golden) closed
21f2f8c  gaps #2 + #3 (banner + admin baseline) closed
8e442ca  gap #4 (populated modifikationsdetails) closed
1304cc8  verification audit
9afeb1c  Phase 5+6 complete (V5 green)
93a56c9  Phase 3+4 complete (V5 green)
9dce8de  Phase 2 complete (V5 green)
99a7ccb  Phase 1 complete (V5 green)
c403c7d  Phase 0 scaffolding
ffc1b39  plan recalibration (cascade vs Balance, Phase 7 renumber)
e2d0140  stakeholder PDF extracted + plan drafted
```

All rollback points available. Nothing running on Heroku. Full repo clean.
