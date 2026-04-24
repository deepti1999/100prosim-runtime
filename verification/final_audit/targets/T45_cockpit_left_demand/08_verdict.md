# T45 — Verdict: **PASS** (restored from FAIL after #111 fix landed in commit f86aae9, 2026-04-24)

Previously: PASS-WITH-CAVEAT → FAIL (Task 1a) → **PASS** (Task 1 fix verified V4 + V5).

"Wieviel werden wir noch brauchen? (Endenergie-Verbrauch je Sektor)" — left column heading visible per Excel reference. The `demandStatusZielChart` canvas is now resized to 588×525 (was stuck at 300×150 default) and `Chart.getChart(canvas) !== undefined` confirms a Chart.js instance attached. The chart paints 4 sector groups × 2 series (Status grey, Ziel blue) showing demand reduction from Status to Ziel.

Same fix path as T43. Screenshots: `bug_111_fix/{01_localhost,02_heroku}_cockpit_post_fix.png`.

**Bug #111 closed.**
