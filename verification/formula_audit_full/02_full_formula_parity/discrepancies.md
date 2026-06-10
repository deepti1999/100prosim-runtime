# §02 Full Formula Parity — discrepancies (DIFFERENT verdicts)

Total DIFFERENT: 227

| formula_key | cat | ft | db_expr | excel_formula | note |
|---|---|---|---|---|---|
| `10.2.1` | renewable | status | `Verbrauch_7` | `='4. Verbrauch'!L189` | DB='verbrauch_7' vs Excel="'4.verbrauch'!l189" |
| `10.2.1_ziel_target` | renewable | ziel | `Verbrauch_7` | `='4. Verbrauch'!M189` | DB='verbrauch_7' vs Excel="'4.verbrauch'!m189" |
| `10.2.2` | renewable | status | `Renewable_10_2 / Renewable_10_2_1 * 100` | `=L232/L233%` | DB='renewable_10_2/renewable_10_2_1*100' vs Excel='l232/l233%' |
| `10.2.2_ziel_target` | renewable | ziel | `Renewable_10_2 / Renewable_10_2_1 * 100` | `=M232/M233%` | DB='renewable_10_2/renewable_10_2_1*100' vs Excel='m232/m233%' |
| `10.3.1` | renewable | status | `Verbrauch_1_4 * Renewable_10_2_2 / 100` | `=AH237*L$234%` | DB='verbrauch_1_4*renewable_10_2_2/100' vs Excel='ah237*l234%' |
| `10.3.1_ziel_target` | renewable | ziel | `Verbrauch_1_4 * Renewable_10_2_2 / 100` | `=AI237*M$234%` | DB='verbrauch_1_4*renewable_10_2_2/100' vs Excel='ai237*m234%' |
| `10.4` | renewable | status | `Renewable_10_4_1 + Renewable_10_4_3 + Renewable_10_4_2` | `=L6*L8%*L9/1000` | DB='renewable_10_4_1+renewable_10_4_3+renewable_10_4_2' vs Excel='l6*l8%*l9/1000' |
| `10.4.1` | renewable | status | `Renewable_10_4_1_3 + Renewable_10_4_1_1 + Renewable_10_4_1_2` | `=SUM(L241:L243)` | DB='renewable_10_4_1_3+renewable_10_4_1_1+renewable_10_4_1_2' vs Excel='sum(l241:l243)' |
| `10.4.1.1` | renewable | status | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.4.1.1_ziel_target` | renewable | ziel | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.4.1.2` | renewable | status | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.4.1.2_ziel_target` | renewable | ziel | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.4.1.3` | renewable | status | `Renewable_4_3_1` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_4_3_1' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.4.1.3_ziel_target` | renewable | ziel | `Renewable_4_3_1` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_4_3_1' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.4.1_ziel_target` | renewable | ziel | `Renewable_10_4_1_3 + Renewable_10_4_1_1 + Renewable_10_4_1_2` | `=SUM(M241:M243)` | DB='renewable_10_4_1_3+renewable_10_4_1_1+renewable_10_4_1_2' vs Excel='sum(m241:m243)' |
| `10.4.2` | renewable | status | `Renewable_1_1_1_1_2 + Renewable_7_1_2_3 + Renewable_7_1_4_3 + Renewable_5_4_2_4 ` | `=SUMIF($AD$5:$AD$228,$AD245,L$5:L$228)` | DB='renewable_1_1_1_1_2+renewable_7_1_2_3+renewable_7_1_4_3+renewable_5_4_2_4+renewa' vs Excel='sumi |
| `10.4.2_target` | renewable | ziel | `Renewable_1_1_1_1_2_target + Renewable_7_1_2_3_target + Renewable_7_1_4_3_target` | `=SUMIF($AD$5:$AD$228,$AD245,M$5:M$228)` | DB='renewable_1_1_1_1_2_target+renewable_7_1_2_3_target+renewable_7_1_4_3_target+ren' vs Excel='sumi |
| `10.4.3` | renewable | status | `Verbrauch_2_9_0 * Renewable_10_2_2 / 100` | `=AH237*L$234%` | DB='verbrauch_2_9_0*renewable_10_2_2/100' vs Excel='ah237*l234%' |
| `10.4.3_ziel_target` | renewable | ziel | `Verbrauch_2_9_0 * Renewable_10_2_2 / 100` | `=AI237*M$234%` | DB='verbrauch_2_9_0*renewable_10_2_2/100' vs Excel='ai237*m234%' |
| `10.4_ziel_target` | renewable | ziel | `Renewable_10_4_1 + Renewable_10_4_3 + Renewable_10_4_2` | `=M6*M8%*M9/1000` | DB='renewable_10_4_1+renewable_10_4_3+renewable_10_4_2' vs Excel='m6*m8%*m9/1000' |
| `10.5` | renewable | status | `Renewable_10_5_1 + Renewable_10_5_3 + Renewable_10_5_2` | `=AT63` | DB='renewable_10_5_1+renewable_10_5_3+renewable_10_5_2' vs Excel='at63' |
| `10.5.1` | renewable | status | `Renewable_10_5_1_1 + Renewable_10_5_1_2 + Renewable_10_5_1_3 + Renewable_10_5_1_` | `=SUM(L241:L243)` | DB='renewable_10_5_1_1+renewable_10_5_1_2+renewable_10_5_1_3+renewable_10_5_1_4' vs Excel='sum(l241: |
| `10.5.1.1` | renewable | status | `Renewable_5_4_1_1` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_5_4_1_1' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.5.1.1_ziel_target` | renewable | ziel | `Renewable_5_4_1_1` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_5_4_1_1' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.5.1.2` | renewable | status | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD251,L$5:L$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad251,l5:l228)' |
| `10.5.1.2_ziel_target` | renewable | ziel | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD251,M$5:M$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad251,m5:m228)' |
| `10.5.1.3` | renewable | status | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.5.1.3_ziel_target` | renewable | ziel | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.5.1.4` | renewable | status | `Renewable_4_3_2` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_4_3_2' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.5.1.4_ziel_target` | renewable | ziel | `Renewable_4_3_2` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_4_3_2' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.5.1_ziel_target` | renewable | ziel | `Renewable_10_5_1_1 + Renewable_10_5_1_2 + Renewable_10_5_1_3 + Renewable_10_5_1_` | `=SUM(M241:M243)` | DB='renewable_10_5_1_1+renewable_10_5_1_2+renewable_10_5_1_3+renewable_10_5_1_4' vs Excel='sum(m241: |
| `10.5.2` | renewable | status | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD245,L$5:L$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad245,l5:l228)' |
| `10.5.2_ziel_target` | renewable | ziel | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD245,M$5:M$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad245,m5:m228)' |
| `10.5.3` | renewable | status | `Verbrauch_3_6_0 * Renewable_10_2_2 / 100` | `=AH237*L$234%` | DB='verbrauch_3_6_0*renewable_10_2_2/100' vs Excel='ah237*l234%' |
| `10.5.3_target` | renewable | ziel | `Verbrauch_3_6_0_ziel * Renewable_10_2_2_target / 100` | `=AI237*M$234%` | DB='verbrauch_3_6_0_ziel*renewable_10_2_2_target/100' vs Excel='ai237*m234%' |
| `10.5_ziel_target` | renewable | ziel | `Renewable_10_5_1 + Renewable_10_5_3 + Renewable_10_5_2` | `=100-M62-M64-M65` | DB='renewable_10_5_1+renewable_10_5_3+renewable_10_5_2' vs Excel='100-m62-m64-m65' |
| `10.6.1` | renewable | status | `Renewable_10_6_1_1 + Renewable_10_6_1_2 + Renewable_10_6_1_3` | `=SUM(L261:L262)` | DB='renewable_10_6_1_1+renewable_10_6_1_2+renewable_10_6_1_3' vs Excel='sum(l261:l262)' |
| `10.6.1.1` | renewable | status | `FIXED VALUE: davon Wasserstoff (FC-Traktion)` | `=SUMIF($AD$5:$AD$228,$AD251,L$5:L$228)` | DB='fixedvalue:davonwasserstoff(fc-traktion)' vs Excel='sumif(ad5:ad228,ad251,l5:l228)' |
| `10.6.1.1_ziel_target` | renewable | ziel | `FIXED VALUE: davon Wasserstoff (FC-Traktion)` | `=SUMIF($AD$5:$AD$228,$AD251,M$5:M$228)` | DB='fixedvalue:davonwasserstoff(fc-traktion)' vs Excel='sumif(ad5:ad228,ad251,m5:m228)' |
| `10.6.1.2` | renewable | status | `Renewable_5_4_3_2` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_5_4_3_2' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.6.1.2_ziel_target` | renewable | ziel | `Renewable_5_4_3_2` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_5_4_3_2' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.6.1.3` | renewable | status | `Renewable_6_1_3_1_1 + Renewable_6_2_3 + Renewable_9_2_1_3` | `=SUMIF($AD$5:$AD$228,$AD252,L$5:L$228)` | DB='renewable_6_1_3_1_1+renewable_6_2_3+renewable_9_2_1_3' vs Excel='sumif(ad5:ad228,ad252,l5:l228)' |
| `10.6.1.3_ziel_target` | renewable | ziel | `Renewable_6_1_3_1_1 + Renewable_6_2_3 + Renewable_9_2_1_3` | `=SUMIF($AD$5:$AD$228,$AD252,M$5:M$228)` | DB='renewable_6_1_3_1_1+renewable_6_2_3+renewable_9_2_1_3' vs Excel='sumif(ad5:ad228,ad252,m5:m228)' |
| `10.6.1_ziel_target` | renewable | ziel | `Renewable_10_6_1_1 + Renewable_10_6_1_2 + Renewable_10_6_1_3` | `=SUM(M260:M262)` | DB='renewable_10_6_1_1+renewable_10_6_1_2+renewable_10_6_1_3' vs Excel='sum(m260:m262)' |
| `10.6.2` | renewable | status | `Verbrauch_6_2 * Renewable_10_2_2 / 100` | `=AH237*L$234%` | DB='verbrauch_6_2*renewable_10_2_2/100' vs Excel='ah237*l234%' |
| `10.6.2_ziel_target` | renewable | ziel | `Verbrauch_6_2 * Renewable_10_2_2 / 100` | `=AI237*M$234%` | DB='verbrauch_6_2*renewable_10_2_2/100' vs Excel='ai237*m234%' |
| `10.7.1` | renewable | status | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD251,L$5:L$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad251,l5:l228)' |
| `10.7.1_ziel_target` | renewable | ziel | `Renewable_4_3_4_2` | `=SUMIF($AD$5:$AD$228,$AD251,M$5:M$228)` | DB='renewable_4_3_4_2' vs Excel='sumif(ad5:ad228,ad251,m5:m228)' |
| `10.7.2` | renewable | status | `Renewable_5_4_3_2 + Renewable_5_4_1_1` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_5_4_3_2+renewable_5_4_1_1' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.7.2_ziel_target` | renewable | ziel | `Renewable_5_4_3_2 + Renewable_5_4_1_1` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_5_4_3_2+renewable_5_4_1_1' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.7.3` | renewable | status | `Renewable_10_6_1_3` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_10_6_1_3' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.7.3_ziel_target` | renewable | ziel | `Renewable_10_6_1_3` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_10_6_1_3' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.7.4` | renewable | status | `Renewable_4_3_1 + Renewable_4_3_2` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_4_3_1+renewable_4_3_2' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.7.4_ziel_target` | renewable | ziel | `Renewable_4_3_1 + Renewable_4_3_2` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_4_3_1+renewable_4_3_2' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.9.1.1` | renewable | status | `Renewable_5_1_2 + Renewable_5_2 + Renewable_5_3` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_5_1_2+renewable_5_2+renewable_5_3' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.9.1.1_ziel_target` | renewable | ziel | `Renewable_5_1_2 + Renewable_5_2 + Renewable_5_3` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_5_1_2+renewable_5_2+renewable_5_3' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `10.9.1.2` | renewable | status | `Renewable_6_1_1_2 + Renewable_6_1_2 + Renewable_6_2_2 + Renewable_6_2_1_2` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_6_1_1_2+renewable_6_1_2+renewable_6_2_2+renewable_6_2_1_2' vs Excel='sumif(ad5:ad228,a |
| `10.9.1.2_ziel_target` | renewable | ziel | `Renewable_6_1_1_2 + Renewable_6_1_2 + Renewable_6_2_2 + Renewable_6_2_1_2` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_6_1_1_2+renewable_6_1_2+renewable_6_2_2+renewable_6_2_1_2' vs Excel='sumif(ad5:ad228,a |
| `10.9.1.3` | renewable | status | `Renewable_4_3 + Renewable_4_4` | `=SUMIF($AD$5:$AD$228,$AD241,L$5:L$228)` | DB='renewable_4_3+renewable_4_4' vs Excel='sumif(ad5:ad228,ad241,l5:l228)' |
| `10.9.1.3_ziel_target` | renewable | ziel | `Renewable_4_3 + Renewable_4_4` | `=SUMIF($AD$5:$AD$228,$AD241,M$5:M$228)` | DB='renewable_4_3+renewable_4_4' vs Excel='sumif(ad5:ad228,ad241,m5:m228)' |
| `1.1.1.1.2` | renewable | status | `Renewable_1_1 * (Renewable_1_1_1_1/100) * Renewable_1_1_1_1_1 / 1000` | `=L6*L8%*L9/1000` | DB='renewable_1_1*(renewable_1_1_1_1/100)*renewable_1_1_1_1_1/1000' vs Excel='l6*l8%*l9/1000' |
| `1.1.1.1.2_ziel_target` | renewable | ziel | `Renewable_1_1 * (Renewable_1_1_1_1/100) * Renewable_1_1_1_1_1 / 1000` | `=M6*M8%*M9/1000` | DB='renewable_1_1*(renewable_1_1_1_1/100)*renewable_1_1_1_1_1/1000' vs Excel='m6*m8%*m9/1000' |
| `1.1.2.1` | renewable | status | `100 - Renewable_1_1_1_1` | `=AT8` | DB='100-renewable_1_1_1_1' vs Excel='at8' |
| `1.1.2.1.1_target` | renewable | ziel | `Renewable_1_1_zeil *Renewable_1_1_2_1_zeil/100* Renewable_1_1_2_1_1_zeil` | `=IF(P9="",AU9,P9)` | DB='renewable_1_1_zeil*renewable_1_1_2_1_zeil/100*renewable_1_1_2_1_1_zeil' vs Excel='if(p9="",au9,p |
| `1.1.2.1.2` | renewable | status | `Renewable_1_1 * Renewable_1_1_2_1 / 100 * Renewable_1_1_2_1_1 / 1000` | `=L6*L13%*L14/1000` | DB='renewable_1_1*renewable_1_1_2_1/100*renewable_1_1_2_1_1/1000' vs Excel='l6*l13%*l14/1000' |
| `1.1.2.1.2.2` | renewable | status | `Renewable_1_1_2_1_2 / Renewable_1_1_2_1_2_1 * 1000` | `=L15*1000/L16` | DB='renewable_1_1_2_1_2/renewable_1_1_2_1_2_1*1000' vs Excel='l15*1000/l16' |
| `1.1.2.1.2.2_target` | renewable | ziel | `Renewable_1_1_2_1_2_ziel / Renewable_1_1_2_1_2_1_ziel * 1000` | `=M15*1000/M16` | DB='renewable_1_1_2_1_2_ziel/renewable_1_1_2_1_2_1_ziel*1000' vs Excel='m15*1000/m16' |
| `1.1.2.1.2_target` | renewable | ziel | `Renewable_1_1_ziel * Renewable_1_1_2_1_ziel / 100 * Renewable_1_1_2_1_1_ziel / 1` | `=M6*M13%*M14/1000` | DB='renewable_1_1_ziel*renewable_1_1_2_1_ziel/100*renewable_1_1_2_1_1_ziel/1000' vs Excel='m6*m13%*m |
| `1.1.2.1_target` | renewable | ziel | `100-Renewable_1_1_1_1_ziel` | `=IF(P8="",AU8,P8)` | DB='100-renewable_1_1_1_1_ziel' vs Excel='if(p8="",au8,p8)' |
| `1.1.2.1_ziel_target` | renewable | ziel | `100 - AnteilThermie` | `=IF(P8="",AU8,P8)` | DB='100-anteilthermie' vs Excel='if(p8="",au8,p8)' |
| `1.1_ziel_target` | renewable | ziel | `LandUse_LU_1.1` | `=IF(P6="",AQ6,P6)` | DB='landuse_lu_1.1' vs Excel='if(p6="",aq6,p6)' |
| `1.2.1.2` | renewable | status | `LandUse_LU_2.1 * Renewable_1_2_1_1 / 1000` | `=L6*L13%*L14/1000` | DB='landuse_lu_2.1*renewable_1_2_1_1/1000' vs Excel='l6*l13%*l14/1000' |
| `1.2.1.2.2` | renewable | status | `Renewable_1_2_1_2 / Renewable_1_2_1_2_1 * 1000` | `=L15*1000/L16` | DB='renewable_1_2_1_2/renewable_1_2_1_2_1*1000' vs Excel='l15*1000/l16' |
| `1.2.1.2.2_ziel_target` | renewable | ziel | `Renewable_1_2_1_2 / Renewable_1_2_1_2_1 * 1000` | `=M15*1000/M16` | DB='renewable_1_2_1_2/renewable_1_2_1_2_1*1000' vs Excel='m15*1000/m16' |
| `1.2.1.2_ziel_target` | renewable | ziel | `LandUse_LU_2.1 * Renewable_1_2_1_1 / 1000` | `=M6*M13%*M14/1000` | DB='landuse_lu_2.1*renewable_1_2_1_1/1000' vs Excel='m6*m13%*m14/1000' |
| `1.2_target` | renewable | ziel | `LandUse_LU_2.1_ziel` | `=IF(P19="",AQ19,P19)` | DB='landuse_lu_2.1_ziel' vs Excel='if(p19="",aq19,p19)' |
| `2.1.1.2` | renewable | status | `Renewable_2_1_1 / Renewable_2_1_1_1` | `=L15*1000/L16` | DB='renewable_2_1_1/renewable_2_1_1_1' vs Excel='l15*1000/l16' |
| `2.1.1.2.2` | renewable | status | `Renewable_2_1_1_2 * Renewable_2_1_1_2_1 / 1000` | `=L6*L13%*L14/1000` | DB='renewable_2_1_1_2*renewable_2_1_1_2_1/1000' vs Excel='l6*l13%*l14/1000' |
| `2.1.1.2.2_ziel_target` | renewable | ziel | `Renewable_2_1_1_2 * Renewable_2_1_1_2_1 / 1000` | `=M6*M13%*M14/1000` | DB='renewable_2_1_1_2*renewable_2_1_1_2_1/1000' vs Excel='m6*m13%*m14/1000' |
| `2.1.1.2.3` | renewable | status | `Renewable_2_1_1_2_2 * 1000 / Renewable_2_1_1` | `=AT9` | DB='renewable_2_1_1_2_2*1000/renewable_2_1_1' vs Excel='at9' |
| `2.1.1.2.3_ziel_target` | renewable | ziel | `Renewable_2_1_1_2_2 * 1000 / Renewable_2_1_1` | `=IF(P9="",AU9,P9)` | DB='renewable_2_1_1_2_2*1000/renewable_2_1_1' vs Excel='if(p9="",au9,p9)' |
| `2.1.1.2_ziel_target` | renewable | ziel | `Renewable_2_1_1 / Renewable_2_1_1_1` | `=M15*1000/M16` | DB='renewable_2_1_1/renewable_2_1_1_1' vs Excel='m15*1000/m16' |
| `2.1.1_ziel_target` | renewable | ziel | `LandUse_LU_6` | `=IF(P28="",AQ28,P28)` | DB='landuse_lu_6' vs Excel='if(p28="",aq28,p28)' |
| `3.1.1.2` | renewable | status | `Renewable_3_1 * Renewable_3_1_1 / 100 * Renewable_3_1_1_1 / 1000` | `=L6*L13%*L14/1000` | DB='renewable_3_1*renewable_3_1_1/100*renewable_3_1_1_1/1000' vs Excel='l6*l13%*l14/1000' |
| `3.1.1.2_ziel_target` | renewable | ziel | `Renewable_3_1 * Renewable_3_1_1 / 100 * Renewable_3_1_1_1 / 1000` | `=M6*M13%*M14/1000` | DB='renewable_3_1*renewable_3_1_1/100*renewable_3_1_1_1/1000' vs Excel='m6*m13%*m14/1000' |
| `4.1.1.1.1.2` | renewable | status | `Renewable_4_1_1_1 * Renewable_4_1_1_1_1 / 100 * Renewable_4_1_1_1_1_1 / 1000` | `=L51*L52%*L53/1000` | DB='renewable_4_1_1_1*renewable_4_1_1_1_1/100*renewable_4_1_1_1_1_1/1000' vs Excel='l51*l52%*l53/100 |
| `4.1.1.1.1.2_ziel_target` | renewable | ziel | `Renewable_4_1_1_1 * Renewable_4_1_1_1_1 / 100 * Renewable_4_1_1_1_1_1 / 1000` | `=M51*M52%*M53/1000` | DB='renewable_4_1_1_1*renewable_4_1_1_1_1/100*renewable_4_1_1_1_1_1/1000' vs Excel='m51*m52%*m53/100 |
| `4.1.1.1_ziel_target` | renewable | ziel | `LandUse_LU_3.1` | `=IF(P51="",AQ51,P51)` | DB='landuse_lu_3.1' vs Excel='if(p51="",aq51,p51)' |
| `4.1.2.1.2` | renewable | status | `Renewable_4_1_2_1 * Renewable_4_1_2_1_1 / 1000` | `=L51*L52%*L53/1000` | DB='renewable_4_1_2_1*renewable_4_1_2_1_1/1000' vs Excel='l51*l52%*l53/1000' |
| `4.1.2.1.2_ziel_target` | renewable | ziel | `Renewable_4_1_2_1 * Renewable_4_1_2_1_1 / 1000` | `=M51*M52%*M53/1000` | DB='renewable_4_1_2_1*renewable_4_1_2_1_1/1000' vs Excel='m51*m52%*m53/1000' |
| `4.1.2.1_ziel_target` | renewable | ziel | `LandUse_LU_2.2.5` | `=IF(P57="",AQ57,P57)` | DB='landuse_lu_2.2.5' vs Excel='if(p57="",aq57,p57)' |
| `4.1.3.1` | renewable | status | `-4.3` | `=AT62` | DB='-4.3' vs Excel='at62' |
| `4.1.3.1_ziel_target` | renewable | ziel | `-4.3` | `=IF(P62="",AU62,P62)` | DB='-4.3' vs Excel='if(p62="",au62,p62)' |
| `4.1.3.2` | renewable | status | `100 - Renewable_4_1_3_1 - Renewable_4_1_3_3 - Renewable_4_1_3_4` | `=AT63` | DB='100-renewable_4_1_3_1-renewable_4_1_3_3-renewable_4_1_3_4' vs Excel='at63' |
| `4.2.1.1.2` | renewable | status | `Renewable_4_2_1 * Renewable_4_2_1_1 / 100 * Renewable_4_2_1_1_1 / 1000` | `=L68*L69%*L70/1000` | DB='renewable_4_2_1*renewable_4_2_1_1/100*renewable_4_2_1_1_1/1000' vs Excel='l68*l69%*l70/1000' |
| `4.2.1.1.2.2` | renewable | status | `100 - Renewable_4_2_1_1_2_1 - Renewable_4_2_1_1_2_3 - Renewable_4_2_1_1_2_4` | `=AT63` | DB='100-renewable_4_2_1_1_2_1-renewable_4_2_1_1_2_3-renewable_4_2_1_1_2_4' vs Excel='at63' |
| `4.2.1.1.2_ziel_target` | renewable | ziel | `Renewable_4_2_1 * Renewable_4_2_1_1 / 100 * Renewable_4_2_1_1_1 / 1000` | `=M68*M69%*M70/1000` | DB='renewable_4_2_1*renewable_4_2_1_1/100*renewable_4_2_1_1_1/1000' vs Excel='m68*m69%*m70/1000' |
| `4.2.1_target` | renewable | ziel | `LandUse_2.2.1` | `=IF(P68="",AQ68,P68)` | DB='landuse_2.2.1' vs Excel='if(p68="",aq68,p68)' |
| `4.3.2` | renewable | status | `Renewable_4_1_3*Renewable_4_1_3_2/100+Renewable_4_2_1_1_2*Renewable_4_2_1_1_2_2` | `=L61*L63%+L71*L73%` | DB='renewable_4_1_3*renewable_4_1_3_2/100+renewable_4_2_1_1_2*renewable_4_2_1_1_2_2' vs Excel='l61*l |
| `4.3.2_ziel_target` | renewable | ziel | `Renewable_4_2_1_1_2+Renewable_4_1_2_1_2+Renewable_4_1_1_1_1_2` | `=M61*M63%+M71*M73%` | DB='renewable_4_2_1_1_2+renewable_4_1_2_1_2+renewable_4_1_1_1_1_2' vs Excel='m61*m63%+m71*m73%' |
| `4.3.3` | renewable | status | `Renewable_4_1_3*Renewable_4_1_3_3/100+Renewable_4_2_1_1_2*Renewable_4_2_1_1_2_3/` | `=L61*L64%+L71*L74%` | DB='renewable_4_1_3*renewable_4_1_3_3/100+renewable_4_2_1_1_2*renewable_4_2_1_1_2_3/' vs Excel='l61* |
| `4.3.3.2` | renewable | status | `Renewable_4_3_3 * Renewable_4_3_3_1 / 100` | `=L6*L13%*L14/1000` | DB='renewable_4_3_3*renewable_4_3_3_1/100' vs Excel='l6*l13%*l14/1000' |
| `4.3.3.2_ziel_target` | renewable | ziel | `Renewable_4_3_3 * Renewable_4_3_3_1 / 100` | `=M6*M13%*M14/1000` | DB='renewable_4_3_3*renewable_4_3_3_1/100' vs Excel='m6*m13%*m14/1000' |
| `4.3.3.4` | renewable | status | `Renewable_4_3_3_2 * Renewable_4_3_3_3 / Renewable_4_3_3_1` | `=L83*L86%` | DB='renewable_4_3_3_2*renewable_4_3_3_3/renewable_4_3_3_1' vs Excel='l83*l86%' |
| `4.3.3.4_ziel_target` | renewable | ziel | `Renewable_4_3_3_2 * Renewable_4_3_3_3 / Renewable_4_3_3_1` | `=M83*M86%` | DB='renewable_4_3_3_2*renewable_4_3_3_3/renewable_4_3_3_1' vs Excel='m83*m86%' |
| `4.3.3_ziel_target` | renewable | ziel | `Renewable_4_3 * Renewable_4_1_3_3 / 100` | `=M61*M64%+M71*M74%` | DB='renewable_4_3*renewable_4_1_3_3/100' vs Excel='m61*m64%+m71*m74%' |
| `4.3.4.2` | renewable | status | `Renewable_4_3_4 * Renewable_4_3_4_1 / 100` | `=L83*L86%` | DB='renewable_4_3_4*renewable_4_3_4_1/100' vs Excel='l83*l86%' |
| `4.3.4.2_ziel_target` | renewable | ziel | `Renewable_4_3_4 * Renewable_4_3_4_1 / 100` | `=M83*M86%` | DB='renewable_4_3_4*renewable_4_3_4_1/100' vs Excel='m83*m86%' |
| `5.1_target` | renewable | ziel | `LandUse_2.2.2` | `=IF(P98="",AQ98,P98)` | DB='landuse_2.2.2' vs Excel='if(p98="",aq98,p98)' |
| `5.4.1.1` | renewable | status | `Renewable_5_4 * Renewable_5_4_1 / 100` | `=L$104*L105%` | DB='renewable_5_4*renewable_5_4_1/100' vs Excel='l104*l105%' |
| `5.4.1.1_ziel_target` | renewable | ziel | `Renewable_5_4 * Renewable_5_4_1 / 100` | `=M$104*M105%` | DB='renewable_5_4*renewable_5_4_1/100' vs Excel='m104*m105%' |
| `5.4.2.2` | renewable | status | `Renewable_5_4 * Renewable_5_4_2 / 100 * Renewable_5_4_2_1 / 100` | `=L83*L84%` | DB='renewable_5_4*renewable_5_4_2/100*renewable_5_4_2_1/100' vs Excel='l83*l84%' |
| `5.4.2.2_ziel_target` | renewable | ziel | `Renewable_5_4 * Renewable_5_4_2 / 100 * Renewable_5_4_2_1 / 100` | `=M83*M84%` | DB='renewable_5_4*renewable_5_4_2/100*renewable_5_4_2_1/100' vs Excel='m83*m84%' |
| `5.4.2.4` | renewable | status | `Renewable_5_4 * (Renewable_5_4_2 / 100) * (Renewable_5_4_2_3 / 100)` | `=L104*L108%*L111%` | DB='renewable_5_4*(renewable_5_4_2/100)*(renewable_5_4_2_3/100)' vs Excel='l104*l108%*l111%' |
| `5.4.2.4_ziel_target` | renewable | ziel | `Renewable_5_4 * (Renewable_5_4_2 / 100) * (Renewable_5_4_2_3 / 100)` | `=M104*M108%*M111%` | DB='renewable_5_4*(renewable_5_4_2/100)*(renewable_5_4_2_3/100)' vs Excel='m104*m108%*m111%' |
| `5.4.3.2` | renewable | status | `Renewable_5_4 * Renewable_5_4_3 / 100 * Renewable_5_4_3_1 / 100` | `=L$104*L114%*L115%` | DB='renewable_5_4*renewable_5_4_3/100*renewable_5_4_3_1/100' vs Excel='l104*l114%*l115%' |
| `5.4.3.2_ziel_target` | renewable | ziel | `Renewable_5_4 * Renewable_5_4_3 / 100 * Renewable_5_4_3_1 / 100` | `=M$104*M114%*M115%` | DB='renewable_5_4*renewable_5_4_3/100*renewable_5_4_3_1/100' vs Excel='m104*m114%*m115%' |
| `5.4.4.2` | renewable | status | `Renewable_5_4 * (Renewable_5_4_4 / 100) * (Renewable_5_4_4_1 / 100)` | `=L$104*L118%*L119%` | DB='renewable_5_4*(renewable_5_4_4/100)*(renewable_5_4_4_1/100)' vs Excel='l104*l118%*l119%' |
| `5.4.4.2_ziel_target` | renewable | ziel | `Renewable_5_4 * (Renewable_5_4_4 / 100) * (Renewable_5_4_4_1 / 100)` | `=M$104*M118%*M119%` | DB='renewable_5_4*(renewable_5_4_4/100)*(renewable_5_4_4_1/100)' vs Excel='m104*m118%*m119%' |
| `6.1.1_target` | renewable | ziel | `lu_223_target` | `=IF(P124="",AQ124,P124)` | DB='lu_223_target' vs Excel='if(p124="",aq124,p124)' |
| `6.1.3.1.1` | renewable | status | `Renewable_6_1_3 * Renewable_6_1_3_1 / 100` | `=L$104*L118%*L119%` | DB='renewable_6_1_3*renewable_6_1_3_1/100' vs Excel='l104*l118%*l119%' |
| `6.1.3.1.1_ziel_target` | renewable | ziel | `Renewable_6_1_3 * Renewable_6_1_3_1 / 100` | `=M$104*M118%*M119%` | DB='renewable_6_1_3*renewable_6_1_3_1/100' vs Excel='m104*m118%*m119%' |
| `6.1.3.2.2` | renewable | status | `Renewable_6_1_3 * Renewable_6_1_3_2 * Renewable_6_1_3_2_1 / 10000` | `=L129*L133%*L134%` | DB='renewable_6_1_3*renewable_6_1_3_2*renewable_6_1_3_2_1/10000' vs Excel='l129*l133%*l134%' |
| `6.1.3.2.2_ziel_target` | renewable | ziel | `Renewable_6_1_3 * Renewable_6_1_3_2 * Renewable_6_1_3_2_1 / 10000` | `=M129*M133%*M134%` | DB='renewable_6_1_3*renewable_6_1_3_2*renewable_6_1_3_2_1/10000' vs Excel='m129*m133%*m134%' |
| `6.1.3.2.4` | renewable | status | `Renewable_6_1_3 * (Renewable_6_1_3_2 / 100) * (Renewable_6_1_3_2_3 / 100)` | `=L129*L133%*L136%` | DB='renewable_6_1_3*(renewable_6_1_3_2/100)*(renewable_6_1_3_2_3/100)' vs Excel='l129*l133%*l136%' |
| `6.1.3.2.4_ziel_target` | renewable | ziel | `Renewable_6_1_3 * (Renewable_6_1_3_2 / 100) * (Renewable_6_1_3_2_3 / 100)` | `=M129*M133%*M136%` | DB='renewable_6_1_3*(renewable_6_1_3_2/100)*(renewable_6_1_3_2_3/100)' vs Excel='m129*m133%*m136%' |
| `6.2.1_ziel_target` | renewable | ziel | `LandUse_LU_2.2.4` | `=IF(P57="",AQ57,P57)` | DB='landuse_lu_2.2.4' vs Excel='if(p57="",aq57,p57)' |
| `7.1` | renewable | status | `Verbrauch_2_9_2` | `='4. Verbrauch'!L89` | DB='verbrauch_2_9_2' vs Excel="'4.verbrauch'!l89" |
| `7.1.2` | renewable | status | `Renewable_7_1 * Renewable_7_1_1 / 100` | `=L148*L149%` | DB='renewable_7_1*renewable_7_1_1/100' vs Excel='l148*l149%' |
| `7.1.2_target` | renewable | ziel | `Renewable_7_1_ziel * Renewable_7_1_1_ziel / 100` | `=M$148*M149%` | DB='renewable_7_1_ziel*renewable_7_1_1_ziel/100' vs Excel='m148*m149%' |
| `7.1.4.3.3_ziel_target` | renewable | ziel | `LandUse_LU_1` | `=IF(P162="",AQ162,P162)` | DB='landuse_lu_1' vs Excel='if(p162="",aq162,p162)' |
| `7.1_target` | renewable | ziel | `V_2_9_0_ziel` | `='4. Verbrauch'!M89` | DB='v_2_9_0_ziel' vs Excel="'4.verbrauch'!m89" |
| `8.1.2` | renewable | status | `Renewable_8_1 * Renewable_8_1_1 / 1000` | `=L6*L13%*L14/1000` | DB='renewable_8_1*renewable_8_1_1/1000' vs Excel='l6*l13%*l14/1000' |
| `8.1.2_ziel_target` | renewable | ziel | `Renewable_8_1 * Renewable_8_1_1 / 1000` | `=M6*M13%*M14/1000` | DB='renewable_8_1*renewable_8_1_1/1000' vs Excel='m6*m13%*m14/1000' |
| `9.1` | renewable | status | `Renewable_9_1_1 + Renewable_9_1_2 + Renewable_9_1_3 + Renewable_9_1_4` | `=L6*L13%*L14/1000` | DB='renewable_9_1_1+renewable_9_1_2+renewable_9_1_3+renewable_9_1_4' vs Excel='l6*l13%*l14/1000' |
| `9.1_ziel_target` | renewable | ziel | `Renewable_9_1_1 + Renewable_9_1_2 + Renewable_9_1_3 + Renewable_9_1_4` | `=M6*M13%*M14/1000` | DB='renewable_9_1_1+renewable_9_1_2+renewable_9_1_3+renewable_9_1_4' vs Excel='m6*m13%*m14/1000' |
| `9.2` | renewable | status | `Renewable_9_1_1 + Renewable_9_1_2 + Renewable_9_1_3 + Renewable_9_1_4` | `=L6*L13%*L14/1000` | DB='renewable_9_1_1+renewable_9_1_2+renewable_9_1_3+renewable_9_1_4' vs Excel='l6*l13%*l14/1000' |
| `9.2.1.1.1.1_ziel_target` | renewable | ziel | `80` | `=IF(P192="",AU192,P192)` | DB='80' vs Excel='if(p192="",au192,p192)' |
| `9.2.1.3.2` | renewable | status | `Renewable_9_2_1_3 / (Renewable_9_2_1_3_1 / 100)` | `=L185*L194%` | DB='renewable_9_2_1_3/(renewable_9_2_1_3_1/100)' vs Excel='l185*l194%' |
| `9.2.1.3.2_ziel_target` | renewable | ziel | `Renewable_9_2_1_3 / (Renewable_9_2_1_3_1 / 100)` | `=M195/M196%` | DB='renewable_9_2_1_3/(renewable_9_2_1_3_1/100)' vs Excel='m195/m196%' |
| `9.2.1.4` | renewable | status | `Verbrauch_9_1_4` | `='4. Verbrauch'!L198` | DB='verbrauch_9_1_4' vs Excel="'4.verbrauch'!l198" |
| `9.2.1.4.2` | renewable | status | `Renewable_9_2_1_4 * 100 / Renewable_9_2_1_4_1` | `=L202*L203%` | DB='renewable_9_2_1_4*100/renewable_9_2_1_4_1' vs Excel='l202*l203%' |
| `9.2.1.4.2_ziel_target` | renewable | ziel | `Renewable_9_2_1_4 * 100 / Renewable_9_2_1_4_1` | `=M202/M203%` | DB='renewable_9_2_1_4*100/renewable_9_2_1_4_1' vs Excel='m202/m203%' |
| `9.2.1.4_target` | renewable | ziel | `Verbrauch_9_1_4` | `='4. Verbrauch'!M198` | DB='verbrauch_9_1_4' vs Excel="'4.verbrauch'!m198" |
| `9.2.1.5` | renewable | status | `Renewable_9_2_1_1 + Renewable_9_2_1_1_2 + Renewable_9_2_1_2_2 + Renewable_9_2_1_` | `=L189+L201+L204` | DB='renewable_9_2_1_1+renewable_9_2_1_1_2+renewable_9_2_1_2_2+renewable_9_2_1_3_2+re' vs Excel='l189 |
| `9.2.1.5.2` | renewable | status | `Renewable_9_2_1_5 * 100 / Renewable_9_2_1_5_1` | `=L189+L201+L204` | DB='renewable_9_2_1_5*100/renewable_9_2_1_5_1' vs Excel='l189+l201+l204' |
| `9.2.1.5.2_ziel_target` | renewable | ziel | `Renewable_9_2_1_5 * 100 / Renewable_9_2_1_5_1` | `=M189+M193+M197+M201+M204` | DB='renewable_9_2_1_5*100/renewable_9_2_1_5_1' vs Excel='m189+m193+m197+m201+m204' |
| `9.2_target` | renewable | ziel | `Renewable_9_1_1_ziel + Renewable_9_1_2_ziel+ Renewable_9_1_3_ziel + Renewable_9_` | `=M6*M13%*M14/1000` | DB='renewable_9_1_1_ziel+renewable_9_1_2_ziel+renewable_9_1_3_ziel+renewable_9_1_4_z' vs Excel='m6*m |
| `9.3.1.2` | renewable | status | `Renewable_9_3_1 * Renewable_9_3_1_1 / 100` | `=L213*L212%` | DB='renewable_9_3_1*renewable_9_3_1_1/100' vs Excel='l213*l212%' |
| `9.3.1.2_target` | renewable | ziel | `Renewable_9_3_1_zeil * Renewable_9_3_1_1_zeil / 100` | `=M212*M213%` | DB='renewable_9_3_1_zeil*renewable_9_3_1_1_zeil/100' vs Excel='m212*m213%' |
| `9.3.2.1` | renewable | status | `Renewable_9_3_1 * Renewable_9_3_2 / 100` | `=L104*L108%*L111%` | DB='renewable_9_3_1*renewable_9_3_2/100' vs Excel='l104*l108%*l111%' |
| `9.3.2.1_ziel_target` | renewable | ziel | `Renewable_9_3_1 * Renewable_9_3_2 / 100` | `=M104*M108%*M111%` | DB='renewable_9_3_1*renewable_9_3_2/100' vs Excel='m104*m108%*m111%' |
| `9.4.3.2` | renewable | status | `Renewable_9_4_3 * Renewable_9_4_3_1 / 100` | `=L224*L225%` | DB='renewable_9_4_3*renewable_9_4_3_1/100' vs Excel='l224*l225%' |
| `9.4.3.2_target` | renewable | ziel | `Renewable_9_4_3_ziel * Renewable_9_4_3_1_ziel / 100` | `=M224*M225%` | DB='renewable_9_4_3_ziel*renewable_9_4_3_1_ziel/100' vs Excel='m224*m225%' |
| `4.1.1.14_ziel` | verbrauch | ziel | `100 - Verbrauch_4_1_1_9_ziel` | `=IF(M143="Aktiv",0,100-M135)` | DB='100-verbrauch_4_1_1_9_ziel' vs Excel='if(m143="aktiv",0,100-m135)' |
| `V_2.1.2_ziel` | verbrauch | ziel | `V_2_1_1_ziel/V_2_1_1_status*100` | `=M48/L48%` | DB='v_2_1_1_ziel/v_2_1_1_status*100' vs Excel='m48/l48%' |
| `V_2.4.2` | verbrauch | status | `Verbrauch_2_4_1 / Verbrauch_2_4_1 * 100` | `=L60/L60%` | DB='verbrauch_2_4_1/verbrauch_2_4_1*100' vs Excel='l60/l60%' |
| `V_2.4.2_ziel` | verbrauch | ziel | `(V_2_4_1_ziel - V_2_4_1_status) / V_2_4_1_status * 100` | `=(M60-L60)/L60%` | DB='(v_2_4_1_ziel-v_2_4_1_status)/v_2_4_1_status*100' vs Excel='(m60-l60)/l60%' |
| `V_2.4.6_ziel` | verbrauch | ziel | `V_2_4_1_status*(1-V_2_4_5_ziel/100)+V_2_4_1_ziel*V_2_4_5_ziel/100` | `=L66*(1-M65%)+M60*M65%` | DB='v_2_4_1_status*(1-v_2_4_5_ziel/100)+v_2_4_1_ziel*v_2_4_5_ziel/100' vs Excel='l66*(1-m65%)+m60*m6 |
| `V_2.4.7` | verbrauch | status | `Verbrauch_2_4_5 * Verbrauch_2_4_2 / 100` | `=L65*L61%` | DB='verbrauch_2_4_5*verbrauch_2_4_2/100' vs Excel='l65*l61%' |
| `V_2.4.7_ziel` | verbrauch | ziel | `V_2_4_5_ziel * V_2_4_2_ziel / 100` | `=M65*M61%` | DB='v_2_4_5_ziel*v_2_4_2_ziel/100' vs Excel='m65*m61%' |
| `V_2.4.9` | verbrauch | status | `Verbrauch_2_4_0 * (100 + Verbrauch_2_4_7) / 100` | `=L59*(100+L67)%` | DB='verbrauch_2_4_0*(100+verbrauch_2_4_7)/100' vs Excel='l59*(100+l67)%' |
| `V_2.4.9_ziel` | verbrauch | ziel | `V_2_4_0_ziel * (100 + V_2_4_7_ziel) / 100` | `=M59*(100+M67)%` | DB='v_2_4_0_ziel*(100+v_2_4_7_ziel)/100' vs Excel='m59*(100+m67)%' |
| `V_2.5.2` | verbrauch | status | `Verbrauch_2_5_0 * Verbrauch_2_5_1 / 100` | `=L29*L30%` | DB='verbrauch_2_5_0*verbrauch_2_5_1/100' vs Excel='l29*l30%' |
| `V_2.5.2_ziel` | verbrauch | ziel | `Verbrauch_2_5_0_ziel * Verbrauch_2_5_1_ziel / 100` | `=M29*M30%` | DB='verbrauch_2_5_0_ziel*verbrauch_2_5_1_ziel/100' vs Excel='m29*m30%' |
| `V_2.5.3` | verbrauch | status | `Verbrauch_2_5_2 / Verbrauch_2_6 * 100` | `=L73/L75%` | DB='verbrauch_2_5_2/verbrauch_2_6*100' vs Excel='l73/l75%' |
| `V_2.5.3_ziel` | verbrauch | ziel | `Verbrauch_2_5_2_ziel  /Verbrauch_2_6_ziel * 100` | `=M73/M75%` | DB='verbrauch_2_5_2_ziel/verbrauch_2_6_ziel*100' vs Excel='m73/m75%' |
| `V_2.7.0` | verbrauch | status | `Verbrauch_2_6 * Verbrauch_2_7 / 100` | `=L$75*L76%` | DB='verbrauch_2_6*verbrauch_2_7/100' vs Excel='l75*l76%' |
| `V_2.7.0_ziel` | verbrauch | ziel | `Verbrauch_2_6_zeil * Verbrauch_2_7_zeil / 100` | `=M$75*M76%` | DB='verbrauch_2_6_zeil*verbrauch_2_7_zeil/100' vs Excel='m75*m76%' |
| `V_2.7.2` | verbrauch | status | `Verbrauch_2_7 * (1 - Verbrauch_2_7_1 / 100)` | `=L76*(1-L78%)` | DB='verbrauch_2_7*(1-verbrauch_2_7_1/100)' vs Excel='l76*(1-l78%)' |
| `V_2.7.2_ziel` | verbrauch | ziel | `Verbrauch_2_7_2_status * (1 - Verbrauch_2_7_1_ziel / 100) / (1 - Verbrauch_2_7_1` | `=L79*(1-M78%)/(1-L78%)*M76/L76` | DB='verbrauch_2_7_2_status*(1-verbrauch_2_7_1_ziel/100)/(1-verbrauch_2_7_1_status/10' vs Excel='l79* |
| `V_2.8.0` | verbrauch | status | `Verbrauch_2_6 * Verbrauch_2_8 / 100` | `=L$75*L76%` | DB='verbrauch_2_6*verbrauch_2_8/100' vs Excel='l75*l76%' |
| `V_2.8.0_ziel` | verbrauch | ziel | `Verbrauch_2_6_ziel * Verbrauch_2_8_ziel/ 100` | `=M$75*M76%` | DB='verbrauch_2_6_ziel*verbrauch_2_8_ziel/100' vs Excel='m75*m76%' |
| `V_2.9.0` | verbrauch | status | `Verbrauch_2_6 * Verbrauch_2_9 / 100` | `=L$75*L76%` | DB='verbrauch_2_6*verbrauch_2_9/100' vs Excel='l75*l76%' |
| `V_2.9.0_ziel` | verbrauch | ziel | `Verbrauch_2_6_ziel* Verbrauch_2_9_ziel/100` | `=M$75*M76%` | DB='verbrauch_2_6_ziel*verbrauch_2_9_ziel/100' vs Excel='m75*m76%' |
| `V_2.9.1` | verbrauch | status | `Verbrauch_2_9_2 / (Verbrauch_2_9_0 / 100)` | `=L89/L87%` | DB='verbrauch_2_9_2/(verbrauch_2_9_0/100)' vs Excel='l89/l87%' |
| `V_2.9.1_ziel` | verbrauch | ziel | `Verbrauch_2_9_2_ziel / Verbrauch_2_9_0_ziel *100` | `=M89/M87%` | DB='verbrauch_2_9_2_ziel/verbrauch_2_9_0_ziel*100' vs Excel='m89/m87%' |
| `V_2.9_ziel` | verbrauch | ziel | `100 - Verbrauch_2_7_ziel - Verbrauch_2_7_3_ziel*Verbrauch_2_7 / 100 - Verbrauch_` | `=100-M76-M80*M76%-M83` | DB='100-verbrauch_2_7_ziel-verbrauch_2_7_3_ziel*verbrauch_2_7/100-verbrauch_2_8_ziel' vs Excel='100- |
| `V_3.4.0` | verbrauch | status | `Verbrauch_3_3 * Verbrauch_3_4 / 100` | `=L$75*L76%` | DB='verbrauch_3_3*verbrauch_3_4/100' vs Excel='l75*l76%' |
| `V_3.4.0_ziel` | verbrauch | ziel | `Verbrauch_3_3_ziel * Verbrauch_3_4_ziel / 100` | `=M$75*M76%` | DB='verbrauch_3_3_ziel*verbrauch_3_4_ziel/100' vs Excel='m75*m76%' |
| `V_3.4.2` | verbrauch | status | `Verbrauch_3_4 * (1 - Verbrauch_3_4_1 / 100)` | `=L76*(1-L78%)` | DB='verbrauch_3_4*(1-verbrauch_3_4_1/100)' vs Excel='l76*(1-l78%)' |
| `V_3.4.2_ziel` | verbrauch | ziel | `Verbrauch_3_4_2_status * (1 - Verbrauch_3_4_1_ziel/100) / (1 - Verbrauch_3_4_1_s` | `=L79*(1-M78%)/(1-L78%)*M76/L76` | DB='verbrauch_3_4_2_status*(1-verbrauch_3_4_1_ziel/100)/(1-verbrauch_3_4_1_status/10' vs Excel='l79* |
| `V_3.5.0` | verbrauch | status | `Verbrauch_3_3 * Verbrauch_3_5 / 100` | `=L$75*L76%` | DB='verbrauch_3_3*verbrauch_3_5/100' vs Excel='l75*l76%' |
| `V_3.5.0_ziel` | verbrauch | ziel | `Verbrauch_3_3_Ziel * Verbrauch_3_5_Ziel / 100` | `=M$75*M76%` | DB='verbrauch_3_3_ziel*verbrauch_3_5_ziel/100' vs Excel='m75*m76%' |
| `V_3.6` | verbrauch | status | `100 - Verbrauch_3_4_status - Verbrauch_3_5_status - Verbrauch_3_4_3_status * Ver` | `=100-L108-L115-L112` | DB='100-verbrauch_3_4_status-verbrauch_3_5_status-verbrauch_3_4_3_status*verbrauch_3' vs Excel='100- |
| `V_3.6.0` | verbrauch | status | `Verbrauch_3_3 * Verbrauch_3_6 / 100` | `=L$75*L76%` | DB='verbrauch_3_3*verbrauch_3_6/100' vs Excel='l75*l76%' |
| `V_3.6.0_ziel` | verbrauch | ziel | `Verbrauch_3_3_ziel * Verbrauch_3_6_ziel / 100` | `=M$75*M76%` | DB='verbrauch_3_3_ziel*verbrauch_3_6_ziel/100' vs Excel='m75*m76%' |
| `V_3.6_ziel` | verbrauch | ziel | `100 - Verbrauch_3_4_ziel - Verbrauch_3_5_ziel - Verbrauch_3_4_3_ziel * Verbrauch` | `=100-M108-M115-M112*M108%` | DB='100-verbrauch_3_4_ziel-verbrauch_3_5_ziel-verbrauch_3_4_3_ziel*verbrauch_3_4_zie' vs Excel='100- |
| `V_4.1.1.13` | verbrauch | status | `Verbrauch_4_1_1_11 * Verbrauch_4_1_1_12 / 100` | `=L138*L139%` | DB='verbrauch_4_1_1_11*verbrauch_4_1_1_12/100' vs Excel='l138*l139%' |
| `V_4.1.1.13_ziel` | verbrauch | ziel | `Verbrauch_4_1_1_11_ziel * Verbrauch_4_1_1_12_ziel / 100` | `=M138*M139%` | DB='verbrauch_4_1_1_11_ziel*verbrauch_4_1_1_12_ziel/100' vs Excel='m138*m139%' |
| `V_4.1.1.18_ziel` | verbrauch | ziel | `Verbrauch_4_1_1_16_ziel * Verbrauch_4_1_1_17_ziel / 100` | `=M144*M145%` | DB='verbrauch_4_1_1_16_ziel*verbrauch_4_1_1_17_ziel/100' vs Excel='m144*m145%' |
| `V_4.1.1.2` | verbrauch | status | `Verbrauch_4_1_0 * Verbrauch_4_1_1 / 100 * Verbrauch_4_1_1_1 / 100` | `=L124*L125%*L126%` | DB='verbrauch_4_1_0*verbrauch_4_1_1/100*verbrauch_4_1_1_1/100' vs Excel='l124*l125%*l126%' |
| `V_4.1.1.2_ziel` | verbrauch | ziel | `Verbrauch_4_1_0_ziel * Verbrauch_4_1_1_ziel / 100 * Verbrauch_4_1_1_1_ziel / 100` | `=M124*M125%*M126%` | DB='verbrauch_4_1_0_ziel*verbrauch_4_1_1_ziel/100*verbrauch_4_1_1_1_ziel/100' vs Excel='m124*m125%*m |
| `V_4.1.1.3` | verbrauch | status | `Verbrauch_4_1_1_6 * Verbrauch_4_1_1_7 / 100  + Verbrauch_4_1_1_11 * Verbrauch_4_` | `=L132*L133%+L138*L139%` | DB='verbrauch_4_1_1_6*verbrauch_4_1_1_7/100+verbrauch_4_1_1_11*verbrauch_4_1_1_12/10' vs Excel='l132 |
| `V_4.1.1.3_ziel` | verbrauch | ziel | `Verbrauch_4_1_1_6_ziel * Verbrauch_4_1_1_7_ziel/100 + Verbrauch_4_1_1_11_ziel * ` | `=M132*M133%+M138*M139%+M144*M145%` | DB='verbrauch_4_1_1_6_ziel*verbrauch_4_1_1_7_ziel/100+verbrauch_4_1_1_11_ziel*verbra' vs Excel='m132 |
| `V_4.1.1.4.0` | verbrauch | status | `Verbrauch_4_1_1_2 * Verbrauch_4_1_1_3 / 100` | `=L127*L128%` | DB='verbrauch_4_1_1_2*verbrauch_4_1_1_3/100' vs Excel='l127*l128%' |
| `V_4.1.1.8` | verbrauch | status | `Verbrauch_4_1_1_6 * Verbrauch_4_1_1_7 / 100` | `=L132*L133%` | DB='verbrauch_4_1_1_6*verbrauch_4_1_1_7/100' vs Excel='l132*l133%' |
| `V_4.1.1.8_ziel` | verbrauch | ziel | `Verbrauch_4_1_1_6_ziel * Verbrauch_4_1_1_7_ziel / 100` | `=M132*M133%` | DB='verbrauch_4_1_1_6_ziel*verbrauch_4_1_1_7_ziel/100' vs Excel='m132*m133%' |
| `V_4.1.1.9` | verbrauch | status | `Verbrauch_4_1_1_8 / Verbrauch_4_1_1_3 *100` | `=L134/L128%` | DB='verbrauch_4_1_1_8/verbrauch_4_1_1_3*100' vs Excel='l134/l128%' |
| `V_4.1.1.9_ziel` | verbrauch | ziel | `Verbrauch_4_1_1_8_ziel / Verbrauch_4_1_1_3_ziel *100` | `=M134/M128%` | DB='verbrauch_4_1_1_8_ziel/verbrauch_4_1_1_3_ziel*100' vs Excel='m134/m128%' |
| `V_4.1.2.13` | verbrauch | status | `Verbrauch_4_1_2_11 * Verbrauch_4_1_2_12 / 100` | `=L163*L164%` | DB='verbrauch_4_1_2_11*verbrauch_4_1_2_12/100' vs Excel='l163*l164%' |
| `V_4.1.2.13_ziel` | verbrauch | ziel | `Verbrauch_4_1_2_11_ziel * Verbrauch_4_1_2_12_ziel / 100` | `=M163*M164%` | DB='verbrauch_4_1_2_11_ziel*verbrauch_4_1_2_12_ziel/100' vs Excel='m163*m164%' |
| `V_4.1.2.18_ziel` | verbrauch | ziel | `Verbrauch_4_1_2_16_ziel * Verbrauch_4_1_2_17_ziel / 100` | `=M169*M170%` | DB='verbrauch_4_1_2_16_ziel*verbrauch_4_1_2_17_ziel/100' vs Excel='m169*m170%' |
| `V_4.1.2.2` | verbrauch | status | `Verbrauch_4_1_0*Verbrauch_4_1_2 / 100*Verbrauch_4_1_2_1 / 100` | `=L124*L150%*L151%` | DB='verbrauch_4_1_0*verbrauch_4_1_2/100*verbrauch_4_1_2_1/100' vs Excel='l124*l150%*l151%' |
| `V_4.1.2.2_ziel` | verbrauch | ziel | `Verbrauch_4_1_2_1_ziel / 100 * Verbrauch_4_1_2_ziel / 100 * Verbrauch_4_1_0_ziel` | `=M124*M150%*M151%` | DB='verbrauch_4_1_2_1_ziel/100*verbrauch_4_1_2_ziel/100*verbrauch_4_1_0_ziel' vs Excel='m124*m150%*m |
| `V_4.1.2.3` | verbrauch | status | `Verbrauch_4_1_2_6 * Verbrauch_4_1_2_7 / 100 + Verbrauch_4_1_2_11 * Verbrauch_4_1` | `=L132*L133%+L138*L139%` | DB='verbrauch_4_1_2_6*verbrauch_4_1_2_7/100+verbrauch_4_1_2_11*verbrauch_4_1_2_12/10' vs Excel='l132 |
| `V_4.1.2.3_ziel` | verbrauch | ziel | `Verbrauch_4_1_2_6_ziel * Verbrauch_4_1_2_7_ziel / 100 + Verbrauch_4_1_2_11_ziel ` | `=M132*M133%+M138*M139%+M144*M145%` | DB='verbrauch_4_1_2_6_ziel*verbrauch_4_1_2_7_ziel/100+verbrauch_4_1_2_11_ziel*verbra' vs Excel='m132 |
| `V_4.1.2.4.0` | verbrauch | status | `Verbrauch_4_1_2_2 * Verbrauch_4_1_2_3 / 100` | `=L152*L153%` | DB='verbrauch_4_1_2_2*verbrauch_4_1_2_3/100' vs Excel='l152*l153%' |
| `V_4.1.2.8` | verbrauch | status | `Verbrauch_4_1_2_6 * Verbrauch_4_1_2_7 / 100` | `=L157*L158%` | DB='verbrauch_4_1_2_6*verbrauch_4_1_2_7/100' vs Excel='l157*l158%' |
| `V_4.1.2.8_ziel` | verbrauch | ziel | `Verbrauch_4_1_2_6_ziel * Verbrauch_4_1_2_7_ziel / 100` | `=M157*M158%` | DB='verbrauch_4_1_2_6_ziel*verbrauch_4_1_2_7_ziel/100' vs Excel='m157*m158%' |
| `V_4.1.2.9` | verbrauch | status | `Verbrauch_4_1_2_8 / Verbrauch_4_1_2_3 * 100` | `=L159/L153%` | DB='verbrauch_4_1_2_8/verbrauch_4_1_2_3*100' vs Excel='l159/l153%' |
| `V_4.1.2.9_ziel` | verbrauch | ziel | `Verbrauch_4_1_2_8_zeil / Verbrauch_4_1_2_3_zeil * 100` | `=M159/M153%` | DB='verbrauch_4_1_2_8_zeil/verbrauch_4_1_2_3_zeil*100' vs Excel='m159/m153%' |
| `V_5.2` | verbrauch | status | `Verbrauch_5_0 * Verbrauch_5_1 / 100` | `=L176*L177%` | DB='verbrauch_5_0*verbrauch_5_1/100' vs Excel='l176*l177%' |
| `V_5.2.2` | verbrauch | status | `Verbrauch_5_2 * Verbrauch_5_2_1 / 100` | `=L178*L179%` | DB='verbrauch_5_2*verbrauch_5_2_1/100' vs Excel='l178*l179%' |
| `V_5.2.2_ziel` | verbrauch | ziel | `Verbrauch_5_2_ziel * Verbrauch_5_2_1_ziel / 100` | `=M178*M179%` | DB='verbrauch_5_2_ziel*verbrauch_5_2_1_ziel/100' vs Excel='m178*m179%' |
| `V_5.2_ziel` | verbrauch | ziel | `Verbrauch_5_0_ziel * Verbrauch_5_1_ziel / 100` | `=M176*M177%` | DB='verbrauch_5_0_ziel*verbrauch_5_1_ziel/100' vs Excel='m176*m177%' |
| `V_6.1_ziel` | verbrauch | ziel | `Verbrauch_6_1_1_ziel + Verbrauch_6_1_2_ziel + Verbrauch_6_1_3_ziel` | `=SUM(M184:M186)` | DB='verbrauch_6_1_1_ziel+verbrauch_6_1_2_ziel+verbrauch_6_1_3_ziel' vs Excel='sum(m184:m186)' |
| `V_6.2` | verbrauch | status | `Verbrauch_4_1_1_10 + Verbrauch_4_1_2_10` | `=AF16` | DB='verbrauch_4_1_1_10+verbrauch_4_1_2_10' vs Excel='af16' |
| `V_6.2_ziel` | verbrauch | ziel | `Verbrauch_4_1_1_10_ziel + Verbrauch_4_1_2_10_ziel` | `=L16*M$10/L$10` | DB='verbrauch_4_1_1_10_ziel+verbrauch_4_1_2_10_ziel' vs Excel='l16*m10/l10' |
| `V_8` | verbrauch | status | `Verbrauch_6_0 + Verbrauch_3_7 + Verbrauch_2_10 + Verbrauch_1_4` | `=L191` | DB='verbrauch_6_0+verbrauch_3_7+verbrauch_2_10+verbrauch_1_4' vs Excel='l191' |
| `V_8_ziel` | verbrauch | ziel | `Verbrauch_6_0_ziel + Verbrauch_3_7_ziel + Verbrauch_2_10_ziel + Verbrauch_1_4_zi` | `=M191` | DB='verbrauch_6_0_ziel+verbrauch_3_7_ziel+verbrauch_2_10_ziel+verbrauch_1_4_ziel' vs Excel='m191' |
| `V_9.1.2_ziel` | verbrauch | ziel | `Verbrauch_9_1_ziel * Verbrauch_9_1_1_ziel / 100 * Population / 1000` | `=M194*M195%*'3. Bedarfsniveau'!M10/1000000` | DB='verbrauch_9_1_ziel*verbrauch_9_1_1_ziel/100*population/1000' vs Excel="m194*m195%*'3.bedarfsnive |
| `V_9.1.4` | verbrauch | status | `Verbrauch_9_1_2 * Verbrauch_9_1_3 / 100` | `=L196*L197%` | DB='verbrauch_9_1_2*verbrauch_9_1_3/100' vs Excel='l196*l197%' |
| `V_9.1.4_ziel` | verbrauch | ziel | `Verbrauch_9_1_2_ziel * Verbrauch_9_1_3_ziel / 100` | `=M196*M197%` | DB='verbrauch_9_1_2_ziel*verbrauch_9_1_3_ziel/100' vs Excel='m196*m197%' |
| `WS_ABREGELUNG_THRESHOLD` | ws_constant | status | `0.65` | `=IF(O32="",D79,O32)/100` | DB='0.65' vs Excel='if(o32="",d79,o32)/100' |
| `WS_ETA_GAS_STROM` | ws_constant | status | `0.585` | `=IF(T33="",D82,T33)/100` | DB='0.585' vs Excel='if(t33="",d82,t33)/100' |
| `WS_ETA_STROM_GAS` | ws_constant | status | `0.65` | `=IF(O33="",D80,O33)/100` | DB='0.65' vs Excel='if(o33="",d80,o33)/100' |
