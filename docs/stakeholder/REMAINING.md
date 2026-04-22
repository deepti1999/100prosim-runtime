# What's remaining — single source of truth

**Last updated:** 2026-04-22 evening (after T54 flow-diagram fix, commit `d0eea4d`, V5-verified on Heroku)
**Source material:** `260403_Portierung_Bestandsaufnahme.pdf` (stakeholder PDF, 12 pages) + `IMPLEMENTATION_PLAN.md` (our 63-target decomposition)

---

## Headline

**51/63 atomic targets shipped and Heroku-verified.** 12 targets outstanding:

| Bucket | Count | Blocked on |
|---|---:|---|
| **External-gated** | 6 | ErnES picks a compute platform |
| **Deferred by decision** | 6 | Separate scoping session (Pascal's call) |

T54 (flow-diagram value→position mis-wiring) is now closed — see
`FLOW_DIAGRAM_AUDIT.md` "Fix shipped (2026-04-22)". The 15 missing
annotations identified during the deep audit (a–o) are *not* T54 targets,
they're cosmetic extensions; captured at the bottom of the audit doc for
Schmidt-Kanefendt's prioritisation.

Every deliverable from the PDF that can be shipped right now **is shipped**. What's left falls into three clear categories below.

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
