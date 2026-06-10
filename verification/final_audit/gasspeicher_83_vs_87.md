# T54 caveat investigation — Gasspeicher Direktverbr Tages: 83 vs 87

**Date:** 2026-04-24
**Investigator:** Claude (Fix 4 of the fix-bundle)
**Target:** `verification/final_audit/targets/T54_flow_diagram_value_node/08_verdict.md` caveat
**Scripts:** `scripts/investigate_gasspeicher_87.py`, `_part2.py`, `_part3.py`

## Summary finding

**Excel's "87" at all three Gasspeicher positions IS a formula, not a
hardcoded visual copy.** `HARDCODED_VALUES_TRACE.md` §6's claim that
"Excel cell H37 contains no formula — the '87' there is a visual copy,
not a computed value" is **incorrect about the cell reference**. There
is no H37; the cells that produce "87" are **`L37` and `Q37` on sheet
`1.Jahresbilanz_Strom`** — both are formulas.

## Evidence

### Excel's cells producing "87"

All on sheet `1.Jahresbilanz_Strom`:

| Cell | Formula | Computed value | Round → diagram label |
|---|---|---:|---:|
| `L37` | `=L36*TLproEingabeEinheit` | 86.94 | **87** |
| `Q37` | `=Q36*TLproEingabeEinheit` | 86.89 | **87** |

Upstream feeders:

| Cell | Formula | Computed value | Semantic |
|---|---|---:|---|
| `L28` | `='Zeitreihen Kalkulation'!P152/N33` | 406,108.38 | `einspeich_sum / 0.65` = `n_output_branch` |
| `L36` | `=L28*N33` | 263,970.44 | `n_output_branch × ETA_STROM_GAS` = `einspeich_sum` (steady) |
| `Q36` | `='Zeitreihen Kalkulation'!U152` | 263,811.17 | `ausspeich_sum` (Rückverstr output) |

Named-range lookup:

| Name | Definition | Value |
|---|---|---:|
| `TLproEingabeEinheit` | `='1.Jahresbilanz_Strom'!$D$85` = `=S26/VerbrauchStrom` = `365/VerbrauchStrom` | 0.0003293634 |
| `VerbrauchStrom` | `='1.Jahresbilanz_Strom'!$S$25` | 1,108,198.26 GWh |

So Excel's `TLproEingabeEinheit = 365 / 1,108,198 = 3.294e-4`.

### Our simulator's formula

`simulator/signals.py::compute_ws_diagram_reference()`:

```python
flow_gasspeicher_direkt_tages = (ely_branch_value * ws_consts["ETA_STROM_GAS"]) * tl_factor  # line 175
flow_gas_storage_tages          = gas_storage * tl_factor                                      # line 176
flow_t_value_tages              = t_value * tl_factor                                          # line 177
```

with

- `ely_branch_value = renewable_value("9.2.1.5.2")` → scenario-target Ely-P2G input ≈ **385,933 GWh**
- `n_output_branch = einspeich_sum / 0.65` → solver-simulated actual ≈ **406,108 GWh**
- `gas_storage = n_output_branch * ETA_STROM_GAS = einspeich_sum` ≈ **263,970 GWh**
- `t_value = ausspeich_sum` ≈ **263,811 GWh**
- `tl_factor = 365 / final_stromnetz = 365 / 1,105,519 ≈ 3.302e-4`

Producing per-field:

| Field | Annual | × tl_factor | Tages | Rounds to |
|---|---:|---:|---:|---:|
| `flow_gasspeicher_direkt_tages` | 385,933 × 0.65 = 250,857 | ×3.302e-4 | 82.84 | **83** |
| `flow_gas_storage_tages` | 263,970 | ×3.302e-4 | **87.16** | **87** |
| `flow_t_value_tages` | 263,811 | ×3.302e-4 | 87.11 | **87** |

### Root cause

**Line 175 uses a different annual basis than lines 176/177.**

- Line 175 uses `ely_branch_value × ETA_STROM_GAS` = the **scenario-target** Ely-P2G input (385,933) post-efficiency (→ 250,857).
- Line 176 uses `gas_storage` = the **solver-simulated actual** electrolysis output (263,970).
- Line 177 uses `t_value` = the **solver-simulated actual** reconversion draw (263,811).

Excel's model at `L36 / Q36` uses the solver-simulated actuals (263,970 / 263,811) for **both** Gasspeicher-in (L36 → L37) and Gasspeicher-out (Q36 → Q37). Excel does NOT have a separate "Direktverbr" annual basis; all three diagram positions ("Ely-P2G → Direktverbr", "Ely-ES → Gasspeicher", "Gasspeicher → Rückv") are labeled "87" with the same L36/Q36 source.

## Mathematical correctness

Both Excel's 87 and our 83 are mathematically internally consistent:

- **Excel's 87** = Tages of actual-simulated einspeich (the gas actually produced by electrolysis over the year), divided by actual annual Stromnetz consumption.
- **Our 83** = Tages of scenario-target Ely-P2G input × efficiency, divided by actual annual Stromnetz consumption.

The ratio 263,970 / 250,857 = 1.0523 reflects the solver "over-shooting" the scenario target input by ~5% — presumably because the 365-day solver's daily einspeich cumulates to more than the scalar `ely_branch_value` annual target, consistent with balanced-scenario convergence behaviour.

Neither is "wrong"; they measure different things.

## Stakeholder-intent question

The Excel diagram visually labels all three Gasspeicher positions with the same number (87). This is the stakeholder-facing artifact. Our simulator produces 83/87/87 — subtly inconsistent across the three gas-flow positions, which a reader comparing against the Excel reference will notice as drift.

**Is Excel's "all 87" an authoritative reference, or is our "83/87/87" a more-informative correction?**

Arguments for Excel's approach (adopt 87):
- Diagram-reading consistency — matches the Excel reference 1:1
- Simpler to explain: one Tages value for the gas tank throughput
- HARDCODED_VALUES_TRACE.md §1 already lists the "Ely-P2G → Direktverbr" literal as "87", so the original reference-capture intended 87

Arguments for our approach (keep 83):
- More granular: distinguishes scenario-planned vs solver-actual when they diverge
- Our line 176/177 already give 87 for the tank-out flow; adding a different number for direct-consumption reveals the solver's scenario overshoot

## Recommendation

**Adopt Excel's convention — fix `flow_gasspeicher_direkt_tages` to use `gas_storage` instead of `ely_branch_value × ETA_STROM_GAS`.**

Rationale:

1. Excel IS the stakeholder reference. The diagram is a portable visual
   artifact the stakeholders compare against; numerical consistency with
   Excel matters more than Python-internal "correctness".
2. The three positions on the flow diagram all refer to the **same gas
   flow** (electrolysis output = tank-in, direct-consume and tank-out
   are time-integrated to match). Labeling them asymmetrically (83/87/87)
   invites questions that aren't answered by any T54 PDF text.
3. HARDCODED_VALUES_TRACE.md already mis-documented H37 (a non-existent
   cell) as hardcoded — correcting to L37/Q37 (formulas) + adopting the
   Excel basis removes both the doc and the code drift.

Proposed one-line fix in `simulator/signals.py` line 175:

```python
# before
flow_gasspeicher_direkt_tages = (ely_branch_value * ws_consts["ETA_STROM_GAS"]) * tl_factor

# after
flow_gasspeicher_direkt_tages = gas_storage * tl_factor
```

This is identical to line 176 (`flow_gas_storage_tages`). Arguably the
two should be one variable, but the template binds them separately (IDs
on lines 350 and 366 of `annual_electricity.html`) so they stay split.

## Outcome per investigation protocol

Per Fix 4 instructions:

> If the answer is "Excel is authoritative, we should match": DO NOT FIX.
> File a TaskCreate with the fix proposal + leave caveat open.
> Pascal decides whether to ship the math change.

→ **Fix NOT applied.** TaskCreate filed for Pascal's decision.
→ T54 caveat REMAINS OPEN (still CAVEAT verdict, not upgraded to PASS).
→ HARDCODED_VALUES_TRACE.md §6 claim about "H37 hardcoded" is wrong and
  should be corrected in the same future commit that adopts the fix.
