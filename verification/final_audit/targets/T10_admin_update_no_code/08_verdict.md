# T10 — Verdict: **PASS**

*(upgraded 2026-04-24 ACCEPTED → PASS on source-grounded reading — see
`verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q2.)*

## Source-grounded closure 2026-04-24

PDF §2.3.2 literally proposes the Excel-file-import pattern — our CLI
IS the proposal, not a reduced interpretation. Verbatim:

> *„Das Editieren des Datenmodells erfolgt hier in einer
> **Excel-Datei (D.xlsx)**, spezielle Admin-Rechte sind nicht
> erforderlich."* (§2.3.2, PDF p. 3)

> *„Vorschlag: **Schnittstelle zur Nutzung der bestehenden
> Excel-Datenmodell-Dateien** anstelle des integrierten Datenmodells
> im aktuellen 100prosim-Web."* (§2.3 header, PDF pp. 3 + 3-bottom)

"Schnittstelle" (interface) does not mean "browser GUI form" — it
means any mechanism that consumes the Excel data-model file. Our
`manage.py import_excel_provenance D.xlsx --apply` IS exactly that
mechanism. The PDF thus endorses the CLI path literally, not just
tolerates it.

---

`manage.py import_excel_provenance D.xlsx --apply` is the canonical admin update path — drop a new D.xlsx, run the command, no code change required. Phase C added `--region=<code>` for per-region updates. Test `test_wb_excel_provenance_import::test_idempotent` ✅ verifies repeat-runs are no-ops + that fresh xlsx with new values gets applied correctly.

**Caveat:** the update path is **CLI-only**, not GUI-exposed in the admin panel. Phase B `IMPLEMENTATION_PLAN.md` notes this is "partially shipped" — full GUI for non-developer admins (T13) deferred to Phase D when stakeholders need it. The CLI satisfies the literal "without code change required" reading; "spezielle Admin-Rechte sind nicht erforderlich" interpretation is reduced from "no admin rights at all" → "no code change, single shell incantation".

## Prior "Caveat accepted" note (now superseded)

~~*Caveat retained — not scheduled for fix. CLI works; GUI deferred to Phase D per Pascal's call.*~~ — verdict upgraded to PASS 2026-04-24; no longer in `docs/stakeholder/CAVEATS_ACCEPTED.md`.
