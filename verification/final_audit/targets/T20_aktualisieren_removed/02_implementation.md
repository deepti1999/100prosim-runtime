# T20 — Implementation

**Commit:** `5fd420e` (shared with T19, Phase 1-B).
**Files:** `simulator/templates/simulator/ws_template_balance_ui.html` — Refresh button + JS handler removed; the `refreshWsSummaryCards()` function now auto-fires on `DOMContentLoaded` with debounce.
**Test module:** `simulator.test_bb_current_app::test_ws_page_only_shows_two_balance_buttons` (asserts both Goal Seek and Refresh strings absent).
