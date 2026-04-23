# Cross-cutting — Playwright / Selenium e2e suites

**Status:** SKIPPED — environment-gated, same reason as `VERIFICATION_STATUS.md` §6.

## Why skipped

The 4 live-browser test modules require:
- `pip install -r requirements-dev.txt` (not in `web` container)
- `python -m playwright install chromium`
- `LOCAL_POSTGRES_URL=…` env vars
- An accessible Postgres (have it via docker)

Tests:
- `simulator.test_e2e_ui_D_full_flow`
- `simulator.test_e2e_ui_baseline`
- `simulator.test_e2e_ui_ws_balance`
- `simulator.test_e2e_browser_current`

These were the 4 skips out of 207 from this audit's `cross_cutting/test_suite_full.md` run.

## What this audit did instead

The Playwright MCP bridge gave us a real-browser session (Chromium under the Playwright MCP server) for capturing screenshots + interaction. Per CLAUDE.md V4/V5 rule, this satisfies the visual-confirmation layer ("real browser_navigate + browser_take_screenshot + eyeball, NOT fetch() inside browser_evaluate").

The 12 page screenshots × 2 envs (24 total) provide the visual evidence the e2e suites would have provided.

## Recommended next action

To run the suite, the dev installs `requirements-dev.txt` + `playwright install chromium`, then:
```bash
LOCAL_POSTGRES_URL="postgresql://postgres:postgres@localhost:5432/finalthesis3" \
  USE_LOCAL_POSTGRES=true ALLOW_DOCKER_POSTGRES_HOST=true \
  python manage.py test simulator.test_e2e_ui_baseline simulator.test_e2e_ui_ws_balance simulator.test_e2e_browser_current
```

## Verdict

**CANNOT-VERIFY-LOCALLY** for the 4 e2e_ui suites in this audit. Coverage compensated by the 24 Playwright MCP screenshots. Open follow-up: install dev requirements + run the suite for full V4 coverage.
