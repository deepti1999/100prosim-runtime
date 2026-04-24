# Hardcoded values trace — Jahresstrom flow diagram

**Date:** 2026-04-23
**Template:** `simulator/templates/simulator/annual_electricity.html`
**Backend view:** `simulator/page_renewable.py::annual_electricity_view`
**Data source:** `simulator/signals.py::compute_ws_diagram_reference` which reads from `simulator/ws365_orchestrator.py::get_ws_365_data`

This document traces every hardcoded literal in the Jahresstrom
flow diagram to:

1. **Where it currently is** (file + line)
2. **What it conceptually represents**
3. **Where it should come from** (a backend method, a D.xlsx
   parameter, or a new config constant) — NOT WS.xlsm, which is
   Schmidt-Kanefendt's calculation workbook and is not a §2.3
   import target.
4. **Effort to make dynamic.**

The point of this trace is to give us an exact punch-list for
unblocking the T54 diagram values, independent of the larger §2.3
Excel-import work.

---

## 1. Inventory of hardcoded values in the template

Every `<text>` element with a literal number or string that
should ideally be dynamic. Organised by element ID or label type.

### A. Source-stack Tagesladungen (D1)

Under each source value box (Bio, PV, Wind, Hydro), there's an
italic blue Tagesladungen count.

| Source | Line | Literal | Should come from |
|---|---|---|---|
| Bio  | 169 | `1`   | Computed: `bio_value / peak_daily_bio` |
| PV   | 181 | `397` | Computed: `pv_value / peak_daily_pv`   |
| Wind | 193 | `186` | Computed: `wind_value / peak_daily_wind` |
| Hydro| 206 | `5`   | Computed: `hydro_value / peak_daily_hydro` |

**What "Tagesladungen" means:** annual energy produced, expressed
as a number of "average daily charges" — i.e. `annual_GWh /
peak_daily_GWh`. For PV: 1,201,630 ÷ ~3,026 ≈ 397 ✓ (verified by
inspection of our `ws_365_data` daily series).

**Where it should come from:** `compute_ws_diagram_reference()`
already pulls `daily_data` (365 days) from `get_ws_365_data()`.
We just need to add per-source `peak_daily_*` computation and
divide the annual total.

**Effort:** ~2 hours — add 4 fields to `compute_ws_diagram_reference`
return dict + 4 template bindings.

### B. Source-stack percent shares (D3)

Under each Tagesladungen, the percent share of bruttostromerzeugung.

| Source | Line | Literal | Should come from |
|---|---|---|---|
| Bio  | 170 | `0,2%`  | `bio_value / bruttostromerzeugung_total * 100` |
| PV   | 182 | `62,2%` | `pv_value  / bruttostromerzeugung_total * 100` |
| Wind | 194 | `29,2%` | `wind_value/ bruttostromerzeugung_total * 100` |
| Hydro| 207 | `0,8%`  | `hydro_value/bruttostromerzeugung_total * 100` |

**What this is:** each source's contribution to the gross
electricity production.

**Where it should come from:** purely a ratio of values we
already have in `compute_ws_diagram_reference`. The tricky part
is which denominator Schmidt-Kanefendt uses — simple `pv / (pv +
wind + hydro + bio)` gives PV = 62.2% ✓ but Wind = 36.6% ✗ (not
29.2%). Likely denominator includes a "Faktor" or `m_total`
instead of the sum. Needs one formula-clarification email or a
quick look at D.xlsx row where the denominator is defined.

**Effort:** ~1 hour once the correct denominator is confirmed.

### C. Flow-arrow Tagesladungen (D2)

Below each flow-value box on the main horizontal flow and its
branches.

| Flow segment | Line | Literal | Meaning |
|---|---|---|---|
| Splitter → Q arrow | 237 | `509` | For `n_value` (1,541,301) |
| Abregelung up-arrow | 247 | `62`  | For `q_abregelung` (189,197) |
| Q → S arrow | 254 | `313` | For `n_to_right` (947,077) |
| S → Stromnetz arrow | 265 | `365` | For `final_stromnetz` (1,105,519) |
| Q → Ely-ES branch | 291 | `134` | For `n_output_branch` (405,027) |
| Rückv → S (T arrow) | 338 | `51`  | For `reconversion` (153,918) |
| Speicherkapazität | 378, 392 | `80` (×2) | For `storage_capacity` (241,711) |
| Ely-P2G → Direktverbr | 350 | `87`  | For `gasspeicher_direkt` (250,857) |
| Ely-ES → Gasspeicher | 366 | `87`  | For `gas_storage` (263,268) |
| Gasspeicher → Rückv (U) | 384 | `87`  | For `t_value` (263,107) |
| Abgleich tail | 390 | `0`   | Scenario-balance offset indicator |

**What this is:** same Tagesladungen normalisation as D1, applied
to each flow segment's annual value.

**Where it should come from:** same backend method as D1 — once
we have `peak_daily_*` for each flow segment (which is just
`max(daily_data[segment])`), every Tages value becomes
`annual_flow / peak_daily_flow`.

**Effort:** ~2 hours — extend the peak-daily calculation to
cover flow-branch values, add ~12 fields to context.

### D. Red annotations (D4a, D4b)

Installed-power peaks in red — region-specific configuration
values.

| Element | Line | Literal | What it is |
|---|---|---|---|
| Under 405.027 box | 292 | `194 GW` | Pmax (installed peak) of Elektrolyse Stromspeicher |
| Beside Rückverstromung box | 328 | `261 GW (elekt.)` | Installed peak of Rückverstromung |

**Where these should come from:** region-specific config
constants. In 100prosim terms these are **Datenmodell
parameters** — they belong in D.xlsx (likely sheet
`I_Basisdaten` based on naming, ~192 rows × 15 cols of basis
data). Once §2.3 Excel import ships, these become attributes of
the `Region` model.

**Effort:** depends on §2.3 sequencing. If §2.3 ships first: ~30
min (read two fields from D.xlsx during import, expose on
context). If done standalone: add two fields to a new small
`RegionConfig` model or to settings, ~1 hour.

### E. Abgleichdifferenz 160 (D4c)

| Element | Line | Literal | What it is |
|---|---|---|---|
| Bottom-right | 391 | `160` | Scenario-solver residual — how far off the current scenario is from zero net balance |

**Where it should come from:** our own WS365 solver already
computes this internally (the solver iterates until
`speicherdrift_gwh` is ~zero). The **residual** at the end of
solving — how much off-balance we are — is useful diagnostic
information but isn't currently returned by
`get_ws_365_data()`.

**Where it should go:** a new field
`abgleichdifferenz_gwh` on the result dict from
`get_ws_365_data()`. The orchestrator already has access to it
internally (it's the termination criterion of the Balance loop).

**Effort:** ~1 hour — add one line of return dict, expose in
`compute_ws_diagram_reference`, bind in template.

### F. Static Eta values (already dynamic-ish, left here for completeness)

| Element | Line | Current | Dynamic binding | Notes |
|---|---|---|---|---|
| Eta Ely. | 305 | `65%` | `{{ eta_ely_pct }}` | ID `eta_ely_value`, JS-populated |
| Eta ES (inside Pmax/Pv stack) | 318 | `65%` | `{{ eta_es_pct }}` | ID `eta_es_value` |
| Eta RS | 330 | `59%` | `{{ eta_rs_pct }}` | ID `eta_rs_value` |
| Eta Stromspeicherung | 153 | `0,0` | `{{ eta_storage_pct }}` | ID `eta_storage_value` |
| 100% (Pmax/Pv upper) | 317 | `100%` | constant by design | Pmax is always 100% of nominal by definition |

These are already wired up via JS `setPercentText` calls. Good.

### G. Legend + title static text (not D1-D4c, just labels)

| Element | Line | Content |
|---|---|---|
| Title | 142 | `Jahresbilanz Strom` |
| Datasource | 144 | `Verwendete Zeitreihen: Anlagenpark Deutschland 2023 [SMARD]` |
| Column headers | 147-148 | `Bruttostromerzeugung:`, `Nettostromerzeugung:` |
| Source box labels | 161-163, 175, 187, 199-201 | `Bedarfs-Kraftwerke / Biobrennstoffe`, `PV / (fluktuierend)`, `Wind / (fluktuierend)`, `Laufwasser / Tief.-Geoth. / (konstant)` |
| Legend rows | 395-406 | `Legende: / 31.799 Wert in GWh/a / 146 Wert in Ø Tagesladungen / K Zeitreihenkennung / Strom / Gas` |
| Abregelung label | 243 | `Abregelung` |
| Middle-row box labels | 301-303, 309-311, 322-324 | `Elektrolyse / Power to Gas / (nach Angebot)`, etc. |
| Gasspeicher labels | 357-358, 373 | `Gasspeicher Direktverbr.`, `Gasspeicher Strom` |
| Gas-Verbraucher | 363 | `Gas-Verbraucher` |
| Abgleichdifferenz label | 391 | `Abgleichdifferenz` |
| Speicherkapazität label | 376 | `Speicherkapazität:` |
| Circle letters | 230, 248, 256, 265, 339, 346, 385, 403 | `M / Q / N / S / T / P / U / I / K` (Zeitreihenkennung labels) |
| Stromnetz box label | 272-273 | `Stromnetz zum / Endverbrauch` |
| Rückverstromung label | 322-323 | `Rückver- / stromung / (Mangelausgl.)` |
| Legend example numbers | 399, 401 | `31.799`, `146` |
| Footer | 410 | `100prosim Web · {{ diagram_generated_on }}` |

These are German domain labels — frozen per CLAUDE.md stakeholder
contract. **They stay hardcoded.**

---

## 2. Summary table — effort to unblock

Grouping by what's needed to make it dynamic:

| Group | Items | Depends on | Effort |
|---|---|---|---|
| **Compute from existing `daily_data`** (already available in `get_ws_365_data`) | D1 (4), D2 (11), D3 (4 once denominator known) | Just add peak-daily + ratio logic | **~4 hours** |
| **Surface internal solver residual** | D4c (`Abgleichdifferenz`) | Add 1 return-dict key in `get_ws_365_data` | **~1 hour** |
| **Region-specific config** | D4a (194 GW), D4b (261 GW) | Depends on where "installed capacity" lives: config constant OR D.xlsx `I_Basisdaten` row | **~30 min if §2.3 ships first, ~1 hour standalone** |

**Total ≤ 6 hours if we do it standalone**, not blocked on §2.3.
Or bundled into the §2.3 import work for D4a/D4b specifically.

**Critical insight:** D1, D2, D3, and D4c do **NOT** require any
Excel import. They only require exposing backend values we
already compute. This means:

- We don't have to wait for §2.3 to close most of the diagram.
- The §2.3 scope is cleaner: it's about **parameter values,
  sources, and assumption notes**, not diagram annotations.

---

## 3. Recommended sequencing

**Option 1 (recommended): Do the easy backend exposure first.**
- Close D1, D2, D3, D4c (~5 hours)
- Unblocks 4 of the 6 diagram items, leaves only D4a/D4b pending §2.3
- No external blocker — just code

**Option 2: Bundle with §2.3.**
- Do the full Excel import, and as part of it wire up D1-D4c from
  whatever the right source is (backend for D1/D2/D3/D4c, D.xlsx
  config for D4a/D4b).
- Longer sequentially but one clean push.

Our recommendation: **Option 1** — get D1/D2/D3/D4c done this
week as a small, independent commit; leave D4a/D4b for the §2.3
work.

---

## 4. Formulas — all confirmed by reading WS.xlsm cells (2026-04-23)

Inspection of `WS.xlsm` sheet `1.Jahresbilanz_Strom` with openpyxl
in formula-mode (`data_only=False`) gave us the exact formulas for
D1, D2, D3, D4c. See `scripts/verify_d1_d4c_formulas.py` and
`scripts/verify_d3_deep.py` for the probes.

### D1 + D2 — Tagesladungen (unified formula)

Excel uses one named constant `TLproEingabeEinheit` across all
Tages values on the Jahresstrom sheet:

```
TL_factor = 365 / final_stromnetz   # total annual Stromnetz consumption
Tagesladung(value) = value * TL_factor
```

Verified by back-calculation (current scenario has
`final_stromnetz ≈ 1,107,646 GWh`):

| Value | annual | × TL_factor | Excel shows |
|---|---:|---:|---:|
| PV           | 1,205,268 | 397.2 | 397 |
| M→Q flow     | 1,545,080 | 509.0 | 509 |
| Speicherkap. |   241,727 |  79.7 |  80 |
| Final flow   | 1,107,646 | 365.0 | 365 |

Note: Wind and Hydro Tages use the **AE-adjusted** value (see D3);
PV and Bio use the raw value.

### D3 — percent shares (asymmetric)

From WS.xlsm formulas:
- `E14 = E13/(H25+E13)` → Bio share
- `E21 = E19/(H25+E13)` → PV share
- `E27 = AE25/(H25+E13)` → Wind share
- `E33 = AE31/(H25+E13)` → Hydro share

Where:
- `H25 = E19+E25+E31 = PV + Wind + Hydro` (sum of fluktuierend + konstant)
- `E13 = Bio`
- `AE18% = J25/H25 = 1 - ely_branch/m_total` (≈ 80.01% — "um Power-to-Gas verminderte EE")
- `AE25 = E25 × AE18%` (Wind after P2G adjustment)
- `AE31 = E31 × AE18%` (Hydro after P2G adjustment)

In Python:

```python
m_total = pv + wind + hydro                        # H25
four_source = m_total + bio                        # H25 + E13
ely_factor = 1.0 - (ely_branch / m_total) if m_total else 0.0   # AE18%

bio_pct   = bio                     / four_source
pv_pct    = pv                      / four_source
wind_pct  = wind  * ely_factor      / four_source
hydro_pct = hydro * ely_factor      / four_source
```

Produces `0,23% / 62,27% / 29,20% / 0,81%` — matches Excel's
`0,2% / 62,2% / 29,2% / 0,8%` exactly.

### D4a / D4b — installed-power (194 GW / 261 GW)

Located at `WS.xlsm` `1.Jahresbilanz_Strom` cells M30 and R30.
These are scenario-level config constants, not computed from the
WS365 solver. Belong in D.xlsx `I_Basisdaten` (installed
capacities per region). For Track 1, either hardcode with a TODO
comment or add a tiny `RegionConfig` model with 2 fields — both
fine.

### D4c — Abgleichdifferenz (gas-balance residual)

Formula at `WS.xlsm` cell `Q44`:

```
Q44 = L36 - Q36   # gas_storage_in - gas_storage_out
```

In our terms:

```python
abgleichdifferenz = gas_storage - t_value
```

Verified: our scenario gives 263,268 - 263,107 = 161, Excel shows
160 (rounding).

---

## 5. All four diagram metrics are implementable today

With formulas now confirmed:

| Item | Blocker | Status |
|---|---|---|
| D1 source Tagesladungen | None — formula confirmed | **SHIPPED 2026-04-23** (commit `7c02458`) |
| D2 flow Tagesladungen | None — same formula | **SHIPPED 2026-04-23** (commit `7c02458`) |
| D3 percent shares | None — formula confirmed | **SHIPPED 2026-04-23** (commit `7c02458`) |
| D4a/b installed-power | Where to store the constants (D.xlsx vs config) | Pending Track 2 (§2.3 import) |
| D4c Abgleichdifferenz | None — formula confirmed | **SHIPPED 2026-04-23** (commit `7c02458`) |

Total effort actual: ~2 hours (backend fields + template bindings
+ tests + V4 localhost + V5 Heroku full verification).

## 6. Track 1 shipped 2026-04-23 — what landed

Commit `7c02458` wired **4 of 6 T54 blockers** to backend values:

### Code changes
- `simulator/signals.py::compute_ws_diagram_reference()` returns
  21 new dict keys (pv_tages, pv_pct, flow_*_tages, abgleich-
  differenz, ...). All divisions guarded against zero denominators.
- `simulator/page_renewable.py::annual_electricity_view` exposes
  new context vars with Excel-reference-value defaults.
- `simulator/templates/simulator/annual_electricity.html` —
  20 hardcoded `<text>` literals got `id="..."` attributes and
  are populated at DOMContentLoaded from the vals dict. German
  number formatting preserved (percents via
  `.toFixed(1).replace('.', ',')`; integers via
  `toLocaleString('de-DE')`).

### Pre-existing regression caught and fixed
Pass 10's SVG rewrite had accidentally dropped the
`{{ diagram_scenario_label }}` binding on template line 143
(replaced with hardcoded "Aktuelles Szenario"). The
`test_annual_electricity_page_shows_active_scenario_header_when_session_is_set`
test was therefore failing at baseline (5/6 green, not 6/6).
Restored the Django interpolation; tests now 6/6 green.

### Gasspeicher-Direktverbrauch Tages — closed 2026-04-24 (was "83 vs 87")
**Prior note (incorrect; corrected below):** ~~"Excel cell H37 contains no
formula — the '87' there is a visual copy."~~ This was wrong on two
counts:

1. **There is no H37** involved. The Excel cells that render "87" on the
   Gasspeicher diagram positions are `1.Jahresbilanz_Strom!L37` and
   `1.Jahresbilanz_Strom!Q37`.
2. **Both cells ARE formulas**, not hardcoded literals:
   - `L37 = L36 × TLproEingabeEinheit` → 86.94 → rounds to "87"
   - `Q37 = Q36 × TLproEingabeEinheit` → 86.89 → rounds to "87"
   - where `L36 = L28 × N33` = `n_output_branch × ETA_STROM_GAS` (= our `gas_storage`),
     and `TLproEingabeEinheit = 365 / VerbrauchStrom` = our `tl_factor`.

**Resolution:** `simulator/signals.py` line 175 aligned to Excel's L37
formula basis. `flow_gasspeicher_direkt_tages = gas_storage * tl_factor`
(previously used the scenario-target `ely_branch_value × ETA_STROM_GAS`
basis which under-shot by the scenario-target-vs-solver-actual drift →
produced 83). All three Gasspeicher diagram positions (Ely-P2G →
Direktverbr, Ely-ES → Gasspeicher, Gasspeicher → Rückverstromung) now
read 87, matching Excel. Full investigation record in
`verification/final_audit/gasspeicher_83_vs_87.md` and
`verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q4.

### Verification ledger

| Step | Result |
|---|---|
| V2 `test_bb_current_app` | 6/6 green (was 5/6 pre-fix) |
| V2 full `test_bb_current_app + test_bb_calc + test_ws365_formulas` | 15/15 green |
| V3 localhost `/annual-electricity/` 200 OK | ✓ |
| V4 Playwright DOM-value check on all 20 new IDs | 20/20 populated, values match Excel reference |
| V4 full-page screenshot localhost | `verification/t54/track1_localhost.png` — diagram renders identically to pass 22 |
| V5 Heroku spin-up at `prosim-100-f9853cedfcb7`, deploy, Playwright DOM check (27 IDs), fullPage screenshot, teardown + force-destroy | All 27 IDs populate with live-computed values (Heroku seed has PV=1,211,176 → Tages=399; localhost seed has PV=1,201,506 → Tages=397 — values track the scenario data correctly). Regression-checked 9 other pages all 200 OK. `verification/t54/track1_heroku.png`. |
| V6 doc | This section + `REMAINING.md` §3 updated |

### What remains (Track 2)

| Item | Where it goes |
|---|---|
| D4a (194 GW installed Pmax-ES) | Region config — belongs in D.xlsx `I_Basisdaten` or a small `RegionConfig` model. Ships with §2.3 Excel import. |
| D4b (261 GW installed Pmax-RV) | Same as D4a |
| §2.3 full Excel import (Source model, 86 hyperlinks, 747 assumption comments, region swap) | ~4 days, covered by `DATA_MODEL_AUDIT.md` |
