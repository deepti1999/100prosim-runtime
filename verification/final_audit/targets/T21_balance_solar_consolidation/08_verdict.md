# T21 — Verdict: **PASS**

`screenshots/{localhost,heroku}/06_ws_szenario_abgleich.png` shows ONLY two buttons at top right: yellow "Balance Solar" + blue "Balance Wind". Old 4-button surface gone. Test `test_bb_current_app::test_ws_page_only_shows_two_balance_buttons` ✅ green.

The unified `Balance Solar` button calls `/api/ws/apply-full-balance/` which orchestrates the WS + Sector+WS sequence internally per commit `cb62793`. `test_bb_bal` confirms the unified call produces the same final state as the prior 2-step sequence.
