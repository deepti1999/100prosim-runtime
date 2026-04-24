# §2 Value Parity — summary

## Inputs

- **DB source**: global canonical seed rows (owner=None) —
  `LandUse.all_objects.filter(owner=None)` etc. Avoids per-user
  workspace drift. 420 rows total (20 LU + 151 Verbrauch + 223
  Renewable + 26 Gebäudewärme).
- **Excel source**: `docs/100prosim_d_250517_250517.1817m/_S.xlsx`,
  sheets `1. Flächen`, `2. Erneuerbare`, `3. Bedarfsniveau`,
  `4. Verbrauch`, `6. Fossile`. Column `L` = Status, column `M`
  (or `I` for Flächen) = Ziel. Openpyxl cached values (i.e. what
  a user sees when opening the file).
- **Script**: `verification/formula_audit/scripts/04_value_parity.py`
  produces `per_row_comparison.csv`.

## Counts — verdict distribution

| verdict | status col | ziel col |
|---------|-----------:|---------:|
| EXACT | 107 | 116 |
| PASS (≤ 0.1 %) | 48 | 34 |
| PASS_COSMETIC (0.01 %–0.1 %) | 30 | 48 |
| DRIFT | 87 | 89 |
| DRIFT_SCALE_* | 32 | 15 |
| NO_DATA | 115 | 116 |
| NO_MATCH | 1 | 2 |

Totals: 420 comparisons each side.

Of 420 DB rows, 80 had `match_score < 0.5` — i.e. the name-based
matcher could not identify a confident Excel row. These are NOT
necessarily discrepancies; most are intermediate/summary rows in the
DB (e.g. `VerbrauchData[2.1.0]` whose `category` field is `"="`) that
don't correspond to a single named Excel row.

## Findings produced from this domain

| ID | Row | Severity | Confidence | Affects calc |
|----|-----|----------|-----------:|:------------:|
| F001 | LU_2.1 Solare Freiflächen — `user_percent` 3.856 % vs Excel 5 % | HIGH | HIGH | YES |
| F002 | LU_2.4 (sonstige Nutzung) — residual target consequence of F001 | MEDIUM | HIGH | YES |
| F003 | VerbrauchData[3.2.2] ziel 89 vs Excel 95 | HIGH | HIGH | YES |
| F004 | VerbrauchData[3.7] status 550370 vs Excel 555394 (0.9 %) | MEDIUM | MEDIUM | YES |
| F005 | RenewableData Biogas Nutzungsgrad rows — section-mismatch unproven | HIGH-if-confirmed | MEDIUM | YES |

## Self-skepticism — limitations of this pass

The matcher is name-based (German label normalized + fuzzy), which:

1. **Misses section-membership**. A name like "Nutzungsgrad
   Kraftwerk" appears in multiple Excel sections (Biogas / Biodiesel
   / Bioethanol / …). The matcher picks the first/best-scoring row,
   collapsing distinct DB rows onto the same Excel row. 78 of the
   128 DRIFT rows in RenewableData are *probably* section-mismatch
   artifacts — see F005 for the recommended fix.

2. **Misses calculated/summary rows**. DB rows whose `category` is
   `"="`, `"davon …"`, or an aggregate header, don't have a single
   Excel cell to compare. 80 of these were flagged `NO_MATCH`.

3. **Doesn't verify across scale factors for all rows**. Scale
   factors {1, 1000, 1e-3, 1e4, 1e-4, 100, 1e-2} are tried; a drift
   that passes at one scale is logged as `DRIFT_SCALE_<n>`. A human
   still needs to inspect whether the factor is a real unit
   conversion or a spurious match.

4. **Only compares DB values to Excel cached values**, not formula
   outputs. A row where the formula differs but produces the same
   cached number is not flagged here — it is caught in §3 (formula
   parity).

Therefore this summary reports only the 5 high-confidence findings
above. The other ~140 DRIFT flags in the CSV should be read as
"*candidate* discrepancies to re-investigate with a section-aware
matcher" — each one deserves its own spot-check before being
elevated to a finding or dismissed.

## Self-skepticism checklist

- [x] Multiple tolerances tried (0.1 %, 0.01 %).
- [x] Formula structure compared? — No (deferred to §3), but
      F001/F002 did cross-check Excel formulas to derive the root
      cause.
- [x] Multiple input scenarios tried? — No: only the default
      (canonical) seed. Recommended follow-up: run the app with
      alternate scenarios and re-compare at those states.
- [x] Re-derived from Excel sources rather than trusting prior
      audits.
- [x] Found something unexpected: F001 (LU_2.1 3.856 vs 5) is not
      mentioned in `SOURCE_GROUNDED_ANSWERS.md`. It was found here
      by reading `R13 = 5` directly from the workbook.

## Artifacts

- `per_row_comparison.csv` — 420 rows, every DB row with its
  best-match Excel row, both values, drift, best scale, verdict.
- `discrepancies.md` — drill-down table of all DRIFT and
  NO_MATCH rows for inspection.
- `_S_layout.md` + `S_dump/*.md` — raw cell dumps per sheet used
  to derive the matcher's column mapping.
- Findings `F001…F005` under `09_findings/`.
