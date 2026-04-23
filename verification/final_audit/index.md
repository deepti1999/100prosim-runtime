# Audit verdict index — running

**Last updated:** 2026-04-24, run in progress.
**Methodology:** see `README.md`.

## Verdict counts

| Verdict | Count | % |
|---|---:|---:|
| PASS | — | — |
| PASS-WITH-CAVEAT | — | — |
| FAIL | — | — |
| CANNOT-VERIFY-LOCALLY | — | — |
| **Total verified** | 0 / 57 | 0 % |

(filled in after batches commit)

## Per-target verdicts (in T-ID order)

| T | Phase | Target | Verdict | Notes |
|---:|---|---|---|---|
| T6 | 0-C | bench script | _pending_ | |
| T8 | A | source URL UI | _pending_ | |
| T9 | A | assumption UI | _pending_ | |
| T10 | A | admin update no code | _pending_ | |
| T11 | B+C | region switcher | _pending_ | |
| T12 | B+C | external Excel | _pending_ | |
| T13 | B+C | non-dev admin edit | _pending_ | |
| T14 | 4-A | clear restores base | _pending_ | |
| T15 | 4-A | T14 across 3 surfaces | _pending_ | |
| T16 | 4-B | Create baseline removed | _pending_ | |
| T17 | 4-B | Reset loads admin baseline | _pending_ | |
| T18 | 4-B | shared baseline | _pending_ | |
| T19 | 1-B | Goal Seek removed | _pending_ | |
| T20 | 1-B | Aktualisieren removed | _pending_ | |
| T21 | 4-C | Balance Solar consolidation | _pending_ | |
| T22 | 4-C | Balance Wind consolidation | _pending_ | |
| T23 | 4-D | busy indicator + buttons functional | _pending_ | |
| T24 | 4-E | auto-cascade Verbrauch | _pending_ | |
| T25 | 4-E | auto-cascade Erneuerbare | _pending_ | |
| T26 | 4-E | auto-cascade Flächen | _pending_ | |
| T27 | 4-E | clear visual feedback | _pending_ | |
| T28 | 1-A | Save All Values removed | _pending_ | |
| T29 | 2-A | page headings German | _pending_ | |
| T30 | 2-A | column labels German | _pending_ | |
| T31 | 2-A | button labels German | _pending_ | |
| T32 | 2-B | manual German | _pending_ | |
| T33 | 2-A/B | native German | _pending_ | |
| T34 | 2-C | display number format | _pending_ | |
| T35 | 2-C | input parsing | _pending_ | |
| T36 | 2-C | JS toLocaleString | _pending_ | |
| T37 | 3-A | sidebar Verbrauch | _pending_ | |
| T38 | 3-A | sidebar Jahresstrom | _pending_ | |
| T39 | 3-A | sidebar Manual | _pending_ | |
| T40 | 3-A | sidebar uniform Cockpit | _pending_ | |
| T41 | 3-B | top-bar dedup | _pending_ | |
| T42 | 3-B | brand in sidebar | _pending_ | |
| T43 | 5-A | cockpit Status↔Ziel | _pending_ | |
| T44 | 5-A | per-sector breakdown | _pending_ | |
| T45 | 5-A | left col demand | _pending_ | |
| T46 | 5-A | right col supply | _pending_ | |
| T47 | 5-A | % delta annotations | _pending_ | |
| T48 | 6-B | chart Nachfrage | _pending_ | |
| T49 | 6-B | chart Effizienz | _pending_ | |
| T50 | 6-B | chart Endenergie | _pending_ | |
| T51 | 6-B | chart Primärenergie | _pending_ | |
| T52 | 6-B | chart Ausbau Erneuerbare | _pending_ | |
| T53 | 5-C | flow diagram audit | _pending_ | |
| T54 | 5-C | flow diagram value→node | _pending_ | |
| T55 | 5-C | font + zoom | _pending_ | |
| T56 | 5-C | flow Excel structure | _pending_ | |
| T57 | 5-B | Min/Max/Kapazität badge | _pending_ | |
| T58 | 5-B | daily stacked bars | _pending_ | |
| T59 | 5-B | Mangelausgleich | _pending_ | |
| T60 | 5-B | unit toggle | _pending_ | |
| T61 | 6-A | history persists | _pending_ | |
| T62 | 6-A | history snapshots-as-columns | _pending_ | |
| T63 | 6-A | history inspectable | _pending_ | |

## Cross-cutting

| Doc | Status |
|---|---|
| pdf_coverage.md | _pending_ |
| test_suite_full.md | _pending_ |
| regression_A.md | _pending_ |
| regression_C.md | _pending_ |
| regression_D.md | _pending_ |
| e2e_ui_full.md | _pending_ |
| cross_process_cache.md | _pending_ |
| region_round_trip.md | _pending_ |
| provenance_audit.md | _pending_ |
| heroku_cold_boot.md | _pending_ |
| security_sweep.md | _pending_ |
| docs_drift.md | _pending_ |

## Heroku spin-up state

- App: see `heroku_up.log` (one provision at start of run, one teardown at end).
- Hostname: filled in after spin-up completes.
- testsim workspace reset: noted per dirty test.
