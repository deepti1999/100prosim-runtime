# Phase 6 — shared evidence (variant-compare charts + history)

## PDF source
§2.5.5 Modifikationsdetails (page 9) → 6-B (T48-T52 five chart types).
§2.5.8 Modifikations-Historie (page 12) → 6-A (T61-T63 history page).

## Implementation
- 6-A history: commit `1051de0`, `simulator/models.py::ModificationHistoryEntry` model, `migrations/0050`, `/historie/` page + view, signal/wrapper logs entries on user save.
- 6-B charts: commit `92ae451`, `/modifikationsdetails/` page with 5 chart canvases, 4-series JSON (Status / Basisszenario / Vorzustand / Aktueller Zustand).

## V2 — tests
- `test_bb_history` 5/5 ✅
- `test_bb_modifikationsdetails` 4/4 (+ 3 added 2026-04-22 covering populated Basisszenario fallback) = 7/7 ✅

## V4 / V5 — visual evidence
**/modifikationsdetails/ (`screenshots/{localhost,heroku}/11_modifikationsdetails.png`):**
All 5 charts rendered with 4-series legend on both envs:
1. "Nachfrage-Einflüsse auf Endenergieverbrauch (Variantenvergleich)" — Einheit GWh/a → T48 ✓
2. "Effizienz-Einflüsse auf Endenergieverbrauch (Variantenvergleich)" — Einheit % → T49 ✓
3. "Endenergie-Verbrauch nach Anwendungsbereichen inkl. Grundstoffe" — TWh/a → T50 ✓
4. "Primärenergie-Beiträge nach Quellen" — TWh/a → T51 ✓
5. "Ausbau der Erneuerbaren Energiequellen" — % → T52 ✓

Each chart's legend: Status (grey) · Basisszenario (blue) · Vorzustand (orange) · Aktueller Zustand (green) — matches Excel AH.Cockpit2 4-series convention.

Notice in fresh testsim workspace: Basisszenario series is empty (warning at top: "Vorzustand-Quelle: Hinweis: Noch kein Basisszenario vom Administrator erstellt — die Serie 'Basisszenario' bleibt leer.") This is graceful degradation per `test_empty_state_renders_gracefully`.

**/historie/ (`screenshots/{localhost,heroku}/10_historie.png`):**
Empty-state German prose: "Noch keine Modifikationen protokolliert. Sobald Sie einen Wert auf Verbrauch, Flächennutzung oder Erneuerbare Energien ändern, erscheint der Eintrag hier."
+ Hint banner: "Diese Seite zeigt die Nachverfolgung Ihrer Änderungen (Phase 6-A, PDF §2.5.8). Sie ist einsehbar, aber nicht rücksetzbar – zum Zurückkehren auf einen früheren Stand verwenden Sie Szenarien → Wiederherstellen oder Auf Baseline zurücksetzen."

This is the testsim fresh-workspace state. Populated state with Excel AH.Monitor column layout was verified previously per `VERIFICATION_STATUS.md` Addendum.

## Edge cases
- **No baseline + no scenario** → graceful empty state (test_empty_state_renders_gracefully ✅)
- **No scenario but baseline exists** → Vorzustand falls back to Basisszenario (test_vorzustand_falls_back_to_baseline_when_no_scenario ✅)
- **Inspect-only (NOT undoable)** — explicitly stated in /historie/ hint per PDF "Nachverfolgung" not "Rückgängig"

## Verdict per target
T48 PASS · T49 PASS · T50 PASS · T51 PASS · T52 PASS
T61 PASS · T62 PASS-WITH-CAVEAT (column layout structurally shipped but not visible in this audit's empty workspace; previously verified populated)
T63 PASS (hint text explicitly states inspect-only, matching PDF Nachverfolgung wording)
