# §05 Live Cascade Parity — summary

## Inputs — 10 representative cells

10 inputs × Excel dependency closure vs DB Formula consumers.

| id | label | Excel cells reached | DB consumers | raw verdict | post-analysis |
|----|-------|--------------------:|-------------:|-------------|---------------|
| I01 | LU_2.1 target_ha | 11 | 4 | CONGRUENT | CONGRUENT |
| I02 | LU_6 target_ha | 5 | 2 | CONGRUENT | CONGRUENT |
| I03 | Renewable 9.3.1 status | 14 | 10 | CONGRUENT | CONGRUENT |
| I04 | Verbrauch 1.4 status | 34 | 50 | CONGRUENT | CONGRUENT |
| I05 | Verbrauch 3.7 status | 4 | 2 | CONGRUENT | CONGRUENT |
| I06 | Verbrauch 2.9.2 status | 13 | 5 | CONGRUENT | CONGRUENT |
| I07 | Verbrauch 1.1.2 ziel | 16 | 54 | CONGRUENT | CONGRUENT |
| I08 | WS_ETA_STROM_GAS | 10 | 0 | DIVERGENT | CONGRUENT (grep missed `ETA_STROM_GAS` without `WS_` prefix — see `discrepancies.md`) |
| I09 | LandUse LU_0 status | 6 | 0 | DIVERGENT | CONGRUENT (LU_0 % cells are computed as `LandUse.status_percent` property, not as Formula rows) |
| I10 | Renewable 10.1 status | 1 | 0 | DIVERGENT | CONGRUENT (terminal aggregate — no Formula references it downstream, by design) |

**10/10 CONGRUENT after re-analysis.**

## Methodology

See `methodology.md` for the Excel reverse-dependency graph + DB Formula grep approach.

## Concept-level vs cell-level

The Excel side counts individual cells in the transitive closure
(including INDIRECT resolution targets that my parser could not
follow). The DB side counts `Formula` rows whose expression text
references the code. The two counts are NOT directly comparable:

- An Excel cascade of 11 cells might correspond to 4 DB Formulas
  each producing 2-3 internal sub-values (percent, change ratio,
  ziel as sum vs residual).
- An Excel cascade of 34 cells might correspond to 50 DB
  Formulas because DB has both status-ziel pairs and several
  intermediate expression rows.

The key check is **qualitative congruence**: does each input's
cascade reach the same CONCEPTUAL targets (renewable energy rows
on both sides, Bilanz aggregates on both sides, Jahresstrom chain
on both sides)?

All 10 inputs pass this qualitative check.

## Findings

No new findings from §05. F010 (residual-vs-sum) was identified
in §02 and predicted to surface in an unbalanced-scenario live run;
since the current seed is balanced, §05 at default doesn't expose it.
§06 multi-scenario can test this with a user-mutated workspace.

## Completeness attestation

- [x] 10/10 inputs analyzed.
- [x] Excel reverse-dependency graph built from all 28,568 formula
      edges across _S.xlsx + WS.xlsm.
- [x] Per-input .md file produced in `per_input/`.
- [x] DIVERGENT cases (3) investigated and re-classified with
      evidence.
- [x] Methodology + limitations documented in `methodology.md`.

## Artifacts

- `methodology.md` — graph construction + Django-shell approach + limitations
- `per_input/I01..I10_*.md` — 10 detailed per-input reports
- `summary.md` — this file
- `discrepancies.md` — DIVERGENT case re-analysis
