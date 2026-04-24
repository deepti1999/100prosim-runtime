# Sector — Prozesswärme (PW)

**Verdict**: 0.90 % DRIFT on total.

| field | Engine | Excel `N25` | drift |
|-------|--------:|------------:|------:|
| status total | 550,370.90 | 555,394.57 | 0.904 % |

Engine via `verbrauch_gesamt.prozesswaerme = V_3.7.status`.

This is **F004** (Bilanz PW status drift 0.9 %). Caused by at least
one PW sub-child having a slightly off status seed compared to
Excel. Drill-down:

| sub | Engine | Excel | drift |
|-----|--------:|------:|------:|
| Strom (`V_3.6.0`) | 71,620.89 | 76,888.81 (N9) | **6.85 %** — root cause |
| Fuels (`V_3.4.0`) | 334,902.85 | ~ (see K/N/Q13+17+19 sum) | needs drill |
| Heat (`V_3.5.0`) | 143,847.16 | 143,571.54 (N21) | 0.19 % (PASS_COSMETIC) |

The PW **Strom** is ~6.9 % short. That likely propagates the 0.9 %
total drift. It could be:
- 3.6.0 status seed is slightly off in DB, OR
- Excel's N9 includes additional contribution (electric boilers?
  industrial electrification share?) that our 3.6.0 subcode doesn't
  capture.

This is the same class as F007/F008 — subcode mapping uncertainty
for the per-energy-carrier split.

**Renewable split**:
- Engine `renewable_by_sector.prozesswaerme = 37,620` (via 10.5.3)
- Excel `O10 = 39,938` — 5.8 % drift

So PW renewable is also ~6 % short; consistent with PW being the
"worst" sector in the §4 comparison.

F004 captures the total drift; F005 (Biogas Nutzungsgrad rows)
suggests a Nutzungsgrad mapping issue which could be a root cause
of PW renewable undercount.
