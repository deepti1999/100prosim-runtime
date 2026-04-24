# Input I10 — Renewable 10.1 status

**Description**: Total renewable energy

**Excel cell**: `_S.xlsx!2. Erneuerbare!L230`

**DB model/code/field**: `RenewableData.10.1.status_value`

## Excel dependency closure

1 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!2. Erneuerbare!T230`

## DB Formula consumers

0 Formula rows reference this code directly in their expression.


## Comparison

Excel cascade reaches 1 cells. DB Formula graph reaches 0 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Bilanz sector renewable + Jahresstrom source circles (for PV/wind)
- Excel cells touched: count 1
- DB Formula rows touched: count 0
- **DIVERGENT** — one side cascades, the other does not. Possible finding.
