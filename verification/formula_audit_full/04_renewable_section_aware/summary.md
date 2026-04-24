# §04 Renewable Section-Aware Parity — summary

## Inputs

- **DB source**: 223 RenewableData rows (owner=None).
- **Mapping**: `01_curated_mappings/renewable_to_excel.csv` (section-aware).
- **Excel source**: `_S.xlsx!2. Erneuerbare`.
- **Script**: `scripts/07_renewable_parity.py`.

## Coverage — 223/223 rows processed

## Status column verdict distribution

| verdict | count |
|---------|------:|
| EXACT | 53 |
| PASS (≤ 0.1 %) | 25 |
| PASS_COSMETIC (≤ 0.01 %) | 11 |
| DRIFT | 68 |
| DRIFT_SCALE_* | 23 |
| NO_MATCH | 27 |
| NO_EXCEL_CELL_DOCUMENTED | 16 |

## Ziel column verdict distribution

| verdict | count |
|---------|------:|
| EXACT | 69 |
| PASS (≤ 0.1 %) | 10 |
| PASS_COSMETIC (≤ 0.01 %) | 27 |
| DRIFT | 65 |
| DRIFT_SCALE_* | 10 |
| NO_MATCH | 26 |
| NO_EXCEL_CELL_DOCUMENTED | 16 |

## F005 status

**CLOSED — proven.** See `f005_resolution.md`.

- `5.4.2.1` Biogas Nutzungsgrad Kraftwerk: DB 37.5/45 vs Excel 25/35 → HIGH DRIFT confirmed.
- `5.4.2.3` Biogas Nutzungsgrad KWK-Abwärme: DB 21.9/25 vs Excel 45/45 → HIGH DRIFT confirmed.
- `6.1.3.2.3` Biodiesel Nutzungsgrad KWK-Abwärme: DB 50/50 vs Excel 50/50 → EXACT.

The section-aware mapping resolved the ambiguity that made Round 1's
F005 unprovable. F005 elevated to HIGH / HIGH confidence.

## Other significant findings (§04)

| ID | Severity | Confidence | description |
|----|---------:|-----------:|-------------|
| F005 (resolved) | HIGH | HIGH | Biogas Nutzungsgrad — confirmed drift |
| F014 (new) | MEDIUM | MEDIUM | Cluster: 20+ renewable efficiency / yield factor drifts 5-30 % |

F014 is the cluster of DRIFT rows (68 status + 65 ziel) at > 1 % —
most concentrated in:
- Biomasse sector Nutzungsgrad and Flächenertrag
- Solar sector areal yields (MWh/ha/a)
- Biogas yield and Biomethan split

Each drift is individually small but collectively points to a
systemic seed-scenario drift where DB values reflect an earlier
scenario state than the current Excel cache.

## Completeness attestation

- [x] 223/223 rows compared
- [x] Status + Ziel both checked per row
- [x] Scale-factor ladder {1, 1000, 1/1000, 10000, 1/10000, 100, 0.01}
- [x] Tolerance ladder {EXACT, 0.01 %, 0.1 %, > 0.1 %}
- [x] F005 proven via section-aware mapping
- [x] OOS rows have documented reasons

## Artifacts

- `per_row_parity.csv` — 223 rows with per-row verdict
- `f005_resolution.md` — F005 closed as HIGH-confirmed
- `curated_mapping_notes.md` — how section ambiguities were resolved
- `summary.md` — this file
- `discrepancies.md` — DRIFT rows table
