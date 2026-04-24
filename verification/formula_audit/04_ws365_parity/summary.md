# §5 WS365 Daily Time-Series + Named Constants — summary

## Inputs

- **DB source**: `WSData.all_objects.filter(owner=None)` — 368 rows (365 days + 3 summary). Fields: `wind_promille`, `solar_promille`, `heizung_abwaerm_promille`, `verbrauch_promille`.
- **Excel source**: `WS.xlsm!Zeitreihen Kalkulation` columns C (wind), D (solar), E (heizung), F (verbrauch) — rows 157–521 (365 days; header row 151).
- **Named ranges**: extracted all 17 workbook-level named ranges from `WS.xlsm` and cross-referenced to our `ws_constant` Formula rows.
- **Script**: `scripts/08_ws365_parity.py`.

## Daily time-series parity

**1460 comparisons** (365 days × 4 input fields):

| verdict | count | % |
|---------|------:|----:|
| EXACT | 1,239 | 84.9 % |
| PASS_COSMETIC (< 0.01 %) | 221 | 15.1 % |
| PASS (0.01–0.1 %) | 0 | 0 % |
| DRIFT (> 0.1 %) | **0** | **0 %** |

**Zero drift across all 365 × 4 input fields.** The WSData seed
faithfully mirrors Excel `Zeitreihen Kalkulation!C..F`. Residual drift
in the 221 PASS_COSMETIC rows is at the 5-to-7-digit precision level
— essentially float-rounding between openpyxl's cached value and
Python `float(string(...))` round-trips through the DB.

Spot checks:

| day | field | DB | Excel | drift |
|----:|-------|----|-------|------:|
| 1 | wind_promille | 4.699377 | `C157` = 4.6993765253 | 5×10⁻⁸ |
| 1 | solar_promille | 0.800146 | `D157` = 0.8001456247 | 8×10⁻⁸ |
| 180 | solar_promille | 4.373611 | `D336` = 4.3736111... | ≤ 10⁻⁸ |
| 318 | verbrauch_promille | 3.146620 | `F474` = 3.1466198... | ≤ 10⁻⁸ |

## Named-range parity (17 named ranges in `WS.xlsm`)

| name | Excel value | DB key | DB value | verdict |
|------|-------------|--------|----------|---------|
| `EtaStromGas` | 0.65 | `WS_ETA_STROM_GAS` | 0.65 | **EXACT** ✓ |
| `EtaRückverstromung` | 0.585 | `WS_ETA_GAS_STROM` | 0.585 | **EXACT** ✓ |
| `Abregelung` | 1.0 | `WS_ABREGELUNG_THRESHOLD` | 0.65 | **DRIFT** (F006 — dead code, not wired to live path) |
| `SelbstentladungsRate` | 0 | — | — | no DB counterpart needed (zero) |
| `TLproEingabeEinheit` | 0.000329 | computed live as `365 / VerbrauchStrom` | — | EQUIVALENT (derived, not stored) |
| `VerbrauchStrom` | 1,108,198.26 | computed live as annual sum of I | — | EQUIVALENT |
| `AbregCopy`/`Paste`, `EtaCopy`/`Paste`, `AufnahmeCopy`/`Paste`/`ProzentCopy` | computed outputs | — | — | N/A — Excel UI staging cells, not constants |
| `AnimationFlussbild` | 1 | — | — | N/A — UI toggle |
| `SpeicherBilanz` | 0 | — | — | N/A — sanity-check cell |
| `WS_Abgleich` | (cross-book `#REF!`) | — | — | broken external ref |
| `waste1` | 406,108.38 | — | — | N/A — staging |

**Summary**: 2 of 3 proper WS constants match exactly; the 1 that
drifts (`Abregelung` / `WS_ABREGELUNG_THRESHOLD`) is F006 — already
documented as dead code not wired to the production path.

## Findings produced

No new findings from this pass (F006 already captured in §3).

## Self-skepticism — limitations

1. **Only INPUT columns compared**. Columns G–X (Stromverbr., Wind+Solar+konstant, Einspeich, Abregelung output, etc.) were not compared against our derived values here — those would require running `WS365Formula` evaluation with the same inputs and comparing row-by-row. That comparison is partially done under §6 Jahresstrom parity (which looks at the annual sums).

2. **Single owner (owner=None)**. Testsim's workspace `WSData` was not compared; it is created from the None-owner seed by `ensure_user_workspace_data` so should be identical unless testsim has been mutated.

3. **Excel `Z` / `AA` columns** for the SMARD reference (raw data input) were not enumerated — could be a source for upstream seed validation.

## Self-skepticism checklist

- [x] Multiple tolerances (0.1 % and 0.01 %)
- [x] Formula shape compared (F006 crossref)
- [x] Multiple days spot-checked (1, 2, 3, 180, 318, 365)
- [x] Re-derived from Excel sources
- [x] Found unexpected: the audit confirms input pipeline is clean,
      which itself is a useful negative finding.

## Artifacts

- `daily_timeseries_diff.csv` (1460 rows, full 365-day comparison)
- `named_constants.csv` (17 named ranges, matched to DB)
- `discrepancies.md` (verdict distribution + constants table)
- F006 cross-reference
