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

## 4. Open questions (small)

Only two, both answerable in <1 hour of investigation:

1. **What's the exact denominator for the percent shares (D3)?**
   Our naive `pv / (pv+wind+hydro+bio)` gives PV correctly but
   Wind wrong. Either a Schmidt-Kanefendt one-line answer, or 15
   min of inspecting D.xlsx row 21 of sheet `I_Basisdaten` where
   "Bruttostromerzeugung gesamt" likely lives.
2. **For Tagesladungen (D1/D2), is the denominator "peak daily"
   or "mean daily"?** Our inspection suggests peak (PV: 1.2M /
   3026 ≈ 397). Worth confirming with one data-point check
   against Schmidt-Kanefendt's Excel output.
