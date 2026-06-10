# Data-model audit — §2.3 Excel-as-source feasibility

**Date:** 2026-04-23 (revised to remove WS.xlsm calculation confusion)
**Source files audited:** `docs/100prosim_d_250517_250517.1817m/D.xlsx` + `_S.xlsx` + related .xlsx files (gitignored — Pascal's local copy of Schmidt-Kanefendt's 100prosim Excel workbooks)
**Scripts used:** `scripts/audit_excel_sources.py`, `scripts/peek_d_sources.py`, `scripts/audit_d_mapping.py`, `scripts/audit_d_v2.py`, `scripts/audit_d_v3.py` (all checked in)

This document answers one question: **what does §2.3 of the stakeholder PDF ask for, and is D.xlsx a viable source?**

For the separate question of where the hardcoded values in the
Jahresstrom flow diagram should come from, see
`docs/stakeholder/HARDCODED_VALUES_TRACE.md`. Those values mostly
come from **our own backend** (not from Excel) and are orthogonal
to §2.3.

---

## 1. What §2.3 actually asks

The German PDF wording is specific. It says:

> **Vorschlag:** Schnittstelle zur Nutzung der bestehenden Excel-**Datenmodell**-Dateien anstelle des integrierten **Datenmodells** im aktuellen 100prosim-Web.

The key word is **"Datenmodell"** (data model) — in 100prosim
terminology that means the **seed parameter values**, not the
calculation logic. Schmidt-Kanefendt is NOT asking us to:

- ❌ replace our WS365 calculation engine (~3,200 LOC of
  `calculation_engine/ws_*.py` + `simulator/ws365_*.py` stays)
- ❌ replace our Bilanz / Verbrauch / Renewable / LandUse engines
- ❌ replace the 760-row `Formula` table
- ❌ replace the UI, async worker, or database schema

He IS asking us to:

1. **Parameter values** currently hardcoded in our seed fixture
   (PV yield per m², population, consumption per capita, installed
   capacities, etc.) — read from D.xlsx instead.
2. **Source references** (the 86 hyperlinks in sheet `9.Quellen`
   pointing to AGEB / BMUV / BMEL / DLR / Ariadne / etc.) —
   surface them in the web UI so users can audit where a number
   came from.
3. **Assumption notes** (the 747 cell comments on sheet `1.`
   prefixed `hsk: | …` documenting each parameter choice) —
   surface them in the web UI.
4. **Region swap** — point at `BB.xlsx` (Brandenburg) instead of
   `D.xlsx` to get Brandenburg-specific parameters; same app,
   different region.

### Rationale from the PDF (§2.3.1 + §2.3.2)

> *"In 100prosim-Excel, the source references and assumptions for
> every parameter are simply and directly traceable via
> hyperlinks. This is the decisive difference from a video-game
> console."*

Without source links, admins can't confidently update values and
users can't audit where numbers come from. And:

> *"The current 100prosim-Web is restricted to a Germany data
> model. Creation of and access to data models for alternative
> regions is not supported. As a result, region-specific use — as
> for instance was intensively used by various Green party
> state-level working groups — is not available."*

Region swap in Excel is trivial (change which file you open).
Region swap in our current web app requires a code change.

---

## 2. D.xlsx audit — does it contain what the PDF claims?

**Yes.** The file has exactly the structure §2.3 describes.

### Sheet inventory

D.xlsx (version `250517.1733_hsk`) has 17 sheets:

| Sheet | Dimensions | Role |
|---|---|---|
| **`1.`** | 2133 × 157 | **Main parameter sheet.** Column E has the parameter label (German descriptive text); other columns hold scenario values (status + target per scenario variant). Row-oriented: each row = one parameter. |
| **`9.Quellen`** | 264 × 33 | **Sources sheet.** 86 hyperlinks, each a URL to the real document the parameter derives from. |
| **`8.Kennzahlen`** | 140 × 96 | Derived key metrics. |
| **`7.VerbrauchStatus`** | 122 × 96 | Consumption-status reference data. |
| **`I_S`** | 798 × 45 | Input/Status — scenario state snapshot (e.g. `E2 = "Deutschland 100%EE"`, `E8 = 84669326` population). |
| **`I_BS.2` / `I_BS.3`** | 84 / 170 × ~30 | Bilanz status. |
| **`I_Region`** | 199 × 19 | Region-specific definitions. |
| **`I_Basisdaten`** | 192 × 15 | Basis data (installed capacities, areas, etc.). |
| **`WS_`** | 43 × 16 | WS time-series inputs (parameters for the WS engine — still "Datenmodell", not calculations). |
| **`O_`** | 211 × 16 | Output mirror. |
| **`Copyright` / `Versionen` / `Stempel` / `Arbeitsblätter` / `EingabeEinAus`** | small | Provenance + config. |

### Traceability verified — 86 source hyperlinks

Sheet `9.Quellen` has 86 hyperlinks. Sample of the first 20 (all confirmed to resolve to real documents):

- `foederale-energiewende.unendlich-viel-energie.de/laenderdaten/`
- `ag-energiebilanzen.de` — AGEB, Germany's national energy-balance authority (year-tables + specific 2023 PDFs)
- `agora-energiewende.de` — energy-policy think-tank
- `bmuv.de` — Federal Ministry for Environment (e-mobility efficiency)
- `bmel.de`, `bundeswaldinventur.de` — Federal Ministry of Agriculture (forest strategy, federal forest inventory)
- `bmdv.bund.de` — Federal Ministry of Transport (transport-in-numbers yearly data)
- `ariadneprojekt.de` — climate-policy research consortium
- `elib.dlr.de` — German Aerospace Center publications
- `bfee-online.de` — federal energy-efficiency office
- `lwg.bayern.de` + `agrowea.de` — Bavarian agriculture / bioenergy
- `asue.de` — CHP-plant reference data

These are the **primary sources** Schmidt-Kanefendt's parameters derive from. The PDF's claim that "every parameter is traceable via hyperlinks" is accurate.

### Assumption notes verified — 747 comments

Sheet `1.` has 747 cell comments, one per parameter, prefixed
`hsk: |`. They document:

- The decision behind the parameter choice
- Cross-references to source rows in `9.Quellen`
- Timestamp / version history
- Specific assumption values with German context

Sample:

- *"Entscheidung: Datenmodell-Datei trägt den Dateinamen 'D', ggf. ohne Trennzeichen gefolgt von einer Version..."* (naming-convention rationale)
- *"- STATUS-Ansatz: GENESIS [9.224], Tabelle 12411-01-01-4, Einwohner gesamt am 31.12.2023: 84.669.326"* (cites the GENESIS statistical table by ID)
- *"- ZIEL-Ansatz: …"* (target-scenario reasoning)

Both components of §2.3.1 ("Quellen" + "Annahmen") are concretely present.

### Other workbooks in the bundle (NOT §2.3 targets)

| File | Contents | Relevance to §2.3 |
|---|---|---|
| **`WS.xlsm`** | Jahresstrom + Zeitreihen Kalkulation + WS_ sheets — this is where the **calculation** happens | NOT a §2.3 target. Our backend (`calculation_engine/ws_engine.py` + `simulator/ws365_*.py`, ~3,200 LOC) already does the equivalent calculations. |
| `C.xlsx` | Compact / config | Secondary, not parameter-data |
| `MH.xlsx` | "Modifikations-Historie" change log | Not a data source |
| `_S.xlsx` | 17 sheets mirror D.xlsx structure with sub-labels | Same data, different view — we'd import D.xlsx directly, not this |
| `AH.xlsm` | Presentation-like | Not a data source |
| `_100prosim.xlsm` | 2 sheets (Start, Version) | Bootstrap shell only |

**Conclusion: §2.3 = import D.xlsx. WS.xlsm is not in scope for §2.3.**

### Bundesland files

We only have D.xlsx (Germany) in Pascal's local bundle. Per-state
`.xlsx` files (e.g. `BB.xlsx`, `NW.xlsx`) would need to come from
ErnES. The import architecture should be **file-agnostic** (any
`.xlsx` following the D.xlsx shape works), so adding a new region
is just "upload the file".

---

## 3. What changes on our side

Only **additive** changes. The import layer is new; the
calculation engine, formulas, UI, and async pipeline stay
untouched.

| Layer | Change | Approx LOC |
|---|---|---|
| `calculation_engine/` (pure math, ~3,500 LOC) | **No change** | 0 |
| `simulator/ws365_*.py`, `ws_365_service.py` (~2,750 LOC) | **No change** | 0 |
| `Formula` table (760 rows) | **No change** | 0 |
| Views, templates, JS, async jobs (~15K LOC) | **No change** | 0 |
| DB schema | +3 columns on parameter models: `source` (FK to new `Source` row), `source_url`, `assumption_note` | ~50 LOC migration + small model edits |
| **NEW** `Source` model | 3 columns: `ref_code`, `display_name`, `url` — one row per `9.Quellen` hyperlink | ~20 LOC |
| **NEW** `Region` model | `code`, `display_name`, `active` | ~20 LOC |
| **NEW** Excel-import management command | Reads D.xlsx, populates parameter tables + Source rows + assumption notes | ~500 LOC, 1–2 days |
| **NEW** Source UI tooltips | Hover shows source URL + assumption note for any parameter | ~150 LOC, ~1 day |
| **NEW** Region selector + upload | Admin picks active region, uploads new .xlsx | ~250 LOC, 1 day |
| Existing seed fixture | **Replaced** by `manage.py import_data_model D.xlsx` | -200 LOC |

**Net:** ~800 LOC added, ~200 LOC removed, ~4 days of focused work.

---

## 4. Open scoping decisions

Before implementing, lock down with Pascal:

1. **Pre-import vs live-read?** Recommend pre-import with re-import
   triggered on file upload. Live-read would require openpyxl on
   every page load — too slow.
2. **Keep admin parameter-edit forms?** Recommend keep + add a
   "Revert to Excel values" button. Admin can override per-scenario
   without losing the Excel source of truth.
3. **Where does the WS_ sheet land?** It contains **parameter
   inputs** to the WS engine (still "Datenmodell"), not
   calculations. Recommend: import it into our existing WS
   parameter tables alongside sheet `1.`.
4. **Which Bundesländer first?** We only have D.xlsx. Ask ErnES
   for the others they want supported at launch.

---

## 5. References

- PDF §2.3 source: `docs/stakeholder/260403_Bestandsaufnahme_DE.md` lines 21–57
- Excel bundle: `docs/100prosim_d_250517_250517.1817m/` (gitignored)
- Audit scripts (checked in under `scripts/`):
  - `audit_excel_sources.py` — sheet-level inventory across all workbooks
  - `peek_d_sources.py` — samples D.xlsx 9.Quellen + comments
  - `audit_d_mapping.py` — searches D.xlsx for our DB cell-codes
  - `audit_d_v2.py` — row labels, Tagesladungen, % shares
  - `audit_d_v3.py` — formulas vs values, scenario parameters
- For the separate hardcoded-value trace (which does NOT import from
  WS.xlsm but comes from our own backend methods + D.xlsx
  configs): `docs/stakeholder/HARDCODED_VALUES_TRACE.md`.
