# §3 Formula parity — spot-check of 30 representative formulas

Each row is hand-mapped from DB Formula.expression to an Excel cell.
Verdict decided by human eyeball after comparing structure.


## `Formula[LANDUSE_CHANGE_RATIO]` — landuse

**DB expression:** `child_target / child_status`

**Excel ref:** `_S.xlsx{m}!1. Flächen!O9`

- cached value: `1.0786135471981573`
- formula: `'=IFERROR(L9/I9,"")'`

**Excel ziel ref:** `1. Flächen!O9`

- cached value: `1.0786135471981573`
- formula: `'=IFERROR(L9/I9,"")'`

**Notes:** child_target / child_status — Excel has L/I ratio per row (O column)

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[LANDUSE_STATUS_PERCENT]` — landuse

**DB expression:** `child_status / parent_status * 100`

**Excel ref:** `_S.xlsx{m}!1. Flächen!J9`

- cached value: `9.452246980098648`
- formula: `'=I9/INDIRECT(I$1&$AB9)%'`

**Notes:** child_status / parent_status * 100 — Excel J column % v.HS

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[LANDUSE_TARGET_PERCENT]` — landuse

**DB expression:** `child_target / parent_target * 100`

**Excel ref:** `_S.xlsx{m}!1. Flächen!M9`

- cached value: `10.195321644197273`
- formula: `'=L9/INDIRECT(L$1&$AB9)%'`

**Notes:** child_target / parent_target * 100 — Excel M column % v.HS

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[10.1]` — renewable

**DB expression:** `Renewable_10_3 + Renewable_10_4 + Renewable_10_5+Renewable_10_6`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!L230`

- cached value: `459452.05288486544`
- formula: `'=L236+L239+L248+L258'`

**Excel ziel ref:** `2. Erneuerbare!M230`

- cached value: `2061993.1821718658`
- formula: `'=M236+M239+M248+M258'`

**Notes:** Endenergie aus Erneuerbaren Q. gesamt = L236+L239+L248+L258

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[10.1_target]` — renewable

**DB expression:** `<none>`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!None`

- cached value: `None`
- formula: `None`

**Excel ziel ref:** `2. Erneuerbare!M230`

- cached value: `2061993.1821718658`
- formula: `'=M236+M239+M248+M258'`

**Notes:** None

**Verdict (auto-inspect):**
  - DB_EMPTY_EXPR — input/fixed row, not computed

## `Formula[10.3]` — renewable

**DB expression:** `Renewable_10_3_1`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!L236`

- cached value: `171003.68337655472`
- formula: `'=L237'`

**Excel ziel ref:** `2. Erneuerbare!M236`

- cached value: `374437.5035180524`
- formula: `'=M237'`

**Notes:** KLIK — L237 (davon Strom)

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[10.4]` — renewable

**DB expression:** `Renewable_10_4_1 + Renewable_10_4_3 + Renewable_10_4_2`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!L239`

- cached value: `172289.86088316783`
- formula: `'=L240+L245+L246'`

**Excel ziel ref:** `2. Erneuerbare!M239`

- cached value: `699077.1419264316`
- formula: `'=M240+M245+M246'`

**Notes:** GW = L240+L245+L246

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[10.5]` — renewable

**DB expression:** `Renewable_10_5_1 + Renewable_10_5_3 + Renewable_10_5_2`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!L248`

- cached value: `65635.52034126216`
- formula: `'=L249+L255+L256'`

**Excel ziel ref:** `2. Erneuerbare!M248`

- cached value: `560767.1028506921`
- formula: `'=M249+M255+M256'`

**Notes:** PW = L249+L255+L256

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[10.6]` — renewable

**DB expression:** `Renewable_10_6_1 + Renewable_10_6_2`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!L258`

- cached value: `50522.98828388071`
- formula: `'=L259+L264'`

**Excel ziel ref:** `2. Erneuerbare!M258`

- cached value: `427711.43387668976`
- formula: `'=M259+M264'`

**Notes:** MA = L259+L260+L261

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[10.2]` — renewable

**DB expression:** `Renewable_9_4_3_3`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!L234`

- cached value: `51.94300645264813`
- formula: `'=L232/L233%'`

**Excel ziel ref:** `2. Erneuerbare!M234`

- cached value: `119.72293460100832`
- formula: `'=M232/M233%'`

**Notes:** Anteil Erneuerb.an Stromverbrauch = L232/L233 * 100

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[9.3.1]` — renewable

**DB expression:** `0`

**Excel ref:** `_S.xlsx{m}!2. Erneuerbare!None`

- cached value: `None`
- formula: `None`

**Notes:** 9.3.1 is an input/fixed row (expression='0' in DB)

**Verdict (auto-inspect):**

## `Formula[V_1.4]` — verbrauch

**DB expression:** `Verbrauch_1_1_3 + Verbrauch_1_2_5 + Verbrauch_1_3_5`

**Excel ref:** `_S.xlsx{m}!4. Verbrauch!L42`

- cached value: `329214.0656749311`
- formula: `'=L26+L33+L40'`

**Excel ziel ref:** `4. Verbrauch!M42`

- cached value: `312753.36239118455`
- formula: `'=M26+M33+M40'`

**Notes:** KLIK total = sum of KLIK children

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[V_1.1.1]` — verbrauch

**DB expression:** `Verbrauch_1_0 * Verbrauch_1_1 / 100`

**Excel ref:** `_S.xlsx{m}!4. Verbrauch!None`

- cached value: `None`
- formula: `None`

**Notes:** Verbrauch_1_0 * Verbrauch_1_1 / 100 — Excel should show same product

**Verdict (auto-inspect):**

## `WS365Formula[einspeich]` — ws365

**DB expression:** `IF(stromverbr_raumw_korr > 0, IF((ueberschuss_strom / stromverbr_raumw_korr) <= 1, ueberschuss_strom * ETA_STROM_GAS, stromverbr_raumw_korr * ETA_STROM_GAS), 0)`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!P158`

- cached value: `0`
- formula: `"=IF(O158/I158<=Abregelung,'Zeitreihen Kalkulation'!O158,'Zeitreihen Kalkulation'!I158*Abregelung)*EtaStromGas"`

**Notes:** IF(O/I <= Abregelung, O, I*Abregelung) * EtaStromGas — F006

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[abregelung]` — ws365

**DB expression:** `IF(stromverbr_raumw_korr > 0, IF((ueberschuss_strom / stromverbr_raumw_korr) <= 1, 0, ueberschuss_strom - einspeich / ETA_STROM_GAS), 0)`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!Q158`

- cached value: `0`
- formula: `'=IF(O158/I158<=Abregelung,0,O158-P158/EtaStromGas)'`

**Notes:** IF(O/I <= Abregelung, 0, O - P/EtaStromGas)

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[mangel_last]` — ws365

**DB expression:** `stromverbr_raumw_korr - direktverbr_strom`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!R158`

- cached value: `556.9080659807905`
- formula: `'=I158-N158'`

**Notes:** I - N (demand minus direct-consumed)

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[brennstoff_ausgleich]` — ws365

**DB expression:** `brennstoff_factor * mangel_last`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!S158`

- cached value: `15.863611030240202`
- formula: `"='1.Jahresbilanz_Strom'!Q$23/'Zeitreihen Kalkulation'!S$154*'Zeitreihen Kalkulation'!R158"`

**Notes:** brennstoff_factor * mangel_last

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[ueberschuss_strom]` — ws365

**DB expression:** `IF(direktverbr_strom == stromverbr_raumw_korr, wind_solar_konstant - stromverbr_raumw_korr, 0)`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!O158`

- cached value: `0`
- formula: `'=IF(N158=I158,M158-I158,0)'`

**Notes:** IF(N=I, M-I, 0)

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[direktverbr_strom]` — ws365

**DB expression:** `MIN(wind_solar_konstant, stromverbr_raumw_korr)`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!N158`

- cached value: `3281.845210031728`
- formula: `'=IF(M158<=I158,M158,I158)'`

**Notes:** IF(M<=I, M, I)

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[stromverbr_raumw_korr]` — ws365

**DB expression:** `stromverbrauch + davon_raumw_korr`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!I158`

- cached value: `3838.7532760125187`
- formula: `'=I$152*F158/1000+H158'`

**Notes:** I$152*F/1000 + H

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[ausspeich_rueckverstr]` — ws365

**DB expression:** `speicher_ausgl_strom / ETA_GAS_STROM`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!U158`

- cached value: `924.8623161547869`
- formula: `'=T158/EtaRückverstromung'`

**Notes:** T/EtaRückverstromung

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `WS365Formula[ladezust_brutto]` — ws365

**DB expression:** `PREV("ladezust_brutto") + einspeich - ausspeich_rueckverstr - ausspeich_gas`

**Excel ref:** `WS.xlsx{m}!Zeitreihen Kalkulation!None`

- cached value: `None`
- formula: `None`

**Notes:** PREV + einspeich - ausspeich_rueckverstr - ausspeich_gas

**Verdict (auto-inspect):**

## `Formula[WS_ETA_STROM_GAS]` — ws_constant

**DB expression:** `0.65`

**Excel ref:** `WS.xlsx{m}!1.Jahresbilanz_Strom!N33`

- cached value: `0.65`
- formula: `'=IF(O33="",D80,O33)/100'`

**Notes:** =0.65; Excel =IF(O33="",D80,O33)/100 with D80=65

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[WS_ETA_GAS_STROM]` — ws_constant

**DB expression:** `0.585`

**Excel ref:** `WS.xlsx{m}!1.Jahresbilanz_Strom!S33`

- cached value: `0.585`
- formula: `'=IF(T33="",D82,T33)/100'`

**Notes:** =0.585; Excel =IF(T33="",D82,T33)/100 with D82=58.5

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand

## `Formula[WS_ABREGELUNG_THRESHOLD]` — ws_constant

**DB expression:** `0.65`

**Excel ref:** `WS.xlsx{m}!1.Jahresbilanz_Strom!N32`

- cached value: `1`
- formula: `'=IF(O32="",D79,O32)/100'`

**Notes:** DB=0.65 but Excel named Abregelung=1.0 — F006 (dead code)

**Verdict (auto-inspect):**
  - MANUAL_REVIEW — compare DB expr to Excel formula by hand
