# §7 Data flow + Cascade Parity — summary

## Approach

Picked 5 representative inputs spanning each major DB model:

1. `LandUse[LU_2.1]` Solare Freiflächen (target_ha) — land use input
2. `VerbrauchData[1.1.2]` Zieleinfluss Endanwendungs-Effizienz — Verbrauch seed
3. `Formula[WS_ETA_STROM_GAS]` — WS365 constant
4. `Region.installed_pmax_ely_gw` — region-scope extension (no Excel analog)
5. `LandUse[LU_6]` Windparkfläche — renewable cascade

For each, traced:
- Excel dependency graph (who reads the cell downstream)
- Our code dependency graph (grep + Formula.expression search)
- Signal/cache invalidation points
- Set-diff

## Results

| input | Excel ∩ DB | Excel ∖ DB | DB ∖ Excel | verdict |
|-------|------------|------------|------------|---------|
| LU_2.1 ziel | ✓ full chain | none | percentage_rebalancer (functional equivalent) | CONGRUENT |
| Verbrauch 1.1.2 ziel | ✓ full chain | none | none | CONGRUENT |
| WS_ETA_STROM_GAS | ✓ 365-day chain | none | `signals.py:120` hardcodes 0.65 (code-hygiene risk) | CONGRUENT (with note) |
| Region.pmax_ely_gw | N/A | (Excel has no equivalent input) | extra input | INTENTIONAL EXTENSION |
| LU_6 | ✓ wind chain | none | none | CONGRUENT |

## Findings produced

No NEW finding from this pass. Cross-references existing findings:

- F006 (`WS_ABREGELUNG_THRESHOLD` dead code) relates to the WS
  constant cascade.
- The `signals.py:120` hardcoded `0.65` is a minor code-hygiene note
  (if `WS_ETA_STROM_GAS` ever changes, this line stays at 0.65).
  Not elevated to a finding because today both values are 0.65.

## Architectural observations

1. **Excel cascade is dense + synchronous**. Every cell with a
   formula recomputes on any upstream change automatically.

2. **Our cascade is event-driven + selective**. Only dependencies
   declared in `Formula.expression` (for computed rows) or wired
   into `recalc_service` (for property-based recalc) fire. Missing
   declarations = silent staleness.

3. **Cross-process signal gap**: Django signals only fire within
   the process that invoked the save. Heroku's web ↔ worker are
   separate processes, so `run_balance_job` in the worker must
   invalidate its OWN caches at job entry to stay coherent (per
   `54d4567`). This is a known architectural constraint and is
   correctly handled today.

4. **Owner + region extensions**: our code supports per-user
   workspaces and per-region (Bundesland) data; Excel has a single
   Germany scenario. These are INTENTIONAL model extensions beyond
   Excel's expressiveness, not parity violations.

## Self-skepticism — limitations

1. **Only 5 inputs traced** — a full cascade-parity proof needs
   hundreds of edit scenarios. For each input we'd need to:
   - Edit the cell in Excel and snapshot the changed cell set.
   - Edit the DB row and snapshot the recomputed row set via
     post-save signals.
   - Set-diff.
   
   This would take order-of-magnitude more time than this pass
   allowed.

2. **Symbolic tracing, not live execution** — I used grep and
   formula-graph traversal to infer consumer sets. I did not run
   live edits and observe actual propagation. The 5 inputs may
   cascade further than my grep captured.

3. **Signal-fire order** — I did not verify that signals fire in
   the right order when multiple interdependent rows change at
   once. Past incidents (`691b99f`) show this is a real risk.

## Self-skepticism checklist

- [x] Multiple inputs traced (5)
- [x] Compared Excel formula graph to DB Formula graph
- [x] Considered signal/cache architecture
- [x] Re-derived from sources (not just reading SOURCE_GROUNDED_ANSWERS)
- [x] Found unexpected: `signals.py:120` hardcodes 0.65 — minor but
      worth noting for future constant hygiene.

## Artifacts

- `input_to_output_trace.md` — per-input consumer set trace.
- `cascade_parity.md` — per-edit scenario analysis, architecture
  notes.
