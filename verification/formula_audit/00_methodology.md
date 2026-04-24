# Audit methodology (§0)

**Purpose.** Deep end-to-end parity audit of the 100ProSim Django app vs
the source Excel workbooks (D / _S / WS / AH / C / MH / _100prosim).
This document fixes the *rules of engagement* before a single number
gets compared, so later claims ("matches", "drift", "discrepancy") are
reproducible and falsifiable.

**Adversarial posture.** The null hypothesis is that **our app is
wrong** for every value, every formula, every flow. Passing a row
requires an affirmative numeric + methodological proof; failing a row
requires only a single counter-example. An unproven claim of match is
logged UNPROVEN, not PASS.

---

## Sources of truth (in priority order)

| rank | artefact | used for |
|-----:|----------|----------|
| 1 | `docs/100prosim_d_*/D.xlsx` → sheet `1.` (2133×157) | parameter values + provenance (*status* + *Quelle*) |
| 2 | `docs/100prosim_d_*/_S.xlsx` → sheets `1. Flächen`, `2. Erneuerbare`, `3. Bedarfsniveau`, `4. Verbrauch`, `5. Bilanz`, `6. Fossile`, `7. Verbrauch Status`, `8. Kennzahlen` | scenario master (17 sheets ≈ app pages) |
| 3 | `docs/100prosim_d_*/WS.xlsm` → sheets `1.Jahresbilanz_Strom` (flow diagram), `Zeitreihen Kalkulation` (521 rows × 56 cols) | WS365 computation |
| 4 | `docs/100prosim_d_*/AH.xlsm`, `C.xlsx`, `MH.xlsx` | archive / change-log / modification-history — spot-check only; not expected to drive values |
| 5 | `docs/100prosim_d_*/__100prosim.Anwendung.pdf`, `~Erlaeuterungen.pdf` | policy + user-manual cross-reference |

**Meta-rule.** If D and _S disagree on a value, _S wins for the app's
runtime display; D supplies the *why* via `9.Quellen`.

Earlier audit artefacts under `scripts/audit_out/` and
`verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` are **context,
not evidence**. Every number herein is re-derived from the workbooks
above.

---

## Tolerances

| layer | tolerance | rationale |
|-------|-----------|-----------|
| static values | ≤ 0.1 % relative OR ≤ 0.01 absolute for small-magnitude metrics | 0.1 % captures rounding (5-digit Excel vs Python float) without masking true drift |
| values near zero (|x| < 1) | ≤ 0.01 absolute | relative loses meaning |
| formula text | exact after normalization (see §"Normalization") | formulas must match semantically |
| formula output at 5 sample inputs | ≤ 0.1 % | catches semantically equivalent but numerically drifting formulas |
| Bilanz rows (sheet `5. Bilanz` vs engine) | ≤ 0.1 % | |
| WS365 daily series (`Zeitreihen Kalkulation`) | ≤ 0.1 % or ≤ 0.1 GWh abs, whichever larger | day-level noise |
| data-flow consumers | set equality (∅ symmetric diff) | different consumer set = different behaviour |
| sector totals (KLIK / GW / PW / MA) | ≤ 0.1 % | |

A value passing at 0.1 % is **also** checked at 0.01 % and any drift
between 0.01 % and 0.1 % is logged as a `COSMETIC` finding.

---

## Extraction method

| source | loader | flag | what it returns |
|--------|--------|------|-----------------|
| Excel values | `openpyxl.load_workbook(path, data_only=True)` | cached computed values | numbers — what a user sees |
| Excel formulas | `openpyxl.load_workbook(path, data_only=False)` | formula strings | text — what the cell contains |
| named ranges | `wb.defined_names[name].attr_text` | — | `sheet!$col$row` reference |
| DB | Django ORM via `docker compose exec` → shared Postgres | — | LandUse / VerbrauchData / RenewableData / GebaeudewaermeData / Formula / WSData |
| Seed | `seed/sqlite_seed.json` (420 rows incl. provenance overlay) | — | ground-truth of the DB-as-committed |
| Code | `Grep` + `Read` over `simulator/**` and `calculation_engine/**` | — | data-flow consumer set |

If a workbook has VBA / macros that *would* alter a value at runtime,
we note it — we do not execute VBA. `openpyxl` returns the last-saved
cached value, which is the value a user opening the file in Excel sees
before any recalc.

---

## Normalization rules (for formula comparison)

1. **Whitespace**: strip leading/trailing, collapse runs of ≥2 spaces to 1.
2. **Case**: Excel function names folded to upper (`sum` → `SUM`).
3. **Named ranges resolved**: `TLproEingabeEinheit` → `'1.Jahresbilanz_Strom'!$D$85`.
4. **Cell refs normalized**: `$A$1`, `A$1`, `$A1`, `A1` → all `A1`
   unless the absolute-vs-relative distinction is semantically
   load-bearing (i.e., the formula is copied to another cell).
5. **Literal constants**: compared numerically at the value-tolerance,
   not textually (so `0.65` == `0.650` == `65/100`).
6. **Sheet qualification**: local refs within a sheet are qualified
   with the sheet name for compare; cross-sheet refs keep their
   qualifier.
7. **Semantic equivalence classes**:
   - `A*B/100` ≡ `A*B*0.01` ≡ `A/100*B` (commutative / scale-equivalent)
   - `SUM(A:A)` ≡ `SUM(A1:A<last_used>)` if no blanks
   - Python `expression` using operators `*`, `/`, `+`, `-` maps 1:1
     to Excel arithmetic; `IF(cond, a, b)` ↔ Python ternary.
   When applying an equivalence class, record which class in the finding.

A "match after normalization" with **different residual structure** is
logged `EQUIVALENT`, not `EXACT`. Pure text-identity is `EXACT`.

---

## Mapping inference

There is no formal DB-key → Excel-cell map. We infer via:

1. `Formula.key` or `Formula.category` + a cell-ref mention in the
   `description` / `notes` / `expression`.
2. Row code (`LU_2.1`, `9.3.1`, `1.1.2`, `2.4.1`) grep'd in the Excel
   B-column across all sheets.
3. German label grep in `_S.xlsx`.
4. Fallback: manual cross-reference per row, documented in the
   comparison script's `MAPPING` dict.

Every inferred mapping is recorded in the script that uses it. If a
row has **no** inferable mapping, it is flagged `NO_EXCEL_CELL_FOUND`
with severity set by whether the row is a top-level input (HIGH) or
an intermediate computed value (MEDIUM).

---

## Domain → deliverable matrix

| § | domain | CSV | discrepancies | summary | findings ref |
|--:|--------|:---:|:-------------:|:-------:|:------------:|
| 2 | Value parity (420 rows) | `01_value_parity/per_row_comparison.csv` | ✓ | ✓ | F0xx |
| 3 | Formula parity (760 rows) | `02_formula_parity/formula_table_vs_excel.csv` | ✓ | ✓ | F0xx |
| 4 | Bilanz parity | `03_bilanz_parity/row_by_row.csv` | ✓ | ✓ | F0xx |
| 5 | WS365 daily | `04_ws365_parity/daily_timeseries_diff.csv` + `named_constants.csv` | ✓ | ✓ | F0xx |
| 6 | Jahresstrom | `05_jahresstrom_parity/every_diagram_node.csv` + `flow_segment_values.csv` | ✓ | ✓ | F0xx |
| 7 | Data flow | — | `06_data_flow/input_to_output_trace.md` + `cascade_parity.md` | ✓ | F0xx |
| 8 | Sector totals | — | `07_sector_totals/<sector>.md` × 4 | ✓ | F0xx |
| 9 | Cross-refs | — | `08_cross_references/named_ranges.md` + `lookup_tables.md` | ✓ | F0xx |

Global ledger: `DISCREPANCY_LEDGER.csv` (one row / finding, sortable
by severity). Final: `FINAL_REPORT.md` with per-domain verdict + top
10 findings + confidence score.

---

## Severity rubric

| sev | criterion |
|-----|-----------|
| **CRITICAL** | Wrong user-facing number; wrong sector/Bilanz total; incorrect downstream cascade |
| **HIGH** | Correct display but wrong source — e.g. value right by coincidence, formula shape diverges from Excel; risk of breakage on future input changes |
| **MEDIUM** | Naming drift, unit-label mismatch, documentation lag — cosmetic to stakeholder but semantically meaningful |
| **LOW** | Spelling, punctuation, source-URL stale, comment drift |
| **COSMETIC** | Text-only differences that don't affect any number or rendering |

Severity × `affects_calc` (YES/NO) is mandatory on every finding.

---

## Reproducibility contract

Every script under `scripts/` must be runnable stand-alone with no
interactive input:

```bash
python verification/formula_audit/scripts/<name>.py
```

(Or `docker compose exec -T web python /app/verification/formula_audit/scripts/<name>.py`
for scripts that need the Postgres DB.)

Every CSV under the domain folders must be regeneratable by running
its script. Every `.md` finding must cite (a) the script path and
(b) the specific cell / DB field names that produced the claim.

---

## What this audit does **not** cover

- VBA execution — we read cached values, not what macro runs would
  produce on open.
- `C.xlsx` full audit — the change-log workbook's named ranges are
  almost all `#REF!`, suggesting it's a historical artifact. We
  enumerate its structure but don't compare values row-by-row.
- `tracelog.xlsx` / `trace2.xlsx` — these are debug traces, not
  sources.
- `AH.xlsm` beyond its named-range enumeration — it's an archive
  workbook for the Cockpit sheets; any value drift there is out of
  scope unless it surfaces in WS.xlsm or _S.xlsx.
- Multi-scenario variation — values are compared at seed/testsim
  defaults. We do NOT run the app across all possible user inputs.
- Performance: this is a correctness audit, not a timing audit.

---

## Self-skepticism checklist (applied at end of each §)

For each domain, before writing a `summary.md` verdict, we answer:

- [ ] Multiple tolerances tried? (0.1 % AND 0.01 %)
- [ ] Formula *structure* compared, not just value?
- [ ] Multiple input scenarios tried (not just defaults)?
- [ ] Did I re-derive from sources rather than trusting prior audits?
- [ ] Anything unexpected found? If not, looked from a different angle?

Domains that answer YES to all five go to PASS. Any NO gets a
"LIMITATIONS" section appended to `summary.md` with what was not
checked and why.

---

Author: Claude Code (Opus 4.7). Date: 2026-04-24.
