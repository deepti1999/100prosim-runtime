# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**100ProSim** — Django web application simulating land-use / energy-balance scenarios (German-language domain: *Verbrauch*, *Bilanz*, *Gebäudewärme*, *WS365*, renewables). This directory is the cleaned runtime bundle (deployment handoff), not the full dev repo: thesis material, dev notes, and screenshots are excluded.

## Runtime architecture

Two-process model (see `Procfile`):

- **web** — `gunicorn landuse_project.wsgi`
- **worker** — `python manage.py run_balance_worker --sleep 0.2` — consumes `BalanceJob` rows for asynchronous WS/balance recalculation. The web process cannot replace it; async balance recalcs will stall without the worker running.

Django project: `landuse_project/` (settings, URLs, health). Single app: `simulator/`. Health endpoints `/healthz` and `/readyz` are wired at the project level.

Production database is PostgreSQL (`DATABASE_URL`). `db.sqlite3` exists for local convenience but is not the deployment target.

## Code layout (big picture)

`simulator/` holds everything. Because it is large and flat, group files by role rather than by filename:

- **Page views** — `page_*.py` (cockpit, bilanz, landuse, renewable, smard, auth) plus `views_pages.py`, `views.py`. Templates in `simulator/templates/`.
- **APIs** — `*_api.py` (`input_api`, `recalc_api`, `balance_api`, `baseline_api`, `ws_api`, `ws_queue_api`) and `views_*.py` counterparts.
- **Calculation pipeline** — top-level `calculation_engine/` package (`ws_engine`, `ws_calculator`, `bilanz_engine`, `verbrauch_engine`, `renewable_engine`, `landuse_engine`, `formula_evaluator`) is the pure-computation layer. `simulator/` wraps it with persistence/orchestration: `recalc_service.py`, `formula_service.py`, `ws_formula_service.py`, `ws_365_service.py`, `workspace_service.py`, `gebaeudewaerme_recalculator.py`, `verbrauch_recalculator.py`, `renewable_recalc.py`, `percentage_rebalancer.py`, `goal_seek.py`.
- **WS365 subsystem** — `ws365_core.py`, `ws365_formula_engine.py`, `ws365_orchestrator.py`, `ws365_sector_balance.py`, `ws_models.py`. Has its own regression suite (`test_ws365_formulas.py`).
- **Async jobs** — `balance_jobs.py` defines jobs; `run_balance_worker` management command drains them.
- **Scenario/workspace state** — `workspace_service.py` + `workspace_signals.py` + `signals.py` + `owner_scope.py` + `middleware.py` (request-scoped scenario state, queue middleware).

When making changes, treat `calculation_engine/` as a pure library and keep Django/ORM imports out of it; persistence and orchestration belong in `simulator/`.

## Common commands

Bootstrap (Postgres + migrations + seed + web + worker):

```bash
bash scripts/bootstrap_runtime.sh          # macOS/Linux
powershell -ExecutionPolicy Bypass -File scripts\bootstrap_runtime.ps1   # Windows
```

If port `8001` is busy the script picks the next free port and prints the URL.

Run all thesis test suites:

```bash
bash scripts/run_thesis_tests.sh
```

Run a single test module / class / method (standard Django test runner):

```bash
python3 manage.py test simulator.test_bb_calc -v 1
python3 manage.py test simulator.test_wb_ws365_formula_engine.SomeTestCase.test_x -v 1
```

Test module naming encodes scope — keep it consistent when adding tests:

- `test_bb_*` — black-box (HTTP/contract level)
- `test_wb_*` — white-box (internal paths)
- `test_it_*` — integration contracts
- `test_e2e_*` / `test_bb_e2e*` — end-to-end flows
- `test_ws365_formulas.py` — WS365 formula-parity regressions

Seed / formula import management commands (in `simulator/management/commands/`) — useful when the DB is empty or formulas changed: `import_formulas_to_db`, `import_ws_formulas`, `import_landuse_formulas`, `import_verbrauch_formulas`, `import_ws_constants`, `load_gebaeudewaerme_data`, `load_verbrauch_data`, `load_endenergie_data`, `sync_renewable_formulas`, `validate_formulas`, `check_all_formulas`, `recalc_verbrauch`, `recalc_gebaeudewaerme`, `clear_calculated_values`.

## Deployment env vars

Required for any non-local deploy: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`. The `web`/`worker` split in `Procfile` must be preserved on managed platforms.

## Workflow (session loop)

This project uses a disciplined verify-before-claim workflow. Every session:

1. **Session start** — the `SessionStart` hook auto-prints `docker compose ps` and git status. If services are down, run `bash scripts/bootstrap_runtime.sh` (it handles migrate + seed + worker start; plain `docker compose up -d` does NOT, it will leave the worker crash-looping on missing tables).
2. **Before changes** — run the relevant regression scenario to establish a known-good baseline for this session (see `regression/`).
3. **Change code** — Claude Code natively enforces read-before-edit. The `PostToolUse` hook runs `python -m py_compile` on every written `.py` file and surfaces syntax errors immediately.
4. **After changes** — `docker compose restart web worker`, run targeted thesis test module, re-run affected regression scenario(s), compare against golden.
5. **Before commit** — all affected regression scenarios must pass (`compare.py` exit 0). If a golden needs updating, regenerate it **deliberately** and commit golden + code in the same commit.
6. **Session end** — `rm -rf verification/ .playwright-mcp/`.

## Regression harness (`regression/`)

Claude-session-driven golden-file UI + calculation regression. Complements the `simulator.test_*` suites, doesn't replace them.

```
regression/
  README.md                      how it works
  playbook.md                    step-by-step recipe Claude follows
  scenarios/<id>.yml             inputs / mutations / probe points
  golden/<id>.json               captured baseline (hand-editable, committed)
  screenshots/<id>/              reference screenshots (committed)
  compare.py                     diffs current-run JSON vs golden
```

Per-session artifacts go to `verification/<today>/` (gitignored, deleted at turn end).

**Available scenarios**:
- `A-baseline-readonly` — login + visit every main page + capture top-line numbers (162 fields). Detects seed / migration / nav drift.
- `C-ws-balance` — trigger WS Balance Solar, poll `BalanceJob` until `succeeded`, capture post-balance UI state (41 fields). Hard-invariant: `speicherdrift_gwh == "0,0"`.

**Extending**: follow the playbook shape (login → navigate → probe → screenshot → emit JSON → `compare.py <id>`). Goldens are regenerated only when a code change intentionally moves them — commit golden diff alongside the code diff.

## Hooks

Configured in `.claude/settings.json`; scripts in `.claude/hooks/`.

- `SessionStart` → `session_start.py` — injects `docker compose ps` + git branch/dirty state as `additionalContext`. Non-blocking; safe when docker isn't running.
- `PostToolUse` on `Write|Edit` → `py_syntax.py` — runs `python -m py_compile` on edited `.py` files. Exit 2 with `systemMessage` on syntax error so the model self-corrects. Skips files under `.venv/`, `venv/`, `staticfiles/`.

Add hooks here when a check is genuinely worth automating. Prefer Monitor over hooks for passive log-watching.

## Test user for UI regression

A `testsim` account is created in the seeded DB for Playwright-driven tests. Credentials and a one-line recreate command live at `.claude/test-credentials.json` (gitignored). If the db volume is reset, recreate with the snippet inside that file.

## Known invariants / gotchas

- **Landing page copy is approximate** — text mentions "9.3.1 (405047)" and "9.3.4 (189289)", but seeded values are `406,403.3` and `195,890.3`. Trust the data, not the copy.
- **WS balance on balanced seed is a no-op** — the seed is already balanced, so `speicherdrift_gwh` is already `0,0` pre-balance; the solar/wind balance button runs but produces zero delta. Scenario C validates that running the op doesn't move the state.
- **Procfile `release:` runs migrations** — only on platforms that honor the release phase (Heroku). Raw `docker compose up -d` does NOT; always use `bootstrap_runtime.sh` locally.
- **Playwright MCP writes `.playwright-mcp/`** — auto-dump of snapshots/console logs to project root on every nav. Gitignored; wipe at end of each turn.
