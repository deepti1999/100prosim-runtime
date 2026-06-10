# F003 — VerbrauchData[3.2.2] Zieleinfluss Prozess-Effizienz: ziel seed drift

**Severity**: HIGH
**Affects calc**: YES — efficiency multiplier for Prozesswärme sector ziel.
**Domain**: §2 value parity (VerbrauchData)
**Confidence**: HIGH — direct cell inspection.

## Observed

| field | DB (owner=None) | Excel `_S.xlsx!4. Verbrauch!M32` |
|-------|-----------------|----------------------------------|
| `status` | 100.0 % | `L32` = 100 (match) |
| `ziel` | **89.00004 %** | `M32` = **95** |
| `user_percent` | None | Excel `P32` = None (no modifikation) |
| `is_calculated` | False | |

Drift on ziel: 6.3 % relative, 6 pp absolute.

## Why it matters

`3.2.2 Zieleinfluss Prozess-Effizienz` is one of 4 efficiency
multipliers in the Prozesswärme (PW) sector. Dropping it from 95 to
89 lowers the ziel PW end-energy by ~6.3 %, which propagates into:

- Bilanz sheet 5 PW total column.
- `3.7 Endenergieverbrauch PW gesamt` (observed 0.9 % short — see F005).
- Overall national energy total shift.

The Excel `M32` is a hand-set scenario parameter (95), not a computed
cell. So the drift is a **seed value mismatch**, not a formula bug.

## Evidence

- `_S.xlsx!4. Verbrauch!L32` = 100, `M32` = 95 (cached value,
  no formula — literal seed).
- DB `VerbrauchData(owner=None, code='3.2.2').ziel = 89.00004`.

## Secondary cross-check — VerbrauchData[1.1.2]

The sibling row `VerbrauchData[1.1.2] Zieleinfluss
Endanwendungs-Effizienz` (a.k.a. KLIK Haushalte efficiency) is
correct:

| field | DB (owner=None) | Excel `4. Verbrauch!M25` |
|-------|-----------------|--------------------------|
| ziel | 95.0 | 95 |

So the drift is isolated to 3.2.2, not a systemic miss across all
Zieleinfluss rows.

## Recommended fix

Update the global-seed `VerbrauchData[3.2.2].ziel` from `89.00004` to
`95.0`. This is a 6 pp seed correction; rerunning the cascade will
pull PW sector totals up ~6 %.

## Scripts

CSV row `VerbrauchData/3.2.2` in `01_value_parity/per_row_comparison.csv`.
Direct spot-check inline in session.
