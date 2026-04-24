# Input I05 — Verbrauch 3.7 status

**Description**: PW Endenergie total

**Excel cell**: `_S.xlsx!4. Verbrauch!L120`

**DB model/code/field**: `VerbrauchData.3.7.status`

## Excel dependency closure

4 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!4. Verbrauch!L18`
- `_S.xlsx!4. Verbrauch!L19`
- `_S.xlsx!4. Verbrauch!L191`
- `_S.xlsx!4. Verbrauch!P19`

## DB Formula consumers

2 Formula rows reference this code directly in their expression.

- `V_8`
- `V_8_ziel`

## Comparison

Excel cascade reaches 4 cells. DB Formula graph reaches 2 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Sector total + Bilanz sector
- Excel cells touched: count 4
- DB Formula rows touched: count 2
- Both sources cascade — CONGRUENT at concept level.
