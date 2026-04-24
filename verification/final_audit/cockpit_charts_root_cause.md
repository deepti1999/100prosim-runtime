# Cockpit charts blank — root-cause investigation

**Date:** 2026-04-24
**Investigator:** Claude (audit follow-up Task 1a)
**Affected targets:** T43, T44, T45, T46, T47 (PDF §2.5.4 "Ergebnisübersicht").
**Verdict change:** PASS-WITH-CAVEAT → **FAIL** for all 5.

> **RESOLVED 2026-04-24** — bug #111 fixed in commit `f86aae9` via the data-attribute payload pattern (cockpit values render into a hidden `<div id="bilanzDataPayload">` with `|unlocalize`-d `data-*` attributes; JS reads via `dataset.<key>` + `parseFloat()`). T43-T47 verdicts restored from FAIL → PASS after V4 (localhost) + V5 (Heroku `prosim-100-d538a1c45903`) Playwright confirmation that all 3 charts attach and the delta table populates with 4 sector rows. New audit tally: **41 PASS / 16 PASS-WITH-CAVEAT / 0 FAIL.** Screenshots: `verification/final_audit/bug_111_fix/{01_localhost,02_heroku}_cockpit_post_fix.png`.

## Headline

`/cockpit/` is **broken on both localhost and Heroku** because Django's German locale (Phase 2-C T34: `LANGUAGE_CODE='de'`, `USE_L10N=True`, `USE_THOUSAND_SEPARATOR=True`) auto-formats numeric template variables as German display strings (`2.432.616,134…`), and `simulator/templates/simulator/cockpit.html` interpolates ~30 such variables directly into a JavaScript object literal at lines 287-340. JavaScript cannot parse `2.432.616,134` as a numeric literal (the second `.` is unexpected after the first decimal interpretation), and the **entire `<script>` block fails at parse time before a single line executes**. As a result:
- All 3 Chart.js canvases remain blank (no Chart constructor is ever called).
- The "Prozentuale Veränderung" delta table `<tbody>` is never populated.
- Console shows a single error: `Unexpected number`.

This is **not** a workspace-state edge case, **not** a missing data fix, **not** a Chart.js loading problem. It is a deterministic template+locale interaction that fires for any non-trivial float value rendered into a JS context.

## Reproduction

### Localhost (docker compose)

```
1. browser_navigate('http://localhost:8001/login/') — login form German.
2. Fill testsim / TestSim!2026, click Anmelden → /simulation/.
3. browser_navigate('http://localhost:8001/cockpit/').
4. browser_evaluate page.waitForTimeout(3000) — wait for any async chart init.
```

**Screenshot:** `verification/final_audit/screenshots/localhost/07_cockpit_blank_repro.png` (committed alongside this doc).

### Console messages

```
Total messages: 1 (Errors: 1, Warnings: 0)

Unexpected number
```

That is the entire JavaScript error surface. No additional warnings. No Chart.js init logs. No data-fetch attempts.

### Network requests after page load

```
[GET] http://localhost:8001/api/baseline/info/ => [200] OK
[GET] http://localhost:8001/api/scenario/list/ => [200] OK
```

**Notice:** there is no chart-data fetch. The cockpit page does not even attempt to retrieve numerical data from the server because the inline JavaScript that would do so never parsed.

(Compare: a working page would show fetches like `/api/cockpit-data/` or similar. None happen.)

### Canvas DOM state

```json
{
  "canvasCount": 3,
  "canvases": [
    {"id": "sectorComparisonChart",  "width": 300, "height": 150, "hasCtx": true, "hasChart": false},
    {"id": "demandStatusZielChart",  "width": 300, "height": 150, "hasCtx": true, "hasChart": false},
    {"id": "supplyStatusZielChart",  "width": 300, "height": 150, "hasCtx": true, "hasChart": false}
  ],
  "tableTBodies": [
    {"rows": 0, "sample": "(empty)"}
  ]
}
```

All 3 canvases exist with their default 300×150 dimensions (no resize ever happened). All have a 2D context available. **None have a Chart.js instance attached** (`Chart.getChart(canvas) === undefined`). The delta table `<tbody>` has 0 rows.

### The smoking gun — the inline `<script>` body

```javascript
<script>
    const bilanzData = {
        status: {
            gesamt_total: 2.432.616,1342535475,
            gesamt_klik: 329.345,68559999997,
            gesamt_gebaeudewaerme: 799.186,5467999999,
            ...
```

Captured directly from `document.documentElement.outerHTML` (script tag idx=1, 15660 bytes). The numbers are German-formatted. JavaScript parses `2.432` as a number; sees `.616` and tries to start a member access; fails; throws `Unexpected number`. The entire script body — including `function initCharts()`, `function updateCharts()`, the `DOMContentLoaded` handler — never runs.

## Why the test suite missed this

`simulator/test_bb_modifikationsdetails.py` (the closest test module) and any other test that hits `/cockpit/` does so via Django's test client (`self.client.get('/cockpit/')`), which:
- Renders the HTML server-side (so the bilanzData JSON appears as a string in the response body).
- Asserts substrings like `"Sektoren: Verbrauch vs. Erneuerbare"` are present in the HTML.
- Never invokes a JavaScript engine. Never tries to PARSE the response as JS.

So the tests pass green even though the JS is malformed. This is exactly the V4/V5 trap CLAUDE.md warns about: "fetch()+regex inside browser_evaluate is NOT verification" — the same trap exists at the Django-test-client level for pages that depend on JS execution.

The 4 environment-skipped Playwright tests (`test_e2e_ui_*`) WOULD have caught this if they ran — they use a real browser. But they're gated behind `requirements-dev.txt` per `cross_cutting/e2e_ui_full.md`.

## Source line where the bug enters

`simulator/templates/simulator/cockpit.html` lines 287-340:

```django
<script>
    const bilanzData = {
        status: {
            gesamt_total: {{ verbrauch_endenergie_gesamt|default:0 }},
            gesamt_klik: {{ verbrauch_endenergie_klik|default:0 }},
            gesamt_gebaeudewaerme: {{ verbrauch_endenergie_gebaeudewaerme|default:0 }},
            gesamt_prozesswaerme: {{ verbrauch_endenergie_prozesswaerme|default:0 }},
            ...
```

There are ~30 template substitutions in this pattern across the `status:` and `ziel:` blocks. Every one of them is a float that Django will render via the active locale formatter. With `LANGUAGE_CODE='de'`, that means German thousand-dot + decimal-comma — both unparseable in JS literal context.

## Fix recipe (NOT applied — audit run)

Django provides the `|unlocalize` filter and the `{% localize off %}` block tag specifically for this case. Either:

```django
gesamt_total: {{ verbrauch_endenergie_gesamt|default:0|unlocalize }},
```

OR wrap the entire JS object literal in:

```django
{% load l10n %}
{% localize off %}
const bilanzData = {
    status: { gesamt_total: {{ verbrauch_endenergie_gesamt|default:0 }}, ... },
    ziel:   { ... },
};
{% endlocalize %}
```

The wrap form is the cleaner fix — single block, no per-line filter sprawl, easy to grep for.

## Audit of analogous template patterns

Searched for other templates that interpolate float-typed context vars into a JS literal:

```
$ grep -rln "const .*= {[^}]*{{[^}]*default:0" simulator/templates/
```

Suspect templates worth Pascal investigating in the same fix sweep:
- `cockpit.html` — confirmed broken above.
- `bilanz.html` — does its own German-formatting in Chart.js callbacks, so likely safe; but the daily-series array MAY have the same risk if values are inlined as a Python list rendered into JS. Worth a quick eyeball.
- `annual_electricity.html` — the SVG diagram works (V5 verified); JS values appear to come from JSON datasets, not direct interpolation. Likely safe.
- `modifikationsdetails.html` — the 5 charts work (V5 verified); presumably uses a JSON-encoded dataset filter.

A grep + per-file review would close this audit completely. Not done here.

## Severity

**FAIL.** The Cockpit page is the **stakeholder's central PDF §2.5.4 deliverable** — they explicitly asked for "Erhöhung der Aussagekraft durch komplexes Diagramm nach Muster 100prosim-Excel" with both Status and Ziel side-by-side, broken down per sector, with delta annotations. The current state shows headers + structure but **none of the diagrams render**. A user opening the page sees an empty visual analysis screen.

Calling this PASS-WITH-CAVEAT in the prior audit was generous — the prior verdict trusted that the structure-being-shipped was sufficient evidence. This deeper investigation reveals a 100%-deterministic bug that breaks the user-facing feature. It must be FAIL until the template fix lands.

## Verdict updates per target

All 5 caveats reclassified to FAIL with this evidence:
- T43 (Status+Target side-by-side): **FAIL** — JS bombs, no chart paint.
- T44 (per-sector breakdown): **FAIL** — same root cause.
- T45 (left "Wieviel" demand): **FAIL** — donut canvas blank, exact same JS error.
- T46 (right "Wo" supply): **FAIL** — donut canvas blank.
- T47 (% delta annotations): **FAIL** — `<tbody>` empty because the JS that populates it never runs.

ONE root cause produces FIVE target failures. The fix is a single template change.

## Heroku evidence

Not re-tested in this Task 1a (Heroku is destroyed; spinning up just for this would violate the "one Heroku cycle in Task 3 only" rule). The prior audit's screenshot `verification/final_audit/screenshots/heroku/07_cockpit.png` shows IDENTICAL blank canvases — same blank Sektoren chart, same blank donuts, same empty delta-table body. The bug ships to production.

## Follow-up tasks created

- **TaskCreate:** "BUG: Cockpit JS bombs on German-formatted numbers in template literals" — full repro, fix recipe, scope of analogous-pattern audit. Owner: Pascal (audit run does not fix).

## Lessons for the test harness

1. **Add at least one Playwright-real-browser test that loads `/cockpit/` and asserts `Chart.getChart(canvas) !== undefined` for each chart.** This single test would have caught this bug at commit time.
2. **Add a Django-system-check or template-lint that flags `{{ float_var|default:0 }}` inside `<script>` blocks.** The `|unlocalize` filter or `{% localize off %}` wrapper is mandatory in JS contexts under L10N.
3. **For every Phase 2-C-equivalent settings change in the future,** sweep all templates for un-marked-up numeric injections.

This bug existed since Phase 2-C (T34, commit `b8e4a45`, 2026-04-21 onward) — ~3 days unnoticed across 4 prior Heroku V5 cycles, the prior 22-pass flow-diagram audit, and the previous "57/57 verified" audit. **The test harness has a known visual-rendering blind spot.** Task 2 (test coverage) addresses this systematically.
