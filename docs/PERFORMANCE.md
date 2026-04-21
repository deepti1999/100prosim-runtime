# Performance optimization reference

**Status:** shipped to Heroku 2026-04-21. All changes merged to `main`.

This document covers what changed, why, and the measured impact. For deployment details (Heroku setup, recovery, scaling), see `HEROKU.md`.

---

## The problem

Pascal reported the balance button taking **3-4 minutes on first click** and **8-10 minutes on second click** on Heroku. Pages like `/bilanz/` and `/cockpit/` took ~5 seconds each.

Root cause was not Python compute speed — it was **query count × Heroku Postgres round-trip time**:
- One "recalc" pass fired ~1,760 SQL queries.
- A balance button press triggered ~50-100 recalc passes (settle loops, goal-seek iterations, sector optimizer).
- At ~2 ms/query RTT on Heroku, that's 100,000+ queries × 2 ms = 200+ seconds pure network time.

Plus the balance machinery ran the full optimization even when the state was **already balanced**.

---

## Final result (measured end-to-end on Heroku prod)

| Action | Before | After |
|---|---:|---:|
| First solar balance (both button steps) | 3-4 min | **~1.8 s** |
| Second solar balance | 8-10 min | **~0.8 s** |
| First wind balance | 2-3 min | **~14 s / then 0.7 s** |
| Second wind balance | 6-8 min | **~0.7 s** |
| `/bilanz/` page warm | ~5 s | **129 ms** |
| `/cockpit/` page warm | ~5 s | **84 ms** |

**Math invariants preserved:** `9.3.1 = 406,403.32`, `9.3.4 = 195,890.29`, `LU_2.1`, `LU_6`, `annual_electricity`, `speicherdrift` all stable.

**No stakeholder-visible changes:** no cell renames, no UI changes, no formula edits, no schema changes to tracked tables.

---

## What changed (in order of impact)

Each step has a commit hash, a safety gate that was verified, and an independent revert path.

### Step 1.2 — Idempotent recalc short-circuit `568d43f`

**File:** `simulator/recalc_cache.py` (new), wired into `recalc_all_renewables_full` and `recalc_all_verbrauch`.

**Mechanism:** Hash the recalc inputs (LandUse, user-input VerbrauchData, fixed RenewableData, Formula definitions) on function entry. If the hash matches the last call, return the cached result in ~7 ms instead of firing 1,766 queries.

**Why it's the biggest single win:** settle loops call recalc ~29 times per balance press; only 1-3 rounds actually change anything. The other 26+ used to run full recalcs for zero row updates. Now they return instantly.

**Safety gate:** unit tests + invariant check after mutation (cache correctly invalidates).

### Step 1.3 — Lazy lookup cache in `_build_context` `8b8ff2d`

**File:** `simulator/formula_service.py`.

**Mechanism:** Process-local cache of namespace-prefixed lookup keys (`LandUse_LU_2.1`, `Verbrauch_2.10`, `Renewable_10.4`). When `evaluate_formula_by_key` is called without explicit lookups, the cache provides them, so `_resolve_variable` hits the fast path instead of `.objects.get(code=X)`.

**Safety gate caught a real bug:** first attempt used permissive bare-code keys that collided across tables (LandUse's clean `'2.1'` vs VerbrauchData's `'2.1'`). Shadow-parity test evaluated all 758 active formulas both ways — **25 mismatches**. Reverted, redone with namespace-prefixed keys only plus a blacklist on `*_code_*` source_types (whose slow path recursively recomputes). **V2: 758/758 pass.**

### Step 1.4 — Redis cache for `calculate_bilanz_data` `639851a` + TLS fix `060e519`

**File:** `calculation_engine/bilanz_engine.py`, `landuse_project/settings.py`.

**Mechanism:** Django cache wrapper keyed on `latest_CalculationRun.id` plus a 300 s TTL. Every balance job and recalc endpoint creates a new `CalculationRun`, so the cache auto-invalidates on any real recompute.

**Heroku-specific fix:** `rediss://` uses self-signed TLS certs that Python rejects by default. With `IGNORE_EXCEPTIONS=True` django-redis silently returned `None` from every `cache.get`. Fix: `ssl_cert_reqs=ssl.CERT_NONE` in connection options (the TLS itself still encrypts; Heroku's internal network is private). Removed `IGNORE_EXCEPTIONS` so real errors surface.

### Step 1.5 — Bulk-load `_get_sector_totals` `e690bee`

**File:** `simulator/ws365_sector_balance.py`.

**Mechanism:** Replaced 6-8 individual `.objects.get(code=X)` calls with two `filter(code__in=[...])` queries (one per table). Inside a 29-round settle loop that's ~174 fewer queries per balance.

### Step 1.6 — Cache lookups in `_auto_context_from_tokens` `ebabf43`

**File:** `simulator/formula_service.py`, `simulator/signals.py`, `simulator/recalc_service.py`, `simulator/verbrauch_recalculator.py`.

**Mechanism:** `_auto_context_from_tokens` is called from `_safe_eval` (the path used by `VerbrauchCalculator` and `evaluate_with_mappings`) with no lookups, so every token fell back to a DB lookup — ~740 queries per recalc pass. Added a process-local cache of 6 per-table bare-code lookups; invalidated via `post_save` signals and explicit calls after `bulk_update` sites.

**Important pitfall:** first attempt used per-call signature checks (3 Max(updated_at) aggregates). The signature queries cost more than the DB lookups saved. Second attempt uses lazy-build + signal-driven invalidation — cache rebuilds only on real data change. Shadow parity: 758/758 pass.

### Step 1.7 — Cache pure compute in `get_ws_365_data` `9243933`

**File:** `simulator/ws365_orchestrator.py`.

**Mechanism:** Split the 365-day WS compute from its side effect. The compute (~45 ms) is now cached by input signature; the side-effect write to `RenewableData 9.3.1 / 9.3.4` still runs every call (the saves are value-compare idempotent, so no-op on unchanged).

### Early-exit gates on balance orchestrators `f2147ef`

**File:** `simulator/ws365_orchestrator.py` (4 functions).

**Mechanism:** At the top of `apply_balanced_landuse_sector_first`, `apply_balanced_wind_landuse_sector_first`, `apply_balanced_landuse`, and `apply_balanced_wind_landuse`, check if the initial state is already within tolerance (GW/PW/mobile gaps ≤ 100, WS drift ≤ 0.1). If so, return immediately with current values.

**Why this was critical on Heroku:** even with all the lower-level caches, the balance orchestrators ran 2 outer cycles × (sector balance + goal_seek + recalc) before checking anything. That alone was 3-5 minutes on Heroku for an already-balanced state.

### Iteration cuts in `_balance_heat_sectors_after_ws` `5bfaa9c` `5ba8026`

**File:** `simulator/ws365_sector_balance.py`.

**Mechanism:**
- GW secant loop: 6 iterations → 3 with zero-slope early-break (2 strikes = exit). Handles the case where v_2.8 has no effect on GW gap, which we observed empirically.
- `settle_totals` default `max_rounds`: 3 → 2. Round 3 was rarely decisive.
- `settle_rounds` in GW probe: 3 → 2.
- `max_convergence_cycles` in `apply_balanced_landuse`/`wind_landuse`: 3 → 2.

**Scenario D regression:** all 14 tests still pass, including hard-asserted values (`LU_2.1 = 680,478.26`, `LU_6 = 715,288.57`, `annual_electricity = 1,108,834.53`).

### Heroku infra config `5c67ddf` `060e519`

**File:** `landuse_project/settings.py`, `requirements.txt`, `.python-version`.

- Added `django-redis` dependency.
- Redis cache backend when `REDIS_URL` is set (production); LocMemCache local fallback.
- Pinned Python to 3.12 (Heroku default was 3.14, Django 4.2.24 officially supports 3.8-3.12).

### Steps deliberately skipped

- **Step 1.1 — DB indexes on `code` columns.** Verified unnecessary — `(owner_id, code)` composite indexes already exist at the Postgres level via `Meta.constraints`.
- **Step 2.1 — GW direct solve.** Shadow harness revealed `v_2.8` has no measurable effect on GW gap on this seed (the optimizer is dormant). Can't prove parity on code that doesn't execute. Reference module kept at `simulator/ws365_gw_direct_solve.py` for future resumption. Instead, the GW secant got an early-break for the zero-slope case (shipped above).
- **Step 2 (compile formula AST)** — already done at `ws365_formula_engine.py:148`.

---

## Architecture

### How the caches compose

```
HTTP request
    │
    ▼
Page view (/bilanz/, /cockpit/, etc.)
    │
    ▼
calculate_bilanz_data ─── Step 1.4 ─► Redis cache (shared across dynos)
    │                                 key = f"bilanz_data_v1_run{CalculationRun.id}"
    ▼                                 ttl = 300s safety floor
Formula evaluation
    ├── _build_context            ─── Step 1.3 ─► process-local lookup cache
    │                                             (namespace-prefixed keys)
    └── _auto_context_from_tokens ─── Step 1.6 ─► process-local lookup cache
                                                  (bare-code per table)
    │
    ▼
recalc_all_renewables_full ─── Step 1.2 ─► process-local recalc result cache
recalc_all_verbrauch                        (keyed on input hash)
    │
    ▼
get_ws_365_data ─────────── Step 1.7 ─► process-local compute cache
                                        (side-effect writes still fire)
    │
    ▼
_get_sector_totals ──────── Step 1.5 ─► bulk filter(code__in=[...])
                                        (2 queries instead of 8)

Balance orchestrators ──── early-exit ─► return immediately if already balanced
    │                                    (4 orchestrator paths)
    ▼ (only when real work needed)
GW secant optimizer ────── zero-slope ─► break after 2 strikes on useless knob
                          early-break   (iteration cap 6 → 3)
```

### Cache invalidation

**Via signals (fires on any single-row `.save()`):**
- `post_save` on `LandUse`, `VerbrauchData`, `RenewableData`, `Formula`, `FormulaVariable`
- Connected to `_invalidate_formula_lookup_caches` in `signals.py`
- Clears: Step 1.3 lookups, Step 1.6 auto-tokens, Step 1.7 WS365

**Via explicit calls (because `bulk_update` bypasses signals):**
- After `RenewableData.objects.bulk_update(...)` in `recalc_service.py`
- After `VerbrauchData.objects.bulk_update(...)` in `verbrauch_recalculator.py`
- Same functions invalidated

**Via `CalculationRun.id` bump (Step 1.4 only):**
- Every `CalculationRun.objects.create()` in `balance_jobs.py` and `recalc_api.py` produces a new `id`, which makes the cache key different, which forces a cache miss on next `/bilanz/` load.

**Manual:**
- `invalidate_auto_tokens_cache()`
- `invalidate_lookups_cache()`
- `invalidate_ws365_cache()`
- `simulator.recalc_cache.invalidate()`

---

## Math safety

### Every step was verified against

1. **Unit + integration test suite** (14 tests total, 1 skipped):
   - `test_bb_calc` (math)
   - `test_bb_bal` (balance)
   - `test_ws365_formulas` (formula parity)
   - `test_bb_e2e` (end-to-end contracts)
   - `test_e2e_ui_D_full_flow` (scenario D solar + wind + cross-variant invariant)
   - All 11 + 3 tests pass after every step.

2. **Shadow-parity gates** for Steps 1.3 and 1.6 — evaluated all 758 active formulas through both the new fast path and the original slow path, asserted `abs(diff) < 1e-9`.

3. **Invariant checks** at session end on live Heroku:
   - `RenewableData 9.3.1 = 406,403.32`
   - `RenewableData 9.3.4 = 195,890.29`
   - `LandUse LU_2.1 target_ha` stable
   - `LandUse LU_6 target_ha` stable

### Things that were almost shipped unsafely

- **Step 1.3 v1** would have caused 25 silent formula mismatches in production. Shadow parity caught it. Reverted and redone.
- **Step 1.6 v1** used per-call `Max(updated_at)` signature checks that cost more than they saved. Fixed by switching to lazy-build + signal invalidation.
- **Step 2.1** would have been code churn with no benefit — synthetic scenarios proved the code it optimized doesn't execute on realistic seeds.

---

## Files touched

**New files:**
- `simulator/recalc_cache.py` — Step 1.2 idempotency cache
- `simulator/ws365_gw_direct_solve.py` — Step 2.1 reference (not wired)
- `.python-version` — Python 3.12 pin

**Modified:**
- `simulator/recalc_service.py`
- `simulator/verbrauch_recalculator.py`
- `simulator/formula_service.py`
- `simulator/signals.py`
- `simulator/ws365_orchestrator.py`
- `simulator/ws365_sector_balance.py`
- `calculation_engine/bilanz_engine.py`
- `landuse_project/settings.py`
- `requirements.txt`

**Untouched (by design):**
- `simulator/models.py` — no schema changes
- `simulator/ws365_core.py` — no math changes
- All test files — no test modifications

---

## Reverting

Every commit is independently revertable:

```bash
git log --oneline | grep perf:    # list perf commits
git revert <commit-hash>           # undo one step
git push heroku main               # redeploy
```

The commits, newest first:

```
5ba8026  perf: early-break GW on zero-slope + cut convergence cycles 3->2
5bfaa9c  perf: halve inner iteration counts in _balance_heat_sectors_after_ws
f2147ef  perf: early-exit on already-balanced state for 4 orchestrator paths
060e519  deploy: fix Heroku Redis TLS cert verification + pin Python 3.12
5c67ddf  deploy: Redis cache backend + django-redis for Heroku
9243933  perf: cache pure compute in get_ws_365_data (Step 1.7)
ebabf43  perf: cache global lookups in _auto_context_from_tokens (Step 1.6)
8b8ff2d  perf: lazy lookup cache in _build_context with strict parity (Step 1.3)
e690bee  perf: bulk-load sector totals in _get_sector_totals (Step 1.5)
639851a  perf: cache calculate_bilanz_data output per CalculationRun (Step 1.4)
568d43f  perf: idempotent short-circuit for recalc functions (Step 1.2)
```

---

## What's left on the roadmap (not urgent)

These were considered and deferred. None are required for the current perf target.

1. **NumPy-vectorize the 365-day compute loop** — 18 list comprehensions in `ws365_core.py`. Current ~45 ms → ~5 ms. Marginal after Step 1.7 caches it.
2. **Signal cascade dedup** — multiple `on_commit` calls in one transaction each fire full recalcs. Could consolidate via a queue flag.
3. **First-class `Sector` + `SectorRole` tables** — adding a 5th sector = DB row, not 18-file edit. Extensibility win, not perf.
4. **First-class `Parameter` table** — physics constants (grid loss 9.2%, η electrolysis 65%, target year 2045, country area 35,759,529 ha) become admin-editable.
5. **i18n wrap** — `USE_I18N=True` is set but zero `gettext` usage. German strings hardcoded in templates.
6. **PyPSA selective integration** — see `PYPSA_MIGRATION_RESEARCH.md` §23.

---

## For the next developer

If you need to:

**Understand why a change was made:** read this file from top to bottom.
**Deploy to Heroku:** see `HEROKU.md`.
**Revert a specific optimization:** `git revert <hash>` from the commit list above.
**Verify math hasn't regressed:** `docker compose exec -T web python manage.py test simulator.test_bb_calc simulator.test_bb_bal simulator.test_ws365_formulas simulator.test_bb_e2e simulator.test_e2e_ui_D_full_flow`.
**Add a new mutation path that bypasses signals:** call `invalidate_auto_tokens_cache()` + `invalidate_lookups_cache()` + `invalidate_ws365_cache()` + `simulator.recalc_cache.invalidate()` after the write.
**Debug slow balance:** check `heroku logs --tail -a prosim-100 --dyno worker`, look for iteration counts or cache misses.
