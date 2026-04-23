# Phase 4 — shared evidence (behaviour fixes)

## PDF source
§2.4.1 (Basis-Wert), §2.4.2 (Baseline), §2.4.3 (Szenario-Abgleich), §2.4.4 (Recalculate / auto-cascade) — pages 4-5.

## Implementation map
| Item | Target IDs | Commit | Files | Test module |
|---|---|---|---|---|
| 4-A | T14, T15 | `cee9a25` | LandUse/Renewable/Verbrauch form templates + JS handlers | `test_bb_input_clear_restores_base` (implicit via current cell-level JS handler tests) |
| 4-B | T16, T17, T18 | `d43ca7d` | `simulator/baseline_api.py`, AdminBaseline model | `test_bb_admin_baseline` (5/5) |
| 4-C | T21, T22 | `cb62793` | `simulator/templates/simulator/ws_template_balance_ui.html`, `views_ws.py`, `views_balance.py` | `test_bb_current_app::test_ws_page_only_shows_two_balance_buttons` (6/6) |
| 4-D | T23 | `eb5a6ae` | `#balanceProgressBanner` + JS poll | `test_bb_balance_after_edit` (covered in test_bb_bal full pass) |
| 4-E | T24, T25, T26, T27 | `86e3ba2` | save handlers (Verbrauch, Renewable removed `skip_cascade`, LandUse), debounce | `test_bb_e2e_auto_cascade` (full pass), `test_bb_renewable_edit` (cascade-on-save) |

## V2 — tests
All Phase 4 test modules ✅ green per `cross_cutting/test_suite_full.md`. Notably:
- `test_bb_admin_baseline` 5/5 — covers staff-only create, shared singleton, restore round-trip, 404 path, can_create flag.
- `test_bb_e2e_auto_cascade` — exercise save → cascade fire (NOT Balance fire) on every input surface.

## V3 — API smoke
- `/api/baseline/create/` (staff gate)
- `/api/baseline/restore/`
- `/api/baseline/info/`
- `/api/save-renewable-user-input/` (no skip_cascade)
- `/api/save-verbrauch-user-input/`
- `/api/update-user-percent/` (LandUse)
- `/api/ws/apply-full-balance/` + `/apply-full-balance-wind/`
- All exercised by the thesis suite.

## V4 — localhost
- /landuse/ shows percent inputs pre-filled with current values; the per-row input has the `data-base-value` attribute (from Phase 4-A) as a placeholder/restore hook.
- /ws/ shows ONLY 2 buttons (Balance Solar + Balance Wind, captured in `06_ws_szenario_abgleich.png`).
- `#balanceProgressBanner` DOM element present (verified by `test_bb_current_app`); not visible in static screenshot because no Balance was running at capture time.

## V5 — Heroku
Same as localhost. Notable:
- Heroku /ws/ Speicherdrift = `0,0 GWh` (clean fresh seed).
- testsim workspace clean, no historie entries (4-E auto-cascade not exercised in this audit; would require a write-then-read round trip on Heroku which would dirty workspace mid-audit).

## Edge cases
- **Admin baseline absent:** /api/baseline/restore/ returns 404 (handled, test asserts).
- **Two-user concurrency for shared baseline:** verified previously on Heroku `prosim-100-687a5505e19f` per `VERIFICATION_STATUS.md` §3 — admin_pascal created baseline, testsim restored it; verified shared singleton.
- **Balance after edit (T23 acceptance gate):** banner verified previously at `prosim-100-687a5505e19f` — banner stayed visible 85 s while job queued, status text updated every 2 s. Documented in `VERIFICATION_STATUS.md` §2.

## Caveats specific to this run
- **Did NOT exercise interactive edit + cascade on Heroku.** Doing so would dirty testsim workspace and contaminate other targets sharing the screenshots. The V2 unit tests + V5 evidence from prior phase verifications cover this.
- **Banner state check** is from prior session (commit `21f2f8c` documented in VERIFICATION_STATUS), not re-run today.

## Verdict per target
T14 PASS · T15 PASS · T16 PASS · T17 PASS · T18 PASS-WITH-CAVEAT (re-using prior 2-user evidence; not re-tested live in this audit) · T21 PASS · T22 PASS · T23 PASS-WITH-CAVEAT (banner DOM verified, live banner streaming verified previously) · T24 PASS · T25 PASS · T26 PASS · T27 PASS-WITH-CAVEAT (cascade fires per tests, "Aktualisiert" toast not visually verified in this audit run because no edit was performed)
