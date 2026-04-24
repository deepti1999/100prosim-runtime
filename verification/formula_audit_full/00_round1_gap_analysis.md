# Round 1 Gap Analysis — what Round 2 must close

Round 1 (`verification/formula_audit/`) produced 9 findings
(F001–F009) and admitted explicit coverage gaps in FINAL_REPORT §6
"What we could NOT verify". This document enumerates every gap and
maps it to a concrete Round 2 work item.

Forbidden words in this document and all downstream Round 2
outputs: *deferred*, *partial*, *plausible more*, *lower bound*,
*sampling*. Every open item is rewritten as a plan of action.

---

## Gap 1 — Formula parity hand-mapped to only 25 of 781 rows (≈ 3 %)

**Round 1 state** (`02_formula_parity/summary.md`):
> "Spot-check results (25 representative formulas) ... 3 % hand-coverage
> and the honest limitation — remaining 97 % dumped to CSV for later
> review."

**Round 2 plan**: produce
`01_curated_mappings/formula_to_excel.csv` with **all 760 Formula
rows** plus the 21 `WS365Formula` rows (total 781). Each row has an
Excel cell reference or an OOS reason (Django-internal helper, UI
only, legacy placeholder). Then `02_full_formula_parity/per_formula_diff.csv`
computes EXACT / EQUIVALENT / DIFFERENT / NO_EXCEL_CELL_DOCUMENTED
per row.

**Target**: 781 rows, 0 UNPROVEN, 0 TBD.

---

## Gap 2 — Bilanz parity covered only the Strom section (15 of N cells)

**Round 1 state** (`03_bilanz_parity/summary.md`):
> "Strom section: 5 × 3 cells (total / renewable / fossil × KLIK/GW/PW/MA/total).
> Liquid (rows 15-17) and solid (rows 18-20) fuels were not compared in this pass."

**Round 2 plan**: `03_full_bilanz_parity/all_sections.csv` covers
every non-empty output cell on `_S.xlsx!5. Bilanz`. Grouped into
per-section files (`strom.md`, `gas.md`, `liquid.md`, `solid.md`,
`heat.md`, `other.md`) — each section compared to the engine's
equivalent output from `calculate_bilanz_data()`.

**Target**: every populated Bilanz cell, status + ziel column,
across all 4 sectors and 4+ energy carriers.

---

## Gap 3 — Renewable name-matching collapsed section-distinct rows (F005 UNPROVEN)

**Round 1 state** (F005):
> "The matcher's current heuristic (best normalized-name match) is
> blind to section membership ... Since DB 5.4.2.3 (21.9/25) and
> 6.1.3.2.3 (50/50) cannot both be the single Excel row 86 (which
> holds 45/45), at least ONE of them is wrong in the DB (or the
> matcher picked the wrong row for one)."

**Round 2 plan**: `01_curated_mappings/renewable_to_excel.csv` is
**hand-authored** — each of the 223 (or more, including
non-testsim) RenewableData rows gets a section-aware
`excel_sheet!cell` mapping. Then
`04_renewable_section_aware/per_row_parity.csv` re-runs the value
comparison against that curated mapping.
`04_renewable_section_aware/f005_resolution.md` closes F005 as
proven or cleared.

**Target**: every RenewableData row mapped or explicitly OOS.
F005 closed.

---

## Gap 4 — Cascade parity was symbolic (grep), not live

**Round 1 state** (`06_data_flow/summary.md`):
> "Symbolic tracing, not live execution — I used grep and formula-graph
> traversal to infer consumer sets. I did not run live edits and
> observe actual propagation."

**Round 2 plan**: `05_live_cascade/` runs **live** diffs:

1. Load `_S.xlsx` and `WS.xlsm` with a formula-evaluation library
   (options: `pycel`, `formulas`, `python-calamine+eval`, or a
   hand-rolled traversal).
2. Record the baseline cached values for every cell.
3. For each of 10 representative inputs, mutate the cell in memory,
   force full recomputation, and record the delta for every cell.
4. On our stack (docker compose), via Django shell, change the
   equivalent DB field under a transaction (rolled back at end to
   leave seed intact — this is analysis, not mutation). Observe
   BalanceJob + recalc_service cascade. Record downstream delta.
5. Pairwise compare Excel-diff vs DB-diff. Set-diff + magnitude.

**Target**: 10 inputs, cell-for-cell diff table per input.

---

## Gap 5 — Only the default scenario was tested

**Round 1 state** (FINAL_REPORT §6):
> "Single default scenario: engine tested with the DB's default seed
> state. Under different scenarios the drift pattern may differ."

**Round 2 plan**: `06_multi_scenario/` runs the same value + formula
+ Bilanz parity against **3 scenarios**:

- `default/` — the baseline canonical seed (re-verification).
- `scenario_D/` — the regression harness's Scenario D write-flow
  state. Trigger via `regression/capture_A.py` + scenario D setup.
- `user_workspace/` — testsim workspace after 5 varied edits
  (LandUse LU_2.1, LandUse LU_6, Renewable 9.3.1, Verbrauch 1.4,
  Gebäudewärme 2.8.0). Edits applied via Django shell; parity
  checked immediately after; edits rolled back via `ensure_user_workspace_data`
  to restore canonical state.

**Target**: value + Bilanz parity numbers for each of 3 scenarios.

---

## Gap 6 — VBA / macro code paths not inspected

**Round 1 state** (FINAL_REPORT §6):
> "VBA code paths — openpyxl reads cached values; Excel's VBA
> (macro) code is not executed. If any Excel macro rewrites cells at
> open, we see the pre-macro state."

**Round 2 plan**: `07_vba_inspection/` extracts VBA from every
`.xlsm` / `.xlsb` in `docs/100prosim_d_*/`:

1. Use `oletools` (`olevba`) or direct zip-extract of
   `xl/vbaProject.bin` + decode via `olefile` + custom decoder.
2. Decode VBA module text for each file.
3. Static-scan for:
   - `Workbook_Open`, `Auto_Open`, `Workbook_BeforeSave`,
     `Workbook_SheetChange`, `Worksheet_Change` handlers
   - Any `Range(...).Value = ...` or `Cells(...).Value = ...`
     assignments (cell mutators)
   - `Application.Calculate`, `ActiveSheet.Calculate` triggers
   - External file I/O or web queries
4. Compare to what our Python pipeline does. Any macro-driven
   cell mutation we don't mirror = finding.

**Target**: every `.xlsm` scanned, decoded-module text under
`extracted_modules/`, findings in `findings.md`.

---

## Round 1 findings carry-forward list

| ID | severity | status entering Round 2 |
|----|---------:|-------------------------|
| F001 | HIGH | CARRY (LU_2.1 user_percent 3.856 vs Excel 5) |
| F002 | MEDIUM | CARRY (residual of F001) |
| F003 | HIGH | CARRY (VerbrauchData 3.2.2 ziel 89 vs 95) |
| F004 | MEDIUM | CARRY (PW 0.9 % status drift) |
| F005 | HIGH-if-confirmed | RE-CLASSIFY (close as proven or cleared in §04) |
| F006 | LOW | CARRY (WS_ABREGELUNG_THRESHOLD dead code) |
| F007 | CRITICAL | CARRY (Bilanz GW Strom = 0) |
| F008 | HIGH | CARRY (Bilanz MA Strom subcode) |
| F009 | LOW | CARRY (Jahresstrom Abregelung 3.3 % drift) |

New findings in Round 2 start at F010.

---

## Execution plan — order of operations

1. Write this file (you are reading it). ✓
2. Build curated mappings (§01) — foundation for everything else.
3. Full formula parity (§02) — uses §01 formula mapping.
4. Full Bilanz parity (§03) — uses §01 bilanz mapping + engine output.
5. Section-aware Renewable (§04) — uses §01 renewable mapping, closes F005.
6. VBA inspection (§07) — independent, can run in parallel with §03-§04.
7. Live cascade (§05) — requires stack running, ~10 inputs × 2 sides.
8. Multi-scenario (§06) — 3 scenarios, value+Bilanz per scenario.
9. FINAL_REPORT — 2500-4000 words, completeness attestation.

Commit per domain at minimum. Commit per curated-mapping file too
(6 commits for §01 alone). If a 6-hour budget hits mid-§02, the
earliest 5 domains (§00+§01 + whatever completed) must survive.

---

## Resource inventory

- DB: Postgres via `docker compose` (up + healthy as of session start).
- Excel: 9 workbooks in `docs/100prosim_d_250517_250517.1817m/`,
  already enumerated in Round 1's `00_source_inventory.md`.
- Python libs installed: openpyxl 3.1.5, pandas 2.3.1, Django 4.2.24.
  Need to install / verify: `pycel`, `formulas`, `oletools` (via
  `pip install --user`).
- Round 1 artifacts under `verification/formula_audit/` are
  READ-ONLY references (kept out of Round 2's output path).
