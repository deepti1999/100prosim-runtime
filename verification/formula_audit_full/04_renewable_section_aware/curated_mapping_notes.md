# Curated mapping notes — how ambiguous names were resolved

The section-aware mapping uses `(category, subcategory)` tuples from
the DB to scope the Excel row search. Key resolution strategies:

## Nutzungsgrad rows (F005 source of ambiguity)

The label "Nutzungsgrad Kraftwerk" appears in both Biogas section
(rows 82-86) and Biomasse/flüssig section (rows 130-140).
`(category='Biogas', subcategory='Main')` restricts search to the
Biogas section's row range, picking row 84 for `5.4.2.1`.
`(category='Biogene Brennstoffe (flüssig)', subcategory='Biodiesel Details')`
picks row 136 for `6.1.3.2.3`.

## "davon …" aggregate labels

Labels starting with "davon" are per-section, e.g.:
- `davon Einsatz für Prozesswärme` appears under Biogas (row 81),
  Biomasse (row ~135), Holz.
Resolved by requiring the section header (column E value) match the
DB category before accepting a row.

## "Anteil …" percentage labels

"Anteil an solaren Dachflächen" appears for solar-thermal (row 8)
and solar-PV (row 17) — different energy forms. Resolved by
sub-category in the DB.

## Fallback strategy

For rows where the section-aware search fails, a global name-match
is attempted (Round 1 behaviour). If both fail, the row is marked
OOS with a specific reason (NO_SECTION_MATCH).

16 of 223 rows fell back to OOS — mostly:
- Summary/aggregate rows (category='Zusammenfassung') whose
  Excel form is a SUMIF aggregate, not a single row.
- Empty-name rows (DB name field blank).
- Rows referencing codes that don't appear in _S.xlsx!2. Erneuerbare
  (e.g., deprecated codes or codes only in D.xlsx).
