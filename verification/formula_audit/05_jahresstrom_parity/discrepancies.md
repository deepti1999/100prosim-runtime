# §6 Jahresstrom Parity — node-by-node

| verdict | our_value | excel_scaled | drift | key | cell | description |
|---------|-----------|--------------|-------|-----|------|-------------|
| PASS_LOOSE (<1%) | 1211176.171964698 | 1205268.2357095385 | 0.0049 | pv_value | E19 | PV value (Solarstrom) |
| PASS_LOOSE (<1%) | 399.1159421930409 | 396.9713027743458 | 0.0054 | pv_tages | E20 | PV Tagesladungen |
| PASS_LOOSE (<1%) | 62.38577500983147 | 62.270424236887024 | 0.0018 | pv_pct | E21 | PV % share (× 100) |
| PASS_COSMETIC | 706236.3411426758 | 706236.586259135 | 0.0000 | wind_value | E25 | Wind value |
| PASS_LOOSE (<1%) | 186.35341930662545 | 186.1192117194711 | 0.0013 | wind_tages | E26 | Wind Tagesladungen |
| PASS_LOOSE (<1%) | 29.12888526901502 | 29.19536548714837 | 0.0023 | wind_pct | E27 | Wind % share (× 100) |
| PASS | 19492.5192579 | 19509.000000000004 | 0.0008 | hydro_value | E31 | Hydro/Laufwasser value |
| PASS | 5.143458928681869 | 5.141336164228204 | 0.0004 | hydro_tages | E32 | Hydro Tagesladungen |
| PASS_LOOSE (<1%) | 0.803973576534951 | 0.8064894914404618 | 0.0031 | hydro_pct | E33 | Hydro % share (× 100) |
| EXACT | 4525.0 | 4525 | 0.0000 | bio_value | E13 | Biomass / Fossile Brennstoffe |
| DRIFT | 1.491112259493947 | 0.0023378502919396554 | 0.9984 | bio_tages | E14 | Bio Tagesladungen |
| DRIFT | 0.2330756156320052 | 0.0 | 1.0000 | bio_pct | E15 | Bio % share |
| PASS_LOOSE (<1%) | 1936905.032365274 | 1931013.8219686735 | 0.0030 | m_total | H25 | Wind+Solar+konstant (M) |
| PASS_COSMETIC | 385933.3286830357 | 385933.813936009 | 0.0000 | ely_branch_value | H28 | Ely branch value (overshoot O) |
| PASS_LOOSE (<1%) | 1550971.7036822382 | 1545080.0080326644 | 0.0038 | n_value | J25 | Stromverbr. J-branch |
| PASS_LOOSE (<1%) | 511.08793845056323 | 508.8928800303481 | 0.0043 | flow_n_value_tages | J26 | J-branch Tagesladungen |
| PASS | 406403.3340795594 | 406108.37619771546 | 0.0007 | n_output_branch | L28 | Einspeich P (= n_output_branch) |
| DRIFT | 195890.29136753705 | 189627.90454725613 | 0.0320 | n_input_branch | L23 | Abregelung input (AbregCopy) |
| DRIFT | 64.55125192795045 | 62.45650061969672 | 0.0325 | flow_q_abregelung_tages | L24 | Abregelung Tagesladungen |
| PASS | 948678.0782351417 | 949343.257555285 | 0.0007 | n_to_right | N25 | Direktverbrauch (N) |
| PASS | 312.6155829325033 | 312.67896934984356 | 0.0002 | flow_n_to_right_tages | N26 | Direktverbr. Tagesladungen |
| PASS | 1107646.315348871 | 1108198.257555285 | 0.0005 | final_stromnetz | S25 | Final Stromnetz (VerbrauchStrom) |
| EXACT | 365.0 | 365 | 0.0000 | flow_final_tages | S26 | Final Tagesladungen (365) |
| PASS_COSMETIC | 250856.6636439732 | 250856.97905840588 | 0.0000 | h2_offer | H36 | H2 offer (=Einspeich sum capacity) |
| PASS | 264162.1671517136 | 263970.44452851504 | 0.0007 | gas_storage | L36 | Gas storage (P sum) |
| PASS_LOOSE (<1%) | 87.04871733357113 | 86.9422159762793 | 0.0012 | flow_gas_storage_tages | L37 | Gas storage Tagesladungen |
| PASS | 264005.53352774266 | 263811.17058561975 | 0.0007 | t_value | Q36 | T value (Ausspeich Rückverstr) |
| PASS_LOOSE (<1%) | 86.99710223590218 | 86.88975696115233 | 0.0012 | flow_t_value_tages | Q37 | T Tagesladungen |
| PASS_LOOSE (<1%) | 242831.11 | 242467 | 0.0015 | storage_capacity | M44 | Speicherkapazität |
| PASS_LOOSE (<1%) | 80.01954588011561 | 79.859767326502 | 0.0020 | flow_storage_capacity_tages | M45 | Speicherkapazität Tages |
| DRIFT | 156.63362397096353 | 159.27394289529184 | 0.0166 | abgleichdifferenz | Q44 | Abgleichdifferenz |
