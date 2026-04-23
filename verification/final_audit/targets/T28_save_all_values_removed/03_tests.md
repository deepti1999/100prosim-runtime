# T28 — Tests

`test_bb_current_app::test_landuse_no_save_all_values_button` ✅ green per `cross_cutting/test_suite_full.md`. Asserts the rendered `/landuse/` HTML body does NOT contain `Save All Values` / `Alle Werte speichern` strings.

`test_bb_e2e` continues to pass — confirms scenario save/restore via `Scenarios → Save current Scenario` is functional, so the alternative path the PDF cites as "covers the intent" is intact.
