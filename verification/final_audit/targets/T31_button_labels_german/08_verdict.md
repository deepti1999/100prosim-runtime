# T31 — Verdict: **PASS-WITH-CAVEAT**

**Implementation:** commit `6c82cce` (Phase 2-A).
**Test module:** `simulator.test_bb_current_app` ✅ green.

**V4 / V5 evidence (German buttons captured):**

| Page | Button labels observed (all German) |
|---|---|
| /login/ | "Anmelden", "Hier registrieren" |
| /simulation/ | "Details anzeigen" (×8), "Exportieren" |
| /landuse/ | "Speicher löschen", edit pencil icon |
| /renewable/ | "Vollständige Tabelle anzeigen", "Löschen" |
| /gebaeudewarme/ | "Alle Werte speichern", "CSV exportieren" |
| /ws/ | "Balance Solar", "Balance Wind", "Zur Seite Jahresstrom" |
| /cockpit/ | "Tabellen Ansicht", "Status (Aktuell)", "Ziel (2050)" |
| /annual-electricity/ | "75 % / 100 % / 125 % / 150 % / 200 %" zoom buttons, "365 Tage", "CSV Export" |
| /bilanz/ | "GWh / Tagesladung" toggle, "Status Bilanz / Ziel Bilanz" tabs |

**Caveats:**
1. **"Balance Solar" / "Balance Wind"** are English-rooted technical terms used in the German energy domain. Pascal's `TRANSLATION_GLOSSARY.md` Phase 2 decision was to KEEP these as-is (not translate to "Solar-Abgleich" etc.) because the term "Balance" appears in the PDF's own German body text (§2.4.3 lists "Balance" untranslated as a button name). This is a documented intentional choice, NOT a missed translation.
2. **CSV** is universal — kept literal.

**Verdict:** PASS-WITH-CAVEAT — all user-facing button labels are German per the glossary, with documented exceptions for domain-standard untranslatable terms.
