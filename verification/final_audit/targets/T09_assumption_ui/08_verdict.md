# T09 — Verdict: **PASS**

Same info-icon path as T8 — popover Annahme section displays `notes_assumption`. V2 covered by `test_wb_provenance_schema` (asserts notes_assumption field added to the 4 models) + `test_wb_excel_provenance_import::test_assumption_text_populated_from_d_xlsx`.

Provenance import (Phase A) populated 265/420 rows (80.5% of 329 HIGH-confidence rows) with assumption text — see `data/import/DE/d_xlsx.manifest.json` for the per-model counts.
