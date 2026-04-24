# F013 — Ziel-Bilanz renewable per-sector values diverge significantly from Excel

**Severity**: HIGH
**Affects calc**: YES — Ziel-Bilanz row 26/52/55 renewable display shows wrong per-sector values.
**Domain**: §03 Full Bilanz parity (Ziel section, renewable carrier, all 4 sectors)
**Confidence**: HIGH — cell-level diff across all 4 sectors.

## Observed

| sector | engine (ziel renewable) | Excel | drift |
|--------|------------------------:|------:|------:|
| KLIK | 312,753.30 | 374,437.50 (I65) | 16 % |
| GW | 137,950.43 | 699,077.14 (L65) | **80 %** |
| PW | 357,517.36 | 560,767.10 (O65) | 36 % |
| MA | 197,521.76 | 427,711.43 (R65) | 54 % |

Excel `5. Bilanz!U65` (total ziel renewable) = 2,061,993.
Engine `erneuerbar.ziel.gesamt = 1,005,742.85`.
Total drift: 51 % (engine is half of Excel).

## Root cause (hypothesis)

Engine `renewable_by_sector` uses codes
`10.3.1` (KLIK Strom), `10.4.3` (GW Strom), `10.5.3` (PW Strom),
`10.6.2` (MA Strom) — which are all **Strom-only** values (Anteil Strom
at erneuerb.).

Excel `U65` aggregates
`L65 = M239 (GW renewable total = gas + liquid + solid + heat + Strom)`
— **all carriers**, not just Strom.

So our engine's "renewable by sector" is actually "renewable Strom by
sector", not "renewable TOTAL by sector". The subcode mismatch is:
- Our: `10.x.3` (Strom-only sub-subcode)
- Should be: `10.x` (sector aggregate across all carriers)

Check by summing:
- Engine KLIK ziel renewable = 312,753 (Strom only)
- Engine GW ziel renewable = 137,950 (Strom only)
- Engine total = 1,005,743

If we used `10.3` (KLIK total renewable), `10.4` (GW total), etc.:
- Our formula `10.4_ziel = 10.4.1 + 10.4.3 + 10.4.2` → 374,438 (matches Excel I65).
- This matches what Excel calls KLIK renewable total.

So the fix is: change `renewable_by_sector` to use
`10.3` / `10.4` / `10.5` / `10.6` (parent codes) instead of
`10.3.1` / `10.4.3` / `10.5.3` / `10.6.2` (Strom-only subcodes).

## Recommended fix

In `calculation_engine/bilanz_engine.py:407-419`:
```python
renewable_by_sector = {
    'status': {
        'kraft_licht': safe_get_renewable('10.3.1', use_target=False),  # ← change to '10.3'
        'gebaeudewaerme': safe_get_renewable('10.4.3', use_target=False),  # ← '10.4'
        'prozesswaerme': safe_get_renewable('10.5.3', use_target=False),  # ← '10.5'
        'mobile': safe_get_renewable('10.6.2', use_target=False),  # ← '10.6'
    },
    ...
}
```

This would bring:
- KLIK renewable: 172,995 → ~171,004 (match L10)
- GW renewable: 17,211 → ~172,290 (match L239) — 10× increase
- Similar for PW / MA

## Cross-references

- F007 (GW Strom = 0) — related but different: F007 is the engine
  returning 0 for Strom due to is_calculated+no-formula fallback.
  F013 is the engine returning Strom-only (17,211) when it should
  return total-renewable (172,290).
- `renewable_gesamt_by_sector` (another key in the engine output)
  *does* use code `10.4` and produces 105,665 which is closer to
  Excel — see `bilanz_engine.py:455+` for that computation.

## Evidence

- `03_full_bilanz_parity/all_sections.csv` — rows with
  `section=Gesamt, carrier_role=renewable, view=ziel`.
- Engine `calculate_bilanz_data()` compared to `_S.xlsx!5. Bilanz`
  rows 65 (ziel total) and 52 (ziel Strom renewable).
