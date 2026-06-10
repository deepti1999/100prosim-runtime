# F010 — Residual-vs-sum divergence for `10.x ziel` aggregate formulas

**Severity**: MEDIUM
**Affects calc**: POSSIBLY — identical at balanced scenarios, may diverge when user inputs unbalance the sibling shares.
**Domain**: §02 Full Formula Parity
**Confidence**: MEDIUM (observed structurally; needs §05 live-cascade confirmation to prove scenario divergence).

## Observed

Several `10.x ziel` (sector-total renewable energy) Formulas compute
the aggregate via **sum of children** in the DB, while Excel computes
the same cell as a **residual** (100 − other siblings). Example:

| formula key | DB expression | Excel formula |
|-------------|---------------|---------------|
| `10.5_ziel_target` | `Renewable_10_5_1 + Renewable_10_5_3 + Renewable_10_5_2` | `=100-M62-M64-M65` |
| `10.4_ziel_target` | `Renewable_10_4_1 + Renewable_10_4_3 + Renewable_10_4_2` | (sum form in Excel L-column; residual hypothesis needs spot-check) |

In the default scenario the children sum to the expected total, so
both forms evaluate to the same number. Under a user-edited scenario
where one sibling is moved without rebalancing the others, the two
forms will diverge:
- Sum form: Total = changed_value + other_siblings
- Residual form: Total = 100 − other_siblings (changed sibling ignored)

## Why this might matter

Our app's recalc flow triggers on every save. If a user edits
`Renewable_10_5_1.ziel`, the DB sum-form recomputes `10.5_ziel` to
include the new value; but if the Excel residual-form was the
scenario's intent, the "correct" value would be `100 − 10.5.2 − 10.5.4`
(i.e., treating 10.5.1 as the filler).

**Interpretation 1**: Excel's residual is the authoritative view —
10.5.1 absorbs any imbalance, and direct edits to 10.5.1 should be
*ignored* in favour of the residual calc.

**Interpretation 2**: DB's sum is the authoritative view — each
child is independently set, and the total is the sum.

Pascal's product design determines which is correct. This is a
**behavioural question**, not a unit-level bug.

## Confirmation plan (§05 live cascade)

Set up an unbalanced scenario:
1. Take baseline: 10.5_ziel = 10.5.1 + 10.5.2 + 10.5.3 = 100 %.
2. Edit 10.5.1 to 150 % (illegal in any reasonable scenario, but
   exposes the divergence).
3. Read DB 10.5_ziel → should be 150 + 10.5.2 + 10.5.3 (sum form).
4. Open Excel with the same inputs → read M234 → should be
   100 − 10.5.2 − 10.5.3 (residual form).
5. Compare.

If they diverge: F010 confirmed at MEDIUM severity. If Excel also
changes to the sum-form (i.e., the residual-form is only for the
default scenario), F010 cleared as an artifact of Excel's specific
scenario state.

## Recommended disposition

Wait for §05 live cascade result before elevating to HIGH. If
confirmed, recommend aligning the DB formula to Excel's residual
form (change `10.x_ziel_target` to `100 − Renewable_10_x_a_ziel
− Renewable_10_x_b_ziel − Renewable_10_x_c_ziel`).

## Scripts

- `02_full_formula_parity/per_formula_diff.csv` rows for keys matching
  `10.[3-6]*_ziel_target` with `diff_category='REAL_DIFF'`.
- §05 live cascade will produce cell-level diff proof.
