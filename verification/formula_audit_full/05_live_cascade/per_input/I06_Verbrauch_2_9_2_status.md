# Input I06 — Verbrauch 2.9.2 status

**Description**: GW Strom Wärmepumpen

**Excel cell**: `_S.xlsx!4. Verbrauch!L46`

**DB model/code/field**: `VerbrauchData.2.9.2.status`

## Excel dependency closure

13 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!4. Verbrauch!CE191`
- `_S.xlsx!4. Verbrauch!CE200`
- `_S.xlsx!4. Verbrauch!CE57`
- `_S.xlsx!4. Verbrauch!CF200`
- `_S.xlsx!4. Verbrauch!L47`
- `_S.xlsx!4. Verbrauch!L50`
- `_S.xlsx!4. Verbrauch!L57`
- `_S.xlsx!4. Verbrauch!L59`
- `_S.xlsx!4. Verbrauch!L68`
- `_S.xlsx!4. Verbrauch!L71`
- `_S.xlsx!4. Verbrauch!L73`
- `_S.xlsx!4. Verbrauch!L74`
- `_S.xlsx!4. Verbrauch!L75`

## DB Formula consumers

5 Formula rows reference this code directly in their expression.

- `7.1`
- `V_2.9.1`
- `V_2.9.1_ziel`
- `V_9_1_ziel`
- `WS_davon_raumw_korr_row_366`

## Comparison

Excel cascade reaches 13 cells. DB Formula graph reaches 5 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Sector total + Bilanz sector
- Excel cells touched: count 13
- DB Formula rows touched: count 5
- Both sources cascade — CONGRUENT at concept level.
