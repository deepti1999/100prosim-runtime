# T20 — Tests

`test_bb_current_app::test_ws_page_only_shows_two_balance_buttons` ✅ green per `cross_cutting/test_suite_full.md`. Asserts the rendered `/ws/` HTML body does NOT contain `Aktualisieren` / `Refresh` strings, and asserts only `Balance Solar` + `Balance Wind` remain (T21/T22 consolidated).
