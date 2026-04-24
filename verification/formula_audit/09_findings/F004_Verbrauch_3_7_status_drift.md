# F004 — VerbrauchData[3.7] Endenergieverbrauch PW gesamt: status drift

**Severity**: MEDIUM — 0.9 % status drift on a sector total.
**Affects calc**: YES — visible sector status but within rounding-adjacent range.
**Domain**: §2 value parity (VerbrauchData, Prozesswärme sector total)
**Confidence**: MEDIUM — drift is small enough to be cumulative-rounding rather than a seed bug.

## Observed

| field | DB (owner=None) | Excel `_S.xlsx!4. Verbrauch!L120` |
|-------|-----------------|-----------------------------------|
| `status` | 550,370.90 GWh/a | **555,394.57 GWh/a** |
| `ziel`   | 490,252.61 GWh/a | 490,251.25 GWh/a (PASS_COSMETIC) |

Drift on status: `|550,370.90 − 555,394.57| / 555,394.57 = 0.905 %`.

## Why it might disagree

Row 3.7 is marked `is_calculated=True` — it is a sum of the PW
children (3.3 / 3.4 / 3.5 / 3.6). The 0.9 % drift suggests one of the
PW children has a status value slightly off in the DB vs Excel.

Note: the ziel column is effectively identical (drift < 1 ppm). So
the bug (if any) is status-side only — meaning a seed value in one
of the PW child rows is mis-entered.

## Next steps (not attempted in this pass)

To close this finding, the PW child rows (3.3.0 / 3.4.0 / 3.5.0 /
3.6.0) need per-row verification against Excel cells on sheet
`4. Verbrauch` and/or `3. Bedarfsniveau`. Per-child drill-down is
deferred to §8 (sector totals parity).

## Recommended fix

Identify the single PW child whose `status` does not match Excel.
Correct it in the seed. Re-run the cascade.

## Scripts

CSV row `VerbrauchData/3.7` in `01_value_parity/per_row_comparison.csv`.
