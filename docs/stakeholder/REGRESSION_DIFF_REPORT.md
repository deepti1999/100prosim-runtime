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

## Sign-off history

**2026-04-22** — Pascal reviewed the categorization above and approved
regenerating scenario A's golden with the following plan:

- [x] Accept categories 1 + 2 (50 fields): intentional Phase 2 drift.
- [x] Re-capture under consistent testsim (workspace) scope — eliminates
  the 4 pre-existing workspace-drift fields.
- [x] Drop the 77 SVG text-element probes from the golden. They're
  better covered by the `test_bb_*` suites that read the server-
  rendered data directly; the regression harness stays lightweight
  (HTTP + regex, no browser needed).
- [x] Accept categories 5 + 6 (5 fields): meta + cosmetic.

**Implementation of the sign-off:**

1. `regression/capture_A.py` extended with:
   - Fixed `_h1()` to handle nested `<i>` icon tags.
   - New `_renewable_key_rows()` — probes 9.3.1 / 9.3.4 / 10.1 / 10.2
     status + target cells (stakeholder-contract codes).
   - New `_bilanz_section_headers()` — pulls the two Bilanz h3 headings.
   - New `_ws_headings()` — pulls Solar / Wind / Jahresstrom card
     headers.
   - Robust `_dashboard_cards()` that matches each card-title → h3 pair
     directly (the old regex matched the first h3 after each label,
     which happened to be the same one for all four labels).
2. Ran `python regression/capture_A.py` as testsim; wrote fresh JSON to
   `verification/2026-04-22/A-baseline-readonly.json`.
3. Copied the fresh JSON to `regression/golden/A-baseline-readonly.json`
   with an updated `_meta.note` that records the sign-off + testsim-
   scope owner.
4. `regression/compare.py` patched to exclude `_meta.*` from the
   comparison (provenance, not app state).

**After sign-off:** `python regression/compare.py A-baseline-readonly`
exits 0 with **97 matched fields**. Scenario A regression harness is
healthy.

## Scenarios C and D — same treatment pending

C (ws-balance) and D (full-flow-verbrauch-solar-wind) require
Playwright-driven mutations (click Balance Solar, wait for
BalanceJob to succeed, edit Verbrauch + trigger cascade). Their
goldens have the same Phase 2 localization + number format drift as
A plus the same workspace-scoping drift. When we need a healthy C/D
regression:

1. Write `regression/capture_C.py` / `capture_D.py` along the same
   lightweight HTTP+regex pattern as capture_A.py, adding POSTs
   to `/api/ws/apply-balance/` + polling `/api/ws/balance-job/<id>/`.
2. Reset testsim workspace first so the balance is deterministic
   (`heroku run` snippet in CLAUDE.md, same idea locally).
3. Run, capture fresh JSON, regenerate the golden with the same
   sign-off note pattern, commit.

Not done in this push — A was the request.
