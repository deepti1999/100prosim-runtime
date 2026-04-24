# §05 Live Cascade — methodology

## Excel side

1. Load `_S.xlsx` and `WS.xlsm` with `openpyxl(data_only=False)`.
2. Walk every formula cell (strings starting with `=`) and parse
   cell references via regex.
3. Build a reverse-dependency graph: `target_cell → set of cells referring to it`.
4. For each input, compute the transitive closure (BFS) up to depth 6.
5. Record baseline cached values for every cell in the closure.

## DB / Django side

1. Via Django ORM (shell inside docker): query `Formula.expression__icontains=<code>` to find every Formula row that references a given data code.
2. The union of these forms the first-order consumer set. Further cascade expansion could be computed by recursively finding consumers of each Formula's output key.
3. The actual recalc cascade is controlled by `recalc_service.py` + `signals.py` — any Formula whose expression references a dirty code gets re-evaluated.

## Comparison

- **Set-size comparison**: Excel counts individual cells (one per row in _S.xlsx!2. Erneuerbare etc.); DB counts Formula rows (one row covers N data rows). Direct equality not expected.
- **Concept-level congruence**: for each input, check whether cascade reaches the expected domain targets (renewable energy rows, Bilanz aggregates, WS365 daily chain, etc.).
- **Verdict**: CONGRUENT if both sides have non-empty cascades OR both empty; DIVERGENT if one has cascade and the other doesn't.

## Limitations

- **Range refs** (e.g., `SUM(L1:L100)`) are approximated to their first cell for graph purposes. Fine for closure detection but understates breadth.
- **INDIRECT** / `INDEX(MATCH(...))` formulas are opaque to this parser — we don't know which specific cell an `INDIRECT` resolves to at runtime. Their edges are MISSING from the reverse-dependency graph.
- **Named ranges** are resolved by name only; we don't expand them.
- **Cross-workbook refs** (e.g., `'[_S.xlsx]1. Flächen'!...`) are recorded per-workbook; cross-book edges are NOT traversed.

Despite these limitations, the graph is dense enough to catch the major cascade paths (multi-hundred cells per input on common paths).
