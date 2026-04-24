# F006 — `WS_ABREGELUNG_THRESHOLD = 0.65` constant is dead code; would produce wrong Einspeich if used

**Severity**: LOW — confirmed unused in production pipeline.
**Affects calc**: NO — production path uses `WS365Formula`, not the legacy constant.
**Domain**: §3 formula parity (WS constants + ws_engine.py legacy)
**Confidence**: HIGH — grep + direct pipeline trace.

## Observed

### The constant

`Formula(key='WS_ABREGELUNG_THRESHOLD', category='ws_constant', expression='0.65')` is loaded by
`calculation_engine/ws_engine.py:40`:

```python
abregelung_threshold = Formula.objects.get(
    key='WS_ABREGELUNG_THRESHOLD', category='ws_constant')
self.ABREGELUNG_THRESHOLD = float(abregelung_threshold.expression)  # 0.65
```

and then used to decide **both** the Einspeich/Abregelung branch
threshold AND the capped-mode multiplier
(`calculation_engine/ws_engine.py:189-192, 199`):

```python
if ratio <= self.ABREGELUNG_THRESHOLD:                         # 0.65
    result['einspeich'] = ueberschuss * ETA_STROM_GAS
else:
    result['einspeich'] = stromverbr * ABREGELUNG_THRESHOLD * ETA_STROM_GAS  # 0.65*0.65 = 0.4225
```

### The Excel equivalent

`WS.xlsm!Zeitreihen Kalkulation!P158` (and identical pattern on P159..P521):

```
= IF(O158/I158 <= Abregelung, O158, I158 * Abregelung) * EtaStromGas
```

Named range `Abregelung` is **`'1.Jahresbilanz_Strom'!N32 = 1`** (cached).
So Excel uses threshold `1.0` and multiplier `1.0`; Einspeich caps
only when daily excess exceeds daily demand.

### Quantified divergence (hypothetical, if ws_engine.py were live)

|  |  Excel  |  `ws_engine.py`  |
|---|---------|------------------|
| threshold on `O/I` | 1.0 | 0.65 |
| capped-mode multiplier | 1.0 | 0.65 |
| day 318 Einspeich (max-ratio day, I=1547, O=5882) | 1005.68 | 653.69 (**35 % short**) |
| days where branch diverges (`0.65 < O/I ≤ 1`) | 0 | 34 (of 365) |
| days where multiplier diverges (`O/I > 1`) | 0 | 124 (of 365) |

If `ws_engine.py` were wired to production, it would under-count
annual Einspeich by a visible double-digit percentage and push
Mangel-Last / Ausspeich artefacts through the rest of the WS365
chain.

## Why this is NOT a live production bug

Grep confirms `calculation_engine/ws_engine.py` has NO importers in
`simulator/`:

```
$ grep -rn "from calculation_engine.ws_engine import" simulator/
(no matches)
$ grep -rn "ws_engine" simulator/ calculation_engine/
(only internal references within ws_engine.py itself)
```

Production WS365 computation flows through `WS365Formula` rows
(added in migration `0044_ws365formula`). The live DB row for
Einspeich has the correct formula:

```
einspeich:  IF(stromverbr_raumw_korr > 0,
               IF((ueberschuss_strom / stromverbr_raumw_korr) <= 1,
                  ueberschuss_strom * ETA_STROM_GAS,
                  stromverbr_raumw_korr * ETA_STROM_GAS),
               0)
```

Threshold = 1, multiplier = 1 — matches Excel. Query:

```
simulator.ws_models.WS365Formula.objects.get(column_name='einspeich').expression
```

## Severity rationale

- `Formula[WS_ABREGELUNG_THRESHOLD]` is loaded only by
  `ws_engine.py`.
- `ws_engine.py` is not imported by any production module.
- So the constant has **no production effect**.
- It IS misleading for anyone reading the code / seed, because the
  0.65 value looks load-bearing but isn't.

## Recommended fix (optional)

1. Either delete `calculation_engine/ws_engine.py` + the
   `WS_ABREGELUNG_THRESHOLD` seed row, OR
2. Change its expression to `1.0` (to match Excel) so that if someone
   re-wires it in the future, it produces the right numbers.

Neither fix is urgent; this is a code-hygiene finding.

## Scripts

- Grep against `simulator/` + `calculation_engine/`
- `WS365Formula.objects.get(column_name='einspeich').expression`
- Excel recompute spot-check in session:
  `python_P = (O*0.65) if O/I<=0.65 else (I*0.65*0.65)` → 653.69 for
  day 318 vs Excel cached 1005.68.
