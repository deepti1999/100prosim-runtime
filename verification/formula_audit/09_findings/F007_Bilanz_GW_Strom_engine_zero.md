# F007 — Bilanz engine returns 0 for `verbrauch_strom` Gebäudewärme status

**Severity**: CRITICAL — affects visible Bilanz status row for GW sector.
**Affects calc**: YES — the Bilanz page on `/bilanz/` shows `GW strom = 0` for status even though the underlying DB value is 10,108 GWh/a.
**Domain**: §4 Bilanz parity
**Confidence**: HIGH — traced through code + DB query.

## Observed

Calling `calculate_bilanz_data()` returns:

```
verbrauch_strom.status = {
  kraft_licht: 329345.69,
  gebaeudewaerme: 0.00,    ← but Excel K9 = 32,877 GWh/a
  prozesswaerme: 71620.89,
  mobile: 28136.00,
  gesamt: 429102.57        ← Excel T9 = 454,279.87
}
```

Excel `_S.xlsx!5. Bilanz!K9` (GW Strom) = **32,877** GWh/a
(formula `='7. Verbrauch Status'!K11`, which is `=K41*$L$5/$AB$4`
= per-capita * population / 1000, K41 = 388.30 kWh/person).

## Root cause

In `calculation_engine/bilanz_engine.py:516-521` the `strom_codes`
mapping has:

```python
strom_codes = {
    'kraft_licht': '1.4',
    'gebaeudewaerme': '2.9.2',   ← see below — wrong subcode
    'prozesswaerme': '3.6.0',
    'mobile': '6.2'
}
```

For `VerbrauchData[code='2.9.2']`:

- `is_calculated = True`
- `status_calculated = False`
- `ziel_calculated = True`
- `status = 10108.0` (pre-computed, stored)
- `ziel = 137950.43` (computed, matches `calculate_ziel_value()`)

In `get_verbrauch_value(code='2.9.2', use_ziel=False)`:
1. `is_calculated = True` → branch calls `verbrauch.calculate_value()`
2. `calculate_value()` returns `None` (no status formula exists —
   Formula table has `V_2.9.2` only with `formula_type='ziel'`)
3. Line 270: `return value if value is not None else 0` → **returns 0**

So the stored `status = 10108.0` on the row is **silently shadowed**
by the 0-fallback.

## Secondary issue: wrong subcode

Even if `get_verbrauch_value` returned 10108 (the stored status) for
2.9.2, that would still not match Excel K9 = 32,877.

- DB `VerbrauchData[2.9.2].status = 10,108` is labeled "=" (category
  empty; this is the **heat-pumps-only** share of GW Strom, per the
  2.9 hierarchy: 2.9 = davon Strom, 2.9.0 = Endenergie total,
  2.9.1 = davon Wärmepumpen %, 2.9.2 = Wärmepumpen-portion value).
- DB `VerbrauchData[2.9.0].status = 32,766.65` ("= Endenergieverbrauch")
  — matches Excel K9 = 32,877 within 0.3 % (PASS_COSMETIC).

Therefore `strom_codes.gebaeudewaerme` **should map to `'2.9.0'`**,
not `'2.9.2'`, to represent *total GW electricity* consistent with
Excel's Bilanz structure.

Combined with the engine bug, the current display is:
```
DB stored:     2.9.2 = 10,108 (heat-pumps-only)
Engine returns: 0    (is_calc=True but no status formula → fallback)
Excel expects: 32,877 (total GW electricity, matches DB 2.9.0)
```

## Cross-check: MA sector suspect

Similar drift on mobile: our engine says `MA strom = 28,136`, Excel
Q9 = 15,300. `strom_codes.mobile = '6.2'` → DB 6.2 = 28,136 ("davon
Strom" under code 6 Mobile Anwendungen). The drift (28k vs 15k) may
be the same class of finding — wrong subcode — but I did not
fully confirm the correct subcode. Left for follow-up.

## Why Excel's value is different AND the engine is broken

Two independent issues stack:

1. **Engine bug**: `get_verbrauch_value` returns 0 for
   `(is_calculated=True, no status formula, stored status!=None)`.
   That's a logic bug — it should fall through to the stored value.

2. **Mapping bug**: even if fixed, `2.9.2` is the wrong subcode for
   "total GW electricity"; should be `2.9.0`.

## Recommended fix

1. In `bilanz_engine.py` `get_verbrauch_value`: if
   `calculate_value()` returns None, fall back to `verbrauch.status`
   (the stored value) before returning 0.
2. In `bilanz_engine.py` `strom_codes`: change `'gebaeudewaerme':
   '2.9.2'` → `'2.9.0'`.
3. Audit the mobile mapping (`'6.2'` vs Excel Q9 15,300).

## Evidence

- `calculation_engine/bilanz_engine.py:229-280` — `get_verbrauch_value`.
- `calculation_engine/bilanz_engine.py:516-521` — `strom_codes` map.
- DB shell (inline): 2.9.2 is_calc=True, calculate_value()=None,
  get_verbrauch_value('2.9.2', use_ziel=False)=0, status=10108.
- `_S.xlsx!5. Bilanz!K9 = 32877`; `K11 = K41 * L5 / AB4 =
  388.30 kWh × 84.67M / 1M = 32876.98 GWh`.
