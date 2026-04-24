# T23 — Verdict: **PASS-WITH-CAVEAT**

Commit `eb5a6ae` adds persistent `#balanceProgressBanner` DOM element with `aria-live="polite"` and JS poll loop against `/api/ws/balance-job/<id>/`. Test `test_bb_balance_after_edit` (covered in `test_bb_bal` full pass) confirms the job runs end-to-end after a Verbrauch edit.

**Live banner streaming was verified previously** on Heroku `prosim-100-687a5505e19f` per `VERIFICATION_STATUS.md` §2 — banner text updated every 2 s ("Status: queued · Job 143f15a1 · 2s … 85s"), `aria-live` preserved, `<strong>` text "Balance läuft …".

**Caveat for this audit:** I did not re-execute the banner streaming live today (would have dirtied testsim and required ~90 s of polling). Banner DOM is present in /ws/ HTML structure (verified via console / DOM inspection in prior phase). Cross-process cache fix (`54d4567`) holds.

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. DOM + prior V5 banner streaming verification sufficient; fresh ~90 s polling re-capture not scheduled. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.

## Source-grounded rationale (2026-04-24)

Per `verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q5 — the PDF's
only rigor mention for this item is §2.4.3:

> *„Während der Tests waren die Buttons nach Szenario-Änderungen meist
> ohne Funktion, nach Betätigung erfolgte kein Abgleich **und keine
> Busy-Anzeige**."*

The bar is "the busy indicator must exist". `#balanceProgressBanner`
DOM is present + `aria-live="polite"` wired + cross-process cache fix
lands the Balance job correctly. The PDF does NOT prescribe polling
cadence, message format, ARIA dynamics, or stream-latency criteria.
Live-streaming re-capture is therefore above-spec; acceptance is
PDF-grounded.
