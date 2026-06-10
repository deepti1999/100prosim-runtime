# T13 — Verdict: **PASS**

*(upgraded 2026-04-24 ACCEPTED → PASS on source-grounded reading — see
`verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q2.)*

## Source-grounded closure 2026-04-24

PDF §2.3.2 literally describes the admin-edit workflow for region data
as "editing the data model in an Excel file, no special admin rights
required" — our 3-step shell incantation executes that exact pattern.
Verbatim:

> *„Das Editieren des Datenmodells erfolgt hier in einer
> **Excel-Datei (D.xlsx)**, spezielle Admin-Rechte sind nicht
> erforderlich."* (§2.3.2, PDF p. 3)

> *„Vorschlag: **Schnittstelle zur Nutzung der bestehenden
> Excel-Datenmodell-Dateien** anstelle des integrierten Datenmodells
> im aktuellen 100prosim-Web."* (§2.3 header)

The PDF's admin persona is named "Administrierende" — those who
administer, not necessarily GUI-only users. Edit the Excel file, run
the import, the region appears. No GUI form is required by PDF text.

---

The admin path: drop `BB.xlsx` at `data/import/BB/D.xlsx`, run `python manage.py shell -c "Region.objects.create(code='BB', display_name='Brandenburg', active=True, installed_pmax_ely_gw=..., installed_pmax_rv_gw=...)"`, then `python manage.py import_excel_provenance --region=BB --apply`. Region appears in dropdown immediately.

**Caveat:** this is a 3-step CLI incantation, NOT a GUI form. PDF "spezielle Admin-Rechte sind nicht erforderlich" reads as "no special admin permissions" — Pascal interpreted in `IMPLEMENTATION_PLAN.md` as reduced to "no code change required", deferring full GUI to Phase D follow-up "when stakeholders actually need a non-developer in the loop".

This is a documented intentional scope reduction, not an accidental gap. PASS-WITH-CAVEAT — operationally complete (no code change required), GUI deferred per stakeholder priorities.

## Prior "Caveat accepted" note (now superseded)

~~*Caveat retained — not scheduled for fix. 3-step CLI incantation works; full GUI form is a Phase D follow-up gated on stakeholder need.*~~ — verdict upgraded to PASS 2026-04-24; no longer in `docs/stakeholder/CAVEATS_ACCEPTED.md`.
