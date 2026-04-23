# PDF coverage — page-to-target map

**PDF source:** `docs/stakeholder/260403_Portierung_Bestandsaufnahme.pdf` (12 pages, H. Schmidt-Kanefendt 2026-04-03).
**Extracted text:** `verification/final_audit/pdf_text/portierung_bestandsaufnahme.txt` (via `pdftotext -layout`).
**Translation references:** `docs/stakeholder/260403_Bestandsaufnahme_DE.md` (canonical German), `260403_Bestandsaufnahme_EN.md` (English).

## Methodology

Walked the extracted PDF text section-by-section. For each section, listed the atomic asks it contains and the T-IDs that map to those asks per `IMPLEMENTATION_PLAN.md` §3 master table. Anything in the PDF text that **does not** correspond to a T-ID is flagged as "uncovered" with a judgement on whether it is a real gap or an artefact (a footer, a page-break header, a paraphrased version of an already-covered ask).

## Section-by-section coverage

### Page 1 — Cover + table of contents

PDF text lines 1–30. Pure index, no asks. **Uncovered: not applicable.**

### Page 2 — §1 Anlass + §2.1 Hosting + §2.2 Antwortzeiten

Lines 33–80.

| PDF text (paraphrased) | T-IDs |
|---|---|
| "Bereitstellung einer geeigneten Rechnerplattform" | T1 |
| "lauffähige Installation" | T2 |
| "Bildung von Hosting-Knowhow bei ErnES-AdministratorInnen (mindestens 2 Personen)" | T3 |
| Implied from §2.1: "Login-Userdaten aus dem vorhergehenden Hosting waren nicht mehr bekannt" → recovery procedure | T4 |
| Acid test: onshore 2.0→2.3 %, offshore 70→60 GW, measure | T5 |
| Implied: reproducible benchmark script | T6 |
| Conditional: "Falls so keine praxistauglichen Antwortzeiten erreicht werden, müsste die Software-Architektur überprüft werden" | T7 |

**Uncovered:** "Praxistaugliche Antwortzeiten" success threshold itself — PDF deliberately does not numerically pin it ("praxistauglich"), and `IMPLEMENTATION_PLAN.md` §12 confirms threshold is to be agreed with Schmidt-Kanefendt. Not a gap, by design.

### Page 3 — §2.3 Datenmodell

Lines 84–116.

| PDF text | T-IDs |
|---|---|
| §2.3.1 "Quellbezüge … einfach und direkt über Verlinkung nachvollziehbar" | T8 |
| §2.3.1 "getroffenen Annahmen" likewise traceable | T9 |
| §2.3.1 "Parameter-Aktualisierung des Basis-Szenarios durch die Administrierenden … erforderlich" | T10 |
| §2.3.2 "verschiedene Bundesländer" | T11 |
| §2.3.2 "Schnittstelle zur Nutzung der bestehenden Excel-Datenmodell-Dateien" | T12 |
| §2.3.2 "spezielle Admin-Rechte sind nicht erforderlich" | T13 |

**Uncovered:** none. T8–T13 cover both subsections.

**Note:** PDF says "Vorschlag" (proposal) at the start of §2.3 and again at the end of §2.3.2. The framing is "we propose this approach"; the asks are the listed properties (traceability, multi-region, admin-edit). Per `260403_Section_2.3_decision.md`, we ship the **properties**, not necessarily the **mechanism** ("Excel as live source"); this nuance is captured in T8–T13 phrasing in `IMPLEMENTATION_PLAN.md` §3.

### Page 4 — §2.4.1 Basis-Wert + §2.4.2 Baseline

Lines 121–157.

| PDF text | T-IDs |
|---|---|
| §2.4.1 "Nach Löschen der Modifikation erscheint automatisch wieder der ursprüngliche Wert" | T14 |
| §2.4.1 implied: applies to all modification surfaces (Verbrauch + Erneuerbare + Flächen — the three places "Modifikation" applies in our app) | T15 (extrapolated) |
| §2.4.2 "Vorschlag: … der Menüpunkt 'Baseline erstellen' kann entfallen" | T16 |
| §2.4.2 "'Auf Baseline zurücksetzen' dazu nutzen, als Baseline das administrierte Basisszenario zu laden" | T17 |
| §2.4.2 "ein zentrales Basisszenario als gemeinsame Baseline" → shared across users | T18 |

**Uncovered:** none.

### Page 5 — §2.4.3 Szenario-Abgleich + §2.4.4 Recalculate + §2.4.5 Save All Values

Lines 161–211.

| PDF text | T-IDs |
|---|---|
| §2.4.3 "Buttons 'Goal Seek' … sind … überflüssig, … wären sie zu löschen" | T19 |
| §2.4.3 "Aktualisieren" (same sentence) | T20 |
| §2.4.3 "ein Botton WS Balance Solar" — single button merging WS Solar + Sector+WS Solar | T21 |
| §2.4.3 same for Wind | T22 |
| §2.4.3 "Buttons nach Szenario-Änderungen meist ohne Funktion … keine Busy-Anzeige" | T23 |
| §2.4.4 "die gesamte Kalkulation … nach jeder Änderung sofort automatisch" — Verbrauch | T24 |
| §2.4.4 same — Erneuerbare ("User Input-Änderungen auf der Seite Erneuerbare") | T25 |
| §2.4.4 same — Flächen (implied; "Kalkulation von Flächen" is part of the list) | T26 |
| §2.4.4 implied: clear feedback that the cascade ran | T27 |
| §2.4.5 "Save All Values' Button überflüssig und unnötig verwirrend" | T28 |

**Uncovered:** none.

### Page 6 — §2.5.1 Englisch-Deutsch + §2.5.2 Zahlenformat

Lines 215–237.

| PDF text | T-IDs |
|---|---|
| §2.5.1 "Überschrift der Seite lautet aber noch Renewable Energy…" | T29 |
| §2.5.1 "sämtliche Spalten" English | T30 |
| §2.5.1 "Buttons … englisch beschriftet" | T31 |
| §2.5.1 "Benutzerhandbuch … komplett in englischer Sprache" | T32 |
| §2.5.1 "Bei … Google-Übersetzung … fehlerhafter Übersetzung" — implies native German required | T33 |
| §2.5.2 "englischen Zahlenformat … sehr verwirrend" — German display format required | T34 |
| §2.5.2 implied: input parsing must accept the display format you're showing | T35 |
| §2.5.2 implied: applies to JS-rendered values too (otherwise inconsistent) | T36 |

**Uncovered:** none.

### Page 7 — §2.5.3 Menüführung

Lines 242–251.

| PDF text | T-IDs |
|---|---|
| §2.5.3 "fehlt auf den Seiten 'Verbrauch', 'Jahresstrom' und 'Benutzerhandbuch'" | T37, T38, T39 |
| §2.5.3 "Auf der Seite 'Cockpit' ist es zwar vorhanden, aber anders formatiert" | T40 |
| §2.5.3 "Die linken Einträge in der oberen Menüleiste wären doppelt" | T41 |
| §2.5.3 "wenn … dort auch der Menüpunkt '100prosim' angeordnet würde" | T42 |

**Uncovered:** none.

### Page 8 — §2.5.4 Ergebnisübersicht

Lines 254–262.

| PDF text + screenshot | T-IDs |
|---|---|
| §2.5.4 "Anzeige in 100prosim-Excel, Status und Ziel mit den einzelnen Anteilen gegenübergestellt" | T43, T44 |
| §2.5.4 screenshot shows left column "Wieviel werden wir noch brauchen?" (extrapolated from screenshot, no exact text) | T45 |
| §2.5.4 screenshot shows right column "Wo soll es herkommen?" (likewise) | T46 |
| §2.5.4 screenshot shows annotated -27 %, ×5.2 deltas (likewise) | T47 |

**Uncovered:** none. The exact column titles ("Wieviel" / "Wo") come from the Excel screenshot embedded in the PDF, not from PDF text body — `IMPLEMENTATION_PLAN.md` §3 marks them as "extrapolated from same screenshot". Acceptable extrapolation.

### Page 9 — §2.5.5 Modifikationsdetails

Lines 265–272.

| PDF text + 5 chart screenshots | T-IDs |
|---|---|
| §2.5.5 implies 5 chart types from Excel AH.Cockpit2 | T48, T49, T50, T51, T52 |

**Uncovered:** none. Each of the 5 Excel screenshots maps 1:1 to a T-ID.

### Page 10 — §2.5.6 Flussdiagramm Strom/H₂

Lines 277–284.

| PDF text + Excel reference diagram | T-IDs |
|---|---|
| §2.5.6 implied: structural audit needed before fix | T53 |
| §2.5.6 "teilweise sind die Werte falsch zugeordnet" | T54 |
| §2.5.6 "wegen der kleinen Schriftart … schlecht lesbar" | T55 |
| §2.5.6 "Die Vorlage aus 100prosim-Excel" — match Excel structure (Bedarfs-KW, PV, Wind, Laufwasser+Geoth → Elektrolyse → Stromspeicher → Rückverstromung; branches: Abregelung, Gasspeicher Direktverbr, Gasspeicher Strom) | T56 |

**Uncovered:** none. T54 has 6 named sub-asks (D1-D4c per `HARDCODED_VALUES_TRACE.md` §6) — all 6 shipped per Track 1 + Phase B.

### Page 11 — §2.5.7 Jahresgang Strom

Lines 289–309.

| PDF text | T-IDs |
|---|---|
| §2.5.7 "Mindestkapazität resultiert aus … Max − Min" | T57 |
| §2.5.7 "Tageswerte der Deckungsbeiträge bzw. Überschüsse von Wind-/Solarstrom" | T58 |
| §2.5.7 "Mangelausgleich" | T59 |
| §2.5.7 "Anstelle von Absolutwerten in GWh wird hier die Einheit Tagesladung verwendet" | T60 |

**Uncovered:** none.

### Page 12 — §2.5.8 Modifikations-Historie

Lines 314–326.

| PDF text + Excel screenshot | T-IDs |
|---|---|
| §2.5.8 "lässt sich die Modifikation des Basis-Szenarios Schritt für Schritt protokollieren" | T61 |
| §2.5.8 screenshot shows snapshot columns (Excel AH.Monitor layout) | T62 |
| §2.5.8 "Nachverfolgung … bezüglich Maßnahme und … Wirkung" — inspectable, not undoable | T63 |

**Uncovered:** none.

## Summary

| Page | Section(s) | T-IDs | Uncovered text |
|---|---|---|---|
| 1 | TOC | — | n/a |
| 2 | §1, §2.1, §2.2 | T1–T7 | "praxistauglich" threshold (deliberately not pinned) |
| 3 | §2.3 | T8–T13 | none |
| 4 | §2.4.1, §2.4.2 | T14–T18 | none |
| 5 | §2.4.3, §2.4.4, §2.4.5 | T19–T28 | none |
| 6 | §2.5.1, §2.5.2 | T29–T36 | none |
| 7 | §2.5.3 | T37–T42 | none |
| 8 | §2.5.4 | T43–T47 | column titles extrapolated from Excel screenshot |
| 9 | §2.5.5 | T48–T52 | none |
| 10 | §2.5.6 | T53–T56 (incl. T54 D1–D4c subitems) | none |
| 11 | §2.5.7 | T57–T60 | none |
| 12 | §2.5.8 | T61–T63 | none |

**Total: 63 T-IDs map to all 12 pages of the PDF.** No uncovered atomic ask except the "praxistauglich" performance threshold, which is deliberately stakeholder-negotiable per PDF text.

**Verdict: PDF coverage is complete.** Every page maps to its T-IDs; every atomic ask in the PDF body is decomposed into a target.
