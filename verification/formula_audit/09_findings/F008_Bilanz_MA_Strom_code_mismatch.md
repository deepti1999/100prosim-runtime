# F008 — Bilanz `verbrauch_strom.mobile` drift: 28,136 vs Excel 15,300

**Severity**: HIGH
**Affects calc**: YES — MA Strom visible on /bilanz/ is 84 % too high.
**Domain**: §4 Bilanz parity
**Confidence**: MEDIUM — drift isolated, cause deferred pending subcode enumeration.

## Observed

| field | Bilanz engine | Excel `_S.xlsx!5. Bilanz!Q9` |
|-------|---------------|------------------------------|
| MA Strom (status) | **28,136.00** GWh/a | **15,300.01** GWh/a |
| drift | | 45.6 % (engine is ~84 % higher than Excel) |

## Chain

`calculation_engine/bilanz_engine.py` maps `strom_codes.mobile = '6.2'`.

DB row: `VerbrauchData[code='6.2', owner=None]`
- category = "davon Strom"
- unit = GWh/a
- status = 28,135.997474
- ziel = 197,521.76

Excel Q9 = `='7. Verbrauch Status'!Q11` = `Q41 * L5 / AB4`.
- Q41 = 180.70 kWh/person/year (Strom MA per-capita)
- L5 = 84,669,326 (population)
- AB4 = 1,000,000 (kWh/GWh)
- Result = 180.70 × 84.669 = **15,301.99** GWh/a

So Excel sees Mobile-Strom as ~15,300 but our DB has 28,136 for
code `6.2`.

## Why they disagree

One hypothesis: DB `6.2 = 28,136` includes **both** the ~15,300 of
Excel Q9 ("Strom for MA incl. Bahn, etc.") **and** an additional
~12,836 that Excel accounts for elsewhere — perhaps electric-traction
rail, which could be tracked as a separate sub-sector in Excel but
aggregated under 6.2 in the DB.

Another hypothesis: 6.2 in the DB represents a *future scenario*
target state (high MA electrification) and the status value is
actually calculated from the ziel back-cast — in which case the
28,136 is wrong as a "status" label.

I was not able to close this within the time budget. Both hypotheses
are testable; the fix is identifying the right subcode under 6.x or
correcting the status seed for 6.2.

## Similar issue for GW → F007

F007 documents the parallel problem on GW Strom:
- `strom_codes.gebaeudewaerme = '2.9.2'` but 2.9.2 is the
  heat-pumps-only subcode, not total GW Strom.
- Even if you fixed the mapping, `get_verbrauch_value()` has a
  fallback-to-zero bug that would mask the stored value.

F007 and F008 are the same class of bug — Bilanz mapping errors
to the wrong Verbrauch subcode — plus a fallback bug.

## Recommended fix

1. Enumerate all VerbrauchData rows under code `6.x` and identify
   which one corresponds to Excel Q9 (total MA Strom).
2. If none exists as a distinct row, create one or change the
   mapping to a parent/aggregate.
3. Same exercise for GW and PW (see F007 and note PW drift 6.85 %).

## Evidence

- Bilanz engine strom_codes at `calculation_engine/bilanz_engine.py:516-521`.
- `VerbrauchData.all_objects.filter(owner=None, code__startswith='6')`
  query (inline in session).
- `_S.xlsx!5. Bilanz!Q9 = 15,300.01`.
- `_S.xlsx!7. Verbrauch Status!Q11 = 15,300.01` (per-capita formula).
