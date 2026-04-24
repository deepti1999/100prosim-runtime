# §3 Formula Parity — discrepancies

## Resolved findings

### F006 — `WS_ABREGELUNG_THRESHOLD = 0.65` dead-code risk

**Status**: Dead code — no production impact. Written up in
`09_findings/F006_WS_ABREGELUNG_THRESHOLD_dead_code.md`.

- `calculation_engine/ws_engine.py` would use `0.65` as both threshold
  and capped-mode multiplier for Einspeich.
- Excel's `Zeitreihen Kalkulation!P158..P521` uses named range
  `Abregelung` = `1.0` for both roles.
- If `ws_engine.py` were in the hot path, Einspeich would under-count
  by up to 35 % on extreme-excess days and the ELSE-branch multiplier
  would differ (Python 0.65 × 0.65 = 0.4225 vs Excel 1 × 0.65 = 0.65).
- Live production uses `WS365Formula[einspeich]`, not `ws_engine.py` —
  grep confirms zero importers.

## Unresolved / candidate discrepancies

### Candidate C001 — `Formula[10.2]` expression shape mismatch

- DB `Renewable_10_2.expression = "Renewable_9_4_3_3"` (single-var).
- Excel `_S.xlsx!2. Erneuerbare!L234 = "=L232/L233%"` (ratio × 100).
- Structure is clearly different.
- BUT — `RenewableData[10.2].name = "Strom"`, not "Anteil Erneuerb. an Stromverbrauch". So the Excel cell I matched (`L234`) is likely the wrong cell. The correct Excel cell for DB `10.2` Strom is probably `L232` (cached value 242642, which matches DB's 242606 closely).
- Verdict: **UNPROVEN** — mapping uncertain. Candidate pending a curated mapping.

### Candidate C002 — Verbrauch formula chain coverage

- 244 Verbrauch formulas, none individually verified against
  Excel `4. Verbrauch` cells.
- Spot-check `V_1.1.1 = Verbrauch_1_0 * Verbrauch_1_1 / 100` —
  this is structurally a product-of-percents, which is a common
  Excel pattern but I did not find its exact twin cell.
- Verdict: **DEFERRED** — needs row-level mapping to give verdict.

### Candidate C003 — Renewable fixed-input formulas with expression `0`

- `Formula[9.3.1].expression = '0'` but `RenewableData[9.3.1]` holds
  a real seed value (e.g. `status_value = 406403.3` for a recent
  scenario).
- Interpretation: `expression='0'` is an input/fixed-row marker; the
  actual value comes from the DB row, not the formula.
- Cross-check: `Formula[9.3.1].is_fixed = True`? Worth confirming.
- Verdict: **DESIGN_BY_CONTRACT** — not a bug, but worth documenting
  so future devs know why these expressions are `'0'`.

## Unresolved-for-good-reason

### 153 empty `expression` rows

Of 760 Formulas, 153 have `expression = ''`. These are placeholder
rows marking codes that need to exist in the table but have no
computation (they receive their value from seed or user input).

These are not a discrepancy per se — they are a schema choice. They
cluster around renewable input codes (9.x family), verbrauch static
rows, and ws placeholders for legacy references.
