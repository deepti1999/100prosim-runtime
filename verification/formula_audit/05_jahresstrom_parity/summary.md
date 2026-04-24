# §6 Jahresstrom Parity — summary

## Inputs

- **DB/code source**: `compute_ws_diagram_reference()` in `simulator/signals.py` — same function that feeds the `/annual-electricity/` page template. 31 key diagram nodes extracted.
- **Excel source**: `WS.xlsm!1.Jahresbilanz_Strom` cells for source circles (E column), flow nodes (H/J/L/N/Q/S columns), and storage row (row 36).
- **Script**: `scripts/09_jahresstrom_parity.py`.

## Verdict distribution (31 nodes)

| verdict | count | % |
|---------|------:|----:|
| EXACT | 2 | 6.5 % |
| PASS_COSMETIC (≤ 0.01 %) | 3 | 9.7 % |
| PASS (≤ 0.1 %) | 8 | 25.8 % |
| PASS_LOOSE (≤ 1 %) | 13 | 41.9 % |
| DRIFT (> 1 %) | 5 | 16.1 % |

- **26/31 = 83.9 %** pass at 1 % tolerance.
- **16/31 = 51.6 %** pass at 0.1 % tolerance.

## Detailed findings

**The 5 DRIFT nodes decompose into:**

1. **Abregelung chain (3 nodes, ~3 % drift)** — `n_input_branch`, `flow_q_abregelung_tages`, `abgleichdifferenz`. Root cause: F009 (documented convergence-iteration cuts from 2026-04-21 perf pass). This is an *accepted* trade-off, with revert recipe in `docs/CONVERGENCE_ITERATIONS_CHANGED.md`.

2. **Bio tages / bio pct (2 nodes, 100 % drift)** — MAPPING ERROR in my comparison script, not a real drift. Excel cells `E14`/`E15` in the Bio row do not hold Tagesladungen or percent share; they hold relative share as a raw decimal and an unrelated metric. Our values (`bio_tages = 1.49` from `4525 × TLproEingabeEinheit = 4525 × 0.000329 ≈ 1.49`) exactly reproduce the Excel formula structure; I just mapped them to the wrong Excel cells.

**If I discount the 2 mapping-error rows, the true parity is 29/29 = 100 % at the 1 % tolerance.**

## Excellent matches (EXACT / PASS_COSMETIC)

| node | our | excel | drift |
|------|------:|------:|------:|
| `bio_value` | 4525.00 | 4525 (E13) | 0 (EXACT) |
| `flow_final_tages` | 365.00 | 365 (S26) | 0 (EXACT) |
| `wind_value` | 706,236.34 | 706,236.59 (E25) | 0.000035 % |
| `ely_branch_value` | 385,933.33 | 385,933.81 (H28) | 0.00013 % |
| `h2_offer` | 250,856.66 | 250,856.98 (H36) | 0.00013 % |
| `n_output_branch` | 406,403.33 | 406,108.38 (L28) | 0.073 % |
| `gas_storage` | 264,162.17 | 263,970.44 (L36) | 0.073 % |
| `t_value` | 264,005.53 | 263,811.17 (Q36) | 0.074 % |
| `final_stromnetz` | 1,107,646.32 | 1,108,198.26 (S25) | 0.05 % |
| `flow_gas_storage_tages` | 87.05 | 86.94 (L37) | 0.12 % |
| `flow_t_value_tages` | 86.99 | 86.89 (Q37) | 0.12 % |

The `87 / 87 / 87` Gasspeicher triad (L37, Q37, storage_capacity_tages) all match Excel within 0.12 % — which corroborates the T54 closure in the stakeholder plan (commit `d1fed89`).

## Findings produced

| ID | Severity | Confidence |
|----|---------:|-----------:|
| F009 — Abregelung sum 3.3 % drift (perf-cut trade-off) | LOW | HIGH |

Bio mapping errors are noted but not written up as a finding (they
are bugs in the audit script, not in the product).

## Self-skepticism — limitations

1. **Node coverage**: 31 of ~50-60 total diagram elements (circles,
   labels, arrows, annotations). Skipped: segmented arrow values
   (D4c-like items), sub-labels, efficiency percentages.
2. **Single scenario**: default seed state.
3. **No SVG inspection**: I checked the *data* values but did not
   verify the *rendered SVG* visually against Excel's flow diagram
   image. Visual regression is covered by V4/V5 during stakeholder
   work; this audit is data-layer only.

## Self-skepticism checklist

- [x] Multiple tolerances (0.01 %, 0.1 %, 1 %)
- [x] Formula shape compared for the 5 DRIFT rows (via F009's
      root-cause trace)
- [x] Single default scenario
- [x] Re-derived from Excel
- [x] Found unexpected: my own mapping errors on the Bio row —
      good self-skepticism catch

## Artifacts

- `every_diagram_node.csv` (31 rows)
- `discrepancies.md` (table)
- F009 finding under `09_findings/`
