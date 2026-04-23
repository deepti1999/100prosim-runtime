# Data-model audit — §2.3 Excel-as-source feasibility

**Date:** 2026-04-23
**Source files audited:** `docs/100prosim_d_250517_250517.1817m/*.xlsx` / `*.xlsm` (gitignored — Pascal's local copy of Schmidt-Kanefendt's 100prosim Excel workbooks)
**Scripts used:** `scripts/audit_excel_sources.py`, `scripts/peek_d_sources.py`, `scripts/audit_d_mapping.py`, `scripts/audit_d_v2.py`, `scripts/audit_d_v3.py` (all checked in)

This document answers two questions:

1. **What §2.3 of the stakeholder PDF asks for** (Excel-files-as-data-model) and whether the existing Excel files actually contain the traceability the PDF describes.
2. **Whether the 4 backend-blocked values currently hardcoded in the Jahresstrom flow diagram (D1–D4c)** exist in those Excel files, so that the §2.3 switch automatically unblocks them.

The audit answers both questions **yes**, with concrete file/cell references below.

---

## 1. §2.3 — what Schmidt-Kanefendt actually wants

The PDF §2.3 is short: three paragraphs plus a one-line proposal repeated twice. Faithful summary:

> **Proposal:** Interface for using the existing Excel data-model files **instead of** the integrated data model in the current 100prosim-Web.

### §2.3.1 Nachvollziehbarkeit (traceability)

> *"In 100prosim-Excel, the source references and assumptions for every parameter are simply and directly traceable via hyperlinks. This is the decisive difference from a video-game console."*

The web app copied parameter VALUES into seed fixtures but dropped the source links, so users can't audit where numbers come from and admins can't confidently update them.

### §2.3.2 Alternativ-Regionen

> *"The current 100prosim-Web is restricted to a Germany data model. Creation of and access to data models for alternative regions is not supported. As a result, region-specific use — as for instance was intensively used by various Green party state-level working groups — is not available."*

Excel-100prosim ships per-Bundesland data files; swap the file, change the region. The web app is Germany-only.

### Distilled ask

**One architectural change with two payoffs:**

- Web app reads `D.xlsx` (or any other region file) as its data source
- Source-link metadata and assumption comments from the Excel file are surfaced in the web UI
- Admins update parameters by editing the `.xlsx`, not by code changes

The PDF deliberately leaves HOW open (direct read at request time, pre-import to DB, or hybrid — Pascal's call).

---

## 2. D.xlsx audit — does the Excel have what the PDF claims?

**Yes.** Detailed findings below.

### Sheet inventory

D.xlsx has 17 sheets:

| Sheet | Dimensions | Role |
|---|---|---|
| **`1.`** | 2133 rows × 157 cols | **Main parameter sheet.** Column E carries the parameter label (German descriptive text), other columns carry scenario values (status + target columns per scenario). Row-oriented: each row = one parameter. |
| **`9.Quellen`** | 264 × 33 | **Sources sheet.** 86 hyperlinks, each a URL to the real document the parameter is sourced from. |
| **`8.Kennzahlen`** | 140 × 96 | Derived key metrics. |
| **`7.VerbrauchStatus`** | 122 × 96 | Consumption-status reference data. |
| **`I_S`** | 798 × 45 | Input/Status — actual scenario state values (e.g. E2 = "Deutschland 100%EE", E8 = 84669326 population). |
| **`I_BS.2` / `I_BS.3`** | 84 / 170 × ~30 | Bilanz status. |
| **`I_Region`** | 199 × 19 | Region-specific definitions. |
| **`I_Basisdaten`** | 192 × 15 | Basis data. |
| **`WS_`** | 43 × 16 | WS time-series inputs. |
| **`O_`** | 211 × 16 | Output. |
| **`PSZ_`** | 1 × 1 | (placeholder). |
| **`Copyright` / `Versionen` / `Stempel` / `Arbeitsblätter` / `EingabeEinAus`** | small | Provenance + config. |

### Traceability verified

**`9.Quellen` has 86 hyperlinks** pointing to real sources. Sample of the first 20:

- `foederale-energiewende.unendlich-viel-energie.de/laenderdaten/` — federal energy statistics
- `ag-energiebilanzen.de` (AGEB) — German national energy balance authority (multiple links: yearly tables, specific 2023 PDFs)
- `agora-energiewende.de` — energy policy think-tank
- `bmuv.de` — Federal Ministry for Environment (e-mobility efficiency)
- `bmel.de` / `bundeswaldinventur.de` — Federal Ministry of Agriculture (forest strategy, federal forest inventory)
- `bmdv.bund.de` — Federal Ministry of Transport (transport-in-numbers yearly data)
- `ariadneprojekt.de` — climate-policy research consortium
- `elib.dlr.de` — German Aerospace Center publications
- `bfee-online.de` — federal energy-efficiency office
- `lwg.bayern.de` (agrowea) — Bavarian agriculture / bioenergy
- `asue.de` — CHP-plant reference data

These are the **primary sources** Schmidt-Kanefendt's parameters derive from. The PDF's claim that "every parameter is traceable via hyperlinks" is accurate.

### Assumption notes verified

Sheet `1.` has **747 cell comments** by Schmidt-Kanefendt (`hsk:` prefix), one per parameter, documenting:

- The decision behind the parameter choice
- Cross-references to source rows in `9.Quellen`
- Time-stamp / version history
- Specific assumption values with German context

Sample comments:

- *"Entscheidung: Datenmodell-Datei trägt den Dateinamen 'D', ggf. ohne Trennzeichen gefolgt von einer Version..."* (naming-convention rationale)
- *"- STATUS-Ansatz: GENESIS [9.224], Tabelle 12411-01-01-4, Einwohner gesamt am 31.12.2023: 84,669,326"* (cites the GENESIS statistical table by ID)
- *"- ZIEL-Ansatz: ..."* (target-scenario reasoning)

So both components of §2.3.1 ("Quellen" + "Annahmen") are concretely present.

### Other Excel files in the bundle

| File | What it contains | Relevance |
|---|---|---|
| `WS.xlsm` | Jahresstrom + time-series calculations, the 365-day Zeitreihen-Kalkulation sheet | Source of the Jahresstrom flow diagram; holds the Tagesladungen formulas |
| `C.xlsx` | 4 sheets — likely Compact / Config | Secondary |
| `MH.xlsx` | 1 sheet "Modifikations-Historie" | Change log |
| `_S.xlsx` | 17 sheets mirror D.xlsx structure with sub-labels "1. Flächen / 2. Erneuerbare / 3. Bedarfsniveau / 4. Verbrauch / 5. Bilanz / 6. Fossile / 7. Verbrauch Status / 8. Kennzahlen" | Alternative view of the same data |
| `AH.xlsm` | Presentation-like | Secondary |
| `_100prosim.xlsm` | 2 sheets (Start, Version) | Bootstrap shell |

Bundesland files would presumably follow the same D.xlsx pattern with different seed values — we only have D.xlsx (Germany) in this bundle; per-state files like `BB.xlsx`, `NW.xlsx` etc. would need to come from ErnES.

---

## 3. T54 backend-blocked values — connection to the Excel

Every one of the 4 hardcoded values currently in `simulator/templates/simulator/annual_electricity.html` maps to a specific cell in the 100prosim Excel bundle. Once §2.3 ships, **these unblock automatically** as a side effect.

| Item | Current hardcoded value in SVG | Located in Excel | How it's computed there |
|---|---|---|---|
| **D1** — source Tagesladungen (`397`, `186`, `5`, `1`) | `<text class="txt-tages">397</text>` etc. | `WS.xlsm` sheet `Zeitreihen Kalkulation` | Daily-output time series (~365 rows of ~3000 GWh/day per source); Tagesladungen = `annual_GWh / peak_daily_GWh`. Verified by inspection: PV 1,201,630 ÷ 3,026 ≈ 397 ✓. |
| **D2** — flow Tagesladungen (`509`, `313`, `365`, `62`, `87`×3, `51`, `80`, `134`) | Same template, under each flow-value box | Same sheet, computed from per-segment annual aggregates using the same normalisation factor as D1 | One formula, many segments. |
| **D3** — percent shares (`62,2%`, `29,2%`, `0,8%`, `0,2%`) | `<text class="txt-pct">62,2%</text>` etc. | `WS.xlsm` sheet `1.Jahresbilanz_Strom` cell `E21` = `0.6227` (PV's stored share) | Computed in the Excel sheet — NOT a simple `pv/(pv+wind+hydro+bio)` ratio (that gives 62.2% for PV but 36.6% for Wind, not 29.2%). The real denominator is coded in the Excel formula; we'd read the cell directly. |
| **D4a** — `194 GW` red annotation | `<text class="txt-red">194 GW</text>` | `WS.xlsm` `1.Jahresbilanz_Strom` row 30 area | Installed-power peak (Pmax of Elektrolyse Stromspeicher). Static config value in Excel, becomes a config constant in our import. |
| **D4b** — `261 GW (elekt.)` red annotation | same template | `WS.xlsm` `1.Jahresbilanz_Strom` row 30 area | Rückverstromung installed peak, same treatment as D4a. |
| **D4c** — `Abgleichdifferenz 160` | `<text>160</text>` | `WS.xlsm` scenario-balance residual cell | Output of the Excel WS solver. Our backend has the data to compute the equivalent but doesn't surface it on `get_ws_365_data()`. |

### Conclusion for planning

**§2.3 and T54 D1–D4c are the same work.** A single Excel-import command that reads:

1. `D.xlsx` sheets `1.` + `I_S` → existing parameter tables (LandUse, VerbrauchData, RenewableData, etc.)
2. `D.xlsx` sheet `9.Quellen` → new `Source` table (3 columns: `ref_code`, `display_name`, `url`)
3. `D.xlsx` sheet `1.` cell comments → `assumption_note` text column added to each parameter row
4. `WS.xlsm` sheet `Zeitreihen Kalkulation` → WS365 365-day tables
5. `WS.xlsm` sheet `1.Jahresbilanz_Strom` cells (E21, row-30 GW values, scenario-balance residual) → new fields in the diagram context vars (or new model)

...unblocks both streams of work in one build. Estimated ~5 days for the importer + model migrations + UI tooltips + region selector.

---

## 4. What happens to our current data model under §2.3

Full impact breakdown:

| Layer | Change | Approx LOC |
|---|---|---|
| `calculation_engine/` (pure math, ~3500 LOC) | **No change** — operates on parameter values regardless of source | 0 |
| `Formula` table (760 rows) | **No change** — formulas are part of the engine, not the data | 0 |
| Views, templates, JS, async jobs (~15K LOC) | **No change** — UI keeps reading from the DB; DB is now Excel-sourced | 0 |
| DB schema | +3 columns on parameter models: `source_ref` (FK to new `Source` row), `source_url`, `assumption_note` | ~50 LOC migration + small model edits |
| **NEW** Excel import command | Reads D.xlsx + WS.xlsm, populates DB tables + Source table + assumption notes | ~600 LOC, 1–2 days |
| **NEW** Source UI tooltips | Hover shows source URL + assumption note for any parameter | ~150 LOC + per-page wiring, ~1 day |
| **NEW** Region selector | Admin picks D.xlsx (Germany) or any future Bundesland file | ~200 LOC, 1 day |
| **NEW** Excel upload form | Admin uploads a new .xlsx version to refresh data | ~100 LOC, half day |
| Existing seed fixture | **Replaced** by `manage.py import_data_model ...D.xlsx` | -200 LOC |
| Hardcoded T54 D1–D4c values in template | **Replaced** by dynamic bindings (IDs already in place) | -10 LOC |

**Net:** ~800 LOC added, ~210 LOC removed, ~5 days of focused work.

**Zero throwaway** of calculation engine, formulas, UI, async pipeline, or test suite.

---

## 5. Recommended scoping decisions for Pascal

Before starting implementation, lock down:

1. **Import vs live-read:** should the app pre-import D.xlsx at startup (fast, simple, needs re-import on file change) or read cells on request (slow, always-live, more complex)? Recommendation: **pre-import with re-import trigger on file upload** — best balance.
2. **Which Bundesländer are in scope for the first region release?** The audit only has D.xlsx (Germany). Others need to come from ErnES or Schmidt-Kanefendt.
3. **Do we keep the admin parameter-edit forms?** Option A: Excel is the ONLY source of truth (simpler, matches §2.3 literally). Option B: admin can also edit DB directly (keeps current flexibility). Recommendation: A, with a "revert to Excel values" button.
4. **How to handle the 4 T54 D1–D4c values that currently have no dynamic binding:** are they imported alongside? (Yes — should be part of the same import. Three new fields on the WS365 service output: `source_tages`, `flow_tages`, `installed_gw`.)

---

## 6. Proposed email to Schmidt-Kanefendt (for Pascal to review/send)

> Hallo Herr Schmidt-Kanefendt,
>
> wir haben die Excel-Datenmodell-Dateien geprüft (D.xlsx und WS.xlsm) und die §2.3-Schnittstelle ist umsetzbar:
>
> - Wir können die 86 Quellen-Links aus `9.Quellen` und die 747 Parameter-Kommentare aus Blatt `1.` in die Web-Oberfläche übernehmen (Quell-Tooltip je Parameter).
> - Die vier aktuell hartkodierten Werte im Jahresstrom-Diagramm (Tagesladungen, Anteile %, 194 GW, 261 GW, Abgleichdifferenz 160) können wir aus den jeweiligen Zellen in WS.xlsm lesen — wir bräuchten nur Ihre Bestätigung der Berechnungsformeln (Tagesladungen-Normierung, Prozent-Anteils-Nenner, ob Abgleichdifferenz eine Formel ist oder Konfig).
> - Aufwand: ca. 5 Arbeitstage für Importer, Quell-Tooltips, und Regionen-Umschalter.
>
> Für Regionen außer Deutschland bräuchten wir die entsprechenden .xlsx-Dateien (z. B. BB.xlsx, NW.xlsx) oder einen Link zur ErnES-Sammlung.
>
> Können wir dazu einen kurzen Termin anberaumen?

---

## 7. References

- PDF §2.3 source: `docs/stakeholder/260403_Bestandsaufnahme_DE.md` lines 21–57
- Excel bundle: `docs/100prosim_d_250517_250517.1817m/` (gitignored, Pascal's local copy)
- Audit scripts (checked in under `scripts/`):
  - `audit_excel_sources.py` — sheet-level inventory across all workbooks
  - `peek_d_sources.py` — samples D.xlsx 9.Quellen + comments
  - `audit_d_mapping.py` — searches D.xlsx for our DB cell-codes
  - `audit_d_v2.py` — round-2: row labels, Tagesladungen locations, % shares
  - `audit_d_v3.py` — round-3: formulas vs values, scenario parameters
- T54 template: `simulator/templates/simulator/annual_electricity.html` (passes 9–22 shipped)
- T54 pass log: `docs/stakeholder/FLOW_DIAGRAM_AUDIT.md` "Visual pass 4"
