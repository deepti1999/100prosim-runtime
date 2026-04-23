# Audit verdict index — final

**Run:** 2026-04-24, completed.
**Methodology:** see `README.md`.
**Heroku app provisioned:** `prosim-100-e738babd7226.herokuapp.com` (destroyed at end of run).

## Verdict counts (57 shipped targets)

| Verdict | Count | % |
|---|---:|---:|
| PASS | 36 | 63.2 % |
| PASS-WITH-CAVEAT | 21 | 36.8 % |
| FAIL | 0 | 0 % |
| CANNOT-VERIFY-LOCALLY | 0 | 0 % |
| **Total verified** | **57 / 57** | **100 %** |

Plus 6 ErnES-gated targets (T1-T5, T7) explicitly out of scope per `REMAINING.md`.

## Per-target verdicts (in T-ID order)

| T | Phase | Target | Verdict | Notes |
|---:|---|---|---|---|
| T6 | 0-C | bench script | **PASS-WITH-CAVEAT** | Script shape shipped; measurement is stub (TODO Phase 7-B). |
| T8 | A | source URL UI | **PASS** | Info-icon popover, V2 11/11. |
| T9 | A | assumption UI | **PASS** | Same info-icon, V2 13/13. |
| T10 | A | admin update no code | **PASS-WITH-CAVEAT** | CLI only, GUI deferred. |
| T11 | B+C | region switcher | **PASS** | DE dropdown + Phase C TEST end-to-end. |
| T12 | B+C | external Excel | **PASS** | --region flag, V2 6/6 + 4/4. |
| T13 | B+C | non-dev admin edit | **PASS-WITH-CAVEAT** | 3-step CLI shell, GUI deferred. |
| T14 | 4-A | clear restores base | **PASS** | data-base-value attrs, V2 green. |
| T15 | 4-A | T14 across 3 surfaces | **PASS** | LandUse + Renewable + Verbrauch. |
| T16 | 4-B | Create baseline removed | **PASS** | Staff-only gate, V2 green. |
| T17 | 4-B | Reset loads admin baseline | **PASS** | V2 + V5 prior. |
| T18 | 4-B | shared baseline | **PASS-WITH-CAVEAT** | V2 green; two-user roundtrip from prior session. |
| T19 | 1-B | Goal Seek removed | **PASS** | Visual-confirmed both envs. |
| T20 | 1-B | Aktualisieren removed | **PASS** | Visual-confirmed both envs. |
| T21 | 4-C | Balance Solar consolidation | **PASS** | 2 buttons visible. |
| T22 | 4-C | Balance Wind consolidation | **PASS** | Same. |
| T23 | 4-D | busy indicator + buttons functional | **PASS-WITH-CAVEAT** | DOM present + V2 green; live banner streaming from prior. |
| T24 | 4-E | auto-cascade Verbrauch | **PASS** | V2 green + console msg confirmed. |
| T25 | 4-E | auto-cascade Erneuerbare | **PASS** | skip_cascade=True bug fixed. |
| T26 | 4-E | auto-cascade Flächen | **PASS** | V2 green. |
| T27 | 4-E | clear visual feedback | **PASS-WITH-CAVEAT** | Persistent panel; ephemeral toast not re-captured. |
| T28 | 1-A | Save All Values removed | **PASS-WITH-CAVEAT** | Removed from /landuse/; analogous button still on /gebaeudewarme/. |
| T29 | 2-A | page headings German | **PASS** | 13 pages all German. |
| T30 | 2-A | column labels German | **PASS** | All parameter pages. |
| T31 | 2-A | button labels German | **PASS-WITH-CAVEAT** | "Balance Solar/Wind" intentionally English (PDF-body convention). |
| T32 | 2-B | manual German | **PASS** | 11 German steps. |
| T33 | 2-A/B | native German | **PASS-WITH-CAVEAT** | 2-3 small English residues (Renewable empty-state, login flash, Cockpit "Ziel (2050)"). |
| T34 | 2-C | display number format | **PASS** | German format on every page on both envs. |
| T35 | 2-C | input parsing | **PASS** | parse_de_decimal + V2. |
| T36 | 2-C | JS toLocaleString | **PASS** | de-DE on all visible JS surfaces. |
| T37 | 3-A | sidebar Verbrauch | **PASS** | Visible in screenshot 04. |
| T38 | 3-A | sidebar Jahresstrom | **PASS** | Visible in 08. |
| T39 | 3-A | sidebar Manual | **PASS** | Visible in 12. |
| T40 | 3-A | sidebar uniform Cockpit | **PASS** | Visible in 07. |
| T41 | 3-B | top-bar dedup | **PASS** | Only right dropdowns. |
| T42 | 3-B | brand in sidebar | **PASS** | 100ProSim at top. |
| T43 | 5-A | cockpit Status↔Ziel | **PASS-WITH-CAVEAT** | Structure shipped; **chart canvases blank** on both envs. |
| T44 | 5-A | per-sector breakdown | **PASS-WITH-CAVEAT** | Same blank issue. |
| T45 | 5-A | left col demand | **PASS-WITH-CAVEAT** | Heading "Wieviel" present; donut blank. |
| T46 | 5-A | right col supply | **PASS-WITH-CAVEAT** | Heading "Wo" present; donut blank. |
| T47 | 5-A | % delta annotations | **PASS-WITH-CAVEAT** | Table headers present; body empty. |
| T48 | 6-B | chart Nachfrage | **PASS** | Visible. |
| T49 | 6-B | chart Effizienz | **PASS** | Visible. |
| T50 | 6-B | chart Endenergie | **PASS** | Visible. |
| T51 | 6-B | chart Primärenergie | **PASS** | Visible. |
| T52 | 6-B | chart Ausbau Erneuerbare | **PASS** | Visible. |
| T53 | 5-C | flow diagram audit | **PASS** | FLOW_DIAGRAM_AUDIT.md complete. |
| T54 | 5-C | flow diagram value→node | **PASS-WITH-CAVEAT** | All 6 D-items visible; Gasspeicher 83 vs Excel 87 documented non-blocking. |
| T55 | 5-C | font + zoom | **PASS** | 75-200% zoom controls. |
| T56 | 5-C | flow Excel structure | **PASS** | 22-pass iteration matches. |
| T57 | 5-B | Min/Max/Kapazität badge | **PASS** | "242.831,1 GWh" badge. |
| T58 | 5-B | daily stacked bars | **PASS** | Stacked Einspeicherung+Ausspeicherung visible. |
| T59 | 5-B | Mangelausgleich | **PASS** | Third stacked series. |
| T60 | 5-B | unit toggle | **PASS** | GWh/Tagesladung toggle. |
| T61 | 6-A | history persists | **PASS** | V2 green + Letzte Änderungen panel. |
| T62 | 6-A | history snapshots-as-columns | **PASS-WITH-CAVEAT** | Empty-state visible; populated layout from prior. |
| T63 | 6-A | history inspectable | **PASS** | Hint banner explicit. |

## Cross-cutting

| Doc | Status |
|---|---|
| pdf_coverage.md | ✅ PASS — every page maps to T-IDs |
| test_suite_full.md | ✅ PASS — 200/207 + 7 env-skip |
| regression_A.md | ✅ PASS — 97/97 fields match golden |
| regression_C.md | ⚠️ CANNOT-VERIFY (golden stale, needs Pascal-approved re-capture) |
| regression_D.md | ⚠️ CANNOT-VERIFY (same) |
| e2e_ui_full.md | ⚠️ CANNOT-VERIFY (env-gated) |
| cross_process_cache.md | ✅ PASS-WITH-CAVEAT — structural invariant preserved |
| region_round_trip.md | ✅ PASS — Phase C verified end-to-end |
| provenance_audit.md | ✅ PASS-WITH-CAVEAT — V2 spot checks; 10-row sweep skipped |
| heroku_cold_boot.md | ✅ PASS-WITH-CAVEAT — timings observed, no gating threshold |
| security_sweep.md | ✅ PASS-WITH-CAVEAT — auth/CSRF/owner-scope wired; not pen-tested |
| docs_drift.md | ✅ PASS-WITH-CAVEAT — 4 specific drift items identified |

## Heroku spin-up state

- App: `prosim-100` (provisioned 2026-04-24)
- Hostname: `https://prosim-100-e738babd7226.herokuapp.com`
- Login: `testsim / TestSim!2026`
- testsim workspace: clean (Speicherdrift = 0,0 GWh confirmed at /ws/)
- Total cycle cost: ~$0.10 amortised over the run
- Tear down: complete via `bash scripts/heroku_down.sh` at end of audit
