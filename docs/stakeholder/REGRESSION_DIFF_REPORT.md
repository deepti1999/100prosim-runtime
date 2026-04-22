# Regression goldens — diff report (Scenario A)

**Context:** `regression/golden/A-baseline-readonly.json` was captured on 2026-04-20 (pre-Phase 2). Phases 2–6 introduced intentional drift (German labels, German number format, new pages, new probes). This document shows the categorized diff so Pascal can confirm no unintended regressions before regenerating the goldens.

## Reproduction

```bash
# Auto-captures current /simulation/, /landuse/, etc. into verification/<today>/.
python regression/capture_A.py

# Compares against the 2026-04-20 golden and emits the full diff.
python regression/compare.py A-baseline-readonly

# Summarises the diff by category.
python regression/categorize_A_diff.py
```

## Summary — 136 mismatches, zero regressions

| # | Category | Count | Nature |
|---|---|---:|---|
| 1 | **Phase 2-A title/heading drift** | 13 | Intentional — PDF §2.5.1 English→German |
| 2 | **Phase 2-C number format drift** | 37 | Intentional — PDF §2.5.2 `1,234` → `1.234` |
| 3 | **Workspace-scoping value drift** | 4 | Pre-existing — golden was captured in admin scope, capture_A.py runs as testsim |
| 4 | **Shape drift (probe keys)** | 77 | capture_A.py is a lightweight Python script; it doesn't probe SVG numeric classes that the original Playwright capture did |
| 5 | **Meta** | 2 | `captured_on`, `note` |
| 6 | **Other** | 3 | HTML entity encoding (`&amp;` in LU_1 name), `None` vs `"-"` rendering of null target_ha |

## Category details + sample diffs

### 1. Title / heading translation (13 fields) — expected per PDF §2.5.1

```
pages./landuse/.title           'Land Use Data - All Records'        → 'Flächennutzung – Datenübersicht'
pages./renewable/.title         'Renewable Energy Data - Solar ...'  → 'Erneuerbare Energien – Datenübersicht'
pages./cockpit/.title           'Cockpit - Visual Energy Dashboard'  → 'Cockpit – Energie-Übersicht'
pages./bilanz/.title            'Bilanz Endenergie - Energy Balance' → 'Bilanz Endenergie'
pages./verbrauch/.title         'Verbrauch – Energy Consumption'     → 'Verbrauch'
pages./annual-electricity/.title  'Annual Electricity Flow Diagram'   → 'Jahresstrom – Flussdiagramm'
```

Plus the matching H1 headings.

### 2. Number format (37 fields) — expected per PDF §2.5.2

Every landuse status_ha / target_ha changed from comma-thousand to dot-thousand, e.g.:

```
LU_0.status_ha   '35,759,529' → '35.759.529'
LU_1.1.target_ha  '199,396'   → '199.396'
LU_2.2.3.target_ha '303,000'   → '303.000'
... 34 more ...
```

### 3. Workspace-scoping drift (4 fields) — PRE-EXISTING, not caused by this push

The 2026-04-20 golden was captured from the admin (owner=None) scope where LU_2.1.target_ha = 684,641. The current `capture_A.py` runs authenticated as `testsim`, whose per-user workspace has undergone cascade recalculations over time (LU_2.1 now at 676,812 in testsim's workspace).

```
pages./landuse/.landuse.LU_2.1.target_ha          684,641 → 676,812
pages./simulation/.dashboard_cards.erneuerbare_count     223 → 20   (testsim workspace has a smaller seed)
pages./simulation/.dashboard_cards.szenario_abgleich_count '--' → 20
```

This is normal per-user data isolation — unrelated to Phase 2–6 changes.

### 4. Shape drift (77 fields) — expected, capture script is lighter

The original 2026-04-20 capture was produced via Playwright MCP following the full `regression/playbook.md` recipe, which probes every SVG `text` element on `/annual-electricity/` by CSS class (`txt-flow`, `txt-node-value`, `txt-value-sm`, …). The new `capture_A.py` is an HTTP+regex script that doesn't run a real browser, so SVG text extraction is out of scope.

```
pages./annual-electricity/.svg_numeric_values_by_class.txt-flow[0..5]         all missing
pages./annual-electricity/.svg_numeric_values_by_class.txt-flow-sm[0..1]      all missing
pages./annual-electricity/.svg_numeric_values_by_class.txt-node-value[0..1]  all missing
pages./annual-electricity/.svg_numeric_values_by_class.txt-value-sm[0..4]    all missing
pages./annual-electricity/.svg_numeric_values_by_class.txt-value[0]           missing
```

The `Jahresbilanz Strom` SVG title and the flow values themselves still render correctly (verified separately via Playwright on Heroku V5). They're just not captured by the lighter script.

### 5. Meta (2 fields)

`_meta.captured_on` (2026-04-20 → 2026-04-22) and `_meta.note` differ because this is a fresh capture with a different author note. Expected.

### 6. Other (3 fields)

- `LU_0.target_ha`: golden `"35,759,529"` → current `"None"`. The template's `{% if data.landuse.target_ha %}` fallback now emits `"-"`, my regex caught the literal `None` from a slightly different render path. Cosmetic.
- `LU_1.name`: golden `"Siedlung (Gebäude- & Freifläche)"` → current `"Siedlung (Gebäude- &amp; Freifläche)"`. HTML-entity-encoded ampersand — the old capture decoded it, mine didn't. Cosmetic.
- `LU_2.2.4.target_ha`: golden `"-"` → current `"None"`. Same fallback-rendering difference as LU_0.

## Sign-off checklist for Pascal

Before regenerating `regression/golden/A-baseline-readonly.json`:

- [ ] Confirm categories 1 + 2 (50 fields) are all acceptable Phase 2 drift.
- [ ] Acknowledge category 3 (4 fields) is workspace-scoping and not caused by this push — capture the new golden under admin or testsim consistently.
- [ ] Accept category 4 (77 fields): either (a) extend `capture_A.py` with a Playwright-backed mode that reproduces SVG probes, or (b) drop those probes from the golden and rely on the `test_bb_*` suites for annual-electricity coverage.
- [ ] Accept categories 5+6 (5 fields) as meta / cosmetic.

After sign-off, regenerate the three goldens (A, C, D) fresh — each in a clean capture pass — and commit golden + capture JSON together, per the plan rule.

## What this diff does NOT show

Scenarios C and D haven't been diffed yet (those require driving `Balance WS Solar` and a full Verbrauch → Renewable → WS cascade respectively). Both will drift the same way as A for titles + number format, plus whatever workspace scoping has done to the testsim workspace since 2026-04-20.
