# F014 — Renewable yield / Nutzungsgrad cluster drift (5-30 %)

**Severity**: MEDIUM
**Affects calc**: YES — per-row renewable-contribution numbers are 5-30 % off from Excel on the drifting rows.
**Domain**: §04 Renewable section-aware parity
**Confidence**: MEDIUM (68 status + 65 ziel drift rows individually small; collective pattern strong).

## Observed

After the section-aware curated mapping, 68 status + 65 ziel rows
still show > 1 % drift between DB and `_S.xlsx!2. Erneuerbare`. The
drift clusters by parameter type:

1. **Nutzungsgrad (efficiency) factors** — Biogas + Biomasse:
   - `5.4.2.1` (Biogas Kraftwerk): DB 37.5/45 vs Excel 25/35 (F005)
   - `5.4.2.3` (Biogas KWK): DB 21.9/25 vs Excel 45/45 (F005)
   - Biomasse rows ~7.x.x similar pattern, smaller magnitudes.

2. **Flächenertrag (areal yield) factors** — MWh/ha/a:
   - Solarthermie yield: DB 3878 vs Excel 5250 (26 % drift)
   - Biodiesel yield: DB 17.8 vs Excel 17.75 (PASS — cosmetic)
   - Biogas Biomasse yield: drift observed but within sub-section
     ambiguity — needs further curation.

3. **Biomethan split ratios**:
   - `5.4.3` Biomethan für MA: DB 1.2 vs Excel 1.25 (3.9 % drift)
   - Related sub-rows small drift each.

## Not a single bug

Unlike F001 (single LU_2.1 percent) or F003 (single Verbrauch 3.2.2),
F014 is a **pattern**: our Renewable seed values were captured at
one point in time; Excel's scenario parameters were later refined.
The drift pattern is consistent with a seed-refresh lag of ~2-3
months.

## Recommended fix

Re-import Renewable seed values from `_S.xlsx!2. Erneuerbare`:
1. For each RenewableData row with a curated Excel mapping (from
   `01_curated_mappings/renewable_to_excel.csv`):
2. Read the Excel cached status + ziel.
3. If drift > 0.1 %, update DB seed + commit the diff for review.

This is NOT something to do silently — stakeholder sign-off needed
before modifying ~50 renewable seed values.

## Scripts

- `04_renewable_section_aware/per_row_parity.csv` rows with
  `verdict_status=DRIFT` or `verdict_ziel=DRIFT`.
- `01_curated_mappings/renewable_to_excel.csv` section-aware mapping.

## Related findings

- F005 — Biogas Nutzungsgrad (one instance of F014)
- F013 — Ziel renewable per-sector subcode mismatch (different — bilanz engine config)
