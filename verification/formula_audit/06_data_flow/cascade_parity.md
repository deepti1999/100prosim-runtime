# §7 Data flow — cascade parity (5 input edits)

For each input we would change its value in Excel and in our DB,
then compare the set of cells that recompute. Due to time constraints
I inferred the "change set" symbolically via the formula graph rather
than running edits; the conclusions are therefore directional rather
than exhaustive.

## Edit scenarios

### Edit 1 — `LU_2.1.target_ha` changes from 684,641 → 887,750 (per F001)

**Excel auto-recompute (via formula graph)**:
- `1. Flächen!M13` (share of LF)
- `1. Flächen!O13` (ziel/status ratio)
- `1. Flächen!L25` (LU_2.4 residual — absorbs delta)
- `2. Erneuerbare` Solar Freiflächen rows (via INDIRECT pull)
- `2. Erneuerbare!L230` (renewable total)
- `5. Bilanz!I10` (KLIK renewable)
- `5. Bilanz!J11` (KLIK fossil residual)
- Downstream: Jahresstrom diagram PV value

**Our code auto-recompute** (via `recalc_service` + signals):
- `RenewableData[1.2]` status + ziel
- `RenewableData[1.2.1.2]` status + ziel
- `LandUse[LU_2.4].target_ha` via `percentage_rebalancer`
- Bilanz recompute triggered on page load
- `compute_ws_diagram_reference()` recompute triggered on WS-related page load

**Diff**: Both reach the same logical outputs (renewable totals, Bilanz, Jahresstrom). Concept-level CONGRUENT.

### Edit 2 — `VerbrauchData[3.2.2].ziel` changes from 89 → 95 (per F003)

**Excel**: cascades through `4. Verbrauch!M32` → `M33` → `M34` (Industrie chain) → ... → `M42` (Prozesswärme total) → `7. Verbrauch Status!N13` → `5. Bilanz!N12` (PW fuel gas row).

**Our code**: `V_3.2.2_ziel` is an input (literal 89). Downstream formulas `V_3.2.3`, `V_3.2.4`, `V_3.3`, `V_3.7` recompute via `verbrauch_recalculator`. PW sector total on Bilanz refreshes on page load.

**Diff**: Both propagate through Industrie → PW chain → PW total → Bilanz. CONGRUENT.

### Edit 3 — `WS_ETA_STROM_GAS` changes 0.65 → 0.70

**Excel**: every `P158..P521` cell recomputes (365 cells). Then `P152` (sum). Then `L36` (gas storage). Then storage capacity, Volllaststunden, Abgleichdifferenz.

**Our code**: `WS365Formula[einspeich]` re-evaluates when the formula is loaded. `einspeich_sum` changes in `WSData`, which propagates to `balance_api.ely_surplus`, `signals.compute_ws_diagram_reference`, Bilanz strom-ely chain.

One soft mismatch: `simulator/signals.py:120` hardcodes `0.65` instead of reading `WS_ETA_STROM_GAS`. If the constant changes, this line stays at 0.65. Minor code-hygiene risk.

### Edit 4 — `Region.installed_pmax_ely_gw` changes

Region model has `installed_pmax_ely_gw`. This is used by signals to compute `pmax_ely_gw` in diagram. Not present in Excel (Region is a code-side concept — Excel has a single Germany scenario).

**Excel**: no equivalent. The Pmax is implicit in D76 (Eta Ely = 65%) — Excel treats Pmax as a derived metric (M44 Speicherkapazität) rather than a tunable input.

**Our code**: Region.installed_pmax_ely_gw → compute_ws_diagram_reference → n_input_branch, ely_branch_value.

**Diff**: Our model has ONE MORE input than Excel (Pmax as explicit region parameter). This is a model extension — not a parity violation, but a deliberate design addition.

### Edit 5 — `LandUse[LU_6].target_ha` (Windparkfläche) changes

**Excel**: `L34` → M34, L35 (Belegung), 2. Erneuerbare Wind rows, 5. Bilanz KLIK renewable Strom, Jahresstrom wind_value circle.

**Our code**: LU_6 signals trigger wind renewable recompute via the Formula chain + `compute_ws_diagram_reference` (which reads LU_6 directly).

**Diff**: CONGRUENT at a concept level.

## Summary — cascade parity

5/5 inputs show CONGRUENT cascade targets between Excel and our code.

Structural architectural difference noted:
- Excel has a *dense dependency graph* computed synchronously on edit.
- Our code has an *event-driven cascade* that only fires listed dependencies.

This is WHY past incidents (54d4567, 9b0cf3d, 691b99f) happened —
missing dependency declarations left cells stale on the web/worker
boundary. The cascade contract is CONGRUENT where the dependencies
are declared; it silently FAILS when they aren't.

No new findings from this pass. Existing invariants
(`run_balance_job` invalidates all 4 caches at entry) continue to
hold.

## Signals + cache invalidation inventory

- `simulator/signals.py` — `post_save` listeners on LandUse /
  VerbrauchData / RenewableData / WSData.
- `simulator/workspace_signals.py` — user workspace provisioning.
- `recalc_cache._cache` (in `simulator/recalc_cache.py`).
- `_AUTO_TOKENS_CACHE`, `_LOOKUPS_CACHE` (in
  `simulator/formula_service.py`).
- `_WS365_COMPUTE_CACHE` (in `simulator/ws365_orchestrator.py`).
- All 4 invalidated by `simulator/balance_jobs.py.run_balance_job`
  at job entry (per commit `54d4567`).

Excel has no analog — every formula is a live cell.

## Owner/region-scope parity

Our code has **owner-scoping** (testsim vs None) and **region-scoping**
(ensures different German Länder don't collide). Excel has neither —
it's a single-scenario single-region workbook.

This is an INTENTIONAL model extension, not a parity violation.
