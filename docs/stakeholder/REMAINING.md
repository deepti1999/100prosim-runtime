# What's remaining — single source of truth

**Last updated:** 2026-04-23 (after T54 Track 1 landed, commit `7c02458`, V5-verified on Heroku — 4 of 6 hardcoded diagram values now backend-computed)
**Source material:** `260403_Portierung_Bestandsaufnahme.pdf` (stakeholder PDF, 12 pages) + `IMPLEMENTATION_PLAN.md` (our 63-target decomposition)

---

## Headline

**51/63 atomic targets shipped and Heroku-verified** from the original plan; T54 diagram sub-items tracked separately (4/6 shipped via Track 1 on 2026-04-23). **14 items outstanding total:**

| Bucket | Count | Blocked on |
|---|---:|---|
| **External-gated (Phase 7)** | 6 | ErnES picks a compute platform |
| **§2.3 Phase A + B** | 6 | Pascal answers D1–D8 in `DATA_MODEL_IMPORT_AUDIT.md` §9 |
| **T54 backend-data** | 2 (D4a/D4b) | §2.3 Phase B (Region.installed_pmax_*) |

T54 D1/D2/D3/D4c (source Tagesladungen, flow Tagesladungen, percent shares, Abgleichdifferenz) shipped 2026-04-23 in commit `7c02458`; see `HARDCODED_VALUES_TRACE.md` §6 for the verification ledger.

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

#### §2.3.1 — Nachvollziehbarkeit (traceability) → Phase A
| ID | Description | Phase |
|---|---|---|
| T8 | Parameter source (Quellbezug) surfaced in UI | A |
| T9 | Parameter assumption (Annahme) surfaced in UI | A |
| T10 | Admin can update parameters without code changes | A |

#### §2.3.2 — Alternativ-Regionen (regions beyond Germany) → Phase B
| ID | Description | Phase |
|---|---|---|
| T11 | Scenario switcher between DE + Bundesländer | B |
| T12 | Data model loaded from external Excel file | B |
| T13 | Region-specific models editable by non-developer admins | B |

Excel-side facts (verified by audit `WORKBOOK_CATALOG.md`):
`D.xlsx!9.Quellen` carries 86 source URLs; `D.xlsx!1.` carries 747
per-cell assumption comments. `_S.xlsx` is the scenario master
whose sheets are 1:1 with our app pages. Per-Bundesland Excel
files exist on <https://www.ernes.de/seite/422657/softwaretools.html>
but are not yet in Pascal's local bundle (only `D.xlsx` for Germany).

**Audit completed 2026-04-23** (commits `d2a4c28`, `55cf302`, `58a1b90`,
`4c78f61`, `4b7b063`). Full record:

- Step A — `260403_Section_2.3_literal.md` — verbatim §2.3 text + 11
  literal asks (L1–L11).
- Step B — `WORKBOOK_CATALOG.md` — per-file catalog of all 9 workbooks.
- Step C — `scripts/audit_out/s_xlsx_map_*.csv` — 420 DB rows mapped
  to `_S.xlsx` at **78.3 % HIGH-confidence + 14.5 % MED + 6 % label-only
  + 1.2 % NONE.**
- Step D — `260403_Section_2.3_decision.md` — binding decision record:
  §2.3 is a **provenance + region + admin-edit** ask, NOT a value import.
  Values already exist in DB; the gap is source URLs, assumption notes,
  region first-class, and admin re-import without code change.
- Step E — `DATA_MODEL_IMPORT_AUDIT.md` (rewritten) — 12 SRs, 10 risks
  (RISK-01 drops H/H → L/L because Phase A is provenance-only),
  2-phase plan (A: ~3 days, B: ~3 days), V2–V6 ritual per phase.

**Phase A** (provenance + tooltip + DE admin import) closes T8 + T9 + T10.
**Phase B** (region first-class + Bundesländer-ready import) closes
T11 + T12 + T13 AND unblocks T54 D4a/D4b (see §3 below).

Both phases are **additive** — provenance columns + region FK with
default `DE` — so the 51 shipped targets stay green. Track 1 D1/D2/D3/D4c
outputs are unaffected.

**Unblocker:** Pascal answers 8 actually-blocking decisions (D1–D8) in
`DATA_MODEL_IMPORT_AUDIT.md` §9. Once D1–D8 are settled, Phase A
opens a single ~3-day implementation. The earlier 4 v1 questions
(`one-shot vs live binding`, etc.) are now resolved (live binding is
out; import + tooltip + admin diff is in).

**Written plan:** `DATA_MODEL_IMPORT_AUDIT.md` (revised) supersedes
the older `IMPLEMENTATION_PLAN.md` §13 stub.

---

## 3. T54 backend-data items (4) — Jahresstrom flow diagram

These four labels currently render in the SVG with **hardcoded
Excel-reference values**. They cannot be made dynamic from existing
backend output; each needs either a formula confirmation from
Schmidt-Kanefendt or a new field added to the WS365 service.

| # | Label in diagram | Status | Details |
|---|---|---|---|
| **D1** | Tagesladungen italic blue numbers under each source value | ✅ Shipped `7c02458` | Now `annual × TLproEingabeEinheit`, `TLproEingabeEinheit = 365 / final_stromnetz`. Wind and Hydro use AE-adjusted numerator (value × `(1 - ely_branch/m_total)`). |
| **D2** | Tagesladungen italic blue numbers on every flow segment | ✅ Shipped `7c02458` | Same factor applied to each flow segment's annual value. |
| **D3** | Percent shares under each source value | ✅ Shipped `7c02458` | Denominator = `pv + wind + hydro + bio` (four sources summed). Numerators asymmetric — PV/Bio raw, Wind/Hydro AE-adjusted. Matches Excel cell formulas E14/E21/E27/E33 exactly. |
| **D4a** | `194 GW` red annotation under 405.027 box (Pmax Ely-ES) | ⏸ Pending §2.3 Phase B | Installed-power region constant — `WORKBOOK_CATALOG.md` confirms `D.xlsx!I_Basisdaten` (192 × 15) is the right home. `Region` model gains `installed_pmax_ely_gw` field; populated by Phase B import. |
| **D4b** | `261 GW (elekt.)` red annotation beside Rückverstromung | ⏸ Pending §2.3 Phase B | Same source as D4a; `installed_pmax_rv_gw` on `Region`. |
| **D4c** | `Abgleichdifferenz 160` at bottom-right | ✅ Shipped `7c02458` | Now `gas_storage - t_value` (net gas-tank drift). Matches Excel Q44 formula `=L36-Q36`. |

**Where D4a/D4b live in the template** (only ones left hardcoded):
`simulator/templates/simulator/annual_electricity.html` — search for
`"194 GW"` and `"261 GW"` to find the remaining `<text class="txt-red">`
elements. They'll become dynamic once §2.3 adds region-config fields.

**Known non-blocking discrepancy** documented in
`HARDCODED_VALUES_TRACE.md` §6: the Gasspeicher Direktverbr Tages
shows `83` (mathematically correct per formula) rather than `87`
(Excel diagram's visual value). Excel cell H37 has no formula —
its "87" is a visual copy. Our 83 is the formula output.

§2.3 (above §2 in this file) remains a separate architectural change
about **parameter sources + assumptions + region swap** — values are
already in DB per the §2.3 audit. See `DATA_MODEL_IMPORT_AUDIT.md`
(revised 2026-04-23) for the §2.3 scope and `HARDCODED_VALUES_TRACE.md`
for the D1–D4c detail.

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
