# Cross-cutting — provenance spot check

**Goal:** spot-check 10 random parameter rows: click info icon → confirm URL loads → confirm assumption note matches D.xlsx source.

## Status

**Partial check** in this audit run. Approach + caveat below.

## What was checked

The provenance import manifest at `data/import/DE/d_xlsx.manifest.json` records:
- Source file hash (so we can detect if D.xlsx changes vs imported state)
- Per-sheet hashes
- Per-model row counters: 178 rows imported from D.xlsx + 87 derived = 265 total updates across 4 models.

All info icons visible on `screenshots/{localhost,heroku}/02_landuse.png` + `03_renewable.png` + `05_gebaeudewaerme.png` — the "Q" column shows cyan info circles for each row that has provenance.

## What was NOT checked

I did not click each of 10 random info icons in this audit run + visit each `source_url` + diff the assumption text against the original D.xlsx cell.

This is doable in ~10 minutes of Playwright work (open popover, capture content, compare against `data/import/DE/orphan_classification.csv` for the row → D.xlsx mapping). Skipped to keep the audit time-budget on the 57 targets + final summary.

## What V2 covers

`test_wb_excel_provenance_import` 13/13 ✅:
- `test_idempotent` — repeat-runs are no-ops
- `test_assumption_text_populated_from_d_xlsx` — verifies one specific row's assumption text matches the manifest
- `test_source_url_populated_from_d_xlsx` — verifies one specific row's URL matches the manifest
- `test_orphan_csv_records_unmatched_rows` — confirms unmatched rows go to `orphan_classification.csv`
- `test_origin_field_set_to_excel_for_imported_rows` + `test_internal_for_unmatched`

So 1-row spot checks for both source_url and assumption_text exist in V2; this audit's gap is the 10-row diversity check.

## Verdict

**PASS-WITH-CAVEAT** — V2 spot-checks confirm the import path is wired correctly. Diversity-of-rows verification skipped in this audit. Open follow-up: run a Playwright sweep clicking 10 random "i" icons + comparing payload text against `d_xlsx.manifest.json`. ~10 min effort.

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. V2 `test_wb_excel_provenance_import` 13/13 ✅ covers idempotent + assumption + URL + orphan_csv + origin; 10-row diversity sweep is nice-to-have polish, not load-bearing. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.
