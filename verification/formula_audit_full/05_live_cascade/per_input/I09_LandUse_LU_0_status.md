# Input I09 — LandUse LU_0 status

**Description**: Germany total area

**Excel cell**: `_S.xlsx!1. Flächen!I8`

**DB model/code/field**: `LandUse.LU_0.status_ha`

## Excel dependency closure

6 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!1. Flächen!I31`
- `_S.xlsx!1. Flächen!J31`
- `_S.xlsx!1. Flächen!O31`
- `_S.xlsx!O_!E102`
- `_S.xlsx!O_!E125`
- `_S.xlsx!O_!G125`

## DB Formula consumers

0 Formula rows reference this code directly in their expression.


## Comparison

Excel cascade reaches 6 cells. DB Formula graph reaches 0 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Solar/Wind renewable rows + Bilanz KLIK renewable
- Excel cells touched: count 6
- DB Formula rows touched: count 0
- **DIVERGENT** — one side cascades, the other does not. Possible finding.
