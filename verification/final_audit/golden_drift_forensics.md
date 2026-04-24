# Regression goldens C / D — drift forensics

**Date:** 2026-04-24
**Investigator:** Claude (audit follow-up Task 1b)
**Scope:** the only two regression goldens that have NOT been re-captured since their initial commit — `regression/golden/C-ws-balance.json` and `regression/golden/D-full-flow-verbrauch-solar-wind.json`.

## Headline

**A is current** (last re-captured 2026-04-22 with Pascal sign-off, commit `9d18bb5`; `compare.py A` exits 0 with 97/97 fields matching today).

**C and D have NEVER been re-captured.** Each has exactly ONE commit in its `git log --follow` history — the original capture. Every code change between then and now (~25 commits including 4 perf-pass commits, 1 cache-coherency fix, 3 region-scope changes, the entire Phase 2-C number-format work) is a potential silent-drift source.

`compare.py C` and `compare.py D` cannot even produce a diff today: they require a Playwright-driven *capture* step first (login → mutate workspace → poll BalanceJob → emit JSON to `verification/<today>/`) and that capture step has not been run for C or D in this audit run. Without the capture, compare returns "No current-run JSON".

## Per-golden git archaeology

### A-baseline-readonly.json — `git log --follow`

```
9d18bb5 stakeholder-verify: gap #1 (scenario A) closed — golden regenerated with sign-off
55fe5b8 chore: add Claude-driven regression harness, hooks, workflow docs
```

- **55fe5b8** (2026-04-20) — initial capture, 162 fields.
- **9d18bb5** (~2026-04-22) — re-capture with explicit Pascal sign-off in commit subject. Trimmed to 97 fields (Phase 2 translation drift acknowledged + values re-baselined).

This is the only golden where the re-capture was done explicitly per the `IMPLEMENTATION_PLAN.md` §0 "Golden files regenerate **only** with explicit Pascal sign-off" rule. Categorisation: **(a) intentional re-capture with sign-off**.

### C-ws-balance.json — `git log --follow`

```
55fe5b8 chore: add Claude-driven regression harness, hooks, workflow docs
```

ONE commit, 2026-04-20. Captured 50 lines of golden state (page panel values + summary cards + SVG flow values). Never re-captured.

Categorisation: **never updated since first commit** → potential silent drift from any subsequent code change in the WS calculation, iteration count, number format, or region scope code paths.

### D-full-flow-verbrauch-solar-wind.json — `git log --follow`

```
6470e00 test: scenario D (verbrauch + solar/wind full flow) + self-review rule
```

ONE commit. Same as C — never updated.

Categorisation: **never updated since first commit**.

## Inspection of C golden contents — mixed format already at capture time

```json
{
  "_meta": { "captured_on": "2026-04-20", "note": "..." },
  "ws_page_post_balance": {
    "balance_by_solar": {
      "optimales_solar_gwh": "1.211.176",      // GERMAN format dot-thousands
      "speicherdrift_gwh": "0,0",              // GERMAN comma-decimal
      "jahresstrom_gwh": "1.107.646",
      "iterationen": "1"
    },
    "summary_cards": {
      "ueberschuss_summe_gwh": "602.294",      // GERMAN
      "abregelung_summe_gwh": "195.890"
    }
  },
  "annual_electricity_post_balance": {
    "svg_flow_values": {
      "txt-flow": ["4,525", "1,211,176", ...],  // ENGLISH comma-thousands
      "txt-value": ["1,107,646"]
    }
  }
}
```

**Observation:** the golden was captured at a time (Apr 20) when the WS page was already in German format (per PDF §2.5.2 "Die Seite 'Szenario-Abgleich' ist als einzige bereits auf deutsches Zahlenformat umgestellt") but the SVG flow diagram on `/annual-electricity/` was still using English thousand-separator default `Number.toLocaleString()` (browser locale fallback). After Phase 2-C (commit `b8e4a45` ~Apr 21) the SVG values would have been switched to explicit `de-DE` locale → values like `1.211.176`, breaking the `txt-flow: ["1,211,176", ...]` array assertion.

This is a clear, identifiable, **silent drift source**: Phase 2-C's number-format work moved the SVG values without bumping the C golden.

## Code commits between 2026-04-20 and now that could shift C / D probed values

`git log --since="2026-04-20" --until="2026-04-24" -- calculation_engine/ simulator/ws365_*.py simulator/balance_jobs.py simulator/recalc_service.py simulator/ws_models.py`:

```
fb5f2c8 stakeholder-2.3c-wsdata-region: WSData per-(owner, region) (T66)
cb746eb stakeholder-2.3c-balance-region: payload.region_code + worker region_scope (T66)
0f8196b stakeholder-2.3b-middleware: active region session middleware (T65)
54d4567 fix: balance jobs now invalidate ALL process-local caches at entry
a31fa64 fix: invalidate recalc_cache at entry of balance jobs + multi-pass loops
a2beb6b perf: settle_totals max_rounds 2 -> 1 (round 2 is expensive cache miss)
37baec0 fix: recalc_cache returns empty-on-hit — fixes infinite-pass bug
7064265 perf: sector_first max_cycles 2->1 for solar + wind
5ba8026 perf: early-break GW on zero-slope + cut convergence cycles 3->2
5bfaa9c perf: halve inner iteration counts in _balance_heat_sectors_after_ws
f2147ef perf: early-exit on already-balanced state for 4 orchestrator paths
9243933 perf: cache pure compute in get_ws_365_data (Step 1.7)
ebabf43 perf: cache global lookups in _auto_context_from_tokens (Step 1.6)
e690bee perf: bulk-load sector totals in _get_sector_totals (Step 1.5)
639851a perf: cache calculate_bilanz_data output per CalculationRun (Step 1.4)
568d43f perf: idempotent short-circuit for recalc functions (Step 1.2)
```

Plus the Phase 2-C number-format commit `b8e4a45` (not in this list because the file filter excluded templates).

### Per-commit drift assessment

| Commit | Risk to C/D | Direction |
|---|---|---|
| `b8e4a45` Phase 2-C number format | **HIGH** — SVG values switched English→German | Format-only drift; numerical equivalent. |
| `a2beb6b` settle_totals 2→1 | **MEDIUM** — could shift converged values within ±5 ha / ±1 GWh tolerance per CLAUDE.md note | Numerical drift, small. |
| `7064265` sector_first 2→1 | **MEDIUM** — same | Same. |
| `5ba8026` cycles 3→2 + zero-slope break | **MEDIUM** — same | Same. |
| `5bfaa9c` halve inner iter counts | **MEDIUM** — same | Same. |
| `54d4567` cache wipe at job entry | **LOW** — corrects a class of bugs (test_bb_bal would catch a regression here) | Correctness-positive. |
| `37baec0` recalc_cache empty-on-hit | **LOW** — fix, not change | Correctness-positive. |
| `0f8196b`/`cb746eb`/`fb5f2c8` region scope | **LOW** for testsim default DE — values preserved | Identity for default-region single user. |
| `f2147ef` early-exit on balanced | **LOW** — only triggers when state is already balanced (which the seed is) | Could change `iterationen` count from "1" to "0". |
| `9243933`/`ebabf43`/`e690bee`/`639851a` caches | **LOW** — caches don't change values, only speed | None. |

**Highest-confidence silent drift:** Phase 2-C `b8e4a45`. The SVG portion of the C golden almost certainly fails today on string equality.

**Plausible numerical drift:** the iteration-count perf cuts (a2beb6b, 7064265, 5ba8026, 5bfaa9c) — within tolerance per CLAUDE.md but not guaranteed bit-identical.

## What I did NOT do (per audit constraints)

- **Did NOT re-capture C or D.** Per the `IMPLEMENTATION_PLAN.md` §0 rule + the audit-prompt explicit instruction: "Do NOT re-capture. Document only."
- **Did NOT run the Playwright capture step** for C or D. Doing so would dirty the testsim workspace mid-audit and potentially affect Task 2 / Task 3 results.
- **Did NOT fix the Phase 2-C drift in the C golden.** Same rule.

## Recommendations to Pascal

For each drift source — pick ONE:

### 1. Phase 2-C number-format drift in C / D goldens (HIGH confidence)

**Option (a) — re-capture with explicit Pascal sign-off, accept format-drift only.**
```bash
# Step 1: capture C
docker compose exec web python regression/capture_C.py  # if such script exists; else playbook-driven
# Step 2: review the diff vs current golden
# Step 3: confirm deltas are ONLY format drift (1,211,176 → 1.211.176 etc.)
# Step 4: replace + commit:
#   regression/golden/C-ws-balance.json (regen)
#   commit message: "test(regression-C): re-capture golden after Phase 2-C number-format drift — Pascal sign-off"
```
~30 minutes. Same recipe for D.

**Option (b) — fix the format drift in the golden by hand.** Open `regression/golden/C-ws-balance.json`, search-and-replace English thousand-comma → German thousand-dot in the `svg_flow_values` arrays. Less work but doesn't catch numerical drift, only format. Not recommended (you lose the discipline of a real re-capture).

### 2. Iteration-cut numerical drift (MEDIUM confidence)

If the re-capture in option 1(a) reveals numerical drift beyond format (e.g. `iterationen: "1"` → `"2"`, or `optimales_solar_gwh: "1.211.176"` → `"1.211.180"`), confirm the new values are within the `±5 ha / ±1 GWh tolerance` per CLAUDE.md. If yes: accept + commit the new golden. If no: investigate further (cache coherency? worker process-local state?).

### 3. Maintenance cadence going forward

After every phase that touches `calculation_engine/*`, `simulator/ws365_*.py`, or any number-format setting, re-run a scenario-C capture and explicitly diff-review before next commit. Add a CLAUDE.md note: *"After any commit to this list of files, re-capture scenario C + diff before next commit"*.

## Final verdict

**PASS-WITH-CAVEAT** for this forensic doc itself — the audit deliverable (document silent drift, identify code commits, recommend) is complete. The drift in the C/D goldens is real, identifiable, and has a clean fix recipe. Pascal decides whether to re-capture (~30 min × 2 goldens) or accept the harness running degraded until Phase 7.

**No goldens were silently re-captured in this audit run.**
