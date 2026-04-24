# T33 — Verdict: **PASS-WITH-CAVEAT**

**Implementation:** Native German via `TRANSLATION_GLOSSARY.md` (committed in Phase 2-A); commits `6c82cce` + `b8e4a45` apply it.
**Test module:** `simulator.test_bb_current_app` does spot-checks of expected German phrasings.

**V4 / V5 evidence (positive):** all 12 captured pages use natural-feeling German energy-domain terminology:
- "Erneuerbare Energien" (not "Erneubare Energien" Google quirk)
- "Szenario-Abgleich" (not "Szenario-Bilanz" or "Szenario-Reconciliation")
- "Speicherdrift" (compact, not "Speicherungsabweichung")
- "Bedarfs-Kraftwerke Biobrennstoffe" — domain-correct terminology
- "Wieviel werden wir noch brauchen?" + "Wo soll es herkommen?" (idiomatic German questions per PDF Excel screenshot)
- "Modifikations-Historie" + "Nachverfolgung" — matches PDF's exact term

**Caveats — found English residues (eyeball):**
1. **Renewable page "Letzte Änderungen" panel empty state:** "No changes yet. When you modify renewable values, they will appear here." (visible in `screenshots/{localhost,heroku}/03_renewable.png`). Should be German. **Real T33 leak** — present on both envs.
2. **Login flash message:** "Welcome back, testsim!" appears on first visit after login (visible in localhost login snapshot). Comes from Django's default `auth.signals` flash; should be German.
3. **/cockpit/ "Status (Aktuell)" + "Ziel (2050)"** — PDF + CLAUDE.md target year is 2045, not 2050. Not a translation issue per se, but a copy-vs-data mismatch.

These are 2-3 minor residues across 12 pages — not "translation incomplete", but a clean-up follow-up worth opening as a small ticket.

**Verdict:** PASS-WITH-CAVEAT — overwhelming majority is native German; 2-3 small residues remain (Renewable empty state, login flash, Cockpit year). Open follow-up: sweep for English in dynamic flash/JS-injected text.

## Caveat resolved 2026-04-24 (Fix 1) — CAVEAT → PASS

All 3 documented residues + 2 additional siblings found during V5 sweep fixed in commits `e340cbc` + `8b06b12`:

| Residue | File / Line | Fix |
|---|---|---|
| Cockpit "Ziel (2050)" | `cockpit.html:191` | "Ziel (2045)" (year + language) |
| LandUse empty-state "No changes yet" | `landuse_list.html:2214` | "Noch keine Änderungen" |
| Renewable empty-state full sentence | `renewable_list.html:517` | German equivalent |
| Login flash "Welcome back" | `page_auth.py:33` | "Willkommen zurück" |
| "Invalid username or password." | `page_auth.py:36,38` | "Ungültiger Benutzername oder Passwort." |
| "Account created…" | `page_auth.py:50` | German equivalent |
| "Please correct the errors below." | `page_auth.py:53` | German equivalent |
| "You have been successfully logged out." | `page_auth.py:61` | "Sie wurden erfolgreich abgemeldet." |
| LandUse pill "${count} changes loaded" | `landuse_list.html:2318` | "${count} Änderungen geladen" |
| LandUse pill "No saved changes" | `landuse_list.html:2324` | "Keine gespeicherten Änderungen" |

V2 — `simulator.test_bb_german_ui::GermanUIResiduesTests` 6/6 ✅
V4 — localhost screenshots under `verification/final_audit/caveat_fixes/localhost/fix1_*.png`
V5 — Heroku screenshots under `verification/final_audit/caveat_fixes/heroku/fix1_*.png` (app `prosim-100-a2eca0df3011`, now destroyed)
V6 — this section + `index.md` updated
