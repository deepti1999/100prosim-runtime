# Ultraplan — performance & extensibility with math-safety guarantees

**Date:** 2026-04-21
**Companion to:** `docs/DEEP_ANALYSIS_2026-04-21.md`

**Prime directive:** no stakeholder-visible number changes without explicit intent. Every step below is gated by regression.

---

## 0. Safety contract — read before touching anything

Anything marked as a "step" in this plan satisfies all of these:

1. **Cell names, codes, and sector names are NEVER renamed.** This plan only changes *internals*.
2. **Every step is scoped to one concern.** One PR = one step = revertable in isolation.
3. **Every step passes the full regression gate BEFORE commit:**
   - `python regression/compare.py A-baseline-readonly` → exit 0
   - `python regression/compare.py C-ws-balance` → exit 0
   - `python regression/compare.py D-full-flow-verbrauch-solar-wind` → exit 0
   - Relevant thesis test module per the CLAUDE.md change-type table
4. **If `compare.py` exits 1 (value drift):** stop, investigate, do not update the golden. Either the change is wrong, or the change is intentional and must be documented + golden re-captured deliberately.
5. **If `compare.py` exits 2 (fingerprint drift):** re-capture the baseline; do not patch values.
6. **Never push.** All commits stay local per `feedback_no_push.md`.
7. **Before each step:** run the baseline regression to prove the current state is the expected one. If A/C/D don't pass *before* starting, we already have a drift and must stop.
8. **Bulk operations (`bulk_update`, `update()`) bypass signals.** That's already how recalc works today — preserving it matters.
9. **Expected numbers that MUST NOT change** (scenario D golden):
   - Row 9.3.1 = **406,403.3** (invariant — never recalculated)
   - Row 9.3.4 = **195,890.3** (invariant — never recalculated)
   - Verbrauch row 7 `ziel` after edits = **1,006,821.8**
   - Verbrauch row 8 `ziel` after edits = **1,858,597.3**
   - Solar: LU_2.1 = **680,478.26 ha**, annual electricity = **1,108,834.53 GWh**
   - Wind: LU_6 = **715,288.57 ha**, annual electricity = **1,108,834.53 GWh**
   - `speicherdrift ≤ 0.1 GWh` after any balance

If any of these move, something broke. Full stop.

---

## Phase 1 — Pure performance, zero behavior change (target: 1 week)

Each step in this phase is independently mergeable and independently revertable.

### Step 1.1 — ~~Add DB indexes on `code`~~ — **SKIPPED, already done**

**Status:** verified unnecessary on 2026-04-21. Attempted the migration and caught a unique-constraint violation (LU_0 appeared to be duplicated). Inspection of the raw Postgres schema revealed each table has **per-workspace scoped indexes already in place**:

```
simulator_landuse:
  landuse_owner_code_uniq     UNIQUE   (owner_id, code)
  landuse_global_code_uniq    UNIQUE   (code) WHERE owner_id IS NULL
  simulator_l_owner_i_babf34  btree    (owner_id, code)

simulator_renewabledata:
  renewable_owner_code_uniq   UNIQUE   (owner_id, code) WHERE code IS NOT NULL
  renewable_global_code_uniq  UNIQUE   (code) WHERE code IS NOT NULL AND owner_id IS NULL
  simulator_r_owner_i_a214f3  btree    (owner_id, code)

simulator_verbrauchdata:
  verbrauch_owner_code_uniq   UNIQUE   (owner_id, code)
  verbrauch_global_code_uniq  UNIQUE   (code) WHERE owner_id IS NULL
  simulator_v_owner_i_42d8a7  btree    (owner_id, code)
```

The ORM filters by `owner_id` through owner-scope middleware, so `.objects.get(code=X)` becomes `WHERE owner_id=? AND code=?` — the composite `(owner_id, code)` index covers it exactly. Adding a standalone `db_index` on `code` would create a redundant single-column index the planner wouldn't use.

**Conclusion:** no migration needed. The perf gain from Step 1.1 was already captured before this session began. Remaining wins come from Steps 1.2 - 2.1 which reduce query **count**, not per-query cost.

### Step 1.2 — Idempotent recalc short-circuit (0.5 day)

**Change:** at the entry of `recalc_all_renewables_full` (`recalc_service.py:112`) and `recalc_all_verbrauch` (`verbrauch_recalculator.py:109`), compute a hash of inputs:

```python
def _recalc_inputs_hash():
    from django.db.models import Max
    return (
        LandUse.objects.aggregate(m=Max('updated_at'))['m'],
        VerbrauchData.objects.filter(is_calculated=False).aggregate(m=Max('updated_at'))['m'],
        RenewableData.objects.filter(is_fixed=True).aggregate(m=Max('updated_at'))['m'],
        Formula.objects.aggregate(m=Max('updated_at'))['m'],  # if present
    )
```

Cache the tuple + the previous result count at module scope. If the hash is unchanged since the last call, return 0 immediately.

**Why it's safe:**
- Only reads `updated_at` on rows Django itself maintains.
- If anything that affects the recalc output has changed, its `updated_at` bumps, hash changes, recalc runs normally.
- Worst case (hash computation wrong): recalc runs when it didn't need to — identical to today.

**Math risk:** none as long as every input mutation goes through Django's `save()` which bumps `updated_at`. The current codebase already relies on this. **Before merging, grep for any `UPDATE`/`raw SQL` writes that bypass `updated_at` and convert them.** (Candidate: `bulk_update` without `updated_at` in the field list — `recalc_service.py:231` already includes `updated_at`, good.)

**Expected effect:** a balance button press does ~29 settle rounds, but only ~1-3 *actually change anything*. The other 26 become instant. Projected solar_sector_ws: 68 s → ~10 s locally.

**Verification:**
- `compare.py A` → 0
- `compare.py C` → 0 (invariants 9.3.1=406403.3, 9.3.4=195890.3 preserved)
- `compare.py D` → 0 (solar + wind LU and annual electricity preserved)
- `test_ws365_formulas` → all pass
- `test_bb_bal` + `test_e2e_ui_D_full_flow` → all pass
- Measure: second consecutive `recalc_all_renewables_full()` fires <20 queries (not 1761).

**Rollback:** remove the hash check at function entry. Zero side-effects.

### Step 1.3 — Plug the `_resolve_variable` fast-path leaks (1 day)

**Pre-audit (do this before writing code):**

```python
# one-off shell command, commit as a test:
from simulator.models import FormulaVariable
print(FormulaVariable.objects.values_list('source_type', flat=True).distinct())
```

Enumerate every `source_type` that appears in the DB. Compare against the branches in `formula_service.py:764-` fast path. For each missing branch, add one.

**Change:** in `formula_service.py`, extend the fast-path branches in `_resolve_variable` to cover every observed `source_type`. For any type that genuinely needs a DB hit (rare edge cases), keep the DB path but log a WARN with the `source_type` — we want to know if prod still hits it.

**Math risk:** **this is the highest-risk step in Phase 1.** It changes where values come from (DB → in-memory dict). If the in-memory dict is stale or the key format mismatches, values go to 0 or None.

**Safety measures:**
- Run with DEBUG logging: log every fast-path hit and miss during the first day on CI.
- Shadow comparison: for 100 formula keys, run both the fast path and the DB path, assert equality. Only then remove the DB path.
- If any production formula returns a different value with the fast path vs the DB path, **do not merge**. Fix the lookup, re-verify.

**Verification:**
- Shadow-comparison test (new): `test_bb_calc_fastpath_parity` — loops 100+ Formula rows, evaluates each with fast path + DB path, asserts abs diff < 1e-9.
- `compare.py A/C/D` → all 0.
- Re-run profile: `recalc_all_renewables_full` should drop from 1761 queries to <100.

**Rollback:** revert the fast-path extensions; DB path still works as today.

### Step 1.4 — Cache `calculate_bilanz_data()` output per CalculationRun (0.5 day)

**Change:** wrap `calculate_bilanz_data()` in `calculation_engine/bilanz_engine.py:278` with:

```python
def calculate_bilanz_data(fail_fast=False):
    cache_key = _bilanz_cache_key()  # = f"bilanz_{latest_CalculationRun.id}"
    cached = django_cache.get(cache_key)
    if cached is not None:
        return cached
    result = _calculate_bilanz_data_impl(fail_fast=fail_fast)
    django_cache.set(cache_key, result, timeout=3600)
    return result
```

Invalidate by bumping `CalculationRun.id` on every recalc completion (already does this). If no `CalculationRun` exists, skip cache (first-run edge case).

**Why it's safe:** the output is pure function of (VerbrauchData, RenewableData, LandUse) state, all of which are snapshotted by `CalculationRun`. A stale cache means we're showing values that match the last recalc — which is always what the page should show.

**Math risk:** only if `CalculationRun.id` doesn't bump on an input change. Audit: grep for `CalculationRun.objects.create(` — verify every mutation path creates one. (Likely gap: direct DB writes from management commands. Those are admin-only, acceptable.)

**Expected effect:** `/bilanz/` from 1165 queries → ~3 on cache hit. Same for `/cockpit/` if it uses the same function.

**Verification:**
- `compare.py A` → 0 (captures /bilanz/ values).
- Browser test: edit Verbrauch 1.1.2 → Save All → navigate to /bilanz/ → confirm new values, not cached ones.
- Re-run profile: `/bilanz/` < 100 queries on cache hit.

**Rollback:** remove the cache wrapper.

### Step 1.6 — Cache lookups in `_auto_context_from_tokens` ✅ SHIPPED `ebabf43`

**Added after Phase 1 initial pass** when deep profile revealed this was the last major query leak.

**Change:** added a process-local cache of 6 per-table bare-code lookups. When `_auto_context_from_tokens` is called with no explicit lookups (the common case via `_safe_eval`), it uses the cached globals instead of firing `.objects.get()` per token.

**Safety gate:** shadow parity test — 758/758 formulas match between cached fast path and DB-fallback slow path.

**Measured (per recalc pass):**
- `recalc_all_verbrauch`: 795 Q → 429 Q (-46 %)
- `recalc_all_renewables_full`: 1761 Q → 893 Q (-49 %)
- Balance cycle cold: 2660 Q → 1423 Q (-46 %)

**Cache invalidation:** post_save signals + explicit calls after bulk_update sites.

**First attempt failed safely:** per-call signature checks (3 Max(updated_at) queries) cost more than they saved. Switched to lazy-build + signal-driven invalidation.

### Step 1.7 — Cache pure compute in `get_ws_365_data` ✅ SHIPPED `9243933`

**Change:** split the 365-day compute from its side effect. Compute is cached by input signature; the write to RenewableData 9.3.1 / 9.3.4 still runs every call (value-compare idempotent).

**Measured:** 48 ms / 12 Q → 10 ms / 11 Q on cache hit.

**Safety gate:** JSON-dump parity of cached vs fresh response. Invariants preserved.

### Step 1.5 — Fix `_get_sector_totals` (0.5 day)

**Change:** `ws365_sector_balance.py:19-72`: replace the 6-8 individual `.objects.get(code=...)` calls with one bulk fetch using `filter(code__in=[...])` → dict → lookups. Pass the `totals` dict into `settle_totals` so it isn't recomputed per iteration.

**Math risk:** very low — reading the same rows, just fewer queries. Edge case: the `try/except DoesNotExist` fallback for `total_energy` section must still work if `VerbrauchData 7` or `RenewableData 10.1` is missing.

**Verification:**
- `compare.py C` and `D` → 0.
- `test_bb_bal` → all pass.
- Measure: `_get_sector_totals` drops from 8 queries to 1.

**Rollback:** revert the single function.

---

## Phase 2 — The biggest single speedup (target: 2-3 days)

### Step 2.1 — GW 2.8 direct solve — **DEFERRED (empirical finding)**

**Status:** deferred on 2026-04-21 after two separate empirical investigations.

**First finding — Phase 1 already makes iterations cheap.** Step 1.2 caches repeat recalcs at ~7 ms each. That collapses the per-iteration cost of the GW secant loop by ~99 %. Savings from replacing 6 iterations with 1 drop from seconds to ~35 ms.

**Second finding — the secant is dormant in practice.** Shadow harness built with a candidate direct-solve (`simulator/ws365_gw_direct_solve.py`) and synthetic imbalance scenarios. Result: **v_2.8 has no measurable effect on the GW gap on the current seed.** Setting v_2.8 to 60, 70, 79.47, 85, 95 all produce identical GW gap (-14.84 GWh). Dropping r_10.4 by 20 % was instantly overwritten by the recalc because r_10.4 is a calculated (not fixed) row. The GW secant loop at `ws365_sector_balance.py:175` only runs when `abs(gap) > 100`, which on this seed **never happens**.

**Implication:** replacing the secant with any alternative changes behavior only in hypothetical scenarios that don't reproduce on the current seed. We have no way to prove parity for a code path that doesn't execute.

**Decision:** do not modify the secant. Keep the existing 6-iteration implementation as-is. The `ws365_gw_direct_solve.py` module is kept in the tree as a reference for a future resumption if stakeholders ever encounter a scenario where the secant actually runs and is measurably slow.

**Risk/benefit summary:** risk of silent math regression is nonzero; benefit on realistic seeds is zero. Don't ship.

**If resumed later:** first find or construct a scenario where the secant actually executes (GW gap > 100 GWh). Only then is shadow-parity testing meaningful. Implement behind a feature flag, validate across N real user-adjustment traces, flip only after full agreement.

**Pre-work (do first):** write down the GW gap equation symbolically. Verified in Finding C that every formula in the chain is linear in `v_2.8`. Concretely:

```
gw_demand(x)  = constants only — does not depend on v_2.8
gw_supply(x)  = a*x + b   (derivable from V_2.8.0_ziel = Verbrauch_2_6_ziel * x / 100
                             and propagation through the DAG to Renewable_10.4)
gap(x) = gw_demand - gw_supply(x) = (gw_demand - b) - a*x
```

Solve: `x* = (gw_demand - b) / a`. Then clamp to `[0, 100]`.

**Change:** replace the secant loop in `ws365_sector_balance.py:167-218` with the direct solve, following the same pattern as the PW direct solve (`ws365_sector_balance.py:288-321`). Keep one correction step as a safety net for numerical noise.

**Math risk:** **medium.** If my linearity claim is subtly wrong (e.g., a downstream formula I didn't see has a non-linear dependency), the direct solve gives a different answer than the secant.

**Safety measures:**
- Shadow mode first: run both the secant and the direct solve; log their results; assert they converge to the same value within tolerance (say, 0.01 ha). Only after 10+ runs of agreement, remove the secant.
- Preserve the secant code in git history; easy to revert if Scenario D drifts.
- Scenario D golden expects `LU_2.1 = 680,478.26 ha ± 5`. The direct solve must hit this within 5 ha.

**Verification:**
- Shadow parity test (new): `test_ws365_gw_direct_solve_parity` — runs both methods on 3 seed variations, asserts |delta| < 1.
- `compare.py D` → 0 (solar variant).
- `test_e2e_ui_D_full_flow.test_solar_variant_reaches_expected_lu_2_1_and_annual_electricity` → pass.

**Rollback:** one-file revert.

### Step 2.2 — Optional: same treatment for mobile knobs (0.5 day)

Apply Step 2.1 logic to mobile primary (v_4.1.2.6). Skip mobile secondary — the two-knob fallback is load-bearing.

**Do this only if 2.1 lands cleanly.** If it doesn't, mobile stays as-is.

---

## Phase 3 — Extensibility refactors (target: 1-2 weeks, NOT YET)

**Gate:** only start after Phase 1+2 are stable in production (Heroku) for at least one stakeholder-visible cycle. Performance fixes must prove their value before we take on architecture work.

### Step 3.1 — `Sector` + `SectorRole` tables (3-5 days)

Data model:

```python
class Sector(models.Model):
    code = CharField(unique=True, db_index=True)  # 'KLIK', 'GW', 'PW', 'MOB'
    name_de = CharField
    name_en = CharField(null=True)
    kind = CharField(choices=['electricity', 'heat', 'fuel'])
    order = IntegerField

class SectorRole(models.Model):
    sector = FK(Sector)
    role = CharField(choices=['demand_code', 'supply_code', 'balance_knob_primary', 'balance_knob_secondary'])
    ref_code = CharField  # the Verbrauch/Renewable code this role points to
    ref_table = CharField(choices=['Verbrauch', 'Renewable'])
```

Seed with existing 4 sectors. `_balance_heat_sectors_after_ws` becomes a loop over `Sector.objects.filter(kind__in=['heat','fuel']).prefetch_related('sectorrole_set')`.

**Math risk:** none if seeded correctly from current hardcoded mappings.

**Verification:** scenario D (solar + wind) must hit identical numbers. The refactor is correct iff the regression passes.

**Rollback:** keep the hardcoded fallback in a branch for 2 weeks; revert if drift shows up.

### Step 3.2 — `Parameter` table for physics constants (1-2 days)

Move `ws365_core.py:18-26` constants to a DB table:

```python
class Parameter(models.Model):
    key = CharField(unique=True)
    value = FloatField
    unit = CharField
    description_de = TextField
    description_en = TextField(null=True)
    source = CharField  # provenance
```

Seed with: `grid_loss_rate=0.092`, `electrolysis_efficiency=0.65`, `rueckverstroemung_efficiency=0.585`, `fixed_82_target=12000`, all tolerances, all knob step sizes, `country_area_ha=35759529`, `target_year=2045`, `solar_mw_per_ha`, `wind_mw_per_ha`.

`ws365_core.py` reads at module load time via `get_parameters()` (memoize with cache invalidation on Parameter save). First call fires 1 query; subsequent calls free.

**Math risk:** only if seeded values diverge from the Python constants by any amount. Seed script must read from the Python file first, then delete the Python constants.

**Verification:** `compare.py D` must show identical numbers before and after.

### Step 3.3 — `PERCENTAGE_GROUPS` table (0.5 day)

`percentage_rebalancer.py:19-26` currently hardcodes `[KLIK only]`. Make it a DB table (`PercentageGroup` + `PercentageGroupMember`). Same shape as SectorRole.

### Step 3.4 — i18n wrapping (2-3 days, lowest priority)

- Add `name_de`/`name_en` columns to Formula, VerbrauchData, RenewableData, LandUse, Sector.
- Migrate existing German names into `name_de`.
- `{% trans %}` wrap all template strings.
- `django-admin makemessages -l de`; commit `.po`.
- Default language stays German. English ships when someone translates.

**Math risk:** zero — display-only.

---

## Phase 4 — Deferred / only if stakeholder asks

- `Carrier` / `Link` / `Conversion` as first-class entities.
- `Region` + `DailyProfile` for multi-country.
- `Cost` / `Capex` / `Opex` parameters.
- PyPSA selective integration (long-duration storage LP, goal-seek replacement).
- Formula deduplication audit.

---

## Projected end state

Assuming Phase 1 + 2 land:

| Path | Today (local) | After Phase 1+2 (local) | Today (Heroku, modeled) | After Phase 1+2 (Heroku, modeled) |
|---|---:|---:|---:|---:|
| `/bilanz/` | 1921 ms, 1165 Q | ~80 ms, ~5 Q | ~5 s | ~100 ms |
| `/cockpit/` | 1790 ms, 1151 Q | ~80 ms, ~5 Q | ~5 s | ~100 ms |
| `/verbrauch/` | 199 ms, 153 Q | ~40 ms, ~5 Q | ~0.5 s | ~60 ms |
| `solar_sector_ws` | 68 s | ~3 s | ~3 min | ~10 s |
| Adding 5th sector | edit 18 files | edit 18 files (Phase 3 lands extensibility) | — | — |

**Zero cell names changed. Zero stakeholder-visible numbers changed.**

---

## Failure modes to watch for

**If `compare.py D` starts exiting with code 1:**
- Which fields drifted? Likely candidates:
  - `LU_2.1` moved → GW direct solve is wrong; revert Step 2.1, keep secant.
  - `annual_electricity` moved → something in the formula evaluation path is now returning 0 or None; suspect Step 1.3 fast-path gap; run shadow-parity test.
  - `speicherdrift` moved → WS365 storage cycle affected; suspect Step 1.2 hash collision; widen the hash inputs.
- `compare.py` exit 2 (fingerprint drift): seed changed underneath. Not our refactor. Re-capture deliberately.

**If `/bilanz/` shows stale numbers after an edit:**
- Step 1.4 cache invalidation is wrong. Check that `CalculationRun.id` actually bumps on the mutation path. Add a logging assertion.

**If a new stakeholder sector is requested before Phase 3 lands:**
- Do it the old way (edit 18 files). Don't rush Phase 3 — its safety depends on Phase 1+2 being stable first.

---

## What I need Pascal's sign-off on before starting

1. **Approval to add indexes** (Step 1.1) — migration on Heroku DB; safe but user-visible as a one-time migration apply.
2. **Approval to add `Parameter.updated_at` hash check** (Step 1.2) — no visible change but changes recalc semantics (short-circuits when unchanged). Agreed-on behavior: "don't recompute if nothing changed" is arguably what users already expect.
3. **Approval to begin shadow-parity testing for Step 1.3 and Step 2.1.** No production behavior change; adds temporary double-compute for comparison. Safe, but adds test complexity.

Phase 3 requires separate sign-off.
