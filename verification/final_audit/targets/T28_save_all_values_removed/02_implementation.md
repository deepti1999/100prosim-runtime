# T28 — Implementation

**Commit:** `455fa65` (per `PROGRESS.md` Phase 1-A).
**Files:** `simulator/templates/simulator/landuse_list.html` — "Save All Values" button + JS handler removed. Underlying `/api/save-all-inputs/` endpoint left in place per the plan ("in case other callers exist; mark deprecation in code comment").
**Test module:** `simulator.test_bb_current_app::test_landuse_no_save_all_values_button` (asserts string absent).

**Caveat noted in audit:** the LandUse fix removed the button **only from /landuse/**. Other parameter pages (`/gebaeudewarme/`) still have an analogous "Alle Werte speichern" button (German). The PDF complaint was specifically about /landuse/, so that's all the target removed — but the same UX pattern persists elsewhere. See `08_verdict.md` for caveat detail.
