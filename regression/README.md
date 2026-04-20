# Regression harness

Claude-session-driven UI + calculation regression tests. Complements the thesis `simulator.test_*` suites, does not replace them.

## Layout

```
regression/
  scenarios/<id>.yml        scenario descriptor (inputs, probe points)
  golden/<id>.json          captured baseline values (hand-editable, committed)
  screenshots/<id>/         reference screenshots (committed)
  playbook.md               step-by-step recipes Claude follows per scenario
  compare.py                diffs a current-run JSON against its golden
```

Run artifacts from each session go to `verification/<today>/`, which is gitignored and cleared at the end of the turn. Only `regression/golden/` and `regression/screenshots/` persist.

## Modes

- **Capture** — run a scenario for the first time (or after an intentional behavior change). Output → `regression/golden/<id>.json` + `regression/screenshots/<id>/`. Commit the result.
- **Verify** — normal mode. Output → `verification/<today>/<id>.json`. Then `python regression/compare.py <id>` exits 0 if equal to golden, non-zero with a diff otherwise.

## Available scenarios

See `playbook.md` for execution steps.

- **A — baseline-readonly** — login + visit every main page + capture top-line numbers. Detects seed / migration / navigation drift. No DB mutations.
- **C — ws-balance** — login + click "WS-Speicher ausgleichen" → poll `BalanceJob` → capture post-balance values. Hard-asserts the thesis invariants `9.3.1 = 405047` and `9.3.4 = 189289`, which the landing page states are fixed through a WS balance.

## Invariants (hard-asserted, not captured)

| Code | Value | Source |
|------|-------|--------|
| 9.3.1 | 405047 | landing page copy — must remain fixed through WS balance |
| 9.3.4 | 189289 | same |

Add more here when the user gives a thesis-verified fact.

## Regenerating goldens

Only when a behavior change is **intentional**:

1. Run the scenario in capture mode.
2. Review the diff (`git diff regression/golden/`) — every changed field must be explainable by the intentional change.
3. Commit golden + code in the same commit so reviewers see both.

Never regenerate goldens "because they drifted" — drift = signal, investigate first.
