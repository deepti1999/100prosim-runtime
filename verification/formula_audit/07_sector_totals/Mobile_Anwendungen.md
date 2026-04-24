# Sector — Mobile Anwendungen (MA)

**Verdict**: Total EXACT; Strom/Fuels sub-split drifts significantly
(F008).

| field | Engine | Excel `Q25` | drift |
|-------|--------:|------------:|------:|
| status total | 753,713.00 | 753,712.78 | 0.00003 % — **EXACT** ✓ |

Engine via `verbrauch_gesamt.mobile = V_6.0.status`.

**Sub-decomposition — the problem**:

| sub | Engine | Excel Q-col | drift |
|-----|--------:|------------:|------:|
| Strom (`V_6.2`) | 28,136 | 15,300 (Q9) | **84 %** — F008 |
| Fuels (`V_6.1`) | 725,577 | ~ (sum of Q12+Q15+Q18) — ~ 738,412 | 1.74 % |
| Heat | 0 | 0 | EXACT |

Interesting: `V_6.0 + V_6.2 ≠ V_6.0 + V_6.1` when the sub-categories
have internal inconsistency.

Quick math check:
- `V_6.1 + V_6.2 = 725,577 + 28,136 = 753,713` ✓ (matches V_6.0)
- Excel `Q9 + Q12 + Q15 + Q18 = 15,300 + 9,196 + 729,217 + 0 = 753,713` ✓

Both sum to the right total — but the Strom/Fuels split differs.
Our engine assigns 28k to Strom + 725k to Fuels; Excel assigns 15k
to Strom + 738k to Fuels.

So **F008 root cause hypothesis**: DB `V_6.1` (Kraftstoffe) holds a
value that's ~13k GWh/a lower than Excel, which compensates in
V_6.2 (Strom) being ~13k higher. Net: total matches.

The fix is to re-evaluate what V_6.1 and V_6.2 should represent,
and whether they should match Excel's Q12/Q15/Q18 (gas/liquid/
solid fuels) vs Excel's Q9 (electricity).

**Renewable**:
- Engine `renewable_by_sector.mobile = 14,779` (via 10.6.2)
- Excel `R10 = 14,623` — 1.06 % drift (just-out-of-spec PASS_COSMETIC)

So MA renewable is approximately right; the total is exact; but the
Strom vs Fuels split is off by ~13k GWh/a internally.
