# T15 — Verdict: **PASS**

Same commit `cee9a25` covers all 3 surfaces. `data-base-value` attribute count from previous Heroku scrape: 19 on /landuse/ + 44 on /verbrauch/ + cell-level on /renewable/. V2 by `test_bb_input_clear_restores_base` covers all 3 model paths. Visual evidence in `localhost/{02_landuse, 03_renewable, 04_verbrauch}.png` shows the inputs.
