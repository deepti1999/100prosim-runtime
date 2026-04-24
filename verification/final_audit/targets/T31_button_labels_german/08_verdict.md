# T31 — Verdict: **PASS**

*(upgraded 2026-04-24 ACCEPTED → PASS on source-grounded reading — see
`verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q3.)*

## Source-grounded closure 2026-04-24

PDF §2.4.3 itself proposes "WS Balance Wind" + "WS Balance Solar" as
the post-consolidation button names. Not an accidental left-over
Englishism — actively-endorsed German-energy-domain terminology.
Verbatim:

> *„Unklar ist, weshalb die Buttons ,WS Balance ....` und Sector + WS
> … Balance jeweils nacheinander in dieser Reihenfolge betätigt
> werden müssen. Dies sollte durch jeweils einen **Button WS Balance
> Wind bzw. WS Balance Solar** möglich gemacht werden."* (§2.4.3,
> PDF p. 5)

The PDF's §2.5.1 localisation-sweep rule ("sämtliche … Buttons
sind noch englisch beschriftet") is a general direction; §2.4.3's
specific button-naming proposal is the governing text for these two
buttons. No conflict — "Balance" is the accepted domain-loanword.

---

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

## Prior "Caveat accepted" note (now superseded)

~~*Caveat retained — not scheduled for fix. "Balance Solar" / "Balance Wind" / "CSV" are intentional per `TRANSLATION_GLOSSARY.md` Phase 2.*~~ — verdict upgraded to PASS 2026-04-24; no longer in `docs/stakeholder/CAVEATS_ACCEPTED.md`.
