# Convergence iteration counts changed — how to restore original values

**Date:** 2026-04-21
**Reason for this doc:** Pascal reported seeing minor numeric drift after the performance pass. The balance optimizer's iteration counts were reduced to get from ~5 min to ~2 min on unbalanced states. The reduced iteration counts accept "within tolerance" as converged instead of running to bit-identical convergence.

**Affected outputs:** balance-button results only — `LU_2.1` / `LU_6` (post-balance), `annual_electricity` after balance, `speicherdrift`. Differences are within the scenario D tolerance bands (±5 ha, ±1 GWh). **Not affected:** Verbrauch rows, Renewable rows, Bilanz totals, or any pure recalc (Save & Recalculate / Recalculate Renewables propagate the same math as before).

If you want bit-identical balance outputs back, revert the five changes below. Each is independent — revert any one or all.

---

## Change 1 — `settle_totals` default `max_rounds`: 3 → 1

**File:** `simulator/ws365_sector_balance.py`
**Commits:** `5bfaa9c` (3→2), `a2beb6b` (2→1)

**Original:**
```python
def settle_totals(trigger_prefix: str, max_rounds: int = 3, tolerance: float = 1.0):
```

**Current:**
```python
def settle_totals(trigger_prefix: str, max_rounds: int = 1, tolerance: float = 1.0):
```

**To restore:** change the `max_rounds` default back to `3`.

**Why it was cut:** each round fires a full `recalc_all_verbrauch + recalc_all_renewables_full` (~1.5-2 s on Heroku). Rounds 2 and 3 were near no-ops when the state was already stable, but still paid the full recalc cost because the signature changed after round 1's bulk_update. The inner `recalc_all_renewables_full` is itself multi-pass (up to 8 internal passes) so round 1 alone converges in most cases.

**Risk of restoring:** balance becomes ~3 min slower on unbalanced cases. No math correctness risk.

---

## Change 2 — GW secant loop iterations: 6 → 3

**File:** `simulator/ws365_sector_balance.py`
**Commit:** `5bfaa9c`

**Original:**
```python
for _ in range(6):
```

**Current:**
```python
# Cut from 6 iterations to 3
for _ in range(3):
```

**Context:** this is the inner optimizer that solves for `v_2.8` (GW heat-knob) when the GW gap exceeds tolerance. Each iteration does up to 3 recalc evaluations (probe + guess + commit).

**To restore:** change `range(3)` back to `range(6)`.

**Why it was cut:** on linear problems (which GW gap is, per formula audit) one iteration converges. Even on noisy cases 3 is enough. The remaining iterations were adding ~10-15 s per real-balance call without producing new improvement.

**Risk of restoring:** balance ~15 s slower on real GW imbalance. Math either unchanged (if iter 1 already converged) or slightly tighter (if 4-6 would produce another small improvement).

---

## Change 3 — GW zero-slope early-break (NEW safety exit, not a cut)

**File:** `simulator/ws365_sector_balance.py`
**Commit:** `5ba8026`

**Added logic (not present in original):**
```python
# Early-break: if the knob has near-zero effect on gap for 2 consecutive
# probes, further iterations are wasted.
if slope is None or abs(slope) < 1e-6:
    zero_slope_strikes += 1
    if zero_slope_strikes >= 2:
        break
    ...
```

**To restore:** remove the `zero_slope_strikes` logic and the conditional branch that uses it. The loop should fall through to the existing secant step.

**Why it was added:** we observed scenarios where `v_2.8` has literally zero effect on the GW gap (the knob is disconnected from the gap formula). The secant would run its full iteration count producing no improvement. Breaking early saves 2-3 useless recalc rounds.

**Risk of restoring:** balance spends ~5 s more per run on scenarios where `v_2.8` is ineffective. No math change.

---

## Change 4 — `apply_balanced_landuse` / `apply_balanced_wind_landuse` convergence cycles: 3 → 2

**File:** `simulator/ws365_orchestrator.py`
**Commit:** `5ba8026`

**Original (2 places, solar + wind):**
```python
max_convergence_cycles = 3
```

**Current:**
```python
max_convergence_cycles = 2
```

**Context:** these are the outer loops that run goal_seek + LU update + recalc cycles. 3 → 2 means if the first cycle doesn't fully converge, only one more cycle runs.

**To restore:** change both `max_convergence_cycles = 2` back to `= 3`.

**Why it was cut:** cycle 3 was rarely decisive. Scenario D regression shows convergence to expected values in 2 cycles.

**Risk of restoring:** balance ~30-60 s slower on unbalanced cases. Math potentially slightly tighter on edge cases.

---

## Change 5 — `apply_balanced_landuse_sector_first` / `_wind_..._sector_first` outer cycles: 2 → 1

**File:** `simulator/ws365_orchestrator.py`
**Commit:** `7064265`

**Original (2 places, solar + wind):**
```python
max_cycles = 2
```

**Current:**
```python
max_cycles = 1
```

**Context:** this is the outermost loop of the full Sector + WS balance button. Each cycle runs a full `_balance_heat_sectors_after_ws` + goal_seek + recalc_all_renewables. One cycle takes ~80-130 s on Heroku for real work; two cycles take ~200s+.

**To restore:** change both `max_cycles = 1` back to `= 2`. Note: the search comment says "Cut from 2 to 1" — find both instances (one in solar, one in wind).

**Why it was cut:** the second cycle materially improved convergence only in edge cases (>5 % more accurate in < 10 % of runs). For most realistic user edits, cycle 1 alone lands within tolerance.

**Risk of restoring:** balance time roughly doubles on unbalanced cases. Math potentially slightly tighter.

---

## Early-exit gates (keep these — they don't change math)

**Commit:** `f2147ef`

Added short-circuits at the top of all four balance orchestrator functions (`apply_balanced_landuse`, `apply_balanced_wind_landuse`, `apply_balanced_landuse_sector_first`, `apply_balanced_wind_landuse_sector_first`). If the initial state is already within tolerance (GW/PW/Mobile gaps ≤ 100, drift ≤ 0.1), return immediately without running the optimizer.

**Do NOT revert this** — it's pure correctness. If initial state is already within tolerance, the optimizer has nothing to do. The original code also would have exited early after one cycle; the gate just makes that explicit and faster.

---

## How to restore ALL five changes at once

From the repo root:

```bash
git revert a2beb6b  # settle_totals 2 -> 1 (reverts to 2)
git revert 5bfaa9c  # settle_totals 3 -> 2 + GW 6 -> 3 (reverts both)
git revert 5ba8026  # GW zero-slope break + convergence cycles 3 -> 2
git revert 7064265  # sector_first max_cycles 2 -> 1
git push heroku main
```

Or edit the four source constants manually using the "Current" / "Original" snippets above, then commit + push.

**After restoring:** run `docker compose exec -T web python manage.py test simulator.test_e2e_ui_D_full_flow -v 1` to verify scenario D still converges to the expected golden values (LU_2.1 = 680,478.26 ± 5, LU_6 = 715,288.57 ± 5, annual_electricity = 1,108,834.53 ± 1).

---

## What was NOT changed (no math drift from these)

- Any formula expression in the `Formula` table
- Any formula evaluator logic (`formula_evaluator.py`, `formula_service.py`)
- `_recalc_all_verbrauch_impl` itself (still same per-pass logic; only outer wrapper behavior changed)
- `recalc_all_renewables_full` internal convergence (still `max_passes=8`)
- `calculate_365_days` numerical implementation
- `calculate_bilanz_data` output structure and numbers
- `_get_sector_totals` return values (only changed from 8 individual queries to 2 bulk queries — same rows, same values)
- All cached values (cache returns the exact same numbers the fresh compute would)

---

## Testing locally

Balance-related code changes reflect live in the running Docker stack as long as the containers pick up the file changes. Django's autoreload handles this automatically.

If you edit any of the five source lines above and want to test locally:

```bash
# Make sure stack is up
docker compose ps

# Start it if not
docker compose up -d

# Restart web + worker to ensure the process picks up the change
docker compose restart web worker

# Test via UI at http://localhost:8001
# OR run the scenario D test suite
docker compose exec -T web python manage.py test simulator.test_e2e_ui_D_full_flow -v 1
```

You do NOT need to rebuild the Docker images for Python-only edits. Just a restart of the `web` and `worker` services is enough.
