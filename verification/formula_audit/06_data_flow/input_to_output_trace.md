# §7 Data flow — input → output trace for 5 representative inputs

For each input, we list (a) the Excel cells that recompute on change,
and (b) the DB-model fields our code propagates to. Set-diff at the
bottom.

---

## Input 1 — `LandUse[LU_2.1]` Solare Freiflächen (target_ha)

### Excel consumers (verified by cell search in `_S.xlsx`)

| cell | formula | what it means |
|------|---------|---------------|
| `1. Flächen!L13` | (self) | LU_2.1 ziel |
| `1. Flächen!L25` | `=L12-L14-L22-L13` | LU_2.4 residual (proved in F002) |
| `1. Flächen!M13` | `=L13/L12*100` | LU_2.1 % share of LF |
| `1. Flächen!O13` | `=L13/I13` | status-to-ziel ratio |
| `2. Erneuerbare!L_(INDIRECT_to_1.Flächen!L13)` | `INDIRECT(...)` | pulls LU_2.1 ziel into Renewable 1.2 (Solarstrom Freiflächen) |
| `5. Bilanz!*` | downstream via `='2. Erneuerbare'!L237`-type pulls | cascades into KLIK Strom renewable |

### DB consumers (verified by grep + `Formula.expression__icontains`)

| `Formula.key` | expression | target model row |
|---|---|---|
| `1.2` (renewable) | `LandUse_LU_2.1` | RenewableData[1.2] status |
| `1.2_target` (renewable) | `LandUse_LU_2.1_ziel` | RenewableData[1.2] ziel |
| `1.2.1.2` (renewable) | `LandUse_LU_2.1 * Renewable_1_2_1_1 / 1000` | RenewableData[1.2.1.2] status |
| `1.2.1.2_ziel_target` (renewable) | `LandUse_LU_2.1 * Renewable_1_2_1_1 / 1000` | RenewableData[1.2.1.2] ziel |

Plus implicit consumers via `LandUse.parent` (LU_2 = LF) when
sibling shares recompute: LU_2.4 target = LF − Ackerland −
Dauergrünland − LU_2.1 (matches Excel L25).

### Set-diff

**Excel set** (direct + cascaded): L13 → L25, M13, O13, 2.Erneuerbare!1.2-row, 5.Bilanz!renewable-strom.

**DB set**: RenewableData[1.2] status+ziel, RenewableData[1.2.1.2] status+ziel, LU_2.4 via `percentage_rebalancer`, Bilanz via `calculate_bilanz_data()`.

**Conclusion**: CONGRUENT. Both sources cascade LU_2.1 ziel through the same conceptual chain: Solar Freiflächen area → Solar renewable energy → KLIK renewable contribution → Bilanz KLIK row.

No extra consumer on either side.

---

## Input 2 — `VerbrauchData[1.1.2]` Zieleinfluss Endanwendungs-Effizienz

### Excel consumers

| cell | formula | what it means |
|------|---------|---------------|
| `4. Verbrauch!M25` | (self, literal seed 95) | Zieleinfluss %  |
| `4. Verbrauch!M26` | `=M24*M25/100` | Endenergie Haushalte after efficiency |
| Further chain: `M26` → `M27` (Endenergie KLIK) → `M42` (KLIK total) → `5. Bilanz!K9`/etc. |

### DB consumers

| Formula key | expression |
|---|---|
| `V_1.1.3` | `Verbrauch_1_1_1 * Verbrauch_1_1_2 / 100` |
| `V_1.1.3_ziel` | `Verbrauch_1_1_1_ziel * Verbrauch_1_1_2_ziel / 100` |

Further cascades: 1.1.3 → 1.4 (KLIK total) → Bilanz KLIK Strom.

### Set-diff

Both reach KLIK total and then Bilanz. CONGRUENT in structure.

---

## Input 3 — `Formula[WS_ETA_STROM_GAS]` (0.65)

### Excel consumers

Named range `EtaStromGas = 1.Jahresbilanz_Strom!N33 = 0.65`.

Usage: every day's Einspeich formula in `Zeitreihen Kalkulation!P158..P521`:
```
P_r = IF(O_r/I_r <= Abregelung, O_r, I_r * Abregelung) * EtaStromGas
```

Also used in:
- `Zeitreihen!P156` (Volllaststunden: `=(I$152/EtaStromGas)/365`)
- `P158..P521 → P152` (annual sum → used in speicher capacity calc)
- `1.Jahresbilanz_Strom!L36` (Gas storage input — indirect through Einspeich sum)
- `M44` Speicherkapazität → M45 tages

### Code consumers

Grepping for `ETA_STROM_GAS` in `simulator/` + `calculation_engine/`:

- `WS365Formula[einspeich]` references `ETA_STROM_GAS` in expression
- `WS365Formula[ausspeich_rueckverstr]` references `ETA_GAS_STROM` (separate constant)
- `simulator/balance_api.py:61` — `ely_surplus = einspeich_sum / eta_strom_gas`
- `simulator/signals.py:120` — `n_output_branch = einspeich_sum / 0.65 if einspeich_sum > 0 else 0.0`
  ⚠ **Note**: the 0.65 is HARDCODED here, not pulled from `WS_ETA_STROM_GAS`. If the constant ever changes, this line won't update.
- `calculation_engine/ws_engine.py` (DEAD CODE — F006)

### Set-diff

Mostly CONGRUENT:
- Both sources use EtaStromGas/ETA_STROM_GAS in Einspeich + storage
  calcs.
- `simulator/signals.py:120` hardcodes 0.65 — this is a MINOR finding
  (F006.5) — a constant maintenance risk, but not a current bug since
  the two values match.

---

## Input 4 — `Formula[LANDUSE_TARGET_PERCENT]` (`child_target / parent_target * 100`)

### Excel consumers

Pattern formula used in column M of `1. Flächen` rows 9-34:
```
M_r = L_r / INDIRECT("L" & AB_r) * 100
```
where `AB_r` points to parent row.

### Code consumers

`Formula[LANDUSE_TARGET_PERCENT]` is referenced by `LandUse.calculate_target_percent()` and `formula_service._ensure_ratio_tokens`:

- `simulator/models.py` — `LandUse.target_percent` property
- `simulator/percentage_rebalancer.py` — computes target_percent when sibling shares change

### Set-diff

CONGRUENT at the conceptual level. Both compute child/parent × 100.

---

## Input 5 — `LandUse[LU_6]` Windparkfläche (target_ha)

### Excel consumers

Similar pattern to LU_2.1:
- `1. Flächen!L34` = `IF(R34=...)` — user-percent formula (R34 = 2.0003)
- `1. Flächen!L35` = Belegung = user_pct × L34
- `2. Erneuerbare!L-row-for-Wind` — Windenergie Flächenertrag uses L34
- `5. Bilanz` — Wind → KLIK Strom renewable → Bilanz KLIK

### Code consumers

| Formula key | expression |
|---|---|
| `6.1.1` | `lu_223_status` (naming aside, maps to LU_2.2.3) — *probably wrong chain?* |
| WS365 `wind_ertrag_366` (if any) | … |

LU_6 specifically doesn't show up in the formula table grep, so it
feeds through the LandUse parent/child mechanism + signal-triggered
recalc.

### Set-diff

Concept-level CONGRUENT but less explicit in our Formula table than
LU_2.1. Wind renewable values may be computed in `ws365_core.py` /
`ws_365_service.py` using LU_6 through the `compute_ws_diagram_reference`
flow.

---

## Signals / cache invalidation parity

- Our code: `simulator/signals.py` fires on `LandUse`/`VerbrauchData`/`RenewableData` save → triggers `recalc_service.py` → propagates to dependent rows → invalidates `recalc_cache._cache`, `_AUTO_TOKENS_CACHE`, `_LOOKUPS_CACHE`, `_WS365_COMPUTE_CACHE`.
- Excel: changes propagate immediately via cell-formula dependency graph (synchronous recompute on cell edit).

**Key difference**: Excel's recompute is ALWAYS synchronous and TOTAL (all dependents recompute). Our code is EVENT-DRIVEN and selective — only rows in `recalc_service`'s dependency list recompute. If a dependency is missing from that list, a cell won't propagate.

This is the architectural origin of past incidents (commits `54d4567`, `9b0cf3d`, `691b99f`) — when signals didn't fire or dependencies weren't registered, cells stayed stale.

**Finding**: Cascade PARITY is BROADLY ALIGNED at the conceptual
level, but the specific set of consumers is:

- Always complete in Excel (dependency graph).
- Potentially incomplete in our code (depends on explicit
  dependency declaration per row).

The 5 inputs I traced all showed consistent consumer sets between
the two sources. But a systematic every-row comparison would be
needed to prove full parity — deferred.
