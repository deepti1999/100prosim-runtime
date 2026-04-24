# Input I08 — WS_ETA_STROM_GAS

**Description**: Power-to-gas efficiency

**Excel cell**: `WS.xlsm!1.Jahresbilanz_Strom!N33`

**DB model/code/field**: `Formula.WS_ETA_STROM_GAS.expression`

## Excel dependency closure

10 cells transitively depend on this input (max depth 6).

Sample (first 30):

- `WS.xlsm!1.Jahresbilanz_Strom!AD13`
- `WS.xlsm!1.Jahresbilanz_Strom!AE12`
- `WS.xlsm!1.Jahresbilanz_Strom!AE24`
- `WS.xlsm!1.Jahresbilanz_Strom!L28`
- `WS.xlsm!1.Jahresbilanz_Strom!L29`
- `WS.xlsm!1.Jahresbilanz_Strom!L36`
- `WS.xlsm!1.Jahresbilanz_Strom!L37`
- `WS.xlsm!1.Jahresbilanz_Strom!M12`
- `WS.xlsm!1.Jahresbilanz_Strom!Q44`
- `WS.xlsm!1.Jahresbilanz_Strom!R44`

## DB Formula consumers

0 Formula rows reference this code directly in their expression.


## Comparison

Excel cascade reaches 10 cells. DB Formula graph reaches 0 direct consumers.

Excel counts individual cells (including INDIRECT intermediate rows); DB Formula consumers are aggregated per code. So direct set equality is not expected — we assess concept-level congruence below.

**Concept-level congruence check**:

- Expected cascade target (domain-level): All WS365 daily rows + Jahresstrom diagram flow cells
- Excel cells touched: count 10
- DB Formula rows touched: count 0
- **DIVERGENT** — one side cascades, the other does not. Possible finding.
