# §4 Bilanz Parity — summary

## Inputs

- **DB source**: `calculation_engine.bilanz_engine.calculate_bilanz_data()` (the same function that powers the `/bilanz/` page).
- **Excel source**: `_S.xlsx!5. Bilanz` rows 9-11 (Strom: verbrauch / renewable / fossil). Liquid (rows 15-17) and solid (rows 18-20) fuels were not compared in this pass (deferred).
- **Script**: `scripts/07_bilanz_parity.py`.

## Cells compared — 15

| section | cells |
|---------|------:|
| Verbrauch Strom (total) | 5 (KLIK, GW, PW, MA, total) |
| Verbrauch Strom (renewable) | 5 |
| Verbrauch Strom (fossil) | 5 |

## Verdict distribution

| verdict | count |
|---------|------:|
| PASS (≤ 0.1 %) | 2 |
| PASS_COSMETIC (0.1–1 %) | 1 |
| DRIFT (> 1 %) | 12 |

## Headline

**12/15 cells diverge > 1 %**. Two root causes identified:

1. **F007 (CRITICAL)** — `verbrauch_strom.gebaeudewaerme` = 0 in engine, Excel = 32,877 GWh/a. Caused by (a) `strom_codes.gebaeudewaerme = '2.9.2'` mapping to the heat-pumps-only subcode rather than the GW-electricity total (`2.9.0`), and (b) a fallback-to-zero bug in `get_verbrauch_value` when a row is `is_calculated=True` but has no status formula.

2. **F008 (HIGH)** — `verbrauch_strom.mobile` = 28,136 GWh/a, Excel = 15,300 GWh/a. Caused by the same class of mapping error: `strom_codes.mobile = '6.2'` captures a DB value that differs from Excel's per-capita-derived MA Strom by 84 %. Subcode enumeration needed to confirm the right target.

Secondary drifts (KLIK renewable +1.2 %, PW 6.85 %) likely follow
downstream from the two primary mismatches (any fossil residual =
total − renewable, so once the total is off the fossil is off too).
PW's 6.85 % could also be a legitimate scenario-value difference
between DB seed and Excel scenario.

Renewables total `verbrauch_strom_renewable.gesamt = 242,606` vs
Excel U10 = 242,642 — **PASS** (drift 0.015 %). So the renewable
*aggregate* is right; the problem is specifically in how our engine
builds the per-sector totals.

## Findings produced

| ID | Severity | Confidence |
|----|---------:|-----------:|
| F007 — Bilanz GW Strom engine returns 0 | CRITICAL | HIGH |
| F008 — Bilanz MA Strom subcode drift 84 % | HIGH | MEDIUM |

## Self-skepticism — limitations

1. **Coverage**: only the Strom section was exhaustively compared.
   Fuel (gas, liquid, solid) and heat sections also need the same
   treatment; deferred.
2. **Single-scenario**: engine tested with the DB's default seed
   state. Under different scenarios (e.g. user-mutated workspace)
   the drift pattern may differ.
3. **Root-cause depth**: F008 identifies the symptom but does not
   enumerate the right subcode. Owner needs to walk `6.x` hierarchy
   with Excel's `Q41` per-capita context to pick the correct mapping.

## Self-skepticism checklist

- [x] Multiple tolerances (0.1 % PASS, 1 % PASS_COSMETIC)
- [x] Formula *values* compared (not formula structure here — Bilanz
      is computed, not declarative)
- [x] Single default scenario
- [x] Re-derived from Excel Bilanz cells (not from prior audit notes)
- [x] Found unexpected: F007 + F008 weren't in prior audit

## Artifacts

- `row_by_row.csv` — 15 rows, per-sector comparison.
- `discrepancies.md` — table with drift per cell.
- F007, F008 findings under `09_findings/`.

## Recommendation for follow-up

Extend this pass to the other Bilanz sections: rows 12-14 (gas),
15-17 (liquid), 18-20 (solid), 27-29 (heat). Re-apply the same
row-by-row script logic. Likely more findings in the same class as
F007/F008.
