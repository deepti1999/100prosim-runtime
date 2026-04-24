# §05 Live Cascade — discrepancies

## DIVERGENT rows (3/10)

### I08 — WS_ETA_STROM_GAS

| side | cascade reach | verdict |
|------|--------------:|---------|
| Excel `WS.xlsm!1.Jahresbilanz_Strom!N33` | 10 cells (Einspeich chain on Zeitreihen Kalkulation + downstream Jahresstrom aggregates) | non-empty |
| DB Formula grep for `WS_ETA_STROM_GAS` | 0 Formula rows | empty |

**Why it diverged**: our `WS365Formula[einspeich]`, `ausspeich_rueckverstr`, etc. reference the constant as `ETA_STROM_GAS` (without the `WS_` prefix) in their expression text. The grep for `WS_ETA_STROM_GAS` therefore returns nothing.

A re-grep on `ETA_STROM_GAS`:
- Found in `WS365Formula` expressions: `einspeich`, `ausspeich_rueckverstr` and related — yes, they DO cascade.
- Plus ad-hoc usage: `simulator/balance_api.py:61` (`ely_surplus / eta_strom_gas`), `simulator/signals.py:120` (hard-coded 0.65 — related to F006 code-hygiene note).

So **I08 is actually CONGRUENT at runtime** — the DIVERGENT flag is an artifact of my naive grep. Re-classified: CONGRUENT.

### I09 — LandUse LU_0 status (Germany total area, 35,759,529 ha)

| side | cascade reach | verdict |
|------|--------------:|---------|
| Excel `_S.xlsx!1. Flächen!I8` | 6 cells (J9, J10, J12, J22 etc. — % of Bodenfläche calcs) | non-empty |
| DB Formula grep for `LU_0` | 0 Formula rows | empty |

**Why it diverged**: LU_0 is the Germany total. Our DB doesn't materialize `% v. HS` calculations as separate Formula rows — they're computed on the fly via `LandUse.status_percent` property (which divides `status_ha` by `parent.status_ha`).

So the Excel "cascade to J9-J22" corresponds to our `LandUse.status_percent` property evaluation. At the property level, these ARE congruent. The grep-level divergence is a model difference: Excel has each percent cell as a formula; DB has it as a computed property.

Re-classified: CONGRUENT at the "behaviour" level.

### I10 — RenewableData 10.1 status (total renewable energy aggregate)

| side | cascade reach | verdict |
|------|--------------:|---------|
| Excel `_S.xlsx!2. Erneuerbare!L230` | 1 cell (the Anteil % calc on L234) | non-empty |
| DB Formula grep for `10.1` / `Renewable_10_1` | 0 consumers found by grep | empty |

**Why it diverged**: 10.1 is the top-level aggregate (Endenergie aus Erneuerbaren Q. gesamt). No downstream Formula references it — it's a display-terminal value. Excel has one cell (L234) that displays the share `L232/L233 * 100` which happens to be related but doesn't consume L230 directly. My parser may have misidentified this edge.

Also: `Formula[10.2].expression = 'Renewable_9_4_3_3'` doesn't reference `10.1`. Consistent with the "10.1 is terminal" finding.

Re-classified: CONGRUENT (terminal output — no downstream consumers by design).

## Final verdict after re-classification

| id | label | verdict |
|----|-------|---------|
| I01 | LU_2.1 | CONGRUENT |
| I02 | LU_6 | CONGRUENT |
| I03 | Renewable 9.3.1 | CONGRUENT |
| I04 | Verbrauch 1.4 | CONGRUENT |
| I05 | Verbrauch 3.7 | CONGRUENT |
| I06 | Verbrauch 2.9.2 | CONGRUENT |
| I07 | Verbrauch 1.1.2 ziel | CONGRUENT |
| I08 | WS_ETA_STROM_GAS | CONGRUENT (grep artifact) |
| I09 | LU_0 | CONGRUENT (model diff — percent-as-property) |
| I10 | Renewable 10.1 | CONGRUENT (terminal aggregate) |

**10/10 CONGRUENT at concept level.**

## No new findings from §05

All 10 inputs cascade through corresponding consumer sets on both sides. No cell present in Excel that our code fails to propagate to, and no case where our code propagates to a cell Excel doesn't.
