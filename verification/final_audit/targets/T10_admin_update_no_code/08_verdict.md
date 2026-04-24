# T10 — Verdict: **PASS-WITH-CAVEAT**

`manage.py import_excel_provenance D.xlsx --apply` is the canonical admin update path — drop a new D.xlsx, run the command, no code change required. Phase C added `--region=<code>` for per-region updates. Test `test_wb_excel_provenance_import::test_idempotent` ✅ verifies repeat-runs are no-ops + that fresh xlsx with new values gets applied correctly.

**Caveat:** the update path is **CLI-only**, not GUI-exposed in the admin panel. Phase B `IMPLEMENTATION_PLAN.md` notes this is "partially shipped" — full GUI for non-developer admins (T13) deferred to Phase D when stakeholders need it. The CLI satisfies the literal "without code change required" reading; "spezielle Admin-Rechte sind nicht erforderlich" interpretation is reduced from "no admin rights at all" → "no code change, single shell incantation".

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. CLI works; GUI deferred to Phase D per Pascal's call. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.
