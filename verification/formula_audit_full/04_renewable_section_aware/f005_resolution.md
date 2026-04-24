# F005 resolution — Biogas Nutzungsgrad proven

## Round 1 state

F005 was logged as **HIGH-if-confirmed / MEDIUM confidence** because
the fuzzy matcher collapsed `5.4.2.3` (Biogas KWK-Abwärme effektiv,
DB = 21.9/25) and `6.1.3.2.3` (Biodiesel KWK-Abwärme effektiv,
DB = 50/50) onto the same Excel row (`2. Erneuerbare!L86 = 45/45`).
Since only one of them could be Excel row 86, the matcher picked
wrong at least once — UNPROVEN which side was wrong.

## Round 2 curated section-aware mapping result

The section-aware mapping (built in §01 using
`(category, subcategory)` tuples) places the two rows in different
Excel sections:

| DB code | DB category/sub | DB status/ziel | Excel cell | Excel status/ziel | verdict |
|---------|-----------------|---------------:|------------|------------------:|---------|
| `5.4.2.1` | Biogas / Main | 37.5 / 45 | `2. Erneuerbare!L84` (Nutzungsgrad Kraftwerk) | 25 / 35 | **DRIFT** |
| `5.4.2.3` | Biogas / Main | 21.9 / 25 | `2. Erneuerbare!L86` (Nutzungsgrad KWK-Abwärme effektiv) | 45 / 45 | **DRIFT** |
| `6.1.3.2.3` | Biogene Brennstoffe (flüssig) / Biodiesel Details | 50 / 50 | `2. Erneuerbare!L136` (Nutzungsgrad KWK-Abwärme effektiv) | 50 / 50 | **EXACT** ✓ |

## Interpretation

1. **`6.1.3.2.3` (Biodiesel KWK-Abwärme) is EXACTLY CORRECT** —
   the curated mapping points to row 136 (Biogene Brennstoffe section),
   and DB matches Excel at 50/50.

2. **`5.4.2.1` (Biogas Nutzungsgrad Kraftwerk) has REAL DRIFT** —
   DB has status=37.5, ziel=45; Excel has status=25, ziel=35.
   The drift is 50 % (status) / 28 % (ziel). This means the Biogas
   power-plant efficiency factor in our seed is ~12 percentage points
   higher than Excel's.

3. **`5.4.2.3` (Biogas Nutzungsgrad KWK-Abwärme effektiv) has REAL
   DRIFT** — DB has status=21.9, ziel=25; Excel has 45/45. The DB
   value is LOWER, ~23 pp. This could affect the Biogas heat-recovery
   contribution to Wärme totals.

## F005 disposition

**Closed as PROVEN.** Biogas Nutzungsgrad seed values in DB diverge
from Excel by 12-23 percentage points. This is NOT a mapping bug;
it's a **seed value drift** similar to F001 (LU_2.1 user_percent),
F003 (VerbrauchData[3.2.2] ziel).

Severity of confirmed finding: **HIGH** (efficiency factors
propagate to GWh/a conversions; a 12 % Nutzungsgrad error translates
to a proportional error in downstream energy accounting).

## Recommended fix

Update Biogas seed values in `seed/sqlite_seed.json`:
- `5.4.2.1.status_value`: 37.5 → 25
- `5.4.2.1.target_value`: 45 → 35
- `5.4.2.3.status_value`: 21.9 → 45
- `5.4.2.3.target_value`: 25 → 45

(Subject to Pascal's confirmation that Excel is the source of truth
for these factors.)

## Evidence

- `04_renewable_section_aware/per_row_parity.csv` rows for codes
  `5.4.2.1`, `5.4.2.3`, `6.1.3.2.3`.
- `01_curated_mappings/renewable_to_excel.csv` section-aware
  mapping entries.
- `_S.xlsx!2. Erneuerbare!L84, L86, L136` cached values:
  25, 45, 50 respectively.
