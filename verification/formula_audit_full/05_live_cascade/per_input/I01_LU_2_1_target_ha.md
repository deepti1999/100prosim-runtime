# Input I01 — LU_2.1 target_ha

**Description**: Solar Freiflächen area

**Excel cell**: `_S.xlsx!1. Flächen!L13`

**DB model/code/field**: `LandUse.LU_2.1.target_ha`

## Excel dependency closure

11 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!1. Flächen!BT13`
- `_S.xlsx!1. Flächen!BT25`
- `_S.xlsx!1. Flächen!L25`
- `_S.xlsx!1. Flächen!M13`
- `_S.xlsx!1. Flächen!M25`
- `_S.xlsx!1. Flächen!O13`
- `_S.xlsx!1. Flächen!O25`
- `_S.xlsx!O_!F107`
- `_S.xlsx!O_!F119`
- `_S.xlsx!O_!H107`
- `_S.xlsx!O_!H119`

## DB Formula consumers

4 Formula rows reference this code directly in their expression.

- `1.2`
- `1.2.1.2`
- `1.2.1.2_ziel_target`
- `1.2_target`

## Comparison

Excel cascade reaches 11 cells. DB Formula graph reaches 4 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Solar/Wind renewable rows + Bilanz KLIK renewable
- Excel cells touched: count 11
- DB Formula rows touched: count 4
- Both sources cascade — CONGRUENT at concept level.
