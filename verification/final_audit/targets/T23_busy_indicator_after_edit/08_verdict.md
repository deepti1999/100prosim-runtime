# T23 — Verdict: **PASS-WITH-CAVEAT**

Commit `eb5a6ae` adds persistent `#balanceProgressBanner` DOM element with `aria-live="polite"` and JS poll loop against `/api/ws/balance-job/<id>/`. Test `test_bb_balance_after_edit` (covered in `test_bb_bal` full pass) confirms the job runs end-to-end after a Verbrauch edit.

**Live banner streaming was verified previously** on Heroku `prosim-100-687a5505e19f` per `VERIFICATION_STATUS.md` §2 — banner text updated every 2 s ("Status: queued · Job 143f15a1 · 2s … 85s"), `aria-live` preserved, `<strong>` text "Balance läuft …".

**Caveat for this audit:** I did not re-execute the banner streaming live today (would have dirtied testsim and required ~90 s of polling). Banner DOM is present in /ws/ HTML structure (verified via console / DOM inspection in prior phase). Cross-process cache fix (`54d4567`) holds.
