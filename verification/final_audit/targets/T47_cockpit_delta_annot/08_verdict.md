# T47 — Verdict: **PASS** (restored from FAIL after #111 fix landed in commit f86aae9, 2026-04-24)

Previously: PASS-WITH-CAVEAT → FAIL (Task 1a) → **PASS** (Task 1 fix verified V4 + V5).

"Prozentuale Veränderung Ziel ggü. Status je Sektor" table now populated with 4 rows (one per sector). Each row carries: sector name, Verbrauch Status, Verbrauch Ziel, Δ Verbrauch, Erneuerbare Status, Erneuerbare Ziel, Δ Erneuerbare. Δ values are coloured (red `text-danger` for negative, green `text-success` for positive) per the JS `colorFor()` logic. Sample row from V5 Heroku screenshot: `KLIK | 329.346 | 312.753 | -5,0 % | 172.995 | 312.753 | +80,8 %`.

Same fix path as T43 — the `initStatusZielCharts()` function that populates this `<tbody>` was never executing because the inline `<script>` block parse-failed. After the fix, `DOMContentLoaded → initStatusZielCharts()` runs and writes the 4 rows.

Screenshots: `bug_111_fix/{01_localhost,02_heroku}_cockpit_post_fix.png`.

**Bug #111 closed.**
