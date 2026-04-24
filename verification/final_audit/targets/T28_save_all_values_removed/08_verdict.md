# T28 — Verdict: **PASS** (scope clarified 2026-04-24)

PASS at the literal level: "Save All Values" button is absent from `/landuse/` on both localhost and live Heroku. PDF §2.4.5 ask satisfied for the page the PDF named.

## Scope alignment 2026-04-24 (Fix 2) — CAVEAT → PASS

Re-read of PDF §2.4.5 (`docs/stakeholder/260403_Bestandsaufnahme_DE.md` line 101-103):

> *„Beim aktuellen 100prosim-Web wird den Anwendenden **auf der Seite „Flächen"** der Button „Save All Values" angeboten. Die Speicherung der Flächenwerte soll vermutlich eine spätere Wiederherstellung des gespeicherten Flächendaten-Standes ermöglichen. Allerdings ist dies **weder für die User-Daten der Erneuerbaren noch für den Verbrauch vorgesehen**. Die Funktion wäre nur dann sinnvoll, wenn sämtliche Scenario-Werte für eine spätere Weiterbearbeitung dieser Szenariovariante gespeichert würden. Dies wird offenbar durch „Scenarios" – „Save current Scenario" (obere Menüleiste rechts) ermöglicht. Wenn dem so ist, ist der **Button „Save All Values" überflüssig** und unnötig verwirrend."*

English gloss:

> *"In the current 100prosim-Web, users are offered the 'Save All Values' button on the **Flächen page**. The button's presumed purpose is to let users restore a saved state of area values later. However, this is **not provided for Erneuerbare or Verbrauch user-data**. The function would only make sense if all scenario values were saved for later scenario-variant editing. This is apparently already provided by 'Scenarios → Save current Scenario' (top-right menu bar). If so, the **'Save All Values' button is redundant** and unnecessarily confusing."*

**PDF scope is literally Flächen-only.** The passage names the Flächen page explicitly and observes that Erneuerbare and Verbrauch do NOT have an analogous button — implying the critique is about the one Flächen button, not a per-page pattern to sweep. The PDF does NOT mention Gebäudewärme or its "Alle Werte speichern" button, which is a separate button with its own JS logic + CSV export sibling.

**Decision:** retain `/gebaeudewarme/` button. Documented intentional scope. V2 test `T28SaveAllScopeTests::test_gebaeudewaerme_retains_alle_werte_speichern` locks this in.

If stakeholders later ask to remove the Gebäudewärme button too, that is a new scope item (T67 or similar), not a re-open of T28.

## Verification ledger

| Step | Evidence |
|---|---|
| V2 | `simulator.test_bb_german_ui::T28SaveAllScopeTests` 2/2 ✅ — /landuse/ has no `#saveAllBtn`; /gebaeudewarme/ does. |
| V4 localhost | `verification/final_audit/caveat_fixes/localhost/fix2_landuse_no_button_still.png` (no button) + `fix2_gebaeudewarme_button_retained.png` (button visible). |
| V5 Heroku | Batched with Fix 1 — see `verification/final_audit/caveat_fixes/heroku/fix2_*.png`. |
| V6 | This verdict update + `verification/final_audit/index.md` tally + `docs_drift.md` item 3 closure. |
