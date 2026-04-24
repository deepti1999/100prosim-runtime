# Input I02 — LU_6 target_ha

**Description**: Windparkfläche area

**Excel cell**: `_S.xlsx!1. Flächen!L34`

**DB model/code/field**: `LandUse.LU_6.target_ha`

## Excel dependency closure

5 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!1. Flächen!BT34`
- `_S.xlsx!1. Flächen!M34`
- `_S.xlsx!1. Flächen!O34`
- `_S.xlsx!O_!F129`
- `_S.xlsx!O_!H129`

## DB Formula consumers

2 Formula rows reference this code directly in their expression.

- `2.1.1`
- `2.1.1_ziel_target`

## Comparison

Excel cascade reaches 5 cells. DB Formula graph reaches 2 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Solar/Wind renewable rows + Bilanz KLIK renewable
- Excel cells touched: count 5
- DB Formula rows touched: count 2
- Both sources cascade — CONGRUENT at concept level.
