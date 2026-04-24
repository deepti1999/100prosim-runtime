# F001 — LU_2.1 Solare Freiflächen: user_percent seed drift

**Severity**: HIGH
**Affects calc**: YES — visible ziel value is 23% short of scenario.
**Domain**: §2 value parity (LandUse)
**Confidence**: HIGH — direct cell inspection + parent-ratio recompute.

## Observed

| field | DB (owner=None) | Excel `_S.xlsx!1. Flächen` |
|-------|-----------------|----------------------------|
| `status_ha` | 19,628.0 | `I13` = 19,627.65  (PASS_COSMETIC) |
| `target_ha` | 684,640.80 | `L13` = **887,749.85** |
| `user_percent` | **3.856 %** | `R13` = **5** |
| parent (LU_2) `target_ha` | 17,754,997 | `L12` = 17,754,997 (match) |

Drift on `target_ha`: `|684640.80 − 887749.85| / 887749.85 = 22.9 %`.

## Why they disagree

Excel cell `L13` is computed by:
```
=IF(R13="",AF13,IF(T13="",INDIRECT("L"&AB13)*R13/100,R13))
```
With `R13 = 5`, `T13 = ""`, `AB13 = 12` → `L13 = L12 × 5/100 = 17754997 × 0.05 = 887749.85`.

Our DB row instead computes the same product with a different percent:
`17754997 × 0.03856 ≈ 684641`.

So the *shape* of the calc is correct — it is the **seed value for
`user_percent`** that diverges: 3.856 % in the DB, 5 % in the Excel
scenario.

## Evidence

- `docs/100prosim_d_250517_250517.1817m/_S.xlsx!1. Flächen!R13` cached value `5`, formula literal `5`.
- `docs/100prosim_d_250517_250517.1817m/_S.xlsx!1. Flächen!L13` cached value `887749.85`.
- DB read (owner=None):
  ```
  LU_2.1 Solare Freiflächen status=19628.0  target=684640.80  pct=3.856
  ```
- Parent LU_2 target_ha in both sources = 17,754,997 ✓

## What "correct" looks like

`LandUse.user_percent` for code `LU_2.1`, global seed row, should be
**5.0** — matching the Excel Ziel-Modifikation column. With that
value the ziel cascades through `workspace_service` /
`percentage_rebalancer` to produce the 887,749.85 ha the scenario PDF
expects.

## What we currently do

The seed shipping today gives `user_percent = 3.856`, producing
`target_ha = 684,640`. Downstream sums (LU_2.4 residual, Bilanz
Flächen totals) shift to absorb the 203 kha gap — see F002.

## Recommended fix (one line)

Update the `LandUse` global seed row for `LU_2.1` to set
`user_percent = 5.0` (and let cascade recompute `target_ha =
887749.85`).

## Scripts

- `verification/formula_audit/scripts/04_value_parity.py` produced
  `01_value_parity/per_row_comparison.csv` row `LU_2.1`.
- Spot-check script run inline in this audit session.
