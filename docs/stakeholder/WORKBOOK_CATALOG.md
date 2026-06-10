# Workbook catalog — 100prosim Excel bundle

**Date:** 2026-04-23
**Bundle:** `docs/100prosim_d_250517_250517.1817m/` (gitignored, Pascal's local copy of Schmidt-Kanefendt's release)
**Scope:** §2.3 Datenmodell audit — what files exist, what each one does, and how the runtime codebase consumes (or doesn't consume) them.
**Method:** `python scripts/catalog_workbooks.py` + `python scripts/probe_s_xlsx_formulas.py` + `python scripts/probe_s_xlsx_values.py`. Raw output in `scripts/audit_out/{workbook_catalog,s_xlsx_probe,s_xlsx_values_probe}.txt`.

---

## 0. Headline

**Nine `.xls*` files** ship in the 250517.1817m release.

- **Two are first-class data substrate** — `D.xlsx` (parameter values + sources) and `_S.xlsx` (scenario master, 1:1 with our app pages).
- **One is a calculation workbook** — `WS.xlsm` (Jahresstrom / Zeitreihen Kalkulation, with VBA macros).
- **One is a reporting / history workbook** — `AH.xlsm` (Auswertungs-Historie, with VBA macros).
- **One is a cockpit config** — `C.xlsx`.
- **One is a stub / log** — `MH.xlsx` (modifications-history, header only).
- **One is the Excel launcher** — `_100prosim.xlsm` (Start + Version).
- **Two are developer trace dumps** — `trace2.xlsx` (empty), `tracelog.xlsx` (8429-row event log). NOT data sources.

**No file in the bundle is read at runtime by `simulator/` or `calculation_engine/`.** Grep for `\.xls[xm]?` in `simulator/` returns 2 hits — both are inline comments documenting where formulas were ported from (`page_renewable.py:167`, `signals.py:125`); no `openpyxl` / `xlrd` / pandas-Excel imports anywhere in the runtime code.

---

## 1. File inventory (one row per file)

| File | Size | Sheets | VBA | External links | Comments | Hyperlinks | Role for §2.3 |
|---|---:|---:|:---:|---:|---:|---:|---|
| **D.xlsx** | 2.93 MB | 17 | – | 5 | 789 | 89 | **PRIMARY parameter substrate** (Datenmodell) |
| **_S.xlsx** | 0.50 MB | 17 | – | 4 | 123 | 4 | **SCENARIO MASTER** — sheets 1:1 with our app pages |
| **WS.xlsm** | 1.41 MB | 10 | YES | 3 | 25 | 3 | Calculation workbook (Jahresstrom + Zeitreihen) |
| **AH.xlsm** | 0.73 MB | 8 | YES | 3 | 79 | 0 | Auswertungs-Historie (analysis / reporting) |
| **C.xlsx** | 0.08 MB | 4 | – | 1 | 13 | 0 | Cockpit config (small) |
| **MH.xlsx** | 0.01 MB | 1 | – | 0 | 0 | 0 | Modifications-Historie stub |
| **_100prosim.xlsm** | 0.18 MB | 2 | YES | 0 | 0 | 0 | Launcher shell |
| **trace2.xlsx** | 0.01 MB | 1 | – | 0 | 0 | 0 | Empty trace dump |
| **tracelog.xlsx** | 0.82 MB | 2 | – | 0 | 0 | 0 | 8 429-row developer event log |

---

## 2. Per-file detail

### 2.1 `D.xlsx` — primary parameter substrate

- 17 sheets, 2.93 MB. File header (sheet `Stempel`): `D. 250517.1733 hsk`.
- Sheet `1.` is the **monolithic parameter dump** (2 133 rows × 157 cols) — every parameter value + its scenario columns. Carries **747 cell comments** (the `hsk: |` author rationale notes) but **0 hyperlinks** (the hyperlinks live in sheet `9.Quellen`).
- Sheet `9.Quellen` is the **canonical sources list** — 264 rows × 33 cols, **86 hyperlinks** (URLs to AGEB, BMUV, BMEL, Ariadne, DLR, BfEE, etc.). This is the file's traceability contract.
- Other sheets:
  - `7.VerbrauchStatus` (122×96, 6 comments) — consumption status reference data
  - `8.Kennzahlen` (140×96, 6 comments) — derived key metrics
  - `I_BS.2`, `I_BS.3` — Bilanz-status carry-overs from BS.xlsx
  - `I_Region` (199×19) — region-specific definitions
  - `I_Basisdaten` (192×15) — installed capacities, areas, base data per region
  - `I_S` (798×45) — input/status snapshot (e.g. row references for Excel formula links)
  - `WS_` (43×16) — WS engine parameter inputs (still "Datenmodell", not calculations)
  - `O_` (211×16) — output mirror
  - `PSZ_` (1×1, empty) / `Copyright` / `Versionen` / `Stempel` / `Arbeitsblätter` / `EingabeEinAus` — provenance + bookkeeping
- **External link targets** (5 files, paths are HSK-side absolute paths):
  - `verkehr-in-zahlen23-24-excel.xlsx` (BMDV national transport statistics)
  - `_S.xlsx` (the scenario master in this bundle)
  - `BS.xlsx` (Bedarfsstatus — NOT in this bundle)
  - `WS.xlsm` (calculation workbook in this bundle)
  - `_S.xlsx` (a Niedersachsen variant, dated 190916)
- **§2.3 status:** This is the file §2.3 explicitly names ("Excel-Datei (`D.xlsx`)") as the editable per-region datamodell. The 86 hyperlinks satisfy SR-002 (data source); the 747 comments satisfy SR-003 (assumption note).
- **Codebase consumption:** none at runtime. The `mapping_*.csv` files under `scripts/audit_out/` correlate D.xlsx rows to our DB rows by label and value (75 % LandUse / 62 % Renewable / 54 % Verbrauch / 35 % Gebäudewärme; full picture in `DATA_MODEL_IMPORT_AUDIT.md` §5.1).

### 2.2 `_S.xlsx` — scenario master, sheets 1:1 with app pages (this is the key new finding)

- 17 sheets, 0.50 MB. File header (sheet `Stempel`): `_S. 250517.1803 hsk`.
- Sheets named EXACTLY like our app pages:
  - `1. Flächen` (36 × 73) — matches `LandUse` page
  - `2. Erneuerbare` (293 × 92) — matches `RenewableData` page
  - `3. Bedarfsniveau` (53 × 98) — matches Verbrauch upper page (consumption baselines)
  - `4. Verbrauch` (213 × 84) — matches `VerbrauchData` page
  - `5. Bilanz` (71 × 87) — matches `Bilanz` (BB) page
  - `6. Fossile` (93 × 75) — fossil/atomar bookkeeping (mostly orthogonal to our DB models)
  - `7. Verbrauch Status` (101 × 96) — historic consumption status
  - `8. Kennzahlen` (128 × 96) — key metrics
- Plus `0.Titel`, `Copyright`, `Kompatibilität`, `Versionen`, `Arbeitsblätter`, `I_`, `WS_`, `O_`, `Stempel` (provenance + utility sheets shared with D / WS / AH).
- **Per-sheet column shape (verified by `probe_s_xlsx_values.py`):**
  - **col E (5)** = parameter label / row description (German text)
  - **col L (12)** = STATUS value (current scenario)
  - **col M (13)** = ZIEL value (target scenario)
  - col R (18) / col S (19) = derived ratios (status/ziel %, etc.)
  - col D (4) = row number for cross-sheet referencing
- **External link map** (decoded from `xl/externalLinks/_rels/`):
  - `[1]` → `C.xlsx`
  - `[2]` → `WS.xlsm`
  - `[3]` → `BS.xlsx` (Bedarfsstatus — **NOT in our bundle**)
  - `[4]` → `D.xlsx`
- **Formula composition (per app-page sheet):**

  | Sheet | Formulas with `[.]` external ref | Internal formulas | Plain values |
  |---|---:|---:|---:|
  | 1. Flächen | 33 | 466 | 95 |
  | 2. Erneuerbare | 314 | 3 002 | 832 |
  | 3. Bedarfsniveau | 80 | 661 | 114 |
  | 4. Verbrauch | 180 | 1 918 | 425 |
  | 5. Bilanz | 86 | 438 | 86 |
  | 6. Fossile | 130 | 553 | 208 |
  | 7. Verbrauch Status | 302 | 598 | 34 |
  | 8. Kennzahlen | 366 | 262 | 10 |

  i.e. _S.xlsx is mostly **derived** from the four substrate workbooks via formulas. Sheet `8. Kennzahlen` is the most-derived (96 % of cells are external-link formulas, predominantly `'[3]3.'!*` to BS.xlsx).
- **§2.3 status:** This is the **operational view** of the data model. Its sheet names match our app pages 1:1, which means it is the most direct human-readable handoff for parameter values. But it is a **view over four substrate files**, not a substrate itself — its values are computed by the chain `_S = f(D, BS, C, WS)`. Editing _S.xlsx directly would orphan most cells, since most are formula cells.
- **Codebase consumption:** none at runtime. **The previous audit (`DATA_MODEL_IMPORT_AUDIT.md` v1) only looked at D.xlsx and missed _S as the natural app-page-shaped artifact** — Pascal's pushback on that audit is what triggered this catalog.

### 2.3 `WS.xlsm` — calculation workbook (Jahresstrom + Zeitreihen)

- 10 sheets, 1.41 MB, has VBA macros. File header (sheet `Stempel`): `WS. 251118.1022 hsk - BAUSTELLE!` ("under construction" tag in the Stempel).
- Key sheets:
  - `1.Jahresbilanz_Strom` (88 × 71) — annual electricity balance source-of-truth (source for the Jahresstrom flow diagram in our app, see `HARDCODED_VALUES_TRACE.md`)
  - `Zeitreihen Kalkulation` (521 × 56, **15 495 cells**) — the 365-day time series with raw 2023 SMARD data column ("Anlagenpark Deutschland 2023 [SMARD]")
  - `2. Jahresgang Strom` (48 × 43), `2a. Jahresgang segmentiert` (48 × 43) — annual-cycle visualization
  - `Abgleich-Hinweise` (67 × 28) — reconciliation hints
  - `WS_` (36 × 17) — WS-engine parameter pinning
- **External link targets:** `BS.xlsx`, `_S.xlsx`, `verkehr-in-zahlen…xlsx`.
- **§2.3 status:** **Out of scope for §2.3.** §2.3 says "Datenmodell"; WS.xlsm is the calculation engine equivalent. Our `calculation_engine/ws_engine.py` + `simulator/ws365_*.py` (~3 200 LOC) is the ported functional equivalent. WS.xlsm remains useful as a **formula-validation reference** (see `HARDCODED_VALUES_TRACE.md` §4 — Track 1 D1/D2/D3/D4c formulas were lifted directly from WS.xlsm cell formulas).
- **Codebase consumption:** none at runtime; referenced in inline comments in `simulator/page_renewable.py:167` and `simulator/signals.py:125` to document where ported formulas came from.

### 2.4 `AH.xlsm` — Auswertungs-Historie (analysis / reporting)

- 8 sheets, 0.73 MB, has VBA macros.
- Key sheets:
  - `0.Cockpit` (45 × 57)
  - `Cockpit1` (241 × 101, large)
  - `Cockpit2` (222 × 76)
  - `Historie` (133 × 15)
  - `Mon2Dat` (306 × 80)
  - `Monitor` (133 × 41)
  - `I_` (798 × 45) — same shape and size as D.xlsx's `I_S` sheet — likely the same data, snapshotted into AH for reporting
- **External link targets:** 3 files (not enumerated in this audit; presumably D / _S / WS).
- **§2.3 status:** **Out of scope for §2.3.** This is a separate output / monitoring artifact, not the editable data model. Our app's "Modifikations-Details" page (T63 family) covers the same need.
- **Codebase consumption:** none at runtime.

### 2.5 `C.xlsx` — cockpit config

- 4 sheets, 0.08 MB.
- Sheets: `0.Titel` (73 × 100), `I_` (9 × 20, only 137 cells), `O_` (402 × 21), `Versionen` (98 × 15).
- **External link target:** 1 file.
- **§2.3 status:** **Possibly in scope** — `I_` carries some seed inputs that might shape what the launcher shows, but its cell count is small (137). Our app's settings + `Scenario` model cover the rough equivalent. **Not a primary import target.**
- **Codebase consumption:** none at runtime.

### 2.6 `MH.xlsx` — Modifikations-Historie stub

- 1 sheet, 0.01 MB. Single useful cell: A1 = "Cursor muss auf A1 stehen!" (a procedural note for Excel users).
- **§2.3 status:** **Out of scope.** This is a behavioural stub for Excel-side modification logging, not data. Our app's `History` model (T61–T63) is the equivalent.
- **Codebase consumption:** none at runtime.

### 2.7 `_100prosim.xlsm` — launcher shell

- 2 sheets, 0.18 MB, has VBA macros.
- Sheets: `Start` (54 × 15), `Version` (10 × 4).
- **§2.3 status:** **Out of scope.** This is the Excel boot loader.
- **Codebase consumption:** none at runtime; our equivalent is the Django landing page + `_100prosim.xlsm` is irrelevant to the web port.

### 2.8 `trace2.xlsx`, `tracelog.xlsx` — developer trace dumps

- `trace2.xlsx`: empty (1 × 1 sheet, 0 cells).
- `tracelog.xlsx`: 8 429-row event log with timestamps from 2026-02-05. Two sheets (`calc_trace_log`, `Tabelle1`) appear to be near-duplicates.
- **§2.3 status:** **Out of scope** — developer artefacts, not data sources.
- **Codebase consumption:** none.

---

## 3. Topology — how the workbooks reference each other

```
                     +----------------+
                     |  D.xlsx        |   <-- per-region datamodell
                     |  17 sheets     |       (Pascal's bundle has D = Germany)
                     |  747 comments  |
                     |   86 src URLs  |
                     +--------+-------+
                              ^
        external refs from:   |
                +-------------+----------------+
                |             |                |
        +-------+----+ +------+------+  +------+--------+
        |  _S.xlsx   | |  WS.xlsm    |  |  AH.xlsm      |
        |  app-page  | |  Jahres-    |  |  reporting    |
        |  view      | |  bilanz +   |  |  history      |
        | (FORMULAS  | |  Zeitreihen |  |  (VBA)        |
        |  to D, BS, | |  Kalkul.    |  +---------------+
        |  C, WS)    | |  (VBA)      |
        +------------+ +-------------+
                ^
                |  external ref
        +-------+-----+
        |  BS.xlsx    |   <-- Bedarfsstatus (consumption-status)
        |  NOT IN     |       referenced by _S.xlsx as [3] but
        |  BUNDLE     |       not present in Pascal's local copy
        +-------------+

        +------------+  +------------+  +------------------+
        | C.xlsx     |  | MH.xlsx    |  | _100prosim.xlsm  |
        | cockpit    |  | mod-hist   |  | launcher         |
        | config     |  | stub       |  | (boot)           |
        +------------+  +------------+  +------------------+
```

**Read this as:** D.xlsx is the source-of-truth substrate. _S.xlsx is the operational view that mirrors our app pages but its cells are formula-derived from D + WS + C + BS. WS.xlsm is the calculation workbook (already ported to Python). AH.xlsm is reporting (out of §2.3 scope). C / MH / launcher are bookkeeping.

---

## 4. Implications for the §2.3 audit

1. **D.xlsx + _S.xlsx are the two files §2.3 cares about.** D supplies the values + sources + assumptions; _S supplies the app-page shape that maps cleanly onto our DB models.
2. **The previous v1 audit's value-matching against D.xlsx alone undercounts.** _S.xlsx is the better starting point for label-to-app-page mapping: its sheet names ARE our app page names, and its col-L (status) / col-M (ziel) layout IS our DB's status / ziel split. Step C of this audit produces that mapping.
3. **BS.xlsx is missing from Pascal's bundle.** _S references it heavily for `7. Verbrauch Status` and `8. Kennzahlen` (300 + 366 external-ref formulas). For a clean import we either need BS.xlsx from Schmidt-Kanefendt OR we treat the BS-derived rows as `origin='internal'` (we already compute them from our own VerbrauchData + GebaeudewaermeData).
4. **WS.xlsm stays out of scope for §2.3.** Already ported to `calculation_engine/`. Use it only as a formula-reference oracle (as Track 1 did).
5. **AH.xlsm, C.xlsx, MH.xlsx, `_100prosim.xlsm`, trace logs** stay out of scope. Their functional equivalents already exist in the web app or are not relevant to the port.
6. **Hyperlinks live on `D.xlsx!9.Quellen`, comments live on `D.xlsx!1.`.** Any provenance-import tool reads from D, not from _S. _S supplies the app-page-shaped indexing; D supplies the citations and assumption text.

---

## 5. Files / scripts produced by this catalog

- `scripts/catalog_workbooks.py` — reusable catalog extractor.
- `scripts/probe_s_xlsx_formulas.py` — _S.xlsx formula-vs-value composition + external-link decoder.
- `scripts/probe_s_xlsx_values.py` — _S.xlsx app-page-sheet value layout (col E = label, col L = status, col M = ziel).
- `scripts/audit_out/workbook_catalog.txt` — raw output of `catalog_workbooks.py` (352 lines).
- `scripts/audit_out/s_xlsx_probe.txt` — raw output of `probe_s_xlsx_formulas.py` (310 lines).
- `scripts/audit_out/s_xlsx_values_probe.txt` — raw output of `probe_s_xlsx_values.py` (455 lines).

These artefacts are the evidence behind every claim in this catalog. Re-run any of them after a workbook update to refresh.
