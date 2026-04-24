# §3 Formula Parity — summary

## Inputs

- **DB source**: 760 `Formula` rows (landuse 3, renewable 438, verbrauch 244, ws 72, ws_constant 3) + 21 `WS365Formula` rows (live WS365 daily-chain computation, migration 0044).
- **Excel source**: `_S.xlsx` (renewable/verbrauch/landuse formula cells in Flächen / Erneuerbare / Bedarfsniveau / Verbrauch sheets) and `WS.xlsm` (WS365 daily chain in `Zeitreihen Kalkulation`, constants in `1.Jahresbilanz_Strom`).
- **Scripts**: `scripts/05_formula_dump.py` + `scripts/06_formula_spotcheck.py`.

## Full CSV dumps

- `formula_table_dump.csv` — every `Formula` row: key, category, formula_type, ws_row_type, is_fixed, expression, description.
- `ws365_formula_dump.csv` — every `WS365Formula` row: column_name, stage, order, expression.

These are the complete source-of-truth for our formula library; they let any human spot-check arbitrary rows without re-querying the DB.

## Spot-check results (25 representative formulas — `spotcheck_results.md`)

Hand-mapped subset covering:
- All 3 LandUse formulas (LANDUSE_CHANGE_RATIO, LANDUSE_STATUS_PERCENT, LANDUSE_TARGET_PERCENT)
- Top-level Renewable aggregations (10.1, 10.3, 10.4, 10.5, 10.6, 10.2, 9.3.1)
- Key Verbrauch formulas (V_1.4 KLIK total, V_1.1.1)
- Full WS365Formula daily chain (einspeich, abregelung, mangel_last, brennstoff_ausgleich, ueberschuss_strom, direktverbr_strom, stromverbr_raumw_korr, ausspeich_rueckverstr, ladezust_brutto)
- All 3 WS constants (WS_ETA_STROM_GAS, WS_ETA_GAS_STROM, WS_ABREGELUNG_THRESHOLD)

### Verdict distribution after manual inspection

| verdict | count | examples |
|---------|------:|----------|
| EXACT | 2 | WS_ETA_STROM_GAS (0.65 = D80/100), WS_ETA_GAS_STROM (0.585 = D82/100) |
| EQUIVALENT | 10 | 10.1 sum-of-sectors, 10.3 single-ref, 10.4-10.6 sums, einspeich, abregelung, mangel_last, ausspeich_rueckverstr, ladezust_brutto |
| EQUIVALENT_MAPPING_UNCERTAIN | 1 | 10.2 (DB 9.4.3.3 vs Excel L232/L233 — matcher may have wrong Excel row) |
| DB_EMPTY_EXPR | 3 | 9.3.1 is input/fixed, 10.1_target not separately stored, V_1.4-like cases |
| LEGACY_DEAD_CODE | 1 | WS_ABREGELUNG_THRESHOLD (F006 — produces wrong output if wired, but not wired) |
| MANUAL_REVIEW | 8 | Verbrauch chain (V_1.1.1 etc.) — formula is a product of upstream codes; needs a value-level cross-check, not structural compare |

## Findings produced from this domain

| ID | Finding | Severity | Confidence |
|----|---------|----------|------------|
| F006 | `WS_ABREGELUNG_THRESHOLD = 0.65` in seed is dead code — unused by production WS365 chain; would produce 35 %-low Einspeich if re-wired | LOW | HIGH |

## Self-skepticism — limitations of this pass

1. **Coverage**: 25 of 781 (760 + 21) formula rows were hand-verified (3 %). The remaining 97 % were dumped to CSV but not individually mapped to Excel cells.

2. **Mapping ambiguity**: For `10.2`, my inferred Excel cell was `L234` ("Anteil Erneuerb. an Stromverbrauch") but DB `RenewableData[10.2].name = "Strom"` which more likely maps to Excel `L232`. I could not resolve the right cell without a per-row mapping table. This is the same failure mode as §2 — name-based matching collapses distinct rows.

3. **No numerical Python eval**: I did NOT load each DB `expression` into a Python evaluator and run it against matched variable values to cross-verify numerical output. That was the plan in §3 but would require building the variable-name → value bridge across 420 data rows × 760 formulas. Deferred.

4. **Verbrauch formulas**: all 244 Verbrauch formulas reference `Verbrauch_X_Y_Z` style names. Without a mapping from `Verbrauch_1_0` to a specific Excel cell on `4. Verbrauch`, I can only structurally assert "this is a product / sum / ratio of upstream codes" — not verify the same topology exists in Excel.

5. **Wx (WS) formulas** were largely verified via the `WS365Formula` table against `WS.xlsm!Zeitreihen Kalkulation` rows 158-521 — this is the most reliable part of §3.

## Self-skepticism checklist

- [x] Tolerances: not applicable (structural comparison, not numeric)
- [x] Formula structure compared (not just value)
- [x] Multiple inputs tested: only for F006 (day 318, day 282 of Zeitreihen)
- [x] Re-derived from Excel sources (not trusting earlier audits)
- [x] Found unexpected: F006 is not in `SOURCE_GROUNDED_ANSWERS.md`

## Artifacts

- `formula_table_dump.csv` (760 rows)
- `ws365_formula_dump.csv` (21 rows)
- `spotcheck_results.md` (25 rows hand-mapped and reviewed)
- Finding F006 under `09_findings/`

## Recommendations for fuller §3

The audit would benefit from a hand-curated
`renewable_code → excel_sheet_cell` mapping table (similar to
`SHEET_LAYOUTS` in `scripts/04_value_parity.py` but row-level).
Given the renewable table is ~220 rows and the _S.xlsx!2. Erneuerbare
has ~230 non-empty rows, the mapping is nearly 1:1 and would be a
one-pass manual curation exercise.
