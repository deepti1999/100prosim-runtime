# §9 Named Ranges — inventory across all workbooks

## Counts

| workbook | named ranges | status |
|----------|------------:|--------|
| WS.xlsm | 17 | enumerated in §5 + F006 cross-refs |
| AH.xlsm | 16 | archive/cockpit — not used by runtime pipeline |
| C.xlsx | 27 | **all `#REF!`** — historical artifact |
| _S.xlsx | 22 | scenario workbook — 12 map to sheet-level input anchors |
| D.xlsx | 1 | `Alpha` on sheet `1.!F1` — cosmetic |
| MH.xlsx | 0 | single-cell modifications history |
| _100prosim.xlsm | 4 | launcher references to other books |
| trace2.xlsx / tracelog.xlsx | 0 | trace logs, not sources |

## WS.xlsm (energy-engine constants)

Already detailed in §5 `named_constants.csv`. Summary:

| name | Excel value | DB mapping | verdict |
|------|-------------|-----------|---------|
| `EtaStromGas` | 0.65 | `WS_ETA_STROM_GAS` | **EXACT** |
| `EtaRückverstromung` | 0.585 | `WS_ETA_GAS_STROM` | **EXACT** |
| `Abregelung` | 1.0 | `WS_ABREGELUNG_THRESHOLD = 0.65` | **DRIFT** (F006 — dead code) |
| `SelbstentladungsRate` | 0 | (implicit) | OK |
| `TLproEingabeEinheit` | 0.000329 | computed live | EQUIVALENT |
| `VerbrauchStrom` | 1,108,198 | computed live | EQUIVALENT |

## _S.xlsx (scenario anchors)

| name | Excel ref | role | DB reflection |
|------|-----------|------|---------------|
| `s_Mod` | `1. Flächen!R13` | Solar Freiflächen % modifier | `LandUse[LU_2.1].user_percent` — F001 reports drift |
| `s_Ziel` | `1. Flächen!U13` | Solar Freiflächen ziel cell | `LandUse[LU_2.1].target_ha` |
| `w_Mod` | `1. Flächen!R34` | Wind % modifier | `LandUse[LU_6].user_percent` |
| `w_Ziel` | `1. Flächen!U34` | Wind ziel | `LandUse[LU_6].target_ha` |
| `h_mod` | `2. Erneuerbare!P62` | H? mod | *unknown* |
| `h_ziel` | `2. Erneuerbare!R62` | H? ziel | *unknown* |
| `b_Mod` | `2. Erneuerbare!P114` | Biomethan mod | *unknown, likely RenewableData 5.4.3* |
| `b_Ziel` | `2. Erneuerbare!R114` | Biomethan ziel | likewise |
| `g_Mod` | `4. Verbrauch!P83` | Gewerbe mod | probably `VerbrauchData[1.2.x]` |
| `g_Ziel` | `4. Verbrauch!S83` | Gewerbe ziel | likewise |
| `q_Mod` | `4. Verbrauch!P108` | Industrie/Q mod | likely 3.x Prozesswärme |
| `q_Ziel` | `4. Verbrauch!S108` | | |
| `t_modG` | `4. Verbrauch!P157` | MA/Traktion G mod | `VerbrauchData[6.x]` |
| `t_modP` | `4. Verbrauch!P132` | | |
| `t_zielG` | `4. Verbrauch!S157` | | |
| `t_zielP` | `4. Verbrauch!S132` | | |
| `AufnahmeCopy` | `1. Flächen!L28` | UI staging | none — UI concern |
| `KLIK`, `Sum`, `WS_Abgleich` | various | cross-sheet links | computed |

**Gap**: These named ranges are user-input anchor cells. Our DB stores
the corresponding values via `user_percent` fields and DB codes but
doesn't explicitly track the *named range* mapping. If a stakeholder
changes `s_Mod` in Excel and we want to mirror, the mapping is
implicit (via LandUse[LU_2.1].user_percent) — not declared anywhere
in our code.

This is a **minor documentation gap**, not a finding.

## AH.xlsm, C.xlsx (archive workbooks)

Named ranges in C.xlsx are all `#REF!` — this is a historical artifact
workbook. Not in the live pipeline. No parity concern.

AH.xlsm's named ranges relate to the Cockpit2 sheet UI which our app
doesn't mirror. No parity concern.

## D.xlsx

Only one named range: `Alpha = '1.'!F1`. Likely a display parameter.
Not used in our runtime pipeline.

## Recommendations

1. Document the `s_Mod`/`w_Mod`/... → DB-field mapping in a
   comment block in `simulator/workspace_service.py` so future
   devs know the Excel ↔ DB link.
2. No code changes required — the *values* propagate correctly
   even without explicit named-range declaration.
