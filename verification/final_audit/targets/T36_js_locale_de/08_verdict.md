# T36 — Verdict: **PASS**

**Implementation:** commit `b8e4a45` (Phase 2-C). `simulator/templates/simulator/*.html` JS blocks updated to call `.toLocaleString('de-DE', {maximumFractionDigits:N})` instead of `.toFixed(N)` / hand-rolled formatters. Chart.js `tooltip` callbacks + axis-tick callbacks updated to German format.

**V4 / V5 evidence:**

| Page | JS-rendered German numbers visible |
|---|---|
| /ws/ | "1.211.176 GWh" (Optimales Solar — JS-injected after auto-fetch on page load) |
| /bilanz/ | Chart axis labels, "242.831,1 GWh" Kapazität badge, line-end annotations "156,6 GWh" |
| /annual-electricity/ | "365 Tage Daten" table values all German format (Stromverbr. 2.181,6 / 4.513,6 etc.) |
| /modifikationsdetails/ | Chart y-axis labels: 350.000 / 300.000 / 250.000 |
| /cockpit/ | Card labels (where present) German |

**Caveat:** Cockpit chart canvases are blank (separate finding for T43-T47), but the JS that WOULD render them uses German format (verified by reading `simulator/templates/simulator/cockpit.html` JS block).

**Verdict:** PASS — JS-rendered numbers use de-DE locale on all visible surfaces.
