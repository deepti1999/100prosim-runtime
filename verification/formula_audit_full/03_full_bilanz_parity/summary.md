# §03 Full Bilanz Parity — summary

## Inputs

- **Engine source**: `calculation_engine.bilanz_engine.calculate_bilanz_data()`
- **Excel source**: `_S.xlsx!5. Bilanz` — both status section (rows 9-27) and ziel section (rows 51-66).
- **Coverage**: 6 energy carriers × 3 roles (total/renewable/fossil) × 5 sectors (KLIK/GW/PW/MA/total) × 2 views (status/ziel) = **180 cells**.

## Row count — 180/180 every cell compared

| verdict | count | % |
|---------|------:|----:|
| EXACT | 16 | 8.9 % |
| PASS (≤ 0.1 %) | 8 | 4.4 % |
| PASS_COSMETIC (≤ 0.01 %) | 11 | 6.1 % |
| PASS_LOOSE (≤ 1 %) | 10 | 5.6 % |
| DRIFT (> 1 %) | 54 | 30.0 % |
| NO_ENGINE_EQUIV | 60 | 33.3 % |
| NO_MATCH | 21 | 11.7 % |

**45/180 = 25 %** cells pass at 1 % tolerance. **54 DRIFT** at > 1 %.

## By section

| section | compared | EXACT/PASS | DRIFT | NO_ENGINE_EQUIV |
|---------|---------:|-----------:|------:|----------------:|
| Strom | 30 | 12 | 18 | 0 |
| Brennstoff gasförmig | 30 | 12 | 14 | 0 (engine merges all fuels) |
| Brennstoff flüssig | 30 | 0 | 0 | 30 (no engine equivalent) |
| Brennstoff fest | 30 | 0 | 0 | 30 |
| Wärme | 30 | 12 | 6 | 0 |
| Gesamt | 30 | 14 | 16 | 0 |

## Per-section files under `per_section/`

- `Strom.md` — Status 15 + Ziel 15 cells; F007 + F008 dominate drift.
- `Brennstoff_gasfoermig.md` — engine's `verbrauch_fuels` merges gas+liquid+solid; 14 DRIFT (F012).
- `Brennstoff_fluessig.md` — all NO_ENGINE_EQUIV; F012.
- `Brennstoff_fest.md` — all NO_ENGINE_EQUIV; F012.
- `Waerme.md` — Status Wärme renewable GW = 0 vs Excel 32,783 (F011).
- `Gesamt.md` — Ziel renewable per-sector drift 16-80 % (F013).

## Findings produced in §03

| ID | Severity | Confidence |
|----|---------:|-----------:|
| F011 — `verbrauch_heat_renewable` returns 0 vs Excel 32,783 | HIGH | HIGH |
| F012 — fuels aggregated; no per-carrier breakdown | MEDIUM | HIGH |
| F013 — Ziel renewable per-sector uses Strom-only subcodes instead of totals | HIGH | HIGH |

## Completeness attestation

- [x] All 180 cells compared (6 sections × 3 roles × 5 sectors × 2 views).
- [x] Per-section files written: 6/6.
- [x] Every DRIFT row appears in `discrepancies.md` with engine/excel/drift/cell.
- [x] Every NO_ENGINE_EQUIV cell has the Excel value recorded with that verdict.
- [x] Tolerance ladder applied: 0.01 % (PASS_COSMETIC), 0.1 % (PASS), 1 % (PASS_LOOSE), > 1 % (DRIFT).

## Artifacts

- `all_sections.csv` — 180 rows
- `summary.md` — this file
- `discrepancies.md` — DRIFT rows table
- `per_section/*.md` — 6 section-specific tables
