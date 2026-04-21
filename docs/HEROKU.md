# Heroku deployment guide

**Live app:** https://prosim-100-adb63f037eb6.herokuapp.com/
**App name:** `prosim-100`
**Owner:** `kkrann1290@gmail.com`
**Region:** `eu-west-1` (Ireland)
**Stack:** `heroku-24` / Python `3.12`

For *why* the optimizations exist and what they do, see `PERFORMANCE.md`.

---

## Architecture on Heroku

| Resource | Plan | Cost | Purpose |
|---|---|---:|---|
| Web dyno | Basic | ~$7/mo | gunicorn serving HTTPS requests |
| Worker dyno | Basic | ~$7/mo | `run_balance_worker` processing queued `BalanceJob` rows |
| Heroku Postgres | `essential-0` | $5/mo | primary database (in-region) |
| Heroku Redis | `mini` | free | shared cache across dynos (Step 1.4 bilanz cache) |

**Monthly spend: ~$20/month.**

## Required environment variables

```
DATABASE_URL                  (auto-set by Postgres addon)
REDIS_URL                     (auto-set by Redis addon)
DJANGO_SECRET_KEY             random 64-byte URL-safe string
DJANGO_DEBUG                  false
DJANGO_ALLOWED_HOSTS          prosim-100-adb63f037eb6.herokuapp.com,prosim-100.herokuapp.com
DJANGO_CSRF_TRUSTED_ORIGINS   https://prosim-100-adb63f037eb6.herokuapp.com,https://prosim-100.herokuapp.com
DB_USE_PGBOUNCER              true
DB_CONN_MAX_AGE               600
PYTHONUNBUFFERED              1
```

View current config: `heroku config -a prosim-100`.

## Python version pin

`.python-version` contains `3.12`. Don't remove — Django 4.2.24 officially supports 3.8-3.12, not the Heroku default (3.14).

---

## Routine operations

### Deploy

```bash
git push heroku main
```

The `release` phase (`Procfile` line 1) runs migrations automatically. Watch the build with `heroku logs --tail -a prosim-100`.

### Initial seed loading (first deploy only)

```bash
heroku run "DISABLE_SIMULATOR_SIGNALS=true python manage.py loaddata seed/sqlite_seed.json" -a prosim-100
```

### Creating the test user

```bash
heroku run "python manage.py shell -c \"
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(username='testsim', defaults={'email':'testsim@prosim-100.local','is_active':True})
u.set_password('TestSim!2026')
u.is_active = True
u.save()
print(f'testsim {\\\"created\\\" if created else \\\"updated\\\"}: id={u.id}')
\"" -a prosim-100
```

Credentials: `testsim / TestSim!2026`.

### Check dyno status

```bash
heroku ps -a prosim-100
```

### Tail logs

```bash
heroku logs --tail -a prosim-100                    # all sources
heroku logs --tail -a prosim-100 --dyno worker      # worker only
heroku logs --tail -a prosim-100 --source heroku    # router only
```

### Restart

```bash
heroku restart -a prosim-100
```

---

## Smoke test (after every deploy)

```bash
curl -s -o /dev/null -w "readyz: %{http_code}\n" https://prosim-100-adb63f037eb6.herokuapp.com/readyz
curl -s -o /dev/null -w "healthz: %{http_code}\n" https://prosim-100-adb63f037eb6.herokuapp.com/healthz
```

Both should return `200`.

Then manually:
1. Log in at `https://prosim-100-adb63f037eb6.herokuapp.com/login/` as `testsim / TestSim!2026`.
2. Visit `/bilanz/` — second load should feel instant (~100-200 ms).
3. Go to `/ws/` and click Solar Balance — both steps should complete in ~1-2 s combined.
4. Click Solar Balance again — should complete in <0.5 s.

---

## If something goes wrong

### Performance regresses

**Check Redis:**

```bash
heroku redis:info -a prosim-100
heroku redis:cli -a prosim-100   # then inside: PING -> expect "PONG"
```

**Check balance jobs are processing:**

```bash
heroku logs --tail -a prosim-100 --dyno worker
```

Look for `Processing ... / Completed ...` lines.

**Check config:**

```bash
heroku config -a prosim-100
```

All env vars from the required list above must be present.

### testsim's workspace drifts

If balance times blow up specifically for testsim (real user accounts won't see this), reset the workspace:

```bash
heroku run "python manage.py shell -c \"
from django.contrib.auth import get_user_model
from simulator.models import LandUse, VerbrauchData, RenewableData
from simulator.ws_models import WSData
from simulator.workspace_service import ensure_user_workspace_data
u = get_user_model().objects.get(username='testsim')
for M in (LandUse, VerbrauchData, RenewableData, WSData):
    M.all_objects.filter(owner=u).delete()
ensure_user_workspace_data(u)
print('testsim workspace reset')
\"" -a prosim-100
```

### Deploy failed at build

Check the build logs (shown during `git push heroku main`). Common causes:

- Missing dep in `requirements.txt` — add it, commit, push again.
- Python version mismatch — `.python-version` should say `3.12`.
- Migrations failed — check the release phase output; may need to fix the migration or run manually.

### Roll back

Heroku keeps the last N slug versions.

```bash
heroku releases -a prosim-100        # list all
heroku rollback v<N> -a prosim-100   # roll back to a specific version
```

Or revert in git:

```bash
git revert <commit-hash>
git push heroku main
```

---

## Scaling

Current setup: 1 web dyno + 1 worker dyno, both Basic tier. Upgrade paths:

```bash
# Scale up the web to handle more concurrent users
heroku ps:resize web=standard-1x -a prosim-100      # $25/mo, 512 MB RAM
heroku ps:scale web=2 -a prosim-100                 # 2 web dynos (Redis cache shares)

# Scale worker for faster balance completion under load
heroku ps:scale worker=2 -a prosim-100              # 2 concurrent balance jobs
```

Note: with multiple web dynos, Redis (Step 1.4's bilanz cache) is shared, so they'll still benefit from cache hits across dynos.

---

## Monitoring suggestions (not yet set up)

- **Heroku metrics dashboard** — built-in, shows response time, throughput, memory.
- **Add-on suggestions if load grows:**
  - Papertrail / Logtail for log search
  - Scout APM / New Relic for detailed request profiling
  - Sentry for error tracking

None of these are necessary for the current scale.

---

## Known characteristics

- **First-call cache warm-up**: after a deploy or dyno cycle, the first request of each type (page load, balance type) takes 2-15 s longer while process-local caches populate. Subsequent calls are fast.
- **`/annual-electricity/` is slower than others** (~1.3 s warm) because the template renders 2.7 MB of 365-day data. Not a query issue. Pagination or client-side rendering would fix it — deferred.
- **testsim vs real users**: testsim is convenient for testing but its workspace can drift during development. Real user accounts won't see this behavior.

---

## Full commit history (this deployment)

```
8eecf6d  docs: Heroku deployment report
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
