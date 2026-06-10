# Next changes — derived from ErnES stocktaking (2026-04-03)

Action-item digest of `260403_Bestandsaufnahme_EN.md`. Each item is phrased as something we can actually do in this codebase, with pointers to the sections of the PDF it comes from. Priorities reflect Schmidt-Kanefendt's own emphasis (hosting handover + response-time "acid test" are explicitly flagged as go/no-go for production readiness).

## Summary of what the stakeholder wants

ErnES wants to take `100prosim-Web` **beyond "working prototype"** into a state where it can **fully replace the Excel-based 100prosim** — including regional data models, the traceability of parameter sources, the richer result charts, and the modification history. The document is respectful ("a great achievement") but clear: there is a long list of gaps that need to be closed before the web tool can replace the Excel workflow stakeholders have been relying on.

---

## P0 — Blockers for production readiness

These are the stakeholder's own "acid-test" items. If they don't land, nothing else matters.

### P0-1. Hand hosting off to an ErnES platform

**Source:** §2.1
**Ask:** ErnES must install the app on its own compute platform by the end of the test phase, and at least 2 ErnES admins must have hosting know-how to avoid single-point-of-failure.
**What this means for us:**
- Document the deploy pipeline in a way an ErnES admin can follow without us. `docs/HEROKU.md` is a good base — needs adding platform-neutral deploy notes (Docker Compose already works, document it as Option B).
- The existing `scripts/heroku_up.sh` / `heroku_down.sh` are part of this handover.
- A second "runbook" page: how to reset testsim, how to rotate the seed, how to read the logs, how to restart.
- Possibly a short video / screenshare handover once ErnES picks its target platform.

### P0-2. Pass the response-time acid test

**Source:** §2.2
**Ask:** Test case — onshore wind area 2.0 % → 2.3 %, offshore 70 GW → 60 GW. Excel = 5.8 s, current web = 120 s (20× slower). On ErnES's real platform the response time must be **practically usable**. If not, the software architecture has to be reviewed and reworked.
**What this means for us:**
- This is the **single most important metric** stakeholders track. 120 s is today's state on the Heroku Basic dyno after our perf pass; stakeholder considers that too slow.
- Run the exact test case (onshore 2.0→2.3 %, offshore 70→60 GW) on the target platform as soon as ErnES picks one. Capture the number.
- If still too slow: the PyPSA integration path in `docs/PYPSA_MIGRATION_RESEARCH.md` §23.1 is the plan of record. Revisit.
- Also worth exploring before PyPSA: further parallelism of the 365-day WS loop, Standard-1X or Performance-M dyno trial, pre-warming caches at worker boot.
- **Write a reproducible benchmark script** (`scripts/bench_balance_2.3pct_60gw.sh`) so this number can be tracked cycle-over-cycle instead of re-derived each time.

---

## P1 — Core UX asks from stakeholders

Each of these is a concrete behaviour change that directly contradicts how Excel users expect the tool to work. Closing them is what makes the web tool feel like a real replacement, not a prototype.

### P1-1. Auto-recalculation on every change (remove the manual "Recalculate" step)

**Source:** §2.4.4
**Ask:** In Excel, every value change triggers a full recalc automatically and instantly. In web, users have to press "Recalculate Renewables" and the consequences of skipping it are undefined.
**What this means for us:**
- Every save of a user input on Verbrauch / Erneuerbare / Flächen should fire the appropriate recalc automatically. The existing `save-recalc-verbrauch` endpoint already does this for Verbrauch — extend the pattern.
- Remove the separate "Recalculate Renewables" button, or keep it hidden for admins only.
- Hard constraint: this must not tank response time on Heroku. Prefer fire-and-forget via the existing `BalanceJob` worker for anything >1 s; use an optimistic UI update + eventual-consistency badge for the user.

### P1-2. Reduce 6 balance buttons to 2 (Solar / Wind)

**Source:** §2.4.3
**Ask:** Excel offers exactly 2 options: adjust open solar area, or adjust onshore wind area. Web currently exposes 6 buttons (Goal Seek, WS Balance Solar, Sector+WS Solar, WS Balance Wind, Sector+WS Wind, Refresh). Users can't tell which to use.
**What this means for us:**
- Remove the "Goal Seek" and "Refresh/Aktualisieren" buttons entirely — stakeholder explicitly flags these as redundant because they already run automatically.
- Merge "WS Balance Solar" and "Sector + WS Solar Balance" into a single "Balance Solar" button whose backend orchestrates both phases.
- Do the same for wind: one "Balance Wind" button.
- Double-check the reported bug: "during testing, buttons were mostly non-functional after scenario changes — no reconciliation and no busy indicator." Confirm whether this was a real bug (possibly the cross-process cache issue we fixed in `54d4567`) or an artifact of stale browser state. If reproducible, add a regression test.

### P1-3. Restore the base value when user clears their modification

**Source:** §2.4.1
**Ask:** In Excel, clearing the user input in the modification field makes the original base-scenario value reappear. In web, the last-entered value stays in the field.
**What this means for us:**
- Treat the modification field as a distinct overlay on the base value, not as a replacement. When empty → show base value greyed out. When filled → show user value with a clear visual indicator that it's an override.
- Applies to Verbrauch target-value fields, Renewable user-input fields, and LandUse user-percent fields.
- Frontend-only change for display; backend contract can stay the same (empty user value = use base).

### P1-4. Baseline = admin-provided base scenario, not user-captured

**Source:** §2.4.2
**Ask:** Replace the user-facing "Create baseline" button. "Reset to baseline" should always reset to the **administered** base scenario. A user who forgets to create a baseline can still return to a canonical starting point. Also: the admin base must be shared across users, so different users' modifications are comparable.
**What this means for us:**
- Swap the semantics of `BaselineSnapshot`: store one canonical admin baseline (singleton per data model), seeded at import time from the Excel data model. `restore_baseline` uses that instead of the user's last-captured snapshot.
- Keep the existing per-user "Scenarios" feature (save/restore) — that's what `Scenarios → Save current Scenario` already does, and stakeholder approves of it. Just remove the overlapping "Create baseline" button.

### P1-5. Drop the "Save All Values" button on the Flächen page

**Source:** §2.4.5
**Ask:** Redundant with "Scenarios → Save current Scenario" and confusing because it only covers areas, not Renewables or Consumption.
**What this means for us:**
- Remove the button from the LandUse template.
- Make sure auto-save on blur / auto-recalc (see P1-1) makes its behaviour unnecessary.

---

## P2 — Localization and layout hygiene

Individually small, collectively they make the tool feel foreign to German stakeholders.

### P2-1. Complete the German translation

**Source:** §2.5.1
**Ask:** Many page headings, column names, button labels, and the entire user manual are still English. Menu bars already say "Erneuerbare Energien" but the page heading still says "Renewable Energy…" — inconsistent.
**What this means for us:**
- Audit every template in `simulator/templates/` for English strings. Grep for common offenders: "Renewable", "Energy", "Status", "Target", "User Input", "Save", "Recalculate", "Land Use".
- Rule of thumb: user-facing German, code-facing English. Stakeholder contract says domain cell names (LU_*, 9.3.1, sector names) stay unchanged — only the surrounding UI labels are translated.
- The user manual (`docs/` or the in-app manual page) needs a full German rewrite.

### P2-2. German number format everywhere

**Source:** §2.5.2
**Ask:** Use dot for thousands, comma for decimal, as per German convention. Currently only the Szenario-Abgleich page does this; everything else uses English (`1,234.5`).
**What this means for us:**
- Set Django `LANGUAGE_CODE = 'de'` and `USE_THOUSAND_SEPARATOR = True` if not already, and use `{% load l10n %}` / `|floatformat` correctly in templates.
- Check any JS that renders numbers (Chart.js, handcrafted formatters) — those bypass Django's i18n and need their own `toLocaleString('de-DE')`.
- Locale-aware input parsing on forms too (`1.234,5` must be accepted).

### P2-3. Consistent menu layout across all pages

**Source:** §2.5.3
**Ask:** The left side-menu is missing on Verbrauch, Jahresstrom, and Benutzerhandbuch; on Cockpit it exists but is styled differently. The left entries in the top bar duplicate the side-menu if the side-menu were universal.
**What this means for us:**
- Extract the side-menu into a shared partial (`base.html` or a `_sidebar.html`) and include it on every page.
- Once universal: remove the duplicated entries from the top bar. Keep only the account menu (Baseline / Scenarios / user dropdown) on the right.
- Move the "100prosim" branding into the side-menu header.

---

## P3 — New visualizations (Excel parity)

These are larger design/build items — each is a real feature, not a tweak. Scope them one by one.

### P3-1. Rich results overview (Status + Target side-by-side with per-sector contributions)

**Source:** §2.5.4
**Ask:** Web shows a toggle between Status or Target. Excel shows both at once with the individual contributions stacked side-by-side (see PDF page 8 "A. Wieviel werden wir noch brauchen?" / "B. Wo soll es herkommen?").
**What this means for us:**
- Redesign `/cockpit/` or a dedicated overview page around a two-column layout: left = demand by sector, right = supply by source. Stacked bars with Status + Target pairs per row.
- Include the % delta annotations (e.g. "-27 %", "x 5.2") from the Excel mock.

### P3-2. Modification-detail variant comparisons

**Source:** §2.5.5
**Ask:** Completely missing in web today. Excel's Cockpit2 sheet shows: demand drivers on final-energy consumption (variant comparison), efficiency drivers, final-energy consumption by application area incl. base materials, primary-energy contributions by source, renewable-source expansion. All as grouped bar charts with "Status / Basisszenario / Vorzustand / Aktueller Zustand" series.
**What this means for us:**
- New page `/modifikationsdetails/` (or integrated into Cockpit).
- Requires persisting two extra snapshots per session: the starting "Vorzustand" and the baseline, in addition to the current state.
- Each chart is a grouped bar with 4 series. Chart.js is sufficient.
- Stakeholder specifically calls out: **"without graphical visualization, relying only on numbers, the specifics of complex energy scenarios cannot be surveyed"** — this is strategic, not cosmetic.

### P3-3. Fix the electricity/H₂ flow diagram

**Source:** §2.5.6
**Ask:** The current diagram on Jahresstrom has wrong value assignments, structure doesn't match the scenario, and the font is too small to read. Reference is the Excel diagram on PDF page 10.
**What this means for us:**
- Compare our current flow diagram against the Excel reference node-by-node: Bedarfs-Kraftwerke / PV / Wind / Laufwasser+Tief-Geoth → Elektrolyse → Elektrolyse-Stromspeicher → Rückverstromung → Stromnetz, with Abregelung + Gasspeicher Direktverbr. + Gasspeicher Strom branches.
- Check which values we're showing vs. which we should be showing; file a bug per mismatch.
- Bump font size / allow zoom.

### P3-4. Improve the annual electricity (H₂ storage) chart

**Source:** §2.5.7
**Ask:** Currently shows state of charge with an arbitrary zero at day 1, so the minimum required storage capacity (Max − Min) is not visible. Also missing: daily deltas between consumption and wind/solar generation (the drivers of charge/discharge). Excel uses "Tagesladung" (day-load) as the unit so the chart is region-independent.
**What this means for us:**
- Rescale the y-axis so Min = 0 (or annotate Min/Max/Capacity directly on the chart).
- Add a stacked-bar overlay showing daily surplus / deficit split by solar and wind, plus the shortfall-compensation (Mangelausgleich) bar.
- Switch unit from absolute GWh to "daily loads" (Tagesladung) — this normalizes across Germany vs. a Bundesland scenario.

### P3-5. Modification history (step-by-step log)

**Source:** §2.5.8
**Ask:** Excel logs each modification step. The PDF example shows 8 consecutive snapshots (rightmost = step 1, leftmost = step 8) of a sufficiency scenario where demand parameters were each reduced 10 % and the delta balanced by shrinking open solar area.
**What this means for us:**
- New model `ModificationHistoryEntry(scenario, timestamp, changed_field, before, after, auto_balance_result)`.
- Persisted on every user save. No auto-GC for now; scenarios are bounded in size.
- UI: new tab / panel showing the history as a table with the parameter rows as rows and each historical snapshot as a column (matching the Excel layout).

---

## P4 — Data model rework (largest item, biggest payoff)

### P4-1. Excel-data-model interface + alternative regions

**Source:** §2.3 (both subsections)
**Ask:** Replace the integrated data model in the DB with an **interface** that reads the existing Excel data-model files (`D.xlsx` and its federal-state siblings). This enables (a) **traceability** — parameter sources and assumptions are hyperlinked in the Excel itself, and (b) **alternative regions** — Bundesländer-specific scenarios, actively used by Green-party working groups today with Excel.
**What this means for us:**
- This is architecturally the largest change the stakeholder is asking for. It touches every layer: data import, data model, formulas, UI (scenario picker by region).
- Options:
  - **Option A (importer):** treat the Excel file as the source of truth. On admin upload, import it into the DB (current structure), but preserve the source/reference links as metadata shown in the UI. This keeps the runtime fast but demands a robust Excel-parsing pipeline.
  - **Option B (live binding):** load the Excel file at request time (or at server boot) and read values from it. Slower but faithful to stakeholder's "interface, not integration" proposal.
  - **Option C (hybrid):** import into DB but keep a `source_excel_path`, `source_cell`, `source_url` on every parameter row. UI shows a "Quelle" link per row that opens the Excel cell or a rendered Excel snippet.
- **Option C looks most tractable** — fits the current architecture, preserves traceability, and is compatible with the frozen cell-name contract.
- Adds first-class `Region` concept. Ties into the hardcoding-reduction work in `docs/PYPSA_MIGRATION_RESEARCH.md` §23.3.

---

## Suggested sequencing

> Final sequencing lives in `IMPLEMENTATION_PLAN.md`. Summary below.

| Phase | Items | Why grouped |
|---|---|---|
| **0 — Scaffolding** | progress tracker, Playwright scenarios, bench script | Pre-work so every later phase has tooling. |
| **1 — Surface removals** | P1-5, P1-2 (button removals) | Frontend-only, 30-min fixes, immediate visible win. |
| **2 — Localization** | P2-1, P2-2 | Mechanical string work; can parallel Phase 3. |
| **3 — Menu consistency** | P2-3 | Template partial extraction. |
| **4 — Behaviour fixes** | P1-1, P1-2, P1-3, P1-4 | Cascade propagation (not Balance), base-value restore, admin baseline, balance consolidation + busy-indicator fix. |
| **5 — Chart rework** | P3-1, P3-3, P3-4 | Redesign cockpit + fix flow diagram + fix annual chart. |
| **6 — History + details** | P3-5, P3-2 | P3-5's snapshot infra unlocks P3-2's variant-compare charts. |
| **7 — Acid test + handover** | P0-1, P0-2 | External-gated on ErnES platform choice. |
| **Deferred** | P4-1 | Data-model rework — needs its own spec and scoping session with Pascal. Tracked in PROGRESS.md with ⏸ status, not dropped. |

**On the cascade/Balance distinction** — §2.4.4 is about **auto-cascade** (Verbrauch → Erneuerbare recompute without a manual button), not auto-Balance. Balance stays manual (two buttons: Solar + Wind). Earlier draft conflated the two; corrected in `IMPLEMENTATION_PLAN.md` §4-E.

**On P4-1 deferral** — we have the Excel files but need a dedicated scoping session before pulling it in. It's the largest architectural change on the list and interacts with the hardcoding-reduction work in `docs/PYPSA_MIGRATION_RESEARCH.md` (Sector / Carrier / Region first-class refactors are prerequisites, not separate work).

---

## Notes on what's NOT in this document

- No mention of the existing cache-coherency or Heroku deployment quirks — those are our internal concerns, not stakeholder-facing. See `CLAUDE.md` for those.
- The stakeholder does **not** challenge the frozen cell names (LU_*, 9.3.1, sector names). Our existing "never rename cells" rule holds; the UI-label translations in P2-1 are on top of the cell codes, not replacements for them.
- "A great achievement" framing — take at face value. The list is long because the ambition is to replace Excel entirely, not because what's there is bad.
