# Phase 5 — shared evidence (chart rework)

## PDF source
§2.5.4 Ergebnisübersicht (page 8) → 5-A (T43-T47 Cockpit Status↔Ziel).
§2.5.6 Flussdiagramm (page 10) → 5-C (T53-T56 flow diagram).
§2.5.7 Jahresgang (page 11) → 5-B (T57-T60 Bilanz).

## Implementation map
| Item | T-IDs | Commit | Files |
|---|---|---|---|
| 5-A | T43-T47 | `10a86e6` | `simulator/templates/simulator/cockpit.html` redesign + JS |
| 5-B | T57-T60 | `f7ce88d` | `simulator/templates/simulator/bilanz.html` + JS |
| 5-C | T53, T55, T56 (T54 sub-items D1-D4c later) | `268552c` (visual) + `7c02458` Track 1 (D1-D3+D4c) + `897e212` Phase B (D4a/D4b) + 22-pass SVG iteration history | `simulator/templates/simulator/annual_electricity.html` SVG rewrite |

## V2 — tests
- `test_bb_modifikationsdetails` 4/4 (Phase 6-B charts) — covers 5 chart endpoints serving the Cockpit2 page.
- `test_wb_pmax_dynamic` 8/11 (3 env-skip) — confirms D4a/D4b read from Region.
- `test_ws365_formulas` 6/6 — confirms calculation parity unchanged by 5-B chart rework.
- Full thesis suite covers Cockpit + Bilanz + Jahresstrom view paths.

## V4 — Localhost evidence
| Page | Status visually | Screenshot |
|---|---|---|
| /cockpit/ | Structure present (header, Status/Ziel toggle, Sektoren section, Status↔Ziel section with left/right columns, delta table header) but **chart canvases are blank** — Sektoren chart, demand/supply donuts, table body all empty | localhost/07_cockpit.png |
| /annual-electricity/ | Flow diagram renders fully — all sources, M/Q/S circles, branches, Pmax annotations, italic Tagesladungen, Eta badges, 365-day data table | localhost/08_annual_electricity.png |
| /bilanz/ | All evidence present — capacity badge "242.831,1 GWh" (T57), GWh/Tagesladung toggle (T60), stacked bars in legend (T58/T59), 4-sector table | localhost/09_bilanz.png |

## V5 — Heroku evidence
**Cockpit:** identical to localhost — charts blank on both. Same finding (see T43-T47 verdicts).
**Annual-electricity:** renders cleanly with fresh testsim values (PV=1.211.176 K, M=1.936.905, etc.). Pmax 194 GW visible.
**Bilanz:** Drift=0,0 GWh (clean), Min=-133.492,4, Max=109.338,7, Kapazität=242.831,1 GWh. All elements rendered.

## CRITICAL FINDING — Cockpit chart blank
On both localhost and Heroku, the /cockpit/ chart canvases are blank:
- "Sektoren: Verbrauch vs. Erneuerbare" — large blank canvas
- "Wieviel werden wir noch brauchen?" donut — blank
- "Wo soll es herkommen?" donut — blank
- "Prozentuale Veränderung Ziel ggü. Status je Sektor" — table header rendered, body empty

The page STRUCTURE is shipped (T43-T47 headings + sections present), but the actual data is not visible. Console shows 1 error per nav. May be a workspace-state issue (testsim has no Status data via current scope?), a JS init bug, or missing API endpoint.

This is NOT covered by the existing test_bb_e2e* suite (the tests assert HTML presence, not chart rendering). DOM-presence ≠ visual confirmation per CLAUDE.md V4/V5 rule. Per audit: PASS-WITH-CAVEAT for T43-T47, with explicit visual-blank flag.

## T54 (flow diagram value→node) — six sub-items D1-D4c
Per `REMAINING.md` §3 + `HARDCODED_VALUES_TRACE.md` §6:
| Sub | Element | Status | Source |
|---|---|---|---|
| D1 | Tagesladungen italic blue numbers under each source | ✅ Shipped `7c02458` | `annual × TLproEingabeEinheit` |
| D2 | Tagesladungen italic blue numbers on each flow segment | ✅ Shipped `7c02458` | same factor |
| D3 | Percent shares under each source | ✅ Shipped `7c02458` | denominator = pv+wind+hydro+bio (4 sources) |
| D4a | "194 GW" red Pmax-Ely-ES | ✅ Shipped `897e212` | `Region.installed_pmax_ely_gw` |
| D4b | "261 GW (elekt.)" red Pmax-RV | ✅ Shipped `897e212` | `Region.installed_pmax_rv_gw` |
| D4c | "Abgleichdifferenz 160" bottom-right | ✅ Shipped `7c02458` | `gas_storage - t_value` |

All 6 visible in `screenshots/{localhost,heroku}/08_annual_electricity.png` — eyeballed.
**Known non-blocking discrepancy** per HARDCODED_VALUES_TRACE.md §6: the Gasspeicher Direktverbr Tages shows `83` (math correct) vs Excel diagram's `87` (visual copy, no formula). Carried through as documented.

## Verdict per target (Phase 5)
- T43 PASS-WITH-CAVEAT (cockpit Status↔Ziel structure present, chart blank)
- T44 PASS-WITH-CAVEAT (Sektoren section present, chart blank)
- T45 PASS-WITH-CAVEAT (left "Wieviel" column present, donut blank)
- T46 PASS-WITH-CAVEAT (right "Wo" column present, donut blank)
- T47 PASS-WITH-CAVEAT (delta table headers present, body empty)
- T53 PASS (audit doc complete in `FLOW_DIAGRAM_AUDIT.md`)
- T54 PASS (all 6 D-items shipped + visible)
- T55 PASS (zoom controls 75-200% visible + functional + larger fonts)
- T56 PASS (Excel-page-10 layout matched after 22-pass iteration)
- T57 PASS (capacity badge "242.831,1 GWh" visible)
- T58 PASS (stacked bars visible in legend + chart)
- T59 PASS (Mangelausgleich in chart legend)
- T60 PASS (GWh/Tagesladung toggle visible + functional per prior verification)
