# F011 — `verbrauch_heat_renewable` returns 0 for all sectors vs Excel 32,783 GWh/a

**Severity**: HIGH
**Affects calc**: YES — Bilanz Wärme renewable row shown as 0 when Excel scenario has 32,783 GWh/a (Biogas Wärmenutzung).
**Domain**: §03 Full Bilanz parity (Wärme section status)
**Confidence**: HIGH — direct trace.

## Observed

| cell | engine | Excel |
|------|-------:|------:|
| `5. Bilanz!L22` (GW Wärme renewable status) | 0 | 32,782.79 |
| `5. Bilanz!U22` (total Wärme renewable status) | 0 | 32,782.79 |

## Root cause

`calculation_engine/bilanz_engine.py:660-661`:
```python
'verbrauch_heat_renewable': {
    'status': v_heat_status_ren,
    'ziel': v_heat_ziel_ren,
},
```

Where `v_heat_status_ren` is built from some renewable_heat mapping
but evaluates to `{kraft_licht: 0, gebaeudewaerme: 0, ...}` at the
current seed state. Excel computes the value as `L22 = L10 + L91 +
L137 + L153 + L159` (summary of Gebäudewärme-renewable from multiple
renewable sources: solar thermal, biogas heat, wood heat, etc.) =
32,782.79 GWh/a.

Our engine either:
- Doesn't sum these contributing codes, OR
- Reads an empty/None value for each contribution, OR
- Is scoped to only `heat_renewable_codes` map which doesn't include
  all the Excel-summed codes.

## Recommended fix

Expand our heat_renewable_codes mapping to include all the
contributing Renewable codes (probably 10.4.2 for GW heat renewable
aggregate). Cross-reference the Excel `L22` SUM references
(`L10 + L91 + L137 + L153 + L159`) to DB codes.

## Evidence

- `03_full_bilanz_parity/all_sections.csv` rows for
  `section=Wärme, carrier_role=renewable, view=status`.
- Excel `_S.xlsx!5. Bilanz!L22 = 32782.79`.
- Engine `calculate_bilanz_data()['verbrauch_heat_renewable']['status']['gebaeudewaerme'] = 0`.
