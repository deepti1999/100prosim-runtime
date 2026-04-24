# T13 — Verdict: **PASS-WITH-CAVEAT**

The admin path: drop `BB.xlsx` at `data/import/BB/D.xlsx`, run `python manage.py shell -c "Region.objects.create(code='BB', display_name='Brandenburg', active=True, installed_pmax_ely_gw=..., installed_pmax_rv_gw=...)"`, then `python manage.py import_excel_provenance --region=BB --apply`. Region appears in dropdown immediately.

**Caveat:** this is a 3-step CLI incantation, NOT a GUI form. PDF "spezielle Admin-Rechte sind nicht erforderlich" reads as "no special admin permissions" — Pascal interpreted in `IMPLEMENTATION_PLAN.md` as reduced to "no code change required", deferring full GUI to Phase D follow-up "when stakeholders actually need a non-developer in the loop".

This is a documented intentional scope reduction, not an accidental gap. PASS-WITH-CAVEAT — operationally complete (no code change required), GUI deferred per stakeholder priorities.

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. 3-step CLI incantation works; full GUI form is a Phase D follow-up gated on stakeholder need. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.
