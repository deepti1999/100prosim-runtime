# T12 — Verdict: **PASS**

`manage.py import_excel_provenance --region=<code> --apply` reads `data/import/<region>/D.xlsx` and writes provenance + values to the DB. Per-region paths convention shipped Phase B; row-creating mode for new regions shipped Phase C. V2: `test_wb_excel_import_region` 6/6 + `test_wb_import_create_region` 4/4 ✅.

The `D.xlsx` files themselves are gitignored (stakeholder bundle), but the **interface** to ingest them is shipped + tested. Per `DATA_MODEL_IMPORT_AUDIT.md` §0b: "Per-Bundesland Excel files exist on https://www.ernes.de/seite/422657/softwaretools.html but are not yet in Pascal's local bundle (only D.xlsx for Germany). Adding one is a 3-step shell incantation."

PASS — the schnittstelle is shipped, exercised by Phase C synthetic TEST region.
