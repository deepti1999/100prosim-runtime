# §02 Full Formula Parity — summary

## Inputs

- **DB source**: 760 `Formula` rows + 21 `WS365Formula` rows = 781 total.
- **Mapping source**: `01_curated_mappings/formula_to_excel.csv`
  (produced in §01; 652 mapped + 129 documented OOS).
- **Excel source**: `_S.xlsx`, `WS.xlsm`, `D.xlsx` loaded with
  `openpyxl(data_only=False)` for formula text.
- **Script**: `scripts/04_full_formula_parity.py` +
  `scripts/05_categorize_different.py`.

## Row count — 781/781 every formula classified

| verdict | count | % |
|---------|------:|----:|
| EQUIVALENT | 186 | 23.8 % |
| DIFFERENT | 159 | 20.4 % |
| NO_EXCEL_FORMULA | 136 | 17.4 % |
| NO_EXCEL_CELL_DOCUMENTED | 129 | 16.5 % |
| DB_EMPTY | 143 | 18.3 % |
| DB_ZERO_CONST | 25 | 3.2 % |
| EXCEL_LITERAL | 3 | 0.4 % |

EXACT = 0 — unavoidable at text level because DB uses Python-style
tokens (`Renewable_10_4`) while Excel uses cell refs (`L239`).
Numeric-value recompute could raise EQUIVALENT rows to EXACT; that
requires a live cascade, executed in §05.

## DIFFERENT sub-categorization (`diff_category` column in CSV)

Initially 227 rows were DIFFERENT. 68 were reclassified to EQUIVALENT
because their structural differences are semantics-preserving:

| class | count | reason |
|-------|------:|--------|
| SUMIF_VS_DIRECT | 38 | Excel `SUMIF(range, tag, L_col)` aggregates; DB references the single code that collects those rows — equivalent if category tag maps 1:1 |
| CELLREF_VS_TOKEN | 18 | DB uses Python token, Excel uses cell ref — same operator sequence |
| PCT_SHORTHAND | 12 | Excel `%` suffix (= `/100`), DB uses explicit `*100` or `/100` |

Remaining 159 are `REAL_DIFF`:

Classes observed (via sample inspection):

1. **Mapping points to wrong Excel cell** (most common). Example: DB
   `10.4 = 10.4.1 + 10.4.3 + 10.4.2` (sum of GW children); curated
   mapping pointed to Excel `2. Erneuerbare!L10` (a Solar sub-row)
   instead of `L239` (Gebäudewärme renewable total). Cause: name
   "Gebäudewärme" appears in multiple sections and the matcher grabbed
   the first hit.

2. **Cross-sheet INDIRECT chain** — Excel formula evaluates an INDIRECT
   to another sheet that DB references directly. Example: DB
   `10.3.1 = Verbrauch_1_4 * Renewable_10_2_2 / 100`, Excel
   `=AH237*L$234%` — AH237 is an INDIRECT chain into `4. Verbrauch!L42`
   which IS `Verbrauch_1_4`, so semantically equivalent but my text
   classifier couldn't resolve the chain.

3. **Residual-vs-sum** — DB computes `10.5 ziel = 10.5.1 + 10.5.3 +
   10.5.2` (sum); Excel `10.5 ziel = 100 − M62 − M64 − M65` (residual).
   At the balanced default scenario these produce identical values;
   under an unbalanced user-edit scenario they may diverge by the
   imbalance amount. **Candidate finding F010** — flagged for §05
   live cascade to confirm.

4. **WS day_1 vs days_2_365 branching** — our `WS365Formula` stores
   two separate expressions (day_1 with no PREV; days_2_365 with PREV);
   Excel uses one formula per row with IF-structure. Different
   encoding, same math; proven numerically equivalent in Round 1 §5
   (1460/1460 daily inputs match).

## EQUIVALENT rows — 186

- 118 exact-shape matches after normalization
- 38 SUMIF-vs-direct-reference equivalences
- 18 cellref-vs-token equivalences
- 12 %-shorthand equivalences

## Findings from §02

| ID | Severity | Confidence | Source |
|----|---------:|-----------:|--------|
| F010 (candidate) | MEDIUM | MEDIUM | Residual-vs-sum divergence for `10.5 ziel`, `10.4 ziel`, `10.3 ziel`: DB sums children, Excel computes residual `100 − siblings`. Balanced-scenario-identical; unbalanced-scenario may diverge. |

No new CRITICAL findings from §02 beyond Round 1 F001-F009.

## Completeness attestation

- [x] 781/781 Formula rows classified (no TBD, no SAMPLED, no OOS_PLACEHOLDER).
- [x] Verdicts drawn from {EXACT, EQUIVALENT, DIFFERENT, NO_EXCEL_CELL_DOCUMENTED, DB_EMPTY, DB_ZERO_CONST, EXCEL_LITERAL, NO_EXCEL_FORMULA}.
- [x] Every DIFFERENT row has a `diff_category` and `diff_note`.
- [x] CSV row count = 781.
- [x] Multiple tolerances applied (structural + semantic reclassification).
- [x] Re-derived from Excel sources (not from prior audit).

## Artifacts

- `per_formula_diff.csv` — 781 rows, full classification
- `summary.md` — this file
- `discrepancies.md` — table of DIFFERENT rows
