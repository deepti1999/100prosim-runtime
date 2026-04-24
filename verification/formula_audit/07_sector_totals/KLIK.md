# Sector — KLIK (Kraft, Licht, Information, Kommunikation, Kälte)

**Verdict**: PASS_COSMETIC at 0.04 %.

| field | Engine | Excel `_S.xlsx!5. Bilanz!H25` | drift |
|-------|--------:|-------------------------------:|------:|
| status total | 329,345.69 | 329,214.07 | 0.040 % |

Engine computes via `verbrauch_gesamt.kraft_licht = V_1.4.status`.
Excel `H25 = '7. Verbrauch Status!H11'`.
Both reach `329k` GWh/a (electricity is the only KLIK contribution).

**Sub-decomposition**:
- Strom: 329,346 (engine) vs 329,214 (Excel) — 0.04 % ✓
- Fuels: 0 (engine) vs 0 (Excel) — EXACT ✓
- Heat: 0 (engine) vs 0 (Excel) — EXACT ✓

Renewable share:
- Engine `renewable_by_sector.kraft_licht = 172,995` (via `10.3.1`)
- Excel `I10 = 171,004` — 1.16 % drift (KLIK renewable over-counts by 1.16 %)

Fossil residual = total − renewable:
- Engine 329,346 − 172,995 = 156,350
- Excel 329,214 − 171,004 = 158,210
- Drift 1.18 %

So KLIK **total is solid**, but the **renewable/fossil split drifts
~1.2 %**. This is a second-order finding — not yet a §2 code
drift, but worth investigating if the 10.3.1 subcode contains all
KLIK-renewable contributions consistent with Excel's L237 reference
and its dependency chain.

No new finding (within F001/F007 ecosystem of subcode-mapping
issues).
