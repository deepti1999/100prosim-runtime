# Cross-cutting — Heroku cold boot timings

**Heroku app:** `prosim-100-e738babd7226.herokuapp.com` (provisioned 2026-04-24 via `bash scripts/heroku_up.sh`).

## Methodology

Observational page-load timings during the audit's Heroku Playwright capture pass. Single-sample per page, NOT a percentile. Heroku Basic dyno timings vary ±2× call-to-call.

## Observed timings (single-sample first-hit per page after dyno warm)

| Page | First-paint estimate (s) | Notes |
|---|---:|---|
| /login/ | ~1 | Heroku dyno cold-spin already complete by this nav. |
| /simulation/ | ~2 | Cards + summary counters fetched on load. |
| /landuse/ | ~3 | 20 LandUse rows + provenance icons + history panel. |
| /renewable/ | ~3 | 223 rows in collapsed tree; full expand would be slower. |
| /verbrauch/ | ~5 | Largest table (~95 rows + sub-rows). Slowest read-heavy page. |
| /gebaeudewarme/ | ~3 | 26 rows + provenance icons. |
| /ws/ | ~2 | Plus auto-fetch of summary cards (200-400 ms async). |
| /cockpit/ | ~3 | (Charts blank — no chart-data round trip happened.) |
| /annual-electricity/ | ~4 | SVG render + 365-day data table. |
| /bilanz/ | ~5 | Chart.js daily series (365 points × 4 datasets) is the heaviest render. |
| /historie/ | ~1 | Empty state. |
| /modifikationsdetails/ | ~3 | 5 charts × 4 series each. |
| /user-manual/ | ~2 | Static content + ~20 image sub-requests. |

## Cold-boot dyno spin

`bash scripts/heroku_up.sh` end-to-end took ~10 minutes (Heroku cli `addons:create` + `git push heroku main` + release-phase migrations + seed + testsim).

The first HTTP hit after a cold dyno spin (testsim login + first /simulation/ visit) added ~5–8 s of dyno wake to the timings above. Subsequent navs while the dyno was warm were the timings tabulated.

## Headline acid-test gap

The PDF §2.2 acid test (onshore 2.0→2.3 %, offshore 70→60 GW, measure Balance Solar elapsed time) was NOT executed in this audit because `scripts/bench_acid_test.sh` is a stub (see T6 verdict). When implemented, expected order-of-magnitude is ~120 s on Heroku Basic per the PDF's prior measurement.

## Verdict

**PASS-WITH-CAVEAT** — timings observed and documented; no gating threshold (per PDF "praxistauglich" wording). Verbrauch + Bilanz are the slowest user-facing reads (~5s). Cold-boot dyno spin adds ~5-8s to first-hit. Improvements would target: Verbrauch per-row N+1 query (per `docs/PYPSA_MIGRATION_RESEARCH.md` §23.2), Bilanz daily-series compaction, possibly Cockpit chart-data endpoint optimization.

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. PDF §2.2 uses *"praxistauglich"* with no numeric target; single-sample timings logged for baseline. Architectural follow-ups documented in PYPSA_MIGRATION_RESEARCH §23.2 but not gated on cold-boot audit. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.
