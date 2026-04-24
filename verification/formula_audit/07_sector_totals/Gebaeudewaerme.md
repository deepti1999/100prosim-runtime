# Sector — Gebäudewärme (GW)

**Verdict**: Total PASS_COSMETIC at 0.04 %; but sub-components have
severe drift (F007).

| field | Engine | Excel `K25` | drift |
|-------|--------:|------------:|------:|
| status total | 799,186.55 | 798,867.25 | 0.040 % |

Engine via `verbrauch_gesamt.gebaeudewaerme = V_2.10.status`.

**Sub-decomposition — the problem area**:

| field | Engine | Excel | drift |
|-------|--------:|------:|------:|
| Strom | **0** | **32,877** (K9) | **100 %** — F007 |
| Fuels (`V_2.7.0`) | 632,956 | — | see F007 discussion |
| Heat (`V_2.8.0`) | 133,464 | 133,580 (K21) | 0.087 % ✓ |

The GW total is correct because the engine's *verbrauch_gesamt*
uses `V_2.10` (which is computed upstream of any Strom-subcode
error). But *verbrauch_strom.gebaeudewaerme* is 0 while Excel's
K9 = 32,877 (because the mapping uses `V_2.9.2` = heat-pumps-only
+ `get_verbrauch_value` returns 0 for is_calculated=True with no
status formula).

The net effect: sector total right, per-energy-carrier split wrong.
Anything that displays "GW Strom" on the /bilanz/ page will show 0
when it should show ~32,877 GWh/a.

**F007 is the critical finding for this sector.**

Renewable share:
- Engine `renewable_by_sector.gebaeudewaerme = 17,211` (via `V_10.4.3 "davon Strom"`)
- Excel `L10 = 17,077` — 0.78 % drift (PASS_COSMETIC)

So the renewable-GW-Strom path is fine; it's the total-GW-Strom
pipeline that's broken.
