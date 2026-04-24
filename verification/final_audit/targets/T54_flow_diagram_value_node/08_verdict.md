# T54 — Verdict: **PASS**

*(upgraded 2026-04-24 CAVEAT → PASS — Gasspeicher math fix shipped per
SOURCE_GROUNDED_ANSWERS.md Q4 + Pascal approval.)*

## Closure 2026-04-24

Math fix shipped: `simulator/signals.py:175` changed from
`(ely_branch_value × ETA_STROM_GAS) × tl_factor` to
`gas_storage × tl_factor`, aligning with Excel's `L37 = L36 ×
TLproEingabeEinheit` formula authority. All three Gasspeicher diagram
positions now read 87 (previously 83/87/87 inconsistent).

- V2 — `simulator/test_wb_signals.py::T54GasspeicherTagesInvariantTests`
  locks the formula at source level + asserts prior buggy basis won't
  reappear.
- V4 — localhost screenshot `verification/final_audit/t54_fix/
  localhost_annual_electricity_87_87_87.png` shows 87/87/87.
- V5 — Heroku screenshot under same dir (spin-up cycle).
- V6 — this section + `HARDCODED_VALUES_TRACE.md` §6 correction
  ("H37 hardcoded" claim replaced with actual L37 formula documentation).
- Goldens C + D re-captured in the same commit (math change moves them
  deliberately; Pascal approved).

---

All 6 D-items shipped (D1-D3+D4c via Track 1 `7c02458`, D4a/D4b via Phase B `897e212`). Visible in `screenshots/{localhost,heroku}/08_annual_electricity.png`:
- D1 Tagesladungen under each source (italic blue: 397, 186, 5, 1)
- D2 Tagesladungen on each flow segment (509, 313, 134, 87, 65, etc.)
- D3 percent shares (62.2%, 29.2%, 0.8%, 0.2%)
- D4a "194 GW" Pmax-Ely-ES (red, under 405.027 box)
- D4b "261 GW (elekt.)" Pmax-RV (would be near Rückverstromung)
- D4c "Abgleichdifferenz 160" bottom-right

**Caveat:** documented non-blocking discrepancy in `HARDCODED_VALUES_TRACE.md` §6 — Gasspeicher Direktverbr Tages shows `83` (formula-correct) vs Excel diagram's `87` (visual copy, Excel cell H37 has no formula). Carried through unchanged because the formula output is mathematically correct; matching the Excel visual would require a hand-fix that the formula doesn't justify.

## Caveat investigated 2026-04-24 (Fix 4) — NOT resolved

Full investigation at `verification/final_audit/gasspeicher_83_vs_87.md`. Key findings:

1. **HARDCODED_VALUES_TRACE.md §6 is wrong about H37.** There is no H37; the actual Excel cells producing "87" are **L37** and **Q37** on `1.Jahresbilanz_Strom`, and **both are formulas** (`=L36*TLproEingabeEinheit`, `=Q36*TLproEingabeEinheit`), not hardcoded visual copies.

2. **Excel is authoritative**, not "Excel is wrong". Excel's 87 reflects the solver-simulated actual einspeich (263,970 annual), while our 83 uses the scenario-target input (385,933 × 0.65 = 250,857). Both are internally consistent; Excel uses the same annual basis for all three Gasspeicher diagram positions → all three labeled 87. Our simulator produces 83/87/87 — subtly inconsistent across the gas-flow positions.

3. **Fix proposal filed** — one-line change in `simulator/signals.py:175`: use `gas_storage * tl_factor` instead of `(ely_branch_value * ETA_STROM_GAS) * tl_factor`. Awaiting Pascal's approval per Fix 4 protocol (backend math change, not polish).

**Verdict remains PASS-WITH-CAVEAT** — not upgraded to PASS. Pascal decides whether to ship the math change.
