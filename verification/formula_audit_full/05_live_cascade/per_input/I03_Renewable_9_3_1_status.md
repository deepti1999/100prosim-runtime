# Input I03 — Renewable 9.3.1 status

**Description**: Biogas Main status

**Excel cell**: `_S.xlsx!2. Erneuerbare!L108`

**DB model/code/field**: `RenewableData.9.3.1.status_value`

## Excel dependency closure

14 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!2. Erneuerbare!BC108`
- `_S.xlsx!2. Erneuerbare!BC118`
- `_S.xlsx!2. Erneuerbare!L110`
- `_S.xlsx!2. Erneuerbare!L112`
- `_S.xlsx!2. Erneuerbare!L118`
- `_S.xlsx!2. Erneuerbare!L120`
- `_S.xlsx!2. Erneuerbare!L185`
- `_S.xlsx!2. Erneuerbare!L197`
- `_S.xlsx!5. Bilanz!L23`
- `_S.xlsx!5. Bilanz!L61`
- `_S.xlsx!5. Bilanz!L62`
- `_S.xlsx!5. Bilanz!U23`
- `_S.xlsx!5. Bilanz!U62`
- `_S.xlsx!WS_!L10`

## DB Formula consumers

10 Formula rows reference this code directly in their expression.

- `3.`
- `3._ziel_target`
- `9.3`
- `9.3.1.2`
- `9.3.1.2_target`
- `9.3.2.1`
- `9.3.2.1_ziel_target`
- `9.3_ziel_target`
- `9.4.1`
- `9.4.1_target`

## Comparison

Excel cascade reaches 14 cells. DB Formula graph reaches 10 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Bilanz sector renewable + Jahresstrom source circles (for PV/wind)
- Excel cells touched: count 14
- DB Formula rows touched: count 10
- Both sources cascade — CONGRUENT at concept level.
