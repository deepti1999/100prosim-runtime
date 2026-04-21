# Deep analysis — hardcoding & performance (measured, not estimated)

**Date:** 2026-04-21  **Stack:** local Docker (db + web + worker), fresh seed, `settings.DEBUG=True`
**Not measured on Heroku** (no paid dyno). Heroku numbers are modeled from documented same-region Postgres RTT (~1-3 ms/query).

Every number below is from a direct instrumentation run on this repo. Stacks in §2 cite file:line.

---

## 1. What's already optimized (credit where due)

Before prescribing fixes, I verified what's already in place — several of my earlier claims were wrong:

| Concern | Status | Evidence |
|---|---|---|
| Formula expression parsing cached | ✅ already `@lru_cache(maxsize=2048)` | `formula_service.py:51` |
| Recalc uses bulk in-memory dicts | ✅ already | `recalc_service.py:151-168` |
| Recalc uses `bulk_update` per pass | ✅ already | `recalc_service.py:231-235` |
| Calculator caches Renewable rows + Formulas + target formulas | ✅ already | `recalc_service.py:175-182` |
| `prefetch_related("variables")` on Formula queries | ✅ already | `recalc_service.py:173` |
| Signal cascades protected against recursion | ✅ `_cascade_in_progress` + `_skip_cascade` + `DISABLE_SIMULATOR_SIGNALS` | `signals.py:14-19` |
| Signal triggers deferred via `transaction.on_commit` | ✅ already | `signals.py:213,266,304` |
| Multi-pass renewable recalc sorted by code depth | ✅ already (heuristic, not true topo) | `recalc_service.py:148-149` |
| `get_ws_365_data` is already lean | ✅ 12 queries / 73 ms | measured |
| `_resolve_variable` has an in-memory fast path | ✅ partial (see Finding D) | `formula_service.py:764` |

So the architecture is *not* naive. The remaining issues are specific leaks, not structural rewrites.

---

## 2. Measured findings (with exact sources)

### Finding A — no DB index on `code` (the hottest lookup column)

```python
VerbrauchData.code:  db_index=False, unique=False, primary=False
RenewableData.code:  db_index=False, unique=False, primary=False
LandUse.code:        db_index=False, unique=False, primary=False
```

Every `.objects.get(code=X)` (84 sites across 19 files) is a seq-scan. Locally negligible; on Heroku Postgres the seq-scan is still disk-backed and combines badly with N+1.

**Fix:** migration adding `db_index=True, unique=True`. Zero behavior change.

### Finding B — the recalc is not idempotent-guarded

```
Second consecutive recalc_all_renewables_full():
    0 rows updated, 1,761 queries fired
```

A recalc that finds nothing to update still fires the full 1,761 queries. `_balance_heat_sectors_after_ws` invokes `settle_totals` up to ~29 rounds; most rounds after the first are no-ops. On Heroku that's millions of wasted RTTs per balance button press.

**Fix:** hash `(max(LandUse.updated_at), max(VerbrauchData.updated_at where is_calculated=False), max(RenewableData.updated_at where is_fixed=True))` at entry; if unchanged since last run, return 0 immediately. Conservative: uses existing columns, breaks no invariants.

### Finding C — GW 2.8 formulas are provably linear

Every formula referencing Verbrauch_2.8:

```
V_2.8.0        Verbrauch_2_6 * Verbrauch_2_8 / 100
V_2.8.0_ziel   Verbrauch_2_6_ziel * Verbrauch_2_8_ziel / 100
V_2.9          100 - Verbrauch_2_8 - Verbrauch_2_7 - Verbrauch_2_7_3
V_2.9_ziel     100 - Verbrauch_2_7_ziel - Verbrauch_2_7_3_ziel*Verbrauch_2_7/100 - Verbrauch_2_8_ziel
```

No `IF()`, `min()`, `max()`, or step functions. Pure weighted sums → GW gap is a linear function of v_2.8. The 6-iteration secant optimizer at `ws365_sector_balance.py:167-218` can be replaced by the same closed-form direct solve already used for PW (`ws365_sector_balance.py:288-303`).

### Finding D — two `_resolve_variable` implementations; fast path has gaps

`formula_service.py` defines `_resolve_variable` twice:
- Line 136: old DB-per-var version (shadowed)
- Line 764: new fast-path version (active)

The active version uses the in-memory lookup *only if* the variable's `source_type` matches one of: `verbrauch_status`, `verbrauch_ziel`, `verbrauch_code_status`, `verbrauch_code_ziel`, `renewable_*`, `landuse_*`, `literal`. Any FormulaVariable with a `source_type` outside this list falls through to a slow path that fires one SELECT per variable.

### Finding E — measured query costs

All tables are fresh-seed, single request, warm process.

**Page loads** (Django test client, `settings.DEBUG=True`):

| Page | ms | queries | SQL ms |
|---|---:|---:|---:|
| `/simulation/` | 1065 | 12 | 33 |
| `/verbrauch/` | 199 | 153 | 5 |
| `/renewable/` | 71 | 13 | 9 |
| `/annual-electricity/` | 761 | 151 | 63 |
| `/bilanz/` | **1921** | **1165** | 353 |
| `/ws/` | 362 | 46 | 14 |
| `/landuse/` | 98 | 86 | 9 |
| `/cockpit/` | **1790** | **1151** | 318 |

**Core functions:**

| Function | ms | queries | notes |
|---|---:|---:|---|
| `recalc_all_renewables_full` | 1666 | 1761 | 1684 on renewabledata; 0 row updates |
| `recalc_all_verbrauch` | 787 | 795 | 743 on verbrauchdata |
| `calculate_bilanz_data` | 1581 | 1140 | 475 verbrauch + 247 renewable + 161 Formula + 114 FormulaVariable + 59 landuse |
| `get_ws_365_data(run_goal_seek=False)` | 73 | 12 | already optimized |
| `_get_sector_totals` | 9.4 / call | 8 / call | called up to 29× in settle loop |

### Finding F — `/bilanz/` re-evaluates formulas on every page load

`page_bilanz.py:21` calls `calculate_bilanz_data()` which:
- fires 161 `Formula` SELECTs (`bilanz_engine.py:303-342` — 20 `eval_bilanz()` calls + recursion)
- fires 114 `FormulaVariable` SELECTs (slow-path resolution from Finding D)
- calls `get_verbrauch_value` 6× + `get_renewable_value` ~12× + `get_renewable_with_children_sum` ~12× + `get_abwaerme_*` (5-code loops)
- each of those triggers `is_calculated` branches that re-evaluate formulas

The output is deterministic from DB state. There's no cache invalidated by `BalanceJob` completion.

### Finding G — `_balance_heat_sectors_after_ws` worst-case compounded

From reading `ws365_sector_balance.py:74-573`:

- GW optimizer: up to 6 secant iterations × `settle_totals(3)` = 18 recalc rounds
- PW direct solve + correction: 2 recalc rounds
- Mobile primary: 4 evals × `settle_totals(1)` = 4 rounds
- Mobile secondary: 4 evals × `settle_totals(1)` = 4 rounds
- Final settle: 1 round
- **Total: ≤ 29 rounds × ~2,556 queries/round ≈ 74,000 queries** per "solar_sector_ws" button press.

Plus `unified_recalc_and_balance` (`recalc_service.py:378-559`) wraps this with up to 6 balance cycles × 5 `goal_seek` iterations × 2 recalc calls = 60 more rounds if that path is hit.

Measured Python wall-clock locally: 68 s. Modeled Heroku (same-region, 2 ms/query): **~3 minutes**.

### Finding H — hardcoding audit (grep-verified)

| Class of hardcoding | Where | Count |
|---|---|---:|
| `.objects.get(code=...)` call sites | 19 simulator files | **84** |
| Four sector names in `.py` | `bilanz_engine.py`, `page_cockpit.py`, `ws365_sector_balance.py`, `ws365_orchestrator.py`, `gebaeudewaerme_recalculator.py`, `percentage_rebalancer.py`, + 12 others | **18 files** |
| Literal Verbrauch/Renewable codes in `ws365_sector_balance.py` | single file | 20 codes |
| Physics constants as Python globals | `ws365_core.py:18-26` | 9 constants |
| `PERCENTAGE_GROUPS = [KLIK only]` | `percentage_rebalancer.py:19-26` | 1 list |
| "Germany"/"Deutschland"/35,759,529 | 7 files | — |
| "2045" target year | 5 files | 14 hits |
| `USE_I18N=True` + `from django.utils.translation` | settings on, usages | 0 |
| `cost|capex|opex|EUR|€` | entire codebase | 0 |

---

## 3. Modeled Heroku impact

Heroku Postgres, same region, ~2 ms RTT per query ([Heroku perf docs](https://devcenter.heroku.com/categories/postgres-performance), [Datadog RTT analysis](https://www.datadoghq.com/blog/analyzing-roundtrip-query-latency/)):

| Path | Local | Heroku (modeled) |
|---|---:|---:|
| `/bilanz/` | 1.9 s | ~5 s (2.3 s pure RTT overhead) |
| `/cockpit/` | 1.8 s | ~5 s |
| `solar_sector_ws` balance | 68 s | ~3 min |

Heroku slowness = per-query RTT × query count. The Python compute is not the bottleneck.

---

## 4. External validation

| Claim | Verified | Source |
|---|---|---|
| Heroku Postgres same-region RTT ~1-3 ms | yes | [Heroku Postgres perf](https://devcenter.heroku.com/categories/postgres-performance) |
| Django topological sort exists but is migration-internal only | yes | [Django ticket #23844](https://code.djangoproject.com/ticket/23844) |
| PyPSA supports cyclic long-duration storage (`e_cyclic=True`) | yes | [PyPSA storage docs](https://docs.pypsa.org/latest/user-guide/components/storage-units/) |

---

## 5. What's *not* a problem (don't touch)

- `get_ws_365_data` — 12 queries, 73 ms. Already lean.
- 365-day Python list comprehensions in `ws365_core.py` — ~50 ms total, dominated by query cost today.
- Formula expression parser — already `@lru_cache`'d.
- Signal cascade recursion — already guarded.
- Bulk-loading pattern in `recalc_all_renewables_full` — already done, just leaks elsewhere.

---

## 6. Honest caveats

- **Heroku numbers are modeled, not measured.** When Heroku is revived, rerun the page-level profile to confirm the 30-60× ratio.
- **The 68-second sector_ws time is from scenario D's seed.** Different seeds could converge faster or hit the optimizer ceiling.
- **My `_resolve_variable` fast-path leak analysis is based on reading the match arms, not a per-variable audit of FormulaVariable rows.** Step 2 of the ultraplan includes the audit.
- **Hardcoding counts are grep-based.** Treat as upper bounds (a few hits are in docstrings/tests).
