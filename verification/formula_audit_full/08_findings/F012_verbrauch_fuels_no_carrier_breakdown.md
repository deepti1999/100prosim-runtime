# F012 — `verbrauch_fuels` aggregates gas+liquid+solid; Excel separates them

**Severity**: MEDIUM (structural; not a calc error but loses display granularity)
**Affects calc**: NO at the aggregate level (totals match within 0.5%);
YES at the per-fuel-type display level (no engine counterpart for separate gas/liquid/solid).
**Domain**: §03 Full Bilanz parity
**Confidence**: HIGH — engine source inspection.

## Observed

Our engine has:
- `verbrauch_fuels` — aggregated total of all fuels (gas + liquid + solid)

Excel `_S.xlsx!5. Bilanz` has three separate rows:
- Row 12 `Brennstoff gasförmig` → per-sector gas consumption
- Row 15 `Brennstoff flüssig` → per-sector liquid consumption
- Row 18 `Brennstoff fest` → per-sector solid consumption

Cell-level comparison:
| Excel cell | Engine value | Excel value | Verdict |
|------------|--------------|-------------|---------|
| K12 (GW gas) | `verbrauch_fuels.GW = 632,956` | 346,430 | DRIFT (engine shows sum of all 3) |
| K15 (GW liquid) | no engine equiv | 136,478 | NO_ENGINE_EQUIV |
| K18 (GW solid) | no engine equiv | 149,501 | NO_ENGINE_EQUIV |
| sum K12+K15+K18 | (sum from engine) | 632,410 | approx match |

Engine GW fuels = 632,956 vs Excel K12+K15+K18 sum = 632,410 — 0.09 %
drift (PASS_COSMETIC). So the **aggregate math is right**; the
**per-carrier breakdown is missing**.

## Why this might matter

- The `/bilanz/` page in our app shows aggregate "Brennstoffe gesamt"
  per sector. Users cannot see the gas/liquid/solid split.
- Stakeholder PDF §2.3 may require per-carrier reporting; if so,
  this is a MEDIUM-severity feature-gap.
- From a correctness standpoint, the total is right within 0.1 %.

## Recommended fix

Option A: Extend engine to produce `verbrauch_gas`, `verbrauch_liquid`,
`verbrauch_solid` by looking up VerbrauchData subcodes for each
fuel type per sector. The Excel L/M/S formulas show the source codes.

Option B: Accept aggregate view as stakeholder-approved. Document
that per-carrier breakdown is out of scope for our app.

## Evidence

- `03_full_bilanz_parity/all_sections.csv` rows marked `NO_ENGINE_EQUIV`
  under `section=Brennstoff flüssig` and `section=Brennstoff fest`.
- Engine output `verbrauch_fuels.status.gesamt = 1,693,436` ≈
  Excel `T12+T15+T18 = 548,139+890,492+267,125 = 1,705,756` — 0.7 % drift.
