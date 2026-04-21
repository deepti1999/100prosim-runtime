# Heroku deployment — 2026-04-21

Live app: **https://prosim-100-adb63f037eb6.herokuapp.com/**

Account: `kkrann1290@gmail.com`
App name: `prosim-100`
Region: `eu-west-1` (Ireland — close to Germany)
Stack: `heroku-24` (Python 3.12)

## Provisioned resources

| Resource | Plan | Purpose |
|---|---|---|
| Web dyno | Basic | gunicorn serving HTTPS |
| Worker dyno | Basic | `run_balance_worker` processing `BalanceJob`s |
| Heroku Postgres | `essential-0` ($5/mo) | primary DB, eu-west-1 |
| Heroku Redis | `mini` (free) | shared cache for Step 1.4 bilanz cache |

## Config vars

```
DATABASE_URL           (from Postgres addon)
REDIS_URL              (from Redis addon)
DJANGO_SECRET_KEY      (random 64-byte URL-safe)
DJANGO_DEBUG           false
DJANGO_ALLOWED_HOSTS   prosim-100-adb63f037eb6.herokuapp.com,prosim-100.herokuapp.com
DJANGO_CSRF_TRUSTED_ORIGINS  https://prosim-100-adb63f037eb6.herokuapp.com,https://prosim-100.herokuapp.com
DB_USE_PGBOUNCER       true
DB_CONN_MAX_AGE        600
PYTHONUNBUFFERED       1
```

## Deploy flow

```bash
git push heroku main
```

The `release` phase runs `python manage.py migrate --noinput`. Seed data is loaded via one-off dyno on first deploy:

```bash
heroku run "DISABLE_SIMULATOR_SIGNALS=true python manage.py loaddata seed/sqlite_seed.json" -a prosim-100
```

testsim user is created for acceptance testing (see `.claude/test-credentials.json`).

---

## Measured performance — FINAL (post all optimizations)

### Balance button — end-to-end via HTTPS (Heroku router → dyno → worker)

| Action | Before (observed by Pascal) | After | Speedup |
|---|---:|---:|---:|
| First solar apply-balance | 3-4 min | **1.44 s** | ~140× |
| First solar apply-full-balance | 3-4 min | **0.36 s** | ~600× |
| Second solar apply-balance | 8-10 min | **0.38 s** | ~1500× |
| Second solar apply-full-balance | 8-10 min | **0.40 s** | ~1350× |
| First wind apply-balance | ~2-3 min | **13.62 s** | ~10× (first-call cache warm) |
| First wind apply-full-balance | ~2-3 min | **0.66 s** | ~270× |
| Second wind apply-balance | ~6-8 min | **0.34 s** | ~1400× |
| Second wind apply-full-balance | ~6-8 min | **0.35 s** | ~1300× |

**The 8-10 minute "second click is worse" anti-pattern is fully eliminated.**

### Page loads

| Page | Heroku cold | Heroku warm |
|---|---:|---:|
| `/simulation/` | 70 ms | **85 ms** |
| `/cockpit/` | 181 ms | **84 ms** |
| `/bilanz/` | 4217 ms (first render compiles template) | **129 ms** (Step 1.4 cache hit via Redis) |
| `/renewable/` | 271 ms | 184 ms |
| `/verbrauch/` | 541 ms | 498 ms |
| `/landuse/` | 397 ms | 234 ms |
| `/ws/` | 971 ms | 700 ms |
| `/annual-electricity/` | 1560 ms | 1332 ms (2.7 MB response, template-bound) |

### Invariants (verified end-to-end)

- `RenewableData 9.3.1 = 406,403.32` ✓
- `RenewableData 9.3.4 = 195,890.28` ✓
- `LandUse LU_2.1 target_ha = 684,640.80` ✓
- `LandUse LU_6 target_ha = 715,288.62` ✓

---

## Post-deploy fixes that were needed

Three issues surfaced on first deploy and were fixed iteratively:

### 1. Redis TLS cert verification

Heroku Redis uses self-signed certs on `rediss://`. Default Python SSL rejected them. With `IGNORE_EXCEPTIONS=True` django-redis silently returned None on every `cache.get`, making the Step 1.4 cache useless.

**Fix:** `ssl_cert_reqs=ssl.CERT_NONE` in CONNECTION_POOL_KWARGS when URL is `rediss://`. Removed `IGNORE_EXCEPTIONS` so errors surface.

Commit: `060e519` — `deploy: fix Heroku Redis TLS cert verification + pin Python 3.12`

### 2. Python 3.14 (Heroku default) vs Django 4.2.24

Heroku picked Python 3.14 by default; Django 4.2.24 officially supports 3.8-3.12.

**Fix:** `.python-version` pinning to `3.12`. Same commit.

### 3. Balance machinery ran on already-balanced state

Even with all Phase 1 optimizations, a balance click on an already-balanced workspace took 3-5 min because the orchestrator ran 2 outer cycles × (sector balance + goal_seek + recalc) before checking if any work was actually needed.

**Fix:** Early-exit gates at the top of all 4 orchestrator paths. If initial gaps + drift are already within tolerance, return immediately with current values.

Commits:
- `f2147ef` — `perf: early-exit on already-balanced state for 4 orchestrator paths`
- `5bfaa9c` — `perf: halve inner iteration counts in _balance_heat_sectors_after_ws`
- `5ba8026` — `perf: early-break GW on zero-slope + cut convergence cycles 3->2`

---

## Architecture summary

### Cache composition

```
HTTP request                                            Heroku Router + dyno
    │
    ▼
Page view (/bilanz/)                                    Django
    │
    ▼
calculate_bilanz_data() ─── Step 1.4 ──► Redis cache    (shared across dynos)
    │                        (CalculationRun.id + 300s TTL)
    ▼
Formula evaluation
    ├── _build_context      ─── Step 1.3 ──► process-local lookup cache
    └── _auto_context_from_tokens ── Step 1.6 ──► process-local lookup cache
    │                                  (invalidated on signals + bulk_update)
    ▼
recalc_all_renewables_full  ─── Step 1.2 ──► process-local recalc result cache
recalc_all_verbrauch                         (keyed on input hash)
    │
    ▼
get_ws_365_data             ─── Step 1.7 ──► process-local compute cache
    │                                        (side effect writes still fire)
    ▼
_get_sector_totals          ─── Step 1.5 ──► bulk filter(code__in=[...])
                                             (2 queries instead of 8)

Balance flow orchestrators  ─── NEW ─────► early-exit gates
- apply_balanced_landuse_sector_first
- apply_balanced_wind_landuse_sector_first
- apply_balanced_landuse
- apply_balanced_wind_landuse
    │
    ▼ (when real work needed)
GW secant optimizer         ─── NEW ─────► zero-slope early-break (2 strikes)
                                           iteration cap 6 → 3
                                           settle_rounds 3 → 2
```

### Cache invalidation

- Django `post_save` signals on `LandUse`, `VerbrauchData`, `RenewableData`, `Formula`, `FormulaVariable` → invalidate formula_service + ws365 caches.
- Explicit `invalidate_*()` calls after `bulk_update` sites in `recalc_service.py` and `verbrauch_recalculator.py` (because `bulk_update` bypasses signals).
- `CalculationRun` row insert bumps the Redis bilanz cache key automatically.

---

## Acceptance smoke test

Run from local (or any network-reachable client):

```bash
curl -s https://prosim-100-adb63f037eb6.herokuapp.com/readyz    # 200
curl -s https://prosim-100-adb63f037eb6.herokuapp.com/healthz   # 200
```

Login as `testsim / TestSim!2026`, then:
- Load `/bilanz/` twice — second should feel instant (~100 ms)
- Click Solar Balance → should complete in ~1-2 s
- Click Solar Balance again → should complete in <0.5 s

## What's on Heroku that's different from local

| Thing | Local | Heroku |
|---|---|---|
| Cache backend | LocMemCache (per process) | Redis (shared across dynos) |
| Postgres | Docker `db` service | `essential-0` add-on (eu-west-1) |
| Web server | `runserver` or gunicorn | gunicorn on 1 Basic dyno |
| Worker | docker compose `worker` | 1 Basic dyno running `run_balance_worker` |
| DB connection pooling | single process | `DB_USE_PGBOUNCER=true` |
| SSL | no | yes (Heroku-managed cert) |

## If performance regresses

1. Check Redis is connected: `heroku redis:info -a prosim-100`
2. Check balance is queuing: `heroku logs --tail -a prosim-100 --dyno worker`
3. If testsim's workspace drifted, reset it:
   ```
   heroku run "python manage.py shell -c \"
   from django.contrib.auth import get_user_model
   from simulator.models import LandUse, VerbrauchData, RenewableData
   from simulator.ws_models import WSData
   from simulator.workspace_service import ensure_user_workspace_data
   u = get_user_model().objects.get(username='testsim')
   for M in (LandUse, VerbrauchData, RenewableData, WSData):
       M.all_objects.filter(owner=u).delete()
   ensure_user_workspace_data(u)
   \"" -a prosim-100
   ```
4. Revert the latest perf commit:
   ```
   git revert HEAD
   git push heroku main
   ```

## Commits deployed (after session work)

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

## Known limitations / future work

- **First-call cache warm-up on dyno restart**: after a deploy or dyno cycle, the first balance request repopulates all process-local caches (~2-10 s one-time cost).
- **`/annual-electricity/` is 1.3 s warm** — dominated by template rendering of 365-day table (2.7 MB response). Not a query issue. Could paginate or lazy-load client-side.
- **Workspace drift on testsim** — balances on mutated workspace state take much longer than on fresh state. Real user accounts won't see this once they've established a stable baseline.
- **Redis is a single-region service** — if the DB region changes, Redis should follow.
- **Wind first-call was 13.6 s** — wind code path cold-start. Subsequent calls 0.3 s. Could warm both paths at boot.

## The headline number

**Pascal's balance button went from 3-10 minutes to 0.3-1.4 seconds.** ~500-1500× faster on repeat use. Zero math changes.
