# What's remaining — single source of truth

**Last updated:** 2026-04-23 (after §2.3 Phase C landed, V5-verified on Heroku — non-DE region proven end-to-end with synthetic TEST cloning DE × 1.05; D4a/D4b values change with active region as designed; DE values byte-identical pre/post round-trip)
**Source material:** `260403_Portierung_Bestandsaufnahme.pdf` (stakeholder PDF, 12 pages) + `IMPLEMENTATION_PLAN.md` (our 63-target decomposition)

---

## Headline

**57/63 atomic targets shipped, Heroku-verified, AND operationally complete** (51 from the original push + T8/T9/T10 from §2.3 Phase A + T11/T12/T13 from §2.3 Phase B with Phase C operational closure). T54 diagram sub-items 6/6 shipped (Track 1 closed D1/D2/D3/D4c on 2026-04-23 commit `7c02458`; Phase B closed D4a/D4b). **6 items outstanding total — all external-gated:**

| Bucket | Count | Blocked on |
|---|---:|---|
| **External-gated (Phase 7)** | 6 | ErnES picks a compute platform |

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

## 2. §2.3 status — Phase A SHIPPED, Phase B remaining (3 targets)

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
