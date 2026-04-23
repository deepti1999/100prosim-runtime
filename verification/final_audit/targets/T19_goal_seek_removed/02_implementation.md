# T19 — Implementation

**Commit:** `5fd420e` (per `PROGRESS.md` Phase 1-B).
**Files:** `simulator/templates/simulator/ws_template_balance_ui.html` (button + JS handler removed); `simulator/page_ws.py` calls `goal_seek=True` on the summary endpoint to preserve auto-run behaviour.

**Approach:** The PDF's "redundant — runs automatically" claim was verified BEFORE removing the button — `refreshWsSummaryCards` debounces auto-fire on page load and the `apply-full-balance*` endpoints internally call goal_seek as part of their pipeline. Once auto-behaviour was confirmed, the explicit button + handler were deleted.

**Test module:** `simulator.test_bb_current_app::test_ws_page_only_shows_two_balance_buttons` asserts only the 2 consolidated buttons (T21/T22) remain — implicitly proving Goal Seek is gone.
