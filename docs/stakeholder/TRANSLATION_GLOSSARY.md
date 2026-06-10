# Translation glossary — Phase 2 (German UI)

**Purpose.** Source-of-truth mapping for English → German UI strings in 100prosim-Web. Per stakeholder PDF §2.5.1 + §2.5.3, a substantial fraction of the app is still English-labelled despite the menu saying "Erneuerbare Energien". This glossary gets reviewed + approved by Pascal before we mass-edit templates.

**Rules:**

1. **Domain cell codes are frozen.** Never translate: `LU_0`, `LU_2.1`, `LU_6`, `9.3.1`, `9.3.4`, `10.1`, `10.2`, `KLIK`, `Gebäudewärme`, `Prozesswärme`, `Mobile Anwendungen`, `Verbrauch`, `Bilanz`, `WS 365`, `Jahresstrom`. These are stakeholder contracts.
2. **Native German, not Google Translate** (T33). Where the PDF already uses a term in German (§§2.4, 2.5), we match it verbatim.
3. **Code identifiers stay English.** Python function names, CSS classes, JS variables, template block names — all stay as-is. Only user-facing text is translated.
4. **Loanwords stay** where German professional usage already accepts them: `Baseline`, `Scenarios`, `Cockpit`, `Dashboard` (controversial — flagged below), `Status`, `Target` (flagged below).

---

## 1. Page titles + block titles

| English (current) | German (proposed) | Notes |
|---|---|---|
| `Land Use Data - All Records` | `Flächennutzung – Datenübersicht` | Matches sidebar menu "Flächennutzung" |
| `Renewable Energy Data - Solar Overview` | `Erneuerbare Energien – Datenübersicht` | Matches sidebar menu |
| `Cockpit - Visual Energy Dashboard` | `Cockpit – Energie-Übersicht` | "Cockpit" is a loanword used in 100prosim-Excel (AH.Cockpit1) |
| `Bilanz Endenergie - Energy Balance Sheet` | `Bilanz Endenergie` | Strip the redundant English tail |
| `Gebäudewärme – Building Heat` | `Gebäudewärme` | Already German, strip English tail |
| `Verbrauch – Energy Consumption` | `Verbrauch` | Already German, strip English tail |
| `100ProSim - Erneuerbare Energie Simulation` (base.html) | *(keep)* | Already German |

## 2. Main page headings (<h1>)

| English | German |
|---|---|
| `Land Use Data Overview` | `Flächennutzung – Übersicht` |
| `Renewable Energy Data Overview` | `Erneuerbare Energien – Übersicht` |
| `Quick Start Guide` | `Kurzanleitung` |
| `System Architecture` | `Systemarchitektur` |
| `User Manual - Land Use Data Management` | `Benutzerhandbuch – Flächennutzung` |

## 3. Table column headers

These are the biggest stakeholder complaint — columns still English on multiple pages.

| English | German | Where |
|---|---|---|
| `Code` | `Code` | Universal — stays (alpha-numeric identifier) |
| `Parameter Hierarchy` | `Parameter-Hierarchie` | /renewable/ |
| `Unit` | `Einheit` | /renewable/, /verbrauch/, /landuse/ |
| `Status Value` | `Status` | /renewable/, /verbrauch/ — match Excel AH.Cockpit1 (PDF §2.5.4) |
| `Target Value` | `Ziel` | /renewable/, /verbrauch/ — match Excel AH.Cockpit1 (PDF §2.5.4) |
| `User Input` | `Benutzereingabe` | Everywhere |
| `Status (ha)` / `Status (%)` | `Status (ha)` / `Status (%)` | Keep — unit in parentheses is universal |
| `Target (ha)` / `Target (%)` | `Ziel (ha)` / `Ziel (%)` | /landuse/ |
| `User (%)` | `Benutzer (%)` | /landuse/ |
| `Land Use Type / Energy Use` | `Flächennutzung / Energieverwendung` | /landuse/ |
| `Categories` | `Kategorien` | /landuse/ side panel |

> **Pascal to confirm:** "Status" and "Ziel" align with 100prosim-Excel's convention. PDF §2.5.4 shows Excel uses exactly `Status` / `Ziel` — we should match.

## 4. Buttons

| English | German | Notes |
|---|---|---|
| `Recalculate Renewables` | *(removed in Phase 4-E)* | Auto-cascade replaces manual button |
| `Recalculate All` | `Alles neu berechnen` | If kept for admin |
| `Show Full Table (Sections 1-9)` | `Vollständige Tabelle anzeigen (Abschnitte 1–9)` | |
| `Back to Dashboard` | `Zurück zur Übersicht` | |
| `Back to Home` | `Zurück zur Startseite` | |
| `Sign In` | `Anmelden` | Login form |
| `Register` / `Create one here` | `Registrieren` / `Hier registrieren` | |
| `Logout` | `Abmelden` | |
| `Save current Scenario` | `Aktuelles Szenario speichern` | PDF §2.4.5 uses this wording |
| `Create Scenario` | `Szenario erstellen` | |
| `Restore Scenario` | `Szenario wiederherstellen` | |
| `Delete Scenario` | `Szenario löschen` | |
| `Baseline erstellen` | *(removed in Phase 4-B)* | Stakeholder asked for removal |
| `Auf Baseline zurücksetzen` | *(keep)* | Already German |
| `Clear all changes` | `Alle Änderungen löschen` | Changes panel |

## 5. Card / section labels

| English | German |
|---|---|
| `Recent Changes` | `Letzte Änderungen` |
| `Changes persist after page refresh` | `Änderungen bleiben nach dem Seiten-Neuladen erhalten` |
| `Renewable Energy Information` | `Hinweise zu Erneuerbaren Energien` |
| `Solar Overview` | `Solar-Übersicht` |
| `Wind Overview` | `Wind-Übersicht` |
| `records` (as in "223 records") | `Datensätze` |
| `Quick Start` | `Schnellstart` |

## 6. Confirmation dialogs / alerts

These use `alert()` / `confirm()` in JS; long sentences. Translations must preserve line breaks (`\n`).

| English | German |
|---|---|
| `WARNING: Reset to Baseline?\nThis will DELETE all current data and restore the database to the baseline snapshot.\nALL CHANGES since the baseline will be LOST!\nAre you absolutely sure?` | `WARNUNG: Auf Baseline zurücksetzen?\nAlle aktuellen Daten werden GELÖSCHT und der Stand wird auf das Baseline-Szenario zurückgesetzt.\nAlle Änderungen seit der Baseline gehen VERLOREN!\nSind Sie absolut sicher?` | **Locked.** `WARNUNG:` for genuinely destructive data-loss dialogs. |
| `Baseline snapshot created successfully!` | `Baseline-Snapshot erfolgreich erstellt!` |
| `Restored to baseline successfully!` | `Erfolgreich auf Baseline zurückgesetzt!` |
| `No baseline exists yet.` | `Noch keine Baseline vorhanden.` |
| `Failed to save` | `Speichern fehlgeschlagen` |
| `Successfully saved N values!` | `N Werte erfolgreich gespeichert!` |

## 7. Footer

| English | German |
|---|---|
| `© 2025 Land Use Data Viewer \| Built with Django & Bootstrap` | `© 2026 100ProSim \| Django & Bootstrap` | **Locked.** App is live in 2026; the "Land Use Data Viewer" prototype name is gone. |

## 8. Loanwords to keep (per usage in 100prosim-Excel or German web convention)

- `Baseline` — PDF uses the loanword directly
- `Scenario` / `Scenarios` (context-dependent) — but `Szenario`/`Szenarien` is preferred per PDF wording
- `Cockpit` — PDF §2.5.4 + Excel AH.Cockpit1/2 use this loanword
- `Dashboard` — **decision:** translate to `Übersicht` everywhere, for consistency with `Simulations-Übersicht`.
- `Goal Seek` — already removed in Phase 1-B
- `Balance` (noun) / `Balance Solar` / `Balance Wind` — PDF §2.4.3 uses German `WS Balance Solar` mixed form. Keep.

## 9. Strings that look English but are in Python code or test identifiers

These stay English (code-facing, not user-facing):

- `owner_scope`, `workspace_signals`, `recalc_cache`, `BalanceJob`
- All Django URL names: `simulator:ws_api_data`, `simulator:baseline_restore`
- Test file names: `test_bb_*`, `test_e2e_*`

---

## Locked decisions (Pascal 2026-04-22)

1. **Column headers:** `Status Value` → `Status`, `Target Value` → `Ziel`. Match Excel AH.Cockpit1 verbatim.
2. **`Dashboard` → `Übersicht`** everywhere, consistent with `Simulations-Übersicht`.
3. **Footer:** `© 2026 100ProSim | Django & Bootstrap` — drop the prototype name.
4. **Alert severity:**
   - `Achtung:` — default for non-destructive warnings.
   - `WARNUNG:` — reserved for genuinely destructive actions (Reset to Baseline, Delete Scenario).
5. **`/smard/` system-architecture page IS translated.** The rule is never-skip from the PDF §2.5.1 ("ein erheblicher Teil der Begriffe" — substantial part). Even though /smard/ is not linked from the nav, it's reachable by URL and rendered in the user's browser → user-facing → in scope.

## /smard/ — specific additions

| English | German |
|---|---|
| `System Architecture` (h1) | `Systemarchitektur` |
| `Energy Simulation Platform - Data Flow Diagram` | `Energie-Simulationsplattform – Datenflussdiagramm` |
| `Technology Stack` | `Technologie-Stack` |
| `Chart.js Graphs • Dashboard` | `Chart.js-Diagramme • Übersicht` |
| `User Interface Layer` | `Benutzeroberfläche` |
| `Application Logic Layer` | `Anwendungslogik` |
| `Data Layer` | `Datenschicht` |
| `External Data Sources` | `Externe Datenquellen` |
| `Interactive Balancing System - Use Case Diagram` (h2) | `Interaktives Balancing-System – Anwendungsfall-Diagramm` |

(Other architecture-box labels translated inline during 2-A edit.)

## Approval

- [x] Decisions locked (2026-04-22)
- [x] Open questions answered
- [x] Cleared to proceed with Phase 2-A mass-edit
