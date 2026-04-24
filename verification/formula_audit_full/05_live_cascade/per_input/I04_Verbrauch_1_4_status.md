# Input I04 — Verbrauch 1.4 status

**Description**: KLIK Strom total

**Excel cell**: `_S.xlsx!4. Verbrauch!L42`

**DB model/code/field**: `VerbrauchData.1.4.status`

## Excel dependency closure

34 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `_S.xlsx!2. Erneuerbare!L230`
- `_S.xlsx!2. Erneuerbare!L233`
- `_S.xlsx!2. Erneuerbare!L234`
- `_S.xlsx!2. Erneuerbare!L236`
- `_S.xlsx!2. Erneuerbare!L237`
- `_S.xlsx!2. Erneuerbare!L239`
- `_S.xlsx!2. Erneuerbare!L246`
- `_S.xlsx!2. Erneuerbare!L248`
- `_S.xlsx!2. Erneuerbare!L256`
- `_S.xlsx!2. Erneuerbare!L258`
- `_S.xlsx!2. Erneuerbare!L264`
- `_S.xlsx!2. Erneuerbare!T229`
- `_S.xlsx!2. Erneuerbare!T236`
- `_S.xlsx!2. Erneuerbare!T237`
- `_S.xlsx!2. Erneuerbare!T239`
- `_S.xlsx!2. Erneuerbare!T246`
- `_S.xlsx!2. Erneuerbare!T248`
- `_S.xlsx!2. Erneuerbare!T256`
- `_S.xlsx!2. Erneuerbare!T258`
- `_S.xlsx!2. Erneuerbare!T264`
- `_S.xlsx!4. Verbrauch!L18`
- `_S.xlsx!4. Verbrauch!L189`
- `_S.xlsx!4. Verbrauch!L19`
- `_S.xlsx!4. Verbrauch!L191`
- `_S.xlsx!4. Verbrauch!P19`
- `_S.xlsx!5. Bilanz!I10`
- `_S.xlsx!5. Bilanz!J11`
- `_S.xlsx!5. Bilanz!L10`
- `_S.xlsx!5. Bilanz!M11`
- `_S.xlsx!5. Bilanz!O10`

(+ 4 more)

## DB Formula consumers

50 Formula rows reference this code directly in their expression.

- `10.3.1`
- `10.3.1_ziel_target`
- `10.4.2`
- `10.4.2_target`
- `10.5.1`
- `10.5.1_ziel_target`
- `10.8`
- `10.8_ziel_target`
- `2.1`
- `2.1_ziel_target`
- `3.`
- `3._ziel_target`
- `4.`
- `4._ziel_target`
- `7.1.4.2`
- `7.1.4.2_ziel_target`
- `7.1.4.3`
- `7.1.4.3.2`
- `7.1.4.3.2_ziel_target`
- `7.1.4.3_ziel_target`
- `9.1`
- `9.1_ziel_target`
- `9.2`
- `9.2.1`
- `9.2.1.4`
- `9.2.1.4.2`
- `9.2.1.4.2_ziel_target`
- `9.2.1.4_target`
- `9.2.1.5`
- `9.2.1.5_ziel_target`

(+ 20 more)

## Comparison

Excel cascade reaches 34 cells. DB Formula graph reaches 50 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): Sector total + Bilanz sector
- Excel cells touched: count 34
- DB Formula rows touched: count 50
- Both sources cascade — CONGRUENT at concept level.
