# T63 — Verdict: **PASS**

`screenshots/{localhost,heroku}/10_historie.png` shows the hint banner: *"Diese Seite zeigt die Nachverfolgung Ihrer Änderungen (Phase 6-A, PDF §2.5.8). Sie ist **einsehbar, aber nicht rücksetzbar** – zum Zurückkehren auf einen früheren Stand verwenden Sie Szenarien → Wiederherstellen oder Auf Baseline zurücksetzen."*

Exact German wording matches PDF intent. NO restore/revert button per row in the page DOM. Test `test_bb_history::test_inspect_only_no_restore_button` ✅ green.
