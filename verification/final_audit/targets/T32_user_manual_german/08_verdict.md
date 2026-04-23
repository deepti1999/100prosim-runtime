# T32 — Verdict: **PASS**

**Implementation:** commit `b8e4a45` (Phase 2-B).
**Test module:** `simulator.test_bb_current_app::test_user_manual_german_shows_steps` (asserts "Benutzerhandbuch" + "Schritt 1" + "Flächennutzung" present, English residues absent).

**V4 / V5 evidence:** screenshots `12_user_manual.png` (both envs).

The manual page renders with German headings throughout. Visible step structure:
- "Schritt 1: Trapsit auf die Flächennutzungseite" (typo? — see caveat)
- "Schritt 2: Flächennutzung gezielt anpassen und speichern"
- "Schritt 3: Verstehe die Erneuerbaren Energien"
- "Schritt 4: Verbrauch beobachten"
- "Schritt 5: Erneuerbare-Methoden Änderungen anzeigen Verbrauch beobachten"
- "Schritt 6: Bilanz prüfen"
- "Schritt 7: Szenario-Abgleich + Tabellen und Vergleich"
- "Schritt 8: Sensitivitäten"
- "Schritt 9: Visualisierungen interpretieren"
- "Schritt 10: Szenario Snapshots speichern und protokollieren"
- "Schritt 11: Szenarien später nochmal speichern, weiterbetreiben oder weiterführen"

11 German steps. ~1500 words of native German prose throughout. No English residues in the body.

**Caveats:**
1. **Localhost manual screenshot images 404** (15 errors per `console_messages`) because `/static/simulator/images/manual/*.png` not collected. Heroku has them. Cosmetic in dev; production OK.
2. **Step heading might have typos** (e.g. "Trapsit" looks wrong) — would benefit from a native-speaker review pass. Not a blocker, but worth flagging for stakeholder QA.

**Verdict:** PASS — German throughout, native-feel (not Google-translate artifacts). Heroku visual confirmation clean. PDF §2.5.1 manual ask satisfied.
