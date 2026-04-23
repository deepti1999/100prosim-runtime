# Phase 3 — shared evidence (sidebar + nav consistency)

## PDF source
§2.5.3 (page 7), lines 244–249. *"In 100prosim-Web ist die Seiten-Menüleiste links auf nahezu allen Seiten identisch vorhanden, es fehlt auf den Seiten 'Verbrauch', 'Jahresstrom' und 'Benutzerhandbuch'. Auf der Seite 'Cockpit' ist es zwar vorhanden, aber anders formatiert. Die linken Einträge in der oberen Menüleiste wären doppelt und damit überflüssig, wenn die Seiten-Menüleiste auf allen Seiten vorhanden wäre und dort auch der Menüpunkt '100prosim' angeordnet würde."*

## Implementation
- Commit `3bc2976` (Phase 3-A + 3-B together).
- New partial `simulator/templates/simulator/_sidebar.html`.
- `base.html` includes the partial; layout uses Bootstrap 5 sidebar pattern.
- Top-bar pruned to right-side dropdowns only (Region, Baseline, Szenarien, account).

## V2 — Tests
`simulator.test_bb_current_app::test_sidebar_present_on_all_pages` ✅ green per `cross_cutting/test_suite_full.md`.
`simulator.test_bb_current_app::test_top_nav_dedup` ✅ green.

## V4 — Localhost screenshots
The sidebar with the standard "SIMULATIONSMODULE" header + 11 menu items + "100ProSim" brand at top is visible on EVERY captured page:

| Page | Screenshot | Sidebar | Brand at top | Top-bar dup? |
|---|---|---|---|---|
| /simulation/ | localhost/01 | ✅ | ✅ "100ProSim" | none |
| /landuse/ | localhost/02 | ✅ | ✅ | none |
| /renewable/ | localhost/03 | ✅ | ✅ | none |
| /verbrauch/ | localhost/04 | ✅ | ✅ | none |
| /gebaeudewarme/ | localhost/05 | ✅ | ✅ | none |
| /ws/ | localhost/06 | ✅ | ✅ | none |
| /cockpit/ | localhost/07 | ✅ | ✅ | none |
| /annual-electricity/ | localhost/08 | ✅ | ✅ | none |
| /bilanz/ | localhost/09 | ✅ | ✅ | none |
| /historie/ | localhost/10 | ✅ | ✅ | none |
| /modifikationsdetails/ | localhost/11 | ✅ | ✅ | none |
| /user-manual/ | localhost/12 | ✅ | ✅ | none |

12 / 12 pages have the sidebar; 0 pages have duplicate top-nav links.

## V5 — Heroku screenshots
Identical results across `screenshots/heroku/01..12.png`. No env-specific differences observed.

## Edge cases
- **Sidebar collapse on narrow viewport:** Bootstrap toggler renders; not exercised in this audit (default desktop screenshots).
- **Cockpit prior custom formatting:** absorbed into the shared `_sidebar.html` per T40 — no longer formatted differently.

## Verdict per target
- T37 PASS · T38 PASS · T39 PASS · T40 PASS · T41 PASS · T42 PASS
