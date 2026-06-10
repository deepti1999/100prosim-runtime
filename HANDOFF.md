# Handoff notes

Short guide for whoever takes this repo over. Complements `README.md` and `START_HERE.md`.

## First-run on a fresh machine

1. Install Docker Desktop + Git.
2. Clone / copy the repo.
3. From the repo root:
   ```
   docker compose up -d
   ```
   An `init` service runs migrations and loads the seed fixture automatically. Then `web` and `worker` start. When the command returns, visit http://localhost:8001.

That's it for normal use.

## Running tests

**Thesis suites** (fast, no browser):
```
bash scripts/run_thesis_tests.sh
# or targeted:
python manage.py test simulator.test_bb_val -v 1
```

**UI regression** — two complementary layers:

1. **Claude-driven harness** (`regression/`) — Playwright MCP scripts I follow during any Claude Code session. Does not require installing anything beyond Docker. Outputs a diff via `python regression/compare.py <scenario-id>`. Scenarios: `A-baseline-readonly`, `C-ws-balance`.

2. **Django-integrated UI tests** (`simulator/test_e2e_ui_*.py` + `simulator/test_e2e_browser_*.py`) — Selenium + Playwright test classes runnable by the normal Django runner. These require Postgres and extra dev deps:
   ```
   pip install -r requirements-dev.txt
   python -m playwright install chromium
   # docker-compose exposes Postgres on localhost:5432
   LOCAL_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/finalthesis3 \
     USE_LOCAL_POSTGRES=true ALLOW_DOCKER_POSTGRES_HOST=true \
     python manage.py test simulator.test_e2e_ui_baseline simulator.test_e2e_ui_ws_balance simulator.test_e2e_browser_current -v 1
   ```
   On SQLite these suites skip themselves; they're designed to run against the Docker Postgres.

## Layout — where stuff lives

- `landuse_project/` — Django project config (settings, urls, health endpoints)
- `simulator/` — the app. Big, flat; see `CLAUDE.md` for a role-based map.
- `calculation_engine/` — pure-Python calc library (no Django imports)
- `regression/` — Claude-driven UI regression harness
- `scripts/bootstrap_runtime.sh` — still works, but `docker compose up -d` is now self-healing so it's no longer required
- `seed/sqlite_seed.json` — initial DB fixture (~4000 rows), loaded once by the `init` compose service
- `.claude/` — Claude Code config. Hooks in `.claude/hooks/`. `settings.json` is committed; `*.local.json` and `test-credentials.json` are gitignored.

## Test login

Playwright MCP regression uses `testsim` / `TestSim!2026`, stored in `.claude/test-credentials.json` (gitignored). If you reset the DB volume, the one-line recreate command is inside that JSON.

The Django-integrated UI tests create their own users in `setUp` (no manual setup needed).

## Git identity

The early commits on this branch were authored by `kkran05 <kkran05@gmail.com>`. If you want future commits to show you instead, run:

```
git config user.name "Your Name"
git config user.email "you@example.com"
```

once in this repo. To rewrite author metadata on existing commits (optional — pre-push only):

```
git commit --amend --reset-author    # last commit only
# or interactive rebase with --reset-author for a range
```

## Environment gotchas I wish I'd known

- `db.sqlite3` in the repo is a leftover from the original bundle; it's gitignored now. The real database is Postgres in Docker. Don't edit the SQLite file expecting it to matter.
- Raw `docker compose restart web` is safe after pulling code — volumes mount the source in.
- Playwright MCP dumps `.playwright-mcp/` to project root on every navigation. Gitignored, safe to wipe anytime.
- The landing page text mentions `9.3.1 (405047)` and `9.3.4 (189289)` as fixed values — the actual seed numbers are `406,403` and `195,890`. Trust the data, not the copy.
- The app has **two balance-job code paths**: under `settings.DEBUG=True` the `/api/ws/apply-balance/` endpoint runs inline; under `DEBUG=False` it enqueues a `BalanceJob` for the worker. Testing async behavior requires running with `DJANGO_DEBUG=false` — the Docker `web` service already sets this.

## Workflow (if you're using Claude Code)

CLAUDE.md at the repo root has the full session loop. Short version: (1) `docker compose up -d`, (2) run affected regression scenario before changes, (3) change code, (4) restart web+worker, (5) re-run scenario, (6) only commit when `python regression/compare.py <id>` exits 0.
