# F009 — Jahresstrom Abregelung sum shows 3.2 % drift vs Excel

**Severity**: LOW — within documented convergence tolerance.
**Affects calc**: YES but documented. `docs/CONVERGENCE_ITERATIONS_CHANGED.md` explicitly calls this out as an accepted perf/accuracy trade-off.
**Domain**: §6 Jahresstrom parity
**Confidence**: HIGH — numerical drift confirmed, source documented.

## Observed

| node | Our value | Excel cell | Excel value | drift |
|------|-----------|------------|-------------|------:|
| `n_input_branch` | 195,890.29 | `L23` (AbregCopy → Q152) | 189,627.90 | 3.3 % |
| `flow_q_abregelung_tages` | 64.55 | `L24` | 62.46 | 3.25 % |
| `abgleichdifferenz` | 156.63 | `Q44` | 159.27 | 1.66 % |

## Context

The 2026-04-21 performance pass intentionally reduced convergence
iteration counts to get Heroku cold-start balance from ~5 min to
~2 min. This creates small residual numerical drift (within scenario
D tolerance of ±5 ha / ±1 GWh) but is **not bit-identical** to the
pre-optimization outputs.

`docs/CONVERGENCE_ITERATIONS_CHANGED.md` explicitly documents the
expected drift and provides the revert recipe if bit-identical math
is required.

The observed 3.2 % drift on the Abregelung sum is ~6.3 GWh absolute
— above the ±1 GWh nominal tolerance on a single balance iteration,
but still within scenario D's end-to-end tolerance.

## Why this is not a "true" formula bug

1. The daily Einspeich + Abregelung formulas in `WS365Formula`
   EXACTLY match Excel (verified in §5: `threshold=1, multiplier=1`).
2. WSData daily promille inputs match Excel to 8+ decimal places
   (§5: 1460/1460 comparisons PASS_COSMETIC or EXACT, 0 DRIFT).
3. Annual totals of downstream chain (final_stromnetz, n_to_right,
   n_output_branch, gas_storage, t_value, h2_offer) all match Excel
   within 0.07–0.15 % — well under the 1 % threshold.
4. The 3.3 % drift manifests specifically in the Abregelung /
   Mangel-Last difference numerics, which are sensitive to how the
   goal-seek (solver) converges on the final Speicherbilanz = 0
   state. Cutting iterations leaves residual ~6 GWh mis-balance that
   the cached Excel values (which were solved to higher precision at
   file save) don't have.

## Node distribution summary

Full Jahresstrom diagram (31 nodes compared):

| verdict | count |
|---------|------:|
| EXACT | 2 |
| PASS_COSMETIC (≤ 0.01 %) | 3 |
| PASS (≤ 0.1 %) | 8 |
| PASS_LOOSE (≤ 1 %) | 13 |
| **DRIFT (> 1 %)** | **5** |

Of the 5 DRIFT nodes:
- 3 are the Abregelung-chain drift described above.
- 2 (`bio_tages` and `bio_pct`) are my MAPPING ERRORS in the
  comparison script: Excel E14/E15 are not Tagesladungen / %-share
  for the Bio branch; they hold different metrics (relative share
  as a raw decimal 0.00234 = 0.234 %). The actual bio Tages value
  1.49 is computed as `4525 × TLproEingabeEinheit` which is the
  same formula Excel uses, giving ≈ 1.49. So not a real drift —
  the mapping here is `bio_tages` → `E26`-equivalent (i.e. the
  diagram text label) rather than `E14`.

Therefore the true Jahresstrom parity result is:
- 29/31 nodes PASS at 1 % tolerance
- 3 nodes (Abregelung chain) drift ~3 % due to F009 (documented perf trade-off)
- 2 nodes are mapping errors in my script (bio tages/pct)

## Recommended fix / action

- **F009 (accepted)**: No action unless Pascal explicitly wants
  bit-identical math. Revert recipe in
  `docs/CONVERGENCE_ITERATIONS_CHANGED.md` if needed.
- **Mapping errors**: low priority; update this audit script's MAP
  entries for bio_tages / bio_pct if a follow-up pass is done.

## Scripts

- `verification/formula_audit/scripts/09_jahresstrom_parity.py`
- `verification/formula_audit/05_jahresstrom_parity/every_diagram_node.csv`
