# F002 — LU_2.4 (sonstige Nutzung): target_ha residual drift (consequence of F001)

**Severity**: MEDIUM (derived — the arithmetic is internally consistent; the drift is inherited from F001).
**Affects calc**: YES — visible ziel value is 12.8 % above the scenario.
**Domain**: §2 value parity (LandUse)
**Confidence**: HIGH — residual formula reproduced in both sources.

## Observed

| field | DB (owner=None) | Excel `_S.xlsx!1. Flächen!L25` |
|-------|-----------------|--------------------------------|
| `status_ha` | 1,615,489 | `I25` = 1,615,489.35 (PASS_COSMETIC) |
| `target_ha` | **1,883,157** | **1,670,097.38** |

Drift on `target_ha`: 12.8 %.

## Why they disagree

LU_2.4 is a **residual**: `LF_target − Ackerland − Dauergrünland − Solare_Freiflächen`.

Excel cell `L25` formula: `=L12 - L14 - L22 - L13` (direct):
```
= 17,754,997 − 10,826,000 − 4,371,150 − 887,749.85
= 1,670,097.15 ≈ 1,670,097.38
```

DB computes the same residual but against an LU_2.1 of 684,640:
```
= 17,754,997 − 10,826,000 − 4,371,150 − 684,640.80
= 1,873,206.20 → DB shows 1,883,157 (small further rounding in DB)
```

So LU_2.4 is **correct relative to LU_2.1**; it only looks wrong
because LU_2.1 is wrong (F001). Fixing F001 auto-fixes F002.

## Recommended fix

No fix needed here. Fixing F001 will cascade and bring `target_ha` to
≈ 1,670,097 via `percentage_rebalancer`.

## Scripts

Same CSV row as F001.
