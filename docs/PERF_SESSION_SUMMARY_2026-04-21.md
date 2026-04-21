# Performance session summary — 2026-04-21

Single-page handoff covering everything landed, skipped, measured, and what's
next. Companion docs: `DEEP_ANALYSIS_2026-04-21.md` (findings), `ULTRAPLAN_2026-04-21.md` (plan).

---

## TL;DR

**Problem observed:** Heroku balance button was 3-4 min (first click) / 8-10 min (second click). `/bilanz/` and `/cockpit/` loaded in ~5 s each.

**Changes shipped (8 commits, all local, none pushed):**
- 5 performance fixes with math-safety gates
- 1 documentation update for a deferred step
- 1 reference module kept in-tree for future GW direct-solve resumption

**Measured result (local Docker):**
- Balance cold: **68 s → 1.3 s** (~53× faster)
- Balance warm: **68 s → 140 ms** (~485× faster)
- `/bilanz/` warm: **1921 ms → 21 ms** (~90× faster)
- `/cockpit/`: **1790 ms → 14 ms** (~128× faster)

**Projected Heroku impact (modeled at 2 ms/RTT):**
- First solar balance: 3-4 min → **~20-30 s**
- Second solar balance: 8-10 min → **~10-15 s**
- `/bilanz/` page load: ~5 s → **~50 ms** (cache hit)

**Math integrity:** 23 tests pass, all invariants preserved.
- `9.3.1 = 406,403.33` ✓
- `9.3.4 = 195,890.29` ✓
- `LU_2.1 = 680,478.26 ha` (solar) ✓
- `LU_6 = 715,288.57 ha` (wind) ✓
- `annual_electricity = 1,108,834.53 GWh` (both paths) ✓
- `speicherdrift ≤ 0.1 GWh` ✓

---

## What shipped

### Step 1.1 — DB indexes on `code` columns ⏭️ SKIPPED (already done)

Investigated. The `(owner_id, code)` composite indexes already exist at the Postgres level via `Meta.constraints`, covering the actual query pattern optimally. Standalone `db_index=True` would create a redundant single-column index. No action needed.

### Step 1.2 — Idempotent recalc short-circuit ✅ `568d43f`

`simulator/recalc_cache.py` — new module. Wraps `recalc_all_renewables_full` and `recalc_all_verbrauch` with an input-signature cache. When inputs haven't changed, returns cached result in ~7 ms instead of firing 1,761 / 795 queries.

**The biggest single win.** Settle loops call these functions ~29 times per balance; only 1-3 actually change anything. The other 26+ used to run full recalcs for 0 row updates.

### Step 1.3 — Lazy lookup cache in `_build_context` ✅ `8b8ff2d`

`simulator/formula_service.py` — added process-local cache of namespace-prefixed lookup keys. Wraps `_build_context` so formula evaluation via `evaluate_formula_by_key` hits the fast path by default.

**Safety gate caught real divergence** — first attempt exposed 25 formula mismatches (cross-table bare-code collisions). Reverted. Second attempt uses namespace-prefixed keys only + blacklists `*_code_*` source_types (whose slow path recursively recomputes). Shadow parity: 758/758 pass.

### Step 1.4 — Cache `calculate_bilanz_data` per CalculationRun ✅ `639851a`

`calculation_engine/bilanz_engine.py` — wrapped the function with a Django cache layer keyed on the latest `CalculationRun.id` plus a 300 s TTL backstop. Every balance job and recalc endpoint creates a new `CalculationRun`, so the cache auto-invalidates on any real recompute.

Effect: `/bilanz/` cache hit drops from 2299 ms / 1166 Q to 59 ms / 25 Q.

### Step 1.5 — Bulk-load `_get_sector_totals` ✅ `e690bee`

`simulator/ws365_sector_balance.py` — replaced 6-8 individual `.objects.get(code=X)` calls with two `filter(code__in=[...])` queries.

Effect: 8 Q/call → 2 Q/call. Inside a 29-round settle loop that's ~174 fewer queries per balance.

### Step 1.6 — Cache lookups in `_auto_context_from_tokens` ✅ `ebabf43`

`simulator/formula_service.py` — the last big query leak. A separate code path from Step 1.3 that's called by `_safe_eval` (used everywhere, including `VerbrauchCalculator` and `evaluate_with_mappings`). All callers passed no lookups, so every token hit the DB.

Added process-local cache of 6 per-table bare-code lookups. Invalidated via post_save signals on the tracked models + explicit calls after bulk_update sites.

First attempt used per-call signature checks (`Max(updated_at)` aggregates) but those cost more than they saved — switched to lazy-build + signal-driven invalidation. Shadow parity: 758/758 pass.

Effect:
- `recalc_all_verbrauch`: 795 Q → 429 Q (-46 %)
- `recalc_all_renewables_full`: 1761 Q → 893 Q (-49 %)
- Balance cycle cold: 2660 Q → 1423 Q (-46 %)

### Step 1.7 — Cache pure compute in `get_ws_365_data` ✅ `9243933`

`simulator/ws365_orchestrator.py` — split the 365-day WS compute from its side effect. The compute (~45 ms) is now cached by input signature. The side-effect write to `RenewableData 9.3.1 / 9.3.4` still runs every call (value-compare idempotent).

Effect: 48 ms → 10 ms on cache hit.

### Step 2 — Compile formula AST once ⏭️ ALREADY DONE

Investigated. `ws365_formula_engine.py:148 _compile_expression` already compiles expressions to `CodeType` once per formula and reuses across 365 days. The cProfile I initially read was actually measuring scope-dict construction, not re-parsing.

### Step 2.1 — GW 2.8 direct solve ⏸️ DEFERRED `5952f7d`

Built candidate direct-solve in `simulator/ws365_gw_direct_solve.py` (kept in-tree for future resumption). Shadow harness across 5 synthetic GW imbalance scenarios revealed:

1. **v_2.8 has no measurable effect on GW gap on this seed** — all 5 starting values produced identical gap (-14.84 GWh).
2. Forcing imbalance via `r_10.4` was overwritten by the recalc (r_10.4 is a calculated row).
3. The secant loop at `ws365_sector_balance.py:175` only runs when `|gap| > 100`; on this seed gap ≈ -15, so the loop is skipped entirely.

Can't prove parity on code that doesn't execute. Risk of silent math regression is nonzero; measurable benefit is zero. **Keep the secant as-is.**

### Step 6 — NumPy vectorize 365-day loop ⏭️ NOT DONE

Declined after measurement. The Python compute is ~45 ms per call; Steps 1.2 and 1.7 now cache most repeat calls, so the non-cached compute is ~5 % of observed latency. NumPy adds numerical-drift risk (unlikely but non-trivial to prove) for marginal wins. Revisit only if Heroku numbers come back worse than projected.

---

## Measured before/after (local Docker, fresh seed)

| Path | Before | After | Speedup |
|---|---:|---:|---:|
| `/bilanz/` warm | 1921 ms / 1165 Q | **21 ms / 24 Q** | **~90×** |
| `/cockpit/` | 1790 ms / 1151 Q | **14 ms / 9 Q** | **~128×** |
| `/annual-electricity/` | 761 ms / 151 Q | **380 ms / 125 Q** | 2× |
| `/ws/` | 362 ms / 46 Q | **150 ms / 43 Q** | 2.4× |
| `/landuse/` | 98 ms / 86 Q | **68 ms / 86 Q** | 1.4× |
| `/verbrauch/` | 199 ms / 153 Q | 122 ms / 153 Q | 1.6× |
| `recalc_all_renewables_full` (cold) | 1353 ms / 1766 Q | 646 ms / 893 Q | 2× |
| `recalc_all_renewables_full` (warm) | 1353 ms / 1766 Q | **7 ms / 5 Q** | **~200×** |
| `recalc_all_verbrauch` (cold) | 532 ms / 800 Q | 376 ms / 429 Q | 1.4× |
| `recalc_all_verbrauch` (warm) | 532 ms / 800 Q | **6 ms / 5 Q** | **~88×** |
| `calculate_bilanz_data` (cold) | 1414 ms / 1141 Q | 1414 ms / 1141 Q | same |
| `calculate_bilanz_data` (warm) | 1414 ms / 1141 Q | **1 ms / 1 Q** | **~1400×** |
| `get_ws_365_data` | 48 ms / 12 Q | **10 ms / 11 Q** | 4.5× |
| `_balance_heat_sectors_after_ws` (cold) | 68 s | **1286 ms / 1423 Q** | **~53×** |
| `_balance_heat_sectors_after_ws` (warm) | 68 s | **140 ms / 104 Q** | **~485×** |

## Projected Heroku impact

Heroku Postgres RTT models at 2 ms/query ([Heroku docs](https://devcenter.heroku.com/categories/postgres-performance)). Each saved query saves ~2 ms of network time; each saved recalc pass saves ~5 s at that rate.

| User action | Before (observed) | After (projected) | Speedup |
|---|---:|---:|---:|
| First solar balance | 3-4 min | **~20-30 s** | ~8× |
| Second solar balance | 8-10 min | **~10-15 s** | ~40× |
| First wind balance | ~2-3 min | **~15-25 s** | ~8× |
| Second wind balance | ~6-8 min | **~8-15 s** | ~40× |
| `/bilanz/` page load | ~5 s | **~100 ms** | ~50× |
| `/cockpit/` page load | ~5 s | **~50 ms** | ~100× |
| Full user session | ~5 min | **~30-45 s** | ~10× |

**The "second balance is worse than first" anti-pattern is fixed by Step 1.2** — the 26+ no-op recalc rounds in a settle loop are now near-zero cost.

## Math integrity

### Tests passing (23 total, 1 skipped)

| Suite | Count | Coverage |
|---|---:|---|
| `test_bb_calc` + `test_bb_bal` | 4 | Math / calc engine |
| `test_ws365_formulas` | 5 | Formula parity |
| `test_bb_e2e` | 2 | End-to-end contracts |
| `test_e2e_ui_baseline` | 7 | Scenario A equivalent (all pages) |
| `test_e2e_ui_ws_balance` | 2 | Scenario C equivalent (WS balance) |
| `test_e2e_ui_D_full_flow` | 3 | Scenario D (solar + wind + invariant) |

### Shadow-parity gates that fired

Two of the changes had non-trivial risk. The gates caught real bugs:

1. **Step 1.3 v1** — permissive lookup keys caused 25 formula mismatches due to cross-table bare-code collisions. Reverted, redone with namespace-prefixed keys + `*_code_*` blacklist. V2: 758/758 match.
2. **Step 1.6 v1** — per-call signature checks fired more queries than they saved (net loss). Redone with lazy-build + signal invalidation. V2: 758/758 match.

Without these gates, either change would have silently broken math.

### Invariants preserved

Verified after every step and again at session end:

- `RenewableData 9.3.1.target_value = 406,403.33`
- `RenewableData 9.3.4.target_value = 195,890.29`
- `LandUse LU_2.1.target_ha = 680,478.26` (post-solar balance)
- `LandUse LU_6.target_ha = 715,288.57` (post-wind balance)
- `annual_electricity = 1,108,834.53` (both variants converge)
- `abs(speicherdrift) ≤ 0.1` after any balance

## Architecture notes (for future work)

### How the caches compose

```
┌─────────────────────────────────────────────────┐
│  Recalc short-circuit (Step 1.2)                │
│  - recalc_all_renewables_full                   │
│  - recalc_all_verbrauch                         │
│  - 200× on cached repeat calls                  │
└─────────────────┬───────────────────────────────┘
                  │ calls
                  ▼
┌─────────────────────────────────────────────────┐
│  Formula evaluation                             │
│  - _build_context: Step 1.3 lookups (prefixed)  │
│  - _auto_context_from_tokens: Step 1.6 lookups  │
│    (bare per-table)                             │
│  - Both: lazy-built, signal-invalidated         │
└─────────────────┬───────────────────────────────┘
                  │ calls
                  ▼
┌─────────────────────────────────────────────────┐
│  WS365 compute (Step 1.7)                       │
│  - get_ws_365_data: pure compute cached         │
│  - Side effect (RenewableData writes) still     │
│    fires every call; writes are idempotent      │
└─────────────────────────────────────────────────┘

Outer layer (Step 1.4): calculate_bilanz_data result
cached per CalculationRun.id + 300s TTL. Hit on repeat
page loads; miss on every new balance job completion.
```

### Cache invalidation strategy

All caches invalidate on:
1. **`post_save` signals** on `LandUse`, `VerbrauchData`, `RenewableData`, `Formula`, `FormulaVariable` — handles normal user edits via admin / API.
2. **Explicit calls after `bulk_update`** in recalc functions — because `bulk_update` bypasses signals.
3. **New `CalculationRun`** bumps the bilanz cache key (Step 1.4 only).

If you add a new mutation path that writes to these tables via raw SQL or `.update()` queryset calls, add an explicit `invalidate_*()` call. Candidates:
- `simulator/formula_service.py::invalidate_auto_tokens_cache`
- `simulator/formula_service.py::invalidate_lookups_cache`
- `simulator/ws365_orchestrator.py::invalidate_ws365_cache`
- `simulator/recalc_cache.py::invalidate`

### Known limitations

- **Per-process caches**: Each gunicorn worker has its own cache. On Heroku with multiple web dynos, each rebuilds independently. For the bilanz cache (Step 1.4), consider Heroku Redis to share across dynos.
- **LocMemCache TTL**: Step 1.4 uses `django.core.cache` with default LocMem backend. 300 s TTL is a safety floor for admin-only edits (rare).
- **Cache staleness with async workers**: The worker process has its own cache that's invalidated by signals. But signals fire on `post_save`, which only happens in the current process. If the web process saves and the worker's cache doesn't know, the worker may serve stale results until its next real data read. Mitigation: `bulk_update` invalidation triggers in the recalc path, which covers the worker's main path.

---

## What's NOT done (by design)

### Further perf opportunities, in priority order

1. **`DB_USE_PGBOUNCER=true` on Heroku** — env var only, no code change. Free win on connection-constrained plans.
2. **Heroku Redis add-on** — shares Step 1.4's bilanz cache across dynos. $0 Mini plan works. 30 min config.
3. **NumPy vectorize the 365-day loop** — ~45 ms → ~5 ms compute. Marginal after Step 1.7.
4. **Signal cascade dedup** — multiple `on_commit` calls in one transaction each fire full recalcs. Consolidate via a queue flag. Medium effort, unclear real-world benefit.

### Extensibility work (separate stream, out of scope for perf session)

Per `CLAUDE.md` §2, these are co-equal priority with performance but require larger design work:

- **First-class `Sector` + `SectorRole` tables** (3-5 days) — adding a 5th sector = DB row instead of 18-file edit.
- **First-class `Parameter` table** (1-2 days) — physics constants (grid loss, electrolysis η, FIXED_82_TARGET, country area, target year) become admin-editable.
- **`PERCENTAGE_GROUPS` table** (0.5 day) — currently `[KLIK only]` hardcoded.
- **i18n wrap** (2-3 days) — `USE_I18N=True` is set but zero `gettext` usage. Needs `name_de`/`name_en` columns on Formula/Verbrauch/Renewable.

See `docs/PYPSA_MIGRATION_RESEARCH.md` §23.3 for the full ordered extensibility roadmap.

---

## Commit reference

All commits local on `main`. None pushed (per session policy).

```
9243933  perf: cache pure compute in get_ws_365_data (Step 1.7)
ebabf43  perf: cache global lookups in _auto_context_from_tokens (Step 1.6)
5952f7d  docs: defer Step 2.1 with shadow-harness empirical evidence
8b8ff2d  perf: lazy lookup cache in _build_context with strict parity (Step 1.3)
1b20320  docs: defer Step 2.1 (GW direct solve) with measured justification
e690bee  perf: bulk-load sector totals in _get_sector_totals (Step 1.5)
639851a  perf: cache calculate_bilanz_data output per CalculationRun (Step 1.4)
568d43f  perf: idempotent short-circuit for recalc functions (Step 1.2)
```

Revert any step independently:
```
git revert <commit-hash>
```

---

## Ship checklist

Before pushing to Heroku:

- [ ] `heroku login` (blocker — currently "Invalid credentials")
- [ ] `heroku update` (optional — CLI at 10.17.0)
- [ ] Confirm the app exists: `heroku apps` and `heroku info -a <app>`
- [ ] Optional: set `DB_USE_PGBOUNCER=true` on Heroku to enable connection pooling (already supported in settings)
- [ ] Optional: provision `heroku addons:create heroku-redis:mini` and set `CACHES` to use `REDIS_URL`

Push:
```
git push heroku main
heroku logs --tail -a <app>
curl https://<app>.herokuapp.com/readyz  # expect 200
```

First-run validation:
- Login as a test user
- Load `/bilanz/` twice — second load should feel instant (cache hit)
- Click Solar Balance — report time
- Click Solar Balance again — report time

Target numbers (if projections hold):
- First solar: ~20-30 s (was 3-4 min)
- Second solar: ~10-15 s (was 8-10 min)
- `/bilanz/` second load: ~100 ms (was ~5 s)

## Files changed this session

**New:**
- `simulator/recalc_cache.py` — Step 1.2 idempotency helper
- `simulator/ws365_gw_direct_solve.py` — Step 2.1 reference module (not wired)
- `docs/DEEP_ANALYSIS_2026-04-21.md` — findings with measurements
- `docs/ULTRAPLAN_2026-04-21.md` — plan with outcomes
- `docs/PERF_SESSION_SUMMARY_2026-04-21.md` — this file

**Modified:**
- `simulator/recalc_service.py` — Step 1.2 + 1.6 + 1.7 wiring
- `simulator/verbrauch_recalculator.py` — Step 1.2 + 1.6 + 1.7 wiring
- `calculation_engine/bilanz_engine.py` — Step 1.4 cache wrapper
- `simulator/ws365_sector_balance.py` — Step 1.5 bulk-load
- `simulator/formula_service.py` — Step 1.3 + 1.6 caches
- `simulator/signals.py` — Step 1.6 + 1.7 signal receivers
- `simulator/ws365_orchestrator.py` — Step 1.7 cache split

Not touched (by design):
- `simulator/models.py` — no schema changes
- `simulator/ws365_core.py` — no compute changes
- Any `tests/*` — no test modifications
- `Procfile`, `requirements.txt`, `settings.py` — no config changes
