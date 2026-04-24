# T43 — Verdict: **FAIL** (downgraded from PASS-WITH-CAVEAT 2026-04-24)

`screenshots/{localhost,heroku}/07_cockpit.png` + `screenshots/localhost/07_cockpit_blank_repro.png` confirm the page structure: "Status (Aktuell)" + "Ziel (2050)" toggle, "Status ↔ Ziel — Gegenüberstellung" section heading.

**FAIL root cause:** see `verification/final_audit/cockpit_charts_root_cause.md`. Inline JS in `simulator/templates/simulator/cockpit.html` lines 287-340 builds a `bilanzData` object with German-locale-formatted floats (`2.432.616,1342535475`) which JavaScript cannot parse. The whole `<script>` block dies at parse time with `Unexpected number`. No Chart.js init runs, so all 3 canvases stay blank and the delta table tbody stays empty.

**Why this is FAIL not CAVEAT:** the user-facing PDF §2.5.4 deliverable ("komplexes Diagramm nach Muster 100prosim-Excel") is not visible to any user on either env. Page structure shipped is necessary but not sufficient for the stakeholder ask.

**Bug task:** #111 (TaskCreate) — fix recipe is `|unlocalize` filter or `{% localize off %}{% endlocalize %}` block wrap.

NOT to be fixed in this audit run.
