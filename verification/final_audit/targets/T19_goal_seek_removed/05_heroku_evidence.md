# T19 — Heroku evidence

**Heroku URL:** `https://prosim-100-e738babd7226.herokuapp.com/ws/`
**Screenshot:** `verification/final_audit/screenshots/heroku/06_ws_szenario_abgleich.png`

**Identical to localhost:** `Balance Solar` + `Balance Wind` only at top-right; NO Goal Seek button. Heroku-only delta: Speicherdrift = `0,0 GWh` (clean fresh seed), vs localhost which had testsim workspace state at `0,1 GWh`.

**Visual confirmation method:** real `browser_navigate` + `browser_take_screenshot` (full-page PNG) + eyeball, NOT `fetch()` inside `browser_evaluate`. Per CLAUDE.md V5 rule.

**Verdict for T19:** PASS at the live layer.
