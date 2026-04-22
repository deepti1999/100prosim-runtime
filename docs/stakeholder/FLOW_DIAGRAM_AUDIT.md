# Flussdiagramm Strom / H₂ — audit vs Excel reference

**Phase 5-C (T53, T54, T55, T56).** Stakeholder PDF §2.5.6 complaint:

> "Auch nach einer ersten Überarbeitung bildet die Grafik die dem Szenario
> zugrundeliegenden Strukturen noch nicht korrekt ab, teilweise sind die
> Werte falsch zugeordnet und wegen der kleinen Schriftart ist das
> Diagramm schlecht lesbar."

## What shipped in Phase 5-C

### T55 — Legibility (fixed)

- Font-size classes bumped ~20–30 % across the SVG:
  | class | before | after |
  |---|---|---|
  | `txt-title` | 20 | 24 |
  | `txt-label` | 12 | 14 |
  | `txt-label-lg` | 16 | 19 |
  | `txt-value` | 16 | 18 |
  | `txt-flow` | 15 | 17 |
  | `txt-node` | 18 | 20 |
  | `txt-metric` | 12 | 14 |
- New zoom controls above the SVG: 75 % / 100 % / 125 % / 150 % / 200 %.
  Uses CSS `transform: scale()` with proportional width/height so the
  scroll container reserves the right space.

### T53 — Node-by-node audit vs Excel

Current `annual_electricity.html` SVG nodes, mapped to the Excel
reference (PDF page 10):

| Excel node (page 10) | SVG element / id in our template |
|---|---|
| Bedarfs-Kraftwerke / Biobrennstoffe | `#bio_value` — yellow rect top-left |
| PV (fluktuierend) | `#pv_value` — yellow rect, mid-left |
| Wind (fluktuierend) | `#wind_value` — yellow rect below PV |
| Laufwasser + Tief.-Geoth. (konstant) | `#hydro_value` — yellow rect, bottom-left |
| M (Bruttostromerzeugung summer) | `#m_value` — circle at centre |
| Abregelung (Q) | `#q_value` |
| Elektrolyse Power to Gas, 65 % Eta Ely. | `#ely_branch_value` / `#ely_offer_value` / `#eta_ely_value` |
| Gasspeicher Direktverbr. | `#gasspeicher_direkt_value` |
| Elektrolyse Stromspeicher (Überschuss), 65 % Eta ES | `#n_value_svg` / `#n_output_branch_value` / `#eta_es_value` / `#ely_surplus_value` / `#h2_surplus_value` |
| Gasspeicher Strom | `#gas_storage_arrow_value` |
| Speicherkapazität | `#storage_capacity_value` |
| Rückverstromung (Mangelausgl.), 59 % Eta RS | `#t_value_svg` / `#eta_rs_value` / `#reconversion_value` |
| Stromnetz zum Endverbrauch | `#final_value` + `#o_value_svg` |

All 13 Excel nodes are **structurally present** in our SVG. Structure
check passes.

### T54 — Value-to-node assignments (needs reference data)

Stakeholder reports "teilweise sind die Werte falsch zugeordnet." We
have not yet done a side-by-side numeric comparison with an Excel
export for the identical scenario. Doing that responsibly requires:

1. A clean seed scenario run in both the Excel tool and the web app.
2. Exporting the Excel "AH.Jahresbilanz" sheet values for each node.
3. Comparing against the web diagram's rendered numbers.
4. Filing a targeted fix per mismatch, with the Excel cell reference in
   the commit message.

**Open action:** once Pascal/Schmidt-Kanefendt share the Excel export
for the current seed (or equivalent reference numbers), run the diff
and correct any mislabelled `id` → `vals.*` binding in
`simulator/templates/simulator/annual_electricity.html` (the JS
`setText(id, value)` block near DOMContentLoaded).

### T56 — Excel-reference structure

The SVG already follows the PDF page 10 reference layout: sources on
the left, M-circle as the conversion/curtailment hub, H₂ electrolysis
+ gas-storage path on the right, with the Stromnetz zum Endverbrauch
as the final sink. No structural rework needed pending the T54 value
audit.

## Verification done in Phase 5-C

- V2 tests: all black-box tests continue to pass.
- V4 localhost: authenticated GET of `/annual-electricity/` returns
  200. Font-size CSS rules and zoom-control DOM present. SVG viewBox
  unchanged so no relayout regressions.
- V5 Heroku: validated at the Phase 5 batch.
