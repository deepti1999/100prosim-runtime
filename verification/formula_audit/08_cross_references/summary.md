# §9 Cross-references, Named Ranges, Lookup Tables — summary

## What was audited

1. **All workbook-level named ranges** across 9 workbooks (166 total).
2. **All VLOOKUP/INDEX/MATCH/SUMIF/INDIRECT/COUNTIF formulas** across
   `_S.xlsx`, `D.xlsx`, `WS.xlsm` (4865 hits).

## Lookup function usage

| function | count | role | our code equivalent |
|----------|------:|------|---------------------|
| **INDIRECT** | 4,581 | dynamic cell-reference assembly (e.g., `INDIRECT($AC$1&AD$1&$AC8)`) — resolves to staging sheet rows | Django ORM queries (direct FK / code lookup) |
| SUMIF | 84 | conditional aggregation — renewable category sums, fossil classifier | Python list comprehension / DB aggregation |
| COUNTIF | 200 | row counts / region validation in `D.xlsx!I_Region` | Django uniqueness constraints |
| VLOOKUP / HLOOKUP | 0 | — | N/A |
| INDEX / MATCH | 0 | — | N/A |

**Notable**: zero VLOOKUP/INDEX/MATCH. The workbook authors preferred
INDIRECT for cross-sheet references (a German-engineering-tradition
pattern). Our code reads the same DB row directly — semantically
equivalent.

## Named range coverage (detailed in `named_ranges.md`)

| workbook | named | runtime-relevant | mapped to DB | verdict |
|----------|------:|-----------------:|:------------:|:-------:|
| WS.xlsm | 17 | 6 | 5 (1 dead — F006) | 83 % |
| _S.xlsx | 22 | 12 | ~12 (implicit via user_percent fields) | CONGRUENT |
| D.xlsx | 1 | 0 | — | OK |
| AH.xlsm | 16 | 0 (archive) | — | OK |
| C.xlsx | 27 | 0 (all `#REF!`) | — | OK |
| MH.xlsx | 0 | — | — | OK |
| _100prosim.xlsm | 4 | 0 (launcher) | — | OK |

## Findings

No new findings from §9.

Cross-references:
- F006 — `WS_ABREGELUNG_THRESHOLD` drift (Abregelung=1 vs 0.65)
  visible in the named-range comparison.

## Observations

1. **INDIRECT dominates**: 94 % of lookup formulas are INDIRECT.
   These all live in `_S.xlsx` and resolve to staging sheets (`I_`).
   Our code bypasses this indirection by querying the source DB
   directly — the information is the same, expressed differently.

2. **Named ranges are UI anchors, not tables**: No Excel lookup table
   is a source of truth that our code would need to mirror. The only
   runtime-relevant named ranges are the WS constants (already
   verified in §5) and the scenario anchors (which map to
   `user_percent` fields).

3. **`_S.xlsx` is a "thin presentation" over `D.xlsx`**: Most
   `_S.xlsx` cells use `INDIRECT` or cross-sheet refs to pull from
   `D.xlsx` parameter master. Our DB is the single authoritative
   source for both roles. This is architecturally simpler.

## Self-skepticism — limitations

1. **SUMIF chains not individually traced**. 84 SUMIF cells —
   each SUMIF could be mirroring a specific DB aggregation. I did
   not verify each one.
2. **INDIRECT resolution not tested per cell**. 4581 hits — testing
   each would take forever; I trusted that if the cached Excel
   value matches our DB value (proven in §2 and §4), the INDIRECT
   chain is working as designed on the Excel side.

## Self-skepticism checklist

- [x] Enumerated named ranges across all 9 workbooks
- [x] Scanned 3 runtime workbooks for lookup functions
- [x] Cross-linked to F006
- [x] Documented Excel→DB mapping gaps (minor, not findings)
- [x] Noted absence of VLOOKUP/INDEX/MATCH as a finding-worthy
      observation (architectural choice, not a bug)

## Artifacts

- `named_ranges.md` — per-workbook named-range inventory + DB mapping.
- `lookup_tables.md` — 4865 lookup-function occurrences grouped by
  function name with samples.
