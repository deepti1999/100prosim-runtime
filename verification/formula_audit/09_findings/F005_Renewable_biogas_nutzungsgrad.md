# F005 — RenewableData Biogas Nutzungsgrad — possible section-mismatch

**Severity**: HIGH if confirmed (efficiency factors drive GWh/a conversion).
**Affects calc**: YES if confirmed — Verstromung and KWK-Abwärme conversion factors.
**Domain**: §2 value parity (RenewableData, Biogas subsection)
**Confidence**: MEDIUM — matcher associated DB row by NAME which appears in multiple Excel sections; needs section-level cross-check before calling PASS/FAIL.

## Observed (as matched by name)

| DB row | DB status | DB ziel | matched Excel cell | Excel L | Excel M |
|--------|-----------|---------|--------------------|---------|---------|
| `RenewableData[5.4.2.1]` Biogas **Nutzungsgrad Kraftwerk** | 37.5 % | 45 % | `2. Erneuerbare!84` *Nutzungsgrad Kraftwerk* | 25 | 35 |
| `RenewableData[5.4.2.3]` Biogas **Nutzungsgrad KWK-Abwärme effektiv** | 21.9 % | 25 % | `2. Erneuerbare!86` *Nutzungsgrad KWK-Abwärme effektiv* | 45 | 45 |
| `RenewableData[6.1.3.2.3]` Biodiesel **Nutzungsgrad KWK-Abwärme effektiv** | 50 % | 50 % | `2. Erneuerbare!86` (same row — collision) | 45 | 45 |

Both the Biogas and Biodiesel flows have a child row named
"Nutzungsgrad KWK-Abwärme effektiv" — the matcher collapsed them
onto Excel row 86.

## Why this is UNPROVEN, not PASS/FAIL

Excel `2. Erneuerbare` groups metrics by energy-source section. Row
86 might belong specifically to the Biogas section, or it might be
the Biodiesel one — without section-header cross-reference we
cannot say which DB row row 86 is supposed to mirror.

The matcher's current heuristic (best normalized-name match) is
blind to section membership. A correct verdict needs:

1. Dump `2. Erneuerbare` section headers (column E hierarchy) to
   establish which row-range belongs to Biogas vs Biodiesel vs
   Biomethan vs …
2. For each DB Nutzungsgrad row, cross-reference ONLY within its
   section range.
3. Then compare `status_value` / `target_value` at 0.1 % tolerance.

## Evidence to date

- `2. Erneuerbare!L84` = 25, `M84` = 35 (Nutzungsgrad Kraftwerk)
- `2. Erneuerbare!L86` = 45, `M86` = 45 (Nutzungsgrad KWK-Abwärme effektiv)
- DB Biogas 5.4.2.1 = 37.5 / 45 — **disagrees** with r84's 25/35 if
  r84 is the Biogas one. CSV flagged DRIFT.
- DB Biogas 5.4.2.3 = 21.9 / 25 — **disagrees** with r86's 45/45 if
  r86 is the Biogas one.
- DB Biodiesel 6.1.3.2.3 = 50 / 50 — **disagrees** with r86's 45/45
  if r86 is the Biodiesel one.

Since DB 5.4.2.3 (21.9/25) and 6.1.3.2.3 (50/50) **cannot both** be
the single Excel row 86 (which holds 45/45), at least ONE of them
is wrong in the DB (or the matcher picked the wrong row for one).

## Suggested next step

Manually enumerate `2. Erneuerbare` sections and produce a
section-aware Nutzungsgrad mapping. Deferred from this pass — logged
as a follow-up.

## Scripts

Rows flagged DRIFT in `01_value_parity/per_row_comparison.csv` for
`RenewableData/5.4.2.1`, `5.4.2.3`, `6.1.3.2.3`.
