# Input I07 — Verbrauch 1.1.2 ziel

**Description**: KLIK HH efficiency

**Excel cell**: `_S.xlsx!4. Verbrauch!M25`

**DB model/code/field**: `VerbrauchData.1.1.2.ziel`

## Excel dependency closure

16 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!2. Erneuerbare!M233`
- `_S.xlsx!2. Erneuerbare!M234`
- `_S.xlsx!2. Erneuerbare!M237`
- `_S.xlsx!2. Erneuerbare!M246`
- `_S.xlsx!2. Erneuerbare!M256`
- `_S.xlsx!2. Erneuerbare!M264`
- `_S.xlsx!4. Verbrauch!M18`
- `_S.xlsx!4. Verbrauch!M189`
- `_S.xlsx!4. Verbrauch!M19`
- `_S.xlsx!4. Verbrauch!M191`
- `_S.xlsx!4. Verbrauch!M26`
- `_S.xlsx!4. Verbrauch!M42`
- `_S.xlsx!4. Verbrauch!P19`
- `_S.xlsx!5. Bilanz!H51`
- `_S.xlsx!5. Bilanz!J53`
- `_S.xlsx!WS_!M4`

## DB Formula consumers

54 Formula rows reference this code directly in their expression.

- `1.1.1`
- `1.1.1_ziel_target`
- `1.1.2`
- `1.1.2.1.1_target`
- `1.1.2.1.2`
- `1.1.2.1.2.2`
- `1.1.2.1.2.2_target`
- `1.1.2.1.2_target`
- `1.1.2_ziel_target`
- `1.2.1`
- `1.2.1_ziel_target`
- `10.4.2`
- `10.4.2_target`
- `10.9.1.2`
- `10.9.1.2_ziel_target`
- `2.1`
- `2.1.1.2.2`
- `2.1.1.2.2_ziel_target`
- `2.1.1.2.3`
- `2.1.1.2.3_ziel_target`
- `2.1_ziel_target`
- `3.`
- `3._ziel_target`
- `4.`
- `4.1.3`
- `4.1.3_ziel_target`
- `4.2.1.1.2.2`
- `4.2.1.1.2.2_ziel_target`
- `4.3`
- `4.3.2`

(+ 24 more)

## Comparison

Excel cascade reaches 16 cells. DB Formula graph reaches 54 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Sector total + Bilanz sector
- Excel cells touched: count 16
- DB Formula rows touched: count 54
- Both sources cascade — CONGRUENT at concept level.
