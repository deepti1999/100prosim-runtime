# What's remaining — single source of truth

**Last updated:** 2026-04-23 (after T54 visual pass 4 = 14 incremental commits `797f0d3`→`f4d1a6a`, V5-verified at pass 22 on Heroku)
**Source material:** `260403_Portierung_Bestandsaufnahme.pdf` (stakeholder PDF, 12 pages) + `IMPLEMENTATION_PLAN.md` (our 63-target decomposition)

---

## Headline

**51/63 atomic targets shipped and Heroku-verified.** 12 targets outstanding from the original plan, plus 4 backend-data items surfaced during T54 visual passes:

| Bucket | Count | Blocked on |
|---|---:|---|
| **External-gated** | 6 | ErnES picks a compute platform |
| **Deferred by decision** | 6 | Separate scoping session (Pascal's call) |
| **T54 backend-data** | 4 | Schmidt-Kanefendt formulas / fields (see §3 below) |

T54 (flow-diagram value→position mis-wiring) is structurally closed
through visual pass 22 — see `FLOW_DIAGRAM_AUDIT.md` "Visual pass 4
shipped". The diagram now matches Excel page 10 in layout, circles,
boxes, gas-vs-Strom colours, and label positions. What is **not** yet
matching Excel is the 4 backend-data items below.

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

## 2. Deferred by decision (6 targets) — Data-model rework

### PDF §2.3 — Datenmodell

Stakeholder's **proposal** (Vorschlag, not mandate):

> *"Schnittstelle zur Nutzung der bestehenden Excel-Datenmodell-Dateien anstelle des integrierten Datenmodells im aktuellen 100prosim-Web."*

Two sub-asks:

#### §2.3.1 — Nachvollziehbarkeit (traceability)
| ID | Description |
|---|---|
| T8 | Parameter source (Quellbezug) surfaced in UI |
| T9 | Parameter assumption (Annahme) surfaced in UI |
| T10 | Admin can update parameters without code changes |

Excel has every parameter hyperlinked to its source (paper, statistic, study). The web app copied the values into seed fixture once, without the links. Fixing this means adding `source_ref`, `source_assumption`, `source_url` fields to every parameter-bearing model + an info-tooltip in the UI + an admin editor.

#### §2.3.2 — Alternativ-Regionen (regions beyond Germany)
| ID | Description |
|---|---|
| T11 | Scenario switcher between DE + Bundesländer |
| T12 | Data model loaded from external Excel file |
| T13 | Region-specific models editable by non-developer admins |

Excel 100prosim ships variants: Germany (`D.xlsx`), plus per-Bundesland sheets on <https://www.ernes.de/seite/422657/softwaretools.html>. Current web app is Germany-only. Fixing this means a first-class `Region` concept + file upload + per-region data tables.

**Why deferred by your decision:**

- You said: *"I'm not quite sure about the phase seven because I'm not quite sure yet, if this is in our scope right now. I do have Excel files but maybe we have to look it into this matter more deeply."*
- This is the biggest architectural change on the list — touches data-model, import pipeline, formula engine, scenario concept, UI.
- Stakeholder phrased §2.3 as *Vorschlag* (proposal), not a must-have for replacing Excel.
- It interacts with the hardcoding-reduction roadmap in `docs/PYPSA_MIGRATION_RESEARCH.md` §23.3 (first-class `Sector` / `Carrier` / `Region` refactors are prerequisites).

**Unblocker:** Pascal schedules a scoping session. Decisions needed:
1. Which Excel files are available and current?
2. Option A (one-shot import + source metadata), Option B (live Excel binding at request time), or Option C (hybrid: import into DB + `source_excel_path` per row)?
3. Which Bundesländer are in scope for the first region release?
4. Timeline — 2 weeks minimum, likely 3–4 weeks if we want all three sub-targets (T8, T11, T13) polished.

**Written plan:** `IMPLEMENTATION_PLAN.md` §13 "Deferred — Data model".

---

## 3. T54 backend-data items (4) — Jahresstrom flow diagram

These four labels currently render in the SVG with **hardcoded
Excel-reference values**. They cannot be made dynamic from existing
backend output; each needs either a formula confirmation from
Schmidt-Kanefendt or a new field added to the WS365 service.

| # | Label in diagram | Current hardcoded value | What's blocking dynamic binding |
|---|---|---|---|
| **D1** | Tagesladungen italic blue numbers under each source value | `397` (PV), `186` (Wind), `5` (Hydro), `1` (Bio) | Per-source normalisation formula unknown. Tried `value / (storage_capacity / 80)` — fits PV (1,201,630 / 3,021.6 ≈ 397.7) but not Wind (706,237 / 3,021.6 ≈ 233.7 ≠ 186). Need Schmidt-Kanefendt's formula. |
| **D2** | Tagesladungen italic blue numbers on every flow segment | `509` on M→Q, `313` on Q→S, `365` on S→Stromnetz, `62` on Abregelung, `134` on Q→Ely-ES, `87` on each gas branch (×3), `51` on Rückv→S, `80` on Speicherkapazität | Same formula gap as D1; values vary per scenario but no obvious denominator from current outputs. |
| **D3** | Percent shares under each source value | `62,2%` (PV), `29,2%` (Wind), `0,8%` (Hydro), `0,2%` (Bio) | Denominator unclear. `pv / (pv + wind + hydro + bio)` gives PV = 62.2% ✓ but Wind = 36.6% ✗ (not 29.2%). Need the exact Excel formula or working-copy cell reference. |
| **D4a** | `194 GW` red annotation under 405.027 box (Pmax of Elektrolyse Stromspeicher) | Static text | Installed-power peak figure. Not computed by backend. Likely a config constant once stakeholder confirms the exact number; currently 194 in Excel, may differ for other regions. |
| **D4b** | `261 GW (elekt.)` red annotation beside Rückverstromung | Static text | Same as D4a — installed-power peak, not in backend. |
| **D4c** | `Abgleichdifferenz 160` (with small `0` to right and `80` Tages below) at bottom-right | Static text | Scenario-solver residual diagnostic. Not exposed by `get_ws_365_data()` today. Would need a new field on the WS365 service output. |

**Where these currently live in the template:** in
`simulator/templates/simulator/annual_electricity.html`, search for
the literal strings `"397"`, `"509"`, `"62,2%"`, `"194 GW"`, `"261 GW"`,
`"160"` to find the hardcoded `<text>` elements. Each is right next to
its dynamic counterpart for easy swap-out once the formula is known.

**Where these live in the Excel source** (per 2026-04-23 data-model
audit, `docs/stakeholder/DATA_MODEL_AUDIT.md`):

- D1 source Tagesladungen → `WS.xlsm` sheet `Zeitreihen Kalkulation`
  (daily series, normalised per source)
- D2 flow Tagesladungen → same sheet, applied to each flow segment
- D3 percent shares → `WS.xlsm` sheet `1.Jahresbilanz_Strom` cell
  `E21` for PV = 0.6227 (equivalents for other sources)
- D4a/b (194 GW / 261 GW) → `WS.xlsm` `1.Jahresbilanz_Strom` row 30
- D4c (Abgleichdifferenz 160) → `WS.xlsm` scenario-balance residual

§2.3 (below) and D1–D4c are effectively the same work: the Excel
import that satisfies §2.3 also unblocks the hardcoded diagram
values automatically. See `DATA_MODEL_AUDIT.md` for full details.

**Effort once unblocked:**
- D1 + D2: ~30 min if it's one formula. Add `tages_*` keys to the
  context vars in `simulator/page_renewable.py::annual_electricity_view`,
  bind them in the template's JS init block.
- D3: ~30 min, similar pattern.
- D4a + D4b: ~15 min — add two config constants (or one constant per
  Region once `Region` becomes first-class), expose in context.
- D4c: ~1–2 hours — new field on `get_ws_365_data()` output, requires
  a small audit of the WS365 solver to surface the residual.

**To unblock:** Schmidt-Kanefendt confirms the Tagesladungen
normalisation rule, the percent-share denominator, the
installed-power values for Germany 2023, and whether
`Abgleichdifferenz` should be computed (and from what).

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
| Deferred §2.3 scoping | Pascal | One meeting |
| T54 backend-data formulas (D1–D4c) | Schmidt-Kanefendt | One email reply with the 3 formulas + 2 GW values |

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
