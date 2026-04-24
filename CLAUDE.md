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

## Live Heroku deployment

**The app is NOT permanently deployed.** To save money during development Pascal spins it up only when he needs to test cross-process behavior or share the link with the group, then destroys it. Leaving it running costs ~$22/mo; the spin-up / teardown pattern is ~$1/mo for occasional use.

- **App name:** `prosim-100` (recreated each cycle — hostname changes, e.g. `prosim-100-3a84fc3068c0.herokuapp.com`)
- **Heroku account:** `kkrann1290@gmail.com`
- **Region:** `eu-west-1`
- **Stack:** `heroku-24` (Python 3.12 via `.python-version` — Django 4.2 does NOT support 3.14 which is Heroku's default)
- **Dyno tier:** Basic (1× web + 1× worker, ~$14/mo dynos)
- **Addons:** `heroku-postgresql:essential-0` ($5/mo), `heroku-redis:mini` ($3/mo)
- **Total when running:** ~$22/mo, prorated per second
- **Test user:** `testsim` / `TestSim!2026`

**Spin up / tear down:**
```bash
bash scripts/heroku_up.sh    # ~10 min: create + addons + config + push + seed + testsim
bash scripts/heroku_down.sh  # ~30 sec: destroy app + addons, stops billing
```

Both scripts are idempotent. Hostname after each `up` is printed in the final "Done" line.

**Heroku CLI gotchas (baked into the scripts):**
- `heroku addons:create --wait` on Postgres times out at 5 min even when provisioning is still in progress. Scripts poll `heroku addons` for `created` state instead of using `--wait`.
- `heroku apps:destroy` on Windows exits non-zero due to a harmless git-remote cleanup error, even though the app IS destroyed. Scripts tolerate the non-zero exit and verify with `heroku apps:info` that the app is actually gone.

Manual deploy (if already provisioned): `git push heroku main` — release phase runs migrations automatically. Full docs in `docs/HEROKU.md`.

**testsim workspace drifts during testing** — reset with:
```
heroku run "python manage.py shell -c '
from django.contrib.auth import get_user_model
from simulator.models import LandUse, VerbrauchData, RenewableData, BalanceJob
from simulator.ws_models import WSData
from simulator.workspace_service import ensure_user_workspace_data
u = get_user_model().objects.get(username=\"testsim\")
BalanceJob.objects.filter(created_by=u).delete()
for M in (LandUse, VerbrauchData, RenewableData, WSData):
    M.all_objects.filter(owner=u).delete()
ensure_user_workspace_data(u)
'" -a prosim-100
```

**Heroku Redis TLS gotcha** — Heroku Redis uses self-signed certs. `settings.py` sets `ssl_cert_reqs=ssl.CERT_NONE`. If you remove it, `cache.get()` silently returns None and Step 1.4 bilanz cache stops working.

## Convergence iteration counts are tuned for speed

The balance optimizer's iteration counts were cut during the 2026-04-21 perf pass to get Heroku from ~5 min to ~2 min on unbalanced states. These cuts produce small numeric drift (within scenario D tolerances of ±5 ha / ±1 GWh) but are NOT bit-identical to the pre-optimization outputs.

If you need bit-identical math back: see `docs/CONVERGENCE_ITERATIONS_CHANGED.md` for the exact revert recipe per file/line. Do not revert without Pascal's explicit ask — the speed improvement is material.

## Code layout (big picture)

`simulator/` holds everything. Because it is large and flat, group files by role rather than by filename:

- **Page views** — `page_*.py` (cockpit, bilanz, landuse, renewable, smard, auth) plus `views_pages.py`, `views.py`. Templates in `simulator/templates/`.
- **APIs** — `*_api.py` (`input_api`, `recalc_api`, `balance_api`, `baseline_api`, `ws_api`, `ws_queue_api`) and `views_*.py` counterparts.
- **Calculation pipeline** — top-level `calculation_engine/` package (`ws_engine`, `ws_calculator`, `bilanz_engine`, `verbrauch_engine`, `renewable_engine`, `landuse_engine`, `formula_evaluator`) is the pure-computation layer. `simulator/` wraps it with persistence/orchestration: `recalc_service.py`, `formula_service.py`, `ws_formula_service.py`, `ws_365_service.py`, `workspace_service.py`, `gebaeudewaerme_recalculator.py`, `verbrauch_recalculator.py`, `renewable_recalc.py`, `percentage_rebalancer.py`, `goal_seek.py`.
- **WS365 subsystem** — `ws365_core.py`, `ws365_formula_engine.py`, `ws365_orchestrator.py`, `ws365_sector_balance.py`, `ws_models.py`. Has its own regression suite (`test_ws365_formulas.py`).
- **Async jobs** — `balance_jobs.py` defines jobs; `run_balance_worker` management command drains them.
- **Scenario/workspace state** — `workspace_service.py` + `workspace_signals.py` + `signals.py` + `owner_scope.py` + `middleware.py` (request-scoped scenario state, queue middleware).

When making changes, treat `calculation_engine/` as a pure library and keep Django/ORM imports out of it; persistence and orchestration belong in `simulator/`.

### Architectural rule: process-local caches + Heroku process boundaries

The app has four process-local in-memory caches (after the 2026-04-21 perf pass):

- `recalc_cache._cache` in `simulator/recalc_cache.py`
- `_AUTO_TOKENS_CACHE` + `_LOOKUPS_CACHE` in `simulator/formula_service.py`
- `_WS365_COMPUTE_CACHE` in `simulator/ws365_orchestrator.py`

**Critical rule:** Django signals only fire within the Python process that triggered the save. On Heroku, the web and worker are SEPARATE processes. A save on the web dyno DOES NOT invalidate the worker's caches. Therefore `run_balance_job` in `simulator/balance_jobs.py` invalidates ALL four caches at job entry.

If you add a new multi-pass loop or long-running worker function that reads state, invalidate caches at its entry too. Otherwise you risk "silent no-op" bugs where pass 1 returns empty because the cache has stale state and the outer loop breaks early.

Past incidents:
- Commit `54d4567` — caches not wiped at job entry caused the 1.1.2 revert bug (user changes 100→95, cascade doesn't propagate because worker has stale 1.1.2=100 in auto_tokens_cache).
- Commit `691b99f` — signature excluded computed ziels, so multi-pass DAG convergence stopped after 1 pass (pass 2 saw same sig, returned empty).

**Companion rule — never have two Python functions with the same name at module scope.** `views.py` had `update_user_percent` defined twice (commit `9b0cf3d` fixed this). Python silently keeps only the last def, and the URL router routes to the wrong signature → 500. Run `grep -n "^def " file.py | sort | uniq -c` when auditing a module.

## Common commands

Bring up the stack (now self-healing):

```bash
docker compose up -d
```

An `init` one-shot service runs migrations and loads the seed fixture (if the DB is empty) before `web` / `worker` start. `bash scripts/bootstrap_runtime.sh` still works but is no longer required for a fresh DB.

Postgres is exposed on `localhost:5432` for host-side tools (Django UI tests in `simulator/test_e2e_ui_*.py` connect this way). Override with `POSTGRES_PORT=5433 docker compose up -d` if the default port is taken.

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
- `test_e2e_*` / `test_bb_e2e*` — end-to-end flows (Django test client)
- `test_e2e_ui_*` — Playwright live-browser UI tests (require Postgres + `requirements-dev.txt` + `playwright install chromium`)
- `test_e2e_browser_*` — Selenium live-browser tests (Chrome headless by default, auto-falls-back to Firefox/Safari)
- `test_ws365_formulas.py` — WS365 formula-parity regressions

The `test_e2e_ui_*` and `test_e2e_browser_*` suites skip themselves on SQLite — they need Postgres to avoid transaction/lock issues under concurrent fetches. To run them:

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium   # one-time
LOCAL_POSTGRES_URL="postgresql://postgres:postgres@localhost:5432/finalthesis3" \
  USE_LOCAL_POSTGRES=true ALLOW_DOCKER_POSTGRES_HOST=true \
  python manage.py test simulator.test_e2e_ui_baseline simulator.test_e2e_ui_ws_balance simulator.test_e2e_browser_current
```

Seed / formula import management commands (in `simulator/management/commands/`) — useful when the DB is empty or formulas changed: `import_formulas_to_db`, `import_ws_formulas`, `import_landuse_formulas`, `import_verbrauch_formulas`, `import_ws_constants`, `load_gebaeudewaerme_data`, `load_verbrauch_data`, `load_endenergie_data`, `sync_renewable_formulas`, `validate_formulas`, `check_all_formulas`, `recalc_verbrauch`, `recalc_gebaeudewaerme`, `clear_calculated_values`.

## Deployment env vars

Required for any non-local deploy: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`. The `web`/`worker` split in `Procfile` must be preserved on managed platforms.

## Stakeholder requirements (hard constraints)

**These are non-negotiable contracts with Pascal's stakeholders. Violating them = breaking the product.**

1. **NEVER rename cells, codes, or labels.** This includes LandUse codes (`LU_0`, `LU_2.1`, `LU_6`, …), Renewable codes (`9.3.1`, `9.3.4`, `10.1`, `10.2`, …), Verbrauch codes, WS365 field names, sector names (`KLIK`, `Gebäudewärme`, `Prozesswärme`, `Mobile Anwendungen`), Bilanz row labels, German UI strings, and `Formula` table names. Cells are a stakeholder contract; external workflows and reports depend on them. **Bug fixes to internal Python / JS / test identifiers are fine — only *domain* names are frozen.** If in doubt, ask.
2. **German UI throughout** — no language changes without explicit approval.
3. **Four-sector model** (KLIK, Gebäudewärme, Prozesswärme, Mobile Anwendungen) is load-bearing — do not restructure.
4. **`Formula` table is authoritative** — don't "clean up" redundant-looking formulas.

## Stakeholder implementation plan (April 2026)

The 12-page stakeholder PDF (`260403_Portierung_Bestandsaufnahme.pdf`, H. Schmidt-Kanefendt 2026-04-03) decomposes into 63 atomic targets (T1–T63). **57/63 are shipped + Heroku-verified** as of 2026-04-23; post-audit 2026-04-24 verdict mix is **42 PASS / 15 PASS-WITH-CAVEAT / 0 FAIL** (see `verification/final_audit/index.md`). Remaining 6 are ErnES-gated (T1–T5, T7). The plan, progress, and open-items live in `docs/stakeholder/`:

- **`REMAINING.md`** — single source of truth for what's still open (13 targets across 3 buckets: T54 flow-diagram audit, Phase 7 external-gated, §2.3 data model deferred).
- `IMPLEMENTATION_PLAN.md` — 63-target plan with the 5-way verification ritual.
- `PROGRESS.md` — live checkbox burndown.
- `260403_Bestandsaufnahme_DE.md` + `_EN.md` — original + translation.
- `TRANSLATION_GLOSSARY.md`, `FLOW_DIAGRAM_AUDIT.md`, `REGRESSION_DIFF_REPORT.md`, `VERIFICATION_STATUS.md` — per-item references.

If the user asks "what's next" / "what's left" / anything about stakeholder work: read `REMAINING.md` first.

**Key learnings from the autonomous Phase 3–6 push:**

- **Commit per item with T-ID in subject**: `stakeholder-<phase>-<item>: <summary> (T<n>)`. One phase = one logical push; V5 Heroku verification batched at the phase boundary.
- **Heroku spin-up/teardown is cheap**: ~$0.06–0.10 per full cycle. Use liberally for V5. `scripts/heroku_up.sh` + `heroku_down.sh` handle the CLI gotchas (5-min `--wait` timeout on Postgres; Windows git-remote non-zero exit on destroy).
- **Goldens regen needs explicit user sign-off** (plan rule). `regression/compare.py` now filters `_meta.*` from the diff (provenance, not app state). `regression/capture_A.py` + `regression/categorize_A_diff.py` turn a scary 100+-field diff into a 6-category decision — makes sign-off review cheap.
- **Workspace-scoped data causes per-user value drift** over time. Pin a consistent owner when capturing goldens (testsim works).
- **Auto-cascade ≠ auto-Balance.** PDF §2.4.4 means "changes in cell A propagate to dependent cells automatically" (Excel-style). Balance (§2.4.3) stays a manual 2-button choice. Don't conflate the two; the codebase now distinguishes them clearly.
- **`save()` vs `save(skip_cascade=True)`**: Renewable's `save_renewable_user_input` used to skip cascade, which broke the T25 cascade contract. Now uses plain `save()`. LandUse + Verbrauch always did.
- **Cross-process cache coherency** (fixed earlier in `54d4567`) holds through Phase 3–6. `run_balance_job` still invalidates all 4 caches at entry. Don't remove that.

## Two main stakeholder work streams (co-equal, both active)

### 1. Performance — Heroku is slow

Production runs on Heroku (see `Procfile`). Heroku is currently slow; that's the pain point stakeholders feel.

- Bias toward fixes that help **single-dyno, Postgres-over-network, no-parallelism** environments.
- Local multi-core Docker wins that don't carry to Heroku are lower value.
- Suspect hot paths (full list in `docs/PYPSA_MIGRATION_RESEARCH.md` §23.2): 365-day WS loop, goal-seek root-find (the 68-second `solar_sector_ws` step is the worst offender), 760-formula cascade, N+1 queries on `/renewable/` and `/verbrauch/`, redundant 365-row `WSData` reads on `/annual-electricity/`.
- Planned speedup path: **integrate** PyPSA at the slow numerical cores (not migrate). See `docs/PYPSA_MIGRATION_RESEARCH.md` §23.1.
- Flag Heroku-targeting changes in commit messages: `perf: cut Heroku recalc cold-start by X%`.

### 2. Reduce hardcoding — extensibility

Much of the current architecture is hardcoded where it should be data-driven. Adding a new sector requires touching ~15 files; adding a new energy carrier needs code; 2045 / Germany / German-language / power densities are all implicit. Main offenders documented in `docs/PYPSA_MIGRATION_RESEARCH.md` §23.3:

- Four sectors (KLIK / Gebäudewärme / Prozesswärme / Mobile Anwendungen) baked into views, templates, column headings, Bilanz layout.
- WS365 shape (365-day cycle, single-node Germany) assumed across `ws365_*.py`.
- Sector-coupling links implicit in formula text (not first-class entities).
- No `TimeHorizon` concept — "2045 net-zero" lives only in seed numbers.
- Country = "Germany" implicit throughout (total area 35,759,529 ha).
- German UI only; no i18n wrapper.
- Power densities (MW/ha for solar/wind) are magic constants in `ws365_core.py` and land-use forms.
- Cost data has no first-class concept.

Highest-leverage refactors, in order: first-class `Sector` table → first-class `Carrier` → first-class `Link` / `Conversion` → `TimeHorizon` → power densities + cost params in DB → i18n wrapper → `Region`.

**Perf and extensibility aren't mutually exclusive.** A first-class `Sector` refactor makes a later PyPSA integration (perf work) easier. Prefer extensibility refactors that also reduce perf cost.

## Workflow (session loop)

This project uses a disciplined verify-before-claim workflow. Every session:

1. **Session start** — the `SessionStart` hook auto-prints `docker compose ps` and git status. If services are down, run `bash scripts/bootstrap_runtime.sh` (it handles migrate + seed + worker start; plain `docker compose up -d` does NOT, it will leave the worker crash-looping on missing tables).
2. **Before changes** — run the relevant regression scenario to establish a known-good baseline for this session (see `regression/`).
3. **Change code** — Claude Code natively enforces read-before-edit. The `PostToolUse` hook runs `python -m py_compile` on every written `.py` file and surfaces syntax errors immediately.
4. **After changes** — `docker compose restart web worker`, run targeted thesis test module, re-run affected regression scenario(s), compare against golden.
5. **Before commit** — all affected regression scenarios must pass (`compare.py` exit 0). If a golden needs updating, regenerate it **deliberately** and commit golden + code in the same commit.
6. **Session end** — `rm -rf verification/ .playwright-mcp/`.

## Per-item verification — NON-NEGOTIABLE

Every behaviour-changing commit must pass five verifications before being claimed done. This exists because in April 2026 we shipped changes that passed locally but broke on Heroku (cross-process cache bugs — commits `54d4567`, `9b0cf3d`). Local-only verification is insufficient.

| Step | What | Pass criterion |
|---|---|---|
| **V2 — Tests (unit/contract)** | Run affected `test_bb_*` / `test_wb_*` / `test_e2e_*` modules. Add new tests for any new code path; weak coverage = add coverage, don't ship. | All tests green locally. |
| **V3 — API smoke** | curl / pytest against the affected HTTP endpoints. | Expected JSON shape + HTTP 200 + contract preserved. |
| **V4 — Playwright localhost** | Run the affected regression scenario at `http://localhost:8001`. Use `browser_navigate` + `browser_take_screenshot` + eyeball, NOT just `fetch()` inside `browser_evaluate`. | Scenario passes; `compare.py <id>` exits 0; rendered page looks correct. |
| **V5 — Playwright on live Heroku** | Spin up via `bash scripts/heroku_up.sh`, navigate to each affected page in a real browser tab, take a screenshot, confirm visually. Tear down via `bash scripts/heroku_down.sh`. | Page actually renders as designed on live URL. |
| **V6 — Docs** | If the change introduced any invariant, gotcha, or decision: update `CLAUDE.md`, per-item doc, or memory file in the same commit. | Written down, not just in my head. |

**Rules:**
- **V5 is mandatory** for anything that touches cache invalidation, signals, balance flow, recalc flow, auto-cascade, worker behaviour, or cross-process state. When in doubt, run it.
- **V5 can be batched per phase** (not per item) during stakeholder-plan work — spin Heroku up once at phase start, run the whole phase's Playwright suite, tear down. Keeps cost to ~$0.10/phase.
- **V4 and V5 require real browser navigation, not just `fetch()` inside `browser_evaluate`.** Running `await fetch('/page/').then(r => r.text()).includes('some-id')` is a DOM-presence check, not visual verification. It will miss:
  - CSS hiding the element (`d-none`, `display: none`, overflow clipping)
  - Layout bugs (elements stacking wrong, columns overflowing)
  - Charts/SVGs failing to render (the DOM is there, the canvas is blank)
  - Broken images, z-index conflicts, mis-aligned controls
  - Real interactive behaviour (click → nothing happens, banner doesn't update)
  If I find myself writing `fetch()` inside `browser_evaluate` to "verify" a UI change, I am skipping V4/V5. Stop and use `browser_navigate` + `browser_take_screenshot` + eyeball instead.
- **New tests are encouraged.** If a regression is possible and no existing test covers it, write one. Don't skip V2 by pretending no test applies.
- **If a verification fails, the item is not done.** Fix the root cause; never suppress the failure. Never update goldens to make a failing test pass unless you are deliberately capturing an intentional change + committing golden and code together.
- **Honest accounting on "verified".** When the user asks "is it verified?", distinguish between (a) DOM-presence check via HTTP/fetch, and (b) real-browser visual confirmation. Don't conflate them. If the user cares enough to ask, they care enough to get the right answer.

See `docs/stakeholder/IMPLEMENTATION_PLAN.md` §1 for the full ritual with per-item examples.

## Periodic self-review (CLAUDE.md + memory upkeep)

**Rule:** at natural checkpoints Claude must pause, scan the recent conversation in its current context, and proactively suggest additions or corrections to `CLAUDE.md` and the memory files. Never silently auto-apply — always propose the exact diff and wait for Pascal's approval.

**Trigger the review when:**
- About to commit a non-trivial change.
- Pascal states a new rule, constraint, invariant, preference, or correction.
- A new stakeholder requirement comes up.
- A workflow gotcha, performance footgun, or domain fact is discovered mid-task.
- Before ending a session or handing off.

**What to look for in the recent conversation:**
- Phrases like "NEVER", "always", "don't", "never push", "never rename" — hard rules.
- Phrases like "I prefer", "we should", "make sure you" — soft guidance worth preserving.
- Domain facts Pascal confirms or corrects (e.g. "actually that value is wrong", "those cells are frozen").
- New performance pain points or known-slow paths.
- Tool / infra discoveries (e.g. hook reload semantics, compose gotchas, solver behaviour).
- Paradigm decisions (e.g. "integrate not migrate", "Heroku is the target").

**How to propose:**
- Phrase as `"Based on [short context], I'd like to add to [file] — proposed diff: ..."`.
- One proposal per distinct learning. Don't batch unrelated facts into one edit.
- If the learning already exists in CLAUDE.md or a memory file, propose an *update*, not a new entry.
- Never write updates silently — Pascal's approval is required.

**Honest caveat:** Claude cannot read its own transcript outside its current context window. The review is bounded by what's still in context at the checkpoint. If the session has been very long, old-but-relevant facts may already be gone — that's expected, and the solution is to write the important things down *when they come up*, not wait for a periodic sweep to rescue them.

## When Claude tests automatically (without being asked)

The user should NOT have to ask me to run tests for routine changes. Scope the test run by the change:

| Change type | Run automatically |
|---|---|
| Formula / `Formula` row | `test_ws365_formulas` + scenario C or D |
| `calculation_engine/*` | `test_bb_calc` + `test_wb_ws365_formula_engine` + scenario C |
| Page / template / JS | scenario A + Playwright test for that page if one exists |
| WS balance logic | scenario C + D + `test_bb_bal` + `test_e2e_ui_D_full_flow` |
| Recalc flow (`recalc_*`, signals, workspace) | `test_bb_e2e` + scenario D |
| Docker / compose / Dockerfile | restart stack + `curl /readyz` + scenario A smoke |
| Docs / comments / gitignore / non-code typos | nothing |
| Uncategorised | pause, ask once, then remember |

Before any non-trivial commit: always run `compare.py A`, `compare.py C`, `compare.py D` plus at least one relevant thesis test module. If the change is genuinely trivial (docs, comments, gitignore), skip.

Tests NEVER auto-update. On failure: investigate first. If the behaviour change is intentional, re-capture the golden deliberately and commit golden + code in the same commit. `compare.py` exit codes:
- **0** — match
- **1** — value drift (investigate: regression or intentional?)
- **2** — baseline fingerprint drift (seed / formula / model changed; re-capture, don't patch)

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

Configured in `.claude/settings.json`; scripts in `.claude/hooks/`. Hook config is loaded at session start, so changes here require `/hooks` or a new session to take effect in the current session.

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

## Working with the Jahresstrom flow diagram (SVG iteration discipline)

The `/annual-electricity/` SVG flow diagram (template
`simulator/templates/simulator/annual_electricity.html`) was iterated
22 times before reaching pass 22's stable state. Lessons from that
push, applicable to any future SVG layout work in this codebase:

- **Excel WS.xlsm is ground truth, and it is parseable.** The file
  `docs/100prosim_d_*/WS.xlsm` (gitignored) contains every shape's
  EMU coordinate in `xl/drawings/drawing1.xml`. EMU → px is `/9525`.
  `scripts/gen_flow_svg.py` is a working extractor — use it to read
  the canonical positions instead of measuring screenshots.
- **Excel main flow has 4 circles, not 5.** M-circle, splitter,
  Q-circle, S-circle. "N" is a letter labelling the 947-value on the
  Q→S arrow, not a separate circle. (Earlier passes assumed 5.)
- **Box-on-arrow visually CUTS the arrow** when the box has white
  fill. Pascal: "don't let the box cut the arrow". Move value boxes
  OFF the arrow (above for horizontal arrows, right of for vertical
  arrows). Arrow flows uninterrupted; the value sits beside.
- **When one circle moves, EVERYTHING tied to it must move.**
  Cascading shifts when Q changes x: Abregelung arrow + Abregelung
  value box + Abregelung Q letter; Q→Ely-ES branch arrow + that
  value box + 134 + 194 GW + P/Eta label; Q→S arrow start;
  Splitter→Q arrow endpoint; ES gas arrow + value box + P letter;
  AND middle-row Stromspeicher box + its centred labels. Make a
  cascade list before each shift or you'll miss an arrow endpoint
  and ship a visible disconnect (commit `2c303d1` was that bug).
- **"Stretch the arrow"** in user feedback means: lengthen the
  horizontal segment between two circles so the value box + label
  stack fits ABOVE the line with breathing room. Default short
  arrows force value boxes onto the line.
- **Eta labels need bordered badges or wider gaps**, not bare text
  in narrow inter-box space. "Eta Ely." is 50px wide at 13px font;
  if the gap to the next box is 30px the label overlaps.
- **Reverting beats fix-forward** for visual regressions. Pass 14
  was rejected and immediately restored via
  `git checkout <prev-pass-sha> -- <file>` — clean, no half-broken
  intermediate commit. Use this whenever a layout change makes
  things worse: revert, then try a different approach.
- **Per-pass commit + Heroku at milestones**: every meaningful pass
  got its own commit so any one could be reverted independently.
  V5 Heroku verify happened at structural milestones (passes 6, 22)
  rather than every pass — saves spin-up cost (~$0.10/cycle) without
  losing live verification at the points where it matters.
- **Update `docs/stakeholder/FLOW_DIAGRAM_AUDIT.md`** with each
  visual-pass cluster (pass 2, pass 3, pass 4 sections). Keeps the
  iteration history searchable.
