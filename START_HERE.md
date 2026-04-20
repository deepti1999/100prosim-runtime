# START HERE

## What this folder is

This is the clean runtime bundle for **100ProSim**.

It contains only the files needed to run or host the application:

- Django project code
- templates and static assets
- database seed data
- thesis-aligned black-box and white-box test modules
- Docker/runtime files
- `README.md`
- this file

It does **not** contain thesis files, PDFs, screenshots, or development handoff notes.

## One-command local startup

From this folder, run:

**macOS / Linux:**

```bash
bash scripts/bootstrap_runtime.sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\bootstrap_runtime.ps1
```

After startup:

- App: printed by the script, usually `http://localhost:8001`
- Health check: printed by the script as `/readyz`

## What the command does

1. starts PostgreSQL
2. runs Django migrations
3. loads the bundled seed data if the database is empty
4. starts the web process
5. starts the background balance worker

If port `8001` is already in use, the script automatically chooses the next free local port.

## For production hosting

The application is designed to run with:

- one **web** process
- one separate **worker** process
- one **PostgreSQL** database

Use:

- `Procfile` for process separation
- `.env.example` as the environment-variable template
- `Dockerfile` and `docker-compose.yml` for container-based setup

The worker process is required for asynchronous WS balance jobs.

## Running the bundled tests

All thesis-relevant test cases are included directly as Python test files inside:

```bash
simulator/test_*.py
```

You can run the complete grouped suites or run each test module separately.

### Run all thesis suites

```bash
bash scripts/run_thesis_tests.sh
```

### Run black-box suites

Core black-box suite:

```bash
python3 manage.py test simulator.test_bb_val simulator.test_bb_calc simulator.test_bb_bal simulator.test_bb_e2e -v 1
```

Supplementary current-webapp black-box suite:

```bash
python3 manage.py test simulator.test_bb_current_app simulator.test_bb_renewable_edit simulator.test_e2e_current_scenario_flow -v 1
```

### Run white-box suites

Main white-box suite:

```bash
python3 manage.py test simulator.test_wb_ws365_formula_engine simulator.test_wb_scenario_state simulator.test_wb_queue_jobs_middleware simulator.test_it_current_recalc_contracts -v 1
```

WS365 regression suite:

```bash
python3 manage.py test simulator.test_ws365_formulas -v 1
```

### Run each test module individually

```bash
python3 manage.py test simulator.test_bb_val -v 1
python3 manage.py test simulator.test_bb_calc -v 1
python3 manage.py test simulator.test_bb_bal -v 1
python3 manage.py test simulator.test_bb_e2e -v 1
python3 manage.py test simulator.test_bb_current_app -v 1
python3 manage.py test simulator.test_bb_renewable_edit -v 1
python3 manage.py test simulator.test_e2e_current_scenario_flow -v 1
python3 manage.py test simulator.test_wb_ws365_formula_engine -v 1
python3 manage.py test simulator.test_wb_scenario_state -v 1
python3 manage.py test simulator.test_wb_queue_jobs_middleware -v 1
python3 manage.py test simulator.test_it_current_recalc_contracts -v 1
python3 manage.py test simulator.test_ws365_formulas -v 1
```

### What each module covers

- `test_bb_val.py`: black-box input validation
- `test_bb_calc.py`: black-box recalculation and response contracts
- `test_bb_bal.py`: black-box balance endpoints and queue behavior
- `test_bb_e2e.py`: black-box end-to-end persistence and baseline restore
- `test_bb_current_app.py`: current UI naming and annual-page behavior
- `test_bb_renewable_edit.py`: renewable user-edit rules
- `test_e2e_current_scenario_flow.py`: scenario create/rename/delete annual-page flow
- `test_wb_ws365_formula_engine.py`: white-box WS365 helper and engine paths
- `test_wb_scenario_state.py`: white-box session/scenario-state paths
- `test_wb_queue_jobs_middleware.py`: white-box queue, API, and middleware paths
- `test_it_current_recalc_contracts.py`: white-box recalculation entry-point contracts
- `test_ws365_formulas.py`: WS365 regression/parity checks
